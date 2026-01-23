"""Smoke tests for ICMECAT class.

Quick validation tests that can run without network access.
Verify module imports, docstrings, and basic instantiation.
"""

import pytest


class TestModuleImports:
    """Verify module can be imported and has expected attributes."""

    def test_import_module(self):
        """Module can be imported without errors."""
        from solarwindpy.solar_activity import icme
        assert icme is not None

    def test_icmecat_class_exists(self):
        """ICMECAT class is importable."""
        from solarwindpy.solar_activity.icme import ICMECAT
        assert ICMECAT is not None

    def test_url_constant_defined(self):
        """ICMECAT_URL constant is defined."""
        from solarwindpy.solar_activity.icme import ICMECAT_URL
        assert isinstance(ICMECAT_URL, str)
        assert ICMECAT_URL.startswith("https://")
        assert "helioforecast" in ICMECAT_URL

    def test_spacecraft_names_defined(self):
        """SPACECRAFT_NAMES constant is defined."""
        from solarwindpy.solar_activity.icme import SPACECRAFT_NAMES
        assert "Ulysses" in SPACECRAFT_NAMES
        assert "Wind" in SPACECRAFT_NAMES


class TestDocstrings:
    """Verify docstrings are present and contain required information."""

    def test_module_docstring_exists(self):
        """Module has a docstring."""
        from solarwindpy.solar_activity import icme
        assert icme.__doc__ is not None
        assert len(icme.__doc__) > 100

    def test_module_docstring_has_url(self):
        """Module docstring references helioforecast.space."""
        from solarwindpy.solar_activity import icme
        assert "helioforecast.space/icmecat" in icme.__doc__

    def test_module_docstring_has_rules_of_road(self):
        """Module docstring includes rules of the road."""
        from solarwindpy.solar_activity import icme
        assert "rules of the road" in icme.__doc__.lower()
        assert "co-authorship" in icme.__doc__.lower()

    def test_module_docstring_has_citation(self):
        """Module docstring includes citation info."""
        from solarwindpy.solar_activity import icme
        assert "Möstl" in icme.__doc__
        assert "10.6084/m9.figshare.6356420" in icme.__doc__

    def test_icmecat_class_docstring(self):
        """ICMECAT class has a docstring."""
        from solarwindpy.solar_activity.icme import ICMECAT
        assert ICMECAT.__doc__ is not None

    def test_icmecat_methods_have_docstrings(self):
        """ICMECAT public methods have docstrings."""
        from solarwindpy.solar_activity.icme import ICMECAT

        methods = ["filter", "contains", "summary", "get_events_in_range"]
        for method_name in methods:
            method = getattr(ICMECAT, method_name)
            assert method.__doc__ is not None, f"{method_name} missing docstring"


class TestClassStructure:
    """Verify class has expected properties and methods."""

    def test_icmecat_has_data_property(self):
        """ICMECAT has data property."""
        from solarwindpy.solar_activity.icme import ICMECAT
        assert hasattr(ICMECAT, "data")

    def test_icmecat_has_intervals_property(self):
        """ICMECAT has intervals property."""
        from solarwindpy.solar_activity.icme import ICMECAT
        assert hasattr(ICMECAT, "intervals")

    def test_icmecat_has_strict_intervals_property(self):
        """ICMECAT has strict_intervals property."""
        from solarwindpy.solar_activity.icme import ICMECAT
        assert hasattr(ICMECAT, "strict_intervals")

    def test_icmecat_has_spacecraft_property(self):
        """ICMECAT has spacecraft property."""
        from solarwindpy.solar_activity.icme import ICMECAT
        assert hasattr(ICMECAT, "spacecraft")

    def test_icmecat_has_filter_method(self):
        """ICMECAT has filter method."""
        from solarwindpy.solar_activity.icme import ICMECAT
        assert callable(getattr(ICMECAT, "filter", None))

    def test_icmecat_has_contains_method(self):
        """ICMECAT has contains method."""
        from solarwindpy.solar_activity.icme import ICMECAT
        assert callable(getattr(ICMECAT, "contains", None))

    def test_icmecat_has_summary_method(self):
        """ICMECAT has summary method."""
        from solarwindpy.solar_activity.icme import ICMECAT
        assert callable(getattr(ICMECAT, "summary", None))
