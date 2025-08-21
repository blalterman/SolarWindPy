Physics Calculations in SolarWindPy
===================================

SolarWindPy provides robust implementations of fundamental plasma physics calculations
optimized for solar wind analysis. This guide covers the theoretical foundations,
valid parameter ranges, and numerical considerations for reliable scientific analysis.

.. warning::
   All physics calculations in SolarWindPy assume positive physical quantities.
   Negative densities, temperatures, or energies will produce invalid results.
   Always validate input parameters before analysis.

Thermal Speed Calculations
--------------------------

Theoretical Foundation
~~~~~~~~~~~~~~~~~~~~~~

SolarWindPy calculates thermal speeds using the standard plasma physics convention:

.. math::
   v_{th} = \sqrt{\frac{2kT}{m}}

where :math:`mw^2 = 2kT` represents the thermal speed convention used throughout
the solar wind physics community.

Valid Parameter Ranges
~~~~~~~~~~~~~~~~~~~~~~

For reliable thermal speed calculations:

- **Temperature**: :math:`T > 0` K (typically :math:`10^4` - :math:`10^7` K for solar wind)
- **Mass**: Standard particle masses from ``solarwindpy.tools.units_constants``
- **Expected Results**: :math:`10^3` - :math:`10^6` m/s for typical solar wind conditions

.. danger::
   **Critical**: Thermal speed calculations require positive thermal energy.
   Negative temperature or energy values will produce NaN results due to
   square root of negative numbers. Always validate ``T > 0`` before calculation.

Numerical Considerations
~~~~~~~~~~~~~~~~~~~~~~~~

- **Precision**: Maintains double precision for temperatures above 1 K
- **Edge Cases**: Returns NaN for non-physical negative temperatures
- **Performance**: Optimized for vectorized operations on large datasets

Example Usage with Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import solarwindpy as swp
   import numpy as np

   # Load plasma data
   plasma = swp.Plasma.from_file('solar_wind_data.csv')
   
   # Validate positive temperatures before calculation
   valid_temp_mask = plasma.temperature > 0
   if not valid_temp_mask.all():
       print(f"Warning: {(~valid_temp_mask).sum()} invalid temperature values")
   
   # Calculate thermal speeds for valid data only
   thermal_speeds = plasma.thermal_speed()[valid_temp_mask]
   
   # Validate results are in expected range
   expected_range = (1e3, 1e6)  # m/s
   valid_results = ((thermal_speeds >= expected_range[0]) & 
                    (thermal_speeds <= expected_range[1]))
   
   if not valid_results.all().all():
       print("Warning: Some thermal speeds outside expected range")

Alfvén Speed Calculations
-------------------------

Theoretical Foundation
~~~~~~~~~~~~~~~~~~~~~~

The Alfvén speed represents the characteristic speed of magnetohydrodynamic waves:

.. math::
   V_A = \frac{B}{\sqrt{\mu_0 \rho}}

where :math:`B` is the magnetic field magnitude and :math:`\rho` is the plasma
mass density including all ion species.

Valid Parameter Ranges
~~~~~~~~~~~~~~~~~~~~~~

For reliable Alfvén speed calculations:

- **Magnetic Field**: :math:`B > 0` nT (typically 1-100 nT in solar wind)
- **Density**: :math:`\rho > 0` kg/m³ (typically :math:`10^{-21}` - :math:`10^{-18}` kg/m³)
- **Expected Results**: :math:`10^4` - :math:`10^6` m/s for typical solar wind conditions

.. danger::
   **Physics-Breaking Error**: Zero density will produce infinite Alfvén speeds.
   The calculation ``rho.pow(-0.5)`` generates ``inf`` when density approaches zero.
   Always validate ``density > minimum_threshold`` before calculation.

.. warning::
   Near-zero magnetic field values may produce unrealistically small Alfvén speeds.
   Consider magnetic field measurement uncertainties in your analysis.

Numerical Considerations
~~~~~~~~~~~~~~~~~~~~~~~~

- **Singularities**: Infinite results for zero density (protected by input validation)
- **Precision Loss**: May occur for extremely small density values (< 1e-25 kg/m³)
- **Unit Consistency**: Calculations performed in SI units, converted for display

