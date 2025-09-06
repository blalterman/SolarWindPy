#!/usr/bin/env python
r"""Two-dimensional histogram and heatmap plotting utilities.

This module provides the Hist2D class for creating publication-quality 2D histograms
optimized for solar wind parameter correlation studies. Features include statistical
normalization schemes, logarithmic scaling, contour plotting, boundary detection,
and joint visualization with marginal distributions.

Key Features:
- Multiple statistical normalization methods (density, column/row, total)
- Automatic colorbar management with appropriate tick spacing
- Contour plotting with automatic level selection
- Boundary edge detection and visualization
- Joint plots with marginal 1D histograms
- Support for log-scaled axes with proper coordinate handling
- Integration with matplotlib's pcolormesh, contour, and contourf
- Alpha blending for uncertainty visualization
- Data selection tools for contour-based analysis

Classes:
    Hist2D : Main 2D histogram class extending PlotWithZdata, CbarMaker, AggPlot

Typical Usage:
    >>> h2d = Hist2D(vx, vy, density, axnorm='d', logx=True)
    >>> ax, cbar = h2d.make_plot()
    >>> ax, labels, cbar, cs = h2d.plot_contours(plot_edges=True)
"""

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
    r"""Create publication-quality 2D histograms for solar wind parameter analysis.

    This class extends PlotWithZdata, CbarMaker, and AggPlot to provide
    comprehensive 2D histogram visualization capabilities with statistical
    normalization schemes optimized for plasma physics correlation studies.

    The class supports various statistical normalizations, logarithmic scaling,
    contour plotting, edge detection, and joint histogram visualization with
    marginal distributions.

    Parameters
    ----------
    x, y : pd.Series or array-like
        X and Y coordinate data for histogram binning
    z : None or pd.Series, optional
        Z-values for color mapping. If None, counts points in each bin.
        If provided, computes mean z-value for each bin.
    axnorm : str or tuple, optional
        Normalization method for the aggregated data:

        **String normalization options**:

        ===== =============================================================
         key                           description
        ===== =============================================================
         c     Column normalize (divide each column by its maximum)
         r     Row normalize (divide each row by its maximum)
         t     Total normalize (divide all values by global maximum)
         d     Density normalize (proper PDF with bin width correction)
         cd    Column density (PDF in each column, marginal along y)
         rd    Row density (PDF in each row, marginal along x)
        ===== =============================================================

        **CRITICAL UNDOCUMENTED FEATURE - Tuple normalization**:

        axnorm can also be a tuple (kind, function) for custom normalization:

        - kind : {'c', 'r'} - Column or row normalization
        - function : str or callable - Aggregation function name or function

        Examples: ('c', 'mean'), ('r', 'median'), ('c', 'std')

        **WARNING**: Tuple functionality is UNTESTED and may not integrate
        properly with colorbar labels or other visualization features.

    logx, logy : bool, optional
        If True, apply log10 transformation to the respective axis.
        Default is False.
    clip_data : bool, optional
        Enable data clipping functionality. Default is False.
    nbins : int, optional
        Number of bins for histogram. Default is 101.
    bin_precision : int, optional
        Decimal precision for bin edges. Default uses internal heuristics.

    Attributes
    ----------
    data : pd.DataFrame
        Processed data with 'x', 'y', and 'z' columns
    bins : dict
        Bin edge arrays for x and y axes
    intervals : dict
        Pandas IntervalIndex objects for x and y binning
    categoricals : dict
        Pandas Categorical objects for efficient aggregation
    edges : dict
        Bin edge arrays converted for matplotlib plotting
    axnorm : str or tuple
        Current normalization method
    log : namedtuple
        Logarithmic scaling flags for x and y axes
    labels : namedtuple
        Axis labels with proper TeX formatting
    clim : tuple
        Color scale limits (vmin, vmax)
    alim : tuple
        Amplitude limits for data filtering

    Methods
    -------
    **Core Functionality**:

    make_plot(ax=None, cbar=True, **kwargs)
        Create pcolormesh visualization with optional colorbar
    agg(fcn=None, **kwargs)
        Aggregate data with normalization and amplitude limiting
    plot_contours(ax=None, levels=None, **kwargs)
        Generate contour plot with automatic level selection

    **Boundary Analysis**:

    get_border()
        Extract top and bottom edges of data distribution
    plot_edges(ax, smooth=True, **kwargs)
        Overlay boundary edges on existing plot

    **Composite Visualizations**:

    make_joint_h2_h1_plot(project_counts=True, **kwargs)
        Create joint plot with 2D histogram and marginal distributions
    project_1d(axis, only_plotted=True, **kwargs)
        Project 2D data onto 1D histogram for marginal analysis

    **Data Selection**:

    id_data_above_contour(level)
        Identify data points above specified contour level
    take_data_in_yrange_across_x(ranges_by_x, get_x_bounds, get_y_bounds)
        Extract data within specified y-ranges across x-values

    **Configuration**:

    set_axnorm(new)
        Update normalization method with validation
    set_labels(**kwargs)
        Set axis labels with Count label integration

    **Internal Methods**:

    _axis_normalizer(agg)
        Apply statistical normalization to aggregated data
    _maybe_convert_to_log_scale(x, y)
        Handle coordinate conversion for log-scaled axes
    _plot_one_edge(ax, edge, smooth=False, **kwargs)
        Plot individual boundary edge with optional smoothing

    Notes
    -----
    **Integration with matplotlib**:
    The class provides seamless integration with matplotlib's pcolormesh,
    contour, and contourf functions while handling coordinate transformations,
    normalization, and colorbar management automatically.

    **Performance considerations**:
    - Large datasets: Consider using amplitude limiting (alim)
    - Sparse data: Apply Gaussian filtering in plot_contours
    - Memory efficiency: Use categorical aggregation with observed=False

    **Solar wind applications**:
    Common use cases include velocity-temperature correlations, magnetic
    field component analysis, and density-speed relationship studies.

    Examples
    --------
    Basic 2D histogram:

    >>> h2d = Hist2D(vx, vy, axnorm='d')  # Density normalization
    >>> fig, ax = plt.subplots()
    >>> ax, cbar = h2d.make_plot(ax=ax)

    Contour plot with edges:

    >>> ax, labels, cbar, cs = h2d.plot_contours(plot_edges=True)

    Joint plot with marginals:

    >>> hax, xax, yax, cbar = h2d.make_joint_h2_h1_plot(figsize=(8, 8))
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
        """Initialize a 2D histogram plot.

        Parameters
        ----------
        x : array-like
            X-coordinate data for the histogram
        y : array-like
            Y-coordinate data for the histogram
        z : array-like, optional
            Z-values for color mapping. If None, counts points in each bin.
        axnorm : str, optional
            Normalization method. See set_axnorm() for supported values.
        logx : bool, optional
            If True, apply log10 transformation to x-axis data. Default is False.
        logy : bool, optional
            If True, apply log10 transformation to y-axis data. Default is False.
        clip_data : bool, optional
            If True, enable data clipping. Default is False.
        nbins : int, optional
            Number of bins for histogram. Default is 101.
        bin_precision : int, optional
            Decimal precision for bin edges. Default is None (uses internal default).
        """
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
        """Convert log-scale data back to linear scale if needed.

        This method handles the conversion from logarithmic coordinates back to
        linear coordinates for plotting. It's used internally when preparing
        data for matplotlib functions that expect linear coordinates.

        Parameters
        ----------
        x : array-like
            X-coordinate data (may be log-transformed)
        y : array-like
            Y-coordinate data (may be log-transformed)

        Returns
        -------
        tuple
            (x, y) data converted back to linear scale if log scaling is enabled.
            If logarithmic scaling is not enabled for an axis, that axis data
            is returned unchanged.

        Notes
        -----
        This conversion is necessary because matplotlib plotting functions expect
        linear coordinate values, while internally the histogram may store data
        in log10 space for computational efficiency.
        """
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
        """Set axis labels with special handling for Count labels.

        Automatically updates Count label objects to reflect the current
        normalization method (axnorm) and rebuilds the label string.

        Parameters
        ----------
        **kwargs
            Axis labels including 'z' for colorbar label
        """
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
        """Set plotting data with logarithmic transformation if needed.

        Calls the parent set_data method and then applies log10 transformation
        to x and/or y data if logarithmic scaling is enabled.

        Parameters
        ----------
        x : array-like
            X-coordinate data
        y : array-like
            Y-coordinate data
        z : array-like
            Z-values for color mapping
        clip : bool
            Whether to enable data clipping
        """
        super().set_data(x, y, z, clip)
        data = self.data
        if self.log.x:
            data.loc[:, "x"] = np.log10(np.abs(data.loc[:, "x"]))
        if self.log.y:
            data.loc[:, "y"] = np.log10(np.abs(data.loc[:, "y"]))
        self._data = data

    def set_axnorm(self, new):
        r"""Set the normalization method for 2D histogram data.

        Configures how the aggregated histogram data is normalized for
        visualization and statistical analysis. Supports both standard
        string-based normalization methods and an advanced undocumented
        tuple-based system for custom aggregation functions.

        Parameters
        ----------
        new : str, tuple, or None
            Normalization method specification:

            **Standard String Methods**:

            ===== =============================================================
             key                           description
            ===== =============================================================
             c     Column normalize (divide each column by its maximum)
             r     Row normalize (divide each row by its maximum)
             t     Total normalize (divide all values by global maximum)
             d     Density normalize (proper PDF with bin width correction)
             cd    Column density (PDF in each column, marginal along y)
             rd    Row density (PDF in each row, marginal along x)
            ===== =============================================================

            **ADVANCED TUPLE INTERFACE** (UNDOCUMENTED & UNTESTED):

            For custom normalization, pass tuple (kind, function):

            - kind : {'c', 'r'}
                'c' for column-wise normalization, 'r' for row-wise
            - function : str or callable
                Pandas aggregation function name or callable function

            Examples:

            - ('c', 'mean') : Divide each column by its mean
            - ('c', 'median') : Divide each column by its median
            - ('r', 'std') : Divide each row by its standard deviation
            - ('c', lambda x: x.quantile(0.9)) : Custom function

            **CRITICAL WARNING**: The tuple functionality:

            - Has NO test coverage or validation
            - May not integrate with colorbar labeling systems
            - Could break with Count label objects
            - May not handle edge cases (all zeros, NaNs, etc.)
            - Is not documented in the main class docstring

            **Use tuple interface at your own risk** and validate results
            thoroughly before using in production or publications.

        Raises
        ------
        AssertionError
            If string normalization method is not recognized
        ValueError
            If tuple normalization has invalid kind parameter

        Notes
        -----
        **Density Normalization ('d', 'cd', 'rd')**:
        These methods account for bin widths and logarithmic scaling to
        produce proper probability density functions. Essential for
        statistical analysis of solar wind parameter distributions.

        **Column/Row Normalization ('c', 'r')**:
        Useful for comparing relative distributions across one dimension
        while preserving shape information along the other.

        **Label Integration**:
        Automatically updates Count label objects to reflect the current
        normalization method, ensuring proper colorbar labeling.

        **Implementation Location**:
        The actual normalization logic is implemented in _axis_normalizer()
        method at lines 383-391 for the undocumented tuple feature.

        Examples
        --------
        Standard normalization:

        >>> h2d.set_axnorm('d')  # Density normalization
        >>> h2d.set_axnorm('c')  # Column normalization

        Advanced tuple usage (EXPERIMENTAL):

        >>> h2d.set_axnorm(('c', 'mean'))    # Column mean normalization
        >>> h2d.set_axnorm(('r', 'median'))  # Row median normalization

        Reset to no normalization:

        >>> h2d.set_axnorm(None)
        """
        if new is not None:
            new = new.lower()
            # Validate string normalization methods
            # Note: tuple methods are validated in _axis_normalizer
            valid_string_methods = {"c", "r", "t", "d", "cd", "rd"}
            if isinstance(new, str):
                assert new in valid_string_methods, (
                    f"Unrecognized axnorm '{new}'. "
                    f"Valid string methods: {sorted(valid_string_methods)}. "
                    f"Tuple methods (kind, function) also supported but undocumented."
                )

        zlbl = self.labels.z
        if isinstance(zlbl, labels_module.Count):
            zlbl.set_axnorm(new)
            zlbl.build_label()

        self._axnorm = new

    def _axis_normalizer(self, agg):
        r"""Apply normalization to aggregated histogram data.

        Handles row, column, total, and density normalization methods.
        Written as an instance method (rather than staticmethod) to access
        `self.log` for proper density normalization calculations.

        This method implements the core 2D histogram normalization algorithms
        used in solar wind parameter correlation studies, allowing for proper
        statistical comparison across different data distributions.

        Parameters
        ----------
        agg : pandas.Series
            Aggregated histogram data with MultiIndex (x, y) representing
            binned count or mean values

        Returns
        -------
        pandas.Series
            Normalized aggregated data according to the axnorm specification

        Notes
        -----
        This method can be called from other classes like `OrbitHist2D`
        which is why it's designed with minimal external dependencies.

        The density normalization ('d', 'cd', 'rd') accounts for logarithmic
        scaling by converting bin widths back to linear scale before normalization.
        This ensures proper probability density function (PDF) normalization
        when dealing with log-transformed data common in plasma physics.

        **CRITICAL UNDOCUMENTED FEATURE**: Lines 383-391 implement tuple support
        for axnorm parameter. When axnorm is a tuple (kind, function), it applies
        custom aggregation functions for normalization:

        - ('c', function): Column-wise normalization using specified function
        - ('r', function): Row-wise normalization using specified function

        Examples of tuple usage (UNTESTED):
        - axnorm=('c', 'mean'): Divide each column by its mean
        - axnorm=('c', 'median'): Divide each column by its median
        - axnorm=('r', 'std'): Divide each row by its standard deviation

        **WARNING**: This tuple functionality lacks comprehensive testing and
        may not integrate properly with colorbar labeling or other features.
        Use with caution and validate results thoroughly.

        Normalization Types
        -------------------
        'c' : Column normalization
            Each column divided by its maximum value
        'r' : Row normalization
            Each row divided by its maximum value
        't' : Total normalization
            All values divided by global maximum
        'd' : Density normalization
            Proper PDF normalization accounting for bin widths
        'cd' : Column density normalization
            PDF in each column (marginal distribution along y)
        'rd' : Row density normalization
            PDF in each row (marginal distribution along x)
        """

        axnorm = self.axnorm
        if axnorm is None:
            pass
        elif axnorm == "c":
            agg = agg.divide(agg.max(level="x"), level="x")
        elif axnorm == "r":
            agg = agg.divide(agg.max(level="y"), level="y")
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
            N = agg.sum(level="x")
            dy = pd.IntervalIndex(
                agg.index.get_level_values("y").unique()
            ).sort_values()
            dy = pd.Series(dy.length, index=dy).sort_index()
            # Divide by total in each column and each row's width
            agg = agg.divide(N, level="x").divide(dy, level="y")

        elif axnorm == "rd":
            #             raise NotImplementedError("Need to verify data alignment, especially `dx` values and index")
            N = agg.sum(level="y")
            dx = pd.IntervalIndex(
                agg.index.get_level_values("x").unique()
            ).sort_values()
            dx = pd.Series(dx.length, index=dx).sort_index()
            # Divide by total in each column and each row's width
            agg = agg.divide(N, level="y").divide(dx, level="x")

        elif hasattr(axnorm, "__iter__"):
            # CRITICAL UNDOCUMENTED FEATURE: Tuple normalization (kind, function)
            # This code path implements custom aggregation-based normalization
            # WARNING: UNTESTED and may not integrate with other features
            try:
                kind, fcn = axnorm
            except (ValueError, TypeError) as e:
                raise ValueError(
                    f"Tuple axnorm must be (kind, function), got {axnorm}"
                ) from e

            # Apply column-wise or row-wise normalization with custom function
            if kind == "c":
                # Column normalization: divide each column by its aggregated value
                # Example: ('c', 'mean') divides each column by its mean
                normalizer = agg.agg(fcn, level="x")  # Aggregate across y for each x
                agg = agg.divide(normalizer, level="x")
            elif kind == "r":
                # Row normalization: divide each row by its aggregated value
                # Example: ('r', 'std') divides each row by its standard deviation
                normalizer = agg.agg(fcn, level="y")  # Aggregate across x for each y
                agg = agg.divide(normalizer, level="y")
            else:
                valid_kinds = {"c", "r"}
                raise ValueError(
                    f"Invalid tuple axnorm kind '{kind}'. "
                    f"Must be one of {sorted(valid_kinds)} for (kind, function) format. "
                    f"Got tuple {axnorm}"
                )
        else:
            # Provide comprehensive error message for invalid axnorm values
            valid_strings = {"c", "r", "t", "d", "cd", "rd"}
            raise ValueError(
                f"Unrecognized axnorm value: {axnorm} (type: {type(axnorm).__name__}). "
                f"\n\nValid options:"
                f"\n  String methods: {sorted(valid_strings)}"
                f"\n  Tuple methods: (kind, function) where kind in {{'c', 'r'}}"
                f"\n  None: No normalization"
                f"\n\nExamples:"
                f"\n  axnorm='d'           # Density normalization"
                f"\n  axnorm=('c', 'mean') # Column mean normalization (UNTESTED)"
                f"\n  axnorm=None          # No normalization"
            )

        return agg

    def agg(self, **kwargs):
        """Aggregate data with normalization and amplitude limiting.

        Performs the complete aggregation pipeline:
        1. Base aggregation (from parent class)
        2. Axis normalization (according to axnorm setting)
        3. Reindexing to fill missing bins
        4. Amplitude limiting (if alim is set)

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to parent agg method

        Returns
        -------
        pandas.Series
            Fully processed aggregated data ready for plotting
        """
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
        """Create colorbar with appropriate tick spacing.

        Automatically sets tick spacing for normalized plots:
        - Column/row normalized plots use MultipleLocator(0.1)
        - Other normalizations use default matplotlib ticking

        Parameters
        ----------
        mappable : matplotlib.cm.ScalarMappable
            The mappable object for the colorbar
        **kwargs
            Additional keyword arguments passed to parent _make_cbar method

        Returns
        -------
        matplotlib.colorbar.Colorbar
            The created colorbar object
        """
        ticks = kwargs.pop(
            "ticks",
            mpl.ticker.MultipleLocator(0.1) if self.axnorm in ("c", "r") else None,
        )
        return super()._make_cbar(mappable, ticks=ticks, **kwargs)

    def _limit_color_norm(self, norm):
        """Apply automatic color normalization limits.

        For most normalization types, limits the color scale to the 1st and 99th
        percentiles to avoid outliers dominating the color mapping. Column and row
        normalized plots are exempt from this limiting.

        Parameters
        ----------
        norm : matplotlib.colors.Normalize
            Color normalization object to modify in-place

        Returns
        -------
        None
            Color normalization limits are skipped for 'c' and 'r' axnorm
        """
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
            # Alpha blending algorithm for uncertainty visualization
            # Must draw to initialize `facecolor`s before accessing them
            plt.draw()
            # Remove `pc` from axis so we can redraw with std
            #             pc.remove()

            # Get current face colors (RGBA) and modify alpha channel
            colors = pc.get_facecolors()  # Shape: (n_faces, 4) RGBA array
            colors[:, 3] = alpha  # Set alpha channel (index 3) to computed values
            pc.set_facecolor(colors)  # Update colors with new transparency
        #             ax.add_collection(pc)

        elif alpha_fcn is not None:
            self.logger.warning("Ignoring `alpha_fcn` because plotting counts")

        return ax, cbar_or_mappable

    def get_border(self):
        r"""Get the top and bottom edges of the 2D histogram.

        Determines the boundary of the data distribution by finding the
        highest and lowest y-values that contain data for each x-column.
        This is particularly useful for solar wind parameter studies where
        you need to identify the envelope of the data distribution.

        The method works by:
        1. Aggregating data into 2D histogram bins
        2. For each x-column, finding the first and last y-bins with data
        3. Recording both the bin coordinates and z-values at these edges

        Returns
        -------
        border : namedtuple
            Named tuple with 'top' and 'bottom' fields, each containing
            a pandas.Series with:

            - Index: MultiIndex with ('y', 'x') levels representing bin coordinates
            - Values: z-values (counts or aggregated values) at the border
            - top: Highest y-value with data for each x-bin
            - bottom: Lowest y-value with data for each x-bin

        Notes
        -----
        The returned Series can be used with plot_edges() to visualize the
        boundary of the data distribution. This is commonly used in plasma
        physics to show the envelope of parameter correlations.

        The border detection algorithm skips empty bins and only considers
        bins with valid (non-NaN) aggregated values.

        Examples
        --------
        >>> h2d = Hist2D(vx, vy, density)
        >>> border = h2d.get_border()
        >>> print(f"Top edge has {len(border.top)} points")
        >>> print(f"Bottom edge has {len(border.bottom)} points")
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
        """Plot a single edge (top or bottom boundary) of the 2D histogram.

        This method handles the plotting of individual boundary lines from
        the get_border() method, with optional smoothing and coordinate
        transformations for log-scaled data.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            The axes object on which to plot the edge
        edge : pandas.Series
            Edge data from get_border() with MultiIndex ('y', 'x')
        smooth : bool, optional
            If True, apply Savitzky-Golay filtering for smooth curves.
            Default is False.
        sg_kwargs : dict, optional
            Keyword arguments passed to scipy.signal.savgol_filter.
            Defaults include window_length (10% of data points, minimum odd)
            and polyorder=3.
        xlim : tuple, optional
            (xmin, xmax) limits for plotting. None values are ignored.
        ylim : tuple, optional
            (ymin, ymax) limits for plotting. None values are ignored.
        **kwargs
            Additional arguments passed to ax.plot()

        Returns
        -------
        list
            Line2D objects returned by ax.plot()

        Notes
        -----
        The method automatically handles coordinate conversion for log-scaled
        axes, converting from internal log10 representation back to linear
        coordinates for plotting.

        Smoothing is particularly useful for noisy boundaries in sparse data
        regions. The Savitzky-Golay filter preserves the overall shape while
        reducing high-frequency noise.

        Data filtering based on xlim and ylim is applied after coordinate
        conversion, ensuring limits are specified in the final plotting
        coordinate system.
        """
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
        """Plot the top and bottom edges of the 2D histogram boundary.

        Visualizes the envelope of the data distribution by plotting both
        the upper and lower boundaries identified by get_border(). This is
        commonly used in solar wind studies to show the range of parameter
        correlations.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            Axis on which to plot the edges
        smooth : bool, optional
            If True, apply Savitzky-Golay filter to smooth the boundary curves.
            Default is True. Smoothing reduces noise in sparse data regions
            while preserving the overall envelope shape.
        sg_kwargs : dict, optional
            Keyword arguments passed to Savitzky-Golay filter. Supported options:

            - 'window_length' : int, default 10% of data points (must be odd)
            - 'polyorder' : int, default 3

            Additional scipy.signal.savgol_filter parameters are also supported.
        **kwargs
            Keyword arguments passed to ax.plot() for line styling.
            Common options include 'color', 'linestyle', 'linewidth', 'label'.

        Returns
        -------
        tuple
            (etop, ebottom) - Line2D objects for the top and bottom edges

        Notes
        -----
        Both edges are plotted with the same styling parameters, making it
        easy to create consistent boundary visualizations. The default color
        is 'cyan' if not specified in kwargs.

        The smoothing algorithm automatically adjusts the window length to
        ensure it's odd (required by Savitzky-Golay filter) and appropriate
        for the data density.

        Examples
        --------
        >>> fig, ax = plt.subplots()
        >>> h2d.make_plot(ax=ax)
        >>> h2d.plot_edges(ax, color='red', linewidth=2, label='Data envelope')
        >>> ax.legend()
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
        """Determine appropriate contour levels based on normalization method.

        Automatically selects sensible contour levels based on the current
        axnorm setting if no levels are explicitly provided. This ensures
        consistent and meaningful contour visualizations across different
        normalization schemes.

        Parameters
        ----------
        levels : array-like or None
            Explicit contour levels. If None, automatic selection is applied.

        Returns
        -------
        array-like or None
            Contour levels appropriate for the current normalization method
        """
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
        """Validate and set defaults for contour plotting keyword arguments.

        Ensures that all keyword argument dictionaries are properly initialized
        and sets appropriate defaults for contour plot customization.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            Target axes for the contour plot
        clabel_kwargs : dict or None
            Contour label formatting arguments
        edges_kwargs : dict or None
            Edge plotting arguments
        cbar_kwargs : dict or None
            Colorbar creation arguments

        Returns
        -------
        tuple
            (clabel_kwargs, edges_kwargs, cbar_kwargs) with defaults applied
        """
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
        """Generate contour plot visualization of 2D histogram data.

        Creates publication-quality contour plots suitable for solar wind
        parameter correlation analysis. Supports both line contours and
        filled contours with automatic level selection based on normalization.

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional
            Target axes for plotting. If None, creates new figure and axes.
        label_levels : bool, optional
            If True, add numeric labels to contour lines. Default is True.
        cbar : bool, optional
            If True, add colorbar to the plot. Default is True.
        limit_color_norm : bool, optional
            If True, limit color range to 1st and 99th percentiles to reduce
            outlier influence. Default is False.
        cbar_kwargs : dict, optional
            Keyword arguments passed to colorbar creation.
        fcn : callable, optional
            Aggregation function for binned data. If None, uses default
            aggregation from the agg() method.
        plot_edges : bool, optional
            If True, overlay the data boundary edges. Default is False.
        edges_kwargs : dict, optional
            Keyword arguments passed to plot_edges() method.
        clabel_kwargs : dict, optional
            Keyword arguments for contour label formatting:

            - 'inline' : bool, whether labels are inline (default True)
            - 'inline_spacing' : int, label spacing (default -3)
            - 'fmt' : str, label format string (default '%s')
        skip_max_clbl : bool, optional
            If True, skip labeling the highest contour level to avoid
            cluttering when the maximum is a small region. Default is True.
        use_contourf : bool, optional
            If True, create filled contours (contourf). Otherwise, create
            line contours (contour). Default is False.
        gaussian_filter_std : int, optional
            Standard deviation for Gaussian smoothing filter. If > 0, applies
            smoothing to reduce noise in sparse data regions. Default is 0.
        gaussian_filter_kwargs : dict, optional
            Additional parameters for scipy.ndimage.gaussian_filter.
        **kwargs
            Additional arguments passed to matplotlib's contour/contourf:

            - 'levels' : array-like or int, contour levels
            - 'cmap' : colormap name or object
            - 'norm' : color normalization object
            - 'linestyles' : line styles for contours
            - 'linewidths' : line widths for contours

        Returns
        -------
        tuple
            (ax, labels, cbar_or_mappable, contour_set) where:

            - ax : the axes object
            - labels : list of contour label objects (None if label_levels=False)
            - cbar_or_mappable : colorbar object or contour set
            - contour_set : matplotlib QuadContourSet object

        Notes
        -----
        **Automatic Level Selection**:
        The method automatically selects appropriate contour levels based on
        the normalization method:

        - 't' (total): [0.01, 0.1, 0.3, 0.7, 0.99] - fractional levels
        - 'c', 'r' (column/row): [0.0, 0.1, ..., 1.0] - normalized levels
        - 'd' (density): [3e-5, 1e-4, 3e-4, 1e-3, 1.7e-3, 2.3e-3] - density levels
        - 'cd', 'rd' (conditional density): matplotlib default levels

        **Coordinate Handling**:
        Automatically converts log-scaled internal coordinates back to linear
        coordinates for proper matplotlib rendering.

        **Smoothing Algorithm**:
        When gaussian_filter_std > 0, applies 2D Gaussian smoothing to the
        aggregated data before contouring. This is useful for:

        - Reducing noise in sparse data regions
        - Creating smoother contours for publication figures
        - Highlighting main distribution features

        **Performance Considerations**:
        - Large datasets: Consider using gaussian filtering for smoother results
        - Dense grids: May benefit from selective level specification
        - Log-scaled data: Automatic coordinate conversion handled internally

        Examples
        --------
        Basic contour plot:

        >>> h2d = Hist2D(vx, vy, axnorm='d')
        >>> ax, labels, cbar, cs = h2d.plot_contours()

        Custom levels with smoothing:

        >>> levels = [0.1, 0.3, 0.5, 0.7, 0.9]
        >>> ax, labels, cbar, cs = h2d.plot_contours(
        ...     levels=levels, gaussian_filter_std=1.0, use_contourf=True
        ... )

        With boundary overlay:

        >>> ax, labels, cbar, cs = h2d.plot_contours(
        ...     plot_edges=True, edges_kwargs={'color': 'red', 'linewidth': 2}
        ... )
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
        """Project 2D histogram data onto 1D marginal distribution.

        Creates a 1D histogram by projecting the 2D data onto one of the axes.
        This is useful for examining marginal distributions and is used internally
        by make_joint_h2_h1_plot() for creating marginal plots.

        The projection can either include all original data points or only those
        that fall within the plotted region of the 2D histogram.

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
        """Create a joint plot with 2D histogram and marginal 1D histograms.

        Generates a publication-quality multi-panel figure combining the main
        2D histogram with marginal distributions along both axes. This visualization
        is particularly valuable in plasma physics for understanding both the
        joint distribution and individual parameter distributions simultaneously.

        The layout consists of:
        - Central panel: 2D histogram (largest panel)
        - Top panel: X-axis marginal distribution
        - Right panel: Y-axis marginal distribution (rotated)
        - Bottom panel: Horizontal colorbar

        Parameters
        ----------
        project_counts : bool, optional
            If True, marginal histograms show count distributions.
            If False, marginal histograms show the joint distribution projected
            onto each axis. Default is True.
        kwargs_1d : dict, optional
            Keyword arguments passed to the 1D histogram plotting methods.
            Common options include styling parameters for marginal plots.
        fig_axes : tuple, optional
            Pre-existing (figure, axes) tuple. Currently not implemented
            due to complexity of subplot layout management.
        **kwargs
            Keyword arguments passed to the main 2D histogram plot:

            - 'figsize' : tuple, figure size (default (5, 6))
            - 'height_ratios' : list, relative heights [top, main, spacer, cbar]
              (default [0.25, 1, 0.2, 0.1])
            - 'width_ratios' : list, relative widths [main, right]
              (default [1, 0.25])
            - 'hspace' : float, height spacing between subplots (default 0)
            - 'wspace' : float, width spacing between subplots (default 0)
            - 'cbar_kwargs' : dict, colorbar customization parameters

        Returns
        -------
        tuple
            (hax, xax, yax, cbar) containing:

            - hax : main 2D histogram axes
            - xax : top marginal (x-projection) axes
            - yax : right marginal (y-projection) axes
            - cbar : colorbar object

        Notes
        -----
        **Layout Design**:
        The subplot layout uses matplotlib's GridSpec for precise control:

        - Grid: 4 rows × 2 columns
        - Row 0: X marginal histogram (spans column 0)
        - Row 1: Main 2D plot (col 0) + Y marginal (col 1)
        - Row 2: Spacer for visual separation
        - Row 3: Horizontal colorbar (spans column 0)

        **Axis Sharing**:
        - X marginal shares x-axis with main plot
        - Y marginal shares y-axis with main plot
        - Automatic tick management with label_outer()

        **Tick Optimization**:
        For linear scales, reduces tick density on main plot to prevent
        overcrowding when combined with marginal histograms.

        **Colorbar Integration**:
        Horizontal colorbar is positioned below the main plot with
        customizable spacing and orientation options.

        Examples
        --------
        Basic joint plot:

        >>> h2d = Hist2D(vx, vy, density, axnorm='d')
        >>> hax, xax, yax, cbar = h2d.make_joint_h2_h1_plot()
        >>> plt.tight_layout()

        Custom layout with styling:

        >>> hax, xax, yax, cbar = h2d.make_joint_h2_h1_plot(
        ...     figsize=(8, 8),
        ...     height_ratios=[0.3, 1, 0.1, 0.15],
        ...     kwargs_1d={'alpha': 0.7, 'color': 'blue'}
        ... )

        Focus on joint distribution:

        >>> hax, xax, yax, cbar = h2d.make_joint_h2_h1_plot(
        ...     project_counts=False,  # Show joint projections
        ...     cbar_kwargs={'orientation': 'horizontal', 'shrink': 0.8}
        ... )

        See Also
        --------
        project_1d : Method used to generate marginal histograms
        make_plot : Method used for the main 2D histogram
        """
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
        r"""Identify data points above a specified contour level.

        Determines which data points fall within histogram bins that have
        aggregated values above the specified threshold. This is particularly
        useful for selecting high-density regions or identifying outliers
        in solar wind parameter studies.

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
        r"""Extract data points within variable y-ranges across x-values.

        Selects data points that fall within specified y-ranges that can vary
        as a function of x. This is useful for extracting data along curved
        boundaries or within envelope functions derived from the histogram
        analysis.

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
