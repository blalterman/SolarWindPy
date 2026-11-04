# Spent-When: PERMANENT(plots stop deriving their save path from their current state)
# Supersedes: none
"""The save path is derived from the plot's current state, never stored.

``Base.path`` is ``class / x / y [/ z] / scale``: each axis contributes its
label's ``path`` (or the label string, spaces as hyphens), z only when the
plot has a z label, and the scale tag ``linX``/``logX`` then ``linY``/``logY``
joined by ``-``. A label path ending in ``norm`` (a normalized ``Count``)
takes the scale tag before its norm part, so the last part reads the x, y and
z scaling in order. Reading ``path`` after any setter gives the path for the
plot as it is now.
"""

from pathlib import Path
from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from solarwindpy.instabilities.beta_ani import BetaRPlot  # noqa: E402
from solarwindpy.plotting.hist1d import Hist1D  # noqa: E402
from solarwindpy.plotting.hist2d import Hist2D  # noqa: E402
from solarwindpy.plotting.scatter import Scatter  # noqa: E402
from solarwindpy.plotting.spiral import SpiralPlot2D  # noqa: E402
from solarwindpy.solar_activity.plots import IndicatorPlot  # noqa: E402


RNG = np.random.default_rng(7)
N = 400
X = pd.Series(10.0 ** RNG.uniform(0, 2, N))
Y = pd.Series(10.0 ** RNG.uniform(0, 2, N))
Z = pd.Series(RNG.uniform(1, 2, N))


class LinePlot(IndicatorPlot):
    """The generic indicator plotter, with its base axis format."""

    def _format_axis(self, ax):
        return super()._format_axis(ax)


def _indicator_plot():
    index = pd.date_range("2000-01-01", periods=12, freq="MS")
    data = pd.DataFrame({"ssn": np.arange(12.0)}, index=index)
    return LinePlot(SimpleNamespace(data=data), "ssn")


def test_scatter_path_has_no_z_part_without_z():
    """A Scatter without z has a path of x, y and scale, with no literal z.

    ON FAILURE: the code is wrong.
    """
    assert Scatter(X, Y).path == Path("Scatter", "x", "y", "linX-linY")


def test_scatter_path_has_a_z_part_with_z():
    """A Scatter with z has class / x / y / z / scale.

    ON FAILURE: the code is wrong.
    """
    assert Scatter(X, Y, Z).path == Path("Scatter", "x", "y", "z", "linX-linY")


def test_scatter_path_follows_set_log():
    """``set_log`` on a Scatter changes the scale tag of its path.

    ON FAILURE: the code is wrong.
    """
    plot = Scatter(X, Y)
    plot.set_log(x=True, y=True)
    assert plot.path == Path("Scatter", "x", "y", "logX-logY")


def test_scatter_path_follows_set_labels():
    """``set_labels`` on a Scatter changes the label parts of its path.

    ON FAILURE: the code is wrong.
    """
    plot = Scatter(X, Y)
    plot.set_labels(x="bulk speed", y="np")
    assert plot.path == Path("Scatter", "bulk-speed", "np", "linX-linY")


def test_hist1d_path_carries_both_scales_and_follows_set_log():
    """A Hist1D path has both axis scales, and the y scale follows ``set_log``.

    ON FAILURE: the code is wrong.
    """
    plot = Hist1D(X, logx=True)
    assert plot.path == Path("Hist1D", "x", "count", "logX-linY")
    plot.set_log(y=True)
    assert plot.path == Path("Hist1D", "x", "count", "logX-logY")


def test_hist1d_path_takes_the_scale_before_the_norm():
    """A normalized Hist1D count folds the scale tag before its norm part.

    ON FAILURE: the code is wrong.
    """
    plot = Hist1D(X, axnorm="t")
    assert plot.path == Path("Hist1D", "x", "count", "linX-linY-Tnorm")


def test_hist2d_path_follows_set_axnorm():
    """``set_axnorm`` after construction changes the norm part of the path.

    ON FAILURE: the code is wrong.
    """
    plot = Hist2D(X, Y, logx=True)
    plot.set_axnorm("c")
    assert plot.path == Path("Hist2D", "x", "y", "count", "logX-linY-Cnorm")


def test_spiral_path_follows_set_axnorm():
    """``set_axnorm`` on a SpiralPlot2D changes the norm part of the path.

    ON FAILURE: the code is wrong.
    """
    plot = SpiralPlot2D(X, Y, min_per_bin=50)
    plot.set_axnorm("t")
    assert plot.path == Path("SpiralPlot2D", "x", "y", "count", "linX-linY-Tnorm")


