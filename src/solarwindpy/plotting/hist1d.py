#!/usr/bin/env python
r"""One-dimensional histogram plotting utilities."""

__all__ = [
    "Hist1D",
]

import numpy as np
import pandas as pd
import matplotlib as mpl

from types import FunctionType
from matplotlib import pyplot as plt

from . import base
from . import labels
from .binned import _PlotSource


class Hist1D(base._OnFixedGrid, base.BinnedPlot):
    r"""Create 1D plot of `x`, optionally aggregating `y` in bins of `x`.

    The bins are a 1-D :class:`~solarwindpy.plotting.binning.FixedGrid`.
    """

    def __init__(
        self,
        x,
        y=None,
        logx=None,
        axnorm=None,
        clip=None,
        nbins=101,
        bin_precision=None,
        mask=None,
    ):
        """Create a one-dimensional histogram.

        Parameters
        ----------
        x : pandas.Series
            Data from which to create bins.
        y : pandas.Series or None, optional
            Values to aggregate in bins of ``x``, aligned to it by label. If
            ``None``, counts of ``x`` are used. Rows where ``x`` or ``y`` is
            NaN are dropped, as in ``Hist2D``.
        logx : bool or None, optional
            If ``True``, compute bins in logarithmic space. None means False,
            or, with a ``BinnedData`` as ``nbins``, its setting for ``x``'s
            column.
        axnorm : {"t", "d", None}, optional
            Normalisation applied to the histogram. ``"t"`` divides by the
            maximum (peak equals 1) and ``"d"`` yields a density.
        clip : bool, str, Mapping or None, optional
            If True, clip x to its 0.01st and 99.99th percentiles before
            binning; ``"l"`` or ``"u"`` clips only the lower or upper tail
            (see ``Base.clip_data``). A mapping may name ``"x"`` only. None
            means False, or, with a ``BinnedData`` as ``nbins``, its setting
            for ``x``'s column. Stored as ``clip``, a ``ClipAxes``.
        nbins : int or array-like or BinnedData, optional
            Binning strategy passed to :func:`numpy.histogram_bin_edges` or
            :func:`pandas.cut` depending on the input type. A ``BinnedData``
            is shared: its bins and bin codes for the column named ``x.name``
            are used, ``logx`` and ``clip`` default to its settings for that
            column, and rows its own mask excludes are not kept.
        bin_precision : int, optional
            Precision for decimal bin edges. Must be None with a
            ``BinnedData``.
        mask : pandas.Series of bool, optional
            Rows to keep, aligned by label to the index of ``x``. Selections
            are returned on the original labels. A label missing from
            ``mask``, or a NaN in it, raises ``ValueError``; neither is
            treated as False.

        Raises
        ------
        KeyError
            If ``nbins`` is a ``BinnedData`` without a column named
            ``x.name``.
        ValueError
            If ``nbins`` is a ``BinnedData`` and ``logx`` or ``clip`` is given
            and differs from its setting, ``bin_precision`` is given, or
            ``x.index`` is not a subset of its index. Also if no row is left
            to bin.
        """
        super(Hist1D, self).__init__()
        self._set_grid_data(
            {"x": x, "y": y}, nbins, {"x": logx}, clip, bin_precision, mask
        )
        self.set_clim(None, None)
        self.set_axnorm(axnorm)
        self.set_labels(x="x", y=labels.special.Count() if y is None else "y")

    _clipped_axes = ("x",)
    _grid_axes = ("x",)

    def _set_data(self, x, y, clip=None, mask=None, within=None):
        r"""Store x, and y aligned to it, keeping the rows with neither NaN.

        Called only by the constructor. A row is kept only if neither x nor y
        is NaN (a y label missing from x's index is NaN) and ``mask`` keeps
        it. ``x`` is stored as ``log10(abs(x))``
        when ``self.log.x`` is set. If ``y`` is None, every point gets
        ``y = 1``. ``clip`` is stored as ``self.clip``, a ``ClipAxes``, None
        as False. ``mask`` is a boolean Series aligned by label to the index
        of ``x``. Rows the mask of ``within``, a shared ``BinnedData``,
        excludes are not kept either. A second call raises ``ValueError``.
        """
        self._claim_data()
        self._source = _PlotSource(
            {"x": x},
            "y",
            y,
            log={"x": self.log.x},
            owner=self.__class__.__name__,
            mask=mask,
            within=within,
        )
        self._store_clip(clip)
        self._bin_names = {"x": getattr(x, "name", None)}
        self._bin_index = getattr(x, "index", None)

    def construct_cdf(self, only_plotted=True):
        r"""Build the empirical cumulative distribution of the observed x values.

        The CDF is built from the x values of the rows the histogram keeps.
        Rows whose y is NaN are not kept, so their x is not in the CDF; y is
        otherwise ignored.

        Parameters
        ----------
        only_plotted : bool
            If True, use only the measurements in bins that survive
            aggregation (see ``get_plotted_data``). Otherwise,
            use every measurement inside the bins.

        Returns
        -------
        cdf: pd.DataFrame
            Indexed by the original row labels of the measurements, in
            ascending order of x.
            ``"x"`` column: the measurements in ascending order, in linear
            units even when ``logx`` is set.
            ``"position"`` column: the normalized position in the CDF, ``i /
            (n - 1)`` for the measurement of rank i (0 to n - 1) among the n
            sorted measurements, from 0 to 1.
            To plot the CDF::

                cdf.plot(x="x", y="position")
        """
        data = self.data
        tk = self.cut.loc[:, "x"].notna().to_numpy()
        if only_plotted:
            tk = tk & self._plotted_rows()

        x = data.loc[tk, "x"]
        # Stable sort, so tied x values keep their original label order.
        cdf = x.sort_values(kind="mergesort")

        if self.log.x:
            cdf = 10.0**cdf

        cdf = cdf.to_frame()
        rank = pd.RangeIndex(cdf.shape[0])
        cdf.loc[:, "position"] = (rank / rank.max()).to_numpy()

        return cdf

    def agg(self, **kwargs):
        if self.axnorm == "d":
            fcn = kwargs.get("fcn", None)
            if (fcn != "count") & (fcn is not None):
                raise ValueError("Unable to calculate a PDF with non-count aggregation")

        return super(Hist1D, self).agg(**kwargs)

    def set_labels(self, **kwargs):
        r"""Set the x or y label; see ``BinnedPlot.set_labels``.

        Raises
        ------
        ValueError
            If a z label is passed: a ``Hist1D`` has none.
        """
        if "z" in kwargs:
            raise ValueError(f"{self.__class__.__name__} doesn't have a z-label")

        super(Hist1D, self).set_labels(**kwargs)

    def make_plot(
        self,
        ax=None,
        fcn=None,
        transpose_axes=False,
        gaussian_filter_std=0,
        plot_window=False,
        plot_window_edges=False,
        gaussian_filter_kwargs=None,
        **kwargs,
    ):
        """Make a plot.

        Parameters
        ----------
        ax: None, mpl.axis.Axis
            If `None`, create a subplot axis.
        fcn: None, str, aggregative function, or 2-tuple
            Passed directly to `{self.__class__.__name__}.agg`. If
            None, use the default aggregation function. If str or a
            single aggregative function, use it. If a 2-tuple is passed,
            then the first element aggregates and the second element
            calculates an uncertainty.
        transpose_axes: bool
            If True, plot independent values on y-axis and dependent
            values on x-axis. Primary use case is plotting 1D projection
            of 2D plot adjascent to 2D axis.
        gaussian_filter_std: int
            If > 0, apply `scipy.ndimage.gaussian_filter` to the z-values using the
            standard deviation specified by `gaussian_filter_std`.
        gaussian_filter_kwargs: None, dict
            If not None and gaussian_filter_std > 0, passed to :func:`scipy.ndimage.gaussian_filter`
        plot_window: bool
            Requires two functions passed to `fcn`. Instead of error bars, plots the uncertainty
            window as a semi-transparent band.
        plot_window_edges: bool
            If True, plot lines at the window boundaries.
        kwargs:
            Without ``plot_window``, passed to :meth:`matplotlib.axes.Axes.errorbar`,
            with ``drawstyle`` defaulting to ``"steps-mid"``. With
            ``plot_window``, passed to :meth:`matplotlib.axes.Axes.plot` for the
            central line. Matplotlib aliases (``c``, ``ls``) are accepted. The
            key ``window_kwargs`` holds a dict of options for the band and its
            edge lines: ``alpha`` (band only) defaults to 0.15, and ``color``
            and ``linestyle`` default to the central line's.

        Returns
        -------
        ax: mpl.axes.Axes
        line: mpl.container.ErrorbarContainer or mpl.lines.Line2D
            The error bars, or with ``plot_window`` the central line.
        band: mpl.collections.PolyCollection or None
            The uncertainty window with ``plot_window``, else None.
        cbar: None
            A Hist1D draws no colorbar; the slot keeps the return order
            ``(ax, artists..., cbar)`` shared by every plot.
        """
        agg = self.agg(fcn=fcn)
        x = agg.index.mid

        dx = None  # Initialize default value. Necessary for `transpose_axes`.
        if fcn is None or isinstance(fcn, (str, FunctionType)):
            y = agg
            dy = None

        elif len(fcn) == 2:
            f0, f1 = fcn
            if isinstance(f0, FunctionType):
                f0 = f0.__name__
            if isinstance(f1, FunctionType):
                f1 = f1.__name__

            y = agg.loc[:, f0]
            dy = agg.loc[:, f1]

        else:
            raise ValueError(f"Unrecognized `fcn` ({fcn})")

        if ax is None:
            fig, ax = plt.subplots()

        if self.log.x:
            x = 10.0**x

        if gaussian_filter_std:
            from scipy.ndimage import gaussian_filter

            if gaussian_filter_kwargs is None:
                gaussian_filter_kwargs = dict()

            # Filter a float copy: integer counts would truncate the smoothed values.
            y = gaussian_filter(
                np.array(y, dtype=float), gaussian_filter_std, **gaussian_filter_kwargs
            )

        drawstyle = kwargs.pop("drawstyle", "steps-mid")

        if transpose_axes:
            x, y = y, x
            dx, dy = dy, dx

        window_kwargs = kwargs.pop("window_kwargs", dict())
        kwargs = mpl.cbook.normalize_kwargs(kwargs, mpl.lines.Line2D)
        if plot_window:
            # The window spans the dependent values, which transposing moves to x.
            if transpose_axes:
                lower = (x - dx, y)
                upper = (x + dx, y)
                band = (y, x - dx, x + dx)
                window_plotter = ax.fill_betweenx
            else:
                lower = (x, y - dy)
                upper = (x, y + dy)
                band = (x, y - dy, y + dy)
                window_plotter = ax.fill_between

            color = kwargs.pop("color", None)
            ls = kwargs.pop("linestyle", "-")
            label = kwargs.pop("label", None)

            window_alpha = window_kwargs.pop("alpha", 0.15)
            window_color = window_kwargs.pop("color", color)
            window_linestyle = window_kwargs.pop("linestyle", ls)

            (line,) = ax.plot(x, y, color=color, linestyle=ls, label=label, **kwargs)
            if plot_window_edges:
                ax.plot(
                    *upper,
                    color=window_color,
                    linestyle=window_linestyle,
                    **window_kwargs,
                )
                ax.plot(
                    *lower,
                    color=window_color,
                    linestyle=window_linestyle,
                    **window_kwargs,
                )

            band = window_plotter(
                *band,
                color=window_color,
                linestyle=window_linestyle,
                alpha=window_alpha,
                **window_kwargs,
            )

        else:
            line = ax.errorbar(x, y, xerr=dx, yerr=dy, drawstyle=drawstyle, **kwargs)
            band = None

        self._format_axis(ax, transpose_axes=transpose_axes)

        return ax, line, band, None
