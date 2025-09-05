#!/usr/bin/env python
r"""One-dimensional histogram plotting utilities for solar wind analysis.

This module provides the Hist1D class for creating publication-quality histograms
from solar wind measurements. Key features include:

Statistical Analysis:
- Probability density functions with proper normalization
- Cumulative distribution function construction
- Multi-function aggregation (mean, median, std) within bins
- Advanced data selection across parameter ranges

Algorithmic Features:
- Logarithmic binning with variable bin width handling
- Density normalization accounting for log-space transformations
- Gaussian smoothing for noise reduction
- Uncertainty visualization via error bars or confidence bands

Solar Wind Applications:
- Parameter distribution analysis (velocity, density, temperature)
- Multi-parameter correlation studies
- Statistical comparison with theoretical models
- Event detection and classification

The histogram algorithms are optimized for:
- Parameters spanning multiple orders of magnitude
- Large datasets with memory-efficient processing
- Integration with matplotlib for publication figures
- Compatibility with pandas MultiIndex data structures
"""

import pdb  # noqa: F401

import numpy as np
import pandas as pd
import matplotlib as mpl

from types import FunctionType
from matplotlib import pyplot as plt

from . import base
from . import labels as labels_module
from .agg_plot import AggPlot

# import os
# import psutil


# def log_mem_usage():
#    usage = psutil.Process(os.getpid()).memory_info()
#    usage = "\n".join(
#        ["{} {:.3f} GB".format(k, v * 1e-9) for k, v in usage._asdict().items()]
#    )
#    logging.getLogger("main").warning("Memory usage\n%s", usage)


