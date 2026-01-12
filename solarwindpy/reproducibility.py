"""Reproducibility utilities for tracking package versions and git state."""

import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_git_info(repo_path=None):
    """Get git commit info for a repository.

    Parameters
    ----------
    repo_path : Path, str, None
        Path to git repository. If None, uses solarwindpy's location.

    Returns
    -------
    dict
        Keys: 'sha', 'short_sha', 'dirty', 'branch', 'path'
    """
    if repo_path is None:
        import solarwindpy

        repo_path = Path(solarwindpy.__file__).parent.parent

    repo_path = Path(repo_path)

    try:
        sha = (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )

        short_sha = sha[:7]

        dirty = (
            subprocess.call(
                ["git", "diff", "--quiet"],
                cwd=repo_path,
                stderr=subprocess.DEVNULL,
            )
            != 0
        )

        branch = (
            subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )

    except (subprocess.CalledProcessError, FileNotFoundError):
        sha = "unknown"
        short_sha = "unknown"
        dirty = None
        branch = "unknown"

    return {
        "sha": sha,
        "short_sha": short_sha,
        "dirty": dirty,
        "branch": branch,
        "path": str(repo_path),
    }


def get_info():
    """Get comprehensive reproducibility info.

    Returns
    -------
    dict
        Keys: 'timestamp', 'python', 'solarwindpy_version', 'git', 'dependencies'
    """
    import solarwindpy

    git_info = get_git_info()

    # Key dependencies
    deps = {}
    for pkg in ["numpy", "scipy", "pandas", "matplotlib", "astropy"]:
        try:
            mod = __import__(pkg)
            deps[pkg] = mod.__version__
        except ImportError:
            deps[pkg] = "not installed"

    return {
        "timestamp": datetime.now().isoformat(),
        "python": sys.version.split()[0],
        "solarwindpy_version": solarwindpy.__version__,
        "git": git_info,
        "dependencies": deps,
    }


def print_info():
    """Print reproducibility info. Call at start of notebooks."""
    info = get_info()
    git = info["git"]

    print("=" * 60)
    print("REPRODUCIBILITY INFO")
    print("=" * 60)
    print(f"Timestamp: {info['timestamp']}")
    print(f"Python: {info['python']}")
    print(f"solarwindpy: {info['solarwindpy_version']}")
    print(f"  SHA: {git['sha']}")
    print(f"  Branch: {git['branch']}")
    if git["dirty"]:
        print("  WARNING: Uncommitted changes present!")
    print(f"  Path: {git['path']}")
    print("-" * 60)
    print("Key dependencies:")
    for pkg, ver in info["dependencies"].items():
        print(f"  {pkg}: {ver}")
    print("=" * 60)


def get_citation_string():
    """Get a citation string for methods sections.

    Returns
    -------
    str
        Formatted string suitable for paper methods section.
    """
    info = get_info()
    git = info["git"]
    dirty = " (with local modifications)" if git["dirty"] else ""
    return (
        f"Analysis performed with solarwindpy {info['solarwindpy_version']} "
        f"(commit {git['short_sha']}{dirty}) using Python {info['python']}."
    )
