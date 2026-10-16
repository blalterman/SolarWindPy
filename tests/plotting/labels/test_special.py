import re

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
            assert isinstance(dist.units, str), f"units should be str for '{unit}'"

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


class TestComparisonLabel:
    """Test ComparisonLabel class."""

    def test_basic_comparison(self, basic_texlabel):
        """Test basic comparison label."""
        # Use same units to avoid ValueError
        label_b = labels_base.TeXlabel(("v", "y", "p"))  # Same units as basic_texlabel
        comp = labels_special.ComparisonLabel(basic_texlabel, label_b, "subtract")
        assert comp.labelA == basic_texlabel
        assert comp.labelB == label_b

    def test_predefined_functions(self, basic_texlabel):
        """Test predefined comparison functions."""
        # Use same units to avoid ValueError
        label_b = labels_base.TeXlabel(("v", "y", "p"))  # Same units as basic_texlabel
        functions = ["subtract", "add", "multiply"]

        for fcn in functions:
            comp = labels_special.ComparisonLabel(basic_texlabel, label_b, fcn)
            assert comp.function_name == fcn

    def test_custom_function(self, basic_texlabel):
        """Test custom function definition."""
        # Use same units to avoid ValueError
        label_b = labels_base.TeXlabel(("v", "y", "p"))  # Same units as basic_texlabel
        custom_fcn = r"{$labelA} / {$labelB}"
        comp = labels_special.ComparisonLabel(
            basic_texlabel, label_b, "divide", custom_fcn
        )
        assert "$labelA" in comp.function
        assert "$labelB" in comp.function

    def test_invalid_function_keys(self, basic_texlabel):
        """Test invalid function keys raise ValueError."""
        label_b = labels_base.TeXlabel(("n", "", "p"))
        invalid_fcn = r"{$invalid} + {$keys}"
        with pytest.raises(ValueError):
            labels_special.ComparisonLabel(
                basic_texlabel, label_b, "invalid", invalid_fcn
            )

    def test_unit_validation(self, basic_texlabel):
        """Test unit validation for comparison labels."""
        # Same units should work
        label_b = labels_base.TeXlabel(("v", "y", "p"))  # Same units as basic_texlabel
        comp = labels_special.ComparisonLabel(basic_texlabel, label_b, "subtract")
        assert comp.units == basic_texlabel.units

    def test_different_units_error(self, basic_texlabel):
        """Test different units raise ValueError."""
        label_b = labels_base.TeXlabel(("n", "", "p"))  # Different units
        with pytest.raises(ValueError):
            labels_special.ComparisonLabel(basic_texlabel, label_b, "subtract")

    @pytest.mark.parametrize("which", ["labelA", "labelB"])
    def test_string_label_raises_type_error_suggesting_manual_label(
        self, basic_texlabel, which
    ):
        """A plain string for either label is refused, naming ``ManualLabel``.

        Author decision (2026-10-16): ``ComparisonLabel`` requires label objects.

        ON FAILURE: the code is wrong.
        """
        args = {"labelA": basic_texlabel, "labelB": basic_texlabel, which: "n_p"}
        expected = (
            f"{which} must be a solarwindpy.plotting.labels.base.Base "
            "(e.g. TeXlabel or ManualLabel), got str: 'n_p'"
        )
        with pytest.raises(TypeError, match=f"^{re.escape(expected)}$"):
            labels_special.ComparisonLabel(args["labelA"], args["labelB"], "add")

    def test_non_label_raises_type_error(self, basic_texlabel):
        """A number for either label is refused with a TypeError.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(TypeError, match="^labelA must be .* got int: 123$"):
            labels_special.ComparisonLabel(123, basic_texlabel, "add")
        with pytest.raises(TypeError, match="^labelB must be .* got int: 456$"):
            labels_special.ComparisonLabel(basic_texlabel, 456, "add")


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
        """A ``TeXlabel`` and a ``ManualLabel`` in the same units combine, sharing them.

        ``ManualLabel`` exposes ``units`` (author decision 2026-10-16), so its
        units take part in the same-units check.

        ON FAILURE: the code is wrong.
        """
        manual = labels_special.ManualLabel("Custom", "kms")
        comp = labels_special.ComparisonLabel(basic_texlabel, manual, "add")
        assert comp.units == r"\mathrm{km \; s^{-1}}"

    def test_mixed_label_comparison_in_different_units_raises(self, basic_texlabel):
        """A ``ManualLabel`` in other units than the ``TeXlabel`` is refused.

        ON FAILURE: the code is wrong.
        """
        manual = labels_special.ManualLabel("Custom", "units")
        with pytest.raises(ValueError, match="they must be the same"):
            labels_special.ComparisonLabel(basic_texlabel, manual, "add")

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


# Each class that wraps another label, built with the given ``other_label``.
_WRAPS_OTHER_LABEL = {
    "Probability": lambda other: labels_special.Probability(other, "> 5"),
    "CountOther": lambda other: labels_special.CountOther(other, "> 5"),
    "MathFcn": lambda other: labels_special.MathFcn("log", other),
    "AbsoluteValue": lambda other: labels_special.AbsoluteValue(other),
}


@pytest.mark.parametrize("name", sorted(_WRAPS_OTHER_LABEL))
def test_plain_string_other_label_raises_type_error_naming_accepted_type(name):
    """A ``str`` other_label is rejected at construction, not later on ``.tex``.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(TypeError, match=r"other_label must be a .*Base.*got str"):
        _WRAPS_OTHER_LABEL[name]("n_p")


