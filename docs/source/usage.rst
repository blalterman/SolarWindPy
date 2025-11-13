Usage Guide
===========

.. contents::
   :local:
   :depth: 2

Overview
--------

SolarWindPy provides a comprehensive framework for analyzing solar wind plasma
and magnetic field data. The package is organized around several key concepts:

- **Plasma**: Central container for multi-species plasma data
- **Ion**: Individual ion species with moments and properties
- **MultiIndex DataFrames**: Hierarchical data structure for scientific
  measurements
- **Physics Conventions**: Consistent units and calculations throughout

Quick Start
-----------

Import the core components:

.. code-block:: python

   import solarwindpy as swp
   import numpy as np
   import pandas as pd

Basic Plasma Analysis
---------------------

Create a plasma object with proton data:

.. code-block:: python

   # Create sample data
   epoch = pd.date_range('2023-01-01', periods=100, freq='1min')

   # Proton density, velocity, temperature
   n_p = np.random.normal(5.0, 1.0, 100)  # cm^-3
   v_p = np.random.normal(400, 50, (100, 3))  # km/s
   T_p = np.random.normal(1e5, 2e4, 100)  # K

   # Create MultiIndex DataFrame with proper structure
   columns = pd.MultiIndex.from_tuples([
       ('n', '', 'p1'),    # Proton density
       ('v', 'x', 'p1'),   # Proton velocity x
       ('v', 'y', 'p1'),   # Proton velocity y
       ('v', 'z', 'p1'),   # Proton velocity z
       ('w', 'par', 'p1'), # Parallel thermal speed
       ('w', 'per', 'p1'), # Perpendicular thermal speed
       ('b', 'x', ''),     # Magnetic field x
       ('b', 'y', ''),     # Magnetic field y
       ('b', 'z', ''),     # Magnetic field z
   ], names=['M', 'C', 'S'])

   # Calculate thermal speeds from temperature using mw² = 2kT convention
   from solarwindpy.core.units_constants import Constants
   const = Constants()
   k_B = const.kb  # Boltzmann constant [J/K]
   m_p = const.m['p1']  # Proton mass [kg]

   # Thermal speed: w = sqrt(2kT/m)
   w_thermal = np.sqrt(2 * k_B * T_p / m_p) / 1000  # Convert to km/s

   # Sample magnetic field data
   b_field = np.random.normal([5, -2, 3], [1, 1, 1], (100, 3))  # nT

   data = pd.DataFrame({
       ('n', '', 'p1'): n_p,
       ('v', 'x', 'p1'): v_p[:, 0],
       ('v', 'y', 'p1'): v_p[:, 1],
       ('v', 'z', 'p1'): v_p[:, 2],
       ('w', 'par', 'p1'): w_thermal,
       ('w', 'per', 'p1'): w_thermal,
       ('b', 'x', ''): b_field[:, 0],
       ('b', 'y', ''): b_field[:, 1],
       ('b', 'z', ''): b_field[:, 2],
   }, index=epoch, columns=columns)

   # Create plasma object
   plasma = swp.Plasma(data, 'p1')

Working with MultiIndex DataFrames
-----------------------------------

SolarWindPy uses a three-level MultiIndex structure. The MultiIndex levels are:

    M: Measurement (n, v, w, b, etc.)
    C: Component (x, y, z for vectors, empty for scalars)
    S: Species (p1, p2, a, etc.)


Accessing Data
--------------

Data can be accessed from specialized methods or from underlying containers.

.. code-block:: python

   # Access measurements from plasma methods - RECOMMENDED
   ndens = plasma.n('p1')

   # Access specific measurements from underlying data
   ndens = plasma.data.xs('n', level='M').xs('p1', level='S')

   # Access measurements from ions
   ndens = plasma.ions.p1.n('p1')

   # Access measurements from ion data
   ndens = plasma.ions.p1.data.xs('n', level='M')
   vpx = plasma.data.xs('v', level='M').xs('x', level='C').xs('p1', level='S')


Physics Calculations
--------------------

The Plasma class is structured to intelligently combine observations from across ions

.. code-block:: python

   # Access the density for protons and alphas
   n = plasma.number_density('p1,a')
   # Caclculate the total proton + alpha density, using the shortcut method
   n  = plasma.n('a+p1')

   # Access the proton and alpha velocities
   v = plasma.velocity('a,p1')
   # Calculate the center of mass velocity with the shortcut method
   v = plasma.v('a+p1')

   # Access the magnetic field data
   b = plasma.bfield
   b = plasma.b # shortcut

   # Access the proton and alpha thermal speeds
   w = plasma.thermal_speed('a,p1')
   # The total thermal speed is physically ambiguous
   w = plasma.w('a+p1')

   # Thermal pressures
   pth = plasma.pth('a,p1')
   # Access the total pressure
   pth = plasma.pth('a+p1')

   # Proton plasma beta
   beta = plasma.beta('p1')
   # Total beta
   beta = plasma.beta('p1+a')
   # Both betas
   beta = plasma.beta('a,p1')
   

Data Visualization
------------------

Use the plotting module for scientific visualizations. The MultiIndex structure maps
directly to plot labels and paths.

