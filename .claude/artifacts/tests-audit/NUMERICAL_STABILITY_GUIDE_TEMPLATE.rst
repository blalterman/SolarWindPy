Numerical Stability Guide
=========================

SolarWindPy performs complex plasma physics calculations that require careful attention
to numerical stability and precision. This guide helps users understand potential
numerical limitations and implement robust analysis procedures.

.. important::
   Numerical stability is critical for scientific accuracy. Always validate
   input parameters and verify results are within expected physical ranges.

Understanding Numerical Limitations
====================================

Floating-Point Precision
~~~~~~~~~~~~~~~~~~~~~~~~~

SolarWindPy uses double-precision floating-point arithmetic (64-bit) for all
physics calculations, providing approximately 15-17 decimal digits of precision.

**Precision Considerations:**
- Calculations maintain accuracy for typical solar wind parameter ranges
- Extreme values (very large or very small) may experience precision loss
- Repeated operations can accumulate rounding errors

**Recommended Parameter Ranges:**

==============================  ====================  ========================
Parameter                       Reliable Range        Precision Notes
==============================  ====================  ========================
Temperature (K)                 1e3 - 1e8            Full precision maintained
Density (kg/m³)                 1e-25 - 1e-15        Below 1e-25 may be unstable
Magnetic Field (nT)             0.1 - 1000           Near-zero values problematic
Velocity (m/s)                  1e2 - 1e6            Relativistic speeds not supported
==============================  ====================  ========================

Common Numerical Issues
=======================

Physics-Breaking Edge Cases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Zero Density Singularities (CRITICAL)**
   Alfvén speed calculations become infinite when plasma density approaches zero.

   .. danger::
      Code: ``rho.pow(-0.5)`` produces ``inf`` when ``rho = 0``
      
      **Impact**: Infinite Alfvén speeds propagate through all MHD calculations
      
      **Solution**: Always validate ``density > minimum_threshold`` before calculation

   .. code-block:: python

      # UNSAFE: Can produce infinite results
      alfven_speed = plasma.alfven_speed()
      
      # SAFE: With density validation
      min_density = 1e-23  # kg/m³
      valid_density = plasma.density.sum(axis=1) > min_density
      alfven_speed = plasma.alfven_speed()[valid_density]

**Negative Thermal Energy (CRITICAL)**
   Thermal speed calculations fail catastrophically with negative temperatures.

   .. danger::
      Code: ``temperature.pow(0.5)`` produces ``NaN`` when ``temperature < 0``
      
      **Impact**: NaN thermal speeds invalidate pressure and temperature analysis
      
      **Solution**: Validate ``temperature > 0`` before all thermal calculations

   .. code-block:: python

      # UNSAFE: Can produce NaN results  
      thermal_speed = plasma.thermal_speed()
      
      # SAFE: With temperature validation
      valid_temp = plasma.temperature > 0
      thermal_speed = plasma.thermal_speed()[valid_temp]

Precision Loss Patterns  
~~~~~~~~~~~~~~~~~~~~~~~

**Catastrophic Cancellation**
   Occurs when subtracting nearly equal large numbers, losing significant digits.

   .. warning::
      Vector magnitude calculations may lose precision for nearly parallel vectors:
      
      ``sqrt(x² + y² + z²)`` when components are very different magnitudes

   .. code-block:: python

      # Example: Problematic for small perpendicular components
      import numpy as np
      
      # Large parallel component with small perpendicular
      x, y, z = 1e6, 1e-3, 1e-3
      magnitude = np.sqrt(x**2 + y**2 + z**2)
      # May lose precision in small components

**Scale-Dependent Errors**
   Calculations become unreliable at parameter extremes.

   .. warning::
      - Very large values: Risk of overflow to infinity
      - Very small values: Risk of underflow to zero
      - Mixed scales: Loss of precision in smaller values

Parameter Validation Framework
==============================

Input Validation Procedures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Step 1: Physical Bounds Checking**

.. code-block:: python

   def validate_physics_parameters(plasma_data):
       """Validate plasma parameters for physics calculations."""
       
       validation_mask = np.ones(len(plasma_data), dtype=bool)
       warnings = []
       
       # Temperature validation
       temp_valid = plasma_data.temperature > 0
       if not temp_valid.all():
           invalid_count = (~temp_valid).sum()
           warnings.append(f"{invalid_count} invalid temperatures (≤ 0)")
           validation_mask &= temp_valid
       
       # Density validation  
       min_density = 1e-23  # kg/m³
       density_total = plasma_data.density.sum(axis=1)
       density_valid = density_total > min_density
       if not density_valid.all():
           invalid_count = (~density_valid).sum()
           warnings.append(f"{invalid_count} invalid densities (≤ {min_density})")
           validation_mask &= density_valid
       
       # Magnetic field validation
       min_b_field = 0.1  # nT
       b_magnitude = plasma_data.magnetic_field_magnitude()
       b_field_valid = b_magnitude > min_b_field
       if not b_field_valid.all():
           invalid_count = (~b_field_valid).sum()
           warnings.append(f"{invalid_count} invalid B-fields (≤ {min_b_field})")
           validation_mask &= b_field_valid
       
       return {
           'valid_mask': validation_mask,
           'warnings': warnings,
           'valid_fraction': validation_mask.sum() / len(validation_mask)
       }