@pytest.mark.parametrize("name", sorted(_WRAPS_OTHER_LABEL))
def test_label_object_other_label_is_stored(name, basic_texlabel):
    """A label object is accepted and stored unchanged.

    ON FAILURE: the code is wrong.
    """
    assert _WRAPS_OTHER_LABEL[name](basic_texlabel).other_label is basic_texlabel


# ---------------------------------------------------------------------------
# Exact strings. Each expected value is the class's format string filled by
# hand from the wrapped label: TeXlabel(("n", "", "p1")) has tex "n_{p_1}",
# units "\mathrm{cm}^{-3}" and path "n_p1" (default template, species table).
# ---------------------------------------------------------------------------

_N_P1 = ("n", "", "p1")


@pytest.fixture()
def n_p1():
    """``TeXlabel`` for proton-1 density: tex ``n_{p_1}``, path ``n_p1``."""
    return labels_base.TeXlabel(_N_P1)


_COMPARISONS = [
    ("> 5", "GT_5"),
    ("< 5", "LT_5"),
    (">= 5", "GEQ_5"),
    ("<= 5", "LEQ_5"),
    (r"\gt 5", "GT_5"),
    (r"\lt 5", "LT_5"),
    (r"\geq 5", "GEQ_5"),
    (r"\leq 5", "LEQ_5"),
    (r"\neq 5", "NEQ_5"),
    (r"\eq 5", "EQ_5"),
    ("== 5", "EQ_5"),
    ("!= 5", "NEQ_5"),
]


@pytest.mark.parametrize("comparison, spelled", _COMPARISONS)
@pytest.mark.parametrize(
    "cls, prefix",
    [(labels_special.Probability, "prob"), (labels_special.CountOther, "cnt")],
    ids=["Probability", "CountOther"],
)
def test_comparison_path_spells_operator_and_replaces_spaces(
    n_p1, cls, prefix, comparison, spelled
):
    """The save path spells the operator in capitals and writes spaces as ``_``.

    Author decisions (2026-10-16): ``>=`` and ``<=`` map to GEQ and LEQ, and
    CountOther paths replace spaces as Probability does.

    ON FAILURE: the code is wrong.
    """
    label = cls(n_p1, comparison)
    assert label.path == Path(f"{prefix}-n_p1-{spelled}")


def test_wrapped_label_path_spaces_become_dashes(n_p1):
    """A space in the wrapped label's path is written ``-`` in the save path.

    ON FAILURE: the code is wrong.
    """
    other = labels_special.ManualLabel("x", "", path="a b")
    assert labels_special.Probability(other, "> 5").path == Path("prob-a-b-GT_5")
    assert labels_special.CountOther(other, "> 5").path == Path("cnt-a-b-GT_5")


def test_probability_tex_units_and_string(n_p1):
    r"""``Probability`` reads ``\mathrm{Prob.}(<tex> <comparison>)`` in percent, spaces as ``\,``.

    ON FAILURE: the code is wrong.
    """
    label = labels_special.Probability(n_p1, "> 5")
    assert label.tex == r"\mathrm{Prob.}(n_{p_1} \, > \, 5)"
    assert str(label) == r"$\mathrm{Prob.}(n_{p_1} \, > \, 5) \; [\%]$"


