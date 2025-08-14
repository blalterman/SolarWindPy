# Phase 2: Core Physics Modules Format Standardization

## **Objective**
Standardize docstring formats to NumPy convention compliance for the 9 core physics modules that form the foundation of SolarWindPy's plasma physics analysis capabilities.

## **Scope**
Convert existing docstrings to strict NumPy format while preserving existing scientific content and adding minimal missing basic documentation.

## **Module Inventory and Format Standardization Targets**

### **High Priority Core Modules (4 modules)**

#### **Module 1: `core/plasma.py` - Primary Plasma Container** (2 hours)
**Current Status**: Module has documentation but needs NumPy format conversion

**Standardization Requirements:**
- **Class Documentation**: Convert existing Plasma class docstring to NumPy format
- **Method Documentation**: Convert 25+ methods to NumPy format with proper parameter notation
- **Property Documentation**: Add basic Returns sections for properties
- **Parameter Format**: Convert to `param : type` notation throughout

**Key Format Conversion Example:**
```python
class Plasma(base.Base):
    """Container for plasma physics data including ions, magnetic field, and spacecraft.
    
    Parameters
    ----------
    data : pandas.DataFrame
        Multi-indexed DataFrame containing plasma measurements
    ions : list of str
        Ion species identifiers (e.g., ['p1', 'a'])
    spacecraft : Spacecraft, optional
        Spacecraft trajectory information
        
    Attributes
    ----------
    species : list
        Available ion species in the plasma
    data : pandas.DataFrame
        Underlying measurement data
    ions : dict
        Dictionary of Ion objects keyed by species
    """
```

**Format Standardization Areas:**
- Convert existing docstrings to NumPy parameter format
- Add missing Returns sections for methods that return values
- Standardize type notation (array_like, optional, etc.)
- Ensure consistent section header formatting

#### **Module 2: `core/ions.py` - Ion Species Handling** (2 hours)
**Current Status**: Has some documentation but needs NumPy format conversion

**Standardization Requirements:**
- **Ion Class**: Convert existing docstring to NumPy format
- **Moment Calculations**: Standardize parameter documentation format
- **Method Documentation**: Add Returns sections where missing
- **Parameter Format**: Convert to consistent `param : type` notation

**Key Format Focus:**
- Standardize existing physics equations to proper LaTeX format
- Convert parameter lists to NumPy parameter section format
- Add basic docstrings for undocumented methods
- Ensure consistent Returns section formatting

#### **Module 3: `core/base.py` - Foundation Base Class** (1.5 hours)
**Current Status**: Has basic documentation requiring NumPy format conversion

**Standardization Requirements:**
- **Base Class**: Convert existing docstring to NumPy format
- **Method Documentation**: Standardize parameter and return documentation
- **Utility Functions**: Add basic docstrings where completely missing
- **Format Consistency**: Ensure uniform NumPy convention throughout

#### **Module 4: `core/vector.py` - Vector Mathematics** (1 hour)
**Current Status**: Mathematical operations need NumPy format standardization

**Standardization Requirements:**
- **Vector Operations**: Convert existing docstrings to NumPy format
- **Parameter Documentation**: Standardize mathematical parameter notation
- **Returns Sections**: Add proper return value documentation
- **LaTeX Format**: Standardize existing mathematical notation formatting

### **Medium Priority Core Modules (3 modules)**

#### **Module 5: `core/spacecraft.py` - Spacecraft Trajectory** (1 hour)
**Standardization Requirements:**
- **Format Conversion**: Convert existing docstrings to NumPy format
- **Parameter Sections**: Standardize coordinate and trajectory parameter documentation
- **Returns Documentation**: Add missing Returns sections for calculation methods

#### **Module 6: `core/tensor.py` - Tensor Mathematics** (1 hour)
**Standardization Requirements:**
- **Format Conversion**: Convert mathematical operation docstrings to NumPy format
- **Parameter Notation**: Standardize tensor parameter documentation
- **LaTeX Standardization**: Ensure consistent mathematical notation formatting

#### **Module 7: `core/alfvenic_turbulence.py` - Alfven Wave Analysis** (1.5 hours)
**Standardization Requirements:**
- **Format Conversion**: Convert existing physics documentation to NumPy format
- **Parameter Standardization**: Ensure consistent turbulence parameter documentation
- **Reference Format**: Standardize existing literature reference formatting

### **Standard Priority Core Modules (2 modules)**

#### **Module 8: `core/units_constants.py` - Physical Constants** (0.5 hours)
**Standardization Requirements:**
- **Format Conversion**: Convert constant documentation to NumPy format
- **Unit Documentation**: Standardize unit specification format
- **Reference Standardization**: Ensure consistent citation formatting

#### **Module 9: `core/__init__.py` - Package Entry Point** (0.5 hours)
**Standardization Requirements:**
- **Module Docstring**: Add basic NumPy format module-level docstring
- **Import Documentation**: Standardize public API documentation format
- **Format Consistency**: Ensure NumPy convention compliance

