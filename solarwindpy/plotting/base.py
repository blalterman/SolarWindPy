#!/usr/bin/env python
r"""Base classes and mixins for SolarWindPy plotting utilities.

This module provides the foundational architecture for all plotting functionality
in SolarWindPy through an abstract base class and specialized mixins. The design
follows the mixin pattern to enable flexible composition of plotting capabilities
while maintaining consistent interfaces and behavior across all plot types.

The module defines:

- Base: Abstract base class providing core plotting infrastructure
- DataLimFormatter: Mixin for automatic matplotlib data limit management
- CbarMaker: Mixin for standardized colorbar creation
- PlotWithZdata: Concrete base class for three-dimensional plotting

Named tuples provide structured storage for plot configuration:

- LogAxes: Boolean flags for logarithmic axis scaling
- AxesLabels: String labels for x, y, and z axes
- RangeLimits: Lower and upper bounds for data ranges

Concrete plot classes derive from combinations of these base classes and mixins
to implement specific visualizations like histograms, contour plots, and scatter
plots while sharing common functionality for axis management, labeling, and
file system integration.
"""

import pdb  # noqa: F401
import logging
import pandas as pd

from pathlib import Path
from collections import namedtuple
from abc import ABC, abstractmethod

LogAxes = namedtuple("LogAxes", "x,y", defaults=(False,))
"""Named tuple for axis logarithmic scaling configuration.

Parameters
----------
x : bool
    True if x-axis should use logarithmic scaling, False for linear.
y : bool
    True if y-axis should use logarithmic scaling, False for linear.

Notes
-----
Default values are False (linear scaling) for both axes.
"""

AxesLabels = namedtuple("AxesLabels", "x,y,z", defaults=(None,))
"""Named tuple for axis label storage and management.

Parameters
----------
x : str or None
    Label for the x-axis. None indicates no label should be applied.
y : str or None
    Label for the y-axis. None indicates no label should be applied.
z : str or None
    Label for the z-axis (typically used for colorbars). None indicates
    no label should be applied.

Notes
-----
Default values are None for all labels. Labels can be simple strings
or more complex objects with formatting attributes.
"""

RangeLimits = namedtuple("RangeLimits", "lower,upper", defaults=(None,))
"""Named tuple for data range boundary specification.

Parameters
----------
lower : float or None
    Lower boundary for data range. None indicates no lower bound.
upper : float or None
    Upper boundary for data range. None indicates no upper bound.

Notes
-----
Used for data clipping and axis limit management. Default values
are None (no limits applied).
"""