def test_count_other_tex_and_both_string_forms(n_p1):
    r"""``CountOther`` reads ``\mathrm{Count.}(<tex> <comparison>)`` in counts.

    ON FAILURE: the code is wrong.
    """
    label = labels_special.CountOther(n_p1, "> 5")
    assert label.tex == r"\mathrm{Count.}(n_{p_1} \, > \, 5)"
    assert str(label) == r"$\mathrm{Count.}(n_{p_1} \, > \, 5) \; [\#]$"
    two_lines = labels_special.CountOther(n_p1, "> 5", new_line_for_units=True)
    assert str(two_lines) == (r"$\mathrm{Count.}(n_{p_1} \, > \, 5) $" "\n" r"$ [\#]$")


def test_count_other_without_comparison_stores_empty_string(n_p1):
    """A missing comparison is stored as the empty string.

    ON FAILURE: the code is wrong.
    """
    assert labels_special.CountOther(n_p1).comparison == ""


@pytest.mark.parametrize(
    "norm, tex, path",
    [
        (None, r"\mathrm{Count}", "count"),
        ("c", r"\mathrm{Col. \, Norm \, Count}", "count/Cnorm"),
        ("r", r"\mathrm{Row \, Norm \, Count}", "count/Rnorm"),
        ("t", r"\mathrm{Total \, Norm \, Count}", "count/Tnorm"),
        ("d", r"\mathrm{Probability \, Density}", "count/Dnorm"),
        ("cd", r"\mathrm{1D \, Probability \, Density}", "count/CDnorm"),
        ("rd", r"\mathrm{1D \, Probability \, Density}", "count/RDnorm"),
    ],
)
def test_count_tex_and_path_per_normalization(norm, tex, path):
    r"""``Count`` names its normalization in ``tex`` (spaces as ``\,``) and in ``path``.

    ON FAILURE: the code is wrong.
    """
    label = labels_special.Count(norm)
    assert label.tex == tex
    assert label.path == Path(path)
    assert str(label) == rf"${tex} \; [\#]$"


def test_math_fcn_tex_units_and_both_string_forms(n_p1):
    r"""``MathFcn`` reads ``\mathrm{<fcn>}(<tex>)``, dimensionless unless told otherwise.

    ON FAILURE: the code is wrong.
    """
    label = labels_special.MathFcn("log", n_p1)
    assert label.tex == r"\mathrm{log}(n_{p_1})"
    assert str(label) == r"$\mathrm{log}(n_{p_1}) \; \left[\mathrm{\#}\right]$"
    two_lines = labels_special.MathFcn("log", n_p1, new_line_for_units=True)
    assert str(two_lines) == (
        r"$\mathrm{log}(n_{p_1}) $" "\n" r"$ \left[\mathrm{\#}\right]$"
    )
    dimensional = labels_special.MathFcn("log", n_p1, dimensionless=False)
    assert dimensional.units == r"\mathrm{log}\left(\mathrm{cm}^{-3}\right)"


def test_math_fcn_spaces_in_wrapped_tex_become_thin_spaces():
    r"""A space in the wrapped label's TeX is written ``\,``.

    ON FAILURE: the code is wrong.
    """
    other = labels_special.ManualLabel("a b", "")
    assert labels_special.MathFcn("log", other).tex == r"\mathrm{log}(a \, b)"


@pytest.mark.parametrize(
    "fcn, path",
    [
        (r"\mathrm{log_{10}}", "log_10-n_p1"),
        (r"\ln", "ln-n_p1"),
        ("a/b", "a-OV-b-n_p1"),
    ],
    ids=["mathrm-braces", "backslash", "slash"],
)
def test_math_fcn_path_strips_tex_from_function_name(n_p1, fcn, path):
    r"""The save path drops ``\mathrm``, braces and backslashes and writes ``/`` as ``-OV-``.

    ON FAILURE: the code is wrong.
    """
    assert labels_special.MathFcn(fcn, n_p1).path == Path(path)


def test_math_fcn_none_function_is_empty_string(n_p1):
    """``set_function(None)`` stores the empty string, as documented.

    ON FAILURE: the code is wrong.
    """
    assert labels_special.MathFcn(None, n_p1).function == ""


