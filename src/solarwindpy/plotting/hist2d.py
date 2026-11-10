#!/usr/bin/env python
r"""Two-dimensional histogram and heatmap plotting utilities."""

__all__ = [
    "Hist2D",
]

import numpy as np
import pandas as pd
import matplotlib as mpl

from matplotlib import pyplot as plt
from collections import namedtuple
from scipy.ndimage import gaussian_filter
from scipy.signal import savgol_filter


from . import base
from . import labels
from .tools import nan_gaussian_filter

from .hist1d import Hist1D


class Hist2D(base._OnFixedGrid, base.ColorPlot, base.BinnedPlot):
    r"""2D histogram of (x, y), optionally aggregating a z-value in each bin.

    Parameters
    ----------
    x, y : pd.Series
        x and y data to bin.
    z : pd.Series, optional
        If not None, the value to aggregate in each bin. If None, each bin
        counts its points.
    logx, logy : bool or None
        If True, bin ``log10(abs(x))`` or ``log10(abs(y))``. None means
        False, or, with a ``BinnedData`` as ``nbins``, its setting for that
        axis's column.
    axnorm : str, optional
        Normalization of the aggregated values; see ``FixedGrid.normalize``
        for the keys.
    clip : bool, str, Mapping or None
        If True, clip x and y to their 0.01st and 99.99th percentiles
        (``Base.clip_data``) when assigning points to bins; the bin edges
        are computed from the unclipped data. ``"l"`` or ``"u"`` clips only
        the lower or upper tail. A mapping such as ``{"y": "u"}`` sets each
        axis on its own. None means False, or, with a ``BinnedData`` as
        ``nbins``, its setting for that axis's column. Stored as ``clip``, a
        ``ClipAxes``.
    nbins : int or str or tuple or BinnedData
        Bin specification of the ``FixedGrid``; see its constructor. A
        ``BinnedData`` is shared: its bins and bin codes for the columns named
        ``x.name`` and ``y.name`` are used, ``logx``, ``logy`` and ``clip``
        default to its settings for those columns (an explicit, differing
        value raises ``ValueError``), and rows its own mask excludes are not
        kept.
    bin_precision : int, optional
        Decimal places to which bin edges are rounded. If None, 5. Must be
        None with a ``BinnedData``.
    mask : pd.Series of bool, optional
        Rows to keep, aligned by label to the index of x and y. A row is
        binned where it is True and x, y and z are not NaN. Selections are
        returned on the original labels. A label missing from ``mask``, or a
        NaN in it, raises ``ValueError``; neither is treated as False.

    Raises
    ------
    KeyError
        If ``nbins`` is a ``BinnedData`` without a column named ``x.name`` or
        ``y.name``.
    ValueError
        If ``nbins`` is a ``BinnedData`` and ``logx``, ``logy`` or ``clip`` is
        given and differs from its setting, ``bin_precision`` is given, or
        ``x.index`` is not a subset of its index. Also if no row is left to
        bin.

    Notes
    -----
    The constructor bins the points on a 2-D
    :class:`~solarwindpy.plotting.binning.FixedGrid`; ``agg`` aggregates and
    normalizes, and ``make_plot`` draws the result with an optional colorbar.

    Examples
    --------
    Count six points in a 3 x 2 grid given by its edges. Every bin is in the
    result, indexed by its (x, y) intervals; an empty bin is NaN.

    >>> import pandas as pd
    >>> import matplotlib.pyplot as plt
    >>> from solarwindpy.plotting.hist2d import Hist2D
    >>> x = pd.Series([1.0, 1.0, 2.0, 2.0, 2.0, 3.0], name="x")
    >>> y = pd.Series([1.0, 2.0, 1.0, 1.0, 2.0, 2.0], name="y")
    >>> h = Hist2D(x, y, nbins=([0.5, 1.5, 2.5, 3.5], [0.5, 1.5, 2.5]))
    >>> counts = h.agg()
    >>> counts.tolist()
    [1.0, 1.0, 2.0, 1.0, nan, 1.0]
    >>> int(counts.sum())
    6
    >>> ax, mesh, cbar = h.make_plot()
    >>> plt.close("all")
    """

    def __init__(
        self,
        x,
        y,
        z=None,
        logx=None,
        logy=None,
        axnorm=None,
        clip=None,
        nbins=101,
        bin_precision=None,
        mask=None,
    ):
        r"""Store the data, labels and normalization, then bin the data."""
        super().__init__()
        self._set_grid_data(
            {"x": x, "y": y, "z": z},
            nbins,
            {"x": logx, "y": logy},
            clip,
            bin_precision,
            mask,
        )
        self.set_clim(None, None)
        self.set_axnorm(axnorm)
        self._set_labels(x="x", y="y", z=labels.special.Count() if z is None else "z")

    # ``_set_data`` stores ``log10(abs())`` of each axis flagged in ``self.log``.
    _log_data = True
    _grid_axes = ("x", "y")

    def _maybe_convert_to_log_scale(self, x, y):
        if self.log.x:
            x = 10.0**x
        if self.log.y:
            y = 10.0**y

        return x, y

    def _make_cbar(self, mappable, **kwargs):
        ticks = kwargs.pop(
            "ticks",
            mpl.ticker.MultipleLocator(0.1) if self.axnorm in ("c", "r") else None,
        )
        return super()._make_cbar(mappable, ticks=ticks, **kwargs)

    def _prep_agg_for_plot(self, fcn=None, use_edges=True, mask_invalid=True):
        """Prepare aggregated data and coordinates for plotting.

        Parameters
        ----------
        fcn : FunctionType, None
            Aggregation function. If None, automatically select in :py:meth:`agg`.
        use_edges : bool
            If True, return bin edges (for pcolormesh).
            If False, return bin centers (for contour).
        mask_invalid : bool
            If True, return masked array with NaN/inf masked.
            If False, return raw values (use when applying gaussian_filter).

        Returns
        -------
        C : np.ma.MaskedArray or np.ndarray
            2D array of aggregated values (masked if mask_invalid=True).
        x : np.ndarray
            X coordinates (edges or centers based on use_edges).
        y : np.ndarray
            Y coordinates (edges or centers based on use_edges).
        """
        agg = self.agg(fcn=fcn).unstack("x")

        if use_edges:
            x = self.edges["x"]
            y = self.edges["y"]
        else:
            x = self.intervals["x"].mid
            y = self.intervals["y"].mid

        x, y = self._maybe_convert_to_log_scale(x, y)

        C = agg.values
        if mask_invalid:
            C = np.ma.masked_invalid(C)

        return C, x, y

    @staticmethod
    def _gaussian_filter(array, sigma, kwargs):
        r"""Smooth the grid ``array`` with a Gaussian of ``sigma`` bins.

        A grid without empty (NaN) bins is filtered by
        :func:`scipy.ndimage.gaussian_filter`. A grid with empty bins is
        filtered by :func:`~solarwindpy.plotting.tools.nan_gaussian_filter`,
        which averages only the occupied neighbours and keeps the empty bins
        empty: the plain filter spreads each NaN over the kernel, blanking the
        bins around every gap. ``kwargs``, a dict or None, is passed to the
        filter.
        """
        kwargs = {} if kwargs is None else kwargs
        array = np.asarray(array, dtype=float)
        if np.isnan(array).any():
            return nan_gaussian_filter(array, sigma, **kwargs)
        return gaussian_filter(array, sigma, **kwargs)

    def make_plot(
        self,
        ax=None,
        cbar=True,
        cbar_kwargs=None,
        fcn=None,
        alpha_fcn=None,
        **kwargs,
    ):
        r"""Make a 2D plot on `ax` using `ax.pcolormesh`.

        Parameters
        ----------
        ax: mpl.axes.Axes, None
            If None, create an `Axes` instance from `plt.subplots`.
        cbar: bool
            If True, create color bar with `labels.z`.
        cbar_kwargs: dict, None
            If not None, kwargs passed to `self._make_cbar`.
        fcn: FunctionType, None
            Aggregation function. If None, automatically select in :py:meth:`agg`.
        alpha_fcn: None, str
            If not None, the function used to aggregate the data for setting alpha
            value; see ``ColorPlot._apply_alpha_fcn``. Ignored, with a warning,
            when the plot counts points.
        kwargs:
            Passed to `ax.pcolormesh`. For values of both signs, `norm`
            defaults to a `CenteredNorm` about 0 and `cmap` to "RdBu_r";
            otherwise `norm` defaults to ten colour bands on [0, 1] for row or
            column normalized data and to a `LogNorm` for densities ("d",
            "cd", "rd"). See ``ColorPlot._color_scale``.

        Returns
        -------
        ax: mpl.axes.Axes
            Axes upon which plot was made.
        mesh: mpl.collections.QuadMesh
            The histogram's cells.
        cbar: colorbar.Colorbar or None
            The colorbar if `cbar` is True, else None.
        """
        agg = self.agg(fcn=fcn).unstack("x")
        x = self.edges["x"]
        y = self.edges["y"]

        if ax is None:
            fig, ax = plt.subplots()

        x, y = self._maybe_convert_to_log_scale(x, y)

        C = np.ma.masked_invalid(agg.values)
        norm, cmap = self._color_scale(kwargs, C)
        XX, YY = np.meshgrid(x, y)
        pc = ax.pcolormesh(XX, YY, C, norm=norm, cmap=cmap, **kwargs)

        if cbar:
            cbar_kwargs = self._prepare_cbar_kwargs(cbar_kwargs, ax)

            # Pass `norm` to `self._make_cbar` so that we can choose the ticks to use.
            cbar = self._make_cbar(pc, **cbar_kwargs)
        else:
            cbar = None

        self._format_axis(ax)

        # The mesh's faces run along x within each y row, as `unstack("x")` does.
        self._apply_alpha_fcn(
            pc, alpha_fcn, lambda fcn: self.agg(fcn=fcn).unstack("x").to_numpy().ravel()
        )

        return ax, pc, cbar

    def plot_hist_with_contours(
        self,
        ax=None,
        cbar=True,
        cbar_kwargs=None,
        fcn=None,
        # Contour-specific parameters
        levels=None,
        use_contourf=True,
        contour_kwargs=None,
        gaussian_filter_std=0,
        gaussian_filter_kwargs=None,
        **kwargs,
    ):
        """Make a 2D pcolormesh plot with contour overlay.

        Combines `make_plot` (pcolormesh background) with `plot_contours`
        (contour/contourf overlay) in a single call.

        Parameters
        ----------
        ax : mpl.axes.Axes, None
            If None, create an `Axes` instance from `plt.subplots`.
        cbar : bool
            If True, create color bar with `labels.z`.
        cbar_kwargs : dict, None
            If not None, kwargs passed to `self._make_cbar`.
        fcn : FunctionType, None
            Aggregation function. If None, automatically select.
        levels : array-like, int, None
            Contour levels. If None, automatically determined.
        use_contourf : bool
            If True, use filled contours. Else use line contours.
        contour_kwargs : dict, None
            Additional kwargs passed to contour/contourf (e.g., linestyles, colors).
        gaussian_filter_std : int
            If > 0, smooth the contour data with a Gaussian of this standard
            deviation, in bins, as :py:meth:`plot_contours` does: the filter
            skips empty bins.
        gaussian_filter_kwargs : dict, None
            Kwargs passed to the Gaussian filter.
        kwargs :
            Passed to `ax.pcolormesh`. `norm` defaults as in `make_plot` and
            is shared by the mesh and the contours.

        Returns
        -------
        ax : mpl.axes.Axes
        mesh : QuadMesh
            The pcolormesh background.
        qset : QuadContourSet
            The contour set from the overlay.
        cbar : colorbar.Colorbar or None
            The colorbar of the mesh if `cbar` is True, else None.
        """
        if ax is None:
            fig, ax = plt.subplots()

        if contour_kwargs is None:
            contour_kwargs = {}

        # --- 1. Plot pcolormesh background ---
        C_edges, x_edges, y_edges = self._prep_agg_for_plot(fcn=fcn, use_edges=True)

        # norm and cmap are shared between pcolormesh and contour.
        norm, cmap = self._color_scale(kwargs, C_edges)

        XX_edges, YY_edges = np.meshgrid(x_edges, y_edges)
        pc = ax.pcolormesh(XX_edges, YY_edges, C_edges, norm=norm, cmap=cmap, **kwargs)

        # --- 2. Plot contour overlay ---
        # Delay masking if gaussian filter will be applied
        needs_filter = gaussian_filter_std > 0
        C_centers, x_centers, y_centers = self._prep_agg_for_plot(
            fcn=fcn, use_edges=False, mask_invalid=not needs_filter
        )

        # Apply Gaussian filter if requested
        if needs_filter:
            C_centers = self._gaussian_filter(
                C_centers, gaussian_filter_std, gaussian_filter_kwargs
            )

            C_centers = np.ma.masked_invalid(C_centers)

        XX_centers, YY_centers = np.meshgrid(x_centers, y_centers)

        # Get contour levels
        levels = self._get_contour_levels(levels)

        # Contour function
        contour_fcn = ax.contourf if use_contourf else ax.contour

        # Default linestyles for contour
        linestyles = contour_kwargs.pop("linestyles", list(self._contour_linestyles))

        if levels is None:
            args = [XX_centers, YY_centers, C_centers]
        else:
            args = [XX_centers, YY_centers, C_centers, levels]

        qset = contour_fcn(
            *args, linestyles=linestyles, cmap=cmap, norm=norm, **contour_kwargs
        )

        # --- 3. Colorbar ---
        if cbar:
            cbar_kwargs = self._prepare_cbar_kwargs(cbar_kwargs, ax)
            cbar = self._make_cbar(pc, **cbar_kwargs)
        else:
            cbar = None

        # --- 4. Format axis ---
        self._format_axis(ax)

        return ax, pc, qset, cbar

    def get_border(self):
        r"""Get the top and bottom edges of the plot.

        Returns
        -------
        border: namedtuple
            Contains "top" and "bottom" fields, each a :class:`pandas.Series`.
        """

        Border = namedtuple("Border", "top,bottom")
        top = {}
        bottom = {}
        for x, v in self.agg().unstack("x").items():
            yt = v.last_valid_index()
            if yt is not None:
                z = v.loc[yt]
                top[(yt, x)] = z

            yb = v.first_valid_index()
            if yb is not None:
                z = v.loc[yb]
                bottom[(yb, x)] = z

        top = pd.Series(top)
        bottom = pd.Series(bottom)
        for edge in (top, bottom):
            edge.index.names = ["y", "x"]

        border = Border(top, bottom)
        return border

    @staticmethod
    def _default_savgol_window(n, polyorder):
        r"""Default Savitzky-Golay window for an edge of ``n`` points, or None.

        10% of ``n``, made odd by subtracting 1 when even; raised to the
        smallest odd length above ``polyorder`` when it is not above it; capped
        at the largest odd length within ``n``. None when no odd length within
        ``n`` exceeds ``polyorder``: the edge is too short to smooth.
        """
        wlength = int(np.floor(n / 10))
        if not wlength % 2:
            wlength -= 1
        if wlength <= polyorder:
            wlength = polyorder + 1 + polyorder % 2
        if wlength > n:
            wlength = n if n % 2 else n - 1
        if wlength <= polyorder:
            return None
        return wlength

    def _plot_one_edge(
        self,
        ax,
        edge,
        smooth=False,
        sg_kwargs=None,
        xlim=(None, None),
        ylim=(None, None),
        **kwargs,
    ):
        x = edge.index.get_level_values("x").mid
        y = edge.index.get_level_values("y").mid

        # Copy so that popping `window_length` and `polyorder` neither mutates
        # the caller's dict nor starves the next edge drawn from it.
        sg_kwargs = dict() if sg_kwargs is None else dict(sg_kwargs)

        if smooth:
            polyorder = sg_kwargs.pop("polyorder", 3)
            wlength = sg_kwargs.pop("window_length", None)
            if wlength is None:
                wlength = self._default_savgol_window(y.shape[0], polyorder)

            if wlength is not None:
                y = savgol_filter(y, wlength, polyorder, **sg_kwargs)

        if self.log.x:
            x = 10.0**x
        if self.log.y:
            y = 10.0**y

        x0, x1 = xlim
        y0, y1 = ylim

        tk = np.full_like(x, True, dtype=bool)
        if x0 is not None:
            tk = tk & (x0 <= x)
        if x1 is not None:
            tk = tk & (x <= x1)
        if y0 is not None:
            tk = tk & (y0 <= y)
        if y1 is not None:
            tk = tk & (y <= y1)

        x = x[tk]
        y = y[tk]

        return ax.plot(x, y, **kwargs)

    def plot_edges(self, ax, smooth=True, sg_kwargs=None, **kwargs):
        """Overplot the edges.

        Parameters
        ----------
        ax : mpl.axes.Axes
            Axis on which to plot.
        smooth: bool
            If True, apply a Savitzky-Golay filter (:py:func:`scipy.signal.savgol_filter`)
            to the y-values before plotting to smooth the curve.
        sg_kwargs: dict, None
            If not None, dict of kwargs passed to Savitzky-Golay filter. Also allows
            for setting of `window_length` and `polyorder` as kwargs. `polyorder`
            defaults to 3. `window_length` defaults to 10% of the number of points
            on the edge, less 1 when even, as the filter needs an odd window. A
            default window that is not above `polyorder`, as below 50 points
            for `polyorder` 3, is raised to the smallest odd length above it, and
            a window longer than the edge to the longest odd length within it.
            When no odd length within the edge exceeds `polyorder` the edge is
            drawn unsmoothed. A `window_length` the caller passes is used as given.
        xlim, ylim: tuple of (float or None, float or None), optional
            Inclusive ``(lower, upper)`` limits, in data coordinates, on the edge
            vertices drawn. A vertex outside a limit is dropped; a vertex exactly
            on a limit is kept. ``None`` leaves that side unbounded. Default
            ``(None, None)``.
        **kwargs
            ``color`` defaults to ``"cyan"`` and ``label`` labels the top
            edge only. The rest are passed to `ax.plot`.

        Returns
        -------
        etop, ebottom : list of mpl.lines.Line2D
            The lines ``ax.plot`` draws for the top and the bottom edge.
        """

        top, bottom = self.get_border()

        color = kwargs.pop("color", "cyan")
        label = kwargs.pop("label", None)
        etop = self._plot_one_edge(
            ax, top, smooth, sg_kwargs, color=color, label=label, **kwargs
        )
        ebottom = self._plot_one_edge(
            ax, bottom, smooth, sg_kwargs, color=color, **kwargs
        )

        return etop, ebottom

    def _get_contour_levels(self, levels):
        if (levels is not None) or (self.axnorm is None):
            pass

        elif (levels is None) and (self.axnorm == "t"):
            levels = [0.01, 0.1, 0.3, 0.7, 0.99]

        elif (levels is None) and (self.axnorm == "d"):
            levels = [3e-5, 1e-4, 3e-4, 1e-3, 1.7e-3, 2.3e-3]

        elif (levels is None) and (self.axnorm in ["r", "c"]):
            levels = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

        elif (levels is None) and (self.axnorm in ["cd", "rd", "w", "wc", "wr"]):
            levels = None

        else:
            raise ValueError(
                f"Unrecognized axis normalization {self.axnorm} for default levels."
            )

        return levels

    def _verify_contour_passthrough_kwargs(self, ax, edges_kwargs, cbar_kwargs):
        if edges_kwargs is None:
            edges_kwargs = dict()
        cbar_kwargs = self._prepare_cbar_kwargs(cbar_kwargs, ax)

        return edges_kwargs, cbar_kwargs

    def plot_contours(
        self,
        ax=None,
        cbar=True,
        cbar_kwargs=None,
        fcn=None,
        plot_edges=False,
        edges_kwargs=None,
        use_contourf=False,
        gaussian_filter_std=0,
        gaussian_filter_kwargs=None,
        levels=None,
        **kwargs,
    ):
        """Make a contour plot on `ax` using `ax.contour`.

        Parameters
        ----------
        ax: mpl.axes.Axes, None
            If None, create an `Axes` instance from `plt.subplots`.
        cbar: bool
            If True, create color bar with `labels.z`.
        cbar_kwargs: dict, None
            If not None, kwargs passed to `self._make_cbar`.
        fcn: FunctionType, None
            Aggregation function. If None, automatically select in :py:meth:`agg`.
        plot_edges: bool
            If True, plot the smoothed, extreme edges of the 2D histogram.
        edges_kwargs: None, dict
            Passed to :py:meth:`plot_edges`.
        use_contourf: bool
            If True, use `ax.contourf`. Else use `ax.contour`.
        gaussian_filter_std: int
            If > 0, smooth the z-values with a Gaussian of this standard
            deviation, in bins. A grid without empty bins is filtered by
            :func:`scipy.ndimage.gaussian_filter`; a grid with empty bins by
            :func:`~solarwindpy.plotting.tools.nan_gaussian_filter`, which
            averages only the occupied bins and leaves the empty ones empty.
        gaussian_filter_kwargs: None, dict
            If not None and gaussian_filter_std > 0, passed to the filter.
        levels: array-like, int, None
            Contour levels. If None, the default for the ``axnorm``, or
            matplotlib's choice when there is none.
        kwargs:
            Passed to :meth:`matplotlib.axes.Axes.contour` or
            :meth:`matplotlib.axes.Axes.contourf`. For values of both signs,
            `norm` defaults to a `CenteredNorm` about 0 and `cmap` to
            "RdBu_r". Otherwise `norm` defaults to ten colour bands on [0, 1]
            for row or column normalized data and to a `LogNorm` for
            densities ("d", "cd", "rd"); otherwise, with at least two levels,
            to a `BoundaryNorm` on the levels.

        Returns
        -------
        ax : mpl.axes.Axes
        qset : QuadContourSet
        cbar : colorbar.Colorbar or None
            The colorbar if `cbar` is True, else None.
        """
        linestyles = kwargs.pop("linestyles", list(self._contour_linestyles))

        if ax is None:
            fig, ax = plt.subplots()

        edges_kwargs, cbar_kwargs = self._verify_contour_passthrough_kwargs(
            ax, edges_kwargs, cbar_kwargs
        )

        agg = self.agg(fcn=fcn).unstack("x")
        x = self.intervals["x"].mid
        y = self.intervals["y"].mid

        x, y = self._maybe_convert_to_log_scale(x, y)

        XX, YY = np.meshgrid(x, y)

        C = agg.values
        if gaussian_filter_std:
            C = self._gaussian_filter(C, gaussian_filter_std, gaussian_filter_kwargs)

        C = np.ma.masked_invalid(C)
        norm, cmap = self._color_scale(kwargs, C)

        assert XX.shape == C.shape
        assert YY.shape == C.shape

        levels = self._get_contour_levels(levels)

        if (norm is None) and (levels is not None) and (len(levels) >= 2):
            norm = mpl.colors.BoundaryNorm(levels, 256, clip=True)

        contour_fcn = ax.contour
        if use_contourf:
            contour_fcn = ax.contourf

        if levels is None:
            args = [XX, YY, C]
        else:
            args = [XX, YY, C, levels]

        qset = contour_fcn(*args, linestyles=linestyles, cmap=cmap, norm=norm, **kwargs)

        if plot_edges:
            etop, ebottom = self.plot_edges(ax, **edges_kwargs)

        if cbar:
            # Pass `norm` to `self._make_cbar` so that we can choose the ticks to use.
            cbar = self._make_cbar(qset, norm=norm, **cbar_kwargs)
        else:
            cbar = None

        self._format_axis(ax)

        return ax, qset, cbar

    def _on_source_index(self, values):
        r"""``values``, given on the kept rows, on every row of the source.

        Rows the histogram does not keep get NaN, or False for a boolean
        Series. Placed by position, so repeated labels are kept apart, and
        the index of ``values`` is not read.
        """
        rows = self._source.rows
        if rows is None:
            return values.set_axis(self._source.index)
        fill = False if values.dtype == bool else np.nan
        full = np.full(rows.size, fill, dtype=np.result_type(values.dtype, type(fill)))
        full[rows] = values.to_numpy()
        return pd.Series(full, index=self._source.index, name=values.name)

    def project_1d(self, axis, only_plotted=True, project_counts=False, **kwargs):
        """Make a ``Hist1D`` from the data stored in this ``Hist2D``.

        Parameters
        ----------
        axis: str
            "x" or "y", specifying the axis to project into 1D.
        only_plotted: bool
            If True, only pass data that appears in the {self.__class__.__name__} plot
            to the :class:`~solarwindpy.plotting.hist1d.Hist1D`.
        project_counts: bool
            If True, only send the variable plotted along `axis` to
            :class:`~solarwindpy.plotting.hist1d.Hist1D`, which then counts it.
            Otherwise, also send the values to aggregate: the z-values when the
            histogram has them, else the other axis. A row whose other-axis
            value the histogram puts in no bin is not sent.
        kwargs:
            Passed to `Hist1D`, e.g. `axnorm`. The bins are the parent's, so
            `bin_precision` raises ``ValueError``.

        Returns
        -------
        h1: solarwindpy.plotting.hist1d.Hist1D

        Notes
        -----
        The ``Hist1D`` takes this histogram's ``BinnedData`` as its ``nbins``:
        each row keeps the bin it has on `axis` here, clipped or not, so the
        projected bins are this histogram's by construction and the projected
        counts are its marginal sums. Binning and display stay on
        ``log10(abs())`` of a log axis, while the values sent are the measured
        ones, sign included and never logged, so the other axis is averaged in
        linear units. A log other axis sets ``log.y`` of the ``Hist1D``, for
        display only.
        """
        axis = axis.lower()
        assert axis in ("x", "y")

        source = self._source
        if not source.counts:
            # Without z every point stores z = 1, so two or more distinct values
            # (two included) mean the caller passed z.
            other = "z"
        else:
            possible_axes = {"x", "y"}
            possible_axes.remove(axis)
            other = possible_axes.pop()

        # Rows sent to the Hist1D, among the rows this histogram keeps.
        # Values by position: `_on_source_index` places them by position.
        x = source.take(axis, labels=False)
        keep = np.ones(x.size, dtype=bool)
        if only_plotted:
            keep &= self._plotted_rows()
        if not project_counts and other != "z":
            keep &= self.binning.axis_codes()[other] >= 0

        # The Hist1D finds the axis in the BinnedData by its name and reads
        # its codes; the measured values are sent on the source's own index,
        # with a mask, so no row is looked up by label.
        column = self.binning.columns[axis]
        x = self._on_source_index(x).rename(column)
        y = None
        if not project_counts:
            y = self._on_source_index(source.take(other, labels=False))

        h1 = Hist1D(
            x,
            y=y,
            nbins=self.binning.binned,
            mask=self._on_source_index(pd.Series(keep)),
            **kwargs,
        )

        logy = False if project_counts or other == "z" else self.log._asdict()[other]
        h1.set_log(y=logy)  # The display scale of the other axis.
        # The labels were checked when they were set on this plot.
        h1._set_labels(x=self.labels._asdict()[axis])
        if not project_counts:
            h1._set_labels(y=self.labels._asdict()[other])

        return h1

    def make_joint_h2_h1_plot(
        self, project_counts=True, kwargs_1d=None, fig_axes=None, **kwargs
    ):
        r"""Draw this histogram with its x and y projections on the margins.

        Parameters
        ----------
        project_counts : bool
            Passed to ``project_1d`` for both margins.
        kwargs_1d : dict, optional
            Passed to ``Hist1D.make_plot`` for both margins.
        fig_axes : None
            Accepted and ignored.
        **kwargs
            ``figsize``, ``height_ratios``, ``width_ratios``, ``hspace``,
            ``wspace`` and ``cbar_kwargs`` lay out the figure; the rest is
            passed to ``make_plot``.

        Returns
        -------
        hax, xax, yax : Axes
            The 2D histogram axis and the x and y projection axes.
        cbar : Colorbar
            The colorbar of the 2D histogram.
        """
        figsize = kwargs.pop("figsize", (5, 6))
        height_ratios = kwargs.pop("height_ratios", [0.25, 1, 0.2, 0.1])
        width_ratios = kwargs.pop("width_ratios", [1, 0.25])
        hspace = kwargs.pop("hspace", 0)
        wspace = kwargs.pop("wspace", 0)

        fig = plt.figure(figsize=figsize)
        gs = mpl.gridspec.GridSpec(
            4,
            2,
            height_ratios=height_ratios,
            width_ratios=width_ratios,
            hspace=hspace,
            wspace=wspace,
        )

        hax = fig.add_subplot(gs[1, 0])
        xax = fig.add_subplot(gs[0, 0], sharex=hax)
        yax = fig.add_subplot(gs[1, 1], sharey=hax)
        cax = fig.add_subplot(gs[3, 0])

        cbar_kwargs = self._prepare_cbar_kwargs(kwargs.pop("cbar_kwargs", None))
        cax = cbar_kwargs.pop("cax", cax)
        orientation = cbar_kwargs.pop("orientation", "horizontal")
        _, _, cbar = self.make_plot(
            ax=hax,
            cbar_kwargs=dict(cax=cax, orientation=orientation, **cbar_kwargs),
            **kwargs,
        )

        if kwargs_1d is None:
            kwargs_1d = dict()

        self.project_1d("x", project_counts=project_counts).make_plot(
            ax=xax, **kwargs_1d
        )
        self.project_1d("y", project_counts=project_counts).make_plot(
            ax=yax, **kwargs_1d, transpose_axes=True
        )

        xax.label_outer()
        # Mimic `ax.label_outer` for `yax`.
        for label in yax.get_yticklabels(which="both"):
            label.set_visible(False)
        yax.get_yaxis().get_offset_text().set_visible(False)
        yax.set_ylabel("")

        log = self.log
        if not log.x:
            hax.xaxis.set_major_locator(
                mpl.ticker.MaxNLocator(
                    nbins=hax.xaxis.get_ticklocs().size - 1, prune="upper"
                )
            )
        if not log.y:
            hax.yaxis.set_major_locator(
                mpl.ticker.MaxNLocator(
                    nbins=hax.yaxis.get_ticklocs().size - 1, prune="upper"
                )
            )

        return hax, xax, yax, cbar

    def id_data_above_contour(self, level):
        r"""Gets data above the `level`.

        Parameters
        ----------
        level: scalar
             The z-value above which to select data. Data is aggregated according
             to `ax_norm`.

        Returns
        -------
        above_contour: pd.Series
            For data in a bin above `level`, indicates the x-`pd.Interval` within
            which the observation falls. `NaN` are observations that are below
            `level`. This object is purposely the same length as the data stored by
            Hist2D and can be used in groupby operations.

        Notes
        -----
        In each x-bin, a row is labelled when its x is in that bin and its y
        lies from the lowest to the highest y-bin reaching `level`. Both are
        compared on the side the bins close: ``(a, b]`` for right-closed bins,
        ``[a, b)`` for left-closed ones, whose last bin also holds its right
        edge.
        """
        data = self.data
        x = data.x
        y = data.y
        intervals = self.intervals
        # Object dtype, because the values written below are `pd.Interval`s.
        above_contour = pd.Series(np.nan, data.index, dtype=object)
        for k, v in self.agg().unstack("x").items():
            tk = v >= level
            if not tk.any():
                # Nothing in this column reaches `level`; its points stay NaN.
                continue
            left, right = k.left, k.right
            bottom, top = v[tk].index.min().left, v[tk].index.max().right
            above_contour_at_x = base._within(
                x, left, right, intervals["x"]
            ) & base._within(y, bottom, top, intervals["y"])
            above_contour[above_contour_at_x] = k

        above_contour = pd.Series(
            pd.Categorical(above_contour), index=above_contour.index
        )

        return above_contour
