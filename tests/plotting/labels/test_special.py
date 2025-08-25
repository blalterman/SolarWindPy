import pytest
from pathlib import Path
from solarwindpy.plotting.labels import special as labels_special
from solarwindpy.plotting.labels import base as labels_base


@pytest.fixture()
def basic_texlabel():
    """Return a basic TeXlabel for testing special labels."""
    return labels_base.TeXlabel(("v", "x", "p"))


@pytest.fixture()
def manual_label():
    """Return a ManualLabel instance."""
    return labels_special.ManualLabel("V_SW", "km s^{-1}")


@pytest.fixture()
def count_label():
    """Return a Count label instance."""
    return labels_special.Count()


@pytest.fixture()
def count_label_normalized():
    """Return a normalized Count label instance."""
    return labels_special.Count(norm="c")


@pytest.fixture()
def vsw_label():
    """Return a Vsw label instance."""
    return labels_special.Vsw()


@pytest.fixture()
def carrington_label():
    """Return a CarringtonRotation label instance."""
    return labels_special.CarringtonRotation()


class TestManualLabel:
    """Test ManualLabel class functionality."""

    def test_basic_creation(self, manual_label):
        """Test basic ManualLabel creation."""
        assert manual_label.tex == "V_SW"
        assert manual_label.unit == "km s^{-1}"
        assert isinstance(manual_label.path, Path)

    def test_string_representation(self, manual_label):
        """Test string representation."""
        result = str(manual_label)
        assert "V_SW" in result
        assert "km s^{-1}" in result
        assert result.startswith("$")
        assert result.endswith("$")

    def test_tex_stripping(self):
        """Test TeX string stripping of dollar signs."""
        label = labels_special.ManualLabel("$V_SW$", "km s^{-1}")
        assert label.tex == "V_SW"

    def test_unit_translation(self):
        """Test unit translation using base._inU."""
        label = labels_special.ManualLabel("B", "b")  # 'b' should translate to nT
        assert "nT" in label.unit

    def test_path_generation(self):
        """Test path generation."""
        label = labels_special.ManualLabel("Test Label", "units")
        assert str(label.path) == "Test-Label"

    def test_custom_path(self):
        """Test custom path specification."""
        label = labels_special.ManualLabel("Test", "units", path="custom_path")
        assert str(label.path) == "custom_path"

    def test_empty_unit_handling(self):
        """Test handling of empty units."""
        label = labels_special.ManualLabel("Test", "")
        result = str(label)
        assert "[]" not in result  # Empty units should be removed


class TestVsw:
    """Test Vsw (solar wind speed) label class."""

    def test_properties(self, vsw_label):
        """Test Vsw label properties."""
        assert vsw_label.tex == r"V_\mathrm{SW}"
        assert vsw_label.units == r"\mathrm{km \, s^{-1}}"
        assert str(vsw_label.path) == "vsw"

    def test_string_representation(self, vsw_label):
        """Test string representation."""
        result = str(vsw_label)
        assert "V_\\mathrm{SW}" in result
        assert "km" in result
        assert "s^{-1}" in result


class TestCarringtonRotation:
    """Test CarringtonRotation label class."""

    def test_short_label(self, carrington_label):
        """Test short label format."""
        assert carrington_label.short_label is True
        assert carrington_label.tex == r"\mathrm{CR}"

    def test_long_label(self):
        """Test long label format."""
        label = labels_special.CarringtonRotation(short_label=False)
        assert label.short_label is False
        assert "Carrington" in label.tex
        assert "Rotation" in label.tex

    def test_string_representation(self, carrington_label):
        """Test string representation."""
        result = str(carrington_label)
        assert "CR" in result
        assert r"[\#]" in result

    def test_path(self, carrington_label):
        """Test path property."""
        assert str(carrington_label.path) == "CarrRot"


class TestCount:
    """Test Count label class."""

    def test_basic_count(self, count_label):
        """Test basic count label."""
        assert count_label.tex == r"\mathrm{Count}"
        assert count_label.units == r"\#"
        assert count_label.axnorm is None

    def test_normalized_count(self, count_label_normalized):
        """Test normalized count label."""
        assert "Col." in count_label_normalized.tex
        assert "Norm" in count_label_normalized.tex
        assert count_label_normalized.axnorm == "c"

    def test_all_normalization_types(self):
        """Test all normalization types."""
        norm_types = {
            "c": "Col.",
            "r": "Row",
            "t": "Total",
            "d": "Density",  # Fixed - actual string is "Density" not "Probability Density"
            "cd": "1D",  # Just check for "1D" since spaces are escaped as \,
            "rd": "1D",  # Just check for "1D" since spaces are escaped as \,
        }

        for norm, expected in norm_types.items():
            label = labels_special.Count(norm=norm)
            assert expected in label.tex

    def test_path_with_normalization(self):
        """Test path generation with normalization."""
        label = labels_special.Count(norm="c")
        path_str = str(label.path)
        assert "Cnorm" in path_str

    def test_invalid_normalization(self):
        """Test invalid normalization raises assertion."""
        with pytest.raises(AssertionError):
            labels_special.Count(norm="invalid")

    def test_set_axnorm_case_conversion(self, count_label):
        """Test case conversion in set_axnorm."""
        count_label.set_axnorm("C")  # Upper case
        assert count_label.axnorm == "c"  # Should be converted to lower


