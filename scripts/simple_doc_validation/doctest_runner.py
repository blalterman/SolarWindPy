#!/usr/bin/env python3
"""Simple doctest runner for SolarWindPy (47 examples)"""

import doctest
import sys
import json
import warnings
from pathlib import Path
from typing import Dict, Any
import importlib.util


class SimpleDocTestRunner:
    """Lightweight doctest runner"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = {
            "files_processed": 0,
            "total_tests": 0,
            "failed_tests": 0,
            "examples_run": 0,
            "files": [],
        }

    def run_file(self, file_path: Path) -> Dict[str, Any]:
        """Run doctests on a single Python file"""
        result = {
            "file": str(file_path),
            "tests_attempted": 0,
            "tests_failed": 0,
            "examples_run": 0,
            "success": True,
            "errors": [],
        }

        try:
            if file_path.suffix != ".py":
                return result

            spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
            if not spec or not spec.loader:
                result["errors"].append(f"Could not load {file_path}")
                result["success"] = False
                return result

            module = importlib.util.module_from_spec(spec)

            with warnings.catch_warnings():
                warnings.filterwarnings("ignore")
                try:
                    spec.loader.exec_module(module)
                except Exception as e:
                    result["errors"].append(f"Import error: {e}")
                    result["success"] = False
                    return result

                finder = doctest.DocTestFinder()
                runner = doctest.DocTestRunner(verbose=self.verbose)

                for test in finder.find(module):
                    if test.examples:
                        test_result = runner.run(test)
                        result["tests_attempted"] += test_result.attempted
                        result["tests_failed"] += test_result.failed
                        result["examples_run"] += len(test.examples)

            result["success"] = (
                result["tests_failed"] == 0 or result["tests_attempted"] == 0
            )

        except Exception as e:
            result["errors"].append(str(e))
            result["success"] = False

        return result

    def run_directory(self, directory: Path, targeted: bool = False) -> Dict[str, Any]:
        """Run doctests on all Python files in directory"""
        python_files = [
            f
            for f in directory.rglob("*.py")
            if "__pycache__" not in str(f) and not f.name.startswith(".")
        ]

        if targeted:
            # Focus on critical modules for sustainable validation
            critical_paths = ["core/", "instabilities/"]
            important_paths = ["plotting/", "fitfunctions/"]

            critical_files = [
                f for f in python_files if any(p in str(f) for p in critical_paths)
            ]
            important_files = [
                f for f in python_files if any(p in str(f) for p in important_paths)
            ]

            # Process critical files first, then important ones
            files_to_process = critical_files + important_files

            if self.verbose:
                print(
                    f"Targeted validation: {len(critical_files)} critical, {len(important_files)} important files"
                )
        else:
            files_to_process = python_files

        for py_file in files_to_process:
            if self.verbose:
                priority = (
                    "CRITICAL"
                    if any(p in str(py_file) for p in ["core/", "instabilities/"])
                    else (
                        "IMPORTANT"
                        if any(
                            p in str(py_file) for p in ["plotting/", "fitfunctions/"]
                        )
                        else "OPTIONAL"
                    )
                )
                print(f"Testing [{priority}] {py_file}")

            file_result = self.run_file(py_file)
            self.results["files"].append(file_result)
            self.results["files_processed"] += 1
            self.results["total_tests"] += file_result["tests_attempted"]
            self.results["failed_tests"] += file_result["tests_failed"]
            self.results["examples_run"] += file_result["examples_run"]

        return self.results

    def generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        success_rate = (
            (self.results["total_tests"] - self.results["failed_tests"])
            / max(self.results["total_tests"], 1)
        ) * 100

        return {
            "summary": {
                "files_processed": self.results["files_processed"],
                "total_tests": self.results["total_tests"],
                "failed_tests": self.results["failed_tests"],
                "examples_run": self.results["examples_run"],
                "success_rate": success_rate,
                "overall_success": self.results["failed_tests"] == 0,
            },
            "files": self.results["files"],
        }


def main():
    """Command-line interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Simple doctest runner for SolarWindPy"
    )
    parser.add_argument("path", help="Path to Python file or directory")
    parser.add_argument("--output-report", help="JSON output file")
    parser.add_argument("--text-report", help="Text report file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--targeted",
        action="store_true",
        help="Run targeted validation (core/instabilities priority)",
    )

    args = parser.parse_args()

    runner = SimpleDocTestRunner(verbose=args.verbose)
    path = Path(args.path)

    if path.is_dir():
        runner.run_directory(path, targeted=args.targeted)
    else:
        result = runner.run_file(path)
        runner.results = {
            "files_processed": 1,
            "total_tests": result["tests_attempted"],
            "failed_tests": result["tests_failed"],
            "examples_run": result["examples_run"],
            "files": [result],
        }

    summary = runner.generate_summary()

    if args.output_report:
        with open(args.output_report, "w") as f:
            json.dump(summary, f, indent=2)

    # Generate text report
    s = summary["summary"]
    text_report = f"""SolarWindPy Doctest Validation Report
=============================================

Files processed: {s['files_processed']}
Total tests: {s['total_tests']}
Failed tests: {s['failed_tests']}
Examples run: {s['examples_run']}
Success rate: {s['success_rate']:.1f}%

"""

    for file_info in summary["files"]:
        status = "✅ PASS" if file_info["success"] else "❌ FAIL"
        text_report += (
            f"{status} {file_info['file']} ({file_info['tests_attempted']} tests)\n"
        )

    if s["failed_tests"] == 0:
        text_report += "\n✅ All tests passed!"

    if args.text_report:
        with open(args.text_report, "w") as f:
            f.write(text_report)

    if args.verbose:
        print(text_report)

    sys.exit(0 if s["overall_success"] else 1)


if __name__ == "__main__":
    main()
