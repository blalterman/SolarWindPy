#!/usr/bin/env python
"""Test SIDC_ID class.

This module tests the SIDC_ID class from solar_activity.sunspot_number.sidc:
- URL mapping and key validation
- Valid and invalid key handling
- URL construction for SIDC endpoints
"""

import pytest
from unittest.mock import Mock, patch

from solarwindpy.solar_activity.sunspot_number.sidc import SIDC_ID


class TestSIDC_ID:
    """Test the SIDC_ID class for URL mapping and key validation."""

    def test_valid_key_initialization(self):
        """Test SIDC_ID initialization with valid keys."""
        valid_keys = ["d", "m", "m13", "y", "hd", "hm", "hm13"]

        for key in valid_keys:
            sidc_id = SIDC_ID(key)
            assert sidc_id.key == key

    def test_url_base_property(self):
        """Test that _url_base returns the correct SIDC base URL."""
        sidc_id = SIDC_ID("d")
        expected_url_base = "http://www.sidc.be/silso/INFO/"
        assert sidc_id._url_base == expected_url_base

    def test_trans_url_mapping(self):
        """Test the _trans_url property provides correct URL mappings."""
        sidc_id = SIDC_ID("d")
        trans_url_dict = sidc_id._trans_url

        expected_mappings = {
            "d": "sndtotcsv.php",
            "m": "snmtotcsv.php",
            "m13": "snmstotcsv.php",
            "y": "snytotcsv.php",
            "hd": "sndhemcsv.php",
            "hm": "snmhemcsv.php",
            "hm13": "snmshemcsv.php",
        }

        for key, expected_filename in expected_mappings.items():
            assert trans_url_dict[key] == expected_filename

    def test_url_construction_valid_keys(self):
        """Test URL construction for valid SIDC keys."""
        test_cases = [
            ("d", "http://www.sidc.be/silso/INFO/sndtotcsv.php"),
            ("m", "http://www.sidc.be/silso/INFO/snmtotcsv.php"),
            ("m13", "http://www.sidc.be/silso/INFO/snmstotcsv.php"),
            ("y", "http://www.sidc.be/silso/INFO/snytotcsv.php"),
            ("hd", "http://www.sidc.be/silso/INFO/sndhemcsv.php"),
            ("hm", "http://www.sidc.be/silso/INFO/snmhemcsv.php"),
            ("hm13", "http://www.sidc.be/silso/INFO/snmshemcsv.php"),
        ]

        for key, expected_url in test_cases:
            sidc_id = SIDC_ID(key)
            assert sidc_id.url == expected_url

    def test_invalid_key_error_handling(self):
        """Test that invalid keys raise appropriate errors."""
        invalid_key = "invalid_key_not_in_mapping"

        # SIDC_ID raises NotImplementedError during initialization for invalid keys
        with pytest.raises(NotImplementedError, match="key unavailable"):
            SIDC_ID(invalid_key)

    def test_inheritance_from_id_base_class(self):
        """Test that SIDC_ID inherits from ID base class."""
        from solarwindpy.solar_activity.base import ID

        sidc_id = SIDC_ID("d")
        assert isinstance(sidc_id, ID)

        # Test that it has the expected inherited properties
        assert hasattr(sidc_id, "key")
        assert hasattr(sidc_id, "url")

    def test_key_case_sensitivity(self):
        """Test that keys are case-sensitive."""
        # Valid key
        valid_id = SIDC_ID("m")
        assert valid_id.key == "m"

        # Case variations should raise NotImplementedError during init
        case_variant_key = "M"  # uppercase

        with pytest.raises(NotImplementedError, match="key unavailable"):
            SIDC_ID(case_variant_key)

    def test_url_property_consistency(self):
        """Test that url property is consistent and repeatable."""
        sidc_id = SIDC_ID("m")
        url1 = sidc_id.url
        url2 = sidc_id.url

        # URL should be consistent across multiple accesses
        assert url1 == url2
        assert url1 is not None
        assert isinstance(url1, str)
        assert url1.startswith("http://")

    def test_all_mapped_keys_produce_valid_urls(self):
        """Test that all keys in the mapping produce valid URL strings."""
        # Get all mapped keys by creating an instance and accessing _trans_url
        sample_id = SIDC_ID("d")
        all_mapped_keys = sample_id._trans_url.keys()

        for key in all_mapped_keys:
            sidc_id = SIDC_ID(key)
            url = sidc_id.url

            # Basic URL validation
            assert isinstance(url, str)
            assert url.startswith("http://www.sidc.be/silso/INFO/")
            assert url.endswith(".php")
            assert len(url) > len(sidc_id._url_base)


