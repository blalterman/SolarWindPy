#!/usr/bin/env python
r"""Specialized plotting tools for spacecraft orbit analysis and solar wind trajectory visualization.

This module provides advanced plotting capabilities specifically designed for analyzing
spacecraft orbits in the context of solar wind measurements. It combines orbital
mechanics visualization with plasma parameter analysis to enable comprehensive
studies of how spacecraft trajectory affects solar wind observations.

The module addresses the unique challenges of solar wind orbital analysis:

- **Trajectory-Parameter Correlation**: Visualization of how orbital position influences
  observed plasma properties, essential for understanding measurement context
- **Mission Phase Analysis**: Comparative plotting across different orbital phases
  (inbound, outbound, perihelion passages) to identify trajectory-dependent effects
- **Multi-Spacecraft Coordination**: Tools for analyzing coordinated observations
  from multiple spacecraft along different orbital trajectories

Core Capabilities
-----------------

Orbital Trajectory Plotting
    Advanced 3D visualization of spacecraft trajectories with solar wind context,
    including heliocentric distance markers, orbital phase identification, and
    trajectory-parameter correlation analysis.

Phase-Based Analysis
    Specialized histogram and scatter plot classes that automatically segment
    data based on orbital phases (inbound/outbound legs) to reveal trajectory-
    dependent phenomena in solar wind measurements.

Comparative Visualization
    Multi-panel layouts optimized for comparing solar wind parameters across
    different orbital phases, enabling identification of systematic effects
    related to spacecraft position and motion.

Integration with Solar Wind Physics
    Seamless integration with SolarWindPy's data structures and labeling systems
    to maintain scientific accuracy and consistency across orbital analysis workflows.

Key Classes
-----------
OrbitPlot : Abstract base class
    Provides common functionality for orbit-aware plotting including trajectory
    segmentation, phase identification, and orbital metadata management.

OrbitHist1D : One-dimensional histograms with orbital phase analysis
    Creates parameter distribution histograms segmented by orbital phases,
    enabling statistical comparison of solar wind properties during different
    mission segments.

OrbitHist2D : Two-dimensional parameter space analysis with orbital context
    Advanced 2D histogram visualization that reveals how parameter relationships
    change with orbital position and phase, critical for understanding measurement
    biases and physical correlations.

Technical Framework
-------------------
The module uses pandas IntervalIndex objects to define orbital phases and
automatically segments time series data accordingly. This approach ensures
temporal accuracy and enables complex trajectory-dependent analysis while
maintaining compatibility with SolarWindPy's data structures.

Orbital phase analysis is particularly valuable for:
- Correcting for trajectory-dependent measurement biases
- Identifying solar wind structures that correlate with spacecraft position
- Validating theoretical predictions across different heliocentric distances
- Planning future mission trajectories based on measurement requirements

Examples
--------
Basic orbital phase histogram analysis:

>>> import pandas as pd
>>> from solarwindpy.plotting.orbits import OrbitHist1D
>>> # Define inbound and outbound trajectory phases
>>> orbit_phases = pd.IntervalIndex([
...     pd.Interval('2018-01-01', '2018-06-01'),  # Inbound
...     pd.Interval('2018-07-01', '2018-12-01')   # Outbound
... ])
>>> # Create phase-segmented velocity histogram
>>> orbit_hist = OrbitHist1D(orbit_phases, velocity_data)
>>> ax = orbit_hist.make_plot()

Multi-phase parameter correlation analysis:

>>> from solarwindpy.plotting.orbits import OrbitHist2D
>>> # Analyze velocity-temperature relationship by orbital phase
>>> orbit_2d = OrbitHist2D(orbit_phases, velocity_data, temperature_data)
>>> axes, cbars = orbit_2d.make_in_out_plot()
"""

import pdb  # noqa: F401

import numpy as np
import pandas as pd
import matplotlib as mpl

from abc import ABC

from . import histograms
from . import tools

# import logging

# from . import labels

# import os
# import psutil

# def log_mem_usage():
#    usage = psutil.Process(os.getpid()).memory_info()
#    usage = "\n".join(
#        ["{} {:.3f} GB".format(k, v * 1e-9) for k, v in usage._asdict().items()]
#    )
#    logging.getLogger("main").warning("Memory usage\n%s", usage)


