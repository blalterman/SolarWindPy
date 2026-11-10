# Spent-When: PERMANENT(solar-activity plots stop deriving their save path from their current state)
# Supersedes: none
"""The save path of a solar-activity plot is derived from its current state.

``IndicatorPlot`` and ``SSNPlot`` take ``Base.path``: ``class / x / y [/ z] /
scale``, with the x part ``year`` (the ``DateTime("Year")`` label), the y part
from the y label, a z part only when ``labels.z`` is set, and the scale tag
``linX``/``logX`` then ``linY``/``logY``. ``path`` reads no data, so the
indicator here is a stand-in holding ``data`` and an ``id.key``, not a
downloaded series.
"""

from pathlib import Path
from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from solarwindpy.solar_activity.plots import IndicatorPlot, SSNPlot  # noqa: E402

# Tests here pass plain str labels on purpose, to exercise that path; they opt
# out of PlainStringLabelWarning the deliberate way its message describes.
pytestmark = pytest.mark.filterwarnings(
    "ignore::solarwindpy.plotting.labels.base.PlainStringLabelWarning"
)


class LinePlot(IndicatorPlot):
    """The generic indicator plotter, with its base axis format."""

    def _format_axis(self, ax):
        return super()._format_axis(ax)


def _indicator():
    index = pd.date_range("2000-01-01", periods=12, freq="MS")
    data = pd.DataFrame({"ssn": 50.0 + np.arange(12.0)}, index=index)
    return SimpleNamespace(data=data, id=SimpleNamespace(key="m13"))


def _ssn_plot():
    return SSNPlot(_indicator())


def _line_plot():
    return LinePlot(_indicator(), "ssn")


def test_ssn_plot_path_names_the_year_the_ssn_key_and_the_scale():
    """An SSNPlot path is ``SSNPlot/year/M13ssn/linX-linY``.

    The y part is the ``SSN("m13")`` label's path, ``M13ssn``.

    ON FAILURE: the code is wrong.
    """
    assert _ssn_plot().path == Path("SSNPlot", "year", "M13ssn", "linX-linY")


def test_indicator_plot_path_names_its_y_label():
    """A generic IndicatorPlot path takes the y label ``y`` it is built with.

    ON FAILURE: the code is wrong.
    """
    assert _line_plot().path == Path("LinePlot", "year", "y", "linX-linY")


@pytest.mark.parametrize("build", [_ssn_plot, _line_plot], ids=["SSNPlot", "LinePlot"])
def test_indicator_plot_path_follows_set_log(build):
    """``set_log`` after construction changes the scale tag, x then y.

    ON FAILURE: the code is wrong.
    """
    plot = build()
    name = type(plot).__name__
    y = plot.path.parts[2]
    plot.set_log(y=True)
    assert plot.path == Path(name, "year", y, "linX-logY")
    plot.set_log(x=True, y=False)
    assert plot.path == Path(name, "year", y, "logX-linY")


@pytest.mark.parametrize("build", [_ssn_plot, _line_plot], ids=["SSNPlot", "LinePlot"])
def test_indicator_plot_path_follows_set_labels(build):
    """``set_labels`` after construction changes the label parts.

    ON FAILURE: the code is wrong.
    """
    plot = build()
    plot.set_labels(x="month", y="sunspot number")
    assert plot.path == Path(
        type(plot).__name__, "month", "sunspot-number", "linX-linY"
    )


@pytest.mark.parametrize("build", [_ssn_plot, _line_plot], ids=["SSNPlot", "LinePlot"])
def test_indicator_plot_path_has_a_z_part_only_while_labels_z_is_set(build):
    """No z part as built; ``set_labels(z=...)`` adds one and z None drops it.

    ON FAILURE: the code is wrong.
    """
    plot = build()
    built = plot.path
    assert plot.labels.z is None
    assert len(built.parts) == 4
    plot.set_labels(z="w")
    assert plot.path == built.parent / "w" / built.name
    plot.set_labels(z=None)
    assert plot.path == built
