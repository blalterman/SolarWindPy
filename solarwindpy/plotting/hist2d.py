#!/usr/bin/env python
r"""Two-dimensional histogram and heatmap plotting utilities."""

import numpy as np
import pandas as pd
import matplotlib as mpl

from matplotlib import pyplot as plt
from collections import namedtuple
from scipy.signal import savgol_filter


from . import base
from . import labels as labels_module
from .tools import nan_gaussian_filter

from . import agg_plot
from . import hist1d

AggPlot = agg_plot.AggPlot
Hist1D = hist1d.Hist1D


class Hist2D(base.PlotWithZdata, base._CbarMaker, AggPlot):
    r"""2D histogram of (x, y), optionally aggregating a z-value in each bin.

    Parameters
    ----------
    x, y : pd.Series
        x and y data to bin.
    z : pd.Series, optional
        If not None, the value to aggregate in each bin. If None, each bin
        counts its points.
    axnorm : str, optional
        Normalization of the aggregated values; see ``set_axnorm`` for the keys.
    logx, logy : bool
        If True, bin ``log10(abs(x))`` or ``log10(abs(y))``.
    clip_data : bool
        If True, clip x and y to their 0.01st and 99.99th percentiles
        (``AggPlot.clip_data``) when assigning points to bins; the bin edges
        are computed from the unclipped data.
    nbins : int or str or tuple
        Bin specification passed to ``calc_bins_intervals``.
    bin_precision : int, optional
        Decimal places to which bin edges are rounded. If None, 5.

    Notes
    -----
    ``calc_bins_intervals`` computes the bins, ``make_cut`` assigns each point
    to a bin, ``agg`` aggregates and normalizes, and ``make_plot`` draws the
    result with an optional colorbar.
    """

    def __init__(
        self,
        x,
        y,
        z=None,
        axnorm=None,
        logx=False,
        logy=False,
        clip_data=False,
        nbins=101,
        bin_precision=None,
    ):
        r"""Store the data, labels and normalization, then bin the data."""
        super().__init__()
        self.set_log(x=logx, y=logy)
        self.set_data(x, y, z, clip_data)
        self.set_labels(
            x="x", y="y", z=labels_module.Count(norm=axnorm) if z is None else "z"
        )

        self.set_axnorm(axnorm)
        self.calc_bins_intervals(nbins=nbins, precision=bin_precision)
        self.make_cut()
        self.set_clim(None, None)

    @property
    def _gb_axes(self):
        return ("x", "y")

    def _maybe_convert_to_log_scale(self, x, y):
        if self.log.x:
            x = 10.0**x
        if self.log.y:
            y = 10.0**y

        return x, y

    def set_labels(self, **kwargs):
        r"""Set axis labels; a ``Count`` z-label is rebuilt with the current ``axnorm``."""
        z = kwargs.pop("z", self.labels.z)
        if isinstance(z, labels_module.Count):
            try:
                z.set_axnorm(self.axnorm)
            except AttributeError:
                pass

            z.build_label()

        super().set_labels(z=z, **kwargs)

    def set_data(self, x, y, z, clip):
        r"""Store the data, taking ``log10(abs())`` of each axis flagged in ``self.log``."""
        super().set_data(x, y, z, clip)
        data = self.data
        if self.log.x:
            data.loc[:, "x"] = np.log10(np.abs(data.loc[:, "x"]))
        if self.log.y:
            data.loc[:, "y"] = np.log10(np.abs(data.loc[:, "y"]))
        self._data = data

    def set_axnorm(self, new):
        r"""The method by which the gridded data is normalized.

        ===== =============================================================
         key                           description
        ===== =============================================================
         c     Column normalize
         d     Density normalize
         r     Row normalize
         t     Divide by the maximum (peak equals 1)
         cd    PDFs in each column
         rd    PDFs in each row
        ===== ============================================================="""
        if new is not None:
            new = new.lower()
            assert new in (
                "c",
                "r",
                "t",
                "d",
                "cd",
                "rd",
            ), f"Unrecgonized axnorm `{new}`"

        zlbl = self.labels.z
        if isinstance(zlbl, labels_module.Count):
            zlbl.set_axnorm(new)
            zlbl.build_label()

        self._axnorm = new

    def _axis_normalizer(self, agg):
        r"""Takes care of row, column, total, and density normaliation.

        On a log axis the densities ("d", "cd", "rd") are normalised over
        ``log10`` of that axis: the bins are log-space intervals, so cell areas
        on the log axes sum to 1.
        """

        axnorm = self.axnorm
        if axnorm is None:
            pass
        elif axnorm == "c":
            agg = agg.divide(agg.groupby(level="x").max(), level="x")
        elif axnorm == "r":
            agg = agg.divide(agg.groupby(level="y").max(), level="y")
        elif axnorm == "t":
            agg = self._divide_by_max(agg)
        elif axnorm == "d":
            N = agg.sum().sum()
            # Widths are in the binned variable, log10 on a log axis.
            dx = self._bin_widths(agg.index.get_level_values("x").unique())
            dy = self._bin_widths(agg.index.get_level_values("y").unique())
            agg = agg.divide(dx, level="x").divide(dy, level="y").divide(N)

        elif axnorm == "cd":
            N = agg.groupby(level="x").sum()
            dy = self._bin_widths(
                pd.IntervalIndex(agg.index.get_level_values("y").unique()).sort_values()
            )
            # Divide by total in each column and each row's width
            agg = agg.divide(N, level="x").divide(dy, level="y")

        elif axnorm == "rd":
            N = agg.groupby(level="y").sum()
            dx = self._bin_widths(
                pd.IntervalIndex(agg.index.get_level_values("x").unique()).sort_values()
            )
            # Divide by total in each column and each row's width
            agg = agg.divide(N, level="y").divide(dx, level="x")

        elif hasattr(axnorm, "__iter__"):
            # TODO: This is an undocumented feature. I do not know if it is
            #       tested nor how it interacts with colorbar labels, etc.
            #       We need to investigate this issue (20250804).
            kind, fcn = axnorm
            if kind == "c":
                agg = agg.divide(agg.groupby(level="x").agg(fcn), level="x")
            elif kind == "r":
                agg = agg.divide(agg.groupby(level="y").agg(fcn), level="y")
            else:
                raise ValueError(f"Unrecognized axnorm with function ({kind}, {fcn})")
        else:
            raise ValueError(f"Unrecognized axnorm ({axnorm})")

        return agg

    def agg(self, **kwargs):
        r"""Aggregate, normalize by ``axnorm``, and apply the ``alim`` limits.

        Every bin is present in the result; bins outside ``alim`` are NaN.
        ``kwargs`` are passed to ``AggPlot.agg``.
        """
        agg = super().agg(**kwargs)
        agg = self._axis_normalizer(agg)
        agg = self._agg_reindexer(agg)
        return self._apply_alim(agg)

    def _make_cbar(self, mappable, **kwargs):
        ticks = kwargs.pop(
            "ticks",
            mpl.ticker.MultipleLocator(0.1) if self.axnorm in ("c", "r") else None,
        )
        return super()._make_cbar(mappable, ticks=ticks, **kwargs)

    @staticmethod
    def _default_norm(axnorm):
        r"""The colour normalisation a plot uses when the caller passes no ``norm``.

        Parameters
        ----------
        axnorm : str or None
            The histogram's ``axnorm``.

        Returns
        -------
        matplotlib.colors.Normalize or None
            Column- and row-normalised values lie in [0, 1], so ``"c"`` and
            ``"r"`` get ten equal colour bands on [0, 1]. Densities (``"d"``,
            ``"cd"``, ``"rd"``) span decades, so they get a clipped
            :class:`~matplotlib.colors.LogNorm`. Otherwise None, leaving the
            choice to matplotlib.
        """
        if axnorm in ("c", "r"):
            return mpl.colors.BoundaryNorm(np.linspace(0, 1, 11), 256, clip=True)
        if axnorm in ("d", "cd", "rd"):
            return mpl.colors.LogNorm(clip=True)
        return None

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
            expected_offset = 1  # edges have n+1 points for n bins
        else:
            x = self.intervals["x"].mid
            y = self.intervals["y"].mid
            expected_offset = 0  # centers have n points for n bins

        # HACK: Works around `gb.agg(observed=False)` pandas bug. (GH32381)
        if x.size != agg.shape[1] + expected_offset:
            agg = agg.reindex(columns=self.categoricals["x"])
        if y.size != agg.shape[0] + expected_offset:
            agg = agg.reindex(index=self.categoricals["y"])

        x, y = self._maybe_convert_to_log_scale(x, y)

        C = agg.values
        if mask_invalid:
            C = np.ma.masked_invalid(C)

        return C, x, y

    def _nan_gaussian_filter(self, array, sigma, **kwargs):
        """Wrapper for shared nan_gaussian_filter. See tools.nan_gaussian_filter."""
        return nan_gaussian_filter(array, sigma, **kwargs)

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
            value.
        kwargs:
            Passed to `ax.pcolormesh`. `norm` defaults to ten colour bands on
            [0, 1] for row or column normalized data and to a `LogNorm` for
            densities ("d", "cd", "rd").

        Returns
        -------
        ax: mpl.axes.Axes
            Axes upon which plot was made.
        cbar_or_mappable: colorbar.Colorbar, mpl.collections.QuadMesh
            If `cbar` is True, return the colorbar. Otherwise, return the `Quadmesh` used
            to create the colorbar.
        """
        agg = self.agg(fcn=fcn).unstack("x")
        x = self.edges["x"]
        y = self.edges["y"]

        # HACK: Works around `gb.agg(observed=False)` pandas bug. (GH32381)
        if x.size != agg.shape[1] + 1:
            agg = agg.reindex(columns=self.categoricals["x"])
        if y.size != agg.shape[0] + 1:
            agg = agg.reindex(index=self.categoricals["y"])

        if ax is None:
            fig, ax = plt.subplots()

        x, y = self._maybe_convert_to_log_scale(x, y)

        norm = kwargs.pop("norm", self._default_norm(self.axnorm))

        C = np.ma.masked_invalid(agg.values)
        XX, YY = np.meshgrid(x, y)
        pc = ax.pcolormesh(XX, YY, C, norm=norm, **kwargs)

        cbar_or_mappable = pc
        if cbar:
            cbar_kwargs = self._prepare_cbar_kwargs(cbar_kwargs, ax)

            # Pass `norm` to `self._make_cbar` so that we can choose the ticks to use.
            cbar = self._make_cbar(pc, **cbar_kwargs)
            cbar_or_mappable = cbar

        self._format_axis(ax)

        color_plot = self.data.loc[:, self.agg_axes].dropna().unique().size > 1
        if (alpha_fcn is not None) and color_plot:
            self.logger.warning(
                "Make sure you verify alpha actually set. I don't yet trust this."
            )
            alpha_agg = self.agg(fcn=alpha_fcn)
            alpha_agg = alpha_agg.unstack("x")
            alpha_agg = np.ma.masked_invalid(alpha_agg.values.ravel())
            # Feature scale then invert so smallest STD
            # is most opaque.
            alpha = 1 - mpl.colors.Normalize()(alpha_agg)
            self.logger.warning("Scaling alpha filter as alpha**0.25")
            alpha = alpha**0.25

            # Set masked values to zero. Otherwise, masked
            # values are rendered as black.
            alpha = alpha.filled(0)
            # Must draw to initialize `facecolor`s
            plt.draw()
            colors = pc.get_facecolors()
            colors[:, 3] = alpha
            pc.set_facecolor(colors)

        elif alpha_fcn is not None:
            self.logger.warning("Ignoring `alpha_fcn` because plotting counts")

        return ax, cbar_or_mappable

    def plot_hist_with_contours(
        self,
        ax=None,
        cbar=True,
        cbar_kwargs=None,
        fcn=None,
        # Contour-specific parameters
        levels=None,
        label_levels=False,
        use_contourf=True,
        contour_kwargs=None,
        clabel_kwargs=None,
        skip_max_clbl=True,
        gaussian_filter_std=0,
        gaussian_filter_kwargs=None,
        nan_aware_filter=False,
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
        label_levels : bool
            If True, add labels to contours with `ax.clabel`.
        use_contourf : bool
            If True, use filled contours. Else use line contours.
        contour_kwargs : dict, None
            Additional kwargs passed to contour/contourf (e.g., linestyles, colors).
        clabel_kwargs : dict, None
            Kwargs passed to `ax.clabel`.
        skip_max_clbl : bool
            If True, don't label the maximum contour level.
        gaussian_filter_std : int
            If > 0, apply Gaussian filter to contour data.
        gaussian_filter_kwargs : dict, None
            Kwargs passed to `scipy.ndimage.gaussian_filter`.
        nan_aware_filter : bool
            If True and gaussian_filter_std > 0, use NaN-aware filtering via
            normalized convolution. Otherwise use standard scipy.ndimage.gaussian_filter.
        kwargs :
            Passed to `ax.pcolormesh`. `norm` defaults as in `make_plot` and
            is shared by the mesh and the contours.

        Returns
        -------
        ax : mpl.axes.Axes
        cbar_or_mappable : colorbar.Colorbar or QuadMesh
        qset : QuadContourSet
            The contour set from the overlay.
        lbls : list or None
            Contour labels if label_levels is True.
        """
        if ax is None:
            fig, ax = plt.subplots()

        if contour_kwargs is None:
            contour_kwargs = {}

        norm = kwargs.pop("norm", self._default_norm(self.axnorm))

        # Get cmap from kwargs (shared between pcolormesh and contour)
        cmap = kwargs.pop("cmap", None)

        # --- 1. Plot pcolormesh background ---
        C_edges, x_edges, y_edges = self._prep_agg_for_plot(fcn=fcn, use_edges=True)

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
            if gaussian_filter_kwargs is None:
                gaussian_filter_kwargs = {}

            if nan_aware_filter:
                C_centers = self._nan_gaussian_filter(
                    C_centers, gaussian_filter_std, **gaussian_filter_kwargs
                )
            else:
                from scipy.ndimage import gaussian_filter

                C_centers = gaussian_filter(
                    C_centers, gaussian_filter_std, **gaussian_filter_kwargs
                )

            C_centers = np.ma.masked_invalid(C_centers)

        XX_centers, YY_centers = np.meshgrid(x_centers, y_centers)

        # Get contour levels
        levels = self._get_contour_levels(levels)

        # Contour function
        contour_fcn = ax.contourf if use_contourf else ax.contour

        # Default linestyles for contour
        linestyles = contour_kwargs.pop(
            "linestyles",
            [
                "-",
                ":",
                "--",
                (0, (7, 3, 1, 3, 1, 3, 1, 3, 1, 3)),
                "--",
                ":",
                "-",
                (0, (7, 3, 1, 3)),
            ],
        )

        if levels is None:
            args = [XX_centers, YY_centers, C_centers]
        else:
            args = [XX_centers, YY_centers, C_centers, levels]

        qset = contour_fcn(
            *args, linestyles=linestyles, cmap=cmap, norm=norm, **contour_kwargs
        )

        # --- 3. Contour labels ---
        lbls = None
        if label_levels:
            if clabel_kwargs is None:
                clabel_kwargs = {}

            inline = clabel_kwargs.pop("inline", True)
            inline_spacing = clabel_kwargs.pop("inline_spacing", -3)
            fmt = clabel_kwargs.pop("fmt", "%s")

            class nf(float):
                r"""Float whose repr drops trailing zeros, for contour labels."""

                def __repr__(self):
                    return float.__repr__(self).rstrip("0")

            try:
                clabel_args = (qset, levels[:-1] if skip_max_clbl else levels)
            except TypeError:
                clabel_args = (qset,)

            qset.levels = [nf(level) for level in qset.levels]
            lbls = ax.clabel(
                *clabel_args,
                inline=inline,
                inline_spacing=inline_spacing,
                fmt=fmt,
                **clabel_kwargs,
            )

        # --- 4. Colorbar ---
        cbar_or_mappable = pc
        if cbar:
            cbar_kwargs = self._prepare_cbar_kwargs(cbar_kwargs, ax)
            cbar_or_mappable = self._make_cbar(pc, **cbar_kwargs)

        # --- 5. Format axis ---
        self._format_axis(ax)

        return ax, cbar_or_mappable, qset, lbls

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
            wlength = sg_kwargs.pop("window_length", int(np.floor(y.shape[0] / 10)))
            polyorder = sg_kwargs.pop("polyorder", 3)

            if not wlength % 2:
                wlength -= 1

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
        ax:
            Axis on which to plot.
        smooth: bool
            If True, apply a Savitzky-Golay filter (:py:func:`scipy.signal.savgol_filter`)
            to the y-values before plotting to smooth the curve.
        sg_kwargs: dict, None
            If not None, dict of kwargs passed to Savitzky-Golay filter. Also allows
            for setting of `window_length` and `polyorder` as kwargs. They default to
            10% of the number of observations (`window_length`) and 3 (`polyorder`).
            Note that because `window_length` must be odd, if the 10% value is even, we
            take 1-window_length.
        kwargs:
            Passed to `ax.plot`
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

        elif (levels is None) and (self.axnorm in ["cd", "rd"]):
            levels = None

        else:
            raise ValueError(
                f"Unrecognized axis normalization {self.axnorm} for default levels."
            )

        return levels

    def _verify_contour_passthrough_kwargs(
        self, ax, clabel_kwargs, edges_kwargs, cbar_kwargs
    ):
        if clabel_kwargs is None:
            clabel_kwargs = dict()
        if edges_kwargs is None:
            edges_kwargs = dict()
        cbar_kwargs = self._prepare_cbar_kwargs(cbar_kwargs, ax)

        return clabel_kwargs, edges_kwargs, cbar_kwargs

    def plot_contours(
        self,
        ax=None,
        label_levels=True,
        cbar=True,
        cbar_kwargs=None,
        fcn=None,
        plot_edges=False,
        edges_kwargs=None,
        clabel_kwargs=None,
        skip_max_clbl=True,
        use_contourf=False,
        gaussian_filter_std=0,
        gaussian_filter_kwargs=None,
        nan_aware_filter=False,
        levels=None,
        **kwargs,
    ):
        """Make a contour plot on `ax` using `ax.contour`.

        Parameters
        ----------
        ax: mpl.axes.Axes, None
            If None, create an `Axes` instance from `plt.subplots`.
        label_levels: bool
            If True, add labels to contours with `ax.clabel`.
        cbar: bool
            If True, create color bar with `labels.z`.
        cbar_kwargs: dict, None
            If not None, kwargs passed to `self._make_cbar`.
        fcn: FunctionType, None
            Aggregation function. If None, automatically select in :py:meth:`agg`.
        plot_edges: bool
            If True, plot the smoothed, extreme edges of the 2D histogram.
        edges_kwargs: None, dict
            Passed to {self.plot_edges!s}.
        clabel_kwargs: None, dict
            If not None, dictionary of kwargs passed to `ax.clabel`.
        skip_max_clbl: bool
            If True, don't label the maximum contour. Primarily used when the maximum
            contour is, effectively, a point.
        use_contourf: bool
            If True, use `ax.contourf`. Else use `ax.contour`.
        gaussian_filter_std: int
            If > 0, apply `scipy.ndimage.gaussian_filter` to the z-values using the
            standard deviation specified by `gaussian_filter_std`.
        gaussian_filter_kwargs: None, dict
            If not None and gaussian_filter_std > 0, passed to :func:`scipy.ndimage.gaussian_filter`
        nan_aware_filter: bool
            If True and gaussian_filter_std > 0, use NaN-aware filtering via
            normalized convolution. Otherwise use standard scipy.ndimage.gaussian_filter.
        levels: array-like, int, None
            Contour levels. If None, the default for the ``axnorm``, or
            matplotlib's choice when there is none.
        kwargs:
            Passed to :meth:`matplotlib.axes.Axes.contour` or
            :meth:`matplotlib.axes.Axes.contourf`. `norm` defaults to ten
            colour bands on [0, 1] for row or column normalized data and to a
            `LogNorm` for densities ("d", "cd", "rd"); otherwise, with at
            least two levels, to a `BoundaryNorm` on the levels.
        """
        cmap = kwargs.pop("cmap", None)
        norm = kwargs.pop("norm", self._default_norm(self.axnorm))
        linestyles = kwargs.pop(
            "linestyles",
            [
                "-",
                ":",
                "--",
                (0, (7, 3, 1, 3, 1, 3, 1, 3, 1, 3)),
                "--",
                ":",
                "-",
                (0, (7, 3, 1, 3, 1, 3)),
            ],
        )

        if ax is None:
            fig, ax = plt.subplots()

        (
            clabel_kwargs,
            edges_kwargs,
            cbar_kwargs,
        ) = self._verify_contour_passthrough_kwargs(
            ax, clabel_kwargs, edges_kwargs, cbar_kwargs
        )

        inline = clabel_kwargs.pop("inline", True)
        inline_spacing = clabel_kwargs.pop("inline_spacing", -3)
        fmt = clabel_kwargs.pop("fmt", "%s")

        agg = self.agg(fcn=fcn).unstack("x")
        x = self.intervals["x"].mid
        y = self.intervals["y"].mid

        # HACK: Works around `gb.agg(observed=False)` pandas bug. (GH32381)
        if x.size != agg.shape[1]:
            agg = agg.reindex(columns=self.categoricals["x"])
        if y.size != agg.shape[0]:
            agg = agg.reindex(index=self.categoricals["y"])

        x, y = self._maybe_convert_to_log_scale(x, y)

        XX, YY = np.meshgrid(x, y)

        C = agg.values
        if gaussian_filter_std:
            if gaussian_filter_kwargs is None:
                gaussian_filter_kwargs = dict()

            if nan_aware_filter:
                C = self._nan_gaussian_filter(
                    C, gaussian_filter_std, **gaussian_filter_kwargs
                )
            else:
                from scipy.ndimage import gaussian_filter

                C = gaussian_filter(C, gaussian_filter_std, **gaussian_filter_kwargs)

        C = np.ma.masked_invalid(C)

        assert XX.shape == C.shape
        assert YY.shape == C.shape

        class nf(float):
            # Source: https://matplotlib.org/3.1.0/gallery/images_contours_and_fields/contour_label_demo.html
            # Define a class that forces representation of float to look a certain way
            # This remove trailing zero so '1.0' becomes '1'
            r"""Float whose repr drops trailing zeros, for contour labels."""

            def __repr__(self):
                return float.__repr__(self).rstrip("0")

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

        try:
            args = (qset, levels[:-1] if skip_max_clbl else levels)
        except TypeError:
            # None can't be subscripted.
            args = (qset,)

        lbls = None
        if label_levels:
            qset.levels = [nf(level) for level in qset.levels]
            lbls = ax.clabel(
                *args,
                inline=inline,
                inline_spacing=inline_spacing,
                fmt=fmt,
                **clabel_kwargs,
            )

        if plot_edges:
            etop, ebottom = self.plot_edges(ax, **edges_kwargs)

        cbar_or_mappable = qset
        if cbar:
            # Pass `norm` to `self._make_cbar` so that we can choose the ticks to use.
            cbar = self._make_cbar(qset, norm=norm, **cbar_kwargs)
            cbar_or_mappable = cbar

        self._format_axis(ax)

        return ax, lbls, cbar_or_mappable, qset

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
            :class:`~solarwindpy.plotting.hist1d.Hist1D`.
            Otherwise, send both axes (but not z-values).
        kwargs:
            Passed to `Hist1D`. Primarily to allow specifying `bin_precision`.

        Returns
        -------
        h1: solarwindpy.plotting.hist1d.Hist1D
        """
        axis = axis.lower()
        assert axis in ("x", "y")

        data = self.data

        if data.loc[:, "z"].unique().size >= 2:
            # Either all 1 or 1 and NaN.
            other = "z"
        else:
            possible_axes = {"x", "y"}
            possible_axes.remove(axis)
            other = possible_axes.pop()

        logx = self.log._asdict()[axis]
        x = self.data.loc[:, axis]
        if logx:
            # Need to convert back to regular from log-space for data setting.
            x = 10.0**x

        y = self.data.loc[:, other] if not project_counts else None
        logy = False  # Defined b/c project_counts option.
        if y is not None and (other == "y"):
            # Only select y-values plotted.
            logy = self.log._asdict()[other]
            yedges = self.edges[other].values
            y = y.where((yedges[0] <= y) & (y <= yedges[-1]))
            if logy:
                y = 10.0**y

        if only_plotted:
            tk = self.get_plotted_data_boolean_series()
            x = x.loc[tk]
            if y is not None:
                y = y.loc[tk]

        h1 = Hist1D(
            x,
            y=y,
            logx=logx,
            clip_data=False,  # Any clipping will be addressed by bins.
            nbins=self.edges[axis].values,
            **kwargs,
        )

        h1.set_log(y=logy)  # Need to propagate logy.
        h1.set_labels(x=self.labels._asdict()[axis])
        if not project_counts:
            h1.set_labels(y=self.labels._asdict()[other])

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
        _, cbar = self.make_plot(
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
        """
        x = self.data.x
        y = self.data.y
        # Object dtype, because the values written below are `pd.Interval`s.
        above_contour = pd.Series(np.nan, self.data.index, dtype=object)
        for k, v in self.agg().unstack("x").items():
            tk = v >= level
            if not tk.any():
                # Nothing in this column reaches `level`; its points stay NaN.
                continue
            left, right = k.left, k.right
            bottom, top = v[tk].index.min().left, v[tk].index.max().right
            above_contour_at_x = (left < x) & (x <= right) & (bottom < y) & (y <= top)
            above_contour[above_contour_at_x] = k

        above_contour = pd.Series(
            pd.Categorical(above_contour), index=above_contour.index
        )

        return above_contour

    def take_data_in_yrange_across_x(
        self,
        ranges_by_x,
        get_x_bounds,
        get_y_bounds,
    ):
        r"""Take data within y-ranges across x-values.

        Parameters
        ----------
        ranges_by_x: iterable
            An iterable with keys used to get the left and right bounds for the data
            and values used to get the top and bottom bounds for the data.

        get_x_bounds: function
            First argument is one key of `ranges_by_x` and returns `left, right`.
            Second argument is a kwarg (`expected_logx`) boolean to transform the returned values according
            to whether or not the keys are :math:`log(x)` or :math:`x` in a manner
            that matches data stored in Hist2D.

        get_y_bounds: functions
            Takes on value of `ranges_by_x` and returns `top, bottom`. Second argument
            Second argument is a kwarg (`expected_logx`) boolean to transform the returned values according
            to whether or not the keys are :math:`log(y)` or :math:`y` in a manner
            that matches data stored in Hist2D.

        Returns
        -------
        taken: np.ndarray 1D
            Array of indices for selecting data in interval.
        """

        available_x = self.agg().unstack("x").columns
        if ranges_by_x.index.symmetric_difference(available_x).size:
            drop = ranges_by_x.index.symmetric_difference(available_x)
            if not drop.isin(available_x).all():
                raise ValueError(
                    "Need a way to drop values in selector that aren't available."
                )
            else:
                self.logger.warning(
                    f"Dropping {drop.size} intervals from available for selecting."
                )

        data = self.data
        logx = self.log.x
        logy = self.log.y

        taken = []
        for x, at_x in ranges_by_x.iterrows():
            l, r = get_x_bounds(x, expected_logx=logx)
            b, t = get_y_bounds(at_x, expected_logy=logy)

            assert l < r
            assert b < t

            tkx = (l < data.x) & (data.x <= r)
            tky = (b < data.y) & (data.y <= t)
            tk = tkx & tky
            tk = tk.loc[tk].index
            taken.append(tk)

        taken = np.sort(np.concatenate(taken))
        return taken