def test_absolute_value_tex_units_path_and_both_string_forms(n_p1):
    r"""``AbsoluteValue`` wraps ``tex`` in ``\left| \right|`` and keeps the units.

    ON FAILURE: the code is wrong.
    """
    label = labels_special.AbsoluteValue(n_p1)
    assert label.tex == r"\left|n_{p_1}\right|"
    assert label.units == r"\mathrm{cm}^{-3}"
    assert label.path == Path("abs-n_p1")
    assert str(label) == r"$\left|n_{p_1}\right| \; \left[\mathrm{cm}^{-3}\right]$"
    two_lines = labels_special.AbsoluteValue(n_p1, new_line_for_units=1)
    assert two_lines.new_line_for_units is True
    assert str(two_lines) == (
        r"$\left|n_{p_1}\right| $" "\n" r"$ \left[\mathrm{cm}^{-3}\right]$"
    )


def test_fixed_special_labels_print_exact_strings():
    """``Vsw``, ``CarringtonRotation``, ``Power``, ``Distance2Sun`` and ``SSN`` strings.

    ON FAILURE: the code is wrong.
    """
    assert str(labels_special.Vsw()) == (
        r"$V_\mathrm{SW} \; \left[\mathrm{km \, s^{-1}}\right]$"
    )
    assert str(labels_special.CarringtonRotation()) == r"$\mathrm{CR} \; [\#]$"
    long_cr = labels_special.CarringtonRotation(short_label=False)
    assert long_cr.tex == r"\mathrm{Carrington \; Rotation}"
    assert str(labels_special.Power()) == r"$\mathrm{Power} \; [\mathrm{\#}]$"
    assert str(labels_special.Distance2Sun("m")) == (
        r"$\mathrm{Distance \; to \; Sun} \; [\mathrm{m}]$"
    )
    assert str(labels_special.SSN("M13")) == (
        r"$\mathrm{13 \; Month \; Smoothed \; SSN} \; [\#]$"
    )


