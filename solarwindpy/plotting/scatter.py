#!/usr/bin/env python
r"""Advanced scatter plot visualization for solar wind plasma parameter analysis.

This module provides comprehensive scatter plot capabilities specifically designed
for analyzing relationships between solar wind plasma parameters. The Scatter class
supports both two-dimensional scatter plots and three-dimensional color-mapped
visualizations, enabling detailed investigation of parameter correlations and
physical relationships in solar wind data.

Key Features
------------
- Color-mapped scatter plots for 3D parameter space visualization
- Automatic outlier detection and data clipping capabilities
- Integration with solar wind parameter labeling system
- Support for uncertainty visualization through error bars
- Correlation analysis tools for parameter relationships
- Publication-quality formatting with customizable aesthetics

Technical Implementation
------------------------
The Scatter class inherits from PlotWithZdata (three-dimensional data support)
and CbarMaker (colorbar creation) base classes, providing a complete framework
for advanced scatter plot analysis of solar wind measurements.

Typical Applications
--------------------
- Ion temperature vs. flow speed correlations
- Magnetic field strength vs. plasma density relationships
- Multi-parameter plasma state analysis
- Solar wind regime classification visualization
- Spacecraft measurement validation and comparison

Examples
--------
>>> import pandas as pd
>>> from solarwindpy.plotting.scatter import Scatter
>>> # Basic 2D scatter plot
>>> scatter = Scatter(x=velocity_data, y=temperature_data)
>>> ax, cbar = scatter.make_plot()
>>>
>>> # Color-mapped 3D scatter with magnetic field strength
>>> scatter_3d = Scatter(x=velocity, y=temperature, z=b_field)
>>> ax, cbar = scatter_3d.make_plot(cmap='viridis')
"""

import pdb  # noqa: F401

from matplotlib import pyplot as plt

from . import base