**Step 2: Result Range Validation**

.. code-block:: python

   def validate_calculation_results(results, calculation_type):
       """Validate physics calculation results are within expected ranges."""
       
       expected_ranges = {
           'thermal_speed': (1e3, 1e6),     # m/s
           'alfven_speed': (1e4, 1e6),      # m/s  
           'plasma_frequency': (1e3, 1e5),  # Hz
           'plasma_beta': (1e-3, 1e2),      # dimensionless
       }
       
       if calculation_type not in expected_ranges:
           return {'valid': True, 'warnings': []}
       
       min_val, max_val = expected_ranges[calculation_type]
       
       # Check for NaN/Inf values
       finite_mask = np.isfinite(results)
       if not finite_mask.all():
           non_finite_count = (~finite_mask).sum()
           return {
               'valid': False,
               'warnings': [f"{non_finite_count} non-finite results in {calculation_type}"]
           }
       
       # Check physical ranges
       range_mask = (results >= min_val) & (results <= max_val)
       if not range_mask.all():
           out_of_range_count = (~range_mask).sum()
           return {
               'valid': False,
               'warnings': [f"{out_of_range_count} {calculation_type} results outside expected range [{min_val}, {max_val}]"]
           }
       
       return {'valid': True, 'warnings': []}

Error Detection and Recovery
============================

Systematic Error Checking
~~~~~~~~~~~~~~~~~~~~~~~~~~

**NaN Detection and Handling**

.. code-block:: python

   def handle_calculation_errors(results, calculation_name):
       """Systematic error detection and user guidance."""
       
       # Check for NaN values
       nan_mask = np.isnan(results)
       if nan_mask.any():
           nan_count = nan_mask.sum()
           print(f"Warning: {nan_count} NaN values in {calculation_name}")
           print("Possible causes:")
           print("- Negative input values (temperature, energy)")
           print("- Invalid mathematical operations (sqrt of negative)")
           print("- Data corruption or measurement errors")
           return results[~nan_mask]  # Return only valid values
       
       # Check for infinite values
       inf_mask = np.isinf(results)
       if inf_mask.any():
           inf_count = inf_mask.sum()
           print(f"Warning: {inf_count} infinite values in {calculation_name}")
           print("Possible causes:")
           print("- Division by zero (zero density in Alfvén speed)")
           print("- Overflow in exponential calculations")
           print("- Extreme parameter values")
           return results[~inf_mask]  # Return only finite values
       
       return results

**Automatic Recovery Procedures**

.. code-block:: python

   def robust_thermal_speed(plasma_data, recovery_mode='filter'):
       """Calculate thermal speeds with automatic error recovery."""
       
       # Step 1: Input validation
       valid_temp = plasma_data.temperature > 0
       if not valid_temp.all():
           print(f"Filtering {(~valid_temp).sum()} invalid temperatures")
           if recovery_mode == 'filter':
               plasma_data = plasma_data[valid_temp]
           elif recovery_mode == 'replace':
               # Replace invalid with median
               plasma_data.temperature[~valid_temp] = plasma_data.temperature[valid_temp].median()
       
       # Step 2: Calculation with error handling
       try:
           thermal_speeds = plasma_data.thermal_speed()
       except Exception as e:
           print(f"Calculation failed: {e}")
           return None
       
       # Step 3: Result validation
       validation = validate_calculation_results(thermal_speeds, 'thermal_speed')
       if not validation['valid']:
           print("Result validation warnings:")
           for warning in validation['warnings']:
               print(f"  - {warning}")
       
       return thermal_speeds

Performance vs. Precision Trade-offs
=====================================

Optimization Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Memory Usage**
   Large datasets may require precision trade-offs for memory efficiency.

   .. code-block:: python

      # Memory-efficient processing for large datasets
      def process_large_dataset(plasma_data, chunk_size=10000):
          """Process large datasets in chunks to maintain precision."""
          
          results = []
          for i in range(0, len(plasma_data), chunk_size):
              chunk = plasma_data[i:i+chunk_size]
              
              # Validate chunk
              validation = validate_physics_parameters(chunk)
              if validation['valid_fraction'] < 0.9:
                  print(f"Chunk {i//chunk_size}: Low valid fraction ({validation['valid_fraction']:.2f})")
              
              # Process valid data only
              valid_chunk = chunk[validation['valid_mask']]
              chunk_results = valid_chunk.thermal_speed()
              results.append(chunk_results)
          
          return pd.concat(results)

