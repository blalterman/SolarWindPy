#!/usr/bin/env python3
"""
Automated Validation Hooks for SolarWindPy CI/CD Integration

This module provides hooks and integration scripts for automated physics
and MultiIndex compliance validation in CI/CD pipelines.

Usage Examples:
    # Pre-commit hook
    python automated_validation_hooks.py --hook precommit
    
    # GitHub Actions integration
    python automated_validation_hooks.py --hook github-actions
    
    # Custom pipeline integration
    python automated_validation_hooks.py --validate-changed --exit-on-error
"""

import os
import sys
import subprocess
import json
import argparse
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
import git


class ValidationHooks:
    """Automated validation hooks for CI/CD integration."""

    def __init__(self, project_root: Optional[str] = None):
        """Initialize validation hooks.

        Args:
            project_root: Path to project root directory
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.physics_validator = self.project_root / "physics_compliance_validator.py"
        self.multiindex_validator = (
            self.project_root / "multiindex_structure_validator.py"
        )

        # Validation configuration
        self.config = {
            "physics": {
                "command": str(self.physics_validator),
                "args": ["--fast", "--ci"],
                "critical": True,
                "timeout": 30,
            },
            "multiindex": {
                "command": str(self.multiindex_validator),
                "args": ["--ci", "--strict"],
                "critical": True,
                "timeout": 30,
            },
        }

    def get_changed_files(self, base_ref: str = "HEAD~1") -> List[str]:
        """Get list of changed Python files.

        Args:
            base_ref: Base reference for comparison (default: HEAD~1)

        Returns:
            List of changed Python file paths
        """
        try:
            repo = git.Repo(self.project_root)

            # Get changed files
            changed_files = []

            # Compare with base reference
            diff_files = repo.git.diff("--name-only", base_ref).splitlines()

            # Filter for Python files and documentation
            for file_path in diff_files:
                if (
                    file_path.endswith(".py")
                    or file_path.endswith(".rst")
                    or file_path.endswith(".md")
                ):
                    full_path = self.project_root / file_path
                    if full_path.exists():
                        changed_files.append(str(full_path))

            return changed_files

        except Exception as e:
            print(f"Warning: Could not determine changed files: {e}")
            # Fallback: validate core files
            return [
                "docs/source/usage.rst",
                "solarwindpy/core/plasma.py",
                "solarwindpy/tools/__init__.py",
            ]

    def run_validation(self, files: List[str], validator_type: str) -> Dict[str, Any]:
        """Run validation on specified files.

        Args:
            files: List of file paths to validate
            validator_type: Type of validator ('physics' or 'multiindex')

        Returns:
            Validation result dictionary
        """
        config = self.config[validator_type]

        # Build command
        cmd = ["python", config["command"]] + files + config["args"]

        # Run validation
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=config["timeout"],
                cwd=self.project_root,
            )

            return {
                "validator": validator_type,
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "critical": config["critical"],
            }

        except subprocess.TimeoutExpired:
            return {
                "validator": validator_type,
                "success": False,
                "stdout": "",
                "stderr": f'Validation timeout after {config["timeout"]}s',
                "return_code": -1,
                "critical": config["critical"],
            }
        except Exception as e:
            return {
                "validator": validator_type,
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "critical": config["critical"],
            }

    def validate_files(self, files: List[str]) -> Dict[str, Any]:
        """Run all validators on specified files.

        Args:
            files: List of file paths to validate

        Returns:
            Combined validation results
        """
        if not files:
            return {
                "overall_success": True,
                "message": "No files to validate",
                "results": [],
            }

        print(f"🔍 Validating {len(files)} files...")
        for file_path in files:
            print(f"   📄 {file_path}")

        # Run all validators
        results = []
        overall_success = True

        for validator_type in ["physics", "multiindex"]:
            print(f"\n⚡ Running {validator_type} validation...")

            result = self.run_validation(files, validator_type)
            results.append(result)

            if not result["success"]:
                if result["critical"]:
                    overall_success = False
                    print(f"❌ {validator_type.title()} validation FAILED (critical)")
                else:
                    print(
                        f"⚠️  {validator_type.title()} validation FAILED (non-critical)"
                    )
            else:
                print(f"✅ {validator_type.title()} validation PASSED")

        return {
            "overall_success": overall_success,
            "results": results,
            "files_validated": len(files),
        }

    def precommit_hook(self) -> int:
        """Pre-commit hook implementation.

        Returns:
            0 for success, 1 for failure
        """
        print("🚀 SolarWindPy Pre-commit Physics Validation")
        print("=" * 50)

        # Get staged files
        try:
            repo = git.Repo(self.project_root)
            staged_files = []

            # Get staged changes
            diff_files = repo.git.diff("--cached", "--name-only").splitlines()

            for file_path in diff_files:
                if file_path.endswith(".py") or file_path.endswith(".rst"):
                    full_path = self.project_root / file_path
                    if full_path.exists():
                        staged_files.append(str(full_path))

            if not staged_files:
                print("ℹ️  No Python/RST files staged for commit")
                return 0

            # Run validation
            results = self.validate_files(staged_files)

            # Report results
            print("\n" + "=" * 50)
            if results["overall_success"]:
                print("✅ ALL VALIDATIONS PASSED - Commit allowed")
                return 0
            else:
                print("❌ VALIDATION FAILURES - Commit blocked")

                # Show failure details
                for result in results["results"]:
                    if not result["success"] and result["critical"]:
                        print(f"\n🔴 {result['validator'].title()} Validation:")
                        if result["stderr"]:
                            print(f"Error: {result['stderr']}")
                        if result["stdout"]:
                            print(result["stdout"])

                print("\nℹ️  Fix validation errors and try again")
                return 1

        except Exception as e:
            print(f"❌ Pre-commit hook error: {e}")
            return 1

    def github_actions_hook(self) -> int:
        """GitHub Actions integration hook.

        Returns:
            0 for success, 1 for failure
        """
        print("🚀 SolarWindPy GitHub Actions Physics Validation")
        print("=" * 60)

        # Determine files to validate
        if os.environ.get("GITHUB_EVENT_NAME") == "pull_request":
            # PR: validate changed files
            base_sha = os.environ.get("GITHUB_BASE_REF", "main")
            try:
                changed_files = self.get_changed_files(f"origin/{base_sha}")
            except:
                # Fallback: validate key files
                changed_files = [
                    "docs/source/usage.rst",
                    "solarwindpy/core/plasma.py",
                    "solarwindpy/tools/__init__.py",
                ]
        else:
            # Push: validate key files
            changed_files = [
                "docs/source/usage.rst",
                "solarwindpy/core/plasma.py",
                "solarwindpy/tools/__init__.py",
            ]

        # Run validation
        results = self.validate_files(changed_files)

        # Create GitHub Actions output
        output_file = os.environ.get("GITHUB_OUTPUT")
        if output_file:
            with open(output_file, "a") as f:
                f.write(
                    f"validation-success={str(results['overall_success']).lower()}\\n"
                )
                f.write(f"files-validated={results['files_validated']}\\n")

        # Set step summary
        summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_file:
            with open(summary_file, "w") as f:
                f.write("# SolarWindPy Physics Validation Results\\n\\n")
                f.write(f"**Files Validated**: {results['files_validated']}\\n")
                f.write(
                    f"**Overall Status**: {'✅ PASSED' if results['overall_success'] else '❌ FAILED'}\\n\\n"
                )

                for result in results["results"]:
                    status = "✅ PASSED" if result["success"] else "❌ FAILED"
                    f.write(f"- **{result['validator'].title()}**: {status}\\n")

        return 0 if results["overall_success"] else 1

    def generate_pre_commit_config(self) -> str:
        """Generate .pre-commit-config.yaml for the project.

        Returns:
            Pre-commit configuration as YAML string
        """
        return f"""# SolarWindPy Pre-commit Configuration
