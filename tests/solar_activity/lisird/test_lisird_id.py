#!/usr/bin/env python
"""Test LISIRD_ID class.

This module tests the LISIRD_ID class from solar_activity.lisird.lisird:
- URL mapping and key validation
- Valid and invalid key handling
- URL construction for LISIRD endpoints
"""

import pytest
from unittest.mock import Mock, patch

from solarwindpy.solar_activity.lisird.lisird import LISIRD_ID


class TestLISIRD_ID:
    """Test the LISIRD_ID class for URL mapping and key validation."""

    def test_valid_key_initialization(self):
        """Test LISIRD_ID initialization with valid keys."""
        valid_keys = ["Lalpha", "CaK", "f107-noaa", "f107-penticton", "MgII"]

        for key in valid_keys:
            lisird_id = LISIRD_ID(key)
            assert lisird_id.key == key

    def test_url_base_property(self):
        """Test that _url_base returns the correct LISIRD base URL."""
        lisird_id = LISIRD_ID("Lalpha")
        expected_url_base = "http://lasp.colorado.edu/lisird/latis/dap/"
        assert lisird_id._url_base == expected_url_base

    def test_trans_url_mapping(self):
        """Test the _trans_url property provides correct URL mappings."""
        lisird_id = LISIRD_ID("Lalpha")
        trans_url_dict = lisird_id._trans_url

        expected_mappings = {
            "Lalpha": "composite_lyman_alpha.jsond",
            "CaK": "cak.jsond",
            "f107-penticton": "penticton_radio_flux.jsond",
            "f107-noaa": "noaa_radio_flux.jsond",
            "MgII": "composite_mg_index.jsond",
        }

        for key, expected_filename in expected_mappings.items():
            assert trans_url_dict[key] == expected_filename

    def test_url_construction_valid_keys(self):
        """Test URL construction for valid LISIRD keys."""
        test_cases = [
            (
                "Lalpha",
                "http://lasp.colorado.edu/lisird/latis/dap/composite_lyman_alpha.jsond",
            ),
            ("CaK", "http://lasp.colorado.edu/lisird/latis/dap/cak.jsond"),
            (
                "f107-noaa",
                "http://lasp.colorado.edu/lisird/latis/dap/noaa_radio_flux.jsond",
            ),
            (
                "f107-penticton",
                "http://lasp.colorado.edu/lisird/latis/dap/penticton_radio_flux.jsond",
            ),
            (
                "MgII",
                "http://lasp.colorado.edu/lisird/latis/dap/composite_mg_index.jsond",
            ),
        ]

        for key, expected_url in test_cases:
            lisird_id = LISIRD_ID(key)
            assert lisird_id.url == expected_url

    def test_invalid_key_error_handling(self):
        """Test that invalid keys raise appropriate errors."""
        # Test behavior with key not in _trans_url mapping
        invalid_key = "invalid_key_not_in_mapping"

        # LISIRD_ID raises NotImplementedError during initialization for invalid keys
        with pytest.raises(NotImplementedError, match="key unavailable"):
            LISIRD_ID(invalid_key)

    def test_inheritance_from_id_base_class(self):
        """Test that LISIRD_ID inherits from ID base class."""
        from solarwindpy.solar_activity.base import ID

        lisird_id = LISIRD_ID("Lalpha")
        assert isinstance(lisird_id, ID)

        # Test that it has the expected inherited properties
        assert hasattr(lisird_id, "key")
        assert hasattr(lisird_id, "url")

    def test_key_case_sensitivity(self):
        """Test that keys are case-sensitive."""
        # Valid key
        valid_id = LISIRD_ID("Lalpha")
        assert valid_id.key == "Lalpha"

        # Case variations should be treated as different keys
        # They may not have URL mappings and should raise NotImplementedError during init
        case_variant_key = "lalpha"  # lowercase

        with pytest.raises(NotImplementedError, match="key unavailable"):
            LISIRD_ID(case_variant_key)

    def test_url_property_consistency(self):
        """Test that url property is consistent and repeatable."""
        lisird_id = LISIRD_ID("Lalpha")
        url1 = lisird_id.url
        url2 = lisird_id.url

        # URL should be consistent across multiple accesses
        assert url1 == url2
        assert url1 is not None
        assert isinstance(url1, str)
        assert url1.startswith("http://")

    def test_all_mapped_keys_produce_valid_urls(self):
        """Test that all keys in the mapping produce valid URL strings."""
        # Get all mapped keys by creating an instance and accessing _trans_url
        sample_id = LISIRD_ID("Lalpha")
        all_mapped_keys = sample_id._trans_url.keys()

        for key in all_mapped_keys:
            lisird_id = LISIRD_ID(key)
            url = lisird_id.url

            # Basic URL validation
            assert isinstance(url, str)
            assert url.startswith("http://lasp.colorado.edu/lisird/latis/dap/")
            assert url.endswith(".jsond")
            assert len(url) > len(lisird_id._url_base)


class TestLISIRD_IDEdgeCases:
    """Test edge cases and error conditions for LISIRD_ID."""

    def test_empty_key_handling(self):
        """Test behavior with empty or None keys."""
        # Empty string key should raise NotImplementedError during init
        with pytest.raises(NotImplementedError, match="key unavailable"):
            LISIRD_ID("")

        # None key also raises NotImplementedError during init
        with pytest.raises(NotImplementedError, match="key unavailable"):
            LISIRD_ID(None)

    def test_whitespace_key_handling(self):
        """Test behavior with whitespace in keys."""
        whitespace_key = " Lalpha "

        # Should not match the valid mapping due to whitespace, raises during init
        with pytest.raises(NotImplementedError, match="key unavailable"):
            LISIRD_ID(whitespace_key)

    def test_numeric_key_handling(self):
        """Test behavior with numeric keys."""
        # String numeric key should raise NotImplementedError during init
        with pytest.raises(NotImplementedError, match="key unavailable"):
            LISIRD_ID("123")

        # Integer key also raises NotImplementedError during init
        with pytest.raises(NotImplementedError, match="key unavailable"):
            LISIRD_ID(123)

    def test_special_characters_in_key(self):
        """Test behavior with special characters in keys."""
        special_key = "f107-special!@#$%"

        # Should not match any valid mapping, raises during init
        with pytest.raises(NotImplementedError, match="key unavailable"):
            LISIRD_ID(special_key)

    def test_url_construction_consistency(self):
        """Test that URL construction is deterministic and correct."""
        key = "MgII"
        id1 = LISIRD_ID(key)
        id2 = LISIRD_ID(key)

        # Both instances should produce the same URL
        assert id1.url == id2.url

        # URL should match expected pattern
        expected = id1._url_base + id1._trans_url[key]
        assert id1.url == expected
