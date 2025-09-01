#!/usr/bin/env python3
"""
Validation framework for executing and testing code examples.

This module provides infrastructure for systematically executing code examples
from documentation with error capture, timeout handling, and result validation.
"""

import sys
import io
import traceback
import time
import json
import signal
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import matplotlib

matplotlib.use("Agg")  # Non-interactive backend for CI compatibility

# Import validation modules
from extract_examples import CodeExample, ExampleInventory


@dataclass
class ExecutionResult:
    """Result of code example execution."""

    success: bool
    execution_time: float
    stdout: str = ""
    stderr: str = ""
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    traceback: Optional[str] = None
    outputs: Dict[str, Any] = None

    def __post_init__(self):
        if self.outputs is None:
            self.outputs = {}


class TimeoutException(Exception):
    """Raised when code execution exceeds timeout."""

    pass


class IsolatedExecutor:
    """Execute code examples in isolated environments with error capture."""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.global_namespace = self._create_base_namespace()

    def _create_base_namespace(self) -> Dict[str, Any]:
        """Create base namespace with common imports."""
        namespace = {
            "__builtins__": __builtins__,
            "__name__": "__main__",
        }

        # Pre-import common modules to avoid repeated imports
        try:
            import numpy as np
            import pandas as pd
            import solarwindpy as swp
            import matplotlib.pyplot as plt

            namespace.update({"np": np, "pd": pd, "swp": swp, "plt": plt})
        except ImportError as e:
            print(f"Warning: Could not pre-import module: {e}")

        return namespace

    def _timeout_handler(self, signum, frame):
        """Handle execution timeout."""
        raise TimeoutException(f"Code execution exceeded {self.timeout} seconds")

    def execute_example(self, example: CodeExample) -> ExecutionResult:
        """Execute a single code example with error capture."""
        start_time = time.time()

        # Create isolated namespace (copy of base)
        local_namespace = self.global_namespace.copy()

        # Capture stdout/stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        try:
            # Set up timeout handler
            if hasattr(signal, "SIGALRM"):  # Unix systems only
                signal.signal(signal.SIGALRM, self._timeout_handler)
                signal.alarm(int(self.timeout))

            # Execute code with output capture
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(example.code, local_namespace, local_namespace)

            # Cancel timeout
            if hasattr(signal, "SIGALRM"):
                signal.alarm(0)

            execution_time = time.time() - start_time

            # Extract outputs (variables created during execution)
            outputs = {}
            for key, value in local_namespace.items():
                if not key.startswith("_") and key not in self.global_namespace:
                    try:
                        # Only capture serializable outputs
                        json.dumps(str(value))  # Test serializability
                        outputs[key] = value
                    except:
                        outputs[key] = f"<{type(value).__name__} object>"

            return ExecutionResult(
                success=True,
                execution_time=execution_time,
                stdout=stdout_capture.getvalue(),
                stderr=stderr_capture.getvalue(),
                outputs=outputs,
            )

        except TimeoutException:
            if hasattr(signal, "SIGALRM"):
                signal.alarm(0)
            return ExecutionResult(
                success=False,
                execution_time=self.timeout,
                stdout=stdout_capture.getvalue(),
                stderr=stderr_capture.getvalue(),
                error_type="TimeoutError",
                error_message=f"Execution exceeded {self.timeout} seconds",
            )

        except Exception as e:
            if hasattr(signal, "SIGALRM"):
                signal.alarm(0)

            execution_time = time.time() - start_time
            return ExecutionResult(
                success=False,
                execution_time=execution_time,
                stdout=stdout_capture.getvalue(),
                stderr=stderr_capture.getvalue(),
                error_type=type(e).__name__,
                error_message=str(e),
                traceback=traceback.format_exc(),
            )


