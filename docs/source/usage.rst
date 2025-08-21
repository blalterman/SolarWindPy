Usage Guide
===========

.. contents::
   :local:
   :depth: 2

Overview
--------

SolarWindPy provides a comprehensive framework for analyzing solar wind plasma and magnetic field data. The package is organized around several key concepts:

- **Plasma**: Central container for multi-species plasma data
- **Ion**: Individual ion species with moments and properties  
- **MultiIndex DataFrames**: Hierarchical data structure for scientific measurements
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
   
   # Create plasma object
   plasma = swp.Plasma(epoch=epoch)
   plasma.add_ion_species('p1', density=n_p, velocity=v_p, temperature=T_p)

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
   thermal_speed = plasma.get_ion('p1').thermal_speed()
   
   # Plasma beta
   beta = plasma.get_ion('p1').beta()
   
   # Alfvén speed
   alfven_speed = plasma.alfven_speed()

Data Visualization
------------------

Use the plotting module for scientific visualizations:

.. code-block:: python

   import solarwindpy.plotting as swpp
   
   # Create time series plot
   fig, ax = swpp.time_series(plasma.data.xs('n', level='M'), 
                             title='Proton Density')
   
   # Scientific scatter plot with proper labels
   swpp.scatter(plasma.data.xs('v', level='M').xs('x', level='C'),
               plasma.data.xs('T', level='M'),
               xlabel=swpp.labels.velocity_x(),
               ylabel=swpp.labels.temperature())

Error Handling and Missing Data
-------------------------------

SolarWindPy follows scientific best practices:

.. code-block:: python

   # Missing data represented as NaN (never 0 or -999)
   data_with_gaps = plasma.data.dropna()
   
   # Validate physical constraints
   plasma.validate_physics()  # Checks for unphysical values

Advanced Features
-----------------

For more complex analyses:

.. code-block:: python

   # Fit functions for statistical analysis
   from solarwindpy.fitfunctions import Gaussian
   
   fit = Gaussian()
   fit.fit(temperature_data)
   
   # Instability analysis
   from solarwindpy.instabilities import beta_ani_inst
   
   stability = beta_ani_inst(beta_parallel, beta_perpendicular)

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
