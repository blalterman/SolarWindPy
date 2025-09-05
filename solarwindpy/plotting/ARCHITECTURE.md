# SolarWindPy Plotting Module Architecture

## Inheritance Patterns and Mixin Design Rationale

### Overview

The SolarWindPy plotting module employs a sophisticated inheritance hierarchy using **mixin classes** and the **Template Method pattern** to provide flexible, composable plotting capabilities for solar wind plasma physics analysis. This document explains the design rationale and inheritance patterns used throughout the module.

### Core Design Principles

1. **Separation of Concerns**: Each mixin handles a specific aspect of plotting functionality
2. **Cooperative Inheritance**: Classes use `super()` for proper method resolution order (MRO)
3. **Template Method Pattern**: Abstract base classes define the plotting workflow, concrete classes implement specifics
4. **Composition over Deep Inheritance**: Mixins provide functionality without deep inheritance chains

### Inheritance Hierarchy

```
Base (ABC)
├── DataLimFormatter (Mixin)
├── CbarMaker (Mixin)
└── PlotWithZdata (Concrete Base)
    ├── AggPlot (ABC)
    │   ├── Hist1D
    │   ├── Hist2D (+ DataLimFormatter + CbarMaker)
    │   └── SpiralMesh
    └── Scatter
```

### Class Responsibilities

#### Base (Abstract Base Class)
- **Purpose**: Foundation for all plotting classes
- **Responsibilities**:
  - Logger initialization and hierarchical naming
  - Common attributes (`data`, `labels`, `path`)
  - Abstract method definitions (`make_plot`, `set_labels`, etc.)
  - Template method implementations (`__str__`, `_format_axis`)
- **Design Pattern**: Template Method - defines the plotting workflow skeleton

#### DataLimFormatter (Mixin)
- **Purpose**: Automatic matplotlib data limit management
- **Responsibilities**:
  - Integrate with matplotlib's `sticky_edges` system
  - Prevent unwanted padding in pcolormesh, imshow plots
  - Coordinate with figure layout for optimal data presentation
- **Design Pattern**: Mixin - adds capability without inheritance overhead
- **Usage**: Combined with classes that need precise data limit control

#### CbarMaker (Mixin)  
- **Purpose**: Robust colorbar creation and management
- **Responsibilities**:
  - Detect figure configuration (subplots, gridspec)
  - Create appropriately sized and positioned colorbars
  - Integrate with automatic label management
  - Handle edge cases in complex subplot layouts
- **Design Pattern**: Mixin - adds colorbar capability to any plot class
- **Usage**: Essential for heatmaps, 2D histograms, and scalar field visualizations

#### PlotWithZdata (Concrete Base)
- **Purpose**: Foundation for 3D data visualization (x, y, z triplets)
- **Responsibilities**:
  - 3D data organization using pandas DataFrame structures
  - Path generation for multi-variable file naming
  - Z-axis labeling and colorbar integration
  - NaN handling for sparse datasets
- **Design Pattern**: Concrete base class implementing Base abstractions
- **Usage**: Base class for all plotting types that visualize scalar fields

#### AggPlot (Abstract Base Class)
- **Purpose**: Data aggregation pipeline for histogram-based plots
- **Responsibilities**:
  - Bin calculation and interval management
  - Pandas categorical/groupby aggregation workflows
  - Statistical normalization schemes
  - Abstract aggregation methods for concrete implementations
- **Design Pattern**: Template Method + Strategy - defines aggregation workflow, delegates specifics
- **Usage**: Base for all histogram and density-based visualizations

### Multiple Inheritance Examples

#### Hist2D Class Composition
```python
class Hist2D(base.PlotWithZdata, base.CbarMaker, AggPlot):
```

**Inheritance Chain Analysis**:
1. **PlotWithZdata**: Provides 3D data handling, path generation, z-axis labeling
2. **CbarMaker**: Adds colorbar creation and positioning capabilities  
3. **AggPlot**: Supplies 2D aggregation pipeline and statistical methods

**Method Resolution Order (MRO)**:
```
Hist2D → PlotWithZdata → CbarMaker → AggPlot → Base → object
```