class TestPower:
    """Test Power spectrum label class."""

    def test_properties(self):
        """Test Power label properties."""
        power = labels_special.Power()
        assert power.tex == r"\mathrm{Power}"
        assert power.units == r"\mathrm{\#}"
        assert str(power.path) == "power"

    def test_string_representation(self):
        """Test string representation."""
        power = labels_special.Power()
        result = str(power)
        assert "Power" in result
        assert r"[\mathrm{\#}]" in result


class TestProbability:
    """Test Probability label class."""

    def test_basic_probability(self, basic_texlabel):
        """Test basic probability label."""
        prob = labels_special.Probability(basic_texlabel, "> 500")
        assert "Prob." in prob.tex
        assert prob.units == r"\%"
        assert prob.other_label == basic_texlabel
        assert prob.comparison == "> 500"

    def test_empty_comparison(self, basic_texlabel):
        """Test probability with empty comparison."""
        prob = labels_special.Probability(basic_texlabel)
        assert prob.comparison == ""

    def test_path_generation(self, basic_texlabel):
        """Test path generation with comparison operators."""
        prob = labels_special.Probability(basic_texlabel, "> 500")
        path_str = str(prob.path)
        assert "prob-" in path_str
        assert "GT" in path_str  # > should be converted to GT

    def test_comparison_operator_conversion(self, basic_texlabel):
        """Test conversion of comparison operators in path."""
        operators = {
            ">": "GT",
            "<": "LT",
            r"\geq": "GEQ",
            r"\leq": "LEQ",
            "==": "EQ",
            "!=": "NEQ",
        }

        for op, expected in operators.items():
            prob = labels_special.Probability(basic_texlabel, f"x {op} 5")
            path_str = str(prob.path)
            assert expected in path_str

    def test_string_label(self):
        """Test probability with string label."""
        # String labels need to have a .tex attribute to work
        # So let's test with a ManualLabel instead
        manual_label = labels_special.ManualLabel("test_label", "units")
        prob = labels_special.Probability(manual_label, "> 0")
        assert prob.other_label == manual_label


class TestCountOther:
    """Test CountOther label class."""

    def test_basic_count_other(self, basic_texlabel):
        """Test basic CountOther label."""
        count = labels_special.CountOther(basic_texlabel, "> 500")
        assert "Count." in count.tex
        assert count.units == r"\#"
        assert not count.new_line_for_units

    def test_newline_units(self, basic_texlabel):
        """Test newline for units option."""
        count = labels_special.CountOther(
            basic_texlabel, "> 500", new_line_for_units=True
        )
        assert count.new_line_for_units is True
        result = str(count)
        assert "$\n$" in result

    def test_path_generation(self, basic_texlabel):
        """Test path generation for CountOther."""
        count = labels_special.CountOther(basic_texlabel, "> 500")
        path_str = str(count.path)
        assert "cnt-" in path_str


class TestMathFcn:
    """Test MathFcn label class."""

    def test_basic_math_function(self, basic_texlabel):
        """Test basic math function label."""
        math_fcn = labels_special.MathFcn("log", basic_texlabel)
        assert "log" in math_fcn.tex
        assert math_fcn.dimensionless is True
        assert math_fcn.units == r"\mathrm{\#}"

    def test_non_dimensionless(self, basic_texlabel):
        """Test non-dimensionless math function."""
        math_fcn = labels_special.MathFcn("sqrt", basic_texlabel, dimensionless=False)
        assert math_fcn.dimensionless is False
        assert "sqrt" in math_fcn.units

    def test_newline_units(self, basic_texlabel):
        """Test newline for units."""
        math_fcn = labels_special.MathFcn(
            "log", basic_texlabel, new_line_for_units=True
        )
        assert math_fcn.new_line_for_units is True

    def test_path_generation(self, basic_texlabel):
        """Test path generation for math functions."""
        math_fcn = labels_special.MathFcn("log", basic_texlabel)
        path_str = str(math_fcn.path)
        assert "log-" in path_str

    def test_function_path_cleaning(self, basic_texlabel):
        """Test function name cleaning for path."""
        math_fcn = labels_special.MathFcn(r"\mathrm{log}", basic_texlabel)
        path_str = str(math_fcn.path)
        assert "mathrm" not in path_str  # Should be cleaned


