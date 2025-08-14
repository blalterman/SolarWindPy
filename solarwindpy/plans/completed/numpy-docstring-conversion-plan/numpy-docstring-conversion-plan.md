# NumPy Docstring Standard Conversion Plan

## Overview
Convert 21 unknown section warnings to NumPy standard sections across 9 files in the SolarWindPy codebase.

## Section Mapping Strategy

### 1. Simple Typo Fixes (4 instances)
- **"Paremeters" → "Parameters"** 
  - hist2d.py: make_plot(), plot_contours()
  - scatter.py: make_plot()
  - spiral.py: plot_contours()

### 2. Class Docstring Conversions (12 instances in plotting modules)

#### For Abstract Base Classes (AggPlot, Base, Scatter):
- **"Properties" → "Attributes"**
  - List all class properties under Attributes section
  
- **"Abstract Properties" → "Attributes"** (merge with above)
  - Mark abstract properties with "(abstract)" notation
  
- **"Abstract Methods" → "Methods"**
  - List abstract methods with brief descriptions
  - Mark with "(abstract)" notation

#### For Concrete Classes (Hist1D, Hist2D):
- **"Properties" → "Attributes"**
  - Simple rename to standard section

### 3. Special Section Conversions (5 instances)

#### plasma.py - beta method:
- **"Derivation" → "Notes"**
  - Move mathematical derivation to Notes section
  - Keep formulas and equations intact

#### alfvenic_turbulence.py - AlfvenicTurbulenceDAmicis:
- **"Properties" → "Attributes"**
  - Convert to standard class attributes listing

#### spiral.py - SpiralPlot2D:
- **"Call Signature" → "Examples"**
  - Move usage examples to Examples section

#### sidc.py - plot_on_colorbar:
- **"Todo" → Remove or convert to comment**
  - Move to inline comment or remove if not needed

## Implementation Order

### Phase 1: Quick Typo Fixes (4 files)
1. solarwindpy/plotting/hist2d.py - Fix "Paremeters" → "Parameters" (2 methods)
2. solarwindpy/plotting/scatter.py - Fix "Paremeters" → "Parameters" (1 method)
3. solarwindpy/plotting/spiral.py - Fix "Paremeters" → "Parameters" (1 method)

### Phase 2: Plotting Module Class Docstrings (5 files)
4. solarwindpy/plotting/agg_plot.py - Convert Properties/Abstract sections
5. solarwindpy/plotting/base.py - Convert Properties/Abstract sections (fix typo: "Properites")
6. solarwindpy/plotting/scatter.py - Convert Properties/Abstract sections
7. solarwindpy/plotting/hist1d.py - Convert Properties section
8. solarwindpy/plotting/hist2d.py - Convert Properties section

### Phase 3: Core Module Updates (2 files)
9. solarwindpy/core/plasma.py - Convert Derivation → Notes
10. solarwindpy/core/alfvenic_turbulence.py - Convert Properties → Attributes

### Phase 4: Miscellaneous (2 files)
11. solarwindpy/plotting/spiral.py - Convert Call Signature → Examples
12. solarwindpy/solar_activity/sunspot_number/sidc.py - Handle Todo section

## Expected Results
- **21 warnings eliminated** - Full NumPy docstring compliance
- **Improved documentation** - Standard sections more discoverable
- **Better Sphinx rendering** - Proper section formatting
- **Easier maintenance** - Consistent documentation style

## Testing Strategy
After each phase:
1. Run `make clean html` to rebuild docs
2. Verify warning count reduction
3. Check HTML rendering for affected classes/methods
4. Ensure no new warnings introduced

## Time Estimate
- Phase 1: 10 minutes (simple find/replace)
- Phase 2: 30 minutes (careful class docstring restructuring)
- Phase 3: 15 minutes (content migration)
- Phase 4: 10 minutes (special cases)
- Testing: 15 minutes
- **Total: ~80 minutes**

## Status Tracking

### Phase 1: Typo Fixes
- [ ] hist2d.py - Fix "Paremeters" → "Parameters" (2 methods)
- [ ] scatter.py - Fix "Paremeters" → "Parameters" (1 method)  
- [ ] spiral.py - Fix "Paremeters" → "Parameters" (1 method)

### Phase 2: Class Docstrings
- [ ] agg_plot.py - Convert Properties/Abstract sections
- [ ] base.py - Convert Properties/Abstract sections (fix typo)
- [ ] scatter.py - Convert Properties/Abstract sections
- [ ] hist1d.py - Convert Properties section
- [ ] hist2d.py - Convert Properties section

### Phase 3: Core Modules
- [ ] plasma.py - Convert Derivation → Notes
- [ ] alfvenic_turbulence.py - Convert Properties → Attributes

### Phase 4: Special Cases
- [ ] spiral.py - Convert Call Signature → Examples
- [ ] sidc.py - Handle Todo section

### Testing
- [ ] Verify 21 warnings eliminated
- [ ] Check documentation rendering
- [ ] Run final build test