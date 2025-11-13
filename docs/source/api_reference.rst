API Reference
=============

Complete API documentation for all modules, classes, and functions in SolarWindPy.

Top-Level API
-------------

Core classes and functions available at the package level.

.. currentmodule:: solarwindpy

.. autosummary::
   :toctree: _autosummary
   :template: class.rst

   Plasma
   Hist1D
   Hist2D
   TeXlabel

Core Module
-----------

Main data structures, physics calculations, and fundamental classes for solar wind analysis.
The core module provides the :class:`~solarwindpy.core.plasma.Plasma` container class and
:class:`~solarwindpy.core.ions.Ion` species class, along with vector/tensor operations
and physical constants.

.. autosummary::
   :toctree: _autosummary
   :template: module.rst
   :recursive:

   solarwindpy.core.plasma
   solarwindpy.core.ions
   solarwindpy.core.base
   solarwindpy.core.vector
   solarwindpy.core.tensor
   solarwindpy.core.spacecraft
   solarwindpy.core.alfvenic_turbulence
   solarwindpy.core.units_constants

Plotting Module
---------------

Visualization tools for creating publication-quality scientific figures. Includes histogram
classes with aggregation, scatter plots, scientific labels with automatic units, and helper
functions for figure management.

.. autosummary::
   :toctree: _autosummary
   :template: module.rst
   :recursive:

   solarwindpy.plotting.histograms
   solarwindpy.plotting.labels
   solarwindpy.plotting.scatter
   solarwindpy.plotting.spiral
   solarwindpy.plotting.orbits
   solarwindpy.plotting.tools
   solarwindpy.plotting.select_data_from_figure

Fit Functions Module
--------------------

Statistical analysis and curve fitting tools for solar wind data. Provides parametric
fit functions (Gaussian, exponential, power law, Moyal) with automatic parameter
estimation, plotting utilities, and trend analysis.

.. autosummary::
   :toctree: _autosummary
   :template: module.rst
   :recursive:

   solarwindpy.fitfunctions.core
   solarwindpy.fitfunctions.gaussians
   solarwindpy.fitfunctions.exponentials
   solarwindpy.fitfunctions.power_laws
   solarwindpy.fitfunctions.moyal
   solarwindpy.fitfunctions.lines
   solarwindpy.fitfunctions.trend_fits
   solarwindpy.fitfunctions.plots
   solarwindpy.fitfunctions.tex_info

Solar Activity Module
---------------------

Tools for accessing and analyzing solar activity indices. Includes sunspot number data,
LISIRD (LASP Interactive Solar Irradiance Data Center) access, and solar cycle analysis.

.. autosummary::
   :toctree: _autosummary
   :template: module.rst
   :recursive:

   solarwindpy.solar_activity.base
   solarwindpy.solar_activity.plots
   solarwindpy.solar_activity.sunspot_number
   solarwindpy.solar_activity.lisird

Instabilities Module
--------------------

Plasma instability analysis and threshold calculations. Includes temperature anisotropy
instability thresholds based on Verscharen et al. (2016) and related analyses.

.. autosummary::
   :toctree: _autosummary
   :template: module.rst
   :recursive:

   solarwindpy.instabilities.verscharen2016
   solarwindpy.instabilities.beta_ani

Tools Module
------------

General utility functions and helper tools for data manipulation and analysis.

.. autosummary::
   :toctree: _autosummary
   :template: module.rst
   :recursive:

   solarwindpy.tools
