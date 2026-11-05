from pathlib import Path
import pytest
import logging

from solarwindpy.plotting.labels import base


@pytest.fixture(scope="module")
def labels_base():
    """The public :mod:`solarwindpy.plotting.labels.base` module."""
    return base


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


def test_run_species_substitution(texlabel_basic):
    """``make_species`` translates each species code in a pattern to TeX.

    ON FAILURE: the code is wrong.
    """
    cases = {
        "p": "p",
        "p1+p2": "p_1+p_2",
        "a+p1": "\\alpha+p_1",
        "Fe": "\\mathrm{Fe}",
    }
    for pattern, expected in cases.items():
        assert texlabel_basic.make_species(pattern) == expected


def test_texlabel_attributes(texlabel_basic):
    """Check attributes of a typical :class:`TeXlabel`."""
    assert texlabel_basic.tex == "{v}_{{x};{p}}"
    assert texlabel_basic.units == "\\mathrm{km \\; s^{-1}}"
    assert texlabel_basic.path == Path("v_x_p")
    assert (
        texlabel_basic.with_units
        == "${v}_{{x};{p}} \\; \\left[\\mathrm{km \\; s^{-1}}\\right]$"
    )


def test_texlabel_ratio_attributes(texlabel_ratio):
    """Check attributes of a ratio :class:`TeXlabel`."""
    assert texlabel_ratio.tex == "{v}_{{x};{p}}/n_{p}"
    assert texlabel_ratio.units == "\\mathrm{km \\; s^{-1}}/\\mathrm{cm}^{-3}"
    assert texlabel_ratio.path == Path("v_x_p-OV-n_p")
    assert (
        texlabel_ratio.with_units
        == "${v}_{{x};{p}}/n_{p} \\; \\left[\\mathrm{km \\; s^{-1}}/\\mathrm{cm}^{-3}\\right]$"
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
        ("c", "Column"),
        ("r", "Row"),
        ("t", "Max"),
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
    assert "{v}_{{x};{p}}" in texlabel_with_error.tex


def test_texlabel_newline_units(texlabel_newline_units):
    """Test newline separation for units."""
    assert "$\n$" in texlabel_newline_units.with_units


def test_species_substitution_comprehensive(labels_base):
    """Each species code, isotope and "+"-sum translates to its TeX form.

    ON FAILURE: the code is wrong.
    """
    test_cases = {
        "p": "p",
        "p1": "p_1",
        "p2": "p_2",
        "a": "\\alpha",
        "a1": "\\alpha_1",
        "a2": "\\alpha_2",
        "e": "e^-",
        "he": "\\mathrm{He}",
        "Fe": "\\mathrm{Fe}",
        "3He": "^{3}\\mathrm{He}",
        "16O": "^{16}\\mathrm{O}",
        "p1+p2": "p_1+p_2",
        "a+Fe": "\\alpha+\\mathrm{Fe}",
    }

    label = labels_base.TeXlabel(("n", "", "p"))
    for pattern, expected in test_cases.items():
        result = label.make_species(pattern)
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
        ("v", "x", "p"): "x",
        ("v", "y", "p"): "y",
        ("v", "z", "p"): "z",
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
        ("beta", "", "p"): "\\#",
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
    assert "{unknown_measurement}_{{x};{p}}" in label.tex


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
    """``mcs0`` and ``mcs1`` expose numerator and denominator as m, c, s.

    ON FAILURE: the code is wrong.
    """
    label = labels_base.TeXlabel(("v", "x", "p"), ("n", "", "a"))
    assert (label.mcs0.m, label.mcs0.c, label.mcs0.s) == ("v", "x", "p")
    assert (label.mcs1.m, label.mcs1.c, label.mcs1.s) == ("n", "", "a")
    assert labels_base.TeXlabel(("v", "x", "p")).mcs1 is None


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
    valid_values = [None, "c", "r", "t", "d", "cd", "rd"]

    for val in valid_values:
        label = labels_base.TeXlabel(("v", "x", "p"), axnorm=val)
        assert label.axnorm == val

    # Test invalid axnorm
    with pytest.raises(ValueError):
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
    """Test handling of empty strings in _MCS components."""
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


class TestNameFeature:
    """``name``: the first line of a label in publication format.

    ON FAILURE: the code is wrong.
    """

    def test_default_name_is_the_registry_name(self, labels_base):
        assert labels_base.TeXlabel(("v", "x", "p")).name == "Velocity"

    def test_set_name_stores_a_string(self, labels_base):
        label = labels_base.TeXlabel(("v", "x", "p"))
        label.set_name(42)
        assert label.name == "42"

    def test_set_name_none_restores_the_default(self, labels_base):
        label = labels_base.TeXlabel(("v", "x", "p"), name="Speed")
        assert label.name == "Speed"
        label.set_name(None)
        assert label.name == "Velocity"

    def test_name_is_not_shown_in_the_default_format(self, labels_base):
        label = labels_base.TeXlabel(("v", "x", "p"), name="Speed")
        assert label.with_units == (
            "${v}_{{x};{p}} \\; \\left[\\mathrm{km \\; s^{-1}}\\right]$"
        )

    def test_name_heads_the_label_in_publication_format(self, labels_base):
        label = labels_base.TeXlabel(
            ("v", "x", "p"), name="Speed", publication_format=True
        )
        assert str(label) == "Speed\n" + str(labels_base.TeXlabel(("v", "x", "p")))

    def test_name_with_axnorm_and_ratio(self, labels_base):
        norm = labels_base.TeXlabel(
            ("n", "", "p"), axnorm="t", name="count", publication_format=True
        )
        assert norm.with_units.startswith("count\n")
        assert "Max" in norm.with_units
        ratio = labels_base.TeXlabel(
            ("v", "x", "p"), ("n", "", "p"), name="v/n", publication_format=True
        )
        assert ratio.with_units.startswith("v/n\n")

    def test_empty_name_adds_no_line(self, labels_base):
        label = labels_base.TeXlabel(("v", "x", "p"), name="", publication_format=True)
        assert "\n" not in label.with_units

    def test_description_is_gone(self, labels_base):
        label = labels_base.TeXlabel(("v", "x", "p"))
        assert not hasattr(label, "description")
        assert not hasattr(label, "set_description")


@pytest.mark.parametrize(
    "mcs, tex",
    [
        (("qpar", "", "p1"), "q_{{\\parallel};{p_1}}"),
        (("Wk", "", "p1"), "W_{K;{p_1}}"),
        (("Wk", "", "a"), "W_{K;{\\alpha}}"),
    ],
    ids=["heat_flux_q", "kinetic_energy_flux_protons", "kinetic_energy_flux_alphas"],
)
def test_energy_flux_labels_match_author_declared_contract(labels_base, mcs, tex):
    """Heat flux is labelled q and kinetic energy flux W_K, both in uW m^-2.

    The symbols are the author's declared contract; the unit matches what
    Plasma.qpar and Plasma.Wk report.

    ON FAILURE: the label changed; confirm with the author before updating.
    """
    label = labels_base.TeXlabel(mcs)
    assert label.tex == tex
    assert label.units == "\\mathrm{\\mu W \\, m^{-2}}"


@pytest.mark.parametrize(
    "mcs, tex",
    [
        (("b", "lat", ""), "B_{\\lambda}"),
        (("b", "colat", ""), "B_{\\theta}"),
        (("v", "lat", "p1"), "{v}_{{\\lambda};{p_1}}"),
        (("v", "colat", "p1"), "{v}_{{\\theta};{p_1}}"),
    ],
    ids=["b_lat", "b_colat", "v_lat_p1", "v_colat_p1"],
)
def test_latitude_is_lambda_and_colatitude_is_theta(labels_base, mcs, tex):
    """A latitude component renders as lambda and a colatitude component as theta.

    The symbols are the author's declared contract, matching Vector.lat (angle
    above the xy-plane) and Vector.colat (angle from +z); both are in degrees.

    ON FAILURE: the label changed; confirm with the author before updating.
    """
    label = labels_base.TeXlabel(mcs)
    assert label.tex == tex
    assert label.units == "\\mathrm{deg.}"


@pytest.mark.parametrize(
    "mcs, units",
    [
        (("cos_phi", "", "p1"), "\\#"),
        (("ratio", "", ""), "\\#"),
        (("Qhat", "", "p1"), "\\#"),
        (("dbeta", "", "p1"), "\\#"),
        (("eth", "", "p1"), "\\mathrm{eV}"),
    ],
    ids=["cos_phi", "ratio", "Qhat", "dbeta", "eth"],
)
def test_measurement_units_follow_author_decision(labels_base, mcs, units):
    """``cos_phi``, ``ratio``, ``Qhat`` and ``dbeta`` are dimensionless; ``eth`` is eV.

    The units are the author's decision (2026-10-16 remaining-module cards);
    before it these measurements fell through to the unknown units ``???``.

    ON FAILURE: the code is wrong, unless the author changed these units.
    """
    assert labels_base.TeXlabel(mcs).units == units


@pytest.mark.parametrize(
    "mcs, tex",
    [
        # Default template "{$M}_{{$C};{$S}}" with C and S empty: the "{};",
        # "{}" and trailing "_{}" clean-up rules leave the bare measurement.
        (("beta", "", ""), "{\\beta}"),
        (("Qhat", "", ""), "{\\widehat{q}}"),
        # S given, C empty: "{};" is removed from the subscript.
        (("Qhat", "", "p1"), "{\\widehat{q}}_{{p_1}}"),
        # A component with no TeX translation is used as written.
        (("v", "w", "p"), "{v}_{{w};{p}}"),
        # "_err" wraps the label in sigma().
        (("v_err", "x", "p"), "\\sigma({v}_{{x};{p}})"),
        # "caani" template "... \; ($C)" with C empty drops "\; ()".
        (("caani", "", ""), "C^{(\\mathrm{Ani})}_{A}"),
        # "nuc" template "\nu_{$C,$S}": an empty side drops its comma.
        (("nuc", "x", ""), "\\nu_{x}"),
        (("nuc", "", "p1"), "\\nu_{p_1}"),
        # "SEP_differential_flux" template "{{$S}} \: dJ/dE" with S empty
        # drops "{{}}" and the leading space.
        (("SEP_differential_flux", "", ""), "\\: dJ/dE"),
        # "SEP_spectrum_index" template "\gamma_{{$S}}" with S empty: the
        # dangling "_" is stripped.
        (("SEP_spectrum_index", "", ""), "\\gamma"),
    ],
    ids=lambda v: "-".join(v) if isinstance(v, tuple) else None,
)
def test_texlabel_tex_is_the_cleaned_template(labels_base, mcs, tex):
    """``tex`` is the measurement's template filled from M, C, S, with empty parts removed.

    Each expected string is the template in ``base._templates`` (or the
    default ``{$M}_{{$C};{$S}}``) filled by hand from the component and
    species tables, then stripped of the empty groups the comment names.

    ON FAILURE: the code is wrong.
    """
    assert labels_base.TeXlabel(mcs).tex == tex


@pytest.mark.parametrize(
    "mcs, path",
    [
        # "/" in each of M, C, S becomes "-OV-".
        (("a/b", "c/d", "e/f"), "a-OV-b_c-OV-d_e-OV-f"),
        # Commas and dots are removed.
        (("t.x", "", "p,q"), "tx_pq"),
        # Only "_" is stripped from the ends; a capital X survives.
        (("X", "", ""), "X"),
    ],
    ids=["slash", "comma-and-dot", "capital-x"],
)
def test_texlabel_path_joins_mcs_with_underscores(labels_base, mcs, path):
    """``path`` joins M, C and S with ``_`` after replacing ``/`` and dropping ``,`` and ``.``.

    ON FAILURE: the code is wrong.
    """
    assert labels_base.TeXlabel(mcs).path == Path(path)


def test_texlabel_longitude_component_has_degree_units(labels_base):
    """A ``lon`` component takes degree units whatever the measurement.

    ON FAILURE: the code is wrong.
    """
    assert labels_base.TeXlabel(("v", "lon", "p1")).units == "\\mathrm{deg.}"


def test_texlabel_unknown_measurement_has_unknown_units(labels_base):
    """A measurement missing from the units table has units ``???``.

    ON FAILURE: the code is wrong.
    """
    assert labels_base.TeXlabel(("zz", "x", "p")).units == "???"


@pytest.mark.parametrize(
    "mcs0, mcs1, units",
    [
        (("v", "x", "p"), ("zz", "", "p"), r"\mathrm{km \; s^{-1}}/???"),
        (("zz", "", "p"), ("v", "x", "p"), r"???/\mathrm{km \; s^{-1}}"),
        (
            ("v_err", "x", "p"),
            ("n", "", "p"),
            r"\mathrm{km \; s^{-1}}/\mathrm{cm}^{-3}",
        ),
        (
            ("n", "", "p"),
            ("v_err", "x", "p"),
            r"\mathrm{cm}^{-3}/\mathrm{km \; s^{-1}}",
        ),
    ],
    ids=[
        "unknown-denominator",
        "unknown-numerator",
        "error-numerator",
        "error-denominator",
    ],
)
def test_ratio_units_look_up_each_measurement_without_err(
    labels_base, mcs0, mcs1, units
):
    """A ratio's units are numerator/denominator units, ``_err`` ignored, ``???`` if unknown.

    ON FAILURE: the code is wrong.
    """
    assert labels_base.TeXlabel(mcs0, mcs1).units == units


def test_axnorm_label_names_the_normalization_in_tex_path_and_units(labels_base):
    r"""A column-normalized label reads "/ Column Max", saves under ``Cnorm``, states ``\#``.

    ON FAILURE: the code is wrong.
    """
    label = labels_base.TeXlabel(("n", "", "p"), axnorm="c")
    assert label.tex == r"n_{p} / \mathrm{Column \; Max}"
    assert label.path == Path("n_p/Cnorm")
    assert label.units == "\\#"
    assert label.with_units == r"$n_{p} / \mathrm{Column \; Max} \; \left[\#\right]$"


@pytest.mark.parametrize(
    "axnorm, tex",
    [
        ("d", r"\mathrm{Density \; of} \; n_{p}"),
        ("cd", r"\mathrm{Column \; Density \; of} \; n_{p}"),
        ("rd", r"\mathrm{Row \; Density \; of} \; n_{p}"),
    ],
)
def test_density_axnorm_label_states_no_units(labels_base, axnorm, tex):
    """A density of a quantity is per unit of the binned axes: no units are stated.

    ON FAILURE: the code is wrong.
    """
    label = labels_base.TeXlabel(("n", "", "p"), axnorm=axnorm)
    assert label.tex == tex
    assert label.units == ""
    assert label.with_units == f"${tex}$"


def test_every_axnorm_a_plot_accepts_has_a_label(labels_base):
    """Each binning's ``allowed_axnorm`` keys are keys of the one label table.

    ``Count`` and ``TeXlabel`` both accept exactly the table's keys, so a key
    a binning adds needs one entry there, and this test names it.

    ON FAILURE: the code is wrong -- a binning accepts an ``axnorm`` no label
    can name; add it to ``labels.base.AXNORM``.
    """
    import numpy as np
    import pandas as pd
    from solarwindpy.plotting.hist1d import Hist1D
    from solarwindpy.plotting.hist2d import Hist2D
    from solarwindpy.plotting.labels.special import Count
    from solarwindpy.plotting.spiral import SpiralPlot2D

    rng = np.random.default_rng(0)
    x = pd.Series(rng.random(200), name="x")
    y = pd.Series(rng.random(200), name="y")
    plots = [
        Hist1D(x, nbins=5),
        Hist2D(x, y, nbins=5),
        SpiralPlot2D(x, y, x.rename("z"), min_per_bin=20),
    ]
    table = set(labels_base.AXNORM)
    for plot in plots:
        assert set(plot.binning.allowed_axnorm) <= table, type(plot).__name__
    for key in table:
        assert Count(key).axnorm == key
        assert labels_base.TeXlabel(("n", "", "p"), axnorm=key).axnorm == key
    with pytest.raises(ValueError):
        Count("nope")


def test_new_line_for_units_splits_label_and_units_into_two_math_lines(labels_base):
    """With ``new_line_for_units`` the units are a second ``$...$`` line.

    ON FAILURE: the code is wrong.
    """
    label = labels_base.TeXlabel(("n", "", "p"), new_line_for_units=True)
    assert label.with_units == "$n_{p} $\n$ " + r"\left[\mathrm{cm}^{-3}\right]$"


def test_logger_is_named_for_module_and_class(labels_base):
    """``logger`` is named ``<module>.<class name>``, as its docstring states.

    ON FAILURE: the code is wrong.
    """
    label = labels_base.TeXlabel(("n", "", "p"))
    assert label.logger.name == "solarwindpy.plotting.labels.base.TeXlabel"


@pytest.mark.parametrize("c", ["x", "y", "z"])
def test_cartesian_component_is_a_lowercase_subscript(labels_base, c):
    """A vector's x, y and z components subscript as written: v_x, B_z.

    ON FAILURE: the code is wrong.
    """
    assert labels_base.TeXlabel(("v", c, "p1")).tex == "{v}_{{%s};{p_1}}" % c
    assert labels_base.TeXlabel(("b", c, "")).tex == "B_{%s}" % c


@pytest.mark.parametrize(
    "mcs, tex",
    [
        (("gse", "x", ""), r"{X}_{\mathrm{GSE}}"),
        (("gse", "z", ""), r"{Z}_{\mathrm{GSE}}"),
        (("hci", "y", ""), r"{Y}_{\mathrm{HCI}}"),
    ],
)
def test_frame_position_axes_stay_upper_case(labels_base, mcs, tex):
    """A frame's coordinate axes are upper case by convention: X_GSE, not x_GSE.

    ON FAILURE: the code is wrong.
    """
    assert labels_base.TeXlabel(mcs).tex == tex


@pytest.mark.parametrize("m", ["T", "w", "beta", "p"])
def test_scalar_component_renders_as_no_component(labels_base, m):
    """The scalar column of a tensor quantity is the bare scalar: T_{p_1}.

    A scalar has no component, as the ``mag`` of a vector is its bare symbol.

    ON FAILURE: the code is wrong.
    """
    scalar = labels_base.TeXlabel((m, "scalar", "p1"))
    assert scalar.tex == labels_base.TeXlabel((m, "", "p1")).tex
    assert "scalar" not in scalar.tex


def test_every_dimensionless_label_shares_one_unit_form(labels_base):
    r"""Dimensionless quantities, ratios and counts all state the registry's one form.

    beta and the temperature anisotropy R are ratios of like quantities, as
    a ratio label is; a count is a pure number. Each states
    ``UNIT_TEX["dimless"]``, ``\#``.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.core import quantities
    from solarwindpy.plotting.labels.special import CarringtonRotation, Count

    dimless = quantities.UNIT_TEX["dimless"]
    assert dimless == r"\#"
    TeXlabel = labels_base.TeXlabel
    assert TeXlabel(("beta", "", "p1")).units == dimless
    assert TeXlabel(("R", "", "p1")).units == dimless
    assert TeXlabel(("n", "", "a"), ("n", "", "p1")).units == dimless
    assert TeXlabel(("n", "", "p1"), axnorm="t").units == dimless
    assert Count().units == dimless
    assert str(CarringtonRotation()).endswith(r"\left[%s\right]$" % dimless)


def test_normalized_ratio_is_parenthesized(labels_base):
    """A normalized ratio groups the ratio: (n_a/n_p) / Max, not n_a/n_p / Max.

    ON FAILURE: the code is wrong.
    """
    label = labels_base.TeXlabel(("n", "", "a"), ("n", "", "p1"), axnorm="t")
    assert label.tex == r"(n_{\alpha}/n_{p_1}) / \mathrm{Max}"
    assert "validate_axnorm" in labels_base.__all__


def test_plots_and_labels_share_one_axnorm_check(labels_base):
    """A plot checks ``axnorm`` with the labels' ``validate_axnorm``, against its keys.

    ON FAILURE: the code is wrong -- a second copy of the check exists, or the
    plot no longer limits the keys to its binning's ``allowed_axnorm``.
    """
    import pandas as pd
    from solarwindpy.plotting import base as plot_base
    from solarwindpy.plotting.hist1d import Hist1D

    assert not hasattr(plot_base.BinnedPlot, "_validate_axnorm")
    assert labels_base.validate_axnorm("W", ("d", "t", "w")) == "w"
    with pytest.raises(ValueError, match="expected one of: d, t, w"):
        Hist1D(pd.Series([1.0, 2.0, 3.0], name="x"), axnorm="c")
    with pytest.raises(ValueError, match="expected one of: c, r, t, d"):
        labels_base.validate_axnorm("q")
