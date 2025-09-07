#!/usr/bin/env python
r"""Two-dimensional histogram and heatmap plotting utilities."""

import pdb  # noqa: F401

import numpy as np
import pandas as pd
import matplotlib as mpl

from matplotlib import pyplot as plt
from collections import namedtuple
from scipy.signal import savgol_filter


from . import base
from . import labels as labels_module

# from .agg_plot import AggPlot
# from .hist1d import Hist1D

from . import agg_plot
from . import hist1d

AggPlot = agg_plot.AggPlot
Hist1D = hist1d.Hist1D

# import os
# import psutil


# def log_mem_usage():
#    usage = psutil.Process(os.getpid()).memory_info()
#    usage = "\n".join(
#        ["{} {:.3f} GB".format(k, v * 1e-9) for k, v in usage._asdict().items()]
#    )
#    logging.getLogger("main").warning("Memory usage\n%s", usage)


# class Hist2D(base.Plot2D, AggPlot):
class Hist2D(base.PlotWithZdata, base.CbarMaker, AggPlot):
    r"""Create a 2D histogram with an optional z-value using an equal number.

    of bins along the x and y axis.

    Parameters
    ----------
    x, y: pd.Series
        x and y data to aggregate
    z: None, pd.Series
        If not None, the z-value to aggregate.
    axnorm: str
        Normalize the histogram.
            key  normalization
            ---  -------------
            c    column
            r    row
            t    total
            d    density
    logx, logy: bool
        If True, log10 scale the axis.

    Attributes
    ----------
    data:
    bins:
    cut:
    axnorm:
    log<x,y>:
    <x,y,z>label:
    path: None, Path

    Methods
    -------
    calc_bins:
        calculate the x, y bins.
    make_cut:
        Utilize the calculated bins to convert (x, y) into pd.Categoral
        or pd.Interval values used in aggregation.
    set_[x,y,z]label:
        Set the x, y, or z label.
    agg:
        Aggregate the data in the bins.
        If z-value is None, count the number of points in each bin.
        If z-value is not None, calculate the mean for each bin.
    make_plot:
        Make a 2D plot of the data with an optional color bar.
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
        self.set_alim(None, None)

    @property
    def _gb_axes(self):
        return ("x", "y")

    def _maybe_convert_to_log_scale(self, x, y):
        if self.log.x:
            x = 10.0**x
        if self.log.y:
            y = 10.0**y

        return x, y

    #     def set_path(self, new, add_scale=True):
    #         # Bug: path doesn't auto-set log information.
    #         path, x, y, z, scale_info = super().set_path(new, add_scale)

    #         if new == "auto":
    #             path = path / x / y / z

    #         else:
    #             assert x is None
    #             assert y is None
    #             assert z is None

    #         if add_scale:
    #             assert scale_info is not None

    #             scale_info = "-".join(scale_info)

    #             if bool(len(path.parts)) and path.parts[-1].endswith("norm"):
    #                 # Insert <norm> at end of path so scale order is (x, y, z).
    #                 path = path.parts
    #                 path = path[:-1] + (scale_info + "-" + path[-1],)
    #                 path = Path(*path)
    #             else:
    #                 path = path / scale_info

    #         self._path = path

    #     set_path.__doc__ = base.Base.set_path.__doc__

    def set_labels(self, **kwargs):

        z = kwargs.pop("z", self.labels.z)
        if isinstance(z, labels_module.Count):
            try:
                z.set_axnorm(self.axnorm)
            except AttributeError:
                pass

            z.build_label()

        super().set_labels(z=z, **kwargs)

    #     def set_data(self, x, y, z, clip):
    #         data = pd.DataFrame(
    #             {
    #                 "x": np.log10(np.abs(x)) if self.log.x else x,
    #                 "y": np.log10(np.abs(y)) if self.log.y else y,
    #             }
    #         )
    #
    #
    #         if z is None:
    #             z = pd.Series(1, index=x.index)
    #
    #         data.loc[:, "z"] = z
    #         data = data.dropna()
    #         if not data.shape[0]:
    #             raise ValueError(
    #                 "You can't build a %s with data that is exclusively NaNs"
    #                 % self.__class__.__name__
    #             )
    #
    #         self._data = data
    #         self._clip = clip

    def set_data(self, x, y, z, clip):
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
         t     Total normalize
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

        Written basically as `staticmethod` so that can be called in `OrbitHist2D`, but
        as actual method with `self` passed so we have access to `self.log` for density
        normalization.
        """

        axnorm = self.axnorm
        if axnorm is None:
            pass
        elif axnorm == "c":
            agg = agg.divide(agg.groupby(level="x").max(), level="x")
        elif axnorm == "r":
            agg = agg.divide(agg.groupby(level="y").max(), level="y")
        elif axnorm == "t":
            agg = agg.divide(agg.max())
        elif axnorm == "d":
            N = agg.sum().sum()
            x = pd.IntervalIndex(agg.index.get_level_values("x").unique())
            y = pd.IntervalIndex(agg.index.get_level_values("y").unique())
            dx = pd.Series(
                x.length, index=x
            )  # dx = pd.Series(x.right - x.left, index=x)
            dy = pd.Series(
                y.length, index=y
            )  # dy = pd.Series(y.right - y.left, index=y)

            if self.log.x:
                dx = 10.0**dx
            if self.log.y:
                dy = 10.0**dy

            agg = agg.divide(dx, level="x").divide(dy, level="y").divide(N)

        elif axnorm == "cd":
            #             raise NotImplementedError("Need to verify data alignment, especially `dx` values and index")
            N = agg.groupby(level="x").sum()
            dy = pd.IntervalIndex(
                agg.index.get_level_values("y").unique()
            ).sort_values()
            dy = pd.Series(dy.length, index=dy).sort_index()
            # Divide by total in each column and each row's width
            agg = agg.divide(N, level="x").divide(dy, level="y")

        elif axnorm == "rd":
            #             raise NotImplementedError("Need to verify data alignment, especially `dx` values and index")
            N = agg.groupby(level="y").sum()
            dx = pd.IntervalIndex(
                agg.index.get_level_values("x").unique()
            ).sort_values()
            dx = pd.Series(dx.length, index=dx).sort_index()
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
        agg = super().agg(**kwargs)
        agg = self._axis_normalizer(agg)
        agg = self._agg_reindexer(agg)

        a0, a1 = self.alim
        if a0 is not None or a1 is not None:
            tk = pd.Series(True, index=agg.index)
            #             tk  = pd.DataFrame(True,
            #                                index=agg.index,
            #                                columns=agg.columns
            #                               )
            if a0 is not None:
                tk = tk & (agg >= a0)
            if a1 is not None:
                tk = tk & (agg <= a1)

            agg = agg.where(tk)

        return agg

    def _make_cbar(self, mappable, **kwargs):
        ticks = kwargs.pop(
            "ticks",
            mpl.ticker.MultipleLocator(0.1) if self.axnorm in ("c", "r") else None,
        )
        return super()._make_cbar(mappable, ticks=ticks, **kwargs)

    def _limit_color_norm(self, norm):
        if self.axnorm in ("c", "r"):
            # Don't limit us to (1%, 99%) interval.
            return None

        pct = self.data.loc[:, "z"].quantile([0.01, 0.99])
        v0 = pct.loc[0.01]
        v1 = pct.loc[0.99]
        if norm.vmin is None:
            norm.vmin = v0
        if norm.vmax is None:
            norm.vmax = v1
        norm.clip = True

    def make_plot(
        self,
        ax=None,
        cbar=True,
        limit_color_norm=False,
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
        limit_color_norm: bool
            If True, limit the color range to 0.001 and 0.999 percentile range
            of the z-value, count or otherwise.
        cbar_kwargs: dict, None
            If not None, kwargs passed to `self._make_cbar`.
        fcn: FunctionType, None
            Aggregation function. If None, automatically select in :py:meth:`agg`.
        alpha_fcn: None, str
            If not None, the function used to aggregate the data for setting alpha
            value.
        kwargs:
            Passed to `ax.pcolormesh`.
            If row or column normalized data, `norm` defaults to `mpl.colors.Normalize(0, 1)`.

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

        #         assert x.size == agg.shape[1] + 1
        #         assert y.size == agg.shape[0] + 1

        # HACK: Works around `gb.agg(observed=False)` pandas bug. (GH32381)
        if x.size != agg.shape[1] + 1:
            #             agg = agg.reindex(columns=self.intervals["x"])
            agg = agg.reindex(columns=self.categoricals["x"])
        if y.size != agg.shape[0] + 1:
            #             agg = agg.reindex(index=self.intervals["y"])
            agg = agg.reindex(index=self.categoricals["y"])

        if ax is None:
            fig, ax = plt.subplots()

        #         if self.log.x:
        #             x = 10.0 ** x
        #         if self.log.y:
        #             y = 10.0 ** y
        x, y = self._maybe_convert_to_log_scale(x, y)

        axnorm = self.axnorm
        default_norm = None
        if axnorm in ("c", "r"):
            default_norm = mpl.colors.BoundaryNorm(
                np.linspace(0, 1, 11), 256, clip=True
            )
        elif axnorm in ("d", "cd", "rd"):
            default_norm = mpl.colors.LogNorm(clip=True)
        norm = kwargs.pop("norm", default_norm)

        if limit_color_norm:
            self._limit_color_norm(norm)

        C = np.ma.masked_invalid(agg.values)
        XX, YY = np.meshgrid(x, y)
        pc = ax.pcolormesh(XX, YY, C, norm=norm, **kwargs)

        cbar_or_mappable = pc
        if cbar:
            if cbar_kwargs is None:
                cbar_kwargs = dict()

            if "cax" not in cbar_kwargs.keys() and "ax" not in cbar_kwargs.keys():
                cbar_kwargs["ax"] = ax

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
            # Remove `pc` from axis so we can redraw with std
            #             pc.remove()
            colors = pc.get_facecolors()
            colors[:, 3] = alpha
            pc.set_facecolor(colors)
        #             ax.add_collection(pc)

        elif alpha_fcn is not None:
            self.logger.warning("Ignoring `alpha_fcn` because plotting counts")

        return ax, cbar_or_mappable

    def get_border(self):
        r"""Get the top and bottom edges of the plot.

        Returns
        -------
        border: namedtuple
            Contains "top" and "bottom" fields, each with a :py:class:`pd.Series`.
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

        if sg_kwargs is None:
            sg_kwargs = dict()

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

        #         if (~tk).any():
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
        if cbar_kwargs is None:
            cbar_kwargs = dict()
        if "cax" not in cbar_kwargs.keys() and "ax" not in cbar_kwargs.keys():
            cbar_kwargs["ax"] = ax

        return clabel_kwargs, edges_kwargs, cbar_kwargs

    def plot_contours(
        self,
        ax=None,
        label_levels=True,
        cbar=True,
        limit_color_norm=False,
        cbar_kwargs=None,
        fcn=None,
        plot_edges=False,
        edges_kwargs=None,
        clabel_kwargs=None,
        skip_max_clbl=True,
        use_contourf=False,
        gaussian_filter_std=0,
        gaussian_filter_kwargs=None,
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
        limit_color_norm: bool
            If True, limit the color range to 0.001 and 0.999 percentile range
            of the z-value, count or otherwise.
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
        maximum_color:
            The color for the maximum of the PDF.
        use_contourf: bool
            If True, use `ax.contourf`. Else use `ax.contour`.
        gaussian_filter_std: int
            If > 0, apply `scipy.ndimage.gaussian_filter` to the z-values using the
            standard deviation specified by `gaussian_filter_std`.
        gaussian_filter_kwargs: None, dict
            If not None and gaussian_filter_std > 0, passed to :py:meth:`scipy.ndimage.gaussian_filter`
        kwargs:
            Passed to :py:meth:`ax.pcolormesh`.
            If row or column normalized data, `norm` defaults to `mpl.colors.Normalize(0, 1)`.
        """
        levels = kwargs.pop("levels", None)
        cmap = kwargs.pop("cmap", None)
        norm = kwargs.pop(
            "norm",
            (
                mpl.colors.BoundaryNorm(np.linspace(0, 1, 11), 256, clip=True)
                if self.axnorm in ("c", "r")
                else None
            ),
        )
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

        #         assert x.size == agg.shape[1]
        #         assert y.size == agg.shape[0]

        # HACK: Works around `gb.agg(observed=False)` pandas bug. (GH32381)
        if x.size != agg.shape[1]:
            #             agg = agg.reindex(columns=self.intervals["x"])
            agg = agg.reindex(columns=self.categoricals["x"])
        if y.size != agg.shape[0]:
            #             agg = agg.reindex(index=self.intervals["y"])
            agg = agg.reindex(index=self.categoricals["y"])

        x, y = self._maybe_convert_to_log_scale(x, y)

        XX, YY = np.meshgrid(x, y)

        C = agg.values
        if gaussian_filter_std:
            from scipy.ndimage import gaussian_filter

            if gaussian_filter_kwargs is None:
                gaussian_filter_kwargs = dict()

            C = gaussian_filter(C, gaussian_filter_std, **gaussian_filter_kwargs)

        C = np.ma.masked_invalid(C)

        assert XX.shape == C.shape
        assert YY.shape == C.shape

        class nf(float):
            # Source: https://matplotlib.org/3.1.0/gallery/images_contours_and_fields/contour_label_demo.html
            # Define a class that forces representation of float to look a certain way
            # This remove trailing zero so '1.0' becomes '1'
            def __repr__(self):
                return str(self).rstrip("0")

        levels = self._get_contour_levels(levels)

        if (norm is None) and (levels is not None):
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
        """Make a `Hist1D` from the data stored in this `His2D`.

        Parameters
        ----------
        axis: str
            "x" or "y", specifying the axis to project into 1D.
        only_plotted: bool
            If True, only pass data that appears in the {self.__class__.__name__} plot
            to the :py:class:`Hist1D`.
        project_counts: bool
            If True, only send the variable plotted along `axis` to :py:class:`Hist1D`.
            Otherwise, send both axes (but not z-values).
        kwargs:
            Passed to `Hist1D`. Primarily to allow specifying `bin_precision`.

        Returns
        -------
        h1: :py:class:`Hist1D`
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
        figsize = kwargs.pop("figsize", (5, 6))
        height_ratios = kwargs.pop("height_ratios", [0.25, 1, 0.2, 0.1])
        width_ratios = kwargs.pop("width_ratios", [1, 0.25])
        hspace = kwargs.pop("hspace", 0)
        wspace = kwargs.pop("wspace", 0)

        #         if fig_axes is not None:
        #             fig, axes = fig_axes
        #             hax, xax, yax, cax = axes
        #         else:
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

        cbar_kwargs = kwargs.pop("cbar_kwargs", dict())
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
        above_contour = pd.Series(np.nan, self.data.index)
        for k, v in self.agg().unstack("x").items():
            tk = v >= level
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