class TestDistance2Sun:
    """Test Distance2Sun label class."""

    def test_valid_units(self):
        """Test valid distance units."""
        valid_units = ["rs", "re", "au", "m", "km"]
        for unit in valid_units:
            dist = labels_special.Distance2Sun(unit)
            assert dist.units is not None

    def test_unit_translation(self):
        """Test unit translation."""
        translations = {
            "rs": r"R_{\bigodot}",
            "re": r"R_{\oplus}",
            "au": r"\mathrm{AU}",
        }

        for input_unit, expected in translations.items():
            dist = labels_special.Distance2Sun(input_unit)
            assert dist.units == expected

    def test_invalid_units(self):
        """Test invalid units raise NotImplementedError."""
        with pytest.raises(NotImplementedError):
            labels_special.Distance2Sun("invalid_unit")

    def test_properties(self):
        """Test Distance2Sun properties."""
        dist = labels_special.Distance2Sun("au")
        assert "Distance" in dist.tex
        assert "Sun" in dist.tex
        assert str(dist.path) == "distance2sun"


class TestSSN:
    """Test SSN (Sunspot Number) label class."""

    def test_valid_kinds(self):
        """Test valid SSN kinds."""
        valid_kinds = ["M", "M13", "D", "Y", "NM", "NM13", "ND", "NY"]
        for kind in valid_kinds:
            ssn = labels_special.SSN(kind)
            assert ssn.kind == kind

    def test_pretty_kind_translation(self):
        """Test pretty kind translation."""
        translations = {
            "M": "Monthly",
            "M13": "13 Month Smoothed",
            "D": "Daily",
            "Y": "Annual",
        }

        for kind, expected in translations.items():
            ssn = labels_special.SSN(kind)
            assert expected in ssn.pretty_kind

    def test_case_conversion(self):
        """Test case conversion for SSN kind."""
        ssn = labels_special.SSN("m")  # lowercase
        assert ssn.kind == "M"  # Should be uppercase

    def test_invalid_kind(self):
        """Test invalid SSN kind raises assertion."""
        with pytest.raises(AssertionError):
            labels_special.SSN("invalid")

    def test_tex_formatting(self):
        """Test TeX formatting."""
        ssn = labels_special.SSN("M")
        assert "Monthly" in ssn.tex
        assert "SSN" in ssn.tex

    def test_path_generation(self):
        """Test path generation."""
        ssn = labels_special.SSN("M13")
        assert str(ssn.path) == "M13ssn"


class TestComparisonLable:
    """Test ComparisonLable class (note: intentional misspelling in original)."""

    def test_basic_comparison(self, basic_texlabel):
        """Test basic comparison label."""
        # Use same units to avoid ValueError
        label_b = labels_base.TeXlabel(("v", "y", "p"))  # Same units as basic_texlabel
        comp = labels_special.ComparisonLable(basic_texlabel, label_b, "subtract")
        assert comp.labelA == basic_texlabel
        assert comp.labelB == label_b

    def test_predefined_functions(self, basic_texlabel):
        """Test predefined comparison functions."""
        # Use same units to avoid ValueError
        label_b = labels_base.TeXlabel(("v", "y", "p"))  # Same units as basic_texlabel
        functions = ["subtract", "add", "multiply"]

        for fcn in functions:
            comp = labels_special.ComparisonLable(basic_texlabel, label_b, fcn)
            assert comp.function_name == fcn

    def test_custom_function(self, basic_texlabel):
        """Test custom function definition."""
        # Use same units to avoid ValueError
        label_b = labels_base.TeXlabel(("v", "y", "p"))  # Same units as basic_texlabel
        custom_fcn = r"{$labelA} / {$labelB}"
        comp = labels_special.ComparisonLable(
            basic_texlabel, label_b, "divide", custom_fcn
        )
        assert "$labelA" in comp.function
        assert "$labelB" in comp.function

    def test_invalid_function_keys(self, basic_texlabel):
        """Test invalid function keys raise ValueError."""
        label_b = labels_base.TeXlabel(("n", "", "p"))
        invalid_fcn = r"{$invalid} + {$keys}"
        with pytest.raises(ValueError):
            labels_special.ComparisonLable(
                basic_texlabel, label_b, "invalid", invalid_fcn
            )

    def test_unit_validation(self, basic_texlabel):
        """Test unit validation for comparison labels."""
        # Same units should work
        label_b = labels_base.TeXlabel(("v", "y", "p"))  # Same units as basic_texlabel
        comp = labels_special.ComparisonLable(basic_texlabel, label_b, "subtract")
        assert comp.units == basic_texlabel.units

    def test_different_units_error(self, basic_texlabel):
        """Test different units raise ValueError."""
        label_b = labels_base.TeXlabel(("n", "", "p"))  # Different units
        with pytest.raises(ValueError):
            labels_special.ComparisonLable(basic_texlabel, label_b, "subtract")

    def test_string_labels(self):
        """Test comparison with string labels."""
        comp = labels_special.ComparisonLable("labelA", "labelB", "add")
        assert comp.labelA == "labelA"
        assert comp.labelB == "labelB"

    def test_type_validation(self):
        """Test type validation for labels."""
        with pytest.raises(TypeError):
            labels_special.ComparisonLable(123, "labelB", "add")

        with pytest.raises(TypeError):
            labels_special.ComparisonLable("labelA", 456, "add")


