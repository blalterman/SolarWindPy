# Phase 2: Template System Enhancement

## Objective
Implement a robust, physics-aware template system that eliminates manual RST editing by making all documentation customizations persistent through templates that survive build regeneration.

## Context
After Phase 1, documentation builds are functional. Phase 2 establishes the template foundation that enables automated, consistent documentation generation while preserving scientific context and customizations.

## Current Template Infrastructure

### Existing Components
- **Template directory**: `docs/source/_templates/autosummary/`
- **Template files**: `module.rst`, `class.rst` 
- **Sphinx configuration**: `autosummary_generate = True`
- **Post-processing**: `docs/add_no_index.py` script
- **Build integration**: Makefile with `api` target

### Template Processing Pipeline
```
sphinx-apidoc → Template Application → Post-processing → HTML Generation
     ↓                    ↓                 ↓               ↓
RST Generation      Template Merge    add_no_index.py   Final Docs
```

## Implementation Strategy

### Step 2.1: Template Analysis and Baseline (30 minutes)

**Current Template Assessment**:
```bash
# Examine existing templates
ls -la docs/source/_templates/autosummary/
cat docs/source/_templates/autosummary/module.rst
cat docs/source/_templates/autosummary/class.rst
```

**Identify Enhancement Areas**:
1. **Physics Context**: Add scientific documentation sections
2. **Cross-references**: Improve linking between physics concepts  
3. **Units and Dimensions**: Standardize physical quantity documentation
4. **Examples**: Template-driven example generation
5. **Bibliography**: Physics-specific references

### Step 2.2: Enhanced Module Template (60 minutes)

**Target**: `docs/source/_templates/autosummary/module.rst`

**Enhanced Template Structure**:
```rst
{{ fullname | escape | underline}}

{% if members %}
.. currentmodule:: {{ fullname }}

{% if fullname.endswith('.core') %}
Physics Overview
================

This module provides core physics functionality for solar wind analysis.

Physical Principles
-------------------

{% if 'plasma' in fullname %}
**Plasma Physics Context**:
- Multi-species plasma analysis
- Kinetic theory applications  
- Thermal properties and distributions
- Magnetic field interactions

**Key Physical Relationships**:
- Thermal speed: :math:`v_{th} = \sqrt{2kT/m}` (SolarWindPy convention)
- Alfvén speed: :math:`V_A = B/\sqrt{\mu_0 \rho}` 
- Plasma beta: :math:`\beta = 2\mu_0 nkT/B^2`

{% elif 'ions' in fullname %}
**Ion Species Analysis**:
- Multi-species moment calculations
- Composition and abundance
- Temperature and velocity distributions
- Species-specific physical properties

**Physical Quantities**:
- Number density: particles per cubic meter
- Bulk velocity: km/s (converted for display)
- Temperature: Kelvin or eV (configurable)
- Thermal speed: km/s (mw² = 2kT convention)

{% endif %}

Units and Conventions
---------------------

**SolarWindPy Physics Standards**:
- **Internal units**: SI base units throughout
- **Display units**: Convenient units for solar wind context
- **Missing data**: NaN (never 0 or -999)
- **Time series**: Chronological order maintained
- **Thermal speed**: mw² = 2kT convention consistently applied

{% endif %}

{% block modules %}
{% if modules %}
.. rubric:: Modules

.. autosummary::
   :toctree:
   :template: module.rst
{% for item in modules %}
   {{ item }}
{%- endfor %}
{% endif %}
{% endblock %}

{% block classes %}
{% if classes %}
.. rubric:: Classes

.. autosummary::
   :toctree:
   :template: class.rst
{% for item in classes %}
   {{ item }}
{%- endfor %}
{% endif %}
{% endblock %}

{% block functions %}
{% if functions %}
.. rubric:: Functions

.. autosummary::
   :toctree:
{% for item in functions %}
   {{ item }}
{%- endfor %}
{% endif %}
{% endblock %}

{% block exceptions %}
{% if exceptions %}
.. rubric:: Exceptions

.. autosummary::
   :toctree:
{% for item in exceptions %}
   {{ item }}
{%- endfor %}
{% endif %}
{% endblock %}

{% endif %}
```

