#!/usr/bin/env python3
"""
Dynamic import testing tool for circular import detection.

This script tests actual module imports at runtime to catch circular
dependencies that might not be caught by static analysis.
"""

import sys
import os
import importlib
import importlib.util
import traceback
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
import time
import gc


class DynamicImportTester:
    """Test module imports dynamically to detect runtime circular imports."""

    def __init__(self, package_root: str):
        self.package_root = Path(package_root)
        self.package_name = self.package_root.name
        self.test_results = {}
        self.circular_imports = []
        self.import_times = {}

    def discover_modules(self) -> List[str]:
        """Discover all importable modules in the package."""
        modules = []

        for py_file in self.package_root.rglob("*.py"):
            if (
                "/tests/" in str(py_file)
                or py_file.name.startswith("test_")
                or "/__pycache__/" in str(py_file)
            ):
                continue

            rel_path = py_file.relative_to(self.package_root)
            parts = list(rel_path.with_suffix("").parts)

            if parts[-1] == "__init__":
                parts = parts[:-1]

            if parts:
                module_name = f"{self.package_name}.{'.'.join(parts)}"
            else:
                module_name = self.package_name

            modules.append(module_name)

        return sorted(modules)

    def test_individual_import(self, module_name: str) -> Dict:
        """Test importing a single module."""
        result = {
            "module": module_name,
            "success": False,
            "error": None,
            "import_time": None,
            "circular_import": False,
        }

        # Clear any previously imported modules to get a clean test
        modules_before = set(sys.modules.keys())

        try:
            start_time = time.time()
            importlib.import_module(module_name)
            end_time = time.time()

            result["success"] = True
            result["import_time"] = end_time - start_time

        except ImportError as e:
            result["error"] = str(e)
            result["success"] = False

            # Check if it's a circular import error
            if "circular" in str(e).lower() or "cannot import name" in str(e).lower():
                result["circular_import"] = True
                self.circular_imports.append(
                    {
                        "module": module_name,
                        "error": str(e),
                        "traceback": traceback.format_exc(),
                    }
                )

        except Exception as e:
            result["error"] = f"{type(e).__name__}: {str(e)}"
            result["success"] = False

        finally:
            # Clean up imported modules for next test
            modules_after = set(sys.modules.keys())
            new_modules = modules_after - modules_before

            # Don't remove core system modules
            for module in new_modules:
                if module.startswith(self.package_name) and module in sys.modules:
                    try:
                        del sys.modules[module]
                    except:
                        pass

            # Force garbage collection
            gc.collect()

        return result

    def test_import_order_variations(self, modules: List[str]) -> Dict:
        """Test different import orders to catch order-dependent circular imports."""
        print("Testing import order variations...")

        order_results = {}

        # Test a few different orderings
        import_orders = [
            "alphabetical",
            "reverse_alphabetical",
            "dependency_first",  # Try to import base modules first
            "random_sample",
        ]

        for order_name in import_orders:
            print(f"  Testing {order_name} order...")

            if order_name == "alphabetical":
                test_modules = sorted(modules)
            elif order_name == "reverse_alphabetical":
                test_modules = sorted(modules, reverse=True)
            elif order_name == "dependency_first":
                # Try to import core/base modules first
                base_modules = [
                    m
                    for m in modules
                    if any(x in m for x in ["base", "core", "__init__"])
                ]
                other_modules = [m for m in modules if m not in base_modules]
                test_modules = sorted(base_modules) + sorted(other_modules)
            else:  # random_sample
                import random

                test_modules = modules.copy()
                random.shuffle(test_modules)
                test_modules = test_modules[
                    : min(10, len(modules))
                ]  # Sample for performance

            # Clear modules before test
            self._clear_package_modules()

            order_results[order_name] = self._test_sequential_imports(test_modules)

        return order_results

    def _clear_package_modules(self):
        """Clear all package modules from sys.modules."""
        to_remove = [m for m in sys.modules if m.startswith(self.package_name)]
        for module in to_remove:
            try:
                del sys.modules[module]
            except:
                pass
        gc.collect()

    def _test_sequential_imports(self, modules: List[str]) -> Dict:
        """Test importing modules sequentially."""
        results = {
            "modules_tested": len(modules),
            "successful_imports": 0,
            "failed_imports": 0,
            "circular_imports": 0,
            "errors": [],
        }

        for module_name in modules:
            try:
                importlib.import_module(module_name)
                results["successful_imports"] += 1
            except ImportError as e:
                results["failed_imports"] += 1
                error_info = {
                    "module": module_name,
                    "error": str(e),
                    "is_circular": "circular" in str(e).lower()
                    or "cannot import name" in str(e).lower(),
                }

                if error_info["is_circular"]:
                    results["circular_imports"] += 1

                results["errors"].append(error_info)
            except Exception as e:
                results["failed_imports"] += 1
                results["errors"].append(
                    {
                        "module": module_name,
                        "error": f"{type(e).__name__}: {str(e)}",
                        "is_circular": False,
                    }
                )

        return results

    def test_cross_imports(self, modules: List[str]) -> Dict:
        """Test importing modules after other modules are already loaded."""
        print("Testing cross-import scenarios...")

        cross_results = {
            "total_tests": 0,
            "successful_cross_imports": 0,
            "failed_cross_imports": 0,
            "circular_import_errors": [],
            "other_errors": [],
        }

        # Test key module combinations
        key_modules = [
            m
            for m in modules
            if any(
                x in m for x in ["core", "__init__", "plotting", "fitfunctions", "base"]
            )
        ]

        for i, first_module in enumerate(key_modules[:5]):  # Limit for performance
            for second_module in key_modules[i + 1 : 6]:  # Test a few combinations
                self._clear_package_modules()

                cross_results["total_tests"] += 1

                try:
                    # Import first module
                    importlib.import_module(first_module)
                    # Then import second module
                    importlib.import_module(second_module)

                    cross_results["successful_cross_imports"] += 1

                except ImportError as e:
                    cross_results["failed_cross_imports"] += 1
                    error_info = {
                        "first_module": first_module,
                        "second_module": second_module,
                        "error": str(e),
                        "traceback": traceback.format_exc(),
                    }

                    if (
                        "circular" in str(e).lower()
                        or "cannot import name" in str(e).lower()
                    ):
                        cross_results["circular_import_errors"].append(error_info)
                    else:
                        cross_results["other_errors"].append(error_info)

                except Exception as e:
                    cross_results["failed_cross_imports"] += 1
                    cross_results["other_errors"].append(
                        {
                            "first_module": first_module,
                            "second_module": second_module,
                            "error": f"{type(e).__name__}: {str(e)}",
                            "traceback": traceback.format_exc(),
                        }
                    )

        return cross_results

    def run_comprehensive_test(self) -> Dict:
        """Run all dynamic import tests."""
        print("Starting comprehensive dynamic import testing...")

        modules = self.discover_modules()
        print(f"Found {len(modules)} modules to test")

        results = {
            "total_modules": len(modules),
            "individual_import_tests": [],
            "order_variation_tests": {},
            "cross_import_tests": {},
            "circular_imports_found": [],
            "summary": {},
        }

        # Test 1: Individual module imports
        print("\n1. Testing individual module imports...")
        for module in modules:
            result = self.test_individual_import(module)
            results["individual_import_tests"].append(result)
            self.test_results[module] = result

        # Test 2: Import order variations
        print("\n2. Testing import order variations...")
        results["order_variation_tests"] = self.test_import_order_variations(modules)

        # Test 3: Cross-import scenarios
        print("\n3. Testing cross-import scenarios...")
        results["cross_import_tests"] = self.test_cross_imports(modules)

        # Collect all circular imports found
        results["circular_imports_found"] = self.circular_imports

        # Generate summary
        successful_individual = sum(
            1 for r in results["individual_import_tests"] if r["success"]
        )
        failed_individual = (
            len(results["individual_import_tests"]) - successful_individual
        )
        circular_individual = sum(
            1 for r in results["individual_import_tests"] if r["circular_import"]
        )

        results["summary"] = {
            "individual_imports_successful": successful_individual,
            "individual_imports_failed": failed_individual,
            "individual_circular_imports": circular_individual,
            "cross_import_circular_errors": len(
                results["cross_import_tests"].get("circular_import_errors", [])
            ),
            "total_circular_imports_detected": len(results["circular_imports_found"]),
        }

        return results

    def save_report(
        self, results: Dict, output_file: str = "dynamic_import_test_report.txt"
    ):
        """Save detailed test report."""
        with open(output_file, "w") as f:
            f.write("SolarWindPy Dynamic Import Test Report\n")
            f.write("=" * 50 + "\n\n")

            summary = results["summary"]
            f.write(f"Total modules tested: {results['total_modules']}\n")
            f.write(
                f"Individual imports successful: {summary['individual_imports_successful']}\n"
            )
            f.write(
                f"Individual imports failed: {summary['individual_imports_failed']}\n"
            )
            f.write(
                f"Circular imports detected: {summary['total_circular_imports_detected']}\n\n"
            )

            if summary["total_circular_imports_detected"] > 0:
                f.write("⚠️  CIRCULAR IMPORTS DETECTED:\n")
                f.write("-" * 30 + "\n")
                for i, error in enumerate(results["circular_imports_found"], 1):
                    f.write(f"\n{i}. Module: {error['module']}\n")
                    f.write(f"   Error: {error['error']}\n")
                    f.write(f"   Traceback:\n")
                    for line in error["traceback"].split("\n"):
                        f.write(f"     {line}\n")
                f.write("\n")
            else:
                f.write("✅ No circular imports detected in dynamic testing!\n\n")

            # Individual test details
            f.write("Individual Import Test Results:\n")
            f.write("-" * 30 + "\n")
            for result in results["individual_import_tests"]:
                status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
                f.write(f"{result['module']}: {status}")
                if result["import_time"]:
                    f.write(f" ({result['import_time']:.4f}s)")
                if result["error"]:
                    f.write(f" - {result['error']}")
                f.write("\n")

            # Cross-import test details
            f.write(f"\nCross-Import Test Results:\n")
            f.write("-" * 30 + "\n")
            cross_results = results["cross_import_tests"]
            f.write(
                f"Total cross-import tests: {cross_results.get('total_tests', 0)}\n"
            )
            f.write(f"Successful: {cross_results.get('successful_cross_imports', 0)}\n")
            f.write(f"Failed: {cross_results.get('failed_cross_imports', 0)}\n")
            f.write(
                f"Circular import errors: {len(cross_results.get('circular_import_errors', []))}\n"
            )

            if cross_results.get("circular_import_errors"):
                f.write("\nCross-import circular errors:\n")
                for error in cross_results["circular_import_errors"]:
                    f.write(
                        f"  {error['first_module']} + {error['second_module']}: {error['error']}\n"
                    )

    def print_summary(self, results: Dict):
        """Print test summary to console."""
        summary = results["summary"]

        print("\n" + "=" * 50)
        print("DYNAMIC IMPORT TEST SUMMARY")
        print("=" * 50)
        print(f"Total modules: {results['total_modules']}")
        print(f"Successful imports: {summary['individual_imports_successful']}")
        print(f"Failed imports: {summary['individual_imports_failed']}")
        print(
            f"Circular imports detected: {summary['total_circular_imports_detected']}"
        )

        if summary["total_circular_imports_detected"] > 0:
            print("\n⚠️  CIRCULAR IMPORTS DETECTED:")
            for error in results["circular_imports_found"]:
                print(f"  {error['module']}: {error['error']}")
        else:
            print("\n✅ No circular imports detected!")


def main():
    """Main function to run dynamic import tests."""
    if len(sys.argv) > 1:
        package_root = sys.argv[1]
    else:
        script_dir = Path(__file__).parent
        package_root = script_dir.parent / "solarwindpy"

    print(f"Testing dynamic imports in: {package_root}")

    if not os.path.exists(package_root):
        print(f"Error: Package directory not found: {package_root}")
        sys.exit(1)

    # Add parent directory to Python path so imports work
    sys.path.insert(0, str(package_root.parent))

    tester = DynamicImportTester(package_root)
    results = tester.run_comprehensive_test()

    tester.print_summary(results)
    tester.save_report(results, "dynamic_import_test_report.txt")

    print(f"\nDetailed report saved to: dynamic_import_test_report.txt")


if __name__ == "__main__":
    main()