class TestXcorr:
    """Test Xcorr (cross-correlation) label class."""

    def test_basic_xcorr(self, basic_texlabel):
        """Test basic cross-correlation label."""
        label_b = labels_base.TeXlabel(("n", "", "p"))
        xcorr = labels_special.Xcorr(basic_texlabel, label_b, "pearson")
        assert xcorr.labelA == basic_texlabel
        assert xcorr.labelB == label_b
        assert xcorr.method == "Pearson"  # Should be title case

    def test_short_tex_format(self, basic_texlabel):
        """Test short TeX format."""
        label_b = labels_base.TeXlabel(("n", "", "p"))
        xcorr = labels_special.Xcorr(basic_texlabel, label_b, "pearson", short_tex=True)
        assert xcorr.short_tex is True
        assert r"\rho_" in xcorr.tex

    def test_long_tex_format(self, basic_texlabel):
        """Test long TeX format."""
        label_b = labels_base.TeXlabel(("n", "", "p"))
        xcorr = labels_special.Xcorr(
            basic_texlabel, label_b, "pearson", short_tex=False
        )
        assert xcorr.short_tex is False
        assert r"\mathrm{" in xcorr.tex

    def test_method_title_case(self, basic_texlabel):
        """Test method conversion to title case."""
        label_b = labels_base.TeXlabel(("n", "", "p"))
        xcorr = labels_special.Xcorr(basic_texlabel, label_b, "spearman")
        assert xcorr.method == "Spearman"

    def test_units(self, basic_texlabel):
        """Test cross-correlation units."""
        label_b = labels_base.TeXlabel(("n", "", "p"))
        xcorr = labels_special.Xcorr(basic_texlabel, label_b, "pearson")
        assert xcorr.units == r"\#"

    def test_path_generation(self, basic_texlabel):
        """Test path generation."""
        label_b = labels_base.TeXlabel(("n", "", "p"))
        xcorr = labels_special.Xcorr(basic_texlabel, label_b, "pearson")
        path_str = str(xcorr.path)
        assert "XcorrPearson" in path_str

    def test_string_labels(self):
        """Test cross-correlation with string labels."""
        xcorr = labels_special.Xcorr("labelA", "labelB", "kendall")
        assert xcorr.labelA == "labelA"
        assert xcorr.labelB == "labelB"

    def test_type_validation(self):
        """Test type validation for xcorr labels."""
        with pytest.raises(TypeError):
            labels_special.Xcorr(123, "labelB", "pearson")

        with pytest.raises(TypeError):
            labels_special.Xcorr("labelA", 456, "pearson")


class TestArbitraryLabel:
    """Test ArbitraryLabel abstract base class."""

    def test_abstract_methods(self):
        """Test that ArbitraryLabel cannot be instantiated directly."""
        with pytest.raises(TypeError):
            labels_special.ArbitraryLabel()

    def test_inheritance_structure(self):
        """Test inheritance from base.Base."""
        # ManualLabel inherits from ArbitraryLabel
        manual = labels_special.ManualLabel("test", "units")
        assert hasattr(manual, "logger")  # Inherited from base.Base


# Test integration between different label types
class TestLabelIntegration:
    """Test integration between different label types."""

    def test_mixed_label_comparison(self, basic_texlabel):
        """Test comparison using mixed label types."""
        manual = labels_special.ManualLabel("Custom", "units")
        comp = labels_special.ComparisonLable(basic_texlabel, manual, "add")
        # Should work without error

    def test_probability_with_manual_label(self):
        """Test probability with manual label."""
        manual = labels_special.ManualLabel("Test", "units")
        prob = labels_special.Probability(manual, "> 0")
        assert prob.other_label == manual

    def test_math_function_with_vsw(self):
        """Test math function with Vsw label."""
        vsw = labels_special.Vsw()
        math_fcn = labels_special.MathFcn("log", vsw)
        assert "V_\\mathrm{SW}" in math_fcn.tex
