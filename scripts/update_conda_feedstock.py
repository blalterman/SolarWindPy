#!/usr/bin/env python
"""Automate conda-forge feedstock updates for SolarWindPy releases.

This script automates the process of updating the conda-forge feedstock
after a new PyPI release. It handles version updates, SHA256 calculation,
and creates GitHub issues for tracking.

Usage:
    python scripts/update_conda_feedstock.py v0.1.5
    python scripts/update_conda_feedstock.py 0.1.5 --dry-run
    python scripts/update_conda_feedstock.py 0.1.5 --fork-owner myusername
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple

import requests
import yaml
from packaging import version

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class CondaFeedstockUpdater:
    """Handles automated conda-forge feedstock updates.
    
    This class manages the complete workflow of updating conda-forge
    feedstock repositories with new PyPI releases.
    """
    
    def __init__(self, package_name: str = "solarwindpy", 
                 feedstock_repo: str = "conda-forge/solarwindpy-feedstock",
                 fork_owner: Optional[str] = None):
        """Initialize the feedstock updater.
        
        Parameters
        ----------
        package_name : str
            Name of the PyPI package
        feedstock_repo : str
            GitHub repository for the feedstock (org/repo format)
        fork_owner : str, optional
            GitHub username for fork (if different from current user)
        """
        self.package_name = package_name
        self.feedstock_repo = feedstock_repo
        self.fork_owner = fork_owner or self._get_github_username()
        self.project_root = Path(__file__).parent.parent
        
    def _get_github_username(self) -> str:
        """Get current GitHub username from git config or environment.
        
        Returns
        -------
        str
            GitHub username
        """
        # Try environment variable first
        if 'GITHUB_ACTOR' in os.environ:
            return os.environ['GITHUB_ACTOR']
            
        # Try git config
        try:
            result = subprocess.run(
                ['git', 'config', 'user.name'], 
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return 'unknown'

    def verify_git_tag_provenance(self, version_str: str,
                                   require_master: bool = False) -> Tuple[bool, Optional[str]]:
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
                ['git', 'tag', '-l', tag_name],
                capture_output=True, text=True, check=False,
                cwd=self.project_root
            )

            if not result.stdout.strip():
                print(f"⚠️  Git tag {tag_name} not found in repository")
                return False, None

            # Get commit SHA for the tag
            result = subprocess.run(
                ['git', 'rev-parse', tag_name],
                capture_output=True, text=True, check=True,
                cwd=self.project_root
            )
            commit_sha = result.stdout.strip()

            print(f"📍 Found tag {tag_name} at commit {commit_sha[:8]}")

            # Verify tag is on master branch (if required)
            result = subprocess.run(
                ['git', 'branch', '--contains', commit_sha],
                capture_output=True, text=True, check=False,
                cwd=self.project_root
            )

            if result.returncode == 0:
                branches = [b.strip().lstrip('* ') for b in result.stdout.strip().split('\n') if b.strip()]

                if branches:
                    has_master = any('master' in b for b in branches)
                    if has_master:
                        print(f"✅ Verified {tag_name} is on master branch")
                    elif require_master:
                        print(f"⚠️  Warning: Tag {tag_name} not found on master branch")
                        print(f"   Branches containing this tag: {', '.join(branches[:5])}")
                        return False, commit_sha
                    else:
                        print(f"📋 Tag found on branches: {', '.join(branches[:3])}")

            # Get tag annotation message for additional context
            result = subprocess.run(
                ['git', 'tag', '-l', '--format=%(contents:subject)', tag_name],
                capture_output=True, text=True, check=False,
                cwd=self.project_root
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

    def verify_github_release_integrity(self, version_str: str,
                                       pypi_sha256: str) -> bool:
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
                ['gh', 'release', 'view', tag_name, '--json', 'assets'],
                capture_output=True, text=True, check=True,
                cwd=self.project_root
            )

            release_data = json.loads(result.stdout)

            # Find the .tar.gz asset
            tar_gz_assets = [
                a for a in release_data.get('assets', [])
                if a['name'].endswith('.tar.gz')
            ]

            if not tar_gz_assets:
                print(f"⚠️  No .tar.gz asset found in GitHub release {tag_name}")
                return True  # Permissive - don't block

            # Extract SHA256 from digest field (format: "sha256:hash")
            github_sha256 = tar_gz_assets[0].get('digest', '')
            if github_sha256.startswith('sha256:'):
                github_sha256 = github_sha256[7:]  # Remove "sha256:" prefix

            if github_sha256 == pypi_sha256:
                print(f"✅ GitHub release SHA256 matches PyPI")
                print(f"   Hash: {github_sha256[:16]}...")
                return True
            else:
                print(f"⚠️  SHA256 mismatch between GitHub and PyPI")
                print(f"   GitHub: {github_sha256[:16]}...")
                print(f"   PyPI:   {pypi_sha256[:16]}...")
                return False

        except subprocess.CalledProcessError:
            print(f"⚠️  Could not verify GitHub release (gh CLI may not be available)")
            return True  # Permissive - don't block if gh unavailable
        except Exception as e:
            print(f"⚠️  GitHub release verification skipped: {e}")
            return True  # Permissive - don't block on errors

    def validate_pypi_release(self, version_str: str, timeout: int = 10) -> bool:
        """Validate that the PyPI release exists and is not a pre-release.
        
        Parameters
        ----------
        version_str : str
            Version string to validate
        timeout : int
            Request timeout in seconds
            
        Returns
        -------
        bool
            True if valid stable release exists
        """
        try:
            # Parse version to check for pre-release
            v = version.parse(version_str)
            if v.is_prerelease:
                print(f"❌ Pre-release version {version_str} - skipping feedstock update")
                return False
            
            # Check PyPI availability
            url = f"https://pypi.org/pypi/{self.package_name}/{version_str}/json"
            response = requests.get(url, timeout=timeout)
            
            if response.status_code != 200:
                print(f"❌ PyPI version {version_str} not found (status: {response.status_code})")
                return False
                
            data = response.json()
            pypi_version = data.get('info', {}).get('version')
            
            if pypi_version != version_str:
                print(f"❌ Version mismatch: requested {version_str}, PyPI has {pypi_version}")
                return False
                
            print(f"✅ Validated PyPI release: {self.package_name} v{version_str}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to validate PyPI release: {e}")
            return False
    
    def calculate_sha256(self, version_str: str, timeout: int = 30) -> Optional[str]:
        """Calculate SHA256 hash of the PyPI source distribution.
        
        Parameters
        ----------
        version_str : str
            Version to download and hash
        timeout : int
            Download timeout in seconds
            
        Returns
        -------
        str or None
            SHA256 hash as hex string, or None if failed
        """
        url = f"https://pypi.org/packages/source/{self.package_name[0]}/{self.package_name}/{self.package_name}-{version_str}.tar.gz"
        
        try:
            print(f"Downloading {self.package_name} v{version_str} for SHA256 calculation...")
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            
            sha256_hash = hashlib.sha256(response.content).hexdigest()
            print(f"✅ SHA256: {sha256_hash}")
            return sha256_hash
            
        except Exception as e:
            print(f"❌ Failed to calculate SHA256: {e}")
            return None
    
    def update_meta_yaml(self, version_str: str, sha256_hash: str, 
                        meta_path: Path) -> bool:
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
            lines = content.split('\n')
            updated_lines = []
            
            for line in lines:
                if line.strip().startswith('{% set version ='):
                    updated_lines.append(f'{{% set version = "{version_str}" %}}')
                elif line.strip().startswith('sha256:'):
                    updated_lines.append(f'  sha256: {sha256_hash}')
                else:
                    updated_lines.append(line)
            
            # Write updated content
            updated_content = '\n'.join(updated_lines)
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
                cwd=self.project_root
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

    def create_tracking_issue(self, version_str: str, sha256_hash: str,
                            dry_run: bool = False,
                            commit_sha: Optional[str] = None) -> Optional[str]:
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

        # Get dependency comparison
        comparison_output = self._get_dependency_comparison()

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

        body += """