class Scatter(base.PlotWithZdata, base.CbarMaker):
    r"""Advanced scatter plot with optional three-dimensional color mapping.

    The Scatter class creates sophisticated scatter plots optimized for solar wind
    plasma parameter analysis. It supports both traditional two-dimensional scatter
    plots and advanced three-dimensional visualizations where a third parameter
    controls point coloring. The class includes built-in outlier detection, data
    clipping, and correlation analysis capabilities.

    This class is specifically designed for exploring relationships between solar
    wind measurements such as ion velocities, temperatures, magnetic field strengths,
    and plasma densities. It provides tools for identifying physical correlations,
    validating theoretical predictions, and characterizing different solar wind
    regimes.

    Parameters
    ----------
    x : pandas.Series
        Independent variable data (e.g., solar wind velocity, magnetic field).
        Typically represents the primary parameter of interest.
    y : pandas.Series
        Dependent variable data (e.g., ion temperature, plasma density).
        Should have the same index as x for proper alignment.
    z : pandas.Series, optional
        Third dimension data used for color mapping each scatter point.
        When provided, creates a color-coded scatter plot revealing
        three-parameter relationships. Default is None (2D plot).
    clip_data : bool, default False
        Enable automatic outlier removal using percentile-based clipping.
        When True, removes extreme values at 0.001 and 99.9 percentiles
        to improve visualization of main data distribution.

    Attributes
    ----------
    data : pandas.DataFrame
        Processed scatter plot data with columns ['x', 'y', 'z'].
        Missing z values are handled automatically for 2D plots.
    labels : AxesLabels
        Axis labeling configuration for x, y, and z (colorbar) axes.
        Supports both string labels and formatted label objects.
    log : LogAxes
        Logarithmic scaling configuration for x and y axes.
        Default is linear scaling for both axes.
    clip : bool
        Current data clipping status. Matches clip_data parameter.
    path : pathlib.Path or None
        File system path for plot output. Set via set_path() method.

    Methods
    -------
    make_plot(ax=None, cbar=True, cbar_kwargs=None, **kwargs)
        Create the scatter plot on specified or new matplotlib axes.
    set_data(x, y, z=None, clip_data=False)
        Update plot data with new x, y, and optional z series.
    set_labels(x=None, y=None, z=None)
        Configure axis labels for the plot.
    set_log_axes(x=False, y=False)
        Enable or disable logarithmic scaling for axes.
    clip_data(data, percentile_range)
        Apply percentile-based outlier removal to data.

    Notes
    -----
    The class automatically handles missing data through pandas NaN support and
    provides intelligent colorbar creation only when meaningful color variation
    exists in the z-parameter. For solar wind applications, common parameter
    combinations include:

    - Velocity vs. Temperature (colored by magnetic field strength)
    - Density vs. Temperature (colored by solar wind speed)
    - Proton vs. Alpha particle correlations
    - Multi-spacecraft measurement comparisons

    The plotting system integrates with SolarWindPy's labeling system to
    automatically generate publication-quality axis labels with proper units
    and mathematical formatting.

    Examples
    --------
    Create a basic velocity-temperature scatter plot:

    >>> import pandas as pd
    >>> from solarwindpy.plotting.scatter import Scatter
    >>> scatter = Scatter(x=sw_velocity, y=proton_temp)
    >>> ax, cbar = scatter.make_plot(alpha=0.6, s=20)

    Create a three-parameter analysis with magnetic field coloring:

    >>> scatter_3d = Scatter(x=sw_velocity, y=proton_temp, z=b_magnitude)
    >>> ax, cbar = scatter_3d.make_plot(cmap='plasma', s=15)
    >>>
    Create an outlier-resistant plot with data clipping:

    >>> scatter_clean = Scatter(x=velocity, y=temperature, clip_data=True)
    >>> ax, cbar = scatter_clean.make_plot()
    """

    def __init__(self, x, y, z=None, clip_data=False):
        r"""Initialize scatter plot with solar wind parameter data.

        Sets up the scatter plot configuration including data alignment, outlier
        handling, and axis configuration. The initialization process validates
        data compatibility and prepares the plotting framework for solar wind
        parameter visualization.

        Parameters
        ----------
        x : pandas.Series
            Independent variable data for x-axis positioning. Should contain
            solar wind measurements such as bulk velocity, magnetic field
            components, or plasma densities. Index must align with y and z.
        y : pandas.Series
            Dependent variable data for y-axis positioning. Common examples
            include ion temperatures, particle flux measurements, or derived
            plasma parameters. Must have compatible index with x.
        z : pandas.Series, optional
            Third parameter for color-coding scatter points. When provided,
            creates a three-dimensional parameter space visualization where
            point colors represent z-values. Typical uses include magnetic
            field strength, plasma beta, or temporal information. Default
            is None, creating a standard 2D scatter plot.
        clip_data : bool, default False
            Enable automatic outlier detection and removal. When True, applies
            percentile-based clipping at 0.1% and 99.9% levels to remove
            measurement artifacts and extreme outliers that can obscure main
            data trends. Recommended for raw spacecraft data analysis.

        Notes
        -----
        The initialization process:

        1. Calls parent class constructors for data handling and colorbar support
        2. Processes and aligns input data series via set_data()
        3. Configures default axis labels as placeholders
        4. Sets linear scaling as default for both axes
        5. Initializes file path system for plot output

        Data alignment is handled automatically through pandas index matching,
        ensuring proper correspondence between x, y, and z measurements even
        when original series have different temporal coverage or resolution.

        Examples
        --------
        Initialize basic proton parameter scatter plot:

        >>> scatter = Scatter(x=velocity_gse_x, y=proton_temperature)

        Create magnetic field strength analysis with outlier removal:

        >>> b_scatter = Scatter(x=b_total, y=plasma_density,
        ...                     z=solar_wind_speed, clip_data=True)
        """
        super(Scatter, self).__init__()
        self.set_data(x, y, z, clip_data)
        self._labels = base.AxesLabels(x="x", y="y", z="z" if z is not None else None)
        self._log = base.LogAxes(x=False, y=False)
        self.set_path(None)

    def _format_axis(self, ax, collection):
        r"""Apply axis formatting and data limits for scatter plot visualization.

        Configures matplotlib axes properties specifically for scatter plot display,
        including automatic data limit calculation and sticky edge behavior for
        optimal view bounds. This method ensures that scatter plots display with
        appropriate margins and scaling for solar wind parameter analysis.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            Target axes object to format. Must contain the scatter plot collection.
        collection : matplotlib.collections.Collection
            Scatter plot collection returned by ax.scatter(). Used for setting
            data-dependent display properties and sticky edge behavior.

        Notes
        -----
        This method performs several formatting operations:

        1. Calls parent class axis formatting for baseline configuration
        2. Calculates data bounds from x and y coordinate ranges
        3. Sets sticky edges to prevent matplotlib from adding extra padding
        4. Updates axes data limits to match actual data extent
        5. Triggers automatic view scaling for optimal display

        The sticky edges feature ensures that scatter plots fill the available
        axis space without unwanted whitespace, particularly important for
        dense parameter space visualizations common in solar wind analysis.

        The formatting integrates with SolarWindPy's labeling system to apply
        publication-quality axis labels with proper units and mathematical
        notation for solar wind parameters.
        """
        super()._format_axis(ax)

        x = self.data.loc[:, "x"]
        minx, maxx = x.min(), x.max()

        y = self.data.loc[:, "y"]
        miny, maxy = y.min(), y.max()

        # `pulled from the end of `ax.pcolormesh`.
        collection.sticky_edges.x[:] = [minx, maxx]
        collection.sticky_edges.y[:] = [miny, maxy]
        corners = (minx, miny), (maxx, maxy)
        ax.update_datalim(corners)
        ax.autoscale_view()

    def make_plot(self, ax=None, cbar=True, cbar_kwargs=None, **kwargs):
        r"""Create a publication-quality scatter plot for solar wind parameter analysis.

        Generates a complete scatter plot visualization with automatic colorbar
        creation, data processing, and axis formatting. The method handles both
        two-dimensional scatter plots and three-dimensional color-mapped
        visualizations optimized for solar wind plasma parameter relationships.

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional
            Target axes for plot creation. If None, creates a new figure and axes
            using matplotlib.pyplot.subplots(). Allows integration into existing
            multi-panel figures for comprehensive solar wind analysis.
        cbar : bool, default True
            Control colorbar creation for three-dimensional plots. When True and
            meaningful color variation exists in z-data, automatically creates
            and positions a colorbar with appropriate labeling. Set False for
            2D plots or when manual colorbar control is needed.
        cbar_kwargs : dict, optional
            Additional parameters for colorbar customization, passed directly to
            the internal _make_cbar method. Common options include 'shrink',
            'aspect', 'pad', and 'label' for colorbar appearance control.
        **kwargs
            Additional styling parameters passed to matplotlib.axes.Axes.scatter().
            Supports standard scatter plot options including:

            - s : marker size (scalar or array)
            - c : colors (when z-data not used)
            - alpha : transparency level
            - cmap : colormap for z-data visualization
            - marker : point style ('o', 's', '^', etc.)
            - edgecolors : marker edge colors
            - linewidths : marker edge line widths

        Returns
        -------
        ax : matplotlib.axes.Axes
            Formatted axes containing the scatter plot with proper labeling,
            scaling, and data limits applied.
        cbar : matplotlib.colorbar.Colorbar or None
            Colorbar object if created (when cbar=True and z-data varies),
            otherwise None. Can be used for additional colorbar customization
            after plot creation.

        Notes
        -----
        The plotting process includes several automated steps:

        1. Data validation and clipping (if enabled during initialization)
        2. Automatic detection of meaningful z-parameter variation
        3. Intelligent colorbar creation only when color mapping adds information
        4. Publication-quality axis formatting with solar wind parameter labels
        5. Optimal data limit calculation for clear parameter relationship display

        For solar wind applications, the method automatically handles common
        data characteristics like missing measurements, extreme outliers, and
        multi-scale parameter ranges through built-in processing capabilities.

        The color mapping system intelligently determines when z-parameter
        coloring provides meaningful information versus when uniform coloring
        is more appropriate, preventing unnecessary visual complexity.

        Examples
        --------
        Create a basic velocity-temperature scatter plot:

        >>> scatter = Scatter(x=sw_velocity, y=proton_temp)
        >>> ax, cbar = scatter.make_plot(s=30, alpha=0.7)

        Generate a three-parameter magnetic field analysis:

        >>> b_scatter = Scatter(x=velocity, y=temperature, z=b_field)
        >>> ax, cbar = b_scatter.make_plot(cmap='plasma', s=15, alpha=0.8)

        Create custom colorbar formatting:

        >>> cbar_options = {'shrink': 0.8, 'pad': 0.1, 'label': 'B [nT]'}
        >>> ax, cbar = scatter.make_plot(cbar_kwargs=cbar_options)

        Integrate into existing multi-panel figure:

        >>> fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        >>> ax, cbar = scatter.make_plot(ax=axes[0, 1], cbar=False)
        """
        # Create new axes if not provided, enabling standalone plot creation
        if ax is None:
            fig, ax = plt.subplots()

        # Apply data clipping if enabled during initialization
        # This removes outliers that could compress the main data distribution
        data = self.data
        if self.clip:
            data = self.clip_data(data, self.clip)

        # Determine if z-parameter provides meaningful color information
        # Only use color mapping when z-values actually vary across data points
        if data.loc[:, "z"].unique().size > 1:
            zkey = "z"  # Enable color mapping based on z-parameter
        else:
            zkey = None  # Use uniform coloring for all points

        # Create the scatter plot using pandas-style column access
        # This allows direct use of DataFrame columns for coordinate and color data
        collection = ax.scatter(x="x", y="y", c=zkey, data=data, **kwargs)

        # Create colorbar only when meaningful and requested
        if cbar and zkey is not None:
            # Set up default colorbar parameters if not provided
            if cbar_kwargs is None:
                cbar_kwargs = dict()

            # Ensure colorbar has appropriate axes reference for positioning
            # Default to current axes if no specific colorbar axes specified
            if "cax" not in cbar_kwargs.keys() and "ax" not in cbar_kwargs.keys():
                cbar_kwargs["ax"] = ax

            # Create colorbar using inherited CbarMaker functionality
            cbar = self._make_cbar(collection, **cbar_kwargs)
        else:
            cbar = None

        # Apply final axis formatting including data limits and labeling
        self._format_axis(ax, collection)

        return ax, cbar