class Hist1D(AggPlot):
    """One-dimensional histogram with statistical analysis capabilities.

    Creates histograms from solar wind measurements with support for logarithmic
    scaling, density normalization, and cumulative distribution functions.
    Extends AggPlot to provide specialized 1D aggregation and visualization.

    This class is optimized for solar wind physics analysis, handling parameters
    that span multiple orders of magnitude (density, temperature, magnetic field)
    and providing statistical tools for distribution analysis.

    Parameters
    ----------
    x : pd.Series
        Primary measurement data for histogram binning.
    y : pd.Series or None, optional
        Secondary data for aggregation. If None, creates count histogram.
    logx : bool, optional
        Enable logarithmic binning and scaling for x-axis.
    axnorm : {'d', 't', None}, optional
        Normalization mode: 'd' for density, 't' for total, None for raw counts.
    clip_data : bool, optional
        Remove extreme outliers (0.1% and 99.9% percentiles) before processing.
    nbins : int or array-like, optional
        Number of bins or explicit bin edges for histogram construction.
    bin_precision : int, optional
        Decimal precision for bin edge calculations.

    Attributes
    ----------
    _gb_axes : tuple
        Groupby axes specification, always ('x',) for 1D histograms.
    path : pathlib.Path
        File system path for saving plots and cached results.
    axnorm : str or None
        Current normalization mode applied to histogram values.
    log : object
        Logarithmic scaling configuration for x and y axes.

    Methods
    -------
    set_data(x, y, clip)
        Configure histogram data with optional transformations.
    agg(**kwargs)
        Aggregate data into histogram bins with normalization.
    construct_cdf(only_plotted=True)
        Generate cumulative distribution function from histogram data.
    take_data_in_yrange_across_x(ranges_by_x, get_x_bounds, get_y_bounds)
        Advanced data selection within variable y-ranges across x-intervals.
    make_plot(ax=None, **kwargs)
        Create matplotlib histogram visualization with error handling.
    _axis_normalizer(agg)
        Apply density or total normalization to aggregated data.

    Examples
    --------
    >>> # Basic count histogram of solar wind velocity
    >>> hist = Hist1D(velocity_data, nbins=50)
    >>> ax, plot_obj = hist.make_plot()

    >>> # Density-normalized temperature distribution (log scale)
    >>> temp_hist = Hist1D(temperature_data, logx=True, axnorm='d')
    >>> cdf = temp_hist.construct_cdf()

    >>> # Aggregated proton density in velocity bins
    >>> n_v_hist = Hist1D(velocity_data, y=density_data, nbins=30)
    >>> ax, plot_obj = n_v_hist.make_plot(fcn='mean')

    Notes
    -----
    The class handles several specialized requirements for solar wind analysis:
    - Logarithmic scaling with proper density normalization
    - Statistical aggregation (mean, median, std) within bins
    - CDF construction for distribution comparison
    - Data selection for conditional probability analysis
    - Integration with matplotlib for publication-quality plots
    """

    def __init__(
        self,
        x,
        y=None,
        logx=False,
        axnorm=None,
        clip_data=False,
        nbins=101,
        bin_precision=None,
    ):
        """Create a one-dimensional histogram.

        Parameters
        ----------
        x : pandas.Series
            Data from which to create bins.
        y : pandas.Series or None, optional
            Values to aggregate in bins of ``x``. If ``None``, counts of
            ``x`` are used.
        logx : bool, optional
            If ``True``, compute bins in logarithmic space.
        axnorm : {"t", "d", None}, optional
            Normalisation applied to the histogram. ``"t"`` uses total
            counts and ``"d"`` yields a density.
        clip_data : bool, optional
            Remove extreme values at the 0.001 and 0.999 percentiles before
            binning or aggregation.
        nbins : int or array-like, optional
            Binning strategy passed to :func:`numpy.histogram_bin_edges` or
            :func:`pandas.cut` depending on the input type.
        bin_precision : int, optional
            Precision for decimal bin edges.
        """
        super(Hist1D, self).__init__()
        self.set_log(x=logx)
        self.set_axnorm(axnorm)
        self.set_data(x, y, clip_data)
        self.set_labels(x="x", y=labels_module.Count(norm=axnorm) if y is None else "y")
        self.calc_bins_intervals(nbins=nbins, precision=bin_precision)
        self.make_cut()
        self.set_clim(None, None)
        self.set_alim(None, None)

    @property
    def _gb_axes(self):
        return ("x",)

    def set_path(self, new, add_scale=True):
        path, x, y, z, scale_info = super(Hist1D, self).set_path(new, add_scale)

        if new == "auto":
            path = path / x / y

        else:
            assert x is None
            assert y is None

        if add_scale:
            assert scale_info is not None
            scale_info = scale_info[0]
            path = path / scale_info

        self._path = path

    set_path.__doc__ = base.Base.set_path.__doc__

    def set_data(self, x, y, clip):
        """Set histogram data with optional logarithmic transformation.

        Prepares data for histogram binning by applying logarithmic
        transformation if configured and handling default y-values for
        count histograms.

        Parameters
        ----------
        x : pd.Series
            Independent variable data for histogram binning.
        y : pd.Series or None
            Dependent variable data for aggregation. If None, creates
            count histogram with unit values.
        clip : bool
            Flag indicating whether to apply data clipping at extremes.
        """
        # Apply logarithmic transformation to x-data if configured
        # Use absolute values to handle negative values in log space
        data = pd.DataFrame({"x": np.log10(np.abs(x)) if self.log.x else x})

        # For count histograms, create unit y-values if none provided
        if y is None:
            y = pd.Series(1, index=x.index)
        data.loc[:, "y"] = y

        # Store processed data and clipping configuration
        self._data = data
        self._clip = clip

    def set_axnorm(self, new):
        """Configure histogram normalization method.

        Sets the normalization mode for histogram display and analysis.
        Affects how bin values are scaled for visualization and statistical
        interpretation.

        Parameters
        ----------
        new : {'d', 't', None}
            Normalization method to apply:
            - 'd': Density normalization (probability density function)
              Creates histogram where total area equals 1
            - 't': Total normalization (peak normalization)
              Scales histogram so maximum value equals 1
            - None: No normalization (raw counts or aggregated values)

        Notes
        -----
        Normalization Methods:

        ====== ================================================================
         Mode                           Description
        ====== ================================================================
         'd'    **Density normalization**: bin_value = count/(bin_width × N)
                Creates probability density function with area = 1
                Accounts for variable bin widths in logarithmic scaling
         't'    **Total normalization**: bin_value = count/max_count
                Peak-normalized histogram with maximum value = 1
                Useful for comparing distribution shapes
         None   **Raw values**: No scaling applied to aggregated data
                Shows actual counts, means, or other aggregated statistics
        ====== ================================================================

        The density normalization is particularly important for logarithmic
        histograms where bin widths vary significantly. For log-scaled data,
        the algorithm converts bin widths back to linear space before
        calculating densities.

        Examples
        --------
        >>> hist = Hist1D(velocity_data, logx=True)
        >>> hist.set_axnorm('d')  # Probability density function
        >>> hist.set_axnorm('t')  # Peak-normalized histogram
        >>> hist.set_axnorm(None) # Raw count histogram
        """
        if new is not None:
            new = new.lower()[0]
            assert new == "d"

        ylbl = self.labels.y
        if isinstance(ylbl, labels_module.Count):
            ylbl.set_axnorm(new)
            ylbl.build_label()

        self._axnorm = new

    def construct_cdf(self, only_plotted=True):
        """Construct cumulative distribution function from histogram data.

        Converts binned histogram data into a cumulative distribution function
        suitable for statistical analysis and probability plotting. Handles
        logarithmic scaling appropriately by back-transforming to linear space.

        Parameters
        ----------
        only_plotted : bool, optional
            If True (default), only include data points that are within the
            current plot limits and would be visible. If False, include all
            available data regardless of plot constraints.

        Returns
        -------
        cdf : pd.DataFrame
            DataFrame with columns:
            - 'x': Original measurement values (back-transformed from log space if applicable)
            - 'position': Normalized cumulative probability [0, 1]

            To plot the CDF:

            >>> cdf = hist.construct_cdf()
            >>> cdf.plot(x='x', y='position')

        Raises
        ------
        ValueError
            If the histogram contains aggregated data (non-uniform y values).
            CDF construction requires raw count data only.

        Notes
        -----
        The CDF construction algorithm:
        1. Validates that data represents counts (y-values are uniform)
        2. Filters data based on plot limits if requested
        3. Sorts x-values in ascending order
        4. Back-transforms from log space if logarithmic scaling is active
        5. Calculates normalized positions as rank/max_rank

        For solar wind physics, CDFs are useful for:
        - Comparing observed distributions to theoretical models
        - Quantifying parameter variability and extreme events
        - Statistical testing (e.g., Kolmogorov-Smirnov tests)
        """
        data = self.data
        # Validate data is histogram counts (uniform y-values indicate count data)
        if not data.loc[:, "y"].unique().size <= 2:
            raise ValueError("Only able to convert data to a cdf if it is a histogram.")

        # Create boolean mask for valid data points (non-NaN x-values)
        tk = self.cut.loc[:, "x"].notna()
        if only_plotted:
            # Further restrict to data within current plot limits
            tk = tk & self.get_plotted_data_boolean_series()

        # Extract x-values for CDF construction
        x = data.loc[tk, "x"]
        # Sort values to create monotonic CDF
        cdf = x.sort_values().reset_index(drop=True)

        # Back-transform from log space if logarithmic scaling is active
        if self.log.x:
            cdf = 10.0**cdf

        # Convert to DataFrame and calculate normalized positions
        cdf = cdf.to_frame()
        # Position = rank / max_rank gives cumulative probability [0, 1]
        cdf.loc[:, "position"] = cdf.index / cdf.index.max()

        return cdf

    def _axis_normalizer(self, agg):
        """Apply normalization to aggregated histogram data.

        Performs density or total normalization on histogram values according
        to the specified normalization mode. Handles logarithmic scaling
        correctly for density calculations by accounting for variable bin widths.

        Parameters
        ----------
        agg : pd.Series
            Aggregated histogram data with interval index representing bins.
            Values are typically counts or other aggregated statistics.

        Returns
        -------
        agg : pd.Series
            Normalized histogram data with same index structure.

        Notes
        -----
        Normalization modes:

        - None: No normalization applied, returns raw aggregated values
        - 'd' (density): Creates probability density function where:
          * Total area under histogram equals 1
          * Each bin value = count / (bin_width * total_count)
          * For log-scaled data: bin_width = 10^(log_right) - 10^(log_left)
        - 't' (total): Normalizes to maximum value (peak normalization)
          * Each bin value = count / max_count

        The density normalization algorithm:
        1. Extract bin widths from IntervalIndex
        2. Transform bin widths from log space if logarithmic scaling active
        3. Calculate density = count / (bin_width * total_counts)
        4. Ensures proper probability density function properties

        This method is designed as an instance method (not static) to access
        self.log for proper density calculations, while being reusable by
        other histogram classes like OrbitHist2D.
        """

        axnorm = self.axnorm
        if axnorm is None:
            # No normalization - return raw aggregated values
            pass
        elif axnorm == "d":
            # Density normalization: create probability density function
            # Total area under histogram will equal 1
            n = agg.sum()  # Total count across all bins
            # Extract bin widths from IntervalIndex
            dx = pd.Series(pd.IntervalIndex(agg.index).length, index=agg.index)
            if self.log.x:
                # For log-scaled data, convert bin widths back to linear space
                # Actual width = 10^(log_right) - 10^(log_left)
                dx = 10.0**dx
            # Density = count / (bin_width * total_count)
            agg = agg.divide(dx.multiply(n))

        elif axnorm == "t":
            # Total normalization: scale to maximum value (peak normalization)
            agg = agg.divide(agg.max())

        else:
            raise ValueError("Unrecognized axnorm: %s" % axnorm)

        return agg

    def agg(self, **kwargs):
        """Aggregate data with optional normalization.

        Performs histogram aggregation with validation for density normalization
        and applies axis normalization according to the configured mode.

        Parameters
        ----------
        **kwargs
            Passed to parent aggregation method. Key parameter is 'fcn'
            specifying the aggregation function.

        Returns
        -------
        agg : pd.Series
            Aggregated and normalized histogram data.

        Raises
        ------
        ValueError
            If density normalization is requested with non-count aggregation.
        """
        # Validate aggregation function compatibility with density normalization
        if self.axnorm == "d":
            fcn = kwargs.get("fcn", None)
            if (fcn != "count") & (fcn is not None):
                raise ValueError("Unable to calculate a PDF with non-count aggregation")

        # Perform base aggregation
        agg = super(Hist1D, self).agg(**kwargs)
        # Apply normalization (density, total, or none)
        agg = self._axis_normalizer(agg)
        # Reindex to handle any missing bins
        agg = self._agg_reindexer(agg)

        return agg

    def set_labels(self, **kwargs):
        if "z" in kwargs:
            raise ValueError(r"{} doesn't have a z-label".format(self))

        y = kwargs.pop("y", self.labels.y)
        if isinstance(y, labels_module.Count):
            y.set_axnorm(self.axnorm)
            y.build_label()

        super(Hist1D, self).set_labels(y=y, **kwargs)

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
            If not None and gaussian_filter_std > 0, passed to :py:meth:`scipy.ndimage.gaussian_filter`
        plot_window: bool
            Requires two functions passed to `fcn`. Instead of error bars, plots the uncertainty
            window as a semi-transparent band.
        plot_window_edges: bool
            If True, plot solid lines at the window boundaries.
        kwargs:
            Passed directly to `ax.plot`.
        """
        agg = self.agg(fcn=fcn)
        x = pd.IntervalIndex(agg.index).mid

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

        # Apply Gaussian smoothing if requested (useful for noisy data)
        if gaussian_filter_std:
            from scipy.ndimage import gaussian_filter

            if gaussian_filter_kwargs is None:
                gaussian_filter_kwargs = dict()

            # Smooth histogram values to reduce statistical noise
            y = gaussian_filter(y, gaussian_filter_std, **gaussian_filter_kwargs)

        drawstyle = kwargs.pop("drawstyle", "steps-mid")

        # Handle axis transposition for adjacent plots (e.g., marginal histograms)
        if transpose_axes:
            x, y = y, x  # Swap independent/dependent variables
            dx, dy = dy, dx  # Swap corresponding uncertainties

        # Extract window plotting parameters and normalize line kwargs
        window_kwargs = kwargs.pop("window_kwargs", dict())
        kwargs = mpl.cbook.normalize_kwargs(kwargs, mpl.lines.Line2D._alias_map)

        # Set up uncertainty window plotting (alternative to error bars)
        if plot_window:
            # Choose appropriate fill function based on axis orientation
            window_plotter = ax.fill_between
            if transpose_axes:
                window_plotter = ax.fill_betweenx

            color = kwargs.pop("color", None)
            ls = kwargs.pop("linestyle", "-")
            label = kwargs.pop("label", None)

            window_alpha = window_kwargs.pop("alpha", 0.15)
            window_color = window_kwargs.pop("color", color)
            window_linestyle = window_kwargs.pop("linestyle", ls)

            line = ax.plot(x, y, color=color, linestyle=ls, label=label, **kwargs)
            if plot_window_edges:
                ax.plot(
                    x,
                    y + dy,
                    color=window_color,
                    linestyle=window_linestyle,
                    **window_kwargs,
                )
                ax.plot(
                    x,
                    y - dy,
                    color=window_color,
                    linestyle=window_linestyle,
                    **window_kwargs,
                )

            # Create semi-transparent uncertainty band
            polycol = window_plotter(
                x,
                y - dy,  # Lower uncertainty bound
                y + dy,  # Upper uncertainty bound
                color=window_color,
                linestyle=window_linestyle,
                alpha=window_alpha,  # Transparency for uncertainty visualization
                **window_kwargs,
            )

            # Return both line and polygon objects for legend handling
            out = (line, polycol)

        else:
            # Standard error bar plotting for uncertainty visualization
            out = ax.errorbar(x, y, xerr=dx, yerr=dy, drawstyle=drawstyle, **kwargs)

        # Apply axis formatting (labels, scales, limits)
        self._format_axis(ax, transpose_axes=transpose_axes)

        return ax, out

    def take_data_in_yrange_across_x(
        self,
        ranges_by_x,
        get_x_bounds,
        get_y_bounds,
    ):
        """Select data points within specified y-ranges for each x-interval.

        Advanced data selection method that filters raw data points based on
        variable y-value ranges across different x-intervals. Commonly used
        for extracting specific parameter regimes or statistical outliers
        from solar wind measurements.

        Parameters
        ----------
        ranges_by_x : pd.DataFrame or iterable
            Data structure where index represents x-interval identifiers
            and values contain information for determining y-range bounds.
            Must have same interval index as histogram aggregation.

        get_x_bounds : callable
            Function that extracts x-interval boundaries.

            Signature: get_x_bounds(x_key, expected_logx=bool) -> (left, right)

            - x_key: Single index value from ranges_by_x
            - expected_logx: Whether x-coordinates are in log space
            - Returns: Tuple of (left_bound, right_bound) for x-interval

        get_y_bounds : callable
            Function that extracts y-range boundaries.

            Signature: get_y_bounds(y_values, expected_logy=bool) -> (bottom, top)

            - y_values: Row data from ranges_by_x for current x-interval
            - expected_logy: Whether y-coordinates are in log space
            - Returns: Tuple of (bottom_bound, top_bound) for y-range

        Returns
        -------
        taken : np.ndarray
            Sorted array of integer indices identifying data points that fall
            within the specified x-intervals and corresponding y-ranges.
            Can be used to index original data arrays.

        Notes
        -----
        Selection Algorithm:
        1. Validate that ranges_by_x index matches available histogram bins
        2. For each x-interval in ranges_by_x:
           - Extract x-bounds using get_x_bounds function
           - Extract y-bounds using get_y_bounds function
           - Apply coordinate transformations for logarithmic scaling
           - Select data points: left < x <= right AND bottom < y <= top
        3. Concatenate and sort all selected indices
        4. Return unique sorted index array

        Common Usage in Solar Wind Physics:
        - Extracting measurements during specific solar wind conditions
        - Filtering data by parameter correlations or thresholds
        - Selecting events within statistical confidence intervals
        - Creating conditional probability distributions

        Examples
        --------
        >>> # Select high-temperature protons in different velocity ranges
        >>> ranges = pd.DataFrame({'temp_min': [1e5, 2e5, 5e5]},
        ...                      index=velocity_bins)
        >>> def x_bounds(v_bin, expected_logx):
        ...     return v_bin.left, v_bin.right
        >>> def y_bounds(row, expected_logy):
        ...     return row['temp_min'], np.inf
        >>> indices = hist.take_data_in_yrange_across_x(
        ...     ranges, x_bounds, y_bounds)
        """

        # Validate that ranges_by_x index matches available histogram bins
        available_x = self.agg().index
        assert not ranges_by_x.index.symmetric_difference(available_x).size

        # Get raw data and logarithmic scaling flags
        data = self.data
        logx = self.log.x  # Whether x-coordinates are in log space
        logy = self.log.y  # Whether y-coordinates are in log space

        taken = []  # Collect indices from each x-interval

        # Process each x-interval and its corresponding y-range
        for x, at_x in ranges_by_x.iterrows():
            # Extract interval boundaries using provided functions
            l, r = get_x_bounds(x, expected_logx=logx)  # left, right x-bounds
            b, t = get_y_bounds(at_x, expected_logy=logy)  # bottom, top y-bounds

            # Validate bounds are properly ordered
            assert l < r, f"Invalid x-bounds: left ({l}) >= right ({r})"
            assert b < t, f"Invalid y-bounds: bottom ({b}) >= top ({t})"

            # Create boolean masks for data selection
            # Use half-open intervals: left < x <= right, bottom < y <= top
            tkx = (l < data.x) & (data.x <= r)
            tky = (b < data.y) & (data.y <= t)
            tk = tkx & tky  # Combined x and y constraints

            # Extract indices of selected data points
            tk = tk.loc[tk].index
            taken.append(tk)

        # Combine all selected indices and sort for consistent ordering
        taken = np.sort(np.concatenate(taken))
        return taken
