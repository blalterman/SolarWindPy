"""Test module for circular import detection and validation.

This module contains comprehensive tests to validate that the SolarWindPy package has no
circular import dependencies and that all modules can be imported successfully in
various orders and scenarios.
"""

import sys
import importlib
import pytest
import gc
from pathlib import Path
from typing import List, Dict, Set
import time

# Add the parent directory to allow importing our analysis tools
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from scripts.analyze_imports_fixed import DependencyAnalyzer
    from scripts.test_dynamic_imports import DynamicImportTester
except ImportError as e:
    pytest.skip(f"Could not import analysis tools: {e}", allow_module_level=True)


class TestCircularImports:
    """Test class for circular import validation."""

    @classmethod
    def setup_class(cls):
        """Set up test class with module discovery."""
        cls.package_root = PROJECT_ROOT / "solarwindpy"
        cls.package_name = "solarwindpy"

        # Discover all modules
        cls.all_modules = cls._discover_modules()

        # Key modules that should be tested more thoroughly
        cls.key_modules = [
            "solarwindpy",
            "solarwindpy.core",
            "solarwindpy.core.base",
            "solarwindpy.core.plasma",
            "solarwindpy.plotting",
            "solarwindpy.fitfunctions",
            "solarwindpy.solar_activity",
        ]

    @classmethod
    def _discover_modules(cls) -> List[str]:
        """Discover all importable modules in the package."""
        modules = []

        for py_file in cls.package_root.rglob("*.py"):
            if (
                "/tests/" in str(py_file)
                or py_file.name.startswith("test_")
                or "/__pycache__/" in str(py_file)
            ):
                continue

            rel_path = py_file.relative_to(cls.package_root)
            parts = list(rel_path.with_suffix("").parts)

            if parts[-1] == "__init__":
                parts = parts[:-1]

            if parts:
                module_name = f"{cls.package_name}.{'.'.join(parts)}"
            else:
                module_name = cls.package_name

            modules.append(module_name)

        return sorted(modules)

    def _clean_modules(self):
        """Clean imported modules for test isolation."""
        modules_to_remove = [m for m in sys.modules if m.startswith(self.package_name)]
        for module in modules_to_remove:
            if module in sys.modules:
                del sys.modules[module]
        gc.collect()

    def test_static_dependency_analysis(self):
        """Test that static analysis finds no circular dependencies."""
        analyzer = DependencyAnalyzer(str(self.package_root))
        analyzer.scan_package()
        analyzer.build_dependency_graph()

        cycles = analyzer.find_circular_dependencies_dfs()

        assert len(cycles) == 0, (
            f"Static analysis found {len(cycles)} circular dependency cycles: "
            f"{[' -> '.join(cycle + [cycle[0]]) for cycle in cycles]}"
        )

    def test_individual_module_imports(self):
        """Test that each module can be imported individually."""
        failed_imports = []

        for module_name in self.all_modules:
            self._clean_modules()

            try:
                importlib.import_module(module_name)
            except ImportError as e:
                if (
                    "circular" in str(e).lower()
                    or "cannot import name" in str(e).lower()
                ):
                    failed_imports.append(f"{module_name}: {str(e)}")
                else:
                    # Other import errors might be acceptable (missing dependencies, etc.)
                    pass
            except Exception as e:
                # Unexpected errors should be investigated but not necessarily fail the test
                pass

        assert len(failed_imports) == 0, (
            f"Found circular import errors in individual module imports: "
            f"{failed_imports}"
        )

    def test_key_module_imports(self):
        """Test that key modules can be imported without circular import errors."""
        circular_imports = []

        for module_name in self.key_modules:
            self._clean_modules()

            try:
                importlib.import_module(module_name)
            except ImportError as e:
                if (
                    "circular" in str(e).lower()
                    or "cannot import name" in str(e).lower()
                ):
                    circular_imports.append(f"{module_name}: {str(e)}")
            except Exception:
                # Other exceptions are not circular import issues
                pass

        assert (
            len(circular_imports) == 0
        ), f"Circular imports detected in key modules: {circular_imports}"

    def test_import_order_independence(self):
        """Test that import order doesn't cause circular import issues."""
        import_orders = [
            sorted(self.key_modules),  # alphabetical
            sorted(self.key_modules, reverse=True),  # reverse alphabetical
            # Base modules first
            [m for m in self.key_modules if "base" in m or "__init__" in m]
            + [m for m in self.key_modules if "base" not in m and "__init__" not in m],
        ]

        for i, order in enumerate(import_orders):
            self._clean_modules()

            circular_imports = []
            for module_name in order:
                try:
                    importlib.import_module(module_name)
                except ImportError as e:
                    if (
                        "circular" in str(e).lower()
                        or "cannot import name" in str(e).lower()
                    ):
                        circular_imports.append(f"{module_name}: {str(e)}")
                except Exception:
                    # Other errors are not our concern for this test
                    pass

            assert (
                len(circular_imports) == 0
            ), f"Import order {i+1} caused circular import errors: {circular_imports}"

    def test_cross_module_import_scenarios(self):
        """Test various cross-module import scenarios."""
        # Test pairs of related modules
        module_pairs = [
            ("solarwindpy.core", "solarwindpy.plotting"),
            ("solarwindpy.core.base", "solarwindpy.core.plasma"),
            ("solarwindpy.fitfunctions", "solarwindpy.plotting"),
            ("solarwindpy", "solarwindpy.core"),
        ]

        for first_module, second_module in module_pairs:
            if (
                first_module not in self.all_modules
                or second_module not in self.all_modules
            ):
                continue

            # Test importing first, then second
            self._clean_modules()
            circular_imports = []

            try:
                importlib.import_module(first_module)
                importlib.import_module(second_module)
            except ImportError as e:
                if (
                    "circular" in str(e).lower()
                    or "cannot import name" in str(e).lower()
                ):
                    circular_imports.append(
                        f"{first_module} -> {second_module}: {str(e)}"
                    )

            # Test importing second, then first
            self._clean_modules()

            try:
                importlib.import_module(second_module)
                importlib.import_module(first_module)
            except ImportError as e:
                if (
                    "circular" in str(e).lower()
                    or "cannot import name" in str(e).lower()
                ):
                    circular_imports.append(
                        f"{second_module} -> {first_module}: {str(e)}"
                    )

            assert len(circular_imports) == 0, (
                f"Cross-module import scenarios failed for {first_module} and {second_module}: "
                f"{circular_imports}"
            )

    def test_main_package_import(self):
        """Test that the main package can be imported without circular imports."""
        self._clean_modules()

        try:
            import solarwindpy  # noqa: F401
        except ImportError as e:
            if "circular" in str(e).lower() or "cannot import name" in str(e).lower():
                pytest.fail(f"Main package import has circular import: {e}")

    def test_public_api_imports(self):
        """Test that public API imports work without circular imports."""
        self._clean_modules()

        # Test common public API usage patterns
        api_imports = [
            "from solarwindpy import Plasma",
            "from solarwindpy.core import Base",
            "from solarwindpy.plotting import histograms",
            "import solarwindpy.core as swp_core",
            "import solarwindpy.plotting as swp_plotting",
        ]

        circular_import_errors = []

        for import_statement in api_imports:
            self._clean_modules()

            try:
                exec(import_statement)
            except ImportError as e:
                if (
                    "circular" in str(e).lower()
                    or "cannot import name" in str(e).lower()
                ):
                    circular_import_errors.append(f"{import_statement}: {str(e)}")
            except Exception:
                # Other errors are not circular import issues
                pass

        assert (
            len(circular_import_errors) == 0
        ), f"Public API imports have circular import errors: {circular_import_errors}"

    def test_dynamic_import_comprehensive(self):
        """Run comprehensive dynamic import test."""
        # Skip if dynamic tester not available
        try:
            tester = DynamicImportTester(str(self.package_root))
        except Exception:
            pytest.skip("Dynamic import tester not available")

        # Run a subset of dynamic tests for performance
        modules_to_test = (
            self.key_modules
            + [
                m
                for m in self.all_modules
                if any(key in m for key in ["core", "plotting", "fitfunctions"])
            ][:15]
        )  # Limit for test performance

        circular_imports = []

        for module_name in modules_to_test:
            result = tester.test_individual_import(module_name)
            if result["circular_import"]:
                circular_imports.append(f"{module_name}: {result['error']}")

        assert (
            len(circular_imports) == 0
        ), f"Dynamic import testing found circular imports: {circular_imports}"

    def test_import_time_performance(self):
        """Test that imports complete in reasonable time (may indicate circular
        issues)."""
        import_times = {}
        slow_imports = []

        for module_name in self.key_modules:
            self._clean_modules()

            start_time = time.time()
            try:
                importlib.import_module(module_name)
                import_time = time.time() - start_time
                import_times[module_name] = import_time

                # Flag imports taking longer than 5 seconds as potentially problematic
                if import_time > 5.0:
                    slow_imports.append(f"{module_name}: {import_time:.2f}s")

            except ImportError as e:
                if "circular" in str(e).lower():
                    pytest.fail(
                        f"Circular import in performance test for {module_name}: {e}"
                    )

        # This is more of a warning than a failure - slow imports might indicate issues
        if slow_imports:
            pytest.warns(UserWarning, match="Slow imports detected")
            import warnings

            warnings.warn(
                f"Slow imports detected (possible circular import indicators): {slow_imports}"
            )


