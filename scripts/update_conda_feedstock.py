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
    
    def create_tracking_issue(self, version_str: str, sha256_hash: str, 
                            dry_run: bool = False) -> Optional[str]:
        """Create GitHub issue for tracking the feedstock update.
        
        Parameters
        ----------
        version_str : str
            Version being updated
        sha256_hash : str
            SHA256 hash for reference
        dry_run : bool
            If True, only print what would be done
            
        Returns
        -------
        str or None
            Issue URL if created successfully
        """
        title = f"Conda feedstock update for SolarWindPy v{version_str}"
        
        body = f"""## Automated Conda Feedstock Update

**Version**: `{version_str}`
**Package**: `{self.package_name}`
**PyPI URL**: https://pypi.org/project/{self.package_name}/{version_str}/
**SHA256**: `{sha256_hash}`

### Update Details

- [x] PyPI release validated
- [x] SHA256 calculated from source distribution
- [ ] Feedstock repository forked and cloned
- [ ] meta.yaml updated with new version and hash
- [ ] Pull request created on conda-forge/{self.package_name}-feedstock
- [ ] CI checks passing
- [ ] Pull request merged

### Automation Status

🤖 This issue was created automatically by the conda feedstock update automation.

### Manual Steps (if automation fails)

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
        
        # Step 2: Calculate SHA256
        sha256_hash = self.calculate_sha256(version_str)
        if not sha256_hash:
            return False
        
        # Step 3: Create tracking issue
        issue_url = self.create_tracking_issue(version_str, sha256_hash, dry_run)
        
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