class ImportValidator:
    """Validate that all imports in examples can be resolved."""

    def __init__(self):
        self.cache = {}  # Cache import resolution results

    def validate_imports(self, dependencies: List[str]) -> Dict[str, Any]:
        """Check if all imports can be resolved."""
        results = {
            "all_imports_valid": True,
            "import_details": {},
            "missing_imports": [],
            "import_errors": [],
        }

        for import_name in dependencies:
            if import_name in self.cache:
                results["import_details"][import_name] = self.cache[import_name]
                continue

            try:
                # Try to import the module/function
                parts = import_name.split(".")
                if len(parts) == 1:
                    __import__(import_name)
                else:
                    module_name = ".".join(parts[:-1])
                    attr_name = parts[-1]
                    module = __import__(module_name, fromlist=[attr_name])
                    getattr(module, attr_name)

                result = {"available": True, "error": None}
                self.cache[import_name] = result
                results["import_details"][import_name] = result

            except ImportError as e:
                result = {"available": False, "error": f"ImportError: {str(e)}"}
                self.cache[import_name] = result
                results["import_details"][import_name] = result
                results["missing_imports"].append(import_name)
                results["all_imports_valid"] = False

            except AttributeError as e:
                result = {"available": False, "error": f"AttributeError: {str(e)}"}
                self.cache[import_name] = result
                results["import_details"][import_name] = result
                results["import_errors"].append(import_name)
                results["all_imports_valid"] = False

        return results