**Cooperative Inheritance Flow**:
- `super().__init__()` calls flow through the MRO
- Each class initializes its specific functionality
- Final result: Fully capable 2D histogram with colorbar and z-data handling

### Design Pattern Justifications

#### Why Mixins Over Deep Inheritance?

**Traditional Deep Inheritance Problems**:
```python
# AVOIDED: Deep inheritance chain
Base → Plot2D → ColorbarPlot → DataLimitPlot → AggPlot → Hist2D
```

**Mixin Benefits**:
- **Flexibility**: Classes can select which capabilities they need
- **Testability**: Each mixin can be tested independently
- **Maintainability**: Changes to colorbar logic don't affect data limit handling
- **Reusability**: `CbarMaker` can be used with `Scatter`, `Hist2D`, `SpiralMesh`

#### Why Template Method Pattern?

**Base Class Template Methods**:
```python
def _format_axis(self):
    """Template method defining axis formatting workflow."""
    self._add_axis_labels()    # Step 1: Add labels
    self._set_axis_scale()     # Step 2: Set scaling  
    self._maybe_set_lims()     # Step 3: Set limits (overridable)
```

**Benefits**:
- **Consistent Workflow**: All plots follow the same formatting steps
- **Extensibility**: Subclasses can override specific steps without rewriting the entire method
- **Code Reuse**: Common formatting logic written once, used everywhere

### Advanced Inheritance Features

#### Abstract Property Handling
```python
# Current implementation (deprecated pattern)
@abstractproperty
def _gb_axes(self):
    pass

# Future implementation (modern pattern)  
@property
@abstractmethod
def _gb_axes(self):
    pass
```

**Migration Notes**:
- `@abstractproperty` deprecated in Python 3.8+
- Phase 3 will migrate to `@property` + `@abstractmethod`
- Maintains same interface, improves Python 3.8+ compatibility

#### Cooperative Super() Usage

**Correct Pattern** (used throughout module):
```python
def __init__(self, **kwargs):
    super().__init__(**kwargs)  # Passes to next class in MRO
    # Class-specific initialization
```

**Benefits**:
- Ensures all classes in inheritance chain are properly initialized
- Handles complex MRO automatically
- Enables flexible mixin composition

### Solar Wind Physics Integration

#### Domain-Specific Design Decisions

**Data Structure Alignment**:
- Inheritance hierarchy mirrors solar wind analysis workflow
- `AggPlot` → statistical analysis of plasma parameters
- `PlotWithZdata` → scalar field visualization (density, temperature, magnetic field strength)
- Mixins provide capabilities needed for publication-quality scientific visualizations

**Performance Considerations**:
- Mixin composition minimizes memory overhead
- Template methods reduce code duplication
- Cooperative inheritance enables efficient method chaining

### Usage Guidelines

#### When to Use Each Pattern

**Mixin Usage**:
- Need colorbar functionality → inherit from `CbarMaker`  
- Need precise data limits → inherit from `DataLimFormatter`
- Need both → `class MyPlot(CbarMaker, DataLimFormatter, Base)`

**Template Method Usage**:
- Common workflow with class-specific variations
- Override specific methods (`_maybe_set_lims`) without rewriting entire workflow
- Maintain consistent behavior across all plot types

**Multiple Inheritance Best Practices**:
- Always call `super()` in `__init__` methods
- Order mixins before base classes in inheritance list
- Use `super()` in overridden methods for cooperative behavior
- Test MRO with `ClassName.__mro__` during development

### Future Architecture Evolution

#### Planned Improvements (Post Phase 1)

1. **Modernize Abstract Properties**: Replace `@abstractproperty` with `@property` + `@abstractmethod`
2. **Simplify Inheritance**: Evaluate 4-level inheritance chains for potential flattening  
3. **Enhanced Mixin Composition**: Additional specialized mixins for specific solar wind visualizations
4. **Performance Optimization**: Investigate protocol-based inheritance for Python 3.8+ type hints

This architecture provides SolarWindPy with flexible, maintainable, and extensible plotting capabilities specifically designed for the complex requirements of solar wind plasma physics research.