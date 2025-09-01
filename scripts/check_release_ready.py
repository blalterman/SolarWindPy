#!/usr/bin/env python3
"""
Release Readiness Validation Script for SolarWindPy

This script validates all prerequisites for creating a release, providing
clear status indicators and actionable guidance for any missing requirements.

Usage:
    python scripts/check_release_ready.py [--verbose]
"""

import subprocess
import sys
import os
import re
from pathlib import Path
from typing import List, Tuple, Dict, Optional


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


def check_git_status() -> Tuple[bool, str]:
    """Check if working directory is clean."""
    code, stdout, stderr = run_command(["git", "status", "--porcelain"])
    if code != 0:
        return False, f"Git status failed: {stderr}"

    if stdout:
        return False, f"Working directory has uncommitted changes:\n{stdout}"

    return True, "Working directory is clean"


def check_branch() -> Tuple[bool, str]:
    """Check if on appropriate branch for release."""
    code, stdout, stderr = run_command(["git", "branch", "--show-current"])
    if code != 0:
        return False, f"Failed to get current branch: {stderr}"

    branch = stdout.strip()
    if branch in ["master", "main"]:
        return True, f"On release branch: {branch}"
    elif branch.startswith("feature/"):
        return (
            False,
            f"On feature branch '{branch}'. Switch to master/main for release.",
        )
    else:
        return True, f"On branch: {branch} (assuming valid release branch)"


def check_setuptools_scm() -> Tuple[bool, str]:
    """Check if setuptools_scm can detect version."""
    try:
        from setuptools_scm import get_version

        version = get_version()
        if "dev" in version:
            return (
                False,
                f"Development version detected: {version}. Create a tag for release.",
            )
        return True, f"Version detected: {version}"
    except ImportError:
        return False, "setuptools_scm not installed. Run: pip install setuptools_scm"
    except Exception as e:
        return False, f"Version detection failed: {e}"


def check_changelog() -> Tuple[bool, str]:
    """Check if CHANGELOG.md exists and has proper structure."""
    changelog_path = Path(__file__).parent.parent / "CHANGELOG.md"

    if not changelog_path.exists():
        return False, "CHANGELOG.md not found. Create changelog file."

    content = changelog_path.read_text()

    # Check for Keep a Changelog format
    if "## [Unreleased]" not in content:
        return (
            False,
            "CHANGELOG.md missing [Unreleased] section. Update to Keep a Changelog format.",
        )

    # Check if unreleased section has content
    unreleased_match = re.search(
        r"## \[Unreleased\]\s*\n(.*?)\n## ", content, re.DOTALL
    )
    if unreleased_match and unreleased_match.group(1).strip():
        return (
            False,
            "CHANGELOG.md has unreleased changes. Move to versioned section before release.",
        )

    return True, "CHANGELOG.md properly formatted"


def check_tests() -> Tuple[bool, str]:
    """Check if tests pass."""
    code, stdout, stderr = run_command(["python", "-m", "pytest", "-q", "--tb=no"])
    if code != 0:
        return False, f"Tests failed. Fix test failures before release:\n{stderr}"

    return True, "All tests passing"


def check_linting() -> Tuple[bool, str]:
    """Check if code passes linting."""
    code, stdout, stderr = run_command(["flake8", "--count"])
    if code != 0:
        return (
            False,
            f"Linting errors found. Fix with 'black .' and address flake8 issues:\n{stderr}",
        )

    return True, "Code passes linting"


def check_pypi_tokens() -> Tuple[bool, str]:
    """Check PyPI token configuration (informational only)."""
    # This is informational - we can't directly check token validity
    return (
        True,
        "PyPI tokens will be validated during deployment (10-day delay expected)",
    )


def check_github_access() -> Tuple[bool, str]:
    """Check GitHub repository access."""
    code, stdout, stderr = run_command(["git", "remote", "get-url", "origin"])
    if code != 0:
        return False, f"No git remote 'origin' configured: {stderr}"

    remote_url = stdout.strip()
    if "github.com" not in remote_url:
        return False, f"Origin is not a GitHub repository: {remote_url}"

    return True, f"GitHub repository configured: {remote_url}"


