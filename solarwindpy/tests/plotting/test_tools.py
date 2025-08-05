#!/usr/bin/env python
"""Tests for plotting helpers."""

from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes

from solarwindpy.plotting import tools
import solarwindpy.plotting as plotting


def test_subplots_returns_axes(monkeypatch):
    """subplots should return a matplotlib Axes object."""

    fig = Figure()
    ax = fig.add_subplot(111)

    def dummy_subplots(*args, **kwargs):
        return fig, ax

    monkeypatch.setattr(plt, "subplots", dummy_subplots)

    fig_tools, ax_tools = tools.subplots()
    assert isinstance(ax_tools, Axes)
    assert ax_tools is ax

    fig_pkg, ax_pkg = plotting.subplots()
    assert isinstance(ax_pkg, Axes)
    assert ax_pkg is ax
