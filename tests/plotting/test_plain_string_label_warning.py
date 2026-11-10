# Spent-When: PERMANENT(plots stop warning on a plain str axis label)
# Supersedes: none
"""A plain ``str`` axis label warns and names the structured labels to use.

A plot's axis labels are label objects from :mod:`solarwindpy.plotting.labels`:
a ``TeXlabel`` built from an ``(M, C, S)`` key, a ``ManualLabel`` for anything
the registry does not know, or a special label such as ``Count``. A plain
``str`` is still accepted and drawn as given, and warns
``PlainStringLabelWarning`` once per call, naming the structured alternatives,
the ``[#]`` units of a dimensionless quantity, and the filter that keeps a
deliberate plain string quiet. ``None``, ``""`` and ``"None"`` mean "no label"
or "a blank label" and do not warn. The package's own placeholders (a new
plot's ``"x"`` and ``"y"``) and its own propagation of labels never warn.

The class is looked up inside each test, so a missing class fails only the
tests that need it.
"""

import warnings

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

import solarwindpy as swp  # noqa: E402
from solarwindpy.fitfunctions.lines import Line  # noqa: E402
from solarwindpy.instabilities.beta_ani import BetaRPlot  # noqa: E402
from solarwindpy.plotting.hist1d import Hist1D  # noqa: E402
from solarwindpy.plotting.hist2d import Hist2D  # noqa: E402
from solarwindpy.plotting.labels import base as labels_base  # noqa: E402
from solarwindpy.plotting.labels.base import TeXlabel  # noqa: E402
from solarwindpy.plotting.labels.datetime import DateTime  # noqa: E402
from solarwindpy.plotting.labels.special import Count, ManualLabel  # noqa: E402
from solarwindpy.plotting.scatter import Scatter  # noqa: E402
from solarwindpy.plotting.spiral import SpiralPlot2D  # noqa: E402

TARGET = pytest.mark.xfail(
    strict=True,
    raises=AttributeError,
    reason="PlainStringLabelWarning does not exist yet in "
    "solarwindpy.plotting.labels.base; remove this marker when the warning lands",
)

# A 2 x 2 grid whose cells hold 1, 2, 3 and 6 points: chosen so every cell is
# occupied and the counts differ.
EDGES = np.array([0.0, 1.0, 2.0])
CELLS = [((0.5, 0.5), 1), ((1.5, 0.5), 2), ((0.5, 1.5), 3), ((1.5, 1.5), 6)]
X = pd.Series([c[0] for c, n in CELLS for _ in range(n)], dtype=float, name="x")
Y = pd.Series([c[1] for c, n in CELLS for _ in range(n)], dtype=float, name="y")
Z = pd.Series(np.arange(X.size, dtype=float) + 1.0, name="z")


def _category():
    """The warning class; AttributeError until it exists."""
    return labels_base.PlainStringLabelWarning


def _line_fit():
    """A fitted ``Line`` through five points on y = 2x + 1."""
    x = np.arange(5, dtype=float)
    fit = Line(x, 2.0 * x + 1.0)
    fit.make_fit()
    return fit


PLOTS = {
    "Hist1D": lambda: Hist1D(X, nbins=EDGES),
    "Hist2D": lambda: Hist2D(X, Y, nbins=[EDGES, EDGES]),
    "Scatter": lambda: Scatter(X, Y, Z),
    "SpiralPlot2D": lambda: SpiralPlot2D(
        X + 0.1 * np.arange(X.size) / X.size,
        Y,
        Z,
        initial_bins=(EDGES, EDGES),
        min_per_bin=100,
    ),
    "FFPlot": lambda: _line_fit().plotter,
}

# Values that state no label or a blank one, and label objects.
NOT_PLAIN = {
    "TeXlabel": TeXlabel(("n", "", "p1")),
    "ManualLabel": ManualLabel("Flux Ratio", "dimless"),
    "Count": Count(),
    "DateTime": DateTime("Year"),
    "None": None,
    "empty str": "",
    "str None": "None",
}


def _recorded(call):
    """Every warning ``call()`` issues, with each one shown."""
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        call()
    return record


@pytest.mark.parametrize("label", NOT_PLAIN.values(), ids=NOT_PLAIN.keys())
@pytest.mark.parametrize("build", PLOTS.values(), ids=PLOTS.keys())
def test_a_label_object_none_or_blank_label_sets_with_no_warning(build, label):
    """``set_labels`` with a label object, None, "" or "None" issues no warning.

    Guard: no warning of any kind, before and after the plain-string warning.

    ON FAILURE: the code is wrong.
    """
    plot = build()
    record = _recorded(lambda: plot.set_labels(x=label))
    assert [str(w.message) for w in record] == []
    assert plot.labels.x is label