class OrbitPlot(ABC):
    r"""Abstract base class for orbit-aware solar wind parameter visualization.

    OrbitPlot provides the foundational framework for all plotting classes that
    need to analyze solar wind data in the context of spacecraft trajectory and
    orbital phases. It handles the complex temporal segmentation required to
    correlate plasma measurements with orbital position and mission phase.

    This abstract class establishes the interface and common functionality for:
    - Orbital phase identification and data segmentation
    - Trajectory-dependent parameter analysis
    - Multi-phase comparative visualization
    - Integration with SolarWindPy's data structures

    The class is designed to work with any solar wind mission that has well-defined
    orbital phases, including heliocentric missions like Parker Solar Probe,
    Solar Orbiter, and planetary missions with significant heliocentric motion.

    Parameters
    ----------
    orbit : pandas.IntervalIndex
        Temporal intervals defining distinct orbital phases for analysis.
        Typically includes inbound and outbound trajectory segments, allowing
        for trajectory-dependent parameter comparison. Each interval represents
        a coherent orbital phase with consistent trajectory characteristics.
    *args, **kwargs
        Additional arguments passed to parent plotting classes, enabling
        flexible inheritance and composition with other SolarWindPy plotting
        functionality.

    Attributes
    ----------
    orbit : pandas.IntervalIndex
        Sorted interval index defining orbital phase boundaries. Used for
        automatic data segmentation and phase-aware analysis.
    grouped : pandas.DataFrameGroupBy
        Pre-configured groupby object that segments data by orbital phases
        combined with other analysis axes, enabling efficient phase-based
        statistical operations.
    path : pathlib.Path
        File system path for plot output, automatically incorporating orbit
        metadata for organized result storage.

    Methods
    -------
    set_orbit(new)
        Update orbital phase definitions with validation and sorting.
    set_path(*args, orbit=None, **kwargs)
        Configure output path with orbital phase metadata integration.
    make_cut()
        Perform temporal segmentation of data based on orbital phases.

    Notes
    -----
    This abstract class implements the Observer pattern for orbital phase
    analysis, automatically updating data segmentation when orbital phase
    definitions change. The temporal segmentation process:

    1. **Phase Identification**: Maps measurement timestamps to orbital phases
       using pandas.cut() with the interval index
    2. **Category Assignment**: Labels data points as 'Inbound', 'Outbound',
       or 'Both' based on trajectory phase
    3. **Data Integration**: Combines phase labels with existing analysis
       categories for comprehensive parameter studies

    The class is optimized for solar wind applications where trajectory effects
    are significant, such as studies of:
    - Radial evolution of solar wind properties
    - Trajectory-dependent measurement biases
    - Orbital phase correlations with solar activity
    - Multi-spacecraft coordination analysis

    Examples
    --------
    Define orbital phases for Parker Solar Probe analysis:

    >>> import pandas as pd
    >>> # Define encounter phases
    >>> psp_orbits = pd.IntervalIndex([
    ...     pd.Interval('2018-11-01', '2018-11-15'),  # Encounter 1 inbound
    ...     pd.Interval('2019-04-01', '2019-04-15')   # Encounter 1 outbound
    ... ])

    Create a custom orbit-aware plotting class:

    >>> class CustomOrbitPlot(OrbitPlot, SomePlottingClass):
    ...     def __init__(self, orbit, data):
    ...         super().__init__(orbit, data)
    ...         # Custom initialization
    """

    def __init__(self, orbit, *args, **kwargs):
        r"""Initialize orbit-aware plotting with trajectory phase definitions.

        Parameters
        ----------
        orbit : pandas.IntervalIndex
            Temporal intervals defining orbital phases for trajectory-dependent
            analysis. Must contain at least one interval representing a coherent
            orbital phase (e.g., inbound leg, outbound leg, encounter period).
        *args, **kwargs
            Additional arguments forwarded to parent classes in the method
            resolution order, enabling flexible composition with other plotting
            classes from the SolarWindPy framework.

        Notes
        -----
        The initialization process establishes orbital phase awareness by:
        1. Validating and storing orbital phase definitions via set_orbit()
        2. Calling parent class constructors to inherit plotting functionality
        3. Setting up data structures for trajectory-dependent analysis

        The orbit parameter defines the temporal framework for all subsequent
        analysis operations, enabling automatic data segmentation and phase-aware
        statistical calculations.
        """
        self.set_orbit(orbit)
        super(OrbitPlot, self).__init__(*args, **kwargs)

    @property
    def _disable_both(self):
        r"""Control availability of 'Both' phase analysis option.

        Returns
        -------
        bool
            True to disable 'Both' phase analysis, preventing potential
            memory issues with large datasets by limiting analysis to
            individual orbital phases (Inbound/Outbound only).
        """
        return True

    @property
    def orbit(self):
        r"""Access current orbital phase definitions.

        Returns
        -------
        pandas.IntervalIndex
            Sorted temporal intervals defining orbital phases for trajectory-
            dependent analysis. Each interval represents a distinct mission
            phase with consistent orbital characteristics.
        """
        return self._orbit

    @property
    def _orbit_key(self):
        r"""Standard key name for orbital phase identification in data structures.

        This property provides a consistent identifier for orbital phase data
        across all analysis operations, ensuring compatibility with pandas
        groupby operations and data structure manipulation.

        Returns
        -------
        str
            The string 'Orbit' used as a consistent key for orbital phase
            identification in DataFrames, groupby operations, and analysis
            metadata throughout the SolarWindPy plotting framework.
        """
        return "Orbit"

    @property
    def grouped(self):
        r"""Pre-configured groupby object for orbital phase analysis.

        Creates a pandas GroupBy object that automatically segments data by
        orbital phases combined with other analysis dimensions, enabling
        efficient phase-aware statistical operations and parameter comparisons.

        Returns
        -------
        pandas.DataFrameGroupBy
            GroupBy object configured for orbital phase analysis, combining
            phase identification with other analysis axes for comprehensive
            trajectory-dependent parameter studies.

        Notes
        -----
        The groupby operation combines orbital phase labels with existing
        analysis axes to create multi-dimensional data segmentation. This
        enables complex analyses such as parameter distributions within
        each orbital phase, cross-phase correlations, and trajectory-
        dependent statistical comparisons.
        """
        gb = self.joint.groupby(list(self._gb_axes) + [self._orbit_key])
        return gb

    def set_path(self, *args, orbit=None, **kwargs):
        r"""Configure file output path with orbital metadata integration.

        Sets up the file system path for plot output, optionally incorporating
        orbital phase metadata for organized storage of trajectory-dependent
        analysis results.

        Parameters
        ----------
        *args, **kwargs
            Arguments passed to parent class set_path method for baseline
            path configuration following SolarWindPy conventions.
        orbit : object with path attribute, optional
            Orbital metadata object containing path information for organizing
            output by orbital phases or mission segments. When provided,
            appends orbit-specific path components to the base output path.

        Notes
        -----
        This method enables organized storage of orbital analysis results by
        automatically incorporating trajectory metadata into file paths. This
        is particularly valuable for long-term studies involving multiple
        orbital phases or comparative analysis across different mission segments.

        Examples
        --------
        Set basic output path:

        >>> orbit_plot.set_path(Path('/analysis/results'))

        Include orbital metadata in path:

        >>> orbit_plot.set_path(Path('/analysis'), orbit=encounter_metadata)
        """
        super(OrbitPlot, self).set_path(*args, **kwargs)
        if orbit is not None:
            self._path = self.path / orbit.path

    def set_orbit(self, new):
        r"""Update orbital phase definitions with validation and sorting.

        Configures the temporal intervals that define distinct orbital phases
        for trajectory-dependent analysis. Validates input format and ensures
        proper temporal ordering for consistent phase identification.

        Parameters
        ----------
        new : pandas.IntervalIndex
            Temporal intervals defining orbital phases for analysis. Each
            interval should represent a coherent orbital phase with consistent
            trajectory characteristics (e.g., inbound leg, outbound leg,
            encounter period, cruise phase).

        Raises
        ------
        TypeError
            If input is not a pandas.IntervalIndex, ensuring type safety
            for subsequent temporal operations and phase identification.

        Notes
        -----
        The method performs automatic sorting of intervals to ensure temporal
        consistency in phase identification. This is critical for proper data
        segmentation and phase-aware analysis operations.

        Orbital phases should be defined based on mission-specific criteria
        such as heliocentric distance, orbital mechanics, or scientific
        objectives. Common phase definitions include:

        - Inbound/Outbound legs relative to perihelion
        - Encounter periods for planetary missions
        - Solar minimum/maximum periods for long-term studies
        - Coordinated observation intervals for multi-spacecraft studies

        Examples
        --------
        Define Parker Solar Probe encounter phases:

        >>> import pandas as pd
        >>> psp_encounters = pd.IntervalIndex([
        ...     pd.Interval('2018-11-01', '2018-11-15'),  # Encounter 1
        ...     pd.Interval('2019-04-01', '2019-04-15')   # Encounter 2
        ... ])
        >>> orbit_plot.set_orbit(psp_encounters)
        """
        if not isinstance(new, pd.IntervalIndex):
            raise TypeError("Orbit must be a pandas.IntervalIndex")
        self._orbit = new.sort_values()

    def make_cut(self):
        r"""Perform temporal data segmentation based on orbital phases.

        Creates categorical phase labels for all data points based on their
        temporal alignment with defined orbital intervals. This method is the
        core of trajectory-dependent analysis, enabling automatic data
        segmentation for phase-aware statistical operations.

        Notes
        -----
        The segmentation process involves several key steps:

        1. **Parent Class Processing**: Calls inherited make_cut() for baseline
           data preparation and any existing categorical segmentation.

        2. **Temporal Mapping**: Uses pandas.cut() to map data timestamps to
           orbital phase intervals, creating interval-based categorization.

        3. **Phase Labeling**: Converts interval categories to meaningful phase
           names ('Inbound', 'Outbound') based on orbital mechanics conventions.

        4. **Category Management**: Optionally adds 'Both' category for combined
           analysis when not disabled by memory management settings.

        5. **Data Integration**: Combines phase labels with existing categorical
           data to create comprehensive analysis framework.

        The resulting categorical data enables efficient groupby operations
        and phase-aware statistical analysis throughout the plotting framework.

        Phase assignment assumes a two-phase orbital model with the first
        interval representing the inbound trajectory leg and the second
        representing the outbound leg. This convention aligns with typical
        heliocentric mission profiles.

        The method automatically handles data points outside defined orbital
        phases by assigning NaN categories, ensuring robust operation with
        incomplete orbital coverage.
        """
        # Apply parent class data cutting for baseline categorical processing
        super(OrbitPlot, self).make_cut()
        cut = self.cut

        # Map data timestamps to orbital phase intervals using pandas.cut()
        # This creates interval-based categorical assignment for each data point
        time = pd.cut(self.data.index, self.orbit)

        # Convert interval categories to meaningful phase names
        # Assumes first interval = Inbound, second interval = Outbound
        time = time.map({self.orbit[0]: "Inbound", self.orbit[1]: "Outbound"}).astype(
            "category"
        )

        # Optionally add 'Both' category for combined phase analysis
        # Disabled by default to prevent memory issues with large datasets
        if not self._disable_both:
            time.add_categories("Both", inplace=True)

        # Create Series with orbital phase labels
        # Name must differ from 'Epoch' to avoid groupby key conflicts
        time = pd.Series(time, index=self.data.index, name=self._orbit_key)

        # Integrate orbital phases with existing categorical data
        # Sort columns for consistent data structure organization
        cut = pd.concat([cut, time], axis=1).sort_index(axis=1)
        self._cut = cut


