# Spent-When: PERMANENT(the plot classes stop defining a summary repr)
# Supersedes: none
"""Tests for the summary ``repr`` of the plot classes.

``repr(plot)``, which ``print`` and Jupyter show, lists on one line each what
the plot holds: its class, the x, y (and z) labels, the number of rows it
keeps, its log flags, its binning (bins per axis on a fixed grid, cells on a
spiral mesh), ``axnorm``, ``clim`` and ``alim`` when set, and ``path``. Each
plot is built on a small hand-chosen frame whose kept rows are counted by hand.
"""

import numpy as np
import pandas as pd
import pytest
import matplotlib

matplotlib.use("Agg")

from solarwindpy.plotting.hist1d import Hist1D  # noqa: E402
from solarwindpy.plotting.hist2d import Hist2D  # noqa: E402
from solarwindpy.plotting.scatter import Scatter  # noqa: E402
from solarwindpy.plotting.spiral import SpiralPlot2D  # noqa: E402

# Six rows; row 2 has NaN x and row 4 NaN y, so a plot on x and y keeps 4 and
# a Hist1D of x alone keeps 5.
X = pd.Series([1.0, 2.0, np.nan, 3.0, 4.0, 5.0], name="x")
Y = pd.Series([1.0, 3.0, 2.0, 2.5, np.nan, 3.5], name="y")
Z = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], name="z")
KEPT = {"Hist1D": 5, "Hist2D": 4, "SpiralPlot2D": 4, "Scatter": 4}

# The spiral's starting grid: 2 x-bins by 2 y-bins. min_per_bin=1 splits each
# cell with two or more points; the count is checked against the mesh itself.
XEDGES = np.array([0.0, 3.0, 6.0])
YEDGES = np.array([0.0, 2.0, 4.0])


def _lines(plot):
    """``repr(plot)`` as its class line and a dict of its ``key: value`` lines."""
    first, *rest = repr(plot).splitlines()
    return first, dict(line.strip().split(": ", 1) for line in rest)


def _build(name):
    if name == "Hist1D":
        return Hist1D(X, nbins=np.array([0.0, 2.0, 4.0, 6.0]))
    if name == "Hist2D":
        return Hist2D(X, Y, nbins=4, axnorm="t")
    if name == "SpiralPlot2D":
        return SpiralPlot2D(X, Y, initial_bins=(XEDGES, YEDGES), min_per_bin=1)
    return Scatter(X, Y, Z)


@pytest.mark.parametrize("name", list(KEPT))
def test_repr_names_the_class_labels_rows_log_and_path(name):
    """Every plot's repr names its class, labels, kept rows, log flags and path.

    It is built before any plotting, so repr must not need a drawn figure.
    ``print`` shows the same text.

    ON FAILURE: the code is wrong.
    """
    plot = _build(name)
    first, fields = _lines(plot)
    assert first == name
    assert fields["x"].split("  ")[0] == str(plot.labels.x)
    assert fields["y"].split("  ")[0] == str(plot.labels.y)
    assert fields["observations"] == str(KEPT[name])
    assert fields["log"] == "x=False, y=False"
    assert fields["path"] == str(plot.path)
    assert str(plot) == repr(plot)


@pytest.mark.parametrize(
    "name, has_z", [("Hist1D", False), ("Hist2D", True), ("Scatter", True)]
)
def test_repr_shows_z_only_when_the_plot_has_one(name, has_z):
    """A z label is listed for a 2-D histogram and a coloured scatter only.

    ON FAILURE: the code is wrong.
    """
    plot = _build(name)
    _, fields = _lines(plot)
    assert {"x", "y", "path"} <= set(fields)
    assert ("z" in fields) is has_z
    if has_z:
        assert fields["z"].split("  ")[0] == str(plot.labels.z)


def test_hist1d_repr_counts_its_bins_and_axnorm():
    """Three bins from four edges; no ``axnorm`` reads ``None``.

    ON FAILURE: the code is wrong.
    """
    _, fields = _lines(_build("Hist1D"))
    assert fields["bins"] == "x: 3"
    assert fields["axnorm"] == "None"


def test_hist2d_repr_counts_its_bins_per_axis():
    """``nbins=4`` gives four bins on each axis, and ``axnorm="t"`` is shown.

    ON FAILURE: the code is wrong.
    """
    _, fields = _lines(_build("Hist2D"))
    assert fields["bins"] == "x: 4, y: 4"
    assert fields["axnorm"] == "t"


def test_spiral_repr_counts_its_mesh_cells():
    """A spiral's binning is its number of mesh cells, one per row of ``mesh.mesh``.

    ON FAILURE: the code is wrong.
    """
    plot = _build("SpiralPlot2D")
    _, fields = _lines(plot)
    assert fields["bins"] == f"{plot.mesh.mesh.shape[0]} mesh cells"


def test_scatter_repr_has_no_binning():
    """A scatter bins nothing, so its repr has no bins, axnorm or clim.

    ON FAILURE: the code is wrong.
    """
    _, fields = _lines(_build("Scatter"))
    assert {"x", "y", "z", "path"} <= set(fields)
    assert not {"bins", "axnorm", "clim"} & set(fields)