@TARGET
@pytest.mark.parametrize("build", PLOTS.values(), ids=PLOTS.keys())
def test_plain_string_labels_warn_once_naming_the_structured_labels(build):
    """Two plain str labels in one call warn once; the label is still set.

    The message names each axis given a plain str, the label objects to use
    instead (``TeXlabel``, ``ManualLabel``), ``labels.available()``, the
    ``[#]`` units of a dimensionless quantity and its unit key ``dimless``,
    and the ``warnings`` filter that silences it.

    ON FAILURE: the code is wrong.
    """
    category = _category()
    plot = build()
    record = _recorded(lambda: plot.set_labels(x="Normalized Flux", y="Speed"))
    issued = [w for w in record if issubclass(w.category, category)]
    assert len(issued) == 1
    message = str(issued[0].message)
    for phrase in (
        "'Normalized Flux'",
        "'Speed'",
        "TeXlabel",
        "ManualLabel",
        "labels.available()",
        "[#]",
        "dimless",
        "filterwarnings",
        category.__name__,
    ):
        assert phrase in message, phrase
    assert (plot.labels.x, plot.labels.y) == ("Normalized Flux", "Speed")


@TARGET
def test_the_warning_is_a_user_warning_naming_the_callers_line():
    """It is a ``UserWarning`` attributed to this file, not the package.

    ON FAILURE: the code is wrong.
    """
    category = _category()
    assert issubclass(category, UserWarning)
    plot = PLOTS["Hist2D"]()
    record = _recorded(lambda: plot.set_labels(z="Mean Speed"))
    (issued,) = [w for w in record if issubclass(w.category, category)]
    assert issued.filename == __file__


@TARGET
def test_a_filter_on_the_category_keeps_a_deliberate_plain_string_quiet():
    """Ignoring the category silences it, and the label is set as given.

    ON FAILURE: the code is wrong.
    """
    category = _category()
    plot = PLOTS["Hist2D"]()
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        warnings.filterwarnings("ignore", category=category)
        plot.set_labels(x="Normalized Flux")
    assert [str(w.message) for w in record] == []
    assert plot.labels.x == "Normalized Flux"


@TARGET
def test_a_plain_string_colorbar_label_warns_and_is_drawn():
    """``cbar_kwargs={"label": str}`` warns once and labels the colorbar.

    ON FAILURE: the code is wrong.
    """
    category = _category()
    plot = PLOTS["Hist2D"]()
    fig, ax = plt.subplots()
    try:
        record = _recorded(
            lambda: plot.make_plot(ax=ax, cbar_kwargs={"label": "Mean Speed"})
        )
        issued = [w for w in record if issubclass(w.category, category)]
        assert len(issued) == 1
        assert "'Mean Speed'" in str(issued[0].message)
        assert fig.axes[-1].get_ylabel() == "Mean Speed"
    finally:
        plt.close("all")


@TARGET
def test_the_packages_own_plotting_paths_issue_no_plain_string_label_warning():
    """Building, labelling and drawing every plot the package offers stays quiet.

    Positive control first: under the same filter, a plain str label raises.
    Then each plotter is built with its default labels and drawn, labelled
    with label objects and drawn, projected, and drawn as a joint plot; a
    ``BetaRPlot`` labels itself; a fit's plotter draws; and a plot of the
    example plasma, ``swp.examples.load_plasma()``, is labelled from its own
    column keys. Each would raise if the package warned on its own behaviour.

    ON FAILURE: the code is wrong; a package call site passes a plain str
    through the public label path.
    """
    category = _category()
    with warnings.catch_warnings():
        warnings.simplefilter("error", category)
        with pytest.raises(category):
            Hist2D(X, Y, nbins=[EDGES, EDGES]).set_labels(x="Normalized Flux")

        try:
            for name, build in PLOTS.items():
                plot = build()
                if name == "FFPlot":
                    plot.plot_raw_used_fit_resid()
                    plot.set_labels(x=TeXlabel(("v", "x", "p1")), y=Count())
                    plot.plot_raw_used_fit_resid()
                    continue
                plot.make_plot()
                repr(plot)
                plot.path
                labels = {"x": TeXlabel(("v", "", "p1"))}
                if name != "Hist1D":
                    labels["y"] = TeXlabel(("n", "", "p1"))
                plot.set_labels(**labels)
                plot.make_plot()

            h2 = Hist2D(X, Y, nbins=[EDGES, EDGES])
            h2.project_1d("x")
            h2.make_joint_h2_h1_plot()
            h2.set_labels(x=TeXlabel(("v", "", "p1")), y=TeXlabel(("n", "", "p1")))
            h2.project_1d("y", project_counts=False)
            h2.make_joint_h2_h1_plot()

            beta = pd.Series(10.0 ** np.linspace(-1, 1, 50), name="beta")
            R = pd.Series(10.0 ** np.linspace(-0.5, 0.5, 50), name="R")
            BetaRPlot(beta, R, "p").make_plot()

            plasma = swp.examples.load_plasma()
            key = ("v", "x", "p1")
            v = plasma.data.loc[:, key].rename("v")
            h1 = Hist1D(v, nbins=3)
            h1.set_labels(x=TeXlabel(key))
            h1.make_plot()
        finally:
            plt.close("all")
