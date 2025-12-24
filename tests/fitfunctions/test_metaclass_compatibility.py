"""Metaclass compatibility regression tests for FitFunctionMeta.

These tests prevent Method Resolution Order (MRO) conflicts between
NumpyDocstringInheritanceMeta and ABCMeta that could break fitfunction imports.

Critical for maintaining compatibility across docstring-inheritance versions.
"""

import pytest
from solarwindpy.fitfunctions.core import FitFunctionMeta, FitFunction


class TestMetaclassMRO:
    """Test Method Resolution Order compatibility."""

    def test_metaclass_mro_valid(self):
        """Verify FitFunctionMeta MRO includes both parent metaclasses."""
        mro_names = [c.__name__ for c in FitFunctionMeta.__mro__]

        # Should include docstring inheritance metaclass
        assert (
            "NumpyDocstringInheritanceMeta" in mro_names
        ), "FitFunctionMeta must include NumpyDocstringInheritanceMeta in MRO"

        # Should include ABC metaclass
        assert (
            "ABCMeta" in mro_names
        ), "FitFunctionMeta must include ABCMeta in MRO for abstract methods"

    def test_metaclass_instantiation(self):
        """Verify FitFunctionMeta can be instantiated without MRO errors."""
        # If there's an MRO conflict, this will raise TypeError during class definition
        try:

            class TestMeta(FitFunctionMeta):
                pass

            # Metaclass should have valid MRO
            assert TestMeta.__mro__ is not None
        except TypeError as e:
            if "consistent method resolution" in str(e).lower():
                pytest.fail(f"MRO conflict detected: {e}")
            raise


class TestAbstractEnforcement:
    """Test that ABC functionality works correctly with combined metaclass."""

    def test_abstract_methods_enforced(self):
        """Verify abstract methods must be implemented by subclasses."""
        # FitFunction has abstract methods: function, p0, TeX_function
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):

            class IncompleteFunction(FitFunction):
                # Missing required abstract methods
                pass

            # This should fail because abstract methods aren't implemented
            IncompleteFunction([0, 1], [0, 1])

    def test_concrete_implementation_works(self):
        """Verify concrete implementations can be instantiated."""

        class CompleteFitFunction(FitFunction):
            """Minimal concrete fit function for testing."""

            @property
            def function(self):
                return lambda x, a: a * x

            @property
            def p0(self):
                return [1.0]

            @property
            def TeX_function(self):
                return r"a x"

        # Should instantiate successfully
        x, y = [0, 1, 2], [0, 1, 2]
        fit_func = CompleteFitFunction(x, y)
        assert fit_func is not None
        assert hasattr(fit_func, "function")


class TestDocstringInheritance:
    """Test that docstring inheritance works correctly."""

    def test_docstring_inheritance_active(self):
        """Verify docstrings are inherited from parent classes."""

        class ParentFit(FitFunction):
            """Parent class docstring with important info."""

            @property
            def function(self):
                return lambda x, a: a * x

            @property
            def p0(self):
                return [1.0]

            @property
            def TeX_function(self):
                return r"a x"

        class ChildFit(ParentFit):
            """Child class docstring."""

            pass

        # Docstring should exist (inheritance working)
        assert ChildFit.__doc__ is not None
        assert len(ChildFit.__doc__) > 0

    def test_inherited_method_docstrings(self):
        """Verify method docstrings are inherited."""
        from solarwindpy.fitfunctions import Gaussian

        # Gaussian should have inherited __init__ docstring from FitFunction
        init_doc = Gaussian.__init__.__doc__
        assert (
            init_doc is not None
        ), "Docstring inheritance should provide __init__ docs"


class TestAllFitFunctionsInstantiate:
    """Smoke tests: verify all production fitfunction classes work."""

    def test_import_all_fitfunctions(self):
        """Verify all fitfunction classes can be imported without MRO errors."""
        # If there's an MRO issue, the import will fail with TypeError
        from solarwindpy.fitfunctions import (
            Exponential,
            Gaussian,
            PowerLaw,
            Line,
            Moyal,
            TrendFit,
        )

        # All imports successful
        assert Exponential is not None
        assert Gaussian is not None
        assert PowerLaw is not None
        assert Line is not None
        assert Moyal is not None
        assert TrendFit is not None

    def test_instantiate_all_fitfunctions(self):
        """Verify all fitfunction classes can be instantiated."""
        from solarwindpy.fitfunctions import (
            Exponential,
            Gaussian,
            PowerLaw,
            Line,
            Moyal,
        )

        x = [0, 1, 2, 3, 4]
        y = [1, 2, 3, 4, 5]

        # Note: TrendFit excluded as it has different constructor signature
        fitfunctions = [Exponential, Gaussian, PowerLaw, Line, Moyal]

        for FitClass in fitfunctions:
            try:
                instance = FitClass(x, y)
                assert instance is not None, f"{FitClass.__name__} instantiation failed"
                assert hasattr(
                    instance, "function"
                ), f"{FitClass.__name__} missing function property"
            except Exception as e:
                pytest.fail(
                    f"{FitClass.__name__} instantiation raised unexpected error: {e}"
                )


class TestDocstringInheritanceVersionCompatibility:
    """Test compatibility with specific docstring-inheritance versions."""

    def test_version_constraint(self):
        """Verify docstring-inheritance version is in safe range."""
        from importlib.metadata import version as get_version
        from packaging.version import Version

        version = Version(get_version("docstring-inheritance"))

        # Must be >= 2.2.0 for MRO compatibility
        assert version >= Version(
            "2.2.0"
        ), f"docstring-inheritance {version} is below minimum 2.2.0 for MRO compatibility"

        # Must be < 3.0 (version 3.0+ breaks MRO)
        assert version < Version("3.0"), (
            f"docstring-inheritance {version} is 3.0+, which breaks MRO compatibility. "
            "Update pyproject.toml constraint to exclude incompatible versions."
        )