def test_beta_r_path_follows_set_axnorm():
    """A BetaRPlot path uses its TeX label paths and follows ``set_axnorm``.

    ON FAILURE: the code is wrong.
    """
    plot = BetaRPlot(X, Y, "p")
    xl, yl = plot.labels.x.path, plot.labels.y.path
    plot.set_axnorm("r")
    assert plot.path == Path("BetaRPlot", xl, yl, "count", "logX-logY-Rnorm")


def test_indicator_plot_path_follows_set_log():
    """An IndicatorPlot path follows ``set_log`` without any other call.

    ON FAILURE: the code is wrong.
    """
    plot = _indicator_plot()
    plot.set_log(y=True)
    assert plot.path == Path("LinePlot", plot.labels.x.path, "y", "linX-logY")


@pytest.mark.parametrize(
    "build",
    [
        lambda: Scatter(X, Y),
        lambda: Hist1D(X),
        lambda: Hist2D(X, Y),
        lambda: SpiralPlot2D(X, Y, min_per_bin=50),
        _indicator_plot,
    ],
    ids=["Scatter", "Hist1D", "Hist2D", "SpiralPlot2D", "IndicatorPlot"],
)
def test_path_is_derived_not_stored(build):
    """No plot stores a path or offers a setter for one.

    ON FAILURE: the code is wrong.
    """
    plot = build()
    assert "_path" not in vars(plot)
    assert not hasattr(plot, "set_path")


@pytest.mark.parametrize("unset", [None, "None"], ids=["None", "string-None"])
def test_scatter_path_has_a_z_part_only_while_labels_z_is_set(unset):
    """``set_labels(z=...)`` adds the z part; z None (or ``"None"``) drops it.

    ON FAILURE: the code is wrong.
    """
    plot = Scatter(X, Y)
    plot.set_labels(z="w")
    assert plot.path == Path("Scatter", "x", "y", "w", "linX-linY")
    plot.set_labels(z=unset)
    assert plot.path == Path("Scatter", "x", "y", "linX-linY")


def test_hist1d_path_follows_set_labels():
    """``set_labels`` on a Hist1D changes the x part; the count part stays.

    ON FAILURE: the code is wrong.
    """
    plot = Hist1D(X)
    plot.set_labels(x="bulk speed")
    assert plot.path == Path("Hist1D", "bulk-speed", "count", "linX-linY")


def test_hist2d_path_without_axnorm_ends_in_the_scale():
    """An unnormalized count ends in ``count``, so the scale tag is the last part.

    ON FAILURE: the code is wrong.
    """
    plot = Hist2D(X, Y, logx=True, logy=True)
    assert plot.path == Path("Hist2D", "x", "y", "count", "logX-logY")


def test_hist2d_path_keeps_its_built_scale_through_set_log():
    """A Hist2D's x and y log are built in: the path keeps them through ``set_log``.

    ``set_log`` passing the values the plot has is allowed and changes
    nothing; changing one raises, and the path is still the built one.

    ON FAILURE: the code is wrong.
    """
    plot = Hist2D(X, Y, logx=True)
    built = Path("Hist2D", "x", "y", "count", "logX-linY")
    plot.set_log(x=True, y=False)
    assert plot.path == built
    with pytest.raises(ValueError):
        plot.set_log(y=True)
    assert plot.path == built


def test_hist2d_path_follows_set_labels_with_the_norm_last():
    """``set_labels`` on a normalized Hist2D changes x and y; the norm stays last.

    ON FAILURE: the code is wrong.
    """
    plot = Hist2D(X, Y, axnorm="c")
    plot.set_labels(x="bulk speed", y="np")
    assert plot.path == Path("Hist2D", "bulk-speed", "np", "count", "linX-linY-Cnorm")


def test_spiral_path_carries_its_built_scale_and_follows_set_labels():
    """A SpiralPlot2D path has its built log scale and follows ``set_labels``.

    ON FAILURE: the code is wrong.
    """
    plot = SpiralPlot2D(X, Y, logx=True, min_per_bin=50)
    assert plot.path == Path("SpiralPlot2D", "x", "y", "count", "logX-linY")
    plot.set_labels(x="bulk speed", y="np")
    assert plot.path == Path("SpiralPlot2D", "bulk-speed", "np", "count", "logX-linY")