def test_distance2sun_unknown_units_error_names_them():
    """An unknown distance unit raises NotImplementedError naming it.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(
        NotImplementedError, match="^Unrecognized distance2sun units furlong$"
    ):
        labels_special.Distance2Sun("furlong")


def test_wrapping_label_type_error_message_is_exact():
    """The TypeError for a non-label ``other_label`` names the type and suggests labels.

    ON FAILURE: the code is wrong.
    """
    expected = (
        "other_label must be a solarwindpy.plotting.labels.base.Base "
        "(e.g. TeXlabel or ManualLabel), got str: 'n_p'"
    )
    with pytest.raises(TypeError, match=f"^{re.escape(expected)}$"):
        labels_special.Probability("n_p")


class TestManualLabelUnits:
    """``ManualLabel`` exposes ``units`` and ``with_units`` like every label."""

    def test_units_and_with_units(self):
        r"""``units`` is the translated unit; ``with_units`` wraps tex in ``\mathrm``.

        Author decision (2026-10-16): ``ManualLabel`` exposes ``units`` and
        ``with_units``; before it, both raised AttributeError.

        ON FAILURE: the code is wrong.
        """
        label = labels_special.ManualLabel("Test Label", "b")
        assert label.units == r"\mathrm{nT}"
        assert label.with_units == r"$\mathrm{Test \; Label} \; [\mathrm{nT}]$"
        assert str(label) == label.with_units

    def test_empty_units_leave_no_trailing_space(self):
        """With empty units the label is the bare TeX, without a trailing space.

        Author decision (2026-10-16).

        ON FAILURE: the code is wrong.
        """
        assert str(labels_special.ManualLabel("Test", "")) == r"$\mathrm{Test}$"

    def test_dollar_signs_are_stripped_from_tex_and_units(self):
        """Surrounding ``$`` are stripped from tex and units, and nothing else.

        ON FAILURE: the code is wrong.
        """
        label = labels_special.ManualLabel("$X$", "$X$")
        assert label.tex == "X"
        assert label.units == "X"


class TestComparisonLabelStrings:
    """Exact TeX, units, paths and errors of ``ComparisonLabel``."""

    @pytest.fixture()
    def n_a(self):
        r"""``TeXlabel`` for alpha density: tex ``n_{\alpha}``, path ``n_a``."""
        return labels_base.TeXlabel(("n", "", "a"))

    @pytest.mark.parametrize(
        "name, tex",
        [
            ("subtract", r"{n_{\alpha}} - {n_{p_1}}"),
            ("add", r"{n_{\alpha}} + {n_{p_1}}"),
            ("multiply", r"{n_{\alpha}} \times {n_{p_1}}"),
        ],
    )
    def test_built_in_functions(self, n_a, n_p1, name, tex):
        """Each built-in function fills its template with both labels' TeX.

        ON FAILURE: the code is wrong.
        """
        label = labels_special.ComparisonLabel(n_a, n_p1, name)
        assert label.tex == tex
        assert label.units == r"\mathrm{cm}^{-3}"
        assert label.path == Path(f"{name}-n_a-n_p1")
        assert str(label) == rf"${tex} \; [\mathrm{{cm}}^{{-3}}]$"

    def test_repeated_thin_spaces_collapse_to_one(self, n_a, n_p1):
        r"""Runs of ``\,`` in the filled template collapse to one, including at the start.

        ON FAILURE: the code is wrong.
        """
        fcn = r"\,\,{$labelA}\,\,\,{$labelB}"
        label = labels_special.ComparisonLabel(n_a, n_p1, "f", fcn)
        assert label.tex == r"\,{n_{\alpha}}\,{n_{p_1}}"

    def test_path_strips_tex_spacing(self):
        r"""TeX spacing commands in either label's path are dropped and spaces become ``-``.

        Author decision (2026-10-16): ComparisonLabel paths strip TeX spacing.

        ON FAILURE: the code is wrong.
        """
        a = labels_special.ManualLabel("A", "kms", path=r"n \; p")
        b = labels_special.ManualLabel("B", "kms", path=r"b\,c")
        label = labels_special.ComparisonLabel(a, b, "subtract")
        assert label.path == Path("subtract-n-p-b-c")

    def test_label_without_units_gives_unknown_units(self, n_a):
        """If either label has no units, the comparison's units are ``???``.

        ON FAILURE: the code is wrong.
        """
        from solarwindpy.plotting.labels.datetime import DateTime

        label = labels_special.ComparisonLabel(n_a, DateTime("Year"), "subtract")
        assert label.units == "???"

    def test_different_units_error_names_both(self, n_a):
        """Different units raise ValueError naming each label's units.

        ON FAILURE: the code is wrong.
        """
        v = labels_base.TeXlabel(("v", "x", "p"))
        expected = (
            "If both ComparisonLabel labels have units, they must be the same.\n"
            "labelA : \\mathrm{cm}^{-3}\n"
            "labelB : \\mathrm{km \\; s^{-1}}\n"
        )
        with pytest.raises(ValueError) as excinfo:
            labels_special.ComparisonLabel(n_a, v, "subtract")
        assert str(excinfo.value) == expected

    def test_unknown_function_name_raises_value_error(self, n_a, n_p1):
        """A name with no built-in template and no ``fcn`` raises ValueError.

        Author decision (2026-10-16): ``set_function`` raises its intended
        ValueError; before the fix this was a TypeError from parsing None.

        ON FAILURE: the code is wrong.
        """
        expected = (
            "ComparisonLabel has no built-in function 'divide'; pass fcn or use "
            "one of add, multiply, subtract."
        )
        with pytest.raises(ValueError, match=f"^{re.escape(expected)}$"):
            labels_special.ComparisonLabel(n_a, n_p1, "divide")

    @pytest.mark.parametrize(
        "fcn, keys",
        [
            ("$labelA / $labelB", ""),
            (r"{$labelA} - x", "$labelA"),
            (r"{$invalid} + {$keys}", "$invalid,$keys"),
        ],
        ids=["no-braced-keys", "one-key", "two-wrong-keys"],
    )
    def test_template_missing_a_key_raises_value_error(self, n_a, n_p1, fcn, keys):
        """A template lacking either braced key raises ValueError listing the keys found.

        Author decision (2026-10-16): ``set_function`` raises its intended
        ValueError; a template with no braced key used to raise TypeError.

        ON FAILURE: the code is wrong.
        """
        expected = (
            "ComparisonLabel's function must have the keys "
            f'"$labelA" and "$labelB".\nkeys : {keys}\n'
        )
        with pytest.raises(ValueError) as excinfo:
            labels_special.ComparisonLabel(n_a, n_p1, "f", fcn)
        assert str(excinfo.value) == expected


class TestXcorrStrings:
    """Exact TeX, strings and paths of ``Xcorr``."""

    def test_long_and_short_tex_from_labels(self, n_p1):
        """Long TeX names the method; short TeX is rho with its initial.

        ON FAILURE: the code is wrong.
        """
        v = labels_base.TeXlabel(("v", "x", "a"))
        long_form = labels_special.Xcorr(n_p1, v, "pearson")
        assert long_form.tex == r"\mathrm{{Pearson}}(n_{p_1},{v}_{{X};{\alpha}})"
        assert str(long_form) == (
            r"$\mathrm{{Pearson}}(n_{p_1},{v}_{{X};{\alpha}}) \; [\#]$"
        )
        assert long_form.path == Path("XcorrPearson-n_p1-v_x_a")
        short = labels_special.Xcorr(n_p1, v, "pearson", short_tex=True)
        assert short.tex == r"\rho_{P}(n_{p_1},{v}_{{X};{\alpha}})"

    def test_string_constituents_spaces_and_tex_spacing(self):
        r"""Spaces in string constituents become one ``\,`` in TeX and ``-`` in the path.

        Author decision (2026-10-16): Xcorr paths strip TeX spacing.

        ON FAILURE: the code is wrong.
        """
        label = labels_special.Xcorr("a b", r"c \, d", "kendall", short_tex=True)
        assert label.tex == r"\rho_{K}(a\,b,c\,d)"
        assert label.path == Path("XcorrKendall-a-b-c-d")


def _all_label_factories():
    """One factory per public label class, each taking ``description``."""
    from solarwindpy.plotting.labels import composition, datetime
    from solarwindpy.plotting.labels.elemental_abundance import ElementalAbundance

    n = labels_base.TeXlabel(_N_P1)
    return {
        "TeXlabel": lambda d: labels_base.TeXlabel(_N_P1, description=d),
        "ManualLabel": lambda d: labels_special.ManualLabel("M", "b", description=d),
        "Vsw": lambda d: labels_special.Vsw(description=d),
        "CarringtonRotation": lambda d: labels_special.CarringtonRotation(
            description=d
        ),
        "Count": lambda d: labels_special.Count(description=d),
        "Power": lambda d: labels_special.Power(description=d),
        "Probability": lambda d: labels_special.Probability(n, "> 5", description=d),
        "CountOther": lambda d: labels_special.CountOther(n, "> 5", description=d),
        "MathFcn": lambda d: labels_special.MathFcn("log", n, description=d),
        "AbsoluteValue": lambda d: labels_special.AbsoluteValue(n, description=d),
        "Distance2Sun": lambda d: labels_special.Distance2Sun("m", description=d),
        "SSN": lambda d: labels_special.SSN("M", description=d),
        "ComparisonLabel": lambda d: labels_special.ComparisonLabel(
            n, n, "subtract", description=d
        ),
        "Xcorr": lambda d: labels_special.Xcorr(n, n, "pearson", description=d),
        "Timedelta": lambda d: datetime.Timedelta("1h", description=d),
        "DateTime": lambda d: datetime.DateTime("Year", description=d),
        "Epoch": lambda d: datetime.Epoch("hour", "day", description=d),
        "Frequency": lambda d: datetime.Frequency("1h", description=d),
        "January1st": lambda d: datetime.January1st(description=d),
        "Ion": lambda d: composition.Ion("O", 6, description=d),
        "ChargeStateRatio": lambda d: composition.ChargeStateRatio(
            ("O", 7), ("O", 6), description=d
        ),
        "ElementalAbundance": lambda d: ElementalAbundance("Fe", "O", description=d),
    }


@pytest.mark.parametrize("name", sorted(_all_label_factories()))
def test_description_argument_is_printed_above_the_label(name):
    """A ``description`` passed to the constructor heads the label on its own line.

    The expected string is the same label built without a description,
    prefixed by the description and a newline (``Base._format_with_description``).

    ON FAILURE: the code is wrong.
    """
    factory = _all_label_factories()[name]
    assert str(factory("Protons")) == "Protons\n" + str(factory(None))
