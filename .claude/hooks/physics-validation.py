#!/usr/bin/env python3
"""Physics Validation Hook for SolarWindPy Auto-validates physics constraints after code
edits."""

import sys
import re
import os


def validate_physics(filepath):
    """Check physics constraints in modified file."""

    if not os.path.exists(filepath):
        print(f"⚠️  File not found: {filepath}")
        return

    try:
        with open(filepath, "r") as f:
            content = f.read()
    except Exception as e:
        print(f"⚠️  Could not read file {filepath}: {e}")
        return

    violations = []
    suggestions = []

    # Check thermal speed convention
    if "thermal_speed" in content or "w_thermal" in content:
        if not re.search(r"2\s*\*\s*(k_B|kB)\s*\*\s*T\s*/\s*m", content):
            violations.append("Thermal speed should use mw² = 2kT convention")
            suggestions.append("Use: w_thermal = np.sqrt(2 * k_B * T / m)")

    # Check Alfvén speed formula
    if "alfven" in content.lower() or "v_a" in content.lower():
        if not re.search(r"B\s*/\s*.*sqrt.*mu_?0.*rho", content):
            violations.append("Alfvén speed should use V_A = B/√(μ₀ρ)")
            suggestions.append("Include ion composition: ρ = Σ(n_i * m_i)")

    # Check unit consistency
    if any(word in content.lower() for word in ["convert", "unit", "si", "cgs"]):
        if "units_constants" not in content:
            violations.append("Unit conversion without units_constants import")
            suggestions.append("from solarwindpy.tools import units_constants")

    # Check for proper missing data handling
    missing_data_patterns = [
        (r"==\s*0(?!\.\d)", "Use NaN for missing data, not 0"),
        (r"==\s*-999", "Use NaN for missing data, not -999"),
        (r"\.fillna\(0\)", "Avoid filling NaN with 0 for physical quantities"),
    ]

    for pattern, message in missing_data_patterns:
        if re.search(pattern, content):
            violations.append(message)
            suggestions.append("Use: np.nan or pd.isna() for missing data checks")

    # Check for physical constraints
    if "temperature" in content.lower() or "density" in content.lower():
        # Look for potential negative value issues
        if re.search(r"[Tt]emperature.*-", content) or re.search(
            r"[Dd]ensity.*-", content
        ):
            violations.append("Check for negative temperatures or densities")
            suggestions.append("Add validation: assert temperature > 0, density > 0")

    # Check for speed of light violations
    if any(word in content.lower() for word in ["velocity", "speed", "v_bulk"]):
        if "c =" in content or "speed_of_light" in content:
            violations.append("Verify velocities don't exceed speed of light")
            suggestions.append("Add check: assert np.all(v < c)")

    # Check DataFrame MultiIndex usage
    if "DataFrame" in content or "MultiIndex" in content:
        if not re.search(r"\.xs\(", content) and "columns" in content:
            violations.append("Consider using .xs() for MultiIndex DataFrame access")
            suggestions.append("Use: df.xs('v', level='M') instead of column filtering")

    # Report results
    if violations:
        print(f"⚠️  Physics validation warnings for {filepath}:")
        for i, violation in enumerate(violations):
            print(f"   {i+1}. {violation}")
            if i < len(suggestions):
                print(f"      💡 {suggestions[i]}")
        print()
    else:
        print(f"✅ Physics validation passed for {filepath}")


def main():
    """Main entry point for physics validation hook."""

    # Handle documented flags by treating them as no-ops for now
    if len(sys.argv) >= 2 and sys.argv[1] in [
        "--strict",
        "--report",
        "--fix",
        "--help",
    ]:
        # These flags are documented but not yet implemented
        # Exit cleanly to avoid breaking hook chains
        if sys.argv[1] == "--help":
            print("Usage: physics-validation.py [--strict|--report|--fix] <filepath>")
        sys.exit(0)

    if len(sys.argv) < 2:
        # No filepath provided - skip validation silently for hook compatibility
        sys.exit(0)

    filepath = sys.argv[1]

    # Input validation - sanitize filepath
    if re.search(r"[;&|`$()<>]", filepath):
        print(f"⚠️  Invalid characters in filepath: {filepath}")
        sys.exit(1)

    # Prevent directory traversal
    if "../" in filepath or filepath.startswith("/"):
        print(f"⚠️  Invalid filepath (directory traversal): {filepath}")
        sys.exit(1)

    # Only validate Python files in relevant directories
    if not filepath.endswith(".py"):
        print(f"⏭️  Skipping non-Python file: {filepath}")
        return

    # Check if file is in relevant directories
    relevant_dirs = [
        "solarwindpy/core",
        "solarwindpy/instabilities",
        "solarwindpy/fitfunctions",
        "solarwindpy/tools",
    ]

    if not any(rel_dir in filepath for rel_dir in relevant_dirs):
        print(f"⏭️  Skipping file outside physics modules: {filepath}")
        return

    print(f"🔬 Running physics validation on: {filepath}")
    validate_physics(filepath)


if __name__ == "__main__":
    main()