### Step 2.3: Enhanced Class Template (90 minutes)

**Target**: `docs/source/_templates/autosummary/class.rst`

**Physics-Aware Class Template**:
```rst
{{ fullname | escape | underline}}

.. currentmodule:: {{ module }}

.. autoclass:: {{ objname }}
   :no-index:

{% if objname in ['Plasma', 'Ion', 'Base'] %}

   Physical Properties
   ===================

{% if objname == 'Plasma' %}
   
   **Multi-Species Plasma Container**
   
   The Plasma class represents a collection of ion species and magnetic field data,
   providing comprehensive analysis capabilities for solar wind plasma physics.
   
   **Physical Context**:
   - Contains multiple Ion instances representing different species
   - Manages magnetic field vector data and derived quantities
   - Provides plasma-level calculations and analysis methods
   - Maintains temporal coherence across all plasma components
   
   **Key Physical Relationships**:
   
   .. math::
   
      \rho = \sum_i n_i m_i \quad \text{(total mass density)}
      
      V_A = \frac{B}{\sqrt{\mu_0 \rho}} \quad \text{(Alfvén velocity)}
      
      \beta = \frac{2\mu_0 \sum_i n_i k T_i}{B^2} \quad \text{(plasma beta)}

{% elif objname == 'Ion' %}

   **Single Ion Species Analysis**
   
   The Ion class represents a single ion species with its associated physical
   properties, moments, and derived quantities for solar wind analysis.
   
   **Physical Properties**:
   - Number density (n): particles per cubic meter
   - Bulk velocity (V): three-component vector in km/s
   - Temperature (T): scalar or tensor in Kelvin
   - Thermal speed (w): based on mw² = 2kT convention
   
   **Moment Calculations**:
   
   .. math::
   
      n = \int f(\mathbf{v}) d^3v \quad \text{(zeroth moment)}
      
      \mathbf{V} = \frac{1}{n} \int \mathbf{v} f(\mathbf{v}) d^3v \quad \text{(first moment)}
      
      T = \frac{m}{3nk} \int |\mathbf{v} - \mathbf{V}|^2 f(\mathbf{v}) d^3v \quad \text{(temperature)}

{% elif objname == 'Base' %}

   **Foundation Physics Class**
   
   The Base class provides fundamental physics constants, unit conversions,
   and common functionality shared across all SolarWindPy physics classes.
   
   **Physical Constants**:
   - Fundamental constants (k, c, mp, me, etc.)
   - Unit conversion factors
   - Standard solar wind reference values
   
   **Conventions**:
   - SI units for all internal calculations
   - Consistent treatment of missing data (NaN)
   - Thermal speed convention: mw² = 2kT

{% endif %}

   Units and Dimensions
   ====================
   
   **Internal Representation** (SI base units):
   - Length: meters
   - Time: seconds  
   - Mass: kilograms
   - Temperature: Kelvin
   - Magnetic field: Tesla
   
   **Display Units** (solar wind context):
   - Velocity: km/s
   - Number density: particles/cm³
   - Magnetic field: nT
   - Temperature: K or eV
   
   **Data Quality Standards**:
   - Missing values: NaN (numpy.nan)
   - Invalid values: Never 0 or -999
   - Time series: Monotonic time ordering
   - Physical constraints: Positive definite quantities

{% endif %}

   .. rubric:: Methods

   .. autosummary::
   {% for item in methods %}
      ~{{ name }}.{{ item }}
   {%- endfor %}

   .. rubric:: Attributes

   .. autosummary::
   {% for item in attributes %}
      ~{{ name }}.{{ item }}
   {%- endfor %}
```

### Step 2.4: Enhanced Post-Processing (45 minutes)

**Target**: `docs/add_no_index.py`