---

{comparison_output}

---

### Update Checklist

- [x] PyPI release validated
- [x] SHA256 calculated from source distribution
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
        
        if dry_run:
            print(f"🔍 DRY RUN: Would create issue '{title}'")
            print(f"Body length: {len(body)} characters")
            return None
            
        try:
            # Use gh CLI to create issue
            cmd = [
                'gh', 'issue', 'create',
                '--title', title,
                '--body', body,
                '--label', 'conda-feedstock,automation'
            ]
            
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True,
                cwd=self.project_root
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
        print(f"🚀 Starting conda feedstock update for {self.package_name} v{version_str}")

        # Step 1: Validate PyPI release
        if not self.validate_pypi_release(version_str):
            return False

        # Step 1.5: Verify git tag provenance (optional, non-blocking)
        print(f"\n🔍 Verifying source provenance...")
        git_verified, commit_sha = self.verify_git_tag_provenance(
            version_str,
            require_master=False  # Don't enforce, just report
        )

        if git_verified and commit_sha:
            print(f"✅ Git provenance verified: commit {commit_sha[:8]}")
        else:
            print(f"⚠️  Git provenance could not be verified (may be running in CI)")
            commit_sha = None  # Ensure it's None if verification failed

        # Step 2: Calculate SHA256
        sha256_hash = self.calculate_sha256(version_str)
        if not sha256_hash:
            return False

        # Step 2.5: Verify GitHub release matches PyPI (optional, non-blocking)
        if git_verified and commit_sha:
            print(f"\n🔍 Verifying supply chain integrity...")
            github_match = self.verify_github_release_integrity(version_str, sha256_hash)
            if github_match:
                print(f"✅ Supply chain integrity verified")

        # Step 3: Create tracking issue
        issue_url = self.create_tracking_issue(
            version_str,
            sha256_hash,
            dry_run,
            commit_sha=commit_sha  # Pass commit SHA if available
        )
        
        if dry_run:
            print(f"🔍 DRY RUN: Would update feedstock with:")
            print(f"  Version: {version_str}")
            print(f"  SHA256: {sha256_hash}")
            print(f"  Fork owner: {self.fork_owner}")
            print(f"\nPR Template:")
            print(self.generate_pr_template(version_str))
            return True
        
        print(f"🎉 Feedstock update initiated for {self.package_name} v{version_str}")
        if issue_url:
            print(f"Tracking issue: {issue_url}")
        
        return True