class Base(ABC):
    r"""Abstract base class for all plotting utilities in SolarWindPy.

    This abstract base class provides the foundational framework for all plotting
    classes in the SolarWindPy package. It defines the common interface for data
    handling, axis configuration, label management, and file path generation that
    all concrete plotting classes must implement.

    The Base class follows the mixin design pattern, providing core functionality
    that can be combined with specialized mixins like DataLimFormatter and
    CbarMaker to create complete plotting solutions.

    Attributes
    ----------
    _labels : AxesLabels
        Named tuple storing x, y, and z axis labels for the plot.
    _log : LogAxes
        Named tuple storing boolean flags for logarithmic scaling on x and y axes.
    _path : pathlib.Path
        File system path for saving the generated figure.
    _logger : logging.Logger
        Logger instance for debugging and status messages.
    _data : pandas.DataFrame
        Plot data storage (set by concrete implementations).
    _clip : bool
        Flag indicating whether data clipping is enabled.

    Methods
    -------
    set_data()
        Abstract method for setting plot data (must be implemented by subclasses).
    make_plot()
        Abstract method for creating the plot (must be implemented by subclasses).
    set_labels(**kwargs)
        Set or update axis labels with automatic path regeneration.
    set_log(x=None, y=None)
        Configure logarithmic scaling for x and/or y axes.
    set_path(new, add_scale=False)
        Generate file path for saving figures with optional scale information.
    _add_axis_labels(ax, transpose_axes=False)
        Apply stored labels to matplotlib axes.
    _set_axis_scale(ax, transpose_axes=False)
        Apply logarithmic scaling settings to matplotlib axes.
    _format_axis(ax, transpose_axes=False)
        Complete axis formatting including labels, scaling, and grid.

    Notes
    -----
    This class implements the Template Method pattern, where the general algorithm
    for plot creation is defined in the base class, but specific steps are
    implemented by concrete subclasses.

    The mixin architecture allows for flexible composition of plotting capabilities.
    For example, a 2D histogram might inherit from Base, DataLimFormatter, and
    CbarMaker to get data handling, axis limit management, and colorbar creation.

    Examples
    --------
    Concrete implementations typically follow this pattern:

    >>> class MyPlot(Base):
    ...     def __init__(self, data):
    ...         super().__init__()
    ...         self.set_data(data)
    ...
    ...     def set_data(self, data):
    ...         # Implementation specific to MyPlot
    ...         pass
    ...
    ...     def make_plot(self):
    ...         # Create the actual matplotlib plot
    ...         pass
    """

    @abstractmethod
    def __init__(self):
        self._init_logger()
        self._labels = AxesLabels(x="x", y="y")
        self._log = LogAxes(x=False)
        self.set_path("auto")

    def __str__(self):
        """Return string representation of the plot object.

        Returns
        -------
        str
            The class name of the plotting object.

        Examples
        --------
        >>> plot = SomeConcreteePlot()
        >>> str(plot)
        'SomeConcreteePlot'
        """
        return self.__class__.__name__

    @property
    def logger(self):
        return self._logger

    def _init_logger(self):
        """Initialize logger for the plotting class.

        Creates a logger instance with a name that includes both the module
        and class name for better debugging and log organization. The logger
        follows Python's hierarchical logging structure.

        Notes
        -----
        The logger name format is 'module.ClassName', which allows for
        fine-grained control over logging levels for different plot types.
        For example, 'solarwindpy.plotting.base.Hist2D'.
        """
        # return None
        logger = logging.getLogger("{}.{}".format(__name__, self.__class__.__name__))
        self._logger = logger

    #     # Old version that cuts at percentiles.
    #     @staticmethod
    #     def clip_data(data, clip):
    #         q0 = 0.0001
    #         q1 = 0.9999
    #         pct = data.quantile([q0, q1])
    #         lo = pct.loc[q0]
    #         up = pct.loc[q1]

    #         if isinstance(data, pd.Series):
    #             ax = 0
    #         elif isinstance(data, pd.DataFrame):
    #             ax = 1
    #         else:
    #             raise TypeError("Unexpected object %s" % type(data))

    #         if isinstance(clip, str) and clip.lower()[0] == "l":
    #             data = data.clip_lower(lo, axis=ax)
    #         elif isinstance(clip, str) and clip.lower()[0] == "u":
    #             data = data.clip_upper(up, axis=ax)
    #         else:
    #             data = data.clip(lo, up, axis=ax)
    #         return data

    #     # New version that uses binning to cut.
    #     #     @staticmethod
    #     #     def clip_data(data, bins, clip):
    #     #         q0 = 0.001
    #     #         q1 = 0.999
    #     #         pct = data.quantile([q0, q1])
    #     #         lo  = pct.loc[q0]
    #     #         up  = pct.loc[q1]
    #     #         lo = bins.iloc[0]
    #     #         up = bins.iloc[-1]
    #     #         if isinstance(clip, str) and clip.lower()[0] == "l":
    #     #             data = data.clip_lower(lo)
    #     #         elif isinstance(clip, str) and clip.lower()[0] == "u":
    #     #             data = data.clip_upper(up)
    #     #         else:
    #     #             data = data.clip(lo, up)
    #     #         return data

    @property
    def data(self):
        return self._data

    @property
    def clip(self):
        return self._clip

    @property
    def log(self):
        return self._log

    @property
    def labels(self):
        return self._labels

    @property
    def path(self):
        r"""Path for saving figure."""
        return self._path

    def set_log(self, x=None, y=None):
        if x is None:
            x = self.log.x
        if y is None:
            y = self.log.y

        log = LogAxes(bool(x), bool(y))
        self._log = log

    def set_labels(self, **kwargs):
        r"""Set or update x, y, or z labels. Any label not specified in kwargs.

        is propagated from `self.labels.<x, y, or z>`.
        """
        auto_update_path = kwargs.pop("auto_update_path", True)

        x = kwargs.pop("x", self.labels.x)
        y = kwargs.pop("y", self.labels.y)
        z = kwargs.pop("z", self.labels.z)

        if len(kwargs.keys()):
            extra = "\n".join(["{}: {}".format(k, v) for k, v in kwargs.items()])
            raise KeyError("Unexpected kwarg\n{}".format(extra))

        self._labels = AxesLabels(x, y, z)

        if auto_update_path:
            self.set_path("auto")

    @abstractmethod
    def set_path(self, new, add_scale=False):
        r"""Build the plot save path.

        Parameters
        ----------
        new: str or Path
            If str and == "auto", then build path from `self.labels`. Otherwise,
            assume parameter specifies the desired path and use `Path(new)`.
        add_scale: bool
            If True, add information about the axis scales to the end of the path.
        """
        # TODO: move "auto" methods here to iterate through `AxesLabels` named tuple
        #       and pull the strings for creating the path. Also check for each
        #       label's scale and add that information.

        if new == "auto":
            try:
                x = self.labels.x.path
            except AttributeError:
                x = self.labels.x
                if not (isinstance(x, str) and x != "None"):
                    x = "x"
                elif isinstance(x, str):
                    x = x.replace(" ", "-")

            try:
                y = self.labels.y.path
            except AttributeError:
                y = self.labels.y
                if not (isinstance(y, str) and y != "None"):
                    y = "y"
                elif isinstance(y, str):
                    y = y.replace(" ", "-")

            try:
                z = self.labels.z.path
            except AttributeError:
                z = self.labels.z
                if not (isinstance(z, str) and z != "None"):
                    z = "z"
                elif isinstance(z, str):
                    z = z.replace(" ", "-")

            path = Path(self.__class__.__name__)

        elif new is None:
            path = Path("")
            x = y = z = None

        else:
            path = Path(new)
            x = y = z = None

        scale_info = None
        if add_scale:
            xscale = "logX" if self.log.x else "linX"
            yscale = "logY" if self.log.y else "linY"
            scale_info = [xscale, yscale]

        return path, x, y, z, scale_info

    def _add_axis_labels(self, ax, transpose_axes=False):
        """Apply stored axis labels to a matplotlib axes object.

        This method retrieves the stored x and y labels and applies them to
        the provided matplotlib axes. Supports optional axis transposition
        for specialized plot types.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            The matplotlib axes object to label.
        transpose_axes : bool, optional
            If True, swap x and y labels before applying. This is useful
            for plots where the data orientation differs from the label
            orientation. Default is False.

        Notes
        -----
        Only applies labels that are not None. This allows for plots with
        unlabeled axes when appropriate.
        """
        xlbl = self.labels.x
        ylbl = self.labels.y

        if transpose_axes:
            xlbl, ylbl = ylbl, xlbl

        if xlbl is not None:
            ax.set_xlabel(xlbl)

        if ylbl is not None:
            ax.set_ylabel(ylbl)

    def _set_axis_scale(self, ax, transpose_axes=False):
        """Apply logarithmic scaling settings to matplotlib axes.

        Configures the x and y axes for logarithmic or linear scaling based
        on the stored log settings. Supports axis transposition for specialized
        plot orientations.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            The matplotlib axes object to configure.
        transpose_axes : bool, optional
            If True, swap the x and y log settings before applying.
            This is useful when the plot data orientation differs from
            the stored log configuration. Default is False.

        Notes
        -----
        Only applies logarithmic scaling when the corresponding log flag is True.
        Axes remain linear by default. Matplotlib will handle the transformation
        of data and tick marks automatically.
        """
        logx = self.log.x
        logy = self.log.y

        if transpose_axes:
            logx, logy = logy, logx

        if logx:
            ax.set_xscale("log")
        if logy:
            ax.set_yscale("log")

    def _format_axis(self, ax, transpose_axes=False):
        """Complete axis formatting with labels, scaling, grid, and ticks.

        This method provides comprehensive axis formatting by applying labels,
        logarithmic scaling, grid lines, and tick mark styling. It serves as
        the main formatting entry point for matplotlib axes in SolarWindPy plots.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            The matplotlib axes object to format.
        transpose_axes : bool, optional
            If True, transpose the axis configuration (swap x and y settings).
            This is useful for plots where data orientation differs from the
            expected label/scale orientation. Default is False.

        Notes
        -----
        This method applies SolarWindPy's standard axis formatting:

        - Axis labels from stored configuration
        - Logarithmic scaling when configured
        - Major grid lines on both axes
        - Inward-outward tick marks on both axes for better readability

        The formatting is applied in a specific order to ensure proper
        interaction between different matplotlib components.
        """
        self._add_axis_labels(ax, transpose_axes=transpose_axes)
        self._set_axis_scale(ax, transpose_axes=transpose_axes)
        ax.grid(True, which="major", axis="both")
        ax.tick_params(axis="both", which="both", direction="inout")

    #         x = self.data.loc[:, "x"]
    #         minx, maxx = x.min(), x.max()
    #         if self.log.x:
    #             minx, maxx = 10.0**np.array([minx, maxx])

    #         y = self.data.loc[:, "y"]
    #         miny, maxy = y.min(), y.max()
    #         if self.log.y:
    #             minx, maxx = 10.0**np.array([miny, maxy])

    #         # `pulled from the end of `ax.pcolormesh`.
    #         collection.sticky_edges.x[:] = [minx, maxx]
    #         collection.sticky_edges.y[:] = [miny, maxy]
    #         corners = (minx, miny), (maxx, maxy)
    #         self.update_datalim(corners)
    #         self.autoscale_view()

    @abstractmethod
    def set_data(self):
        pass

    @abstractmethod
    def make_plot(self):
        pass


