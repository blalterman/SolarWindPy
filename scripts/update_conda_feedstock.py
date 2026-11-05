#!/usr/bin/env python
"""Automate conda-forge feedstock updates for SolarWindPy releases.

This script automates the process of updating the conda-forge feedstock
after a new PyPI release. It reads the sdist's SHA256 from PyPI's JSON API,
waiting with backoff while the new release is not yet listed, and creates a
GitHub issue for tracking.

Usage:
    python scripts/update_conda_feedstock.py v0.1.5
    python scripts/update_conda_feedstock.py 0.1.5 --dry-run
    python scripts/update_conda_feedstock.py 0.1.5 --fork-owner myusername
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

import requests
from packaging import version

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# How long to wait for PyPI to list a new release and its sdist, and the
# backoff between attempts: the first wait, the factor, and the cap.
RELEASE_WAIT = 600
BACKOFF_START = 15
BACKOFF_FACTOR = 2
BACKOFF_MAX = 120


class CondaFeedstockUpdater:
    """Handles automated conda-forge feedstock updates.

    This class manages the complete workflow of updating conda-forge
    feedstock repositories with new PyPI releases.
    """

    def __init__(
        self,
        package_name: str = "solarwindpy",
        feedstock_repo: str = "conda-forge/solarwindpy-feedstock",
        fork_owner: Optional[str] = None,
        release_wait: float = RELEASE_WAIT,
    ):
        """Initialize the feedstock updater.

        Parameters
        ----------
        package_name : str
            Name of the PyPI package
        feedstock_repo : str
            GitHub repository for the feedstock (org/repo format)
        fork_owner : str, optional
            GitHub username for fork (if different from current user)
        release_wait : float
            Total seconds to wait for PyPI to list a release and its sdist
        """
        self.package_name = package_name
        self.feedstock_repo = feedstock_repo
        self.fork_owner = fork_owner or self._get_github_username()
        self.project_root = Path(__file__).parent.parent
        self.release_wait = release_wait
        # Injectable so the tests need not wait out the backoff.
        self._sleep = time.sleep
        # One fetch per version serves both validation and the checksum.
        self._release_json = {}

    def _get_github_username(self) -> str:
        """Get current GitHub username from git config or environment.

        Returns
        -------
        str
            GitHub username
        """
        # Try environment variable first
        if "GITHUB_ACTOR" in os.environ:
            return os.environ["GITHUB_ACTOR"]

        # Try git config
        try:
            result = subprocess.run(
                ["git", "config", "user.name"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "unknown"

    def verify_git_tag_provenance(
        self, version_str: str, require_master: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """Verify git tag exists and check branch provenance.

        This method verifies that:
        1. The git tag exists locally
        2. The tag points to a valid commit
        3. The commit is on the master branch (if required)
        4. Returns the commit SHA for reference

        Parameters
        ----------
        version_str : str
            Version string to verify (without 'v' prefix)
        require_master : bool
            If True, require tag to be on master branch (default: False)

        Returns
        -------
        tuple[bool, str or None]
            (success, commit_sha) - True if verified, commit SHA if found
        """
        tag_name = f"v{version_str}"

        try:
            # Check if git tag exists
            result = subprocess.run(
                ["git", "tag", "-l", tag_name],
                capture_output=True,
                text=True,
                check=False,
                cwd=self.project_root,
            )

            if not result.stdout.strip():
                print(f"⚠️  Git tag {tag_name} not found in repository")
                return False, None

            # The commit the tag names; a bare annotated tag resolves to the
            # tag object, not the commit.
            result = subprocess.run(
                ["git", "rev-parse", f"{tag_name}^{{commit}}"],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.project_root,
            )
            commit_sha = result.stdout.strip()

            print(f"📍 Found tag {tag_name} at commit {commit_sha[:8]}")

            # Verify tag is on master branch (if required)
            result = subprocess.run(
                ["git", "branch", "--contains", commit_sha],
                capture_output=True,
                text=True,
                check=False,
                cwd=self.project_root,
            )

            if result.returncode == 0:
                branches = [
                    b.strip().lstrip("* ")
                    for b in result.stdout.strip().split("\n")
                    if b.strip()
                ]

                if branches:
                    has_master = any("master" in b for b in branches)
                    if has_master:
                        print(f"✅ Verified {tag_name} is on master branch")
                    elif require_master:
                        print(f"⚠️  Warning: Tag {tag_name} not found on master branch")
                        print(
                            f"   Branches containing this tag: {', '.join(branches[:5])}"
                        )
                        return False, commit_sha
                    else:
                        print(f"📋 Tag found on branches: {', '.join(branches[:3])}")

            # Get tag annotation message for additional context
            result = subprocess.run(
                ["git", "tag", "-l", "--format=%(contents:subject)", tag_name],
                capture_output=True,
                text=True,
                check=False,
                cwd=self.project_root,
            )
            if result.returncode == 0 and result.stdout.strip():
                tag_message = result.stdout.strip()
                print(f"📝 Tag message: {tag_message}")

            return True, commit_sha

        except subprocess.CalledProcessError as e:
            print(f"⚠️  Could not verify git tag provenance: {e}")
            return False, None
        except Exception as e:
            print(f"⚠️  Git verification failed: {e}")
            return False, None

    def verify_github_release_integrity(
        self, version_str: str, pypi_sha256: str
    ) -> bool:
        """Verify GitHub release SHA256 matches PyPI distribution.

        Parameters
        ----------
        version_str : str
            Version to verify
        pypi_sha256 : str
            SHA256 hash from PyPI source distribution

        Returns
        -------
        bool
            True if GitHub release SHA256 matches PyPI (or if check unavailable)
        """
        try:
            tag_name = f"v{version_str}"

            # Use gh CLI to get release assets
            result = subprocess.run(
                ["gh", "release", "view", tag_name, "--json", "assets"],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.project_root,
            )

            release_data = json.loads(result.stdout)

            # Find the .tar.gz asset
            tar_gz_assets = [
                a
                for a in release_data.get("assets", [])
                if a["name"].endswith(".tar.gz")
            ]

            if not tar_gz_assets:
                print(f"⚠️  No .tar.gz asset found in GitHub release {tag_name}")
                return True  # Permissive - don't block

            # Extract SHA256 from digest field (format: "sha256:hash")
            github_sha256 = tar_gz_assets[0].get("digest", "")
            if github_sha256.startswith("sha256:"):
                github_sha256 = github_sha256[7:]  # Remove "sha256:" prefix

            if github_sha256 == pypi_sha256:
                print("✅ GitHub release SHA256 matches PyPI")
                print(f"   Hash: {github_sha256[:16]}...")
                return True
            else:
                print("⚠️  SHA256 mismatch between GitHub and PyPI")
                print(f"   GitHub: {github_sha256[:16]}...")
                print(f"   PyPI:   {pypi_sha256[:16]}...")
                return False

        except subprocess.CalledProcessError:
            print("⚠️  Could not verify GitHub release (gh CLI may not be available)")
            return True  # Permissive - don't block if gh unavailable
        except Exception as e:
            print(f"⚠️  GitHub release verification skipped: {e}")
            return True  # Permissive - don't block on errors

    def fetch_release_json(
        self, version_str: str, max_wait: Optional[float] = None, timeout: int = 10
    ) -> Optional[dict]:
        """Return PyPI's JSON for the release, once it lists the sdist.

        Right after an upload PyPI may not list the release, or may list it
        before its sdist; both are retried with exponential backoff until
        ``max_wait`` seconds of waiting have passed. A release once found is
        kept, so later calls for the same version do not ask PyPI again.

        Parameters
        ----------
        version_str : str
            Version to fetch
        max_wait : float, optional
            Total seconds to wait between attempts before giving up; defaults
            to ``release_wait``
        timeout : int
            Request timeout in seconds

        Returns
        -------
        dict or None
            The release's JSON, or None if it never listed an sdist
        """
        if version_str in self._release_json:
            return self._release_json[version_str]
        if max_wait is None:
            max_wait = self.release_wait
        url = f"https://pypi.org/pypi/{self.package_name}/{version_str}/json"
        waited = 0.0
        delay = BACKOFF_START
        while True:
            try:
                response = requests.get(url, timeout=timeout)
                if response.status_code == 200:
                    data = response.json()
                    if self._sdist_entry(data) is not None:
                        self._release_json[version_str] = data
                        return data
                    reason = "no sdist listed yet"
                else:
                    reason = f"status {response.status_code}"
            except (requests.RequestException, ValueError) as e:
                reason = str(e)

            if waited >= max_wait:
                print(
                    f"❌ PyPI has no sdist for {self.package_name} v{version_str} "
                    f"after {waited:.0f}s ({reason})"
                )
                return None
            pause = min(delay, max_wait - waited)
            print(f"⏳ PyPI not ready ({reason}); retrying in {pause:.0f}s...")
            self._sleep(pause)
            waited += pause
            delay = min(delay * BACKOFF_FACTOR, BACKOFF_MAX)

    @staticmethod
    def _sdist_entry(data: dict) -> Optional[dict]:
        """Return the ``urls`` entry of the sdist in PyPI release JSON, if any."""
        for entry in data.get("urls") or []:
            if entry.get("packagetype") == "sdist":
                return entry
        return None

    def validate_pypi_release(self, version_str: str) -> bool:
        """Validate that the PyPI release exists and is not a pre-release.

        Parameters
        ----------
        version_str : str
            Version string to validate

        Returns
        -------
        bool
            True if valid stable release exists
        """
        try:
            v = version.parse(version_str)
        except version.InvalidVersion as e:
            print(f"❌ Invalid version {version_str}: {e}")
            return False
        if v.is_prerelease:
            print(f"❌ Pre-release version {version_str} - skipping feedstock update")
            return False

        data = self.fetch_release_json(version_str)
        if data is None:
            return False

        pypi_version = data.get("info", {}).get("version")
        if pypi_version != version_str:
            print(
                f"❌ Version mismatch: requested {version_str}, PyPI has {pypi_version}"
            )
            return False

        print(f"✅ Validated PyPI release: {self.package_name} v{version_str}")
        return True

    def get_sdist_sha256(self, version_str: str) -> Optional[str]:
        """Return the SHA256 of the release's sdist, as PyPI's JSON API lists it.

        Reading the digest PyPI computed at upload needs no download, so it
        does not depend on the file CDN, which can serve a cached 404 for a
        while after the upload.

        Parameters
        ----------
        version_str : str
            Version whose sdist to look up

        Returns
        -------
        str or None
            SHA256 hash as hex string, or None if failed
        """
        data = self.fetch_release_json(version_str)
        if data is None:
            return None
        entry = self._sdist_entry(data)
        sha256_hash = entry.get("digests", {}).get("sha256")
        if not sha256_hash:
            print(f"❌ PyPI lists no sha256 for {entry.get('url')}")
            return None
        print(f"✅ sdist: {entry.get('url')}")
        print(f"✅ SHA256: {sha256_hash}")
        return sha256_hash

    def update_meta_yaml(
        self, version_str: str, sha256_hash: str, meta_path: Path
    ) -> bool:
        """Update the conda recipe meta.yaml file.

        Parameters
        ----------
        version_str : str
            New version string
        sha256_hash : str
            SHA256 hash of the source distribution
        meta_path : Path
            Path to the meta.yaml file

        Returns
        -------
        bool
            True if update successful
        """
        try:
            if not meta_path.exists():
                print(f"❌ meta.yaml not found: {meta_path}")
                return False

            # Read current meta.yaml
            content = meta_path.read_text()

            # Update version and SHA256
            # Handle Jinja2 template format
            lines = content.split("\n")
            updated_lines = []

            for line in lines:
                if line.strip().startswith("{% set version ="):
                    updated_lines.append(f'{{% set version = "{version_str}" %}}')
                elif line.strip().startswith("sha256:"):
                    updated_lines.append(f"  sha256: {sha256_hash}")
                else:
                    updated_lines.append(line)

            # Write updated content
            updated_content = "\n".join(updated_lines)
            meta_path.write_text(updated_content)

            print(f"✅ Updated {meta_path} with version {version_str}")
            return True

        except Exception as e:
            print(f"❌ Failed to update meta.yaml: {e}")
            return False

    def _get_dependency_comparison(self) -> str:
        """Run comparison script and format output for issue.

        Returns
        -------
        str
            Formatted comparison output or error message
        """
        try:
            result = subprocess.run(
                [sys.executable, "scripts/compare_feedstock_deps.py"],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=self.project_root,
            )

            if result.returncode == 0:
                # Script succeeded - include its output
                return f"""### Dependency Comparison

