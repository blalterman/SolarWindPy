import pytest
from pathlib import Path
from solarwindpy.plotting.labels import datetime as datetime_labels
from solarwindpy.plotting.labels.special import ArbitraryLabel
from solarwindpy.plotting.labels.base import Base


def test_timedelta_latex_and_path():
    """Verify ``Timedelta`` LaTeX and path string."""
    td = datetime_labels.Timedelta("2h")
    assert str(td.path) in ("dt-2h", "dt-2H")
    assert str(td) in (
        "$\\Delta t \\; [2 \\; \\mathrm{h}]$",
        "$\\Delta t \\; [2 \\; \\mathrm{H}]$",
    )


def test_datetime_label():
    """Verify ``DateTime`` label formatting."""
    dt = datetime_labels.DateTime("Day of Year")
    assert str(dt.path) == "day-of-year"
    assert str(dt) == "$\\mathrm{Day \\; of \\; Year}$"


def test_epoch_label():
    """Verify ``Epoch`` label formatting."""
    epoch = datetime_labels.Epoch("Hour", "Day")
    assert str(epoch.path) == "Hour-of-Day"
    assert str(epoch) == "$\\mathrm{Hour \\, of \\, Day}$"


def test_frequency_label():
    """Validate ``Frequency`` label output."""
    freq = datetime_labels.Frequency("1h")
    assert str(freq.path) in (
        "frequency_of_(1 \\; \\mathrm{h})^-1",
        "frequency_of_(1 \\; \\mathrm{H})^-1",
    )
    assert str(freq) in (
        "$\\mathrm{Frequency} \\; [(1 \\; \\mathrm{h})^-1]$",
        "$\\mathrm{Frequency} \\; [(1 \\; \\mathrm{H})^-1]$",
    )


def test_january1st_label():
    """Validate ``January1st`` label output."""
    jan = datetime_labels.January1st()
    assert str(jan.path) == "January-1st-of-Year"
    assert str(jan) == "$\\mathrm{January \\; 1^{st} \\; of \\; Year}$"


class TestTimedelta:
    """Test Timedelta class functionality."""

    def test_timedelta_inheritance(self):
        """Test that Timedelta inherits from ArbitraryLabel."""
        td = datetime_labels.Timedelta("1h")
        assert isinstance(td, ArbitraryLabel)
        assert isinstance(td, Base)

    def test_timedelta_various_offsets(self):
        """Test Timedelta with various pandas offsets."""
        test_cases = ["1h", "2H", "30min", "1d", "5s", "10ms", "1M", "1Y", "1W", "1Q"]

        for offset in test_cases:
            td = datetime_labels.Timedelta(offset)
            assert td.offset is not None
            assert isinstance(td.path, Path)
            assert r"\Delta t" in td.tex

    def test_timedelta_tex_property(self):
        """Test TeX property of Timedelta."""
        td = datetime_labels.Timedelta("1h")
        assert td.tex == r"\Delta t"

    def test_timedelta_invalid_offset(self):
        """Test Timedelta with invalid offset."""
        td = datetime_labels.Timedelta("invalid_offset")
        assert str(td.path) == "dt-UNK"
        assert "???" in td.units

    def test_timedelta_path_generation(self):
        """Test path generation for different offsets."""
        td_hour = datetime_labels.Timedelta("1h")
        td_day = datetime_labels.Timedelta("1d")

        # Paths should be different
        assert td_hour.path != td_day.path
        assert "dt-" in str(td_hour.path)
        assert "dt-" in str(td_day.path)

    def test_timedelta_units_formatting(self):
        """Test units formatting."""
        td = datetime_labels.Timedelta("2h")
        units = td.units
        assert "2" in units
        assert "mathrm" in units

    def test_timedelta_string_representation(self):
        """Test string representation."""
        td = datetime_labels.Timedelta("1d")
        str_repr = str(td)
        assert str_repr.startswith("$")
        assert str_repr.endswith("$")
        assert r"\Delta t" in str_repr

    def test_timedelta_with_units_property(self):
        """Test with_units property."""
        td = datetime_labels.Timedelta("1h")
        with_units = td.with_units
        assert r"\Delta t" in with_units
        assert "[" in with_units
        assert "]" in with_units

    def test_timedelta_set_offset(self):
        """Test set_offset method."""
        td = datetime_labels.Timedelta("1h")
        original_offset = td.offset

        # Test setting new offset
        td.set_offset("2d")
        assert td.offset != original_offset