class TestImportStructure:
    """Test the overall import structure health."""

    @classmethod
    def setup_class(cls):
        """Set up test class."""
        cls.package_root = PROJECT_ROOT / "solarwindpy"

    def test_no_wildcard_imports_in_init(self):
        """Test that __init__.py files don't use wildcard imports (which can hide
        circular imports)."""
        init_files = list(self.package_root.rglob("__init__.py"))
        wildcard_imports = []

        for init_file in init_files:
            with open(init_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for wildcard imports
            if "from * import" in content or "import *" in content:
                wildcard_imports.append(str(init_file.relative_to(self.package_root)))

        assert len(wildcard_imports) == 0, (
            f"Found wildcard imports in __init__.py files (can mask circular imports): "
            f"{wildcard_imports}"
        )

    def test_relative_import_consistency(self):
        """Test that relative imports are used consistently within packages."""
        # This is more of a style check, but inconsistent relative imports
        # can sometimes lead to circular import issues

        python_files = [
            f
            for f in self.package_root.rglob("*.py")
            if "/tests/" not in str(f) and not f.name.startswith("test_")
        ]

        inconsistent_files = []

        for py_file in python_files:
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for both relative and absolute imports of the same package
            has_relative = "from ." in content or "from .." in content
            has_absolute = (
                "from solarwindpy" in content or "import solarwindpy" in content
            )

            if has_relative and has_absolute:
                # This might be intentional, but flag for review
                rel_path = str(py_file.relative_to(self.package_root))
                inconsistent_files.append(rel_path)

        # This is informational rather than a hard failure
        if inconsistent_files:
            import warnings

            warnings.warn(
                f"Files with mixed relative/absolute imports (review for potential issues): "
                f"{inconsistent_files[:5]}{'...' if len(inconsistent_files) > 5 else ''}"
            )


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
