#!/usr/bin/env python3
"""
Coverage Monitor Hook for SolarWindPy
Provides detailed coverage analysis and suggestions for improvement.
"""

import subprocess
import json
import sys
from pathlib import Path


def run_coverage_analysis():
    """Run coverage analysis and return results."""
    
    print("📊 Running comprehensive coverage analysis...")
    
    try:
        # Run pytest with coverage
        result = subprocess.run([
            "pytest", 
            "--cov=solarwindpy", 
            "--cov-report=json",
            "--cov-report=term-missing",
            "-q"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            print(f"⚠️  Some tests failed during coverage analysis:")
            print(result.stdout)
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏱️  Coverage analysis timed out (>60s)")
        return False
    except FileNotFoundError:
        print("❌ pytest not found. Install with: pip install pytest pytest-cov")
        return False


def analyze_coverage_by_module():
    """Analyze coverage by module and provide specific guidance."""
    
    coverage_file = Path("coverage.json")
    if not coverage_file.exists():
        print("⚠️  Coverage report not found")
        return
    
    try:
        with open(coverage_file) as f:
            coverage_data = json.load(f)
    except Exception as e:
        print(f"⚠️  Could not parse coverage data: {e}")
        return
    
    print("\n📈 Module-specific coverage analysis:")
    
    # Define module-specific requirements
    module_requirements = {
        "solarwindpy/core": {"required": 95, "description": "Core physics calculations"},
        "solarwindpy/instabilities": {"required": 95, "description": "Instability calculations"},
        "solarwindpy/fitfunctions": {"required": 90, "description": "Curve fitting algorithms"},
        "solarwindpy/plotting": {"required": 85, "description": "Visualization tools"},
        "solarwindpy/tools": {"required": 90, "description": "Utility functions"},
        "solarwindpy/solar_activity": {"required": 85, "description": "Solar indices"}
    }
    
    files = coverage_data.get("files", {})
    
    for module_path, requirements in module_requirements.items():
        required_coverage = requirements["required"]
        description = requirements["description"]
        
        # Find files in this module
        module_files = [f for f in files.keys() if f.startswith(module_path)]
        
        if not module_files:
            print(f"   📂 {module_path}: No files found")
            continue
        
        # Calculate average coverage for module
        total_lines = 0
        covered_lines = 0
        
        for file_path in module_files:
            file_data = files[file_path]["summary"]
            total_lines += file_data["num_statements"]
            covered_lines += file_data["covered_lines"]
        
        if total_lines == 0:
            continue
            
        coverage_percent = (covered_lines / total_lines) * 100
        status = "✅" if coverage_percent >= required_coverage else "⚠️"
        
        print(f"   {status} {module_path}: {coverage_percent:.1f}% (req: {required_coverage}%)")
        print(f"      {description}")
        
        # Suggest improvements for low coverage modules
        if coverage_percent < required_coverage:
            suggest_improvements(module_path, module_files, files)


def suggest_improvements(module_path, module_files, files_data):
    """Suggest specific improvements for low coverage modules."""
    
    print(f"      💡 Improvement suggestions for {module_path}:")
    
    # Find files with lowest coverage in this module
    file_coverage = []
    for file_path in module_files:
        file_data = files_data[file_path]["summary"]
        if file_data["num_statements"] > 0:
            coverage = (file_data["covered_lines"] / file_data["num_statements"]) * 100
            file_coverage.append((file_path, coverage, file_data))
    
    # Sort by coverage (lowest first)
    file_coverage.sort(key=lambda x: x[1])
    
    # Show worst 3 files
    for file_path, coverage, file_data in file_coverage[:3]:
        if coverage < 90:  # Only show files below 90%
            missing = file_data["num_statements"] - file_data["covered_lines"]
            print(f"         - {file_path}: {coverage:.1f}% ({missing} lines missing)")
            
            # Suggest test types based on module
            if "core" in module_path:
                print(f"           → Add physics validation tests")
                print(f"           → Test edge cases (zero density, high temperature)")
            elif "fitfunctions" in module_path:
                print(f"           → Test convergence and numerical stability")
                print(f"           → Add parametrized tests for different distributions")
            elif "plotting" in module_path:
                print(f"           → Test plot generation and formatting")
                print(f"           → Add visual regression tests")


def check_critical_coverage():
    """Check coverage of critical functions."""
    
    print("\n🎯 Critical function coverage check:")
    
    critical_patterns = [
        "thermal_speed",
        "alfven_speed", 
        "coulomb_number",
        "plasma_beta",
        "instability",
        "fit_function"
    ]
    
    try:
        # Use grep to find critical functions in source
        for pattern in critical_patterns:
            result = subprocess.run([
                "grep", "-r", "--include=*.py", "--max-count=100", f"def.*{pattern}", "solarwindpy/"
            ], capture_output=True, text=True)
            
            if result.stdout:
                functions = result.stdout.strip().split('\n')
                print(f"   🔍 Found {len(functions)} functions matching '{pattern}'")
                
                # Suggest testing if not already covered
                test_result = subprocess.run([
                    "grep", "-r", "--include=*.py", "--max-count=50", f"test.*{pattern}", "tests/"
                ], capture_output=True, text=True)
                
                if not test_result.stdout:
                    print(f"      ⚠️  No tests found for {pattern} functions")
                    print(f"      💡 Consider adding tests for critical {pattern} calculations")
    
    except Exception as e:
        print(f"   ⚠️  Could not analyze critical functions: {e}")


def main():
    """Main entry point for coverage monitoring."""
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Quick mode: just run basic coverage
        success = run_coverage_analysis()
        sys.exit(0 if success else 1)
    
    # Full analysis mode
    print("🔍 Starting comprehensive coverage monitoring...")
    
    # Run coverage analysis
    success = run_coverage_analysis()
    
    if success:
        # Detailed analysis
        analyze_coverage_by_module()
        check_critical_coverage()
        
        print("\n✅ Coverage monitoring completed")
        print("💡 Use 'pytest --cov=solarwindpy --cov-report=html' for interactive report")
    else:
        print("\n❌ Coverage analysis failed")
        print("💡 Fix test failures before analyzing coverage")
        sys.exit(1)


if __name__ == "__main__":
    main()