**Precision Preservation**
   Maintain numerical accuracy in complex calculations.

   .. code-block:: python

      # Use appropriate algorithms for numerical stability
      from scipy.special import logsumexp
      
      # Instead of: exp(a) + exp(b) + exp(c) (overflow risk)
      # Use: exp(logsumexp([a, b, c])) (numerically stable)

Best Practices Summary
======================

Input Validation Checklist
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before any physics calculation:

1. ✅ **Check for positive physical quantities**
   - Temperature > 0 K
   - Density > minimum_threshold
   - Energy > 0

2. ✅ **Validate parameter ranges**
   - Within instrument measurement ranges  
   - Consistent with physical expectations
   - No extreme values that could cause overflow

3. ✅ **Apply quality filters**
   - Remove flagged data points
   - Filter measurement uncertainties
   - Apply temporal consistency checks

Result Validation Checklist
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After physics calculations:

1. ✅ **Check for mathematical errors**
   - No NaN values in results
   - No infinite values
   - All results are finite numbers

2. ✅ **Validate physical ranges**  
   - Results within expected bounds
   - Consistent with literature values
   - Reasonable for solar wind conditions

3. ✅ **Cross-validate results**
   - Compare with alternative methods
   - Check internal consistency
   - Verify with established benchmarks

Long-term Data Quality
~~~~~~~~~~~~~~~~~~~~~~

For ongoing analysis projects:

1. **Document validation procedures** used
2. **Track validation statistics** over time
3. **Monitor parameter distributions** for anomalies
4. **Implement automated quality checks** in analysis pipelines

Troubleshooting Guide
=====================

Common Error Messages
~~~~~~~~~~~~~~~~~~~~~

**"RuntimeWarning: invalid value encountered in sqrt"**
   - **Cause**: Attempting square root of negative values
   - **Solution**: Validate inputs are positive before calculation
   - **Prevention**: Use temperature/energy validation functions

**"RuntimeWarning: divide by zero encountered"**  
   - **Cause**: Zero density in Alfvén speed or similar calculations
   - **Solution**: Apply minimum density threshold
   - **Prevention**: Systematic density validation

**"Results contain NaN values"**
   - **Cause**: Invalid mathematical operations in calculation chain
   - **Solution**: Trace back to identify source of invalid inputs
   - **Prevention**: Comprehensive input validation framework

**"Results outside expected physical range"**
   - **Cause**: Extreme parameter values or measurement errors
   - **Solution**: Apply physical bounds checking and data filtering
   - **Prevention**: Implement systematic data quality procedures

Getting Help
~~~~~~~~~~~~

If you encounter numerical stability issues:

1. **Check this guide** for common solutions
2. **Review input data** for measurement anomalies  
3. **Consult physics literature** for expected parameter ranges
4. **Report persistent issues** to SolarWindPy developers with minimal reproducible examples

Advanced Topics
===============

Custom Validation Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For specialized analysis needs, implement custom validation:

.. code-block:: python

   def custom_solar_wind_validation(plasma_data):
       """Custom validation for specific solar wind conditions."""
       
       # Example: Validate for high-speed stream analysis
       velocity_threshold = 500e3  # m/s
       high_speed_mask = plasma_data.velocity.magnitude() > velocity_threshold
       
       # Apply stricter validation for high-speed conditions
       if high_speed_mask.any():
           # Require higher precision for extreme conditions
           min_density = 1e-22  # kg/m³ (stricter)
           temp_range = (1e5, 1e7)  # K (narrower range)
           
           # Custom validation logic
           # ...
       
       return validation_results

Precision Monitoring
~~~~~~~~~~~~~~~~~~~~

Track numerical precision throughout analysis:

.. code-block:: python

   def precision_monitor(calculation_func, *args, **kwargs):
       """Monitor numerical precision of calculations."""
       
       # Perform calculation with monitoring
       start_precision = np.finfo(np.float64).eps
       
       result = calculation_func(*args, **kwargs)
       
       # Estimate precision loss
       relative_error = np.abs((result - expected_result) / expected_result)
       precision_loss = relative_error / start_precision
       
       if precision_loss.max() > 1e6:
           print(f"Warning: Significant precision loss detected (factor of {precision_loss.max():.1e})")
       
       return result, precision_loss

This guide provides the foundation for numerically robust plasma physics analysis
with SolarWindPy. Always prioritize validation and verification for scientific accuracy.