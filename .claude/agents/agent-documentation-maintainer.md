---
name: DocumentationMaintainer
description: Maintains comprehensive documentation including docstrings, API docs, and user guides
priority: medium
tags:
  - documentation
  - sphinx
  - docstrings
  - api
applies_to:
  - docs/**/*.rst
  - "**/*.py"
  - README.rst
---

# DocumentationMaintainer Agent

## Purpose
Ensures comprehensive, accurate, and well-maintained documentation across all levels of the SolarWindPy package.

## Key Responsibilities

### NumPy-Style Docstrings
```python
def plasma_beta(density, temperature, magnetic_field):
    """Calculate plasma beta parameter.
    
    Plasma beta is the ratio of thermal pressure to magnetic pressure,
    indicating whether thermal or magnetic forces dominate.
    
    Parameters
    ----------
    density : array_like
        Number density in particles/cm³
    temperature : array_like
        Temperature in Kelvin
    magnetic_field : array_like
        Magnetic field magnitude in nT
    
    Returns
    -------
    beta : ndarray
        Plasma beta (dimensionless)
    
    See Also
    --------
    alfven_speed : Calculate Alfvén wave speed
    thermal_pressure : Calculate thermal pressure
    
    Notes
    -----
    The plasma beta is calculated as:
    
    .. math::
        \\beta = \\frac{2\\mu_0 n k_B T}{B^2}
    
    where :math:`\\mu_0` is the permeability of free space,
    :math:`n` is number density, :math:`k_B` is Boltzmann constant,
    :math:`T` is temperature, and :math:`B` is magnetic field.
    
    Examples
    --------
    >>> import numpy as np
    >>> n = np.array([5.0, 10.0])  # cm⁻³
    >>> T = np.array([1e5, 2e5])   # K
    >>> B = np.array([5.0, 10.0])  # nT
    >>> beta = plasma_beta(n, T, B)
    >>> print(beta)
    [0.69 0.69]
    
    References
    ----------
    .. [1] Baumjohann, W. and Treumann, R.A., 1996. Basic space plasma
           physics. Imperial College Press.
    
    Raises
    ------
    ValueError
        If input arrays have incompatible shapes
    ZeroDivisionError
        If magnetic_field contains zeros
    """
    # Implementation
    pass
```

### Class Documentation
```python
class Plasma(Base):
    """Container for plasma measurements and derived quantities.
    
    The Plasma class provides a unified interface for working with
    multi-species plasma data from in-situ measurements.
    
    Parameters
    ----------
    data : pd.DataFrame
        Plasma measurements with MultiIndex columns ('M', 'C', 'S')
    *species : str
        Variable number of species identifiers (e.g., 'p1', 'a')
    spacecraft : Spacecraft, optional
        Associated spacecraft trajectory data
    
    Attributes
    ----------
    ions : dict
        Dictionary of Ion objects keyed by species
    b : Vector
        Magnetic field vector
    data : pd.DataFrame
        Underlying measurement data
    
    Methods
    -------
    nc()
        Calculate Coulomb number
    beta()
        Calculate plasma beta
    export(filename)
        Export data to file
    
    Examples
    --------
    Basic usage:
    
    >>> plasma = Plasma(data, 'p1', 'a')
    >>> protons = plasma.p1  # Access proton Ion
    >>> beta = plasma.beta()  # Calculate plasma beta
    
    With spacecraft data:
    
    >>> plasma = Plasma(data, 'p1', spacecraft=sc)
    >>> coulomb = plasma.nc()  # Requires spacecraft
    """
```

## Sphinx Documentation

### Module Documentation (RST)
```rst
Core Module
===========

.. automodule:: solarwindpy.core
   :members:
   :undoc-members:
   :show-inheritance:

The core module provides fundamental classes for solar wind analysis:

.. toctree::
   :maxdepth: 2
   
   core.plasma
   core.ions
   core.spacecraft
   core.base

Key Concepts
------------

Data Structure
~~~~~~~~~~~~~~

All data uses pandas DataFrames with three-level MultiIndex columns:

* **M** - Measurement type (n, v, w, T, b)
* **C** - Vector component (x, y, z) or empty for scalars  
* **S** - Species (p1, p2, a) or empty for magnetic field

Physical Units
~~~~~~~~~~~~~~

Internal calculations use SI units:

* Density: particles/m³
* Velocity: m/s
* Temperature: Kelvin
* Magnetic field: Tesla

Display units are converted as needed:

* Density: cm⁻³
* Velocity: km/s
* Magnetic field: nT
```

