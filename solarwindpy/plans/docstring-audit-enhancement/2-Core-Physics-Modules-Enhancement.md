# Phase 2: Core Physics Modules Enhancement

## **Objective**
Comprehensive docstring enhancement for the 9 core physics modules that form the foundation of SolarWindPy's plasma physics analysis capabilities.

## **Scope**
Target all core modules with emphasis on plasma physics algorithms, mathematical operations, and scientific accuracy in documentation.

## **Module Inventory and Enhancement Targets**

### **High Priority Core Modules (4 modules)**

#### **Module 1: `core/plasma.py` - Primary Plasma Container** (3 hours)
**Current Status**: Module has some documentation but missing comprehensive NumPy format compliance

**Enhancement Requirements:**
- **Class Documentation**: Complete Plasma class docstring with physics background
- **Method Documentation**: All 25+ methods need NumPy format docstrings
- **Property Documentation**: Ion access properties and convenience attributes
- **Physics Integration**: Coulomb collision documentation, magnetic field interactions

**Key Documentation Targets:**
```python
class Plasma(base.Base):
    """Container for plasma physics data including ions, magnetic field, and spacecraft.
    
    The Plasma class serves as the central container for multi-species plasma
    analysis, combining ion moment data, magnetic field measurements, and
    spacecraft trajectory information for comprehensive plasma physics calculations.
    
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
        
    Examples
    --------
    >>> plasma = Plasma(data, ['p1', 'a'], spacecraft=sc)
    >>> proton_density = plasma.p1.n  # Convenient species access
    >>> coulomb_collisions = plasma.nc()  # Physics calculations
    """
```

**Missing Documentation Areas:**
- Ion access convenience methods (`__getattr__` functionality)
- Physics calculation methods (`nc()`, `beta()`, thermal parameters)
- Data manipulation methods (`dropna()`, time selection)
- Multi-species analysis capabilities

#### **Module 2: `core/ions.py` - Ion Species Handling** (2.5 hours)
**Current Status**: Missing comprehensive docstrings for ion moment calculations

**Enhancement Requirements:**
- **Ion Class**: Complete physics-based documentation
- **Moment Calculations**: Thermal speed, temperature, pressure tensors
- **Species Properties**: Mass, charge, and derived quantities
- **Mathematical Operations**: Vector and tensor computations

**Key Documentation Focus:**
- Ion moment physics: `mw² = 2kT` relationships
- Pressure tensor calculations and physical interpretation
- Species-specific constants and properties
- Integration with plasma physics calculations

#### **Module 3: `core/base.py` - Foundation Base Class** (2 hours)
**Current Status**: Basic documentation present but needs NumPy format enhancement

**Enhancement Requirements:**
- **Base Class Architecture**: Logging, utilities, and common functionality
- **Data Validation**: DataFrame structure validation methods
- **Unit Handling**: Conversion and consistency checking
- **Error Management**: Exception handling and logging integration

#### **Module 4: `core/vector.py` - Vector Mathematics** (1.5 hours)
**Current Status**: Mathematical operations need comprehensive documentation

**Enhancement Requirements:**
- **Vector Operations**: Dot products, cross products, magnitudes
- **Coordinate Transformations**: Various coordinate system conversions
- **Mathematical Notation**: Proper LaTeX formatting for vector equations
- **Physics Applications**: Vector field analysis in plasma context

### **Medium Priority Core Modules (3 modules)**

#### **Module 5: `core/spacecraft.py` - Spacecraft Trajectory** (1.5 hours)
**Enhancement Requirements:**
- **Trajectory Calculations**: Position, velocity, acceleration documentation
- **Coordinate Systems**: Various reference frame transformations
- **Integration Points**: How spacecraft data integrates with plasma analysis

#### **Module 6: `core/tensor.py` - Tensor Mathematics** (1.5 hours)
**Enhancement Requirements:**
- **Tensor Operations**: Mathematical operations and transformations
- **Physics Applications**: Pressure tensor, stress tensor applications
- **LaTeX Formatting**: Complex tensor equation documentation

#### **Module 7: `core/alfvenic_turbulence.py` - Alfven Wave Analysis** (2 hours)
**Enhancement Requirements:**
- **Turbulence Theory**: Alfven wave physics background
- **Analysis Methods**: Turbulence parameter calculations
- **Literature References**: Proper citations for turbulence algorithms

### **Standard Priority Core Modules (2 modules)**

#### **Module 8: `core/units_constants.py` - Physical Constants** (1 hour)
**Enhancement Requirements:**
- **Constant Definitions**: Physical constants with proper units and references
- **Unit Conversions**: Conversion factor documentation
- **Scientific Accuracy**: Proper literature citations for constant values

#### **Module 9: `core/__init__.py` - Package Entry Point** (0.5 hours)
**Enhancement Requirements:**
- **Package Overview**: Core module summary and usage patterns
- **Import Structure**: Public API documentation
- **Integration Guide**: How core modules work together

## **Documentation Standards for Core Modules**

### **Physics-Specific Requirements**