Example Usage with Robust Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import solarwindpy as swp
   import numpy as np

   # Load plasma data
   plasma = swp.Plasma.from_file('solar_wind_data.csv')
   
   # Define minimum physical thresholds
   min_density = 1e-23  # kg/m³ - minimum reliable density
   min_b_field = 0.1    # nT - minimum reliable magnetic field
   
   # Validate input parameters
   density_valid = plasma.density.sum(axis=1) > min_density
   b_field_valid = plasma.magnetic_field_magnitude() > min_b_field
   valid_mask = density_valid & b_field_valid
   
   if not valid_mask.all():
       invalid_count = (~valid_mask).sum()
       print(f"Warning: {invalid_count} data points fail validation")
   
   # Calculate Alfvén speeds for valid data
   alfven_speeds = plasma.alfven_speed()[valid_mask]
   
   # Validate results are physical
   expected_range = (1e4, 1e6)  # m/s
   physical_results = ((alfven_speeds >= expected_range[0]) & 
                       (alfven_speeds <= expected_range[1]))
   
   if not physical_results.all().all():
       print("Warning: Some Alfvén speeds outside expected physical range")

Plasma Frequency Calculations
-----------------------------

Theoretical Foundation
~~~~~~~~~~~~~~~~~~~~~~

The plasma frequency represents the characteristic oscillation frequency of electrons:

.. math::
   \omega_p = \sqrt{\frac{n e^2}{\epsilon_0 m_e}}

For ion plasma frequencies, the electron mass is replaced with the appropriate ion mass.

Valid Parameter Ranges
~~~~~~~~~~~~~~~~~~~~~~

For reliable plasma frequency calculations:

- **Number Density**: :math:`n > 0` m⁻³ (typically :math:`10^6` - :math:`10^8` m⁻³)
- **Expected Results**: :math:`10^3` - :math:`10^5` Hz for typical solar wind conditions

.. note::
   Plasma frequency calculations are generally more numerically stable than 
   thermal or Alfvén speed calculations, but still require positive densities.

Multi-Species Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When calculating plasma frequencies for multiple ion species:

- Validate each species density individually
- Consider mass-to-charge ratios for accurate frequencies
- Account for measurement uncertainties in composition

Error Handling and Troubleshooting
===================================

Common Issues and Solutions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**NaN Results in Calculations**
   - **Cause**: Negative input parameters (temperature, density, energy)
   - **Solution**: Validate all inputs are positive before calculation
   - **Prevention**: Use input validation functions provided in utilities

**Infinite Alfvén Speeds**
   - **Cause**: Zero or near-zero plasma density
   - **Solution**: Apply minimum density threshold (typically 1e-23 kg/m³)
   - **Prevention**: Check density measurements for instrument limitations

**Results Outside Expected Ranges**
   - **Cause**: Extreme parameter values or measurement errors
   - **Solution**: Apply physical bounds checking and data quality filters
   - **Prevention**: Implement systematic data validation procedures

Validation Utilities
~~~~~~~~~~~~~~~~~~~~

SolarWindPy provides validation utilities for common parameter checking:

.. code-block:: python

   from solarwindpy.tools import validate_physics_parameters
   
   # Comprehensive parameter validation
   validation_results = validate_physics_parameters(
       temperature=plasma.temperature,
       density=plasma.density,
       magnetic_field=plasma.magnetic_field
   )
   
   # Apply validation mask
   valid_data = plasma[validation_results.valid_mask]

Best Practices for Scientific Analysis
=======================================

Parameter Validation Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Pre-calculation Validation**
   - Check for positive temperatures, densities, and energies
   - Validate measurement ranges against instrument specifications
   - Apply quality flags from data providers

2. **Post-calculation Validation**
   - Verify results fall within expected physical ranges
   - Check for NaN or infinite values in results
   - Compare with established literature values when possible

3. **Uncertainty Propagation**
   - Consider measurement uncertainties in final results
   - Document validation criteria and thresholds used
   - Provide uncertainty estimates for derived quantities

Performance Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~

For large-scale analysis:

- Use vectorized operations instead of loops
- Apply validation masks to reduce calculation overhead
- Consider memory usage for very large datasets
- Implement progress monitoring for long calculations

Scientific Accuracy Assurance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Cross-validation**: Compare results with other established codes
- **Literature Comparison**: Validate against published solar wind studies  
- **Physical Consistency**: Ensure results satisfy basic plasma physics relations
- **Reproducibility**: Document all validation procedures and thresholds used

References and Further Reading
==============================

.. [1] Parks, G. K. (2004). Physics of Space Plasmas: An Introduction.
.. [2] Baumjohann, W., & Treumann, R. A. (2012). Basic Space Plasma Physics.
.. [3] Verscharen, D., et al. (2019). The multi-scale nature of the solar wind. 
       Living Reviews in Solar Physics, 16(1), 5.