def test_clim_and_alim_appear_only_once_set():
    """Unset limits are left out; set ones are listed with their bounds.

    ON FAILURE: the code is wrong.
    """
    plot = _build("Hist2D")
    _, fields = _lines(plot)
    assert "clim" not in fields and "alim" not in fields
    plot.set_clim(2, None)
    plot.set_alim(0.1, 0.9, kind="quantile")
    _, fields = _lines(plot)
    assert fields["clim"] == "lower=2, upper=None"
    assert fields["alim"] == "lower=0.1, upper=0.9 (quantile)"


def test_repr_reports_a_log_axis():
    """A logarithmic x is reported as ``x=True``.

    ON FAILURE: the code is wrong.
    """
    plot = Hist2D(X, Y, nbins=4, logx=True)
    _, fields = _lines(plot)
    assert fields["log"] == "x=True, y=False"


def test_hist1d_z_label_error_still_names_the_class():
    """Setting a z label on a Hist1D names the class in one line.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(ValueError, match=r"^Hist1D doesn't have a z-label$"):
        _build("Hist1D").set_labels(z="z")


# ---------------------------------------------------------------------------
# Ranges: each axis line shows its bin range and the range of the data binned
# ---------------------------------------------------------------------------


def test_hist2d_axes_show_bin_and_data_ranges_without_the_nan_rows():
    """Edges [0, 2, 4, 6] on both axes: 3 bins over [0, 6] each.

    The kept rows (labels 0, 1, 3, 5; rows 2 and 4 hold a NaN) have x 1, 2,
    3, 5, y 1, 3, 2.5, 3.5 and z 1, 2, 4, 6.

    ON FAILURE: the code is wrong.
    """
    edges = np.array([0.0, 2.0, 4.0, 6.0])
    _, fields = _lines(Hist2D(X, Y, Z, nbins=[edges, edges]))
    assert fields["x"] == "x  bins 3 [0, 6]  data [1, 5]"
    assert fields["y"] == "y  bins 3 [0, 6]  data [1, 3.5]"
    assert fields["z"] == "z  data [1, 6]"


def test_a_log_axis_shows_its_ranges_in_data_units():
    """log10 edges [0, 1, 2, 3] are bins over [1, 1000]; x spans 2 to 500.

    ON FAILURE: the code is wrong.
    """
    x = pd.Series([2.0, 30.0, np.nan, 500.0])
    y = pd.Series([1.0, 2.0, 3.0, 4.0])
    h = Hist2D(x, y, logx=True, nbins=[np.array([0.0, 1.0, 2.0, 3.0]), [0.0, 5.0]])
    _, fields = _lines(h)
    assert fields["x"] == "x  bins 3 [1, 1000]  data [2, 500]"


def test_numbers_are_shown_to_four_significant_figures():
    """x from 251.33 to 898.71 on edges 250 to 900 reads [251.3, 898.7].

    ON FAILURE: the code is wrong.
    """
    x = pd.Series([251.33, 600.0, 898.71])
    h = Hist1D(x, nbins=np.array([250.0, 575.0, 900.0]))
    _, fields = _lines(h)
    assert fields["x"] == "x  bins 2 [250, 900]  data [251.3, 898.7]"


def test_a_count_axis_has_no_data_range():
    """A count's z is the constant 1, so its line is the label alone.

    ON FAILURE: the code is wrong.
    """
    h = Hist2D(X, Y, nbins=4)
    _, fields = _lines(h)
    assert fields["z"] == str(h.labels.z)


def test_spiral_axes_show_the_mesh_extent_and_data_ranges():
    """The mesh spans the initial edges, [0, 6] in x and [0, 4] in y.

    The top edge of each axis is raised 1% so the largest value lies inside:
    x to 6.06 and y to 4.04 (``AdaptiveMesh.initial_edges``).

    ON FAILURE: the code is wrong.
    """
    _, fields = _lines(_build("SpiralPlot2D"))
    assert fields["x"] == "x  mesh [0, 6.06]  data [1, 5]"
    assert fields["y"] == "y  mesh [0, 4.04]  data [1, 3.5]"


def test_scatter_axes_show_data_ranges():
    """A scatter bins nothing: each axis shows its data range alone.

    ON FAILURE: the code is wrong.
    """
    _, fields = _lines(_build("Scatter"))
    assert fields["x"] == "x  data [1, 5]"
    assert fields["y"] == "y  data [1, 3.5]"
    assert fields["z"] == "z  data [1, 6]"


@pytest.mark.parametrize("cls", [Hist1D, Hist2D, SpiralPlot2D, Scatter])
def test_repr_of_an_unbuilt_plot_does_not_raise(cls):
    """A plot whose constructor never ran still has a one-line repr.

    ON FAILURE: the code is wrong.
    """
    text = repr(cls.__new__(cls))
    assert text.startswith(cls.__name__)
