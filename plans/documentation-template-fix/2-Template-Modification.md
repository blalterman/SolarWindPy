# Phase 2: Template Modification

## Objective
Enhance existing Sphinx templates and create new templates to support physics-specific documentation needs while maintaining full persistence across documentation rebuilds.

## Implementation Strategy

### Template Enhancement Approach
1. **Incremental Enhancement**: Modify existing templates step-by-step
2. **Physics-First Design**: Prioritize scientific documentation needs  
3. **Backward Compatibility**: Ensure existing documentation continues working
4. **Validation Integration**: Include template validation at each step

## Template Modifications

### 2.1 Enhanced Class Template

#### Target: `docs/source/_templates/autosummary/class.rst`

**Current Template Problems**:
- Generic structure not optimized for scientific classes
- No support for physics-specific properties
- Missing units and mathematical relationship documentation
- No validation or constraint information

**Enhanced Template Design**:

```rst
{{ fullname | escape | underline }}

.. autoclass:: {{ fullname }}
   :members:
   :show-inheritance:
   :no-index:

   {% if "Plasma" in objname or "Ion" in objname or "Base" in objname %}
   
   .. rubric:: Physics Overview
   
   {{ objname }} represents {{ overview_text | default("a physics object in the solar wind analysis framework") }}.
   
   {% endif %}

   .. rubric:: Methods

   .. autosummary::
      :nosignatures:
   {% for item in methods %}
      {{ item }}
   {%- endfor %}

   .. rubric:: Attributes

   .. autosummary::
   {% for item in attributes %}
      {{ item }}
   {%- endfor %}

   {% if "Plasma" in objname or "Ion" in objname %}
   
   .. rubric:: Physical Properties
   
   The following properties represent derived physical quantities:
   
   .. autosummary::
   {% for item in attributes %}
   {%- if "temperature" in item.lower() or "density" in item.lower() or "velocity" in item.lower() or "pressure" in item.lower() %}
      {{ item }}
   {%- endif %}
   {%- endfor %}

   .. rubric:: Units and Dimensions
   
   This class follows SI units internally with the following conventions:
   
   * **Temperature**: Kelvin (K)
   * **Density**: particles per cubic meter (m⁻³)
   * **Velocity**: meters per second (m/s)
   * **Magnetic field**: Tesla (T)
   * **Pressure**: Pascal (Pa)

   {% endif %}

   {% if methods and any("fit" in method.lower() or "calculate" in method.lower() for method in methods) %}
   
   .. rubric:: Mathematical Relationships
   
   Key equations implemented by this class:
   
   .. note::
      Detailed mathematical formulations are documented in the individual method docstrings.
      
   {% endif %}

   {% if "validate" in " ".join(methods).lower() or "check" in " ".join(methods).lower() %}
   
   .. rubric:: Physics Constraints
   
   This class enforces physical constraints and validation rules. See validation methods for details.
   
   {% endif %}
```

**Key Enhancements**:
1. **Physics Overview**: Context for scientific classes
2. **Physical Properties**: Separate section for derived quantities
3. **Units and Dimensions**: Clear unit documentation
4. **Mathematical Relationships**: Formula documentation support
5. **Physics Constraints**: Validation rule documentation
6. **Conditional Sections**: Only show relevant sections for physics classes

#### Implementation Steps

**Step 2.1.1**: Create enhanced class template
```bash
# Backup current template
cp docs/source/_templates/autosummary/class.rst docs/source/_templates/autosummary/class.rst.backup

# Implement enhanced version
# Edit docs/source/_templates/autosummary/class.rst with enhanced content
```

**Step 2.1.2**: Test template with sample class
```bash
cd docs
make clean
make api
make html
# Verify enhanced documentation appears for physics classes
```

**Step 2.1.3**: Validate template syntax
```bash
# Check for Jinja2 template errors
python -c "
from jinja2 import Template
with open('docs/source/_templates/autosummary/class.rst') as f:
    Template(f.read())
print('Template syntax valid')
"
```

### 2.2 Enhanced Module Template

#### Target: `docs/source/_templates/autosummary/module.rst`

