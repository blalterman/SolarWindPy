#!/usr/bin/env python
"""Wait for PyPI package availability after publication.

This script polls PyPI to confirm a new version is available before
triggering conda-forge feedstock updates. Includes exponential backoff
and timeout handling.

Usage:
    python scripts/wait_for_pypi.py v0.1.5
    python scripts/wait_for_pypi.py 0.1.5 --timeout 600
"""

import argparse
import sys
import time
from pathlib import Path

import requests
from packaging import version

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def normalize_version(version_str: str) -> str:
    """Normalize version string by removing 'v' prefix if present.
    
    Parameters
    ----------
    version_str : str
        Version string that may or may not have 'v' prefix
        
    Returns
    -------
    str
        Version string without 'v' prefix
    """
    return version_str.lstrip('v')


def check_pypi_availability(package_name: str, version_str: str, timeout: int = 5) -> bool:
    """Check if a specific version is available on PyPI.
    
    Parameters
    ----------
    package_name : str
        Name of the package to check
    version_str : str
        Version to check for
    timeout : int, optional
        Request timeout in seconds, by default 5
        
    Returns
    -------
    bool
        True if version is available, False otherwise
    """
    url = f"https://pypi.org/pypi/{package_name}/{version_str}/json"
    
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            # Verify the version matches exactly
            return data.get('info', {}).get('version') == version_str
        return False
    except (requests.RequestException, ValueError):
        return False


def wait_for_pypi(package_name: str, version_str: str, max_wait: int = 300, 
                  check_interval: int = 30) -> bool:
    """Wait for PyPI package availability with exponential backoff.
    
    Parameters
    ----------
    package_name : str
        Name of the package to check
    version_str : str
        Version to wait for
    max_wait : int, optional
        Maximum wait time in seconds, by default 300 (5 minutes)
    check_interval : int, optional
        Initial check interval in seconds, by default 30
        
    Returns
    -------
    bool
        True if package becomes available, False if timeout
    """
    start_time = time.time()
    current_interval = check_interval
    attempt = 1
    
    print(f"Waiting for {package_name} v{version_str} on PyPI...")
    
    while time.time() - start_time < max_wait:
        print(f"Attempt {attempt}: Checking PyPI availability...")
        
        if check_pypi_availability(package_name, version_str):
            elapsed = time.time() - start_time
            print(f"✅ {package_name} v{version_str} is available on PyPI (after {elapsed:.1f}s)")
            return True
            
        remaining = max_wait - (time.time() - start_time)
        if remaining <= 0:
            break
            
        sleep_time = min(current_interval, remaining)
        print(f"⏳ Not available yet. Waiting {sleep_time}s before next check...")
        time.sleep(sleep_time)
        
        # Exponential backoff with max of 60 seconds
        current_interval = min(current_interval * 1.5, 60)
        attempt += 1
    
    print(f"❌ Timeout: {package_name} v{version_str} not available after {max_wait}s")
    return False


def validate_version(version_str: str) -> bool:
    """Validate version string format and exclude release candidates.
    
    Parameters
    ----------
    version_str : str
        Version string to validate
        
    Returns
    -------
    bool
        True if valid non-RC version, False otherwise
    """
    try:
        v = version.parse(version_str)
        if v.is_prerelease:
            print(f"❌ Release candidate detected: {version_str}")
            print("Conda feedstock updates are only triggered for stable releases")
            return False
        return True
    except Exception as e:
        print(f"❌ Invalid version format: {version_str} ({e})")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Wait for PyPI package availability",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python scripts/wait_for_pypi.py v0.1.5
  python scripts/wait_for_pypi.py 0.1.5 --timeout 600
  python scripts/wait_for_pypi.py 0.2.0 --package mypackage
"""
    )
    
    parser.add_argument(
        "version",
        help="Version to wait for (with or without 'v' prefix)"
    )
    parser.add_argument(
        "--package", 
        default="solarwindpy",
        help="Package name to check (default: solarwindpy)"
    )
    parser.add_argument(
        "--timeout", 
        type=int, 
        default=300,
        help="Maximum wait time in seconds (default: 300)"
    )
    parser.add_argument(
        "--interval", 
        type=int, 
        default=30,
        help="Initial check interval in seconds (default: 30)"
    )
    parser.add_argument(
        "--no-rc-check", 
        action="store_true",
        help="Skip release candidate validation (for testing)"
    )
    
    args = parser.parse_args()
    
    # Normalize version string
    version_str = normalize_version(args.version)
    
    # Validate version (unless disabled)
    if not args.no_rc_check and not validate_version(version_str):
        sys.exit(1)
    
    # Wait for PyPI availability
    success = wait_for_pypi(
        args.package, 
        version_str, 
        args.timeout, 
        args.interval
    )
    
    if success:
        print(f"🎉 Ready to proceed with conda feedstock update for {args.package} v{version_str}")
        sys.exit(0)
    else:
        print(f"💥 Failed to confirm PyPI availability for {args.package} v{version_str}")
        print("Manual intervention may be required.")
        sys.exit(1)


if __name__ == "__main__":
    main()
