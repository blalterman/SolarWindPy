# Spent-When: PERMANENT(the repository stops maintaining a test suite)
# Supersedes: none
"""Publication-format labels: a display name over the usual symbol line.

In publication format a label is two lines: the quantity's name in words, from
the quantity registry, over the TeX symbol with its units. A per-label
``publication_format`` overrides the module default that
``set_publication_format`` sets.
"""

import pytest

from solarwindpy.plotting.labels import base
from solarwindpy.plotting.labels.base import TeXlabel
from solarwindpy.plotting.labels.special import Count


@pytest.fixture
def restore_default():
    """Restore the module default after a test that changes it."""
    before = base.publication_format()
    try:
        yield
    finally:
        base.set_publication_format(before)


@pytest.mark.parametrize(
    "mcs, name, symbol",
    [
        (
            ("n", "", "p1"),
            "Number Density",
            r"$n_{p_1} \; \left[\mathrm{cm}^{-3}\right]$",
        ),
        (
            ("T", "par", "p1"),
            "Temperature",
            r"${T}_{{\parallel};{p_1}} \; \left[10^5 \, \mathrm{K}\right]$",
        ),
        (
            ("v", "x", "a"),
            "Velocity",
            r"${v}_{{x};{\alpha}} \; \left[\mathrm{km \; s^{-1}}\right]$",
        ),
        (
            ("sigma_c", "", "p1"),
            "Normalized Cross Helicity",
            r"$\sigma_{c;{p_1}} \; \left[\#\right]$",
        ),
    ],
)
def test_label_is_its_name_over_its_symbol(mcs, name, symbol):
    """The first line is the registry name, the second the default label.

    ON FAILURE: the code is wrong.
    """
    label = TeXlabel(mcs, publication_format=True)
    assert label.name == name
    assert str(label) == f"{name}\n{symbol}"
    assert str(label).split("\n")[1] == str(TeXlabel(mcs))


def test_name_overrides_the_registry_name():
    """``name=`` replaces the first line only.

    ON FAILURE: the code is wrong.
    """
    label = TeXlabel(("v", "", "p1"), name="Solar Wind Speed", publication_format=True)
    assert str(label) == (
        "Solar Wind Speed\n" + r"${v}_{{p_1}} \; \left[\mathrm{km \; s^{-1}}\right]$"
    )


def test_description_keyword_is_removed():
    """``description`` was merged into ``name``: one optional first line.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(TypeError):
        TeXlabel(("n", "", "p1"), description="Wind")


def test_per_label_setting_overrides_the_module_default(restore_default):
    """True or False on a label wins; None follows the module default.

    ON FAILURE: the code is wrong.
    """
    base.set_publication_format(True)
    assert base.publication_format() is True
    assert "\n" in str(TeXlabel(("n", "", "p1")))
    assert "\n" not in str(TeXlabel(("n", "", "p1"), publication_format=False))

    base.set_publication_format(False)
    assert base.publication_format() is False
    assert "\n" not in str(TeXlabel(("n", "", "p1")))
    assert "\n" in str(TeXlabel(("n", "", "p1"), publication_format=True))


def test_module_default_applies_to_labels_already_built(restore_default):
    """A label reads the default when it renders, so existing plots follow it.

    ON FAILURE: the code is wrong -- the format is fixed when the label is
    built, so ``set_publication_format`` misses labels a plot already holds.
    """
    label = TeXlabel(("n", "", "p1"))
    count = Count("t")
    one_line = (str(label), str(count))
    base.set_publication_format(True)
    assert str(label) == "Number Density\n" + one_line[0]
    assert str(count) == "Normalized Count\n" + r"$N / N_{\max} \; \left[\#\right]$"
    base.set_publication_format(False)
    assert (str(label), str(count)) == one_line


def test_ratio_names():
    """A ratio of one quantity is "<Name> Ratio"; of two, "<Name0> / <Name1>".

    ON FAILURE: the code is wrong.
    """
    same = TeXlabel(("n", "", "a"), ("n", "", "p1"), publication_format=True)
    mixed = TeXlabel(("v", "", "p1"), ("n", "", "p1"), publication_format=True)
    assert same.name == "Number Density Ratio"
    assert mixed.name == "Velocity / Number Density"
    assert str(same).split("\n")[0] == "Number Density Ratio"


def test_normalization_stays_on_the_symbol_line():
    """An ``axnorm`` changes the symbol line; the name is the quantity's.

    ON FAILURE: the code is wrong.
    """
    label = TeXlabel(("n", "", "p1"), axnorm="t", publication_format=True)
    assert str(label) == (
        "Number Density\n" + r"$n_{p_1} / \mathrm{Max} \; \left[\#\right]$"
    )


def test_unregistered_quantity_has_no_name_line():
    """A measurement the registry does not know renders on one line.

    ON FAILURE: the code is wrong.
    """
    label = TeXlabel(("not_a_quantity", "", "p1"), publication_format=True)
    assert label.name is None
    assert "\n" not in str(label)


@pytest.mark.parametrize(
    "norm, name, symbol_line",
    [
        (None, "Count", r"$N \; \left[\#\right]$"),
        ("t", "Normalized Count", r"$N / N_{\max} \; \left[\#\right]$"),
        (
            "c",
            "Column-Normalized Count",
            r"$N / N_{\max,\mathrm{col}} \; \left[\#\right]$",
        ),
        (
            "r",
            "Row-Normalized Count",
            r"$N / N_{\max,\mathrm{row}} \; \left[\#\right]$",
        ),
        ("d", "Probability Density", r"$p$"),
        ("cd", "Column Probability Density", r"$p_{\mathrm{col}}$"),
        ("rd", "Row Probability Density", r"$p_{\mathrm{row}}$"),
    ],
)
def test_count_is_its_name_over_its_symbol(norm, name, symbol_line, restore_default):
    r"""A ``Count`` in publication format is its name over the symbol ``N`` or ``p``.

    The second line is a symbol, as for any quantity, rather than the words
    of the one-line label, which would repeat the name. A count divided by a
    maximum is a pure number, ``\#``; a density states no units.

    ON FAILURE: the code is wrong.
    """
    base.set_publication_format(True)
    label = Count(norm)
    assert label.name == name
    assert str(label) == f"{name}\n{symbol_line}"


@pytest.mark.parametrize(
    "label, expected",
    [
        (
            lambda: TeXlabel(("v", "x", "p1")),
            r"${v}_{{x};{p_1}} \; \left[\mathrm{km \; s^{-1}}\right]$",
        ),
        (
            lambda: TeXlabel(("T", "scalar", "p1")),
            r"${T}_{{p_1}} \; \left[10^5 \, \mathrm{K}\right]$",
        ),
        (
            lambda: TeXlabel(("n", "", "a"), ("n", "", "p1")),
            r"$n_{\alpha}/n_{p_1} \; \left[\#\right]$",
        ),
        (
            lambda: TeXlabel(("n", "", "p1"), axnorm="d"),
            r"$\mathrm{Density \; of} \; n_{p_1}$",
        ),
        (lambda: Count(), r"$\mathrm{Count} \; \left[\#\right]$"),
        (
            lambda: Count("t"),
            r"$\mathrm{Count \, / \, Max} \; \left[\#\right]$",
        ),
    ],
)
def test_default_format_is_unchanged(label, expected):
    """With the default off, labels render on one line, as before.

    ON FAILURE: the code is wrong.
    """
    assert base.publication_format() is False
    assert str(label()) == expected