## **Format Standardization Standards for Core Modules**

### **NumPy Format Requirements**

#### **NumPy Parameter Format Standards**
```python
def thermal_speed(temperature, mass):
    """Calculate thermal speed from temperature and mass.
    
    Parameters
    ----------
    temperature : float or array_like
        Ion temperature in Kelvin [K]
    mass : float
        Ion mass in kilograms [kg]
        
    Returns
    -------
    float or ndarray
        Thermal speed in meters per second [m/s]
    """
```

#### **Format Consistency Requirements**
- **Parameter Format**: All parameters with consistent `param : type` notation
- **Type Documentation**: Standardized type specifications (array_like, optional)
- **Returns Format**: Consistent return value documentation
- **Section Headers**: Proper underline formatting for all sections

#### **Conservative Documentation Approach**
**DO NOT ADD Examples sections to functions that don't already have them**

- **Existing Examples**: Convert existing examples to proper NumPy format
- **No New Examples**: Do not add Examples sections where they don't exist
- **Format Focus**: Concentrate on parameter and return documentation
- **Content Preservation**: Maintain existing scientific content accuracy

### **Format Conversion Framework**

#### **Required Format Conversions**
- **Parameters**: Convert to NumPy `param : type` format
- **Returns**: Add Returns sections where missing
- **Existing Content**: Preserve existing Notes and References
- **No New Sections**: Do not add new Examples or References

#### **Format Validation Requirements**  
- **pydocstyle Compliance**: All docstrings pass NumPy convention checks
- **Parameter Format**: Consistent parameter documentation style
- **Returns Documentation**: Proper return value format
- **Section Consistency**: Uniform section header formatting

## **Format Conversion Strategy**

### **Phase 2 Module Processing Order**
1. **plasma.py** - Highest impact, most methods requiring format conversion
2. **ions.py** - Core calculations, many methods needing standardization
3. **base.py** - Foundation class, format affects all derived classes
4. **vector.py** - Mathematical operations with parameter standardization needs
5. **alfvenic_turbulence.py** - Specialized module with existing documentation
6. **spacecraft.py** - Coordinate systems with parameter documentation
7. **tensor.py** - Mathematical operations requiring format consistency
8. **units_constants.py** - Constants needing standardized documentation
9. **__init__.py** - Package entry point requiring basic module docstring

### **Quality Assurance Process**
1. **Format Conversion**: Convert existing docstrings to NumPy format
2. **Content Preservation**: Ensure existing scientific content remains accurate
3. **pydocstyle Validation**: NumPy convention compliance check
4. **Consistency Review**: Uniform formatting across all modules
5. **Sphinx Integration**: Verify documentation builds correctly

## **Validation and Testing Criteria**

### **NumPy Convention Compliance**
- [ ] All public classes have comprehensive docstrings
- [ ] All public methods follow NumPy parameter/returns format
- [ ] Properties include proper return value documentation
- [ ] Module-level docstrings provide comprehensive overviews

### **Format Standardization Standards**
- [ ] **Parameter Format**: All parameters use NumPy `param : type` notation
- [ ] **Returns Sections**: All functions returning values have Returns documentation
- [ ] **Type Consistency**: Standardized type specifications throughout
- [ ] **Existing Content Preserved**: No loss of existing scientific information

### **Code Quality Checks**
- [ ] **pydocstyle Compliance**: Zero NumPy convention violations
- [ ] **Sphinx Integration**: Enhanced documentation builds successfully
- [ ] **Example Validation**: All docstring examples execute correctly
- [ ] **Cross-Reference Accuracy**: Internal links and references valid

## **Success Criteria**

### **Primary Format Standardization Goals**
- **Format Compliance**: All 9 core modules follow NumPy docstring conventions
- **Content Preservation**: Existing scientific content maintained accurately
- **Consistency**: Uniform formatting across all core modules
- **pydocstyle Clean**: Zero violations for NumPy format compliance

### **Quality Metrics**
- **Zero pydocstyle Violations**: Clean NumPy format compliance
- **Format Consistency**: Uniform parameter and return documentation
- **Content Preservation**: No scientific accuracy loss during conversion
- **Sphinx Compatibility**: Documentation builds without format warnings

## **Integration with Subsequent Phases**

### **Dependencies for Phase 3 (Fitfunctions)**
- **Format Standards**: Established NumPy convention patterns
- **Parameter Format**: Consistent mathematical parameter documentation
- **Validation Framework**: pydocstyle compliance testing established

### **Foundation for Advanced Modules**
- **Base Class Format**: Foundation NumPy format for all derived classes
- **Format Standards**: Established consistent documentation patterns
- **Quality Framework**: pydocstyle validation processes proven effective

This conservative format standardization of core physics modules establishes the NumPy convention foundation for the entire SolarWindPy package, ensuring consistent documentation formatting while preserving scientific integrity.