def check_build_system() -> Tuple[bool, str]:
    """Check if package can be built."""
    code, stdout, stderr = run_command(["python", "-m", "build", "--help"])
    if code != 0:
        return False, "Build system not available. Run: pip install build"

    return True, "Build system available"


def print_status(check_name: str, passed: bool, message: str, verbose: bool = False):
    """Print colored status message."""
    if passed:
        icon = f"{Colors.GREEN}✅{Colors.END}"
        status = f"{Colors.GREEN}PASS{Colors.END}"
    else:
        icon = f"{Colors.RED}❌{Colors.END}"
        status = f"{Colors.RED}FAIL{Colors.END}"

    print(f"{icon} {Colors.BOLD}{check_name:<30}{Colors.END} [{status}] {message}")

    if not passed and verbose:
        print(f"   {Colors.YELLOW}💡 Action needed:{Colors.END} {message}")


def print_summary(results: Dict[str, Tuple[bool, str]]):
    """Print release readiness summary."""
    passed = sum(1 for success, _ in results.values() if success)
    total = len(results)
    failed = total - passed

    print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}RELEASE READINESS SUMMARY{Colors.END}")
    print(f"{Colors.BOLD}{'='*80}{Colors.END}")

    if failed == 0:
        print(f"{Colors.GREEN}🚀 READY FOR RELEASE!{Colors.END}")
        print(
            f"{Colors.GREEN}All {total} checks passed. You can proceed with release creation.{Colors.END}"
        )
        print(f"\n{Colors.BLUE}Next steps:{Colors.END}")
        print(
            f"  1. Create release tag: python scripts/bump_version.py [major|minor|patch|rc]"
        )
        print(f"  2. Push tag: git push origin <tag>")
        print(f"  3. Monitor GitHub Actions workflow")
    else:
        print(f"{Colors.RED}❌ NOT READY FOR RELEASE{Colors.END}")
        print(f"{Colors.RED}{failed} of {total} checks failed.{Colors.END}")
        print(f"\n{Colors.YELLOW}Required actions:{Colors.END}")
        for check_name, (success, message) in results.items():
            if not success:
                print(f"  • {check_name}: {message}")

    print(f"\n{Colors.BLUE}Checks performed:{Colors.END}")
    for check_name, (success, _) in results.items():
        status = (
            f"{Colors.GREEN}✅{Colors.END}"
            if success
            else f"{Colors.RED}❌{Colors.END}"
        )
        print(f"  {status} {check_name}")


def main():
    """Main release readiness validation."""
    verbose = "--verbose" in sys.argv

    print(f"{Colors.BOLD}SolarWindPy Release Readiness Check{Colors.END}")
    print(f"{Colors.BOLD}{'='*50}{Colors.END}\n")

    # Define all checks
    checks = [
        ("Git Status", check_git_status),
        ("Branch Check", check_branch),
        ("Version Detection", check_setuptools_scm),
        ("Changelog", check_changelog),
        ("Tests", check_tests),
        ("Code Quality", check_linting),
        ("Build System", check_build_system),
        ("GitHub Access", check_github_access),
        ("PyPI Tokens", check_pypi_tokens),
    ]

    results = {}

    # Run all checks
    for check_name, check_func in checks:
        try:
            success, message = check_func()
            results[check_name] = (success, message)
            print_status(check_name, success, message, verbose)
        except Exception as e:
            results[check_name] = (False, f"Check failed with error: {e}")
            print_status(check_name, False, f"Check failed with error: {e}", verbose)

    # Print summary
    print_summary(results)

    # Exit with appropriate code
    failed_count = sum(1 for success, _ in results.values() if not success)
    sys.exit(failed_count)


if __name__ == "__main__":
    main()