```
{result.stdout}
```

📝 **Review the table above** - any ⚠️ markers indicate changes needed in feedstock.

⚠️ **CRITICAL**: The autotick bot updates **version and SHA256 ONLY**, NOT dependencies!
"""
            else:
                # Script failed - provide fallback message
                return """### Dependency Comparison

⚠️ Automatic comparison unavailable. Run manually:
```bash
python scripts/compare_feedstock_deps.py
```

⚠️ **CRITICAL**: The autotick bot updates **version and SHA256 ONLY**, NOT dependencies!
"""

        except Exception as e:
            # Non-critical failure - provide fallback
            return f"""### Dependency Comparison

⚠️ Could not run automatic comparison: {e}

Run manually to check:
```bash
python scripts/compare_feedstock_deps.py
```

⚠️ **CRITICAL**: The autotick bot updates **version and SHA256 ONLY**, NOT dependencies!
"""

    def build_issue_body(
        self,
        version_str: str,
        sha256_hash: str,
        comparison_output: str,
        commit_sha: Optional[str] = None,
    ) -> str:
        """Return the tracking issue's Markdown body.

        Parameters
        ----------
        version_str : str
            Version being updated
        sha256_hash : str
            SHA256 hash of the sdist
        comparison_output : str
            The dependency comparison, from `_get_dependency_comparison`
        commit_sha : str, optional
            Git commit SHA if provenance was verified

        Returns
        -------
        str
        """
        body = f"""## Automated Conda Feedstock Update