class ValidationReporter:
    """Generate comprehensive validation reports."""

    def __init__(self):
        self.results = []

    def add_result(
        self,
        example: CodeExample,
        execution_result: ExecutionResult,
        import_result: Dict[str, Any],
    ) -> None:
        """Add validation result for an example."""
        self.results.append(
            {
                "example_id": example.example_id,
                "file_path": example.file_path,
                "line_range": f"{example.line_start}-{example.line_end}",
                "example_type": example.example_type,
                "execution_success": execution_result.success,
                "execution_time": execution_result.execution_time,
                "error_type": execution_result.error_type,
                "error_message": execution_result.error_message,
                "has_stdout": bool(execution_result.stdout),
                "has_stderr": bool(execution_result.stderr),
                "imports_valid": import_result["all_imports_valid"],
                "missing_imports": import_result["missing_imports"],
                "import_errors": import_result["import_errors"],
                "outputs_count": len(execution_result.outputs),
                "timestamp": time.time(),
            }
        )

    def generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics."""
        total = len(self.results)
        if total == 0:
            return {"total_examples": 0}

        successful = sum(1 for r in self.results if r["execution_success"])
        import_failures = sum(1 for r in self.results if not r["imports_valid"])

        error_types = {}
        for result in self.results:
            if result["error_type"]:
                error_types[result["error_type"]] = (
                    error_types.get(result["error_type"], 0) + 1
                )

        avg_execution_time = sum(r["execution_time"] for r in self.results) / total

        return {
            "total_examples": total,
            "successful_executions": successful,
            "success_rate": successful / total * 100,
            "import_failures": import_failures,
            "common_error_types": dict(
                sorted(error_types.items(), key=lambda x: x[1], reverse=True)
            ),
            "average_execution_time": avg_execution_time,
            "examples_with_output": sum(
                1 for r in self.results if r["outputs_count"] > 0
            ),
        }

    def save_report(self, output_path: Path) -> None:
        """Save detailed validation report."""
        report = {
            "validation_timestamp": time.time(),
            "summary": self.generate_summary(),
            "detailed_results": self.results,
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"Validation report saved to {output_path}")


class ExampleValidator:
    """Main validation orchestrator."""

    def __init__(self, timeout: float = 30.0):
        self.executor = IsolatedExecutor(timeout)
        self.import_validator = ImportValidator()
        self.reporter = ValidationReporter()

    def validate_example(self, example: CodeExample) -> Dict[str, Any]:
        """Validate a single example comprehensively."""
        print(f"Validating {example.example_id}...")

        # Skip bash examples for now
        if example.example_type == "bash":
            return {"skipped": True, "reason": "Bash examples not currently supported"}

        # Validate imports
        import_result = self.import_validator.validate_imports(example.dependencies)

        # Execute example
        execution_result = self.executor.execute_example(example)

        # Record results
        self.reporter.add_result(example, execution_result, import_result)

        return {
            "success": execution_result.success,
            "imports_valid": import_result["all_imports_valid"],
            "execution_time": execution_result.execution_time,
            "error": (
                execution_result.error_message if not execution_result.success else None
            ),
        }

    def validate_all_from_inventory(self, inventory_path: Path) -> None:
        """Validate all examples from inventory file."""
        with open(inventory_path, "r") as f:
            inventory_data = json.load(f)

        examples = []
        example_id = 0

        # Process RST documentation files
        for file_path, file_data in inventory_data.get(
            "rst_documentation_files", {}
        ).items():
            for i, code_block in enumerate(file_data.get("code_blocks", [])):
                # Skip bash examples for now
                if code_block.get("type", "").endswith("bash"):
                    continue

                example_id += 1
                line_ranges = file_data.get("line_ranges", [[0, 0]])
                line_range = line_ranges[i] if i < len(line_ranges) else [0, 0]

                example = CodeExample(
                    code=code_block["content"],
                    file_path=file_path,
                    line_start=line_range[0],
                    line_end=line_range[1],
                    example_type="rst_code_block",
                    example_id=f"rst_example_{example_id}",
                )
                example.dependencies = code_block.get("dependencies", [])
                examples.append(example)

        # Process README.rst examples
        for file_path, file_data in inventory_data.get("readme_rst", {}).items():
            for i, code_block in enumerate(file_data.get("code_blocks", [])):
                # Skip bash examples for now
                if code_block.get("type", "").endswith("bash"):
                    continue

                example_id += 1
                line_ranges = file_data.get("line_ranges", [[0, 0]])
                line_range = line_ranges[i] if i < len(line_ranges) else [0, 0]

                example = CodeExample(
                    code=code_block["content"],
                    file_path=file_path,
                    line_start=line_range[0],
                    line_end=line_range[1],
                    example_type="readme_code_block",
                    example_id=f"readme_example_{example_id}",
                )
                example.dependencies = code_block.get("dependencies", [])
                examples.append(example)

        # Process Python docstring examples
        for file_path, file_data in inventory_data.get(
            "python_docstring_examples", {}
        ).items():
            for i, doctest_block in enumerate(file_data.get("doctest_blocks", [])):
                example_id += 1
                line_ranges = file_data.get("line_ranges", [[0, 0]])
                line_range = line_ranges[i] if i < len(line_ranges) else [0, 0]

                example = CodeExample(
                    code=doctest_block["content"],
                    file_path=file_path,
                    line_start=line_range[0],
                    line_end=line_range[1],
                    example_type="doctest",
                    example_id=f"doctest_example_{example_id}",
                )
                example.dependencies = doctest_block.get("dependencies", [])
                examples.append(example)

        print(f"Validating {len(examples)} examples...")

        for example in examples:
            try:
                self.validate_example(example)
            except Exception as e:
                print(f"Error validating {example.example_id}: {e}")

        # Generate final report
        summary = self.reporter.generate_summary()
        print(f"\nValidation Summary:")
        print(f"Total examples: {summary['total_examples']}")
        print(
            f"Successful: {summary['successful_executions']} ({summary.get('success_rate', 0):.1f}%)"
        )
        print(f"Import failures: {summary['import_failures']}")
        print(
            f"Average execution time: {summary.get('average_execution_time', 0):.2f}s"
        )

        if summary.get("common_error_types"):
            print("Most common errors:")
            for error_type, count in list(summary["common_error_types"].items())[:3]:
                print(f"  {error_type}: {count}")


if __name__ == "__main__":
    # Test the validation framework
    validator = ExampleValidator(timeout=30.0)

    # Check if inventory exists
    inventory_path = Path("docs_audit_inventory.json")
    if inventory_path.exists():
        validator.validate_all_from_inventory(inventory_path)
        validator.reporter.save_report(Path("validation_results.json"))
    else:
        print(f"Inventory file not found: {inventory_path}")
        print("Run extract_examples.py first to create the inventory.")
