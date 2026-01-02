#!/usr/bin/env python3
"""Simple side-by-side dependency comparison.

Displays pyproject.toml dependencies next to feedstock meta.yaml
dependencies for manual review.

Usage:
    python scripts/compare_feedstock_deps.py
"""

import base64
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from typing import Optional


def extract_pyproject_deps(pyproject_path: Path = Path("pyproject.toml")) -> list[str]:
    """Extract dependencies from pyproject.toml using simple regex."""
    content = pyproject_path.read_text()

    # Find dependencies = [ ... ] section
    deps_match = re.search(
        r'dependencies\s*=\s*\[(.*?)\]',
        content,
        re.MULTILINE | re.DOTALL
    )

    if not deps_match:
        return []

    # Extract each dependency line
    deps_section = deps_match.group(1)
    deps = re.findall(r'"([^"]+)"', deps_section)

    # Strip comments and whitespace
    cleaned_deps = []
    for dep in deps:
        # Remove any trailing comments (though they shouldn't be inside quotes)
        cleaned = dep.strip()
        if cleaned:
            cleaned_deps.append(cleaned)

    return cleaned_deps


def fetch_feedstock_meta_yaml(package: str = "solarwindpy") -> Optional[str]:
    """Fetch feedstock meta.yaml from GitHub (simple urllib, no requests)."""
    url = f"https://api.github.com/repos/conda-forge/{package}-feedstock/contents/recipe/meta.yaml"

    try:
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/vnd.github.v3+json")

        # Use GITHUB_TOKEN if available
        if token := os.getenv("GITHUB_TOKEN"):
            req.add_header("Authorization", f"token {token}")

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.load(response)
            content = base64.b64decode(data["content"]).decode("utf-8")
            return content

    except Exception as e:
        print(f"⚠️  Could not fetch feedstock: {e}", file=sys.stderr)
        return None


def extract_feedstock_deps(meta_yaml_content: str) -> list[str]:
    """Extract run dependencies from meta.yaml using simple regex."""
    # Find requirements.run section (stops at first blank line or next section)
    run_match = re.search(
        r'run:\s*\n((?:    - [^\n]+\n)+)',
        meta_yaml_content,
        re.MULTILINE
    )

    if not run_match:
        return []

    # Extract each dependency line
    run_section = run_match.group(1)
    deps = re.findall(r'    - ([^\n]+)', run_section)

    # Filter out Jinja2 variables and clean
    cleaned_deps = []
    for dep in deps:
        dep = dep.strip()
        # Skip python variable lines (they start with {{)
        if not dep.startswith('{{') and dep:
            cleaned_deps.append(dep)

    return cleaned_deps


def display_side_by_side(pyproject_deps: list[str], feedstock_deps: list[str]):
    """Display dependencies side-by-side, matched by package name."""
    print("\n" + "="*80)
    print("DEPENDENCY COMPARISON")
    print("="*80)

    print(f"\n{'pyproject.toml':<40} | {'feedstock meta.yaml':<40}")
    print("-"*40 + "-+-" + "-"*40)

    # Build maps of package name -> full spec
    def get_pkg_name(dep: str) -> str:
        """Extract package name from dependency spec."""
        return dep.split(">=")[0].split("<")[0].split("==")[0].strip()

    pyproject_map = {get_pkg_name(dep): dep for dep in pyproject_deps}
    feedstock_map = {get_pkg_name(dep): dep for dep in feedstock_deps}

    # Get all unique package names
    all_packages = sorted(set(pyproject_map.keys()) | set(feedstock_map.keys()))

    # Display matched by package name
    for pkg_name in all_packages:
        left = pyproject_map.get(pkg_name, "")
        right = feedstock_map.get(pkg_name, "")

        # Determine marker
        marker = "  "
        if left and right:
            if left != right:
                marker = "⚠️"
        elif left and not right:
            marker = "➕"
        elif right and not left:
            marker = "➖"

        print(f"{marker} {left:<38} | {right:<38}")

    print("="*80)
    print("\nLegend: ⚠️ = Different  ➕ = Added in pyproject  ➖ = Only in feedstock")
    print("\n💡 Manually review differences and update feedstock if needed")


def main():
    print("🔍 Comparing SolarWindPy dependencies...\n")

    # Extract from pyproject.toml
    pyproject_deps = extract_pyproject_deps()
    print(f"✅ Found {len(pyproject_deps)} dependencies in pyproject.toml")

    # Fetch and extract from feedstock
    meta_content = fetch_feedstock_meta_yaml()
    if not meta_content:
        print("❌ Could not fetch feedstock - skipping comparison")
        print(f"\nPyproject.toml dependencies ({len(pyproject_deps)}):")
        for dep in pyproject_deps:
            print(f"  - {dep}")
        return 1

    feedstock_deps = extract_feedstock_deps(meta_content)
    print(f"✅ Found {len(feedstock_deps)} dependencies in feedstock\n")

    # Display
    display_side_by_side(pyproject_deps, feedstock_deps)

    return 0


if __name__ == "__main__":
    sys.exit(main())