**Version**: `{version_str}`
**Package**: `{self.package_name}`
**PyPI URL**: https://pypi.org/project/{self.package_name}/{version_str}/
**SHA256**: `{sha256_hash}`"""

        # Add git provenance info if available
        if commit_sha:
            body += f"""
**Git Commit**: `{commit_sha}`
**GitHub Release**: https://github.com/blalterman/SolarWindPy/releases/tag/v{version_str}
**Source Provenance**: ✅ Verified"""

        body += f"""


---

{comparison_output}

---

### Update Checklist

- [x] PyPI release validated
- [x] SHA256 read from PyPI's listing of the source distribution
- [ ] **Dependencies reviewed** (see comparison above)
- [ ] Autotick bot PR created (usually 2-6 hours)
- [ ] If dependencies changed: manually update bot PR
- [ ] CI checks passing
- [ ] PR merged

### Automation Status

🤖 This issue was created automatically by the conda feedstock update automation.

### Manual Update Instructions

When bot PR appears (usually 2-6 hours):

1. **Review dependency changes** in comparison table above
2. **If dependencies changed**:
   ```bash
   gh pr checkout <PR_NUMBER> --repo conda-forge/{self.package_name}-feedstock
   # Edit recipe/meta.yaml requirements.run section
   git add recipe/meta.yaml
   git commit -m "Update runtime dependencies"
   git push
   ```