class DataLimFormatter(ABC):
    """Mixin class for automatic data limit formatting in matplotlib plots.

    This mixin extends the base axis formatting functionality to automatically
    configure matplotlib axes data limits and view scaling based on the actual
    data ranges. It is designed to work with plot collections (like those from
    pcolormesh, contour, etc.) that need precise data limit management.

    The mixin follows the cooperative inheritance pattern and must be used
    alongside a Base-derived class. It overrides the _format_axis method to
    add data limit management while preserving all base formatting functionality.

    Methods
    -------
    _format_axis(ax, collection, **kwargs)
        Enhanced axis formatting that includes automatic data limit configuration
        based on the plot's x and y data ranges.

    Notes
    -----
    This mixin is particularly useful for 2D plotting functions like histograms,
    contour plots, and color mesh plots where matplotlib's automatic data limit
    detection may not work optimally.

    The class uses matplotlib's sticky_edges feature to ensure that the plot
    boundaries exactly match the data boundaries, preventing unwanted whitespace
    around the data.

    Examples
    --------
    Typical usage in a concrete plotting class:

    >>> class MyColorMeshPlot(DataLimFormatter, Base):
    ...     def make_plot(self):
    ...         fig, ax = plt.subplots()
    ...         collection = ax.pcolormesh(self.x_edges, self.y_edges, self.z_data)
    ...         self._format_axis(ax, collection)
    ...         return fig, ax
    """

    def _format_axis(self, ax, collection, **kwargs):
        """Enhanced axis formatting with automatic data limit configuration.

        Extends the base _format_axis method to include precise data limit
        management for matplotlib plot collections. This ensures that the
        axes boundaries exactly match the data boundaries.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            The matplotlib axes object to format.
        collection : matplotlib.collections.Collection
            The plot collection (e.g., from pcolormesh, contour) that needs
            data limit configuration. Must have sticky_edges attribute.
        **kwargs
            Additional keyword arguments passed to the parent _format_axis method.

        Notes
        -----
        This method performs the following operations:

        1. Calls the parent _format_axis for standard formatting
        2. Extracts x and y data ranges from self.data DataFrame
        3. Sets sticky edges on the collection to match data bounds
        4. Updates matplotlib's data limits and auto-scales the view

        The data is expected to be stored in a DataFrame with 'x' and 'y' columns.
        This follows SolarWindPy's standard data organization pattern.
        """
        super()._format_axis(ax, **kwargs)

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