.. code-block:: python

   import matplotlib.pyplot as plt
   from solarwindpy.plotting.labels import TeXlabels

   # Create time series plot of proton density
   fig, ax = plt.subplots()
   ndens = plasma.n('a+p1')
   ax.plot(ndens.index, ndens.values)
   ax.set_ylabel(TeXlabel(('n', '', 'p1+a'))) # Density is a scalar
   ax.set_title('Total Proton + Alpha Density Time Series')
   plt.show()

   # Scatter plot with proper labels
   fig, ax = plt.subplots()
   vx = plasma.v('p1').xs('x', axis=1, level='C')
   wpar = plasma.w('p1').xs('par', axis=1, level='C')
   ax.scatter(vx, wpar)

   # Create labels - note how MultiIndex maps directly to plot labels
   xlbl = TeXlabel(('v', 'x', 'p1'))
   ylbl = TeXlabel(('w', 'par', 'p1'))
   ax.set_xlabel(xlbl)
   ax.set_ylabel(ylbl)

   plt.show()

The labels include units automatically:

.. code-block:: pycon

   >>> xlbl = TeXlabel(('v', 'x', 'p1'))
   >>> print(xlbl)
   r'v_{x;p_1} \; \left[\mathrm{km \, s^{-1}}\right]'
   >>> ylbl = TeXlabel(('w', 'par', 'p1'))
   >>> print(ylbl)
   r'w_{\parallel;p_1} \; \left[\mathrm{km \, s^{-1}}\right]'

TeXlabels have built-in path methods for defining figure paths:

.. code-block:: pycon

   >>> xlbl.path
   Path('v_x_p1')
   >>> ylbl.path
   Path('w_par_p1')

TeXlabels can generate normalized quantities and are unit-aware:

.. code-block:: pycon

   >>> ratio_label = TeXlabel(('v', 'x', 'p1'), ('w', 'par', 'p1'))
   >>> print(ratio_label)
   r'v_{x;p_1} / w_{\parallel;p_1} \; \left[\#\right]'

Create a 2D histogram using SolarWindPy aggregation tools:

.. code-block:: python

   # Create a 2D histogram of the data
   from solarwindpy.plotting import Hist2D
   
   beta = plasma.beta('p1').xs('par', axis=1, level='S')
   h2d = Hist2D(vx, beta, nbins=(50, 50), logy=True) # calculate log-scaled y-bins
   h2d.set_labels(x=xlbl, y=TeXlabel('beta', 'par', 'p1'))
   h2d.make_plot()

SolarWindPy plotting tools have built-in path management that includes axis scales and plot normalizations:

.. code-block:: pycon

   >>> h2d.path
   Path('Hist2D/v_x_p1/beta_par_p1/linX-logY/count')

The path updates when you change normalization:

.. code-block:: pycon

   >>> h2d.set_axnorm('c')  # Make the plot column-normalized
   >>> h2d.path
   Path('Hist2D/v_x_p1/beta_par_p1/linX-logY/Cnorm')
   
Show all available labels:

.. code-block:: pycon

   >>> import solarwindpy.plotting.labels as labels
   >>> labels.available_labels()


Error Handling and Missing Data
-------------------------------

SolarWindPy follows scientific best practices:

.. code-block:: python

   # Missing data represented as NaN
   data_without_gaps = plasma.data.dropna()

   # Check for physical constraints manually
   # Density should be positive
   assert (plasma.n('p1') > 0).all(), 'Density must be positive'

   # Thermal speeds should be positive
   thermal_data = plasma.data.xs('w', level='M')
   assert (thermal_data > 0).all().all(), 'Thermal speeds must be positive'


Non-Linear Fitting
------------------

For more complex analyses:

.. code-block:: python

   # Fit functions for statistical analysis
   from solarwindpy.fitfunctions import Gaussian

   # Get thermal speed data
   w_par = plasma.w('p1').xs('par', level='C')
   
   # Histogram data
   from solarwindpy.plotting import Hist1D
   h1d = Hist1D(w_par, nbins=50)
   h1d.set_labels(x=TeXlabel(('w', 'par', 'p1')))
   
   # Get aggregated data
   agg = h1d.agg()
   
   # Aggregated index is an IntervalIndex, but was previously monkey patched to address
   # a pandas pretty printing bug.
   x_data = pd.IntervalIndex(agg.index).mid
   y_data = agg.values

   fit = Gaussian(x_data, y_data)
   fit.make_fit()
   
   # Plot the resulting fit
   fit.plotter.set_labels(x=TeXlabel(('w', 'par', 'p1')))
   fit.plotter.plot_raw_used_fit_resid()


Best Practices
--------------

1. **Units**: All internal calculations use SI units
2. **Time**: Use pandas DatetimeIndex for temporal data
3. **Missing Data**: Represent gaps as NaN, not fill values
4. **Built-In Aggregation**: Use plasma methods to aggregate quantities where applicable

Next Steps
----------

- See the :doc:`tutorial` for detailed examples
- Browse the :doc:`api_reference` for complete function documentation
- Check out specific modules for specialized functionality