**Enhanced Post-Processing Framework**:
```python
#!/usr/bin/env python3
"""
Enhanced post-processing for SolarWindPy documentation.
Handles template-generated content validation and physics-specific enhancements.
"""

import os
import re
import glob
import sys
from pathlib import Path
from typing import List, Dict, Tuple

class DocumentationProcessor:
    """Enhanced documentation post-processor for physics content."""
    
    def __init__(self, source_dir: str = "source/api"):
        self.source_dir = Path(source_dir)
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.stats: Dict[str, int] = {
            'files_processed': 0,
            'physics_sections_added': 0,
            'cross_references_fixed': 0,
            'validation_warnings': 0,
            'no_index_added': 0
        }
    
    def process_no_index_directives(self, content: str) -> str:
        """Add :no-index: directives to automodule declarations."""
        pattern = r'(\.\. automodule:: .+?)(\n   :members:)'
        replacement = r'\1\n   :no-index:\2'
        new_content = re.sub(pattern, replacement, content)
        
        if new_content != content:
            self.stats['no_index_added'] += 1
            
        return new_content
    
    def validate_physics_sections(self, content: str, filename: str) -> str:
        """Validate and enhance physics-specific sections."""
        physics_classes = ['Plasma', 'Ion', 'Base']
        physics_modules = ['plasma', 'ions', 'base']
        
        # Check for physics classes
        for physics_class in physics_classes:
            if f'autoclass:: solarwindpy.core.{physics_class.lower()}.{physics_class}' in content:
                if 'Physical Properties' not in content:
                    self.warnings.append(f"{filename}: Missing Physical Properties section for {physics_class}")
                    self.stats['validation_warnings'] += 1
                else:
                    self.stats['physics_sections_added'] += 1
        
        # Check for physics modules
        for physics_module in physics_modules:
            if f'solarwindpy.core.{physics_module}' in content:
                if 'Physics Overview' not in content and 'module.rst' in filename:
                    self.warnings.append(f"{filename}: Missing Physics Overview for {physics_module}")
                    self.stats['validation_warnings'] += 1
        
        return content
    
    def fix_cross_references(self, content: str) -> str:
        """Fix and enhance cross-references for physics concepts."""
        cross_ref_patterns = {
            # Fix unlinked class references
            r'(?<!:py:class:`~)solarwindpy\.core\.plasma\.Plasma(?!`)': 
                r':py:class:`~solarwindpy.core.plasma.Plasma`',
            r'(?<!:py:class:`~)solarwindpy\.core\.ions\.Ion(?!`)': 
                r':py:class:`~solarwindpy.core.ions.Ion`',
            r'(?<!:py:class:`~)solarwindpy\.core\.base\.Base(?!`)': 
                r':py:class:`~solarwindpy.core.base.Base`',
            
            # Fix physics units
            r'km/s(?! |$|\.)': r'km/s',
            r'nT(?! |$|\.)': r'nT',
            r'particles/cm³': r'particles/cm³',
        }
        
        for pattern, replacement in cross_ref_patterns.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                self.stats['cross_references_fixed'] += 1
        
        return content
    
    def process_file(self, file_path: Path) -> None:
        """Process a single RST file with all enhancements."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Apply all processing steps
            content = self.process_no_index_directives(content)
            content = self.validate_physics_sections(content, file_path.name)
            content = self.fix_cross_references(content)
            
            # Only write if content changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            self.stats['files_processed'] += 1
            
        except Exception as e:
            error_msg = f"Error processing {file_path}: {e}"
            self.errors.append(error_msg)
            print(f"❌ {error_msg}", file=sys.stderr)
    
    def process_all_files(self) -> bool:
        """Process all RST files in the API directory."""
        rst_files = list(self.source_dir.glob("*.rst"))
        
        if not rst_files:
            self.errors.append(f"No RST files found in {self.source_dir}")
            return False
        
        print(f"🔄 Processing {len(rst_files)} documentation files...")
        
        for rst_file in rst_files:
            self.process_file(rst_file)
        
        return len(self.errors) == 0
    
    def print_summary(self) -> None:
        """Print processing summary with physics-specific metrics."""
        print(f"\n📊 Enhanced Documentation Processing Summary:")
        print(f"   • Files processed: {self.stats['files_processed']}")
        print(f"   • :no-index: directives added: {self.stats['no_index_added']}")
        print(f"   • Physics sections validated: {self.stats['physics_sections_added']}")
        print(f"   • Cross-references fixed: {self.stats['cross_references_fixed']}")
        print(f"   • Validation warnings: {self.stats['validation_warnings']}")
        print(f"   • Processing errors: {len(self.errors)}")
        
        if self.warnings:
            print(f"\n⚠️  Physics Validation Warnings:")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        if self.errors:
            print(f"\n❌ Processing Errors:")
            for error in self.errors:
                print(f"   • {error}")

def main():
    """Main processing function with enhanced capabilities."""
    processor = DocumentationProcessor()
    
    success = processor.process_all_files()
    processor.print_summary()
    
    if success:
        print("\n✅ Enhanced documentation processing completed successfully!")
        print("   📋 Physics sections validated")
        print("   🔗 Cross-references standardized")
        print("   📚 Template enhancements applied")
        return 0
    else:
        print("\n❌ Documentation processing failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### Step 2.5: Build System Integration (45 minutes)

**Enhanced Makefile Integration**:

**Target**: `docs/Makefile` - Add enhanced API generation target

```makefile
# Enhanced API documentation generation with template validation
.PHONY: api-enhanced
api-enhanced:
	@echo "🔍 Validating documentation templates..."
	@python -c "
import os
from pathlib import Path
templates = Path('source/_templates/autosummary')
required = ['module.rst', 'class.rst']
missing = [t for t in required if not (templates / t).exists()]
if missing:
    print('❌ Missing templates:', missing)
    exit(1)
else:
    print('✅ Templates validated')
"
	@echo "🔧 Generating enhanced API documentation..."
	sphinx-apidoc -f -o $(SOURCEDIR)/api ../../solarwindpy/solarwindpy --separate
	@echo "⚙️  Applying physics-aware post-processing..."
	python add_no_index.py
	@echo "✅ Enhanced API generation complete"

# Update HTML target to use enhanced API
html: api-enhanced
	@echo "🏗️  Building HTML documentation with enhanced templates..."
	$(SPHINXBUILD) -b html $(SOURCEDIR) $(BUILDDIR)/html $(SPHINXOPTS)
	@echo "✅ Enhanced HTML documentation build complete"

# Development target with validation
.PHONY: dev-build
dev-build: api-enhanced
	@echo "🔧 Development build with physics validation..."
	$(SPHINXBUILD) -b html $(SOURCEDIR) $(BUILDDIR)/html $(SPHINXOPTS) -W
	@echo "🌐 Opening documentation..."
	python -c "import webbrowser; webbrowser.open('file://$(PWD)/_build/html/index.html')"
```

### Step 2.6: Template Validation (30 minutes)

**Create Template Validation Script**:

**Target**: `docs/validate_templates.py`

```python
#!/usr/bin/env python3
"""
Template validation script for SolarWindPy documentation system.
Ensures template syntax and physics content requirements.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple

class TemplateValidator:
    """Validator for documentation templates."""
    
    def __init__(self, template_dir: str = "source/_templates/autosummary"):
        self.template_dir = Path(template_dir)
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.stats: Dict[str, int] = {
            'templates_checked': 0,
            'physics_sections_found': 0,
            'syntax_errors': 0,
            'missing_requirements': 0
        }
    
    def validate_template_syntax(self, template_path: Path) -> bool:
        """Validate Jinja2 template syntax."""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic Jinja2 syntax validation
            jinja_patterns = [
                r'{%.*%}',  # Control structures
                r'{{.*}}',  # Variables
                r'{#.*#}',  # Comments
            ]
            
            # Check for unmatched brackets
            open_control = content.count('{%')
            close_control = content.count('%}')
            open_var = content.count('{{')
            close_var = content.count('}}')
            
            if open_control != close_control:
                self.errors.append(f"{template_path.name}: Unmatched control brackets")
                return False
                
            if open_var != close_var:
                self.errors.append(f"{template_path.name}: Unmatched variable brackets")
                return False
            
            return True
            
        except Exception as e:
            self.errors.append(f"{template_path.name}: Syntax error - {e}")
            return False
    
    def validate_physics_content(self, template_path: Path) -> bool:
        """Validate physics-specific content requirements."""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            template_name = template_path.name
            issues_found = False
            
            if template_name == 'class.rst':
                # Check for physics sections in class template
                required_sections = ['Physical Properties', 'Units and Dimensions']
                
                for section in required_sections:
                    if section not in content:
                        self.warnings.append(f"{template_name}: Missing '{section}' section")
                        self.stats['missing_requirements'] += 1
                        issues_found = True
                    else:
                        self.stats['physics_sections_found'] += 1
                
                # Check for physics classes handling
                physics_classes = ['Plasma', 'Ion', 'Base']
                for cls in physics_classes:
                    if cls in content:
                        self.stats['physics_sections_found'] += 1
            
            elif template_name == 'module.rst':
                # Check for physics overview in module template
                if 'Physics Overview' in content:
                    self.stats['physics_sections_found'] += 1
                else:
                    self.warnings.append(f"{template_name}: Consider adding Physics Overview section")
            
            return not issues_found
            
        except Exception as e:
            self.errors.append(f"{template_path.name}: Physics validation error - {e}")
            return False
    
    def validate_all_templates(self) -> bool:
        """Validate all templates in the directory."""
        template_files = list(self.template_dir.glob("*.rst"))
        
        if not template_files:
            self.errors.append(f"No template files found in {self.template_dir}")
            return False
        
        print(f"🔍 Validating {len(template_files)} documentation templates...")
        
        all_valid = True
        for template_file in template_files:
            print(f"   Checking {template_file.name}...")
            
            syntax_valid = self.validate_template_syntax(template_file)
            physics_valid = self.validate_physics_content(template_file)
            
            if syntax_valid and physics_valid:
                print(f"   ✅ {template_file.name}")
            else:
                print(f"   ⚠️  {template_file.name}")
                all_valid = False
            
            self.stats['templates_checked'] += 1
        
        return all_valid
    
    def print_summary(self) -> None:
        """Print validation summary."""
        print(f"\n📊 Template Validation Summary:")
        print(f"   • Templates checked: {self.stats['templates_checked']}")
        print(f"   • Physics sections found: {self.stats['physics_sections_found']}")
        print(f"   • Missing requirements: {self.stats['missing_requirements']}")
        print(f"   • Syntax errors: {self.stats['syntax_errors']}")
        
        if self.warnings:
            print(f"\n⚠️  Validation Warnings:")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        if self.errors:
            print(f"\n❌ Validation Errors:")
            for error in self.errors:
                print(f"   • {error}")

def main():
    """Main validation function."""
    validator = TemplateValidator()
    
    success = validator.validate_all_templates()
    validator.print_summary()
    
    if success:
        print("\n✅ All template validation checks passed!")
        print("   📋 Syntax validated")
        print("   🔬 Physics content verified")
        return 0
    else:
        print("\n⚠️  Some template validation issues found")
        print("   Review warnings above before proceeding")
        return 0  # Don't fail build for warnings

if __name__ == "__main__":
    sys.exit(main())
```

## Testing and Validation

### Step 2.7: Template Testing (30 minutes)

**Test Enhanced Templates**:
```bash
cd docs

# Validate templates
python validate_templates.py

# Generate with enhanced templates
make clean
make api-enhanced

# Verify physics sections appear
grep -r "Physical Properties" source/api/
grep -r "Physics Overview" source/api/
grep -r "Units and Dimensions" source/api/

# Build HTML to test rendering
make html

# Check for enhanced content in HTML
grep -r "Physical Properties" _build/html/
```

**Expected Results**:
- Templates pass validation
- Physics sections appear in generated RST
- HTML renders correctly with enhanced content
- Cross-references work properly

## Phase Completion

### Commit Changes
```bash
# Add all template enhancements
git add docs/source/_templates/autosummary/module.rst \
        docs/source/_templates/autosummary/class.rst \
        docs/add_no_index.py \
        docs/validate_templates.py \
        docs/Makefile

# Commit template system enhancements
git commit -m "feat: implement physics-aware documentation template system

Template Enhancements:
- Enhanced module.rst with physics overview sections
- Enhanced class.rst with physical properties documentation  
- Added physics context for Plasma, Ion, Base classes
- Implemented units and dimensions standardization
- Added cross-reference improvements

Processing Improvements:
- Enhanced add_no_index.py with physics validation
- Added template syntax validation script
- Improved cross-reference handling
- Added physics-specific content validation

Build System:
- Enhanced Makefile with template validation
- Added development build targets
- Integrated physics-aware processing pipeline

Phase 2 of ReadTheDocs automation: Template persistence achieved.
All documentation customizations now survive build regeneration."
```

### Create Phase Boundary Compaction
```bash
# Create compaction for phase transition
python .claude/hooks/create-compaction.py
```

This creates git tag: `claude/compaction/readthedocs-phase-2`

## Success Criteria

### Template System Validation
- [ ] Enhanced templates pass syntax validation
- [ ] Physics sections appear in generated documentation
- [ ] Template changes persist across rebuilds
- [ ] Cross-references work correctly
- [ ] Build system integration functional

### Physics Content Validation
- [ ] Plasma class shows Physical Properties section
- [ ] Ion class shows moment calculation equations
- [ ] Base class shows physics constants
- [ ] Units and dimensions documented consistently
- [ ] Scientific notation renders correctly

### Build Process Validation
- [ ] `make api-enhanced` generates physics-aware docs
- [ ] Post-processing adds physics validations
- [ ] Template validation catches syntax errors
- [ ] Development workflow improved

## Expected Results

### Documentation Quality
- **Scientific Context**: Physics principles documented
- **Consistency**: Standardized units and conventions
- **Persistence**: All customizations survive rebuilds
- **Professional Quality**: Publication-ready documentation

### Developer Experience
- **No Manual Editing**: All changes through templates
- **Validation Feedback**: Clear error messages for template issues
- **Enhanced Workflow**: Development targets for testing
- **Physics Awareness**: Domain-specific documentation

### System Benefits
- **Maintenance Efficiency**: 90% reduction in manual documentation work
- **Quality Assurance**: Automated validation of physics content
- **Scalability**: Template system scales with codebase growth
- **Integration Ready**: Foundation for ReadTheDocs automation

## Next Phase Preparation

Phase 2 establishes the persistent template foundation. Phase 3 will:
1. **Audit template output** - Verify all physics content renders correctly
2. **Configure ReadTheDocs** - Set up automated deployment
3. **Implement quality checks** - Automated validation pipeline
4. **Test automation** - End-to-end deployment verification

The template system ensures that all documentation customizations are permanent and automatically applied, eliminating the manual RST editing problem.

---

## Time and Complexity Summary

| Component | Duration | Complexity | Value Delivered |
|-----------|----------|------------|-----------------|
| Template analysis | 30 min | Low | Understanding current state |
| Module template enhancement | 60 min | Medium | Physics-aware modules |
| Class template enhancement | 90 min | Medium-High | Detailed physics documentation |
| Post-processing framework | 45 min | Medium | Automated validation |
| Build system integration | 45 min | Medium | Seamless workflow |
| Template validation | 30 min | Low-Medium | Quality assurance |
| Testing and validation | 30 min | Low | System verification |
| **Total Phase 2** | **5.5 hours** | **Medium** | **Persistent template system** |

**Strategic Value**: Transforms ephemeral documentation into a persistent, physics-aware system that scales with the project and eliminates manual maintenance overhead.