#### **Mathematical Notation Standards**
```python
def thermal_speed(temperature, mass):
    """Calculate thermal speed from temperature and mass.
    
    Implements the relationship mw² = 2kT for plasma thermal motion,
    where thermal speed w = sqrt(2kT/m).
    
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
        
    Notes
    -----
    The thermal speed is defined as:
    
    .. math::
        w = \\sqrt{\\frac{2kT}{m}}
        
    where k is Boltzmann's constant, T is temperature, and m is mass.
    
    References
    ----------
    .. [1] Chen, F. F. "Introduction to Plasma Physics and Controlled Fusion"
           Springer, 2016.
    """
```

#### **Unit Documentation Requirements**
- **Physical Quantities**: All parameters with SI units specified
- **Dimensionless Quantities**: Clear identification when unitless
- **Unit Conversions**: Documentation of any internal unit handling
- **Validation**: Expected ranges and physical limits

#### **Example Code Standards**
```python
Examples
--------
Create a plasma object and access ion properties:

>>> data = load_plasma_data('2020-01-01')
>>> plasma = Plasma(data, ['p1', 'a'])  
>>> proton_temp = plasma.p1.T  # Proton temperature [K]
>>> alpha_density = plasma.a.n  # Alpha particle density [cm^-3]

Calculate plasma physics parameters:

>>> beta = plasma.beta()  # Plasma beta parameter
>>> coulomb = plasma.nc()  # Coulomb collision frequency [s^-1]
```

### **Scientific Documentation Framework**

#### **Required Sections for Physics Methods**
- **Parameters**: Complete type and unit documentation
- **Returns**: Physical interpretation and units
- **Notes**: Physics background and equations
- **References**: Literature citations for algorithms
- **Examples**: Practical usage with real physics context

#### **Physics Validation Requirements**  
- **Unit Consistency**: All physical quantities properly documented
- **Equation Accuracy**: LaTeX math notation validated
- **Reference Verification**: Literature citations accurate and complete
- **Example Testing**: Code examples execute and produce expected results

## **Implementation Strategy**

### **Phase 2 Module Processing Order**
1. **plasma.py** - Highest impact, most complex documentation needs
2. **ions.py** - Core physics calculations, mathematical complexity  
3. **base.py** - Foundation class, affects all other modules
4. **vector.py** - Mathematical operations, LaTeX requirements
5. **alfvenic_turbulence.py** - Specialized physics, literature citations
6. **spacecraft.py** - Coordinate systems, integration documentation
7. **tensor.py** - Complex mathematics, tensor notation
8. **units_constants.py** - Standards compliance, reference accuracy
9. **__init__.py** - Package integration, public API clarity

### **Quality Assurance Process**
1. **Draft Enhancement**: Initial docstring improvements
2. **Physics Review**: Scientific accuracy validation
3. **Format Validation**: NumPy convention compliance check
4. **Example Testing**: Code example execution verification
5. **Integration Testing**: Cross-module documentation consistency

## **Validation and Testing Criteria**

### **NumPy Convention Compliance**
- [ ] All public classes have comprehensive docstrings
- [ ] All public methods follow NumPy parameter/returns format
- [ ] Properties include proper return value documentation
- [ ] Module-level docstrings provide comprehensive overviews

### **Physics Documentation Standards**
- [ ] **Units Specified**: All physical quantities include SI units
- [ ] **Equations Documented**: LaTeX math notation for all physics relationships
- [ ] **References Included**: Literature citations for physics algorithms
- [ ] **Examples Provided**: Practical usage examples with physics context

### **Code Quality Checks**
- [ ] **pydocstyle Compliance**: Zero NumPy convention violations
- [ ] **Sphinx Integration**: Enhanced documentation builds successfully
- [ ] **Example Validation**: All docstring examples execute correctly
- [ ] **Cross-Reference Accuracy**: Internal links and references valid

## **Success Criteria**

### **Primary Documentation Goals**
- **Complete Coverage**: All 9 core modules have comprehensive docstrings
- **Physics Accuracy**: Scientific content validated for accuracy
- **NumPy Compliance**: Full adherence to NumPy docstring conventions
- **Enhanced Sphinx Output**: Professional-quality API documentation

### **Quality Metrics**
- **Zero pydocstyle Violations**: Clean NumPy format compliance
- **100% Public API Coverage**: All public methods and classes documented
- **Physics Validation**: Scientific accuracy confirmed by domain experts
- **Example Success Rate**: 100% of docstring examples execute successfully

## **Integration with Subsequent Phases**

### **Dependencies for Phase 3 (Fitfunctions)**
- **Mathematical Framework**: Established LaTeX notation standards
- **Physics Integration**: Core plasma physics concepts properly documented
- **Example Standards**: Code example format and validation established

### **Foundation for Advanced Modules**
- **Base Class Documentation**: Foundation for all derived classes
- **Physics Standards**: Established scientific documentation requirements
- **Quality Framework**: Validation and testing processes proven effective

This comprehensive enhancement of core physics modules establishes the scientific and technical documentation foundation for the entire SolarWindPy package, ensuring both developer accessibility and scientific integrity.