class OrbitHist1D(OrbitPlot, histograms.Hist1D):
    r"""One-dimensional histogram analysis with orbital phase segmentation.

    OrbitHist1D creates sophisticated parameter distribution histograms that
    automatically segment solar wind measurements by spacecraft orbital phases.
    This enables statistical comparison of plasma properties between different
    trajectory segments, revealing how orbital position influences observed
    parameter distributions.

    The class is particularly valuable for studying radial evolution of solar
    wind properties, identifying trajectory-dependent measurement biases, and
    characterizing parameter variations across different mission phases.

    Parameters
    ----------
    orbit : pandas.IntervalIndex
        Temporal intervals defining orbital phases for comparative analysis.
        Typically includes inbound and outbound trajectory segments enabling
        statistical comparison of parameter evolution with heliocentric distance.
    x : pandas.Series
        Solar wind parameter data for histogram analysis. Common parameters
        include bulk velocity, magnetic field strength, ion temperature, or
        plasma density measurements from spacecraft instrumentation.
    **kwargs
        Additional parameters passed to parent histogram class, including
        binning specifications, data processing options, and visualization
        parameters for histogram customization.

    Attributes
    ----------
    orbit : pandas.IntervalIndex
        Orbital phase definitions inherited from OrbitPlot base class.
    data : pandas.DataFrame
        Processed parameter data with orbital phase labels for segmented analysis.
    intervals : dict
        Bin definitions for histogram construction, optimized for solar wind
        parameter ranges and distribution characteristics.

    Methods
    -------
    make_plot(ax=None, fcn=None, **kwargs)
        Create orbital phase comparison histogram with automatic legend.
    agg(**kwargs)
        Perform phase-aware statistical aggregation of parameter distributions.
    _format_axis(ax)
        Apply specialized formatting for orbital phase comparison plots.

    Notes
    -----
    The class combines orbital awareness from OrbitPlot with histogram
    capabilities from Hist1D to create powerful parameter distribution
    analysis tools. Key features include:

    - **Phase Segmentation**: Automatic separation of data by orbital phases
      enabling direct comparison of parameter statistics between trajectory segments
    - **Statistical Analysis**: Built-in calculation of phase-specific statistics
      including means, medians, and distribution moments
    - **Visual Comparison**: Overlay plotting of phase-specific histograms with
      automatic legend generation for clear trajectory-dependent visualization

    Orbital phase analysis is particularly insightful for:
    - Radial gradients in solar wind parameters
    - Asymmetric solar wind evolution (inbound vs. outbound differences)
    - Trajectory-dependent measurement validation
    - Mission phase optimization for future spacecraft

    Examples
    --------
    Analyze solar wind velocity distribution by orbital phase:

    >>> import pandas as pd
    >>> from solarwindpy.plotting.orbits import OrbitHist1D
    >>> # Define Parker Solar Probe encounter phases
    >>> psp_phases = pd.IntervalIndex([
    ...     pd.Interval('2018-11-01', '2018-11-15'),  # Inbound
    ...     pd.Interval('2019-03-15', '2019-03-30')   # Outbound
    ... ])
    >>> # Create phase-segmented velocity histogram
    >>> vel_hist = OrbitHist1D(psp_phases, velocity_data, nbins=50)
    >>> ax = vel_hist.make_plot()
    >>> # Histogram automatically shows inbound vs outbound velocity distributions
    """

    def __init__(self, orbit, x, **kwargs):
        r"""Initialize orbital phase histogram analysis.

        Parameters
        ----------
        orbit : pandas.IntervalIndex
            Temporal intervals defining distinct orbital phases for comparative
            histogram analysis. Each interval represents a coherent trajectory
            segment with consistent orbital characteristics.
        x : pandas.Series
            Solar wind parameter measurements for histogram analysis. Data should
            span the temporal range covered by orbital phase definitions for
            meaningful phase-based statistical comparison.
        **kwargs
            Additional configuration options passed to parent histogram class:

            - nbins : int or array-like, binning specification for histogram
            - bin_precision : float, precision for automatic bin edge calculation
            - logx : bool, logarithmic scaling for parameter axis
            - clip_data : bool, outlier removal for improved visualization
            - density : bool, normalize histograms for probability density

        Notes
        -----
        Initialization establishes the framework for orbital phase histogram
        analysis by combining orbital awareness with parameter distribution
        capabilities. The process configures automatic data segmentation and
        prepares statistical analysis tools for trajectory-dependent studies.
        """
        super(OrbitHist1D, self).__init__(orbit, x, **kwargs)

    def _format_axis(self, ax):
        super(OrbitHist1D, self)._format_axis(ax)
        ax.legend(loc=0, ncol=1, framealpha=0)

    def agg(self, **kwargs):
        fcn = kwargs.pop("fcn", None)
        agg = super(OrbitHist1D, self).agg(fcn=fcn, **kwargs)

        if not self._disable_both:
            cut = self.cut.drop("Orbit", axis=1)
            tko = self.agg_axes
            gb_both = self.joint.drop("Orbit", axis=1).groupby(list(self._gb_axes))
            agg_both = self._agg_runner(cut, tko, gb_both, fcn).copy(deep=True)

            agg = agg.unstack("Orbit")
            agg_both = pd.concat({"Both": agg_both}, axis=1, names=["Orbit"])
            if agg_both.columns.nlevels == 2:
                agg_both = agg_both.swaplevel(0, 1, 1)

            agg = (
                pd.concat([agg, agg_both], axis=1)
                .sort_index(axis=1)
                .stack("Orbit")
                .sort_index(axis=0)
            )

        #         for k, v in self.intervals.items():
        #             # if > 1 intervals, pass level. Otherwise, don't as this raises a NotImplementedError. (20190619)
        #             agg = agg.reindex(index=v, level=k if agg.index.nlevels > 1 else None)

        return agg

    def make_plot(self, ax=None, fcn=None, **kwargs):
        r"""Make a plot on `ax`.

        If `ax` is None, create a `mpl.subplots` axis.

        `**kwargs` passed directly to `ax.plot`.

        `drawstyle` defaults to `steps-mid`

        `fcn` passed to `self.agg`. Only one function is allow b/c we
        don't yet handle uncertainties.
        """
        if ax is None:
            fig, ax = tools.subplots()

        agg = self.agg(fcn=fcn).unstack(self._orbit_key)
        agg = agg.reindex(index=self.intervals["x"])

        x = pd.IntervalIndex(agg.index).mid
        if self.log.x:
            x = 10.0**x

        drawstyle = kwargs.pop("drawstyle", "steps-mid")
        for k, v in agg.items():
            ax.plot(x, v, drawstyle=drawstyle, label=k, **kwargs)

        self._format_axis(ax)

        return ax


