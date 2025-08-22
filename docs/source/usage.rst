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

SolarWindPy uses a three-level MultiIndex structure:

.. code-block:: python

   # Access specific measurements
   proton_density = plasma.data.xs('n', level='M').xs('p1', level='S')
   proton_velocity_x = plasma.data.xs('v', level='M').xs('x', level='C').xs('p1', level='S')

   # The MultiIndex levels are:
   # M: Measurement (n, v, w, b, etc.)
   # C: Component (x, y, z for vectors, empty for scalars)
   # S: Species (p1, p2, a, etc.)

Physics Calculations
--------------------

Calculate derived quantities:

.. code-block:: python

   # Thermal speed (mw² = 2kT convention)
   thermal_speed = plasma.p1.thermal_speed()

   # Plasma beta for protons
   beta = plasma.beta('p1')

   # Access ion properties directly
   proton_density = plasma.p1.n      # Number density [cm^-3]
   proton_velocity = plasma.p1.v     # Velocity vector [km/s]
   proton_temp = plasma.p1.T         # Temperature [K]

Data Visualization
------------------

Use the plotting module for scientific visualizations:

.. code-block:: python

   import matplotlib.pyplot as plt
   import solarwindpy.plotting.labels as labels

   # Create time series plot of proton density
   fig, ax = plt.subplots()
   proton_density = plasma.data.xs('n', level='M').xs('p1', level='S')
   ax.plot(proton_density.index, proton_density.values)
   ax.set_ylabel(labels.density('p1'))
   ax.set_title('Proton Density Time Series')
   plt.show()

   # Scientific scatter plot with proper labels
   fig, ax = plt.subplots()
   vx = plasma.data.xs('v', level='M').xs('x', level='C').xs('p1', level='S')
   temp = plasma.data.xs('w', level='M').xs('par', level='S').xs('p1', level='S')
   ax.scatter(vx, temp)
   ax.set_xlabel(labels.velocity_x('p1'))
   ax.set_ylabel(labels.thermal_speed_par('p1'))
   plt.show()

Error Handling and Missing Data
-------------------------------

SolarWindPy follows scientific best practices:

.. code-block:: python

   # Missing data represented as NaN (never 0 or -999)
   data_with_gaps = plasma.data.dropna()

   # Check for physical constraints manually
   # Density should be positive
   assert (plasma.p1.n > 0).all(), "Density must be positive"

   # Temperature should be positive
   thermal_data = plasma.data.xs('w', level='M')
   assert (thermal_data > 0).all().all(), "Thermal speeds must be positive"

Advanced Features
-----------------

For more complex analyses:

.. code-block:: python

   # Fit functions for statistical analysis
   from solarwindpy.fitfunctions import Gaussian

   # Get thermal speed data for fitting
   w_par = plasma.data.xs('w', level='M').xs('par', level='C').xs('p1', level='S')
   x_data = w_par.index.astype('int64') // 10**9  # Convert to seconds
   y_data = w_par.values

   fit = Gaussian(x_data, y_data)
   fit.fit()

   # Instability analysis
   from solarwindpy.instabilities.verscharen2016 import beta_ani_inst

   # Calculate plasma betas
   beta_par = plasma.beta('p1').par
   beta_per = plasma.beta('p1').per

   # Check instability threshold
   instability_threshold = beta_ani_inst(beta_par)

Best Practices
--------------

1. **Units**: All internal calculations use SI units
2. **Time**: Use pandas DatetimeIndex for temporal data
3. **Missing Data**: Represent gaps as NaN, not fill values
4. **Physics**: Validate results against known constraints
5. **Performance**: Use vectorized operations with NumPy/Pandas

Next Steps
----------

- See the :doc:`tutorial` for detailed examples
- Browse the :doc:`api_reference` for complete function documentation
- Check out specific modules for specialized functionality