**Current Template Problems**:
- No scientific context for physics modules
- Missing physics background information
- No mathematical overview
- Generic structure for all modules

**Enhanced Template Design**:

```rst
{{ fullname | escape | underline }}

{% set module_parts = fullname.split('.') %}
{% set module_name = module_parts[-1] %}

{% if "core" in fullname %}
.. note::
   This module contains core physics classes and functions for solar wind analysis.
   
{% elif "plotting" in fullname %}
.. note::
   This module provides visualization tools specialized for plasma physics data.
   
{% elif "fitfunctions" in fullname %}
.. note::
   This module contains mathematical fitting functions commonly used in plasma physics analysis.
   
{% elif "instabilities" in fullname %}
.. note::
   This module implements plasma instability analysis and detection algorithms.
   
{% elif "tools" in fullname %}
.. note::
   This module provides utility functions for physical calculations and data processing.
   
{% endif %}

.. automodule:: {{ fullname }}
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

{% if "plasma" in module_name.lower() %}

.. rubric:: Physics Background

The plasma module provides the fundamental framework for representing and analyzing 
solar wind plasma measurements. It implements the multi-species plasma model with
full electromagnetic field interactions.

**Key Physical Concepts**:

* Multi-species ion composition (protons, alpha particles, heavy ions)
* Magnetic field vector representation and derived quantities  
* Plasma moments (density, velocity, temperature, pressure)
* Thermal properties and distribution functions

{% elif "ions" in module_name.lower() %}

.. rubric:: Physics Background

Ion species representation in solar wind plasma, implementing individual ion
properties and collective behavior analysis.

**Physical Properties**:

* Ion moments computed from distribution functions
* Species-specific thermal properties
* Composition ratios and charge states
* Flow velocities and differential streaming

{% elif module_name.lower() in ["gaussians", "exponentials", "power_laws", "lines"] %}

.. rubric:: Mathematical Background

This module implements {{ module_name.replace('_', ' ').title() }} fitting functions
commonly used in plasma physics data analysis.

**Applications**:

* Plasma distribution function fitting
* Spectral analysis and peak identification
* Background subtraction and trend removal
* Statistical analysis of plasma parameters

{% endif %}

{% if "examples" in globals() or "usage" in globals() %}

.. rubric:: Usage Examples

Basic usage patterns for this module:

.. code-block:: python

   import solarwindpy as swp
   
   # Module-specific usage examples would be inserted here
   # Based on the specific module being documented

{% endif %}
```

**Key Enhancements**:
1. **Scientific Context**: Module-specific physics background
2. **Mathematical Background**: For fitting and analysis modules
3. **Usage Guidance**: Physics-relevant examples
4. **Conditional Content**: Tailored to module purpose
5. **Cross-references**: Links to related physics concepts

#### Implementation Steps

**Step 2.2.1**: Create enhanced module template
```bash
# Backup current template
cp docs/source/_templates/autosummary/module.rst docs/source/_templates/autosummary/module.rst.backup

# Implement enhanced version
```

**Step 2.2.2**: Test with core physics modules
```bash
make clean
make api
# Verify physics background sections appear correctly
```

### 2.3 New Function Template

#### Target: `docs/source/_templates/autosummary/function.rst` (NEW)

**Rationale**: Standalone physics functions need specialized documentation

**Function Template Design**:

```rst
{{ fullname | escape | underline }}

.. autofunction:: {{ fullname }}
   :no-index:

{% set func_name = objname.lower() %}

{% if "calculate" in func_name or "compute" in func_name %}

.. rubric:: Mathematical Implementation

This function implements a physics calculation with the following characteristics:

* **Input Parameters**: Physical quantities with specified units
* **Output**: Computed physical quantity with units
* **Validation**: Input parameter validation for physical constraints
* **Precision**: Numerical precision considerations for physics applications

{% endif %}

{% if "convert" in func_name or "transform" in func_name %}

.. rubric:: Unit Conversion

This function performs unit conversion or coordinate transformation:

* **Input Units**: {{ input_units | default("See function signature") }}
* **Output Units**: {{ output_units | default("See function signature") }}  
* **Conversion Factor**: Based on fundamental physical constants
* **Accuracy**: Maintains numerical precision for scientific applications

{% endif %}

{% if "validate" in func_name or "check" in func_name %}

.. rubric:: Physics Validation

This function enforces physics constraints and validation rules:

* **Physical Limits**: Validates parameters against known physical bounds
* **Consistency Checks**: Ensures internal consistency of related quantities
* **Error Handling**: Provides clear physics-based error messages
* **Performance**: Optimized for real-time data validation

{% endif %}

.. rubric:: Usage Notes

.. important::
   This function follows SolarWindPy conventions for units and data structures.
   See the main documentation for details on the physics framework.
   
{% if "deprecated" in (doc | default("")).lower() %}

.. deprecated:: 
   This function is deprecated. See the function docstring for recommended alternatives.
   
{% endif %}
```