class OrbitHist2D(OrbitPlot, histograms.Hist2D):
    r"""Two-dimensional parameter space analysis with orbital phase awareness.

    OrbitHist2D provides sophisticated visualization of solar wind parameter
    relationships that automatically segments data by spacecraft orbital phases.
    This enables detailed analysis of how parameter correlations evolve with
    orbital position, revealing trajectory-dependent phenomena and physical
    relationships in the solar wind.

    The class is essential for understanding parameter coupling evolution,
    identifying trajectory-dependent biases in multi-parameter relationships,
    and characterizing how solar wind physics changes with heliocentric distance.

    Parameters
    ----------
    orbit : pandas.IntervalIndex
        Temporal intervals defining orbital phases for comparative 2D analysis.
        Enables correlation studies across different trajectory segments to
        reveal how parameter relationships evolve with orbital position.
    x : pandas.Series
        First parameter for 2D histogram analysis (typically independent variable).
        Common choices include solar wind velocity, magnetic field strength,
        or heliocentric distance measurements.
    y : pandas.Series
        Second parameter for 2D histogram analysis (typically dependent variable).
        Often includes ion temperatures, plasma densities, or derived parameters
        that may correlate with the x-parameter.
    **kwargs
        Additional configuration options for 2D histogram analysis including
        binning specifications, normalization options, and visualization parameters.

    Attributes
    ----------
    orbit : pandas.IntervalIndex
        Orbital phase definitions for trajectory-dependent analysis.
    data : pandas.DataFrame
        Multi-parameter data with orbital phase labels for segmented 2D analysis.
    edges : dict
        2D bin edge definitions for histogram construction in both x and y dimensions.
    axnorm : str
        Normalization method for histogram displays ('c', 'r', or other options).

    Methods
    -------
    make_one_plot(kind, ax=None, fcn=None, **kwargs)
        Create single orbital phase 2D histogram ('Inbound', 'Outbound', or 'Both').
    make_in_out_plot(fcn=None, **kwargs)
        Generate side-by-side comparison of inbound and outbound phase histograms.
    make_in_out_both_plot(fcn=None, **kwargs)
        Create comprehensive three-panel display with inbound, outbound, and combined analysis.
    project_1d(axis, **kwargs)
        Extract 1D projection from 2D orbital analysis for detailed distribution study.

    Notes
    -----
    OrbitHist2D combines sophisticated 2D histogram capabilities with orbital
    phase awareness to enable advanced multi-parameter solar wind analysis.
    Key capabilities include:

    **Phase-Specific Correlations**: Reveals how parameter relationships change
    between inbound and outbound trajectory segments, identifying asymmetric
    solar wind evolution and trajectory-dependent measurement effects.

    **Comparative Visualization**: Specialized plotting methods create publication-
    quality multi-panel figures that clearly demonstrate phase-dependent parameter
    relationships and their statistical significance.

    **Statistical Robustness**: Built-in normalization and aggregation functions
    ensure meaningful statistical comparison across orbital phases with different
    temporal coverage or measurement densities.

    Applications include:
    - Radial evolution of parameter correlations (e.g., velocity-temperature relationships)
    - Trajectory bias identification in multi-parameter measurements
    - Solar wind regime classification across different orbital phases
    - Validation of theoretical predictions for heliocentric distance dependencies

    Examples
    --------
    Analyze velocity-temperature correlation by orbital phase:

    >>> import pandas as pd
    >>> from solarwindpy.plotting.orbits import OrbitHist2D
    >>> # Define orbital phases for correlation analysis
    >>> orbit_phases = pd.IntervalIndex([
    ...     pd.Interval('2018-11-01', '2018-12-01'),  # Inbound phase
    ...     pd.Interval('2019-03-01', '2019-04-01')   # Outbound phase
    ... ])
    >>> # Create 2D orbital histogram
    >>> orbit_2d = OrbitHist2D(orbit_phases, velocity_data, temperature_data)
    >>> # Compare inbound vs outbound parameter relationships
    >>> axes, cbars = orbit_2d.make_in_out_plot()
    """

    def __init__(self, orbit, x, y, **kwargs):
        r"""Initialize orbital phase 2D histogram analysis.

        Parameters
        ----------
        orbit : pandas.IntervalIndex
            Temporal intervals defining orbital phases for comparative 2D parameter
            analysis. Each interval represents a trajectory segment for correlation
            studies across different orbital positions.
        x : pandas.Series
            First parameter dimension for 2D correlation analysis. Typically the
            independent variable in parameter relationship studies, with temporal
            coverage spanning the defined orbital phases.
        y : pandas.Series
            Second parameter dimension for 2D correlation analysis. Usually the
            dependent variable in parameter relationship studies, aligned temporally
            with x-parameter measurements.
        **kwargs
            Advanced configuration options for 2D histogram analysis:

            - nbins : int or tuple, bin specifications for x and y dimensions
            - bin_precision : float or tuple, precision for automatic binning
            - logx, logy : bool, logarithmic scaling for parameter axes
            - axnorm : str, normalization method for histogram display
            - clip_data : bool, outlier removal for improved correlation visualization

        Notes
        -----
        Initialization configures the framework for sophisticated 2D parameter
        relationship analysis across orbital phases. The process establishes
        data structures for multi-phase correlation studies and prepares
        visualization tools for trajectory-dependent parameter analysis.
        """
        super(OrbitHist2D, self).__init__(orbit, x, y, **kwargs)

    def _format_in_out_axes(self, inbound, outbound):
        #         logging.getLogger("main").warning("Formatting in out axes")
        #         log_mem_usage()

        xlim = np.concatenate([inbound.get_xlim(), outbound.get_xlim()])
        x0 = xlim.min()
        x1 = xlim.max()
        #         x0, x1 = outbound.get_xlim()
        inbound.set_xlim(x1, x0)
        outbound.set_xlim(x0, x1)
        outbound.yaxis.label.set_visible(False)

        # Make the Inbound/Outbound transition cyan.
        sin = inbound.spines["right"]
        sout = outbound.spines["left"]
        for spine in (sin, sout):
            spine.set_edgecolor("cyan")
            spine.set_linewidth(2.5)

        # TODO: Get top and bottom axes to line up without `tight_layout`, which
        #       puts colorbar into an unusable location.

    #         for k, ax in axes.items():
    #             au = 1.49597871e+11 # [m]
    #             rs = 695700000 # [m]
    #             conversion = au/rs
    #             if self.labels.x == labels.special.Distance2Sun("Rs"):
    #                 tax = ax.twiny()
    #                 tax.grid(False)
    #                 tax.set_xlim(* (np.array(ax.get_xlim()) / conversion))
    #                 tax.set_xlabel(labels.special.Distance2Sun("AU"))

    @staticmethod
    def _prune_lower_yaxis_ticks(ax0, ax1):
        nbins = ax0.get_yticks().size - 1
        for ax in (ax0, ax1):
            if ax.get_yscale() == "linear":
                ax.yaxis.set_major_locator(
                    mpl.ticker.MaxNLocator(nbins=nbins, prune="lower")
                )

    def _format_in_out_both_axes(self, axi, axo, axb, cbari, cbaro, cbarb):
        #         logging.getLogger("main").warning("Formatting in out both axes")
        #         log_mem_usage()

        ylim = np.concatenate([axi.get_ylim(), axi.get_ylim(), axb.get_ylim()])
        y0 = ylim.min()
        y1 = ylim.max()
        for ax in (axi, axo, axb):
            ax.set_ylim(y0, y1)

        # TODO: annotate Inbound and Outbound? Might be handled by TrendFitter
        self._prune_lower_yaxis_ticks(axi, axo)

        if not self.log.y:
            self._prune_lower_yaxis_ticks(cbari.ax, cbaro.ax)

    def agg(self, **kwargs):
        r"""Wrap Hist1D and Hist2D `agg` so that we can aggergate orbit legs.

        Legs: Inbound, Outbound, and Both."""
        #         logging.getLogger("main").warning("Starting agg")
        #         log_mem_usage()

        fcn = kwargs.pop("fcn", None)
        agg = super(OrbitHist2D, self).agg(fcn=fcn, **kwargs)

        #         logging.getLogger("main").warning("Running Both agg")
        #         log_mem_usage()

        if not self._disable_both:
            cut = self.cut.drop("Orbit", axis=1)
            tko = self.agg_axes
            gb_both = self.joint.drop("Orbit", axis=1).groupby(list(self._gb_axes))
            agg_both = self._agg_runner(cut, tko, gb_both, fcn).copy(deep=True)

            agg = agg.unstack("Orbit")
            agg_both = pd.concat({"Both": agg_both}, axis=1, names=["Orbit"])
            if agg_both.columns.nlevels == 2:
                agg_both = agg_both.swaplevel(0, 1, 1)

            agg = (
                pd.concat([agg, agg_both], axis=1)
                .sort_index(axis=1)
                .stack("Orbit")
                .sort_index(axis=0)
            )

        #         for k, v in self.intervals.items():
        #             # if > 1 intervals, pass level. Otherwise, don't as this raises a NotImplementedError. (20190619)
        #             agg = agg.reindex(index=v, level=k if agg.index.nlevels > 1 else None)

        #         logging.getLogger("main").warning("Grouping agg for axis normalization")
        #         log_mem_usage()

        grouped = agg.groupby(self._orbit_key)
        transformed = grouped.transform(self._axis_normalizer)
        return transformed

    def project_1d(self, axis, project_counts=False, **kwargs):
        r"""Make a `Hist1D` from the data stored in this `His2D`.

        Parameters
        ----------
        axis: str
            "x" or "y", specifying the axis to project into 1D.
        kwargs:
            Passed to `Hist1D`. Primarily to allow specifying `bin_precision`.

        Returns
        -------
        h1: `Hist1D`
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
        if y is not None:
            # Only select y-values plotted.
            logy = self.log._asdict()[other]
            yedges = self.edges[other].values
            y = y.where((yedges[0] <= y) & (y <= yedges[-1]))
            if logy:
                y = 10.0**y

        h1 = OrbitHist1D(
            self.orbit,
            x,
            y=y,
            logx=logx,
            clip_data=False,  # Any clipping will be addressed by bins.
            nbins=self.edges[axis].values,
            **kwargs,
        )
        h1.set_labels(x=self.labels._asdict()[axis], y=self.labels._asdict()[other])
        h1.set_path("auto")

        return h1

    def _put_agg_on_ax(self, ax, agg, cbar, limit_color_norm, cbar_kwargs, **kwargs):
        r"""Refactored putting `agg` onto `ax`.

        Python was crashing due to the way too many `agg` runs (20190731)."""
        #         logging.getLogger("main").warning("Putting agg on ax")
        #         log_mem_usage()

        x = self.edges["x"]
        y = self.edges["y"]

        if self.log.x:
            x = 10.0**x
        if self.log.y:
            y = 10.0**y

        XX, YY = np.meshgrid(x, y)

        axnorm = self.axnorm
        norm = kwargs.pop(
            "norm", mpl.colors.Normalize(0, 1) if axnorm in ("c", "r") else None
        )

        #         pdb.set_trace()

        if limit_color_norm:
            self._limit_color_norm(norm)

        #         logging.getLogger("main").warning("Reindexing agg on ax")
        #         log_mem_usage()

        # Unstacking drops some NaN bins, so we must reindex again.
        agg = agg.reindex(index=self.intervals["y"], columns=self.intervals["x"])

        #         logging.getLogger("main").warning("Do the plotting")
        #         log_mem_usage()

        C = np.ma.masked_invalid(agg.values)
        pc = ax.pcolormesh(XX, YY, C, norm=norm, **kwargs)

        if cbar:
            if cbar_kwargs is None:
                cbar_kwargs = dict()
            #             use_gridspec = kwargs.pop("use_gridspec", False)
            cbar = self._make_cbar(pc, ax, **cbar_kwargs)

        self._format_axis(ax)

        #         logging.getLogger("main").warning("Done putting agg on axis")
        #         log_mem_usage()

        return cbar

    def make_one_plot(
        self,
        kind,
        ax=None,
        fcn=None,
        cbar=True,
        limit_color_norm=False,
        cbar_kwargs=None,
        **kwargs,
    ):
        r"""Create a single orbital phase 2D histogram for detailed parameter relationship analysis.

        Generates a focused visualization of parameter correlations within one specific
        orbital phase, enabling detailed examination of trajectory-dependent phenomena
        and parameter relationships during distinct mission segments.

        This method is particularly valuable for detailed analysis of individual orbital
        phases, validation of phase-specific correlations, and creation of targeted
        visualizations for specific mission segments or scientific investigations.

        Parameters
        ----------
        kind : str
            Orbital phase identifier for histogram creation. Accepts flexible input
            formats for user convenience:

            =================== ========================
            Phase               Accepted Inputs
            =================== ========================
            Inbound trajectory  'Inbound', 'I', 'i'
            Outbound trajectory 'Outbound', 'O', 'o'
            Combined analysis   'Both', 'B', 'b'
            =================== ========================

        ax : matplotlib.axes.Axes, optional
            Target axes for plot creation. If None, creates new figure and axes
            using SolarWindPy's enhanced subplot functionality with appropriate
            sizing for 2D parameter space visualization.
        fcn : callable, optional
            Statistical aggregation function applied to histogram data for advanced
            analysis. Common options include numpy statistical functions (mean,
            median, std) for parameter relationship characterization.
        cbar : bool, default True
            Enable automatic colorbar creation with appropriate labeling and
            positioning. Colorbar reflects the statistical significance and
            magnitude of parameter relationships within the orbital phase.
        limit_color_norm : bool, default False
            Apply intelligent color normalization limits to enhance visualization
            of parameter relationship structure while maintaining statistical accuracy.
        cbar_kwargs : dict, optional
            Advanced colorbar customization parameters including positioning,
            labeling, and appearance options for publication-quality output.
        **kwargs
            Additional visualization parameters passed to underlying 2D histogram
            methods, including color mapping, transparency, and display options.

        Returns
        -------
        ax : matplotlib.axes.Axes
            Formatted axes containing the orbital phase 2D histogram with proper
            labeling, scaling, and parameter relationship visualization.
        cbar : matplotlib.colorbar.Colorbar or None
            Colorbar object if created, enabling additional customization after
            plot generation. None if colorbar creation disabled.

        Raises
        ------
        ValueError
            If kind parameter doesn't match recognized orbital phase identifiers.
        NotImplementedError
            If 'Both' phase analysis is requested but disabled for memory management.

        Notes
        -----
        This method provides the foundation for orbital phase-specific parameter
        relationship analysis, enabling:

        **Focused Analysis**: Detailed examination of parameter correlations within
        specific orbital phases without interference from other trajectory segments.

        **Statistical Validation**: Application of custom statistical functions to
        quantify the strength and significance of phase-specific relationships.

        **Publication Graphics**: Creation of high-quality visualizations suitable
        for scientific publication with proper labeling and formatting.

        The method automatically handles data aggregation, statistical processing,
        and visualization formatting to ensure scientifically accurate and visually
        clear representation of orbital phase-dependent parameter relationships.

        Examples
        --------
        Analyze inbound trajectory velocity-temperature relationship:

        >>> orbit_2d = OrbitHist2D(orbit_phases, velocity, temperature)
        >>> ax, cbar = orbit_2d.make_one_plot('Inbound', cmap='plasma')

        Create statistical analysis of outbound phase with custom function:

        >>> import numpy as np
        >>> ax, cbar = orbit_2d.make_one_plot('o', fcn=np.mean,
        ...                                   limit_color_norm=True)

        Generate publication-ready combined phase analysis:

        >>> cbar_config = {'shrink': 0.8, 'label': 'Occurrence Rate'}
        >>> ax, cbar = orbit_2d.make_one_plot('Both', cbar_kwargs=cbar_config)
        """
        trans = {"i": "Inbound", "o": "Outbound", "b": "Both"}
        try:
            kind = trans[kind.lower()[0]]
        except KeyError:
            raise ValueError("Unrecognized kind '{}'".format(kind))

        if kind == "Both" and self._disable_both:
            raise NotImplementedError(
                "Disabled both to prevent double linked list kernel crash"
            )

        if ax is None:
            fig, ax = tools.subplots()

        agg = self.agg(fcn=fcn).xs(kind, axis=0, level="Orbit").unstack("x")
        cbar = self._put_agg_on_ax(
            ax, agg, cbar, limit_color_norm, cbar_kwargs, **kwargs
        )

        return ax, cbar

    def make_in_out_plot(
        self, fcn=None, cbar=True, limit_color_norm=False, cbar_kwargs=None, **kwargs
    ):
        r"""Plot "Inbound" and "Outbound" on axes joined at perihelion.

        If `ax` is None, create a `mpl.subplots` axis.

        `**kwargs` passed directly to `ax.plot`.

        `drawstyle` defaults to `steps-mid`

        `fcn` passed to `self.agg`. Only one function is allow b/c we
        don't yet handle uncertainties.
        """
        fig, axes = tools.subplots(
            ncols=2, gridspec_kw=dict(wspace=0), sharex=False, sharey=True
        )

        agg = self.agg(fcn=fcn)
        aggi = agg.xs("Inbound", axis=0, level="Orbit").unstack("x")
        aggo = agg.xs("Outbound", axis=0, level="Orbit").unstack("x")

        cbari = self._put_agg_on_ax(
            axes[0], aggi, False, limit_color_norm, cbar_kwargs, **kwargs
        )
        cbaro = self._put_agg_on_ax(
            axes[1], aggo, cbar, limit_color_norm, cbar_kwargs, **kwargs
        )

        self._format_in_out_axes(*axes)

        # For the sake of legacy code. (20190731)
        axes = pd.Series(axes, index=("Inbound", "Outbound"))
        cbars = pd.Series([cbari, cbaro], index=("Inbound", "Outbound"))
        #         logging.getLogger("main").warning("Done with plot")
        #         log_mem_usage()

        return axes, cbars

    def make_in_out_both_plot(
        self, fcn=None, cbar=True, limit_color_norm=False, cbar_kwargs=None, **kwargs
    ):
        r"""Plot "Inbound", "Outbound", and "Both" on stacked axes.

        If `ax` is None, create a `mpl.subplots` axis.

        `**kwargs` passed directly to `ax.plot`.

        `drawstyle` defaults to `steps-mid`

        `fcn` passed to `self.agg`. Only one function is allow b/c we
        don't yet handle uncertainties.
        """

        if self._disable_both:
            raise NotImplementedError(
                "Disabled to attempt removing double-linked list kernel crash"
            )

        fig, axes = tools.subplots(
            nrows=3,
            gridspec_kw=dict(wspace=0, hspace=0),
            sharex=True,
            sharey=False,  # Can't `sharey`, because prevents pruning Inbound and Outbound lower y-ticks.
        )

        agg = self.agg(fcn=fcn)
        aggi = agg.xs("Inbound", axis=0, level="Orbit").unstack("x")
        aggo = agg.xs("Outbound", axis=0, level="Orbit").unstack("x")
        aggb = agg.xs("Both", axis=0, level="Orbit").unstack("x")

        cbar = kwargs.pop("cbar", True)

        axi, axo, axb = axes
        cbari = self._put_agg_on_ax(
            axi, aggi, cbar, limit_color_norm, cbar_kwargs, **kwargs
        )
        cbaro = self._put_agg_on_ax(
            axo, aggo, cbar, limit_color_norm, cbar_kwargs, **kwargs
        )
        cbarb = self._put_agg_on_ax(
            axb, aggb, cbar, limit_color_norm, cbar_kwargs, **kwargs
        )

        #         axi, cbari = self.make_one_plot("Inbound", axes[0], **kwargs)
        #         axo, cbaro = self.make_one_plot("Outbound", axes[1], **kwargs)
        #         axb, cbarb = self.make_one_plot("Both", axes[2], **kwargs)

        #         self._format_joint_axes(*axes)
        self._format_in_out_both_axes(axi, axo, axb, cbari, cbaro, cbarb)

        # For the sake of legacy code. (20190731)
        axes = pd.Series(axes, index=("Inbound", "Outbound", "Both"))
        cbars = pd.Series([cbari, cbaro, cbarb], index=("Inbound", "Outbound", "Both"))

        #         logging.getLogger("main").warning("Done with plot")
        #         log_mem_usage()

        return axes, cbars
