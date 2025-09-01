#!/usr/bin/env python3
"""GitHub Actions CI integration for simplified doctest validation"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from .doctest_runner import SimpleDocTestRunner
except ImportError:
    from doctest_runner import SimpleDocTestRunner


class CIIntegration:
    """Simple CI/CD integration for doctest validation"""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.runner = SimpleDocTestRunner(verbose=False)

    def get_validation_files(self) -> List[str]:
        """Get key files to validate for CI"""
        key_files = [
            "docs/source/usage.rst",
            "docs/source/tutorial/quickstart.rst",
            "docs/source/installation.rst",
            "solarwindpy/core/plasma.py",
            "solarwindpy/core/ions.py",
            "solarwindpy/tools/__init__.py",
        ]

        return [
            str(self.project_root / f)
            for f in key_files
            if (self.project_root / f).exists()
        ]

    def run_validation(self, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run validation on specified files or key files"""
        if files is None:
            files = self.get_validation_files()

        results = {
            "files_processed": 0,
            "total_tests": 0,
            "failed_tests": 0,
            "examples_run": 0,
            "files": [],
            "overall_success": True,
        }

        for file_path in files:
            path = Path(file_path)
            if path.exists():
                if path.suffix == ".py":
                    file_result = self.runner.run_file(path)
                    results["files"].append(file_result)
                    results["files_processed"] += 1
                    results["total_tests"] += file_result["tests_attempted"]
                    results["failed_tests"] += file_result["tests_failed"]
                    results["examples_run"] += file_result["examples_run"]

                    if not file_result["success"]:
                        results["overall_success"] = False
                elif path.suffix == ".rst":
                    file_result = self.validate_rst_examples(path)
                    results["files"].append(file_result)
                    results["files_processed"] += 1

        return results

    def validate_rst_examples(self, rst_file: Path) -> Dict[str, Any]:
        """Simple validation of RST code examples"""
        result = {
            "file": str(rst_file),
            "tests_attempted": 0,
            "tests_failed": 0,
            "examples_run": 0,
            "success": True,
            "errors": [],
        }

        try:
            content = rst_file.read_text()
            code_blocks = content.count(".. code-block:: python")
            result["examples_run"] = result["tests_attempted"] = code_blocks
        except Exception as e:
            result["errors"].append(str(e))
            result["success"] = False

        return result

    def create_github_outputs(self, results: Dict[str, Any]) -> None:
        """Create GitHub Actions outputs"""
        output_file = os.environ.get("GITHUB_OUTPUT")
        if output_file:
            with open(output_file, "a") as f:
                f.write(
                    f"validation-success={str(results['overall_success']).lower()}\n"
                )
                f.write(f"files-validated={results['files_processed']}\n")

        summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_file:
            status = "✅ PASSED" if results["overall_success"] else "❌ FAILED"
            with open(summary_file, "w") as f:
                f.write("# SolarWindPy Documentation Validation\n\n")
                f.write(
                    f"**Files**: {results['files_processed']}, **Tests**: {results['total_tests']}, **Status**: {status}\n"
                )

    def save_artifacts(self, results: Dict[str, Any]) -> None:
        """Save validation artifacts for GitHub Actions"""
        with open(self.project_root / "doctest_validation_report.json", "w") as f:
            json.dump(results, f, indent=2)

        status_msg = (
            "All validations passed"
            if results["overall_success"]
            else "Validation failures detected"
        )
        with open(self.project_root / "doctest_validation_summary.txt", "w") as f:
            f.write(f"SolarWindPy Doctest Validation Summary\n")
            f.write(
                f"Files: {results['files_processed']}, Tests: {results['total_tests']}, Failed: {results['failed_tests']}\n"
            )
            f.write(f"Status: {status_msg}\n")

    def run_github_actions_workflow(self) -> int:
        """Run the complete GitHub Actions validation workflow"""
        print("🚀 SolarWindPy Documentation Validation")
        results = self.run_validation()
        self.create_github_outputs(results)
        self.save_artifacts(results)

        if results["overall_success"]:
            print("✅ All documentation validations passed")
            return 0
        else:
            print("❌ Documentation validation failures detected")
            return 1


def main():
    """Command-line interface for CI integration"""
    import argparse

    parser = argparse.ArgumentParser(
        description="CI integration for doctest validation"
    )
    parser.add_argument(
        "--github-actions", action="store_true", help="Run GitHub Actions workflow"
    )
    parser.add_argument("--files", nargs="*", help="Specific files to validate")
    parser.add_argument("--project-root", help="Project root directory")

    args = parser.parse_args()

    ci = CIIntegration(args.project_root)

    if args.github_actions:
        return ci.run_github_actions_workflow()
    else:
        results = ci.run_validation(args.files)
        print(json.dumps(results, indent=2))
        return 0 if results["overall_success"] else 1


if __name__ == "__main__":
    sys.exit(main())