### API Reference Generation
```python
# docs/source/conf.py
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',  # NumPy/Google style docstrings
    'sphinx.ext.intersphinx',
    'sphinx.ext.mathjax',  # Math rendering
    'sphinx.ext.viewcode',  # Source links
    'sphinx.ext.autosummary',
]

# Napoleon settings for NumPy style
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False

# Autosummary settings
autosummary_generate = True
autosummary_imported_members = False
```

## Usage Examples

### Inline Code Examples
```python
def process_data(plasma):
    """Process plasma data with examples.
    
    Examples
    --------
    Load and process data:
    
    >>> plasma = load_plasma('data.csv')
    >>> plasma = remove_outliers(plasma)
    >>> plasma = interpolate_gaps(plasma)
    
    Calculate derived quantities:
    
    >>> beta = plasma.beta()
    >>> print(f"Mean beta: {beta.mean():.2f}")
    Mean beta: 1.23
    """
```

### Jupyter Notebook Integration
```python
def export_notebook_examples():
    """Export documentation notebooks."""
    notebooks = [
        'getting_started.ipynb',
        'data_loading.ipynb',
        'analysis_examples.ipynb',
        'plotting_gallery.ipynb'
    ]
    
    for nb in notebooks:
        # Convert to RST for docs
        os.system(f'jupyter nbconvert --to rst {nb}')
```

## Documentation Standards

### Docstring Checklist
- [ ] One-line summary (imperative mood)
- [ ] Extended description if needed
- [ ] Parameters section with types
- [ ] Returns section with types
- [ ] Raises section for exceptions
- [ ] Examples section with doctests
- [ ] See Also for related functions
- [ ] Notes for technical details
- [ ] References for citations

### Mathematical Notation
```python
r"""Calculate instability threshold.

The threshold is given by:

.. math::
    \gamma = \frac{\omega_p}{\Omega_c} \sqrt{\frac{T_\perp}{T_\parallel} - 1}

where :math:`\omega_p` is plasma frequency and :math:`\Omega_c` is
cyclotron frequency.
"""
```

## Documentation Testing

### Doctest Integration
```python
def run_doctests():
    """Run doctests in all modules."""
    import doctest
    import solarwindpy
    
    results = doctest.testmod(solarwindpy, verbose=True)
    
    if results.failed > 0:
        raise ValueError(f"{results.failed} doctests failed")
```

### Example Validation
```python
import pytest

@pytest.mark.doctest
def test_docstring_examples():
    """Validate all docstring examples run correctly."""
    import doctest
    import glob
    
    for module_file in glob.glob('solarwindpy/**/*.py', recursive=True):
        module = import_module_from_file(module_file)
        results = doctest.testmod(module)
        assert results.failed == 0
```

## Documentation Building

### Build Commands
```bash
# Build HTML documentation
cd docs
make clean
make html

# Build PDF documentation  
make latexpdf

# Check for broken links
make linkcheck

# Spell check
make spelling
```

### Automated Checks
```python
def check_documentation():
    """Verify documentation completeness."""
    issues = []
    
    # Check for missing docstrings
    for obj in inspect.getmembers(module):
        if callable(obj) and not obj.__doc__:
            issues.append(f"Missing docstring: {obj.__name__}")
    
    # Check parameter documentation
    for func in get_public_functions():
        params = inspect.signature(func).parameters
        doc_params = parse_docstring_params(func.__doc__)
        
        for param in params:
            if param not in doc_params:
                issues.append(f"Undocumented parameter: {func.__name__}.{param}")
    
    return issues
```

## Cross-References

### Internal Links
```python
"""See :class:`~solarwindpy.core.plasma.Plasma` for details.

Related functions:

* :func:`~solarwindpy.core.ions.Ion.thermal_speed`
* :meth:`~solarwindpy.core.plasma.Plasma.beta`
"""
```

### External Links
```python
"""Based on method from [Verscharen2016]_.

.. [Verscharen2016] Verscharen, D., et al. (2016). 
   "Ion-scale turbulence in the solar wind."
   Research in Astronomy and Astrophysics, 16(5), 029.
   https://doi.org/10.1088/1674-4527/16/5/029
"""
```

## Integration Points

- Coordinates with **TestEngineer** for doctest validation
- References physics from **PhysicsValidator**
- Documents patterns from **DataFrameArchitect**
- Includes performance notes from **PerformanceOptimizer**

## Common Issues

1. **Outdated Examples**: Update when API changes
2. **Math Rendering**: Ensure LaTeX syntax is correct
3. **Cross-References**: Verify links after refactoring
4. **Parameter Types**: Keep synchronized with type hints
5. **Build Warnings**: Address all Sphinx warnings

## Best Practices

1. Write documentation as you code
2. Include practical examples
3. Explain the "why" not just "what"
4. Keep examples runnable
5. Document assumptions and limitations
6. Use consistent terminology
7. Provide context for physics/math
8. Link to papers for algorithms