class TestSIDC_IDEdgeCases:
    """Test edge cases and error conditions for SIDC_ID."""

    def test_empty_key_handling(self):
        """Test behavior with empty or None keys."""
        # Empty string key should raise NotImplementedError during init
        with pytest.raises(NotImplementedError, match="key unavailable"):
            SIDC_ID("")

        # None key also raises NotImplementedError during init
        with pytest.raises(NotImplementedError, match="key unavailable"):
            SIDC_ID(None)

    def test_whitespace_key_handling(self):
        """Test behavior with whitespace in keys."""
        whitespace_key = " m "

        # Should not match the valid mapping due to whitespace, raises during init
        with pytest.raises(NotImplementedError, match="key unavailable"):
            SIDC_ID(whitespace_key)

    def test_numeric_key_handling(self):
        """Test behavior with numeric keys."""
        # String numeric key should raise NotImplementedError during init
        with pytest.raises(NotImplementedError, match="key unavailable"):
            SIDC_ID("13")

        # Integer key also raises NotImplementedError during init
        with pytest.raises(NotImplementedError, match="key unavailable"):
            SIDC_ID(13)

    def test_special_characters_in_key(self):
        """Test behavior with special characters in keys."""
        special_key = "m13-special!@#$%"

        # Should not match any valid mapping, raises during init
        with pytest.raises(NotImplementedError, match="key unavailable"):
            SIDC_ID(special_key)

    def test_url_construction_consistency(self):
        """Test that URL construction is deterministic and correct."""
        key = "hm13"
        id1 = SIDC_ID(key)
        id2 = SIDC_ID(key)

        # Both instances should produce the same URL
        assert id1.url == id2.url

        # URL should match expected pattern
        expected = id1._url_base + id1._trans_url[key]
        assert id1.url == expected

    def test_key_length_variations(self):
        """Test that key length variations are handled properly."""
        # Valid keys of different lengths
        short_key = "d"  # 1 character
        medium_key = "m13"  # 3 characters
        long_key = "hm13"  # 4 characters

        short_id = SIDC_ID(short_key)
        medium_id = SIDC_ID(medium_key)
        long_id = SIDC_ID(long_key)

        assert short_id.key == short_key
        assert medium_id.key == medium_key
        assert long_id.key == long_key

        # Invalid keys of various lengths
        with pytest.raises(NotImplementedError):
            SIDC_ID("abc")  # 3 characters but invalid

        with pytest.raises(NotImplementedError):
            SIDC_ID("toolong")  # longer than any valid key

    def test_similar_valid_keys(self):
        """Test that similar but distinct valid keys work correctly."""
        # These keys are similar but should map to different URLs
        monthly = SIDC_ID("m")
        monthly_smoothed = SIDC_ID("m13")
        hemispheric_monthly = SIDC_ID("hm")
        hemispheric_monthly_smoothed = SIDC_ID("hm13")

        # Should all be different URLs
        urls = [
            monthly.url,
            monthly_smoothed.url,
            hemispheric_monthly.url,
            hemispheric_monthly_smoothed.url,
        ]

        assert len(set(urls)) == 4  # All URLs should be unique

        # Check specific mappings
        assert "snmtotcsv.php" in monthly.url
        assert "snmstotcsv.php" in monthly_smoothed.url
        assert "snmhemcsv.php" in hemispheric_monthly.url
        assert "snmshemcsv.php" in hemispheric_monthly_smoothed.url