class CbarMaker(ABC):
    """Mixin class for creating and managing matplotlib colorbars.

    This mixin provides standardized colorbar creation functionality for plots
    that require color mapping (e.g., 2D histograms, contour plots, heatmaps).
    It handles the complexities of matplotlib's colorbar API and provides
    consistent styling across SolarWindPy visualizations.

    The mixin follows the cooperative inheritance pattern and is designed to
    work alongside Base-derived classes that provide label management through
    the labels.z attribute.

    Methods
    -------
    _make_cbar(mappable, **kwargs)
        Create a matplotlib colorbar with automatic label detection and
        flexible axis/cax positioning.

    Notes
    -----
    This mixin simplifies colorbar creation by:

    - Automatically using the z-label from the parent class
    - Handling both ax and cax positioning options
    - Providing robust figure detection
    - Supporting all standard matplotlib colorbar options

    The mixin expects the parent class to have a `labels` attribute with a
    `z` component, typically provided by Base or PlotWithZdata classes.

    Examples
    --------
    Typical usage in a concrete plotting class:

    >>> class My2DPlot(CbarMaker, Base):
    ...     def make_plot(self):
    ...         fig, ax = plt.subplots()
    ...         mappable = ax.pcolormesh(self.x, self.y, self.z, cmap='viridis')
    ...         self._make_cbar(mappable, ax=ax)
    ...         return fig, ax
    """

    def _make_cbar(self, mappable, **kwargs):
        """Create a matplotlib colorbar with automatic configuration.

        Creates a colorbar for the given mappable object (e.g., the result of
        pcolormesh, contour, imshow) with automatic label detection and flexible
        positioning options. Provides robust figure detection and consistent
        styling across SolarWindPy plots.

        Parameters
        ----------
        mappable : matplotlib.cm.ScalarMappable
            The mappable object (e.g., result of ax.pcolormesh, ax.contour)
            that defines the colorbar's color mapping. See matplotlib's
            `figure.colorbar` documentation for details.
        ax : matplotlib.axes.Axes, optional
            The axes to which the colorbar will be attached. Cannot be used
            simultaneously with `cax`. If neither `ax` nor `cax` is provided,
            raises ValueError.
        cax : matplotlib.axes.Axes, optional
            The axes in which to draw the colorbar. Cannot be used
            simultaneously with `ax`. If neither `ax` nor `cax` is provided,
            raises ValueError.
        label : str, optional
            Label for the colorbar. If not provided, automatically uses
            `self.labels.z` from the parent class.
        **kwargs
            Additional keyword arguments passed directly to `matplotlib.figure.colorbar`.
            Common options include `shrink`, `aspect`, `pad`, `ticks`, and `format`.

        Returns
        -------
        matplotlib.colorbar.Colorbar
            The created colorbar instance, which can be further customized
            if needed.

        Raises
        ------
        ValueError
            If both `ax` and `cax` are provided, or if neither is provided.
            This prevents ambiguous colorbar positioning.

        Notes
        -----
        The method performs robust figure detection by handling both single axes
        and arrays of axes. This ensures compatibility with various matplotlib
        subplot configurations.

        For normalized plots (e.g., row or column normalized histograms), consider
        using `ticks=matplotlib.ticker.MultipleLocator(0.1)` for better tick spacing.

        Examples
        --------
        Basic usage with automatic labeling:

        >>> mappable = ax.pcolormesh(x, y, z)
        >>> cbar = self._make_cbar(mappable, ax=ax)

        With custom formatting:

        >>> cbar = self._make_cbar(mappable, ax=ax,
        ...                        shrink=0.8,
        ...                        format='%.2f')
        """
        ax = kwargs.pop("ax", None)
        cax = kwargs.pop("cax", None)
        if ax is not None and cax is not None:
            raise ValueError("Can't pass ax and cax.")

        if ax is not None:
            try:
                fig = ax.figure
            except AttributeError:
                fig = ax[0].figure
        elif cax is not None:
            try:
                fig = cax.figure
            except AttributeError:
                fig = cax[0].figure
        else:
            raise ValueError(
                "You must pass `ax` or `cax`. We don't want to rely on `plt.gca()`."
            )

        label = kwargs.pop("label", self.labels.z)
        cbar = fig.colorbar(mappable, label=label, ax=ax, cax=cax, **kwargs)

        return cbar