repos:
  - repo: local
    hooks:
      - id: solarwindpy-physics-validation
        name: SolarWindPy Physics Validation
        entry: python automated_validation_hooks.py --hook precommit
        language: system
        types: [python]
        pass_filenames: false
        
      - id: solarwindpy-physics-quick
        name: Quick Physics Check
        entry: python physics_compliance_validator.py
        language: system
        args: [--fast, --ci]
        types: [python]
        
      - id: solarwindpy-multiindex-check  
        name: MultiIndex Structure Check
        entry: python multiindex_structure_validator.py
        language: system
        args: [--ci]
        types: [python]
"""

    def generate_github_workflow(self) -> str:
        """Generate GitHub Actions workflow YAML.

        Returns:
            GitHub Actions workflow as YAML string
        """
        return """name: Physics Compliance Validation

on:
  push:
    branches: [ master, main ]
    paths:
      - 'solarwindpy/**/*.py'
      - 'docs/source/**/*.rst'
      - 'tests/**/*.py'
  pull_request:
    branches: [ master, main ]
    paths:
      - 'solarwindpy/**/*.py'
      - 'docs/source/**/*.rst'
      - 'tests/**/*.py'

jobs:
  physics-validation:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
      with:
        fetch-depth: 0
        
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .
        pip install GitPython
        
    - name: Run Physics Validation
      id: validation
      run: |
        python automated_validation_hooks.py --hook github-actions
        
    - name: Upload validation results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: validation-results
        path: |
          compliance_report.json
          validation_report.txt
"""


def main():
    """Main entry point for validation hooks."""
    parser = argparse.ArgumentParser(
        description="SolarWindPy Automated Validation Hooks"
    )
    parser.add_argument(
        "--hook", choices=["precommit", "github-actions"], help="Run specific hook type"
    )
    parser.add_argument(
        "--validate-changed", action="store_true", help="Validate only changed files"
    )
    parser.add_argument("--files", nargs="*", help="Specific files to validate")
    parser.add_argument(
        "--exit-on-error",
        action="store_true",
        help="Exit with error code on validation failure",
    )
    parser.add_argument(
        "--generate-config",
        choices=["precommit", "github"],
        help="Generate configuration files",
    )
    parser.add_argument("--project-root", help="Project root directory")

    args = parser.parse_args()

    # Initialize hooks
    hooks = ValidationHooks(args.project_root)

    # Generate configuration files
    if args.generate_config:
        if args.generate_config == "precommit":
            print(hooks.generate_pre_commit_config())
        elif args.generate_config == "github":
            print(hooks.generate_github_workflow())
        return 0

    # Run hooks
    if args.hook == "precommit":
        return hooks.precommit_hook()
    elif args.hook == "github-actions":
        return hooks.github_actions_hook()

    # Manual validation
    files_to_validate = []

    if args.files:
        files_to_validate = args.files
    elif args.validate_changed:
        files_to_validate = hooks.get_changed_files()
    else:
        # Default: validate key files
        files_to_validate = [
            "docs/source/usage.rst",
            "solarwindpy/core/plasma.py",
            "solarwindpy/tools/__init__.py",
        ]

    # Run validation
    results = hooks.validate_files(files_to_validate)

    if not results["overall_success"] and args.exit_on_error:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