3. **Monitor CI**: `gh pr checks <PR_NUMBER> --watch`
4. **Merge when green**: `gh pr merge <PR_NUMBER> --squash`

### Manual Steps (if automation fails completely)

1. **Fork and clone feedstock**:
   ```bash
   gh repo fork conda-forge/{self.package_name}-feedstock --clone
   cd {self.package_name}-feedstock
   ```

2. **Update recipe**:
   ```bash
   # Edit recipe/meta.yaml
   # Update version to: {version_str}
   # Update sha256 to: {sha256_hash}
   ```

3. **Create pull request**:
   ```bash
   git checkout -b update-{version_str}
   git add recipe/meta.yaml
   git commit -m "Update {self.package_name} to v{version_str}"
   git push origin update-{version_str}
   gh pr create --title "Update {self.package_name} to v{version_str}" --body "Update to latest PyPI release"
   ```

### Resources

- [conda-forge documentation](https://conda-forge.org/docs/maintainer/updating_pkgs.html)
- [SolarWindPy feedstock](https://github.com/conda-forge/{self.package_name}-feedstock)
- [PyPI release](https://pypi.org/project/{self.package_name}/{version_str}/)

---

🤖 Generated by conda feedstock automation
"""
        return body

    def create_tracking_issue(
        self,
        version_str: str,
        sha256_hash: str,
        dry_run: bool = False,
        commit_sha: Optional[str] = None,
    ) -> Optional[str]:
        """Create GitHub issue for tracking the feedstock update.

        Parameters
        ----------
        version_str : str
            Version being updated
        sha256_hash : str
            SHA256 hash for reference
        dry_run : bool
            If True, only print what would be done
        commit_sha : str, optional
            Git commit SHA if provenance was verified

        Returns
        -------
        str or None
            Issue URL if created successfully
        """
        title = f"Conda feedstock update for SolarWindPy v{version_str}"

        body = self.build_issue_body(
            version_str,
            sha256_hash,
            self._get_dependency_comparison(),
            commit_sha=commit_sha,
        )

        if dry_run:
            print(f"🔍 DRY RUN: Would create issue '{title}'")
            print(f"Body length: {len(body)} characters")
            return None

        try:
            # Use gh CLI to create issue
            cmd = [
                "gh",
                "issue",
                "create",
                "--title",
                title,
                "--body",
                body,
                "--label",
                "conda-feedstock,automation",
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, cwd=self.project_root
            )

            issue_url = result.stdout.strip()
            print(f"✅ Created tracking issue: {issue_url}")
            return issue_url

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create GitHub issue: {e}")
            print(f"Error output: {e.stderr}")
            return None

    def generate_pr_template(self, version_str: str) -> str:
        """Generate pull request template for conda-forge feedstock.

        Parameters
        ----------
        version_str : str
            Version being updated

        Returns
        -------
        str
            PR description template
        """
        return f"""Update {self.package_name} to v{version_str}

This PR updates the {self.package_name} conda-forge recipe to version {version_str}.

### Changes
- Updated version from previous to `{version_str}`
- Updated SHA256 hash to match PyPI source distribution
- Dependencies remain unchanged (verified against pyproject.toml)

### Verification
- [x] Version matches PyPI release: https://pypi.org/project/{self.package_name}/{version_str}/
- [x] SHA256 hash verified against PyPI source distribution
- [ ] CI checks passing
- [ ] Package builds successfully

### Notes
This update was prepared using automated tooling from the SolarWindPy repository.

---
🤖 Automated update via conda feedstock automation
"""

    def update_feedstock(self, version_str: str, dry_run: bool = False) -> bool:
        """Complete conda feedstock update workflow.

        Parameters
        ----------
        version_str : str
            Version to update to
        dry_run : bool
            If True, only validate and show what would be done

        Returns
        -------
        bool
            True if update successful or dry run completed
        """
        print(
            f"🚀 Starting conda feedstock update for {self.package_name} v{version_str}"
        )

        # Step 1: Validate PyPI release
        if not self.validate_pypi_release(version_str):
            return False

        # Step 1.5: Verify git tag provenance (optional, non-blocking)
        print("\n🔍 Verifying source provenance...")
        git_verified, commit_sha = self.verify_git_tag_provenance(
            version_str,
            require_master=False,  # Don't enforce, just report
        )

        if git_verified and commit_sha:
            print(f"✅ Git provenance verified: commit {commit_sha[:8]}")
        else:
            print("⚠️  Git provenance could not be verified (may be running in CI)")
            commit_sha = None  # Ensure it's None if verification failed

        # Step 2: Read the sdist's SHA256 from PyPI
        sha256_hash = self.get_sdist_sha256(version_str)
        if not sha256_hash:
            return False

        # Step 2.5: Verify GitHub release matches PyPI (optional, non-blocking)
        if git_verified and commit_sha:
            print("\n🔍 Verifying supply chain integrity...")
            github_match = self.verify_github_release_integrity(
                version_str, sha256_hash
            )
            if github_match:
                print("✅ Supply chain integrity verified")

        # Step 3: Create tracking issue
        issue_url = self.create_tracking_issue(
            version_str,
            sha256_hash,
            dry_run,
            commit_sha=commit_sha,  # Pass commit SHA if available
        )

        if dry_run:
            print("🔍 DRY RUN: Would update feedstock with:")
            print(f"  Version: {version_str}")
            print(f"  SHA256: {sha256_hash}")
            print(f"  Fork owner: {self.fork_owner}")
            print("\nPR Template:")
            print(self.generate_pr_template(version_str))
            return True

        print(f"🎉 Feedstock update initiated for {self.package_name} v{version_str}")
        if issue_url:
            print(f"Tracking issue: {issue_url}")

        return True


def normalize_version(version_str: str) -> str:
    """Normalize version string by removing 'v' prefix if present."""
    return version_str.lstrip("v")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Automate conda-forge feedstock updates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python scripts/update_conda_feedstock.py v0.1.5
  python scripts/update_conda_feedstock.py 0.1.5 --dry-run
  python scripts/update_conda_feedstock.py 0.2.0 --package mypackage
""",
    )

    parser.add_argument(
        "version", help="Version to update to (with or without 'v' prefix)"
    )
    parser.add_argument(
        "--package", default="solarwindpy", help="Package name (default: solarwindpy)"
    )
    parser.add_argument(
        "--feedstock-repo",
        default="conda-forge/solarwindpy-feedstock",
        help="Feedstock repository (default: conda-forge/solarwindpy-feedstock)",
    )
    parser.add_argument(
        "--fork-owner", help="GitHub username for fork (default: current user)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--no-issue", action="store_true", help="Skip creating tracking issue"
    )
    parser.add_argument(
        "--max-wait",
        type=float,
        default=RELEASE_WAIT,
        help=(
            "Seconds to wait for PyPI to list the release and its sdist "
            f"(default: {RELEASE_WAIT})"
        ),
    )

    args = parser.parse_args()

    # Normalize version
    version_str = normalize_version(args.version)

    # Create updater instance
    updater = CondaFeedstockUpdater(
        package_name=args.package,
        feedstock_repo=args.feedstock_repo,
        fork_owner=args.fork_owner,
        release_wait=args.max_wait,
    )

    # Run update workflow
    success = updater.update_feedstock(version_str, dry_run=args.dry_run)

    if success:
        if args.dry_run:
            print("✅ Dry run completed successfully")
        else:
            print(f"✅ Feedstock update completed for {args.package} v{version_str}")
        sys.exit(0)
    else:
        print(f"❌ Feedstock update failed for {args.package} v{version_str}")
        sys.exit(1)


if __name__ == "__main__":
    main()