class PlotWithZdata(Base):
    """Concrete base class for plots that require three-dimensional data (x, y, z).

    This class extends the abstract Base class to provide concrete implementations
    for plots that work with three-dimensional data, such as 2D histograms,
    contour plots, surface plots, and other visualizations where a z-value
    corresponds to each (x, y) coordinate pair.

    PlotWithZdata handles data organization, path generation for three-variable
    plots, and label management for x, y, and z dimensions. It provides the
    foundation for all SolarWindPy plotting classes that visualize relationships
    between three variables.

    Attributes
    ----------
    _data : pandas.DataFrame
        DataFrame containing 'x', 'y', and 'z' columns with the plot data.
        NaN values are automatically removed during data setting.
    _clip : bool
        Flag indicating whether data clipping is enabled for this plot instance.

    Methods
    -------
    set_data(x, y, z=None, clip_data=False)
        Configure the plot data from input arrays, with optional z-data and clipping.
    set_path(new, add_scale=True)
        Generate file paths for three-variable plots with optional scale information.
    set_labels(**kwargs)
        Set axis labels with support for z-axis labeling.

    Notes
    -----
    This class provides concrete implementations of the abstract methods from Base,
    making it suitable for direct use or as a parent class for specialized plot types.

    The z-data is optional and defaults to uniform values (all ones) when not provided.
    This allows the same interface to be used for both weighted and unweighted plots.

    All input data is organized into a pandas DataFrame for consistent access patterns
    and automatic handling of missing values through dropna().

    Examples
    --------
    Basic usage for a 2D histogram-like plot:

    >>> class MyContourPlot(PlotWithZdata):
    ...     def make_plot(self):
    ...         fig, ax = plt.subplots()
    ...         ax.contour(self.data['x'], self.data['y'], self.data['z'])
    ...         self._format_axis(ax)
    ...         return fig, ax
    ...
    >>> plot = MyContourPlot()
    >>> plot.set_data(x_array, y_array, z_array)
    >>> plot.set_labels(x='X Variable', y='Y Variable', z='Intensity')
    >>> fig, ax = plot.make_plot()
    """

    def __init__(self):
        """Initialize PlotWithZdata instance.

        Provides concrete implementation of the abstract __init__ method
        from Base class. Sets up logging, labels, and path management
        for three-dimensional plotting.
        """
        super().__init__()

    def set_data(self, x, y, z=None, clip_data=False):
        """Set the plot data from input arrays.

        Organizes input data into the internal DataFrame structure and handles
        missing values, default z-values, and data validation. This method
        provides the concrete implementation of the abstract set_data method
        from the Base class.

        Parameters
        ----------
        x : array-like
            X-coordinate data. Must be convertible to pandas Series.
        y : array-like
            Y-coordinate data. Must be the same length as x.
        z : array-like, optional
            Z-coordinate data (e.g., weights, intensities, values).
            If None, defaults to uniform values of 1.0. Must be the
            same length as x and y if provided.
        clip_data : bool, optional
            Flag indicating whether data clipping should be enabled
            for this plot. Default is False.

        Raises
        ------
        ValueError
            If the resulting data contains only NaN values after cleaning,
            making the plot impossible to generate.

        Notes
        -----
        This method performs several data processing steps:

        1. Organizes x, y, z into a pandas DataFrame
        2. Sets default z-values (all ones) if z is not provided
        3. Removes rows containing any NaN values
        4. Validates that some data remains after cleaning
        5. Stores the clip_data flag for later use

        The resulting DataFrame always has columns ['x', 'y', 'z'] regardless
        of whether z-data was provided, ensuring consistent access patterns
        across different plot types.
        """
        data = pd.DataFrame({"x": x, "y": y})

        if z is None:
            z = pd.Series(1, index=data.index)

        data.loc[:, "z"] = z
        data = data.dropna()
        if not data.shape[0]:
            raise ValueError(
                "You can't build a %s with data that is exclusively NaNs"
                % self.__class__.__name__
            )
        self._data = data
        self._clip = bool(clip_data)

    def set_path(self, new, add_scale=True):
        """Generate file path for three-variable plots with scale information.

        Extends the base set_path method to handle three-dimensional plot paths
        with proper organization of x, y, and z components. Supports automatic
        path generation and optional axis scale information.

        Parameters
        ----------
        new : str or pathlib.Path
            Path specification. If "auto", generates path from plot labels.
            Otherwise, uses the provided path directly.
        add_scale : bool, optional
            If True, adds logarithmic scale information to the path.
            Default is True (differs from Base class default).

        Notes
        -----
        For automatic path generation, the resulting path structure is:
        ClassName/x_label/y_label/z_label[/scale_info]

        Scale information format is "linX-linY" or "logX-logY" depending
        on the axis scale settings. This provides clear organization for
        saved figures across different variable combinations and scales.

        Special handling is provided for normalized plots (paths ending with
        "norm") to maintain proper scale ordering.

        The method overrides the Base class default for add_scale to True,
        reflecting the importance of scale information for multi-variable plots.
        """
        # Bug: path doesn't auto-set log information.
        path, x, y, z, scale_info = super().set_path(new, add_scale)

        if new == "auto":
            path = path / x / y / z

        else:
            assert x is None
            assert y is None
            assert z is None

        if add_scale:
            assert scale_info is not None

            scale_info = "-".join(scale_info)

            if bool(len(path.parts)) and path.parts[-1].endswith("norm"):
                # Insert <norm> at end of path so scale order is (x, y, z).
                path = path.parts
                path = path[:-1] + (scale_info + "-" + path[-1],)
                path = Path(*path)
            else:
                path = path / scale_info

        self._path = path

    def set_labels(self, **kwargs):
        """Set axis labels with support for z-axis labeling.

        Extends the base set_labels method to handle z-axis labels while
        preserving all base functionality for x and y labels. Enables
        comprehensive labeling for three-dimensional plots.

        Parameters
        ----------
        x : str, optional
            Label for the x-axis. If not provided, uses current x label.
        y : str, optional
            Label for the y-axis. If not provided, uses current y label.
        z : str, optional
            Label for the z-axis (colorbar, contour levels, etc.).
            If not provided, uses current z label.
        auto_update_path : bool, optional
            If True, automatically regenerates the file path based on
            the new labels. Default is True.
        **kwargs
            Additional keyword arguments (will raise KeyError if unexpected
            arguments are provided).

        Notes
        -----
        This method ensures that z-axis labels are properly handled while
        maintaining compatibility with the base class label management system.
        The z-label is typically used for colorbar labels in 2D plots.

        Path regeneration occurs automatically unless auto_update_path=False,
        ensuring that saved figures are organized according to their labels.
        """
        z = kwargs.pop("z", self.labels.z)
        super().set_labels(z=z, **kwargs)