**Key Features**:
1. **Mathematical Implementation**: Formula and calculation details
2. **Unit Conversion**: Input/output unit documentation
3. **Physics Validation**: Constraint and validation information
4. **Usage Notes**: Integration with SolarWindPy framework
5. **Deprecation Support**: Clear migration guidance

#### Implementation Steps

**Step 2.3.1**: Create function template
```bash
# Create new function template
touch docs/source/_templates/autosummary/function.rst
# Implement function template content
```

**Step 2.3.2**: Configure Sphinx to use function template
```python
# Add to docs/source/conf.py
autosummary_context = {
    'function': 'function.rst'
}
```

### 2.4 Enhanced Package Template

#### Target: Override default package documentation

**Package Overview Enhancement**:

```rst
{{ fullname | escape | underline }}

{% set package_name = fullname.split('.')[-1] %}

{% if package_name == "core" %}

.. rubric:: Core Physics Framework

The core package provides fundamental classes and functions for solar wind plasma analysis.
This package implements the mathematical and physical foundations for all other modules.

**Primary Components**:

* :py:class:`~solarwindpy.core.plasma.Plasma` - Multi-species plasma container
* :py:class:`~solarwindpy.core.ions.Ion` - Individual ion species representation
* :py:class:`~solarwindpy.core.base.Base` - Abstract base with logging and constants

**Physics Implementation**:

* SI units used internally throughout
* Consistent handling of missing data (NaN)
* Thermal speed convention: mw² = 2kT
* Time series data with chronological ordering

{% elif package_name == "plotting" %}

.. rubric:: Plasma Physics Visualization

Specialized plotting tools for solar wind and plasma physics data visualization,
providing publication-quality figures with proper scientific formatting.

**Capabilities**:

* Multi-dimensional plasma parameter visualization
* Time series plotting with physics-aware formatting
* Statistical distribution analysis plots
* Correlation and scatter analysis tools

{% elif package_name == "fitfunctions" %}

.. rubric:: Mathematical Fitting Framework

Mathematical functions for fitting plasma physics data, implementing common
distribution functions and trend analysis tools used in space physics research.

**Function Categories**:

* Gaussian distributions for velocity/temperature analysis
* Power laws for spectral and scaling analysis
* Exponential functions for decay processes
* Linear trends for background subtraction

{% elif package_name == "instabilities" %}

.. rubric:: Plasma Instability Analysis

Implementation of plasma instability detection and analysis algorithms,
providing tools for identifying and characterizing various plasma wave modes
and instabilities in solar wind data.

{% endif %}

.. toctree::
   :maxdepth: 2

{% for item in modules %}
   {{ item }}
{%- endfor %}

{% for item in subpackages %}
   {{ item }}
{%- endfor %}
```

**Key Features**:
1. **Package Overview**: Clear scientific context
2. **Physics Implementation**: Technical details
3. **Cross-references**: Links to key classes/functions
4. **Hierarchical Organization**: Proper package structure

## Template Validation Strategy

### 2.5 Template Testing Framework

**Validation Approach**:
1. **Syntax Validation**: Jinja2 template syntax checking
2. **Build Testing**: Generate documentation and verify output
3. **Content Verification**: Ensure all sections render correctly
4. **Cross-reference Testing**: Verify all links work
5. **Physics Content Review**: Validate scientific accuracy

**Automated Testing Script**:

```python
# docs/validate_templates.py
"""Template validation script for SolarWindPy documentation."""

import os
import sys
from pathlib import Path
from jinja2 import Template, TemplateSyntaxError

def validate_template(template_path):
    """Validate a single template file."""
    try:
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        # Test template syntax
        Template(template_content)
        print(f"✅ {template_path}: Syntax valid")
        return True
        
    except TemplateSyntaxError as e:
        print(f"❌ {template_path}: Syntax error - {e}")
        return False
    except Exception as e:
        print(f"❌ {template_path}: Error - {e}")
        return False

def main():
    """Validate all templates."""
    template_dir = Path("docs/source/_templates/autosummary")
    templates = list(template_dir.glob("*.rst"))
    
    print("🔍 Validating documentation templates...")
    
    valid_count = 0
    for template in templates:
        if validate_template(template):
            valid_count += 1
    
    print(f"\n📊 Results: {valid_count}/{len(templates)} templates valid")
    
    if valid_count == len(templates):
        print("✅ All templates are valid!")
        return 0
    else:
        print("❌ Some templates have errors")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### 2.6 Implementation Timeline

**Template Modification Schedule**:

| Task | Duration | Dependencies | Validation |
|------|----------|--------------|------------|
| **Enhanced Class Template** | 45 min | Phase 1 analysis | Syntax + build test |
| **Enhanced Module Template** | 30 min | Class template | Build test |  
| **Function Template Creation** | 30 min | Module template | Syntax + integration |
| **Package Template Enhancement** | 20 min | All templates | Full build test |
| **Template Validation Framework** | 25 min | All templates | Automated testing |
| **Integration Testing** | 30 min | All components | Full documentation build |

**Total Phase 2 Time**: 3 hours

## Success Criteria

### Template Enhancement Validation

- [ ] **Enhanced class template** renders physics sections for core classes
- [ ] **Enhanced module template** shows scientific context appropriately  
- [ ] **Function template** provides physics-specific documentation
- [ ] **Package template** creates proper scientific overview
- [ ] **Template validation** passes all syntax and build tests
- [ ] **Full documentation build** completes without errors or warnings

### Physics Documentation Quality

- [ ] **Units and dimensions** clearly documented for all physical quantities
- [ ] **Mathematical relationships** properly formatted with LaTeX support
- [ ] **Physics constraints** documented for validation methods
- [ ] **Scientific context** provided for all major components
- [ ] **Cross-references** work correctly between related physics concepts

### Persistence Verification

- [ ] **Template changes persist** across multiple documentation rebuilds
- [ ] **Generated documentation** shows enhanced content consistently
- [ ] **CI/CD builds** incorporate template enhancements automatically
- [ ] **No manual intervention** required to maintain enhancements

## Commit Tracking

- Template backup creation: `<checksum_template_backup>`
- Enhanced class template: `<checksum_class_template>`
- Enhanced module template: `<checksum_module_template>`
- Function template creation: `<checksum_function_template>`
- Package template enhancement: `<checksum_package_template>`
- Validation framework: `<checksum_validation_framework>`
- Phase 2 completion: `<checksum_phase2_complete>`

## Risk Mitigation

### Template Modification Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Template syntax errors** | Low | High | Validation script + testing |
| **Build failures** | Low | Medium | Incremental testing |
| **Content formatting issues** | Medium | Low | Visual review process |
| **Physics accuracy errors** | Low | High | Scientific review |

### Rollback Strategy

```bash
# Emergency rollback procedure
cd docs/source/_templates/autosummary/

# Restore from backups
mv class.rst.backup class.rst
mv module.rst.backup module.rst

# Remove new templates if problematic
rm -f function.rst

# Rebuild documentation
cd ../../..
make clean
make html
```

## Next Phase Preparation

Phase 3 (Build System Integration) should address:
1. **Post-processing enhancements** for template-generated content
2. **Build system optimization** for improved template performance
3. **CI/CD integration validation** to ensure automated builds work
4. **Additional processing steps** for physics-specific content
5. **Performance optimization** for large-scale documentation generation

The enhanced templates provide the foundation for persistent, physics-aware documentation that will significantly improve the quality and usability of SolarWindPy's documentation system.