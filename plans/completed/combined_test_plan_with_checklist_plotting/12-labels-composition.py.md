---
name: 'Combined Plan and Checklist: Composition Labels'
about: Unified documentation and checklist for validating composition-related plotting labels.
labels: [sweep, plotting, labels, composition, Ion, ChargeState]
---

> Phase 13 of Enhanced Plotting Test Plan

## 🧠 Context

The `solarwindpy.plotting.labels.composition` module provides specialized labels for plasma composition analysis, including ion species and charge state representations. The module defines classes for representing individual ions with their charge states and provides LaTeX formatting for scientific notation in plots.

### Key Components
- **Ion Class**: Represents individual ion species with charge states
- **ChargeState Class**: Specialized charge state representations
- **Known Species**: Predefined list of common plasma species
- **LaTeX Formatting**: Automatic LaTeX generation for ion notation

### Scientific Context
- Common plasma species: C, Fe, He, Mg, Ne, N, O, Si, S
- Ion charge state notation (e.g., O^6+, Fe^10+)
- Path-safe naming for file outputs
- Integration with base plotting infrastructure

## 📋 Comprehensive Test Checklist

### 13.1 Module Structure and Exports

- [ ] **Export validation**: `__all__` contains `["Ion", "ChargeState"]`
- [ ] **Import verification**: `from . import base` works correctly
- [ ] **Path integration**: `from pathlib import Path` functions properly
- [ ] **Debug import**: `import pdb` present for development (noqa handled)

### 13.2 Known Species Definition

#### Species list validation
- [ ] **Species tuple**: `known_species` contains expected plasma species
- [ ] **Species completeness**: Common plasma species included (C, Fe, He, Mg, Ne, N, O, Si, S)
- [ ] **Species format**: Species names properly capitalized
- [ ] **Immutability**: Species tuple immutable after definition

#### Species coverage
- [ ] **Solar wind species**: Major solar wind species represented
- [ ] **Plasma physics relevance**: Species relevant to space plasma research
- [ ] **Extensibility**: System can handle unknown species with warnings

### 13.3 Ion Class Structure

#### Inheritance and initialization
- [ ] **Base inheritance**: `Ion` properly inherits from `base.Base`
- [ ] **Initialization**: `__init__(species, charge)` works correctly
- [ ] **Super call**: `super().__init__()` called appropriately
- [ ] **Species/charge setting**: `set_species_charge(species, charge)` called in init

### 13.4 Ion Class Properties

#### Species property
- [ ] **Species getter**: `@property species` returns correct species
- [ ] **Species storage**: `_species` attribute stores species correctly
- [ ] **Species immutability**: Species cannot be directly modified
- [ ] **Species type**: Species stored as expected type (string)

#### Charge property  
- [ ] **Charge getter**: `@property charge` returns correct charge
- [ ] **Charge storage**: `_charge` attribute stores charge correctly
- [ ] **Charge immutability**: Charge cannot be directly modified
- [ ] **Charge format**: Charge stored in appropriate format

#### LaTeX representation
- [ ] **LaTeX property**: `@property tex` generates correct LaTeX
- [ ] **LaTeX format**: Format `"{species}^{charge}"` applied correctly
- [ ] **LaTeX rendering**: Generated LaTeX renders properly in matplotlib
- [ ] **Special characters**: Handles superscripts and charge signs correctly

#### Units property
- [ ] **Units definition**: `@property units` returns `"\#"` 
- [ ] **Units meaning**: Hash symbol appropriate for count/number units
- [ ] **Escape handling**: Backslash escape handled correctly (noqa comment)
- [ ] **Units consistency**: Units consistent across ion instances

#### Path property
- [ ] **Path generation**: `@property path` creates valid Path object
- [ ] **Path format**: Format `species_charge` with character replacement
- [ ] **Character replacement**: Plus/minus signs replaced (+ → p, - → m)
- [ ] **File safety**: Generated paths safe for filesystem use

### 13.5 Species and Charge Validation

#### `set_species_charge()` method
- [ ] **Species capitalization**: `species.title()` applied correctly
- [ ] **Known species check**: Warning logged for unknown species
- [ ] **Species validation**: Known species processed without warnings
- [ ] **Species storage**: Valid species stored in `_species`

#### Charge validation logic
- [ ] **Charge parsing**: `int(charge)` conversion attempted
- [ ] **Valid charge handling**: Integer charges processed correctly
- [ ] **Invalid charge detection**: `ValueError` caught for invalid charges
- [ ] **Invalid charge flag**: `invalid_charge` flag set appropriately

### 13.6 Error Handling and Logging

#### Warning system
- [ ] **Unknown species warning**: Appropriate warning for unknown species
- [ ] **Logger access**: `self.logger` accessible from base class
- [ ] **Warning format**: Warning message format clear and informative
- [ ] **Warning level**: Warning level appropriate for unknown species

#### Error conditions
- [ ] **Invalid charge handling**: Proper handling of non-integer charges
- [ ] **Empty species**: Behavior with empty or None species
- [ ] **Empty charge**: Behavior with empty or None charge
- [ ] **Type errors**: Graceful handling of incorrect parameter types