class TestDateTime:
    """Test DateTime class functionality."""

    def test_datetime_inheritance(self):
        """Test that DateTime inherits from ArbitraryLabel."""
        dt = datetime_labels.DateTime("Year")
        assert isinstance(dt, ArbitraryLabel)
        assert isinstance(dt, Base)

    def test_datetime_various_kinds(self):
        """Test DateTime with various kinds."""
        test_cases = [
            "Year",
            "Month",
            "Day",
            "Hour",
            "Minute",
            "Second",
            "Day of Year",
            "Hour of Day",
            "Fractional Day",
        ]

        for kind in test_cases:
            dt = datetime_labels.DateTime(kind)
            assert dt.kind == kind
            assert isinstance(dt.path, Path)
            assert r"\mathrm{" in dt.tex

    def test_datetime_tex_formatting(self):
        """Test TeX formatting with spaces."""
        dt = datetime_labels.DateTime("Day of Year")
        expected_tex = r"\mathrm{Day \; of \; Year}"
        assert dt.tex == expected_tex

    def test_datetime_path_generation(self):
        """Test path generation."""
        dt = datetime_labels.DateTime("Day of Year")
        assert str(dt.path) == "day-of-year"

        dt_simple = datetime_labels.DateTime("Year")
        assert str(dt_simple.path) == "year"

    def test_datetime_string_representation(self):
        """Test string representation."""
        dt = datetime_labels.DateTime("Month")
        str_repr = str(dt)
        assert str_repr.startswith("$")
        assert str_repr.endswith("$")
        assert "Month" in str_repr

    def test_datetime_set_kind(self):
        """Test set_kind method."""
        dt = datetime_labels.DateTime("Year")
        assert dt.kind == "Year"

        dt.set_kind("Month")
        assert dt.kind == "Month"

    def test_datetime_with_units_property(self):
        """Test with_units property."""
        dt = datetime_labels.DateTime("Year")
        with_units = dt.with_units
        assert with_units == str(dt)
        assert "$" in with_units


class TestEpoch:
    """Test Epoch class functionality."""

    def test_epoch_inheritance(self):
        """Test that Epoch inherits from ArbitraryLabel."""
        epoch = datetime_labels.Epoch("Hour", "Day")
        assert isinstance(epoch, ArbitraryLabel)
        assert isinstance(epoch, Base)

    def test_epoch_basic_properties(self):
        """Test basic Epoch properties."""
        epoch = datetime_labels.Epoch("Hour", "Day")
        assert epoch.smaller == "Hour"
        assert epoch.larger == "Day"
        assert epoch.space == r"\,"

    def test_epoch_case_conversion(self):
        """Test case conversion for smaller and larger."""
        epoch = datetime_labels.Epoch("hour", "day")
        assert epoch.smaller == "Hour"
        assert epoch.larger == "Day"

    def test_epoch_tex_formatting(self):
        """Test TeX formatting."""
        epoch = datetime_labels.Epoch("Hour", "Day")
        expected_tex = r"\mathrm{Hour \, of \, Day}"
        assert epoch.tex == expected_tex

    def test_epoch_path_generation(self):
        """Test path generation."""
        epoch = datetime_labels.Epoch("Hour", "Day")
        assert str(epoch.path) == "Hour-of-Day"

        epoch2 = datetime_labels.Epoch("Minute", "Hour")
        assert str(epoch2.path) == "Minute-of-Hour"

    def test_epoch_different_spacing(self):
        """Test different spacing options."""
        spaces = [" ", r"\,", r"\;", r"\:"]

        for space in spaces:
            epoch = datetime_labels.Epoch("Hour", "Day", space=space)
            assert epoch.space == space
            assert space in epoch.tex

    def test_epoch_invalid_space(self):
        """Test invalid space raises ValueError."""
        with pytest.raises(ValueError, match="Unrecognized Space"):
            datetime_labels.Epoch("Hour", "Day", space="invalid")

    def test_epoch_string_representation(self):
        """Test string representation."""
        epoch = datetime_labels.Epoch("Hour", "Day")
        str_repr = str(epoch)
        assert str_repr.startswith("$")
        assert str_repr.endswith("$")
        assert "Hour" in str_repr
        assert "Day" in str_repr

    def test_epoch_setter_methods(self):
        """Test setter methods."""
        epoch = datetime_labels.Epoch("Hour", "Day")

        epoch.set_smaller("minute")
        assert epoch.smaller == "Minute"

        epoch.set_larger("year")
        assert epoch.larger == "Year"

        epoch.set_space(r"\;")
        assert epoch.space == r"\;"


class TestFrequency:
    """Test Frequency class functionality."""

    def test_frequency_inheritance(self):
        """Test that Frequency inherits from ArbitraryLabel."""
        freq = datetime_labels.Frequency("1h")
        assert isinstance(freq, ArbitraryLabel)
        assert isinstance(freq, Base)

    def test_frequency_with_string_offset(self):
        """Test Frequency with string offset."""
        freq = datetime_labels.Frequency("1h")
        assert isinstance(freq.other, datetime_labels.Timedelta)
        assert r"\mathrm{Frequency}" in freq.tex

    def test_frequency_with_timedelta_object(self):
        """Test Frequency with Timedelta object."""
        td = datetime_labels.Timedelta("2d")
        freq = datetime_labels.Frequency(td)
        assert freq.other == td

    def test_frequency_tex_property(self):
        """Test TeX property."""
        freq = datetime_labels.Frequency("1h")
        assert freq.tex == r"\mathrm{Frequency}"

    def test_frequency_units_property(self):
        """Test units property."""
        freq = datetime_labels.Frequency("1h")
        units = freq.units
        assert units.endswith("^-1")  # Fixed - uses ^-1 not ^{-1}
        assert "(" in units
        assert ")" in units

    def test_frequency_path_generation(self):
        """Test path generation."""
        freq = datetime_labels.Frequency("1h")
        path_str = str(freq.path)
        assert "frequency_of_" in path_str

    def test_frequency_with_invalid_offset(self):
        """Test Frequency with invalid offset."""
        freq = datetime_labels.Frequency("invalid")
        path_str = str(freq.path)
        assert "UNK" in path_str or "???" in path_str

    def test_frequency_string_representation(self):
        """Test string representation."""
        freq = datetime_labels.Frequency("1d")
        str_repr = str(freq)
        assert str_repr.startswith("$")
        assert str_repr.endswith("$")
        assert "Frequency" in str_repr
        assert "[" in str_repr
        assert "]" in str_repr

    def test_frequency_set_other(self):
        """Test set_other method."""
        freq = datetime_labels.Frequency("1h")
        original_other = freq.other

        freq.set_other("2d")
        assert freq.other != original_other


class TestJanuary1st:
    """Test January1st class functionality."""

    def test_january1st_inheritance(self):
        """Test that January1st inherits from ArbitraryLabel."""
        jan = datetime_labels.January1st()
        assert isinstance(jan, ArbitraryLabel)
        assert isinstance(jan, Base)

    def test_january1st_tex_property(self):
        """Test TeX property."""
        jan = datetime_labels.January1st()
        expected_tex = r"\mathrm{January \; 1^{st} \; of \; Year}"
        assert jan.tex == expected_tex

    def test_january1st_path_property(self):
        """Test path property."""
        jan = datetime_labels.January1st()
        assert str(jan.path) == "January-1st-of-Year"

    def test_january1st_string_representation(self):
        """Test string representation."""
        jan = datetime_labels.January1st()
        str_repr = str(jan)
        assert str_repr.startswith("$")
        assert str_repr.endswith("$")
        assert "January" in str_repr
        assert "1^{st}" in str_repr
        assert "Year" in str_repr

    def test_january1st_with_units_property(self):
        """Test with_units property."""
        jan = datetime_labels.January1st()
        with_units = jan.with_units
        assert with_units == str(jan)


class TestDateTimeModule:
    """Test module-level functionality."""

    def test_module_classes(self):
        """Test that module has expected classes."""
        expected_classes = ["Timedelta", "DateTime", "Epoch", "Frequency", "January1st"]

        for class_name in expected_classes:
            assert hasattr(datetime_labels, class_name)
            cls = getattr(datetime_labels, class_name)
            assert isinstance(cls, type)

    def test_class_inheritance_chain(self):
        """Test inheritance chain for all classes."""
        classes = [
            datetime_labels.Timedelta,
            datetime_labels.DateTime,
            datetime_labels.Epoch,
            datetime_labels.Frequency,
            datetime_labels.January1st,
        ]

        for cls in classes:
            # All should inherit from ArbitraryLabel
            assert issubclass(cls, ArbitraryLabel)
            # All should ultimately inherit from Base
            assert issubclass(cls, Base)


class TestDateTimeIntegration:
    """Test integration between datetime classes."""

    def test_timedelta_in_frequency(self):
        """Test using Timedelta in Frequency."""
        td = datetime_labels.Timedelta("1h")
        freq = datetime_labels.Frequency(td)
        assert freq.other == td

    def test_different_epoch_combinations(self):
        """Test different epoch combinations."""
        epochs = [
            ("Hour", "Day"),
            ("Minute", "Hour"),
            ("Day", "Month"),
            ("Month", "Year"),
        ]

        for smaller, larger in epochs:
            epoch = datetime_labels.Epoch(smaller, larger)
            assert epoch.smaller == smaller
            assert epoch.larger == larger
            assert f"{smaller}-of-{larger}" == str(epoch.path)

    def test_label_uniqueness(self):
        """Test that different labels generate unique paths."""
        labels = [
            datetime_labels.Timedelta("1h"),
            datetime_labels.DateTime("Hour"),
            datetime_labels.Epoch("Hour", "Day"),
            datetime_labels.Frequency("1h"),
            datetime_labels.January1st(),
        ]

        paths = [str(label.path) for label in labels]
        assert len(paths) == len(set(paths))  # All unique

    def test_scientific_accuracy(self):
        """Test that labels represent scientifically accurate concepts."""
        # Test time delta representation
        td = datetime_labels.Timedelta("1h")
        assert r"\Delta t" in td.tex

        # Test frequency units
        freq = datetime_labels.Frequency("1h")
        assert "^-1" in freq.units

        # Test epoch relationships
        epoch = datetime_labels.Epoch("Hour", "Day")
        assert "of" in epoch.tex
