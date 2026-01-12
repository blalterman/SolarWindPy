import importlib.util
from pathlib import Path
import pytest
import logging


@pytest.fixture(scope="module")
def labels_base():
    """Load :mod:`solarwindpy.plotting.labels.base` without side effects."""
    path = (
        Path(__file__).resolve().parents[3]
        / "solarwindpy"
        / "plotting"
        / "labels"
        / "base.py"
    )
    spec = importlib.util.spec_from_file_location("swp_labels_base", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def texlabel_basic(labels_base):
    """Return a typical :class:`TeXlabel` instance."""
    return labels_base.TeXlabel(("v", "x", "p"))


@pytest.fixture()
def texlabel_ratio(labels_base):
    """Return a ratio :class:`TeXlabel` instance."""
    return labels_base.TeXlabel(("v", "x", "p"), ("n", "", "p"))


@pytest.fixture()
def texlabel_with_axnorm(labels_base):
    """Return a :class:`TeXlabel` instance with axis normalization."""
    return labels_base.TeXlabel(("n", "", "p"), axnorm="c")


@pytest.fixture()
def texlabel_with_error(labels_base):
    """Return a :class:`TeXlabel` instance with error measurement."""
    return labels_base.TeXlabel(("v_err", "x", "p"))


@pytest.fixture()
def texlabel_newline_units(labels_base):
    """Return a :class:`TeXlabel` instance with newline for units."""
    return labels_base.TeXlabel(("T", "", "p"), new_line_for_units=True)


def test_run_species_substitution(labels_base):
    """Verify direct species substitution helper."""
    cases = {
        "p": ("p", 1),
        "p1+p2": ("p_1+p_2", 2),
        "a+p1": ("\\alpha+p_1", 2),
        "Fe": ("\\mathrm{Fe}", 1),
    }
    for pattern, expected in cases.items():
        assert labels_base._run_species_substitution(pattern) == expected


def test_texlabel_attributes(texlabel_basic):
    """Check attributes of a typical :class:`TeXlabel`."""
    assert texlabel_basic.tex == "{v}_{{X};{p}}"
    assert texlabel_basic.units == "\\mathrm{km \\; s^{-1}}"
    assert texlabel_basic.path == Path("v_x_p")
    assert (
        texlabel_basic.with_units
        == "${v}_{{X};{p}} \\; \\left[\\mathrm{km \\; s^{-1}}\\right]$"
    )


def test_texlabel_ratio_attributes(texlabel_ratio):
    """Check attributes of a ratio :class:`TeXlabel`."""
    assert texlabel_ratio.tex == "{v}_{{X};{p}}/n_{p}"
    assert texlabel_ratio.units == "\\mathrm{km \\; s^{-1}}/\\mathrm{cm}^{-3}"
    assert texlabel_ratio.path == Path("v_x_p-OV-n_p")
    assert (
        texlabel_ratio.with_units
        == "${v}_{{X};{p}}/n_{p} \\; \\left[\\mathrm{km \\; s^{-1}}/\\mathrm{cm}^{-3}\\right]$"
    )


def test_texlabel_equality_and_hash(texlabel_basic, texlabel_ratio, labels_base):
    """Ensure equality and hashing are based on ``str``."""
    same_basic = labels_base.TeXlabel(("v", "x", "p"))
    same_ratio = labels_base.TeXlabel(("v", "x", "p"), ("n", "", "p"))

    assert texlabel_basic == same_basic
    assert hash(texlabel_basic) == hash(same_basic)

    assert texlabel_ratio == same_ratio
    assert hash(texlabel_ratio) == hash(same_ratio)


def test_texlabel_comparison_operators(texlabel_basic, labels_base):
    """Test comparison operators for TeXlabel objects."""
    label_a = labels_base.TeXlabel(("a", "x", "p"))  # Alphabetically first
    label_z = labels_base.TeXlabel(("z", "x", "p"))  # Alphabetically last

    assert label_a < label_z
    assert label_a <= label_z
    assert label_z > label_a
    assert label_z >= label_a
    assert label_a != label_z


def test_texlabel_axnorm_types(labels_base):
    """Test different axis normalization types."""
    test_cases = [
        ("c", "Col."),
        ("r", "Row"),
        ("t", "Total"),
        ("d", "Density"),
        (None, ""),
    ]

    for axnorm, expected_prefix in test_cases:
        label = labels_base.TeXlabel(("n", "", "p"), axnorm=axnorm)
        if axnorm:
            assert expected_prefix in label.tex
            assert label.units == "\\#"
        else:
            assert label.units == "\\mathrm{cm}^{-3}"


def test_texlabel_error_measurement(texlabel_with_error):
    """Test error measurement handling."""
    assert "\\sigma" in texlabel_with_error.tex
    assert "{v}_{{X};{p}}" in texlabel_with_error.tex


def test_texlabel_newline_units(texlabel_newline_units):
    """Test newline separation for units."""
    assert "$\n$" in texlabel_newline_units.with_units


def test_species_substitution_comprehensive(labels_base):
    """Test comprehensive species substitution patterns."""
    test_cases = {
        "p": ("p", 1),
        "p1": ("p_1", 1),
        "p2": ("p_2", 1),
        "a": ("\\alpha", 1),
        "a1": ("\\alpha_1", 1),
        "a2": ("\\alpha_2", 1),
        "e": ("e^-", 1),
        "he": ("\\mathrm{He}", 1),
        "Fe": ("\\mathrm{Fe}", 1),
        "3He": ("^{3}\\mathrm{He}", 1),
        "16O": ("^{16}\\mathrm{O}", 1),
        "p1+p2": ("p_1+p_2", 2),
        "a+Fe": ("\\alpha+\\mathrm{Fe}", 2),
    }

    for pattern, expected in test_cases.items():
        result = labels_base._run_species_substitution(pattern)
        assert result == expected, f"Failed for pattern '{pattern}'"


def test_measurement_translation(labels_base):
    """Test measurement translation."""
    test_cases = {
        ("beta", "", "p"): "\\beta",
        ("theta", "", "p"): "\\theta",
        ("pth", "", "p"): "P",
        ("dv", "", "p"): "\\Delta v",
        ("qhat", "", "p"): "\\widehat{q}",
    }

    for mcs, expected_tex_part in test_cases.items():
        label = labels_base.TeXlabel(mcs)
        assert expected_tex_part in label.tex


def test_component_translation(labels_base):
    """Test component translation."""
    test_cases = {
        ("v", "x", "p"): "X",
        ("v", "y", "p"): "Y",
        ("v", "z", "p"): "Z",
        ("v", "r", "p"): "R",
        ("v", "per", "p"): "\\perp",
        ("v", "par", "p"): "\\parallel",
    }

    for mcs, expected_component in test_cases.items():
        label = labels_base.TeXlabel(mcs)
        assert expected_component in label.tex


def test_units_translation(labels_base):
    """Test units translation."""
    test_cases = {
        ("v", "x", "p"): "\\mathrm{km \\; s^{-1}}",
        ("n", "", "p"): "\\mathrm{cm}^{-3}",
        ("b", "x", ""): "\\mathrm{nT}",
        ("T", "", "p"): "10^5 \\, \\mathrm{K}",
        ("beta", "", "p"): "\\mathrm{\\#}",
    }

    for mcs, expected_units in test_cases.items():
        label = labels_base.TeXlabel(mcs)
        assert label.units == expected_units


def test_path_generation(labels_base):
    """Test path generation for different inputs."""
    test_cases = {
        ("v", "x", "p"): "v_x_p",
        ("n", "", "p"): "n_p",
        ("b", "x", ""): "b_x",  # Fixed - empty strings are stripped
        ("beta", "", ""): "beta",
    }

    for mcs, expected_path in test_cases.items():
        label = labels_base.TeXlabel(mcs)
        assert str(label.path) == expected_path


def test_ratio_label_same_units(labels_base):
    """Test ratio labels with same units become dimensionless."""
    # Same measurement, different components - same units
    label = labels_base.TeXlabel(("v", "x", "p"), ("v", "y", "p"))
    assert label.units == "\\#"


def test_ratio_label_different_units(labels_base):
    """Test ratio labels with different units."""
    # Different measurements - different units
    label = labels_base.TeXlabel(("v", "x", "p"), ("n", "", "p"))
    expected_units = "\\mathrm{km \\; s^{-1}}/\\mathrm{cm}^{-3}"
    assert label.units == expected_units


def test_template_substitution(labels_base):
    """Test template substitution for complex measurements."""
    # Test specific template
    label = labels_base.TeXlabel(("cs", "", "p"))
    assert "C_{s;p}" in label.tex

    # Test default template
    label = labels_base.TeXlabel(("unknown_measurement", "x", "p"))
    assert "{unknown_measurement}_{{X};{p}}" in label.tex


def test_tex_cleanup(labels_base):
    """Test TeX string cleanup operations."""
    # Test empty component cleanup
    label = labels_base.TeXlabel(("v", "", "p"))
    assert "{}" not in label.tex
    assert "()" not in label.tex

    # Test empty species cleanup
    label = labels_base.TeXlabel(("v", "x", ""))
    assert "_;{}" not in label.tex


def test_base_class_properties(labels_base):
    """Test Base class properties and methods."""
    base_instance = labels_base.TeXlabel(("v", "x", "p"))

    # Test logger
    assert hasattr(base_instance, "logger")
    assert isinstance(base_instance.logger, logging.Logger)

    # Test string representations
    assert str(base_instance) == base_instance.with_units
    assert repr(base_instance) == str(base_instance.tex)


def test_mcs_namedtuple(labels_base):
    """Test MCS namedtuple functionality."""
    mcs = labels_base.MCS("v", "x", "p")
    assert mcs.m == "v"
    assert mcs.c == "x"
    assert mcs.s == "p"


def test_texlabel_set_methods(labels_base):
    """Test TeXlabel setter methods."""
    label = labels_base.TeXlabel(("v", "x", "p"))

    # Test set_axnorm
    label.set_axnorm("r")
    assert label.axnorm == "r"

    label.set_axnorm("C")  # Test case conversion
    assert label.axnorm == "c"

    # Test set_new_line_for_units
    label.set_new_line_for_units(True)
    assert label.new_line_for_units is True

    label.set_new_line_for_units(0)  # Test bool conversion
    assert label.new_line_for_units is False

    # Test set_mcs
    label.set_mcs(("n", "", "p"), ("T", "", "p"))
    assert label.mcs0.m == "n"
    assert label.mcs1.m == "T"


def test_axnorm_validation(labels_base):
    """Test axis normalization validation."""
    valid_values = [None, "c", "r", "t", "d"]

    for val in valid_values:
        label = labels_base.TeXlabel(("v", "x", "p"), axnorm=val)
        assert label.axnorm == val

    # Test invalid axnorm
    with pytest.raises(AssertionError):
        labels_base.TeXlabel(("v", "x", "p"), axnorm="invalid")


def test_path_special_characters(labels_base):
    """Test path handling with special characters."""
    # Test forward slash replacement
    label = labels_base.TeXlabel(("test/measurement", "x", "p"))
    assert "-OV-" in str(label.path)

    # Test comma and dot removal
    label = labels_base.TeXlabel(("test.measurement", "x", "p,ion"))
    path_str = str(label.path)
    assert "." not in path_str
    assert "," not in path_str


def test_empty_string_handling(labels_base):
    """Test handling of empty strings in MCS components."""
    cases = [
        ("", "x", "p"),  # Empty measurement
        ("v", "", "p"),  # Empty component
        ("v", "x", ""),  # Empty species
        ("", "", ""),  # All empty
    ]

    for mcs in cases:
        # Should not raise exception
        label = labels_base.TeXlabel(mcs)
        assert hasattr(label, "tex")
        assert hasattr(label, "units")
        assert hasattr(label, "path")


class TestDescriptionFeature:
    """Tests for the description property on Base/TeXlabel classes.

    The description feature allows human-readable text to be prepended
    above the mathematical LaTeX label for axis/colorbar labels.
    """

    def test_description_default_none(self, labels_base):
        """Default description is None when not specified."""
        label = labels_base.TeXlabel(("v", "x", "p"))
        assert label.description is None

    def test_set_description_stores_value(self, labels_base):
        """set_description() stores the given string."""
        label = labels_base.TeXlabel(("v", "x", "p"))
        label.set_description("Test description")
        assert label.description == "Test description"

    def test_set_description_converts_to_string(self, labels_base):
        """set_description() converts non-string values to string."""
        label = labels_base.TeXlabel(("v", "x", "p"))
        label.set_description(42)
        assert label.description == "42"
        assert isinstance(label.description, str)

    def test_set_description_none_clears(self, labels_base):
        """set_description(None) clears the description."""
        label = labels_base.TeXlabel(("v", "x", "p"))
        label.set_description("Some text")
        assert label.description == "Some text"
        label.set_description(None)
        assert label.description is None

    def test_description_init_parameter(self, labels_base):
        """TeXlabel accepts description in __init__."""
        label = labels_base.TeXlabel(("n", "", "p"), description="density")
        assert label.description == "density"

    def test_description_appears_in_with_units(self, labels_base):
        """Description is prepended to with_units output."""
        label = labels_base.TeXlabel(("v", "x", "p"), description="velocity")
        result = label.with_units
        assert result.startswith("velocity\n")
        assert "$" in result  # Still contains the TeX label

    def test_description_with_newline_separator(self, labels_base):
        """Description uses newline to separate from label."""
        label = labels_base.TeXlabel(("T", "", "p"), description="temperature")
        result = label.with_units
        lines = result.split("\n")
        assert len(lines) >= 2
        assert lines[0] == "temperature"

    def test_format_with_description_none_unchanged(self, labels_base):
        """_format_with_description returns unchanged when description is None."""
        label = labels_base.TeXlabel(("v", "x", "p"))
        assert label.description is None
        test_string = "$test \\; [units]$"
        result = label._format_with_description(test_string)
        assert result == test_string

    def test_format_with_description_adds_prefix(self, labels_base):
        """_format_with_description prepends description."""
        label = labels_base.TeXlabel(("v", "x", "p"))
        label.set_description("info")
        test_string = "$test \\; [units]$"
        result = label._format_with_description(test_string)
        assert result == "info\n$test \\; [units]$"

    def test_description_with_axnorm(self, labels_base):
        """Description works correctly with axis normalization."""
        label = labels_base.TeXlabel(("n", "", "p"), axnorm="t", description="count")
        result = label.with_units
        assert result.startswith("count\n")
        assert "Total" in result or "Norm" in result

    def test_description_with_ratio_label(self, labels_base):
        """Description works with ratio-style labels."""
        label = labels_base.TeXlabel(
            ("v", "x", "p"), ("n", "", "p"), description="v/n ratio"
        )
        result = label.with_units
        assert result.startswith("v/n ratio\n")
        assert "/" in result  # Contains ratio

    def test_description_empty_string_treated_as_falsy(self, labels_base):
        """Empty string description is treated as no description."""
        label = labels_base.TeXlabel(("v", "x", "p"), description="")
        result = label.with_units
        # Empty string is falsy, so _format_with_description returns unchanged
        assert not result.startswith("\n")

    def test_str_includes_description(self, labels_base):
        """__str__ returns with_units which includes description."""
        label = labels_base.TeXlabel(("v", "x", "p"), description="speed")
        assert str(label).startswith("speed\n")