### 13.7 ChargeState Class (if implemented)

#### Class structure
- [ ] **Class existence**: `ChargeState` class defined and accessible
- [ ] **Base inheritance**: Proper inheritance structure
- [ ] **Initialization**: Constructor works correctly
- [ ] **Functionality**: Core functionality implemented

#### Integration with Ion
- [ ] **Compatibility**: `ChargeState` works with `Ion` class
- [ ] **Shared functionality**: Common functionality properly shared
- [ ] **Distinct features**: Unique `ChargeState` features work correctly

### 13.8 LaTeX Integration and Formatting

#### LaTeX generation
- [ ] **Syntax correctness**: Generated LaTeX syntactically correct
- [ ] **Rendering quality**: LaTeX renders clearly in plots
- [ ] **Mathematical notation**: Proper superscript formatting for charges
- [ ] **Font consistency**: Consistent with other label formatting

#### Special formatting cases
- [ ] **Positive charges**: Positive charges formatted correctly (e.g., ^6+)
- [ ] **Negative charges**: Negative charges formatted correctly (e.g., ^1-)
- [ ] **Neutral species**: Zero charge handled appropriately
- [ ] **Multi-digit charges**: Multi-digit charges display correctly

### 13.9 File Path Integration

#### Path generation
- [ ] **Path object creation**: `Path` objects created correctly
- [ ] **Character substitution**: Safe character substitution for file systems
- [ ] **Path uniqueness**: Different ions generate unique paths
- [ ] **Path validity**: Paths valid across different operating systems

#### File system compatibility
- [ ] **Cross-platform**: Paths work on Windows, macOS, Linux
- [ ] **Special characters**: No invalid filesystem characters in paths
- [ ] **Path length**: Generated paths reasonable length
- [ ] **Collision avoidance**: Different ions don't generate identical paths

### 13.10 Integration with Base Classes

#### Base class integration
- [ ] **Logger access**: Inherits logger functionality from base
- [ ] **Base methods**: Base class methods accessible and functional
- [ ] **Initialization chain**: Initialization chain works correctly
- [ ] **Property inheritance**: Base properties accessible if applicable

### 13.11 Performance and Memory

#### Memory efficiency
- [ ] **Object size**: Ion objects use memory efficiently
- [ ] **String caching**: LaTeX strings generated efficiently
- [ ] **Path caching**: Path objects cached appropriately
- [ ] **Cleanup**: No memory leaks with repeated Ion creation

#### Performance characteristics
- [ ] **Creation speed**: Ion objects created quickly
- [ ] **Property access**: Properties accessed efficiently
- [ ] **LaTeX generation**: LaTeX generation reasonably fast
- [ ] **Scalability**: Performance maintained with many Ion objects

### 13.12 Documentation and Usage

#### Documentation quality
- [ ] **Class docstrings**: Clear documentation for Ion class
- [ ] **Method documentation**: All methods properly documented
- [ ] **Property documentation**: Properties clearly explained
- [ ] **Usage examples**: Examples of Ion usage provided

#### Scientific accuracy
- [ ] **Notation standards**: Ion notation follows scientific standards
- [ ] **Species accuracy**: Species symbols scientifically correct
- [ ] **Charge representation**: Charge notation follows conventions
- [ ] **Physical meaning**: Labels represent physical quantities correctly

### 13.13 Test Infrastructure

#### Test framework
- [ ] **Unit test structure**: Tests for individual Ion methods
- [ ] **Property testing**: All properties tested independently
- [ ] **Integration testing**: Ion objects tested in plotting contexts
- [ ] **Error condition testing**: Invalid inputs tested appropriately

#### Test data
- [ ] **Representative ions**: Test data covers common plasma ions
- [ ] **Edge cases**: Unusual species and charge states tested
- [ ] **Invalid cases**: Invalid inputs tested for proper error handling
- [ ] **Performance cases**: Large numbers of ions tested

## 🎯 Testing Strategy

### Unit Testing Approach
- Test Ion class initialization and properties independently
- Verify LaTeX generation for various ion species and charges
- Test species validation and warning system
- Validate path generation and character substitution

### Integration Testing
- Test Ion objects in actual plotting scenarios
- Verify LaTeX rendering in matplotlib contexts
- Test file path usage in save operations
- Validate integration with other label systems

### Scientific Validation
- Verify ion notation follows scientific conventions
- Test species coverage for relevant plasma physics applications
- Validate charge state representations
- Test integration with plasma composition analysis workflows

### Edge Case Coverage
- Unknown species handling
- Invalid charge states
- Extreme charge values
- Special formatting cases

---

**Status**: ✅ COMPLETED
**Commit**: 5b47880
**Tests Added**: 37 comprehensive test cases
**Time Invested**: 1.5 hours
**Test Results**: 37/37 passing (100% success rate)

**Estimated Time**: 1.5 hours  
**Dependencies**: Base label classes, pathlib, LaTeX rendering  
**Priority**: MEDIUM (Domain-specific composition functionality)