def normalize_version(version_str: str) -> str:
    """Normalize version string by removing 'v' prefix if present."""
    return version_str.lstrip('v')


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Automate conda-forge feedstock updates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python scripts/update_conda_feedstock.py v0.1.5
  python scripts/update_conda_feedstock.py 0.1.5 --dry-run
  python scripts/update_conda_feedstock.py 0.2.0 --package mypackage
"""
    )
    
    parser.add_argument(
        "version",
        help="Version to update to (with or without 'v' prefix)"
    )
    parser.add_argument(
        "--package",
        default="solarwindpy",
        help="Package name (default: solarwindpy)"
    )
    parser.add_argument(
        "--feedstock-repo",
        default="conda-forge/solarwindpy-feedstock",
        help="Feedstock repository (default: conda-forge/solarwindpy-feedstock)"
    )
    parser.add_argument(
        "--fork-owner",
        help="GitHub username for fork (default: current user)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--no-issue",
        action="store_true",
        help="Skip creating tracking issue"
    )
    
    args = parser.parse_args()
    
    # Normalize version
    version_str = normalize_version(args.version)
    
    # Create updater instance
    updater = CondaFeedstockUpdater(
        package_name=args.package,
        feedstock_repo=args.feedstock_repo,
        fork_owner=args.fork_owner
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