# class Plot2D(CbarMaker, Base):
#     def set_data(self, x, y, z=None, clip_data=False):
#         data = pd.DataFrame({"x": x, "y": y})

#         if z is None:
#             z = pd.Series(1, index=data.index)

#         data.loc[:, "z"] = z
#         data = data.dropna()
#         if not data.shape[0]:
#             raise ValueError(
#                 "You can't build a %s with data that is exclusively NaNs"
#                 % self.__class__.__name__
#             )
#         self._data = data
#         self._clip = bool(clip_data)

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

#     set_path.__doc__ = Base.set_path.__doc__

#     def set_labels(self, **kwargs):
#         z = kwargs.pop("z", self.labels.z)
#         super().set_labels(z=z, **kwargs)

# #     def _make_cbar(self, mappable, **kwargs):
# #         f"""Make a colorbar on `ax` using `mappable`.

# #         Parameters
# #         ----------
# #         mappable:
# #             See `figure.colorbar` kwarg of same name.
# #         ax: mpl.axis.Axis
# #             See `figure.colorbar` kwarg of same name.
# #         norm: mpl.colors.Normalize instance
# #             The normalization used in the plot. Passed here to determine
# #             y-ticks.
# #         kwargs:
# #             Passed to `fig.colorbar`. If `{self.__class__.__name__}` is
# #             row or column normalized, `ticks` defaults to
# #             :py:class:`mpl.ticker.MultipleLocator(0.1)`.
# #         """
# #         ax = kwargs.pop("ax", None)
# #         cax = kwargs.pop("cax", None)
# #         if ax is not None and cax is not None:
# #             raise ValueError("Can't pass ax and cax.")

# #         if ax is not None:
# #             try:
# #                 fig = ax.figure
# #             except AttributeError:
# #                 fig = ax[0].figure
# #         elif cax is not None:
# #             try:
# #                 fig = cax.figure
# #             except AttributeError:
# #                 fig = cax[0].figure
# #         else:
# #             raise ValueError(
# #                 "You must pass `ax` or `cax`. We don't want to rely on `plt.gca()`."
# #             )

# #         label = kwargs.pop("label", self.labels.z)
# #         cbar = fig.colorbar(mappable, label=label, ax=ax, cax=cax, **kwargs)

# #         return cbar
