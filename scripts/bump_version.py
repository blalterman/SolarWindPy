#!/usr/bin/env python3
"""
Semantic Version Bump Script for SolarWindPy

This script creates semantic version tags following the v{major}.{minor}.{patch}
format with optional prerelease suffixes (rc, beta, alpha).

Usage:
    python scripts/bump_version.py [major|minor|patch|rc|beta|alpha] [--dry-run] [--from-version VERSION]
    
Examples:
    python scripts/bump_version.py patch          # 1.0.0 -> 1.0.1
    python scripts/bump_version.py minor          # 1.0.0 -> 1.1.0
    python scripts/bump_version.py major          # 1.0.0 -> 2.0.0
    python scripts/bump_version.py rc             # 1.0.0 -> 1.0.1-rc1
    python scripts/bump_version.py rc --from-version 1.0.0  # Explicit base version
    python scripts/bump_version.py patch --dry-run  # Show what would happen
"""

import subprocess
import sys
import re
import argparse
from pathlib import Path
from typing import List, Tuple, Optional
from packaging import version


# Color codes for terminal output
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def run_command(cmd: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return 1, "", f"Command not found: {' '.join(cmd)}"


def get_latest_version() -> Optional[str]:
    """Get the latest version tag from git."""
    code, stdout, stderr = run_command(
        ["git", "tag", "-l", "v*", "--sort=-version:refname"]
    )
    if code != 0:
        print(f"{Colors.RED}Failed to get git tags: {stderr}{Colors.END}")
        return None

    tags = [line.strip() for line in stdout.split("\n") if line.strip()]

    # Filter out compaction tags and find latest release tag
    release_tags = [
        tag for tag in tags if tag.startswith("v") and not "compaction" in tag
    ]

    if not release_tags:
        return None

    return release_tags[0]


def parse_version(
    version_string: str,
) -> Tuple[int, int, int, Optional[str], Optional[int]]:
    """Parse a version string into components.

    Returns: (major, minor, patch, prerelease_type, prerelease_number)
    """
    # Remove 'v' prefix if present
    if version_string.startswith("v"):
        version_string = version_string[1:]

    # Match semantic version with optional prerelease
    pattern = r"^(\d+)\.(\d+)\.(\d+)(?:-(alpha|beta|rc)(\d*))?$"
    match = re.match(pattern, version_string)

    if not match:
        raise ValueError(f"Invalid version format: {version_string}")

    major, minor, patch, prerelease_type, prerelease_num = match.groups()

    return (
        int(major),
        int(minor),
        int(patch),
        prerelease_type,
        int(prerelease_num) if prerelease_num else None,
    )


def bump_version(current_version: str, bump_type: str) -> str:
    """Bump version according to semantic versioning rules."""
    major, minor, patch, prerelease_type, prerelease_num = parse_version(
        current_version
    )

    if bump_type == "major":
        return f"v{major + 1}.0.0"
    elif bump_type == "minor":
        return f"v{major}.{minor + 1}.0"
    elif bump_type == "patch":
        if prerelease_type:
            # If current is prerelease, bump to release
            return f"v{major}.{minor}.{patch}"
        else:
            # Normal patch bump
            return f"v{major}.{minor}.{patch + 1}"
    elif bump_type in ["rc", "beta", "alpha"]:
        if prerelease_type == bump_type:
            # Bump prerelease number
            next_num = (prerelease_num or 0) + 1
            return f"v{major}.{minor}.{patch}-{bump_type}{next_num}"
        elif prerelease_type:
            # Switch prerelease type
            return f"v{major}.{minor}.{patch}-{bump_type}1"
        else:
            # Add prerelease to current version
            return f"v{major}.{minor}.{patch + 1}-{bump_type}1"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")


def validate_version_progression(current: str, new: str) -> bool:
    """Validate that new version is a proper progression from current."""
    try:
        # Remove 'v' prefix for comparison
        current_clean = current[1:] if current.startswith("v") else current
        new_clean = new[1:] if new.startswith("v") else new

        current_ver = version.parse(current_clean)
        new_ver = version.parse(new_clean)

        return new_ver > current_ver
    except Exception:
        return False


def check_working_directory() -> bool:
    """Check if working directory is clean."""
    code, stdout, stderr = run_command(["git", "status", "--porcelain"])
    if code != 0:
        print(f"{Colors.RED}Failed to check git status: {stderr}{Colors.END}")
        return False

    if stdout:
        print(f"{Colors.RED}Working directory has uncommitted changes:{Colors.END}")
        print(stdout)
        print(
            f"{Colors.YELLOW}Commit or stash changes before creating a release tag.{Colors.END}"
        )
        return False

    return True


def create_tag(tag_name: str, dry_run: bool = False) -> bool:
    """Create a git tag."""
    if dry_run:
        print(f"{Colors.BLUE}[DRY RUN] Would create tag: {tag_name}{Colors.END}")
        return True

    # Create annotated tag
    code, stdout, stderr = run_command(
        ["git", "tag", "-a", tag_name, "-m", f"Release {tag_name}"]
    )

    if code != 0:
        print(f"{Colors.RED}Failed to create tag: {stderr}{Colors.END}")
        return False

    print(f"{Colors.GREEN}✅ Created tag: {tag_name}{Colors.END}")

    # Show next steps
    print(f"\n{Colors.BLUE}Next steps:{Colors.END}")
    print(f"  1. Push tag: git push origin {tag_name}")
    print(
        f"  2. Monitor GitHub Actions: https://github.com/blalterman/SolarWindPy/actions"
    )
    print(f"  3. Check release: https://github.com/blalterman/SolarWindPy/releases")

    return True


def main():
    """Main version bump script."""
    parser = argparse.ArgumentParser(
        description="Bump SolarWindPy version following semantic versioning"
    )
    parser.add_argument(
        "bump_type",
        choices=["major", "minor", "patch", "rc", "beta", "alpha"],
        help="Type of version bump",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes",
    )
    parser.add_argument(
        "--from-version",
        type=str,
        help="Specify base version instead of auto-detecting from git tags",
    )

    args = parser.parse_args()

    print(f"{Colors.BOLD}SolarWindPy Version Bump{Colors.END}")
    print(f"{Colors.BOLD}{'='*40}{Colors.END}\n")

    # Check working directory unless dry run
    if not args.dry_run and not check_working_directory():
        sys.exit(1)

    # Get current version
    if args.from_version:
        current_version = args.from_version
        if not current_version.startswith("v"):
            current_version = f"v{current_version}"
        print(f"{Colors.BLUE}Using specified version: {current_version}{Colors.END}")
    else:
        current_version = get_latest_version()
        if not current_version:
            print(
                f"{Colors.YELLOW}No existing version tags found. Starting from v0.0.0{Colors.END}"
            )
            current_version = "v0.0.0"
        else:
            print(f"{Colors.BLUE}Current version: {current_version}{Colors.END}")

    # Calculate new version
    try:
        new_version = bump_version(current_version, args.bump_type)
        print(f"{Colors.GREEN}New version: {new_version}{Colors.END}")
    except ValueError as e:
        print(f"{Colors.RED}Error: {e}{Colors.END}")
        sys.exit(1)

    # Validate progression
    if not validate_version_progression(current_version, new_version):
        print(
            f"{Colors.RED}Error: Invalid version progression from {current_version} to {new_version}{Colors.END}"
        )
        sys.exit(1)

    # Show version details
    try:
        major, minor, patch, prerelease_type, prerelease_num = parse_version(
            new_version
        )
        print(f"\n{Colors.BOLD}Version Details:{Colors.END}")
        print(f"  Major: {major}")
        print(f"  Minor: {minor}")
        print(f"  Patch: {patch}")
        if prerelease_type:
            print(f"  Prerelease: {prerelease_type}{prerelease_num or ''}")
            print(f"  {Colors.YELLOW}Note: This is a prerelease version{Colors.END}")
    except ValueError as e:
        print(f"{Colors.RED}Error parsing new version: {e}{Colors.END}")
        sys.exit(1)

    # Create the tag
    if create_tag(new_version, args.dry_run):
        if not args.dry_run:
            print(f"\n{Colors.GREEN}🎉 Version bump complete!{Colors.END}")
        else:
            print(
                f"\n{Colors.BLUE}Dry run complete. Use without --dry-run to create the tag.{Colors.END}"
            )
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
