# Phase 4: Plotting Visualization Modules Enhancement

## **Objective**
Comprehensive docstring enhancement for the 18 plotting modules that provide data visualization, publication-quality plotting, and interactive analysis capabilities for plasma physics research.

## **Scope**
Target all plotting modules with emphasis on visualization method documentation, plot customization parameters, and matplotlib integration best practices.

## **Module Inventory and Enhancement Targets**

### **Foundation Plotting Modules (4 modules)**

#### **Module 1: `plotting/base.py` - Base Plotting Infrastructure** (2.5 hours)
**Current Status**: Core plotting utilities with limited documentation

**Enhancement Requirements:**
- **Base Classes**: Common plotting functionality and matplotlib integration
- **Style Management**: Color schemes, fonts, and publication standards
- **Figure Management**: Size, DPI, and output format handling
- **Axis Configuration**: Scientific notation, units, and scaling

**Key Documentation Targets:**
```python
class BasePlot:
    """Base class for scientific plotting with matplotlib integration.
    
    Provides common functionality for creating publication-quality plots
    with consistent styling, proper axis handling, and scientific
    formatting standards for plasma physics visualizations.
    
    Parameters
    ----------
    figsize : tuple, optional
        Figure size in inches (width, height). Default is (10, 8).
    dpi : int, optional
        Figure resolution in dots per inch. Default is 100.
    style : str, optional
        Plotting style preset. Options: ['publication', 'presentation', 'notebook'].
        Default is 'publication'.
        
    Attributes
    ----------
    fig : matplotlib.figure.Figure
        The matplotlib figure object
    ax : matplotlib.axes.Axes or list
        Axis or list of axes for plotting
    colors : dict
        Color scheme for consistent plot styling
        
    Methods
    -------
    setup_axes(**kwargs)
        Configure axes with scientific notation and units
    apply_style(style_name)
        Apply predefined styling to the plot
    save(filename, **kwargs)
        Save plot with publication-quality settings
        
    Examples
    --------
    Create a base plot with publication styling:
    
    >>> plot = BasePlot(figsize=(8, 6), style='publication')
    >>> plot.setup_axes(xlabel='Time [s]', ylabel='Density [cm⁻³]')
    >>> plot.save('plasma_density.pdf', dpi=300)
    
    Notes
    -----
    Default styling follows scientific publication standards with:
    - Times New Roman fonts for consistency
    - Appropriate line weights and marker sizes  
    - Color-blind friendly color schemes
    - Proper axis scaling and tick formatting
    """
```

#### **Module 2: `plotting/agg_plot.py` - Aggregated Plot Utilities** (2 hours)
**Enhancement Requirements:**
- **Multi-panel Plotting**: Subplot management and layout optimization
- **Data Aggregation**: Statistical summaries and composite visualizations
- **Layout Management**: Figure composition and spacing
- **Integration Points**: How aggregated plots work with other modules

#### **Module 3: `plotting/tools.py` - General Plotting Tools** (2 hours)
**Enhancement Requirements:**
- **Utility Functions**: Common plotting operations and helpers
- **Data Preparation**: Formatting data for visualization
- **Customization Utilities**: Style and formatting helper functions
- **Performance Optimization**: Efficient plotting for large datasets

#### **Module 4: `plotting/select_data_from_figure.py` - Interactive Data Selection** (2 hours)
**Enhancement Requirements:**
- **Interactive Features**: Mouse-based data selection and zooming
- **Event Handling**: Matplotlib event integration
- **Data Extraction**: Converting plot coordinates to data values
- **User Interface**: Interactive analysis workflow documentation

### **Histogram and Distribution Modules (3 modules)**

#### **Module 5: `plotting/histograms.py` - Legacy Histogram Interface** (1 hour)
**Enhancement Requirements:**
- **Legacy Support**: Backward compatibility documentation
- **Migration Guide**: Transition to hist1d/hist2d modules
- **Deprecation Warnings**: Clear upgrade path documentation

#### **Module 6: `plotting/hist1d.py` - 1D Histogram Plotting** (2 hours)
**Enhancement Requirements:**
- **Distribution Visualization**: Single-variable histogram creation
- **Statistical Overlays**: Mean, median, and distribution fitting
- **Binning Strategies**: Automatic and manual bin selection
- **Customization Options**: Styling and formatting parameters

**Mathematical Documentation Focus:**
```python
def plot_histogram(data, bins='auto', density=False, **kwargs):
    """Create publication-quality 1D histogram with statistical overlays.
    
    Generates histogram plots with automatic binning, statistical
    summaries, and optional distribution fitting for plasma physics
    data analysis.
    
    Parameters
    ----------
    data : array_like
        Input data for histogram generation [data units]
    bins : int, str, or array_like, optional
        Histogram binning strategy:
        - int: Number of equal-width bins
        - str: Algorithm ('auto', 'sturges', 'fd', 'scott')  
        - array: Explicit bin edges [data units]
        Default is 'auto'.
    density : bool, optional
        If True, create probability density. If False, create counts.
        Default is False.
    statistics : bool, optional
        Include statistical summary (mean, std, skew). Default is True.
    fit_distribution : str, optional
        Overlay distribution fit. Options: ['gaussian', 'lognormal', None].
        Default is None.
        
    Returns
    -------
    fig : matplotlib.figure.Figure
        Figure object containing the histogram
    ax : matplotlib.axes.Axes  
        Axes object for further customization
    hist_data : dict
        Dictionary containing histogram counts, bin edges, and statistics
        
    Examples
    --------
    Create histogram of plasma density measurements:
    
    >>> density_data = plasma.p1.n.dropna()
    >>> fig, ax, stats = plot_histogram(
    ...     density_data, 
    ...     bins=50,
    ...     density=True,
    ...     fit_distribution='lognormal'
    ... )
    >>> ax.set_xlabel('Proton Density [cm⁻³]')
    >>> ax.set_ylabel('Probability Density')
    
    Notes
    -----
    Automatic binning uses the Freedman-Diaconis rule for optimal
    bin width selection based on data distribution characteristics.
    
    For plasma physics data, log-normal distributions are often
    appropriate due to multiplicative physical processes.
    """
```

#### **Module 7: `plotting/hist2d.py` - 2D Histogram Plotting** (2.5 hours)
**Enhancement Requirements:**
- **Joint Distributions**: Two-variable histogram and density plots
- **Correlation Analysis**: Statistical relationship visualization
- **Color Mapping**: Scientific color schemes and scaling
- **Contour Integration**: Density contour overlay capabilities

### **Specialized Visualization Modules (4 modules)**

#### **Module 8: `plotting/scatter.py` - Scatter Plot Analysis** (2 hours)
**Enhancement Requirements:**
- **Correlation Plots**: Two-variable relationship visualization
- **Color Coding**: Third variable encoding and interpretation
- **Statistical Overlays**: Regression lines and confidence intervals
- **Large Dataset Handling**: Efficient plotting for big data

#### **Module 9: `plotting/spiral.py` - Spiral Mesh Calculations** (2 hours)
**Enhancement Requirements:**
- **Spiral Geometry**: Mathematical spiral generation and properties
- **Mesh Operations**: Grid generation and coordinate transformations
- **Physics Applications**: Spiral structures in plasma dynamics
- **Visualization Integration**: How spirals integrate with plotting

#### **Module 10: `plotting/orbits.py` - Orbital Trajectory Plots** (2 hours)
**Enhancement Requirements:**
- **Trajectory Visualization**: Spacecraft orbit and path plotting
- **Coordinate Systems**: Various reference frames and projections  
- **3D Capabilities**: Three-dimensional trajectory representation
- **Physics Context**: Orbital mechanics in plasma environment

### **Label and Annotation Modules (6 modules)**

#### **Module 11: `plotting/labels/base.py` - Base Label Formatting** (1.5 hours)
**Enhancement Requirements:**
- **Text Formatting**: Scientific notation and unit handling
- **LaTeX Integration**: Mathematical symbol and equation rendering
- **Internationalization**: Multi-language support considerations
- **Accessibility**: Color-blind and visually impaired accommodations

#### **Module 12: `plotting/labels/special.py` - Special Scientific Labels** (1.5 hours)
**Enhancement Requirements:**
- **Physics Symbols**: Greek letters, subscripts, and scientific notation
- **Unit Formatting**: Proper SI unit representation and powers
- **Mathematical Expressions**: Complex equation rendering
- **Standardization**: Consistent symbol usage across package

#### **Module 13: `plotting/labels/chemistry.py` - Chemical Species Labels** (1.5 hours)
**Enhancement Requirements:**
- **Ion Notation**: Proper chemical species representation (H⁺, He²⁺)
- **Isotope Labels**: Mass number and atomic number formatting
- **Chemical Formulas**: Molecular species and reaction notation
- **Physics Context**: Ion species in plasma physics applications

#### **Module 14: `plotting/labels/composition.py` - Composition Ratio Labels** (1.5 hours)
**Enhancement Requirements:**
- **Ratio Formatting**: Fractional abundance representation
- **Statistical Notation**: Uncertainty and confidence interval display
- **Comparative Analysis**: Multi-species comparison formatting
- **Units and Scaling**: Proper normalization and scaling documentation

#### **Module 15: `plotting/labels/datetime.py` - Time Formatting Labels** (1.5 hours)
**Enhancement Requirements:**
- **Time Series**: Temporal axis formatting and tick spacing
- **Multiple Time Scales**: Seconds to years with appropriate resolution
- **Time Zone Handling**: UTC and local time considerations
- **Epoch Formatting**: Scientific time standards (spacecraft time)

#### **Module 16: `plotting/labels/elemental_abundance.py` - Element Abundance Labels** (1.5 hours)
**Enhancement Requirements:**
- **Abundance Notation**: Logarithmic and linear abundance scales
- **Element Symbols**: Periodic table notation and isotope variants
- **Solar Standards**: Reference abundance scales and normalization
- **Comparative Displays**: Multi-element abundance comparisons

### **Package Organization Modules (2 modules)**

#### **Module 17: `plotting/labels/__init__.py` - Labels Package Entry** (0.5 hours)
**Enhancement Requirements:**
- **Label Package Overview**: Comprehensive module summary
- **Import Structure**: Public API and convenience functions
- **Usage Examples**: Common labeling patterns and workflows

#### **Module 18: `plotting/__init__.py` - Main Plotting Package Entry** (0.5 hours)
**Enhancement Requirements:**
- **Package Architecture**: Complete plotting ecosystem overview
- **Integration Guide**: How plotting modules work together
- **Best Practices**: Publication-quality plotting workflows

## **Visualization Documentation Standards**

### **Plot Method Documentation Template**
```python
def create_scientific_plot(data, plot_type='scatter', **kwargs):
    """Create publication-quality scientific visualization.
    
    Parameters
    ----------
    data : pandas.DataFrame or dict
        Input data with columns for x, y, and optional color/size variables
    plot_type : str, optional
        Type of visualization. Options: ['scatter', 'line', 'histogram', 'contour'].
        Default is 'scatter'.
    xlabel : str, optional
        X-axis label with units [units]
    ylabel : str, optional
        Y-axis label with units [units]
    title : str, optional
        Plot title
    figsize : tuple, optional
        Figure size in inches (width, height). Default is (10, 8).
    colormap : str, optional
        Matplotlib colormap name. Default is 'viridis'.
    save_path : str, optional
        File path to save the figure. If None, displays interactively.
        
    Returns
    -------
    fig : matplotlib.figure.Figure
        The created figure object
    ax : matplotlib.axes.Axes
        The axes object for further customization
        
    Examples
    --------
    Create scatter plot of plasma parameters:
    
    >>> data = {'density': plasma.p1.n, 'temperature': plasma.p1.T}
    >>> fig, ax = create_scientific_plot(
    ...     data, 
    ...     plot_type='scatter',
    ...     xlabel='Proton Density [cm⁻³]',
    ...     ylabel='Proton Temperature [K]',
    ...     title='Plasma Parameter Correlation'
    ... )
    
    Customize and save the plot:
    
    >>> ax.set_xscale('log')
    >>> ax.set_yscale('log') 
    >>> fig.savefig('plasma_correlation.pdf', dpi=300, bbox_inches='tight')
    
    Notes
    -----
    All plots follow scientific publication standards with appropriate
    fonts, line weights, and color schemes suitable for both print
    and digital media.
    """
```

### **Interactive Feature Documentation**
```python
def interactive_data_selector(fig, ax, callback=None):
    """Add interactive data selection capability to existing plot.
    
    Parameters
    ----------
    fig : matplotlib.figure.Figure
        Figure containing the plot
    ax : matplotlib.axes.Axes
        Axes with data to select from
    callback : callable, optional
        Function called when selection is made: callback(selected_data)
        
    Returns
    -------
    selector : object
        Selection handler object for managing interaction
        
    Examples
    --------
    Enable interactive selection on scatter plot:
    
    >>> fig, ax = plt.subplots()
    >>> ax.scatter(x_data, y_data)
    >>> def process_selection(data):
    ...     print(f"Selected {len(data)} points")
    >>> selector = interactive_data_selector(fig, ax, process_selection)
    
    Notes
    -----
    - Left click and drag to select rectangular regions
    - Right click to clear current selection
    - Double click to select all visible data
    """
```

## **Implementation Strategy**

### **Phase 4 Module Processing Order**
1. **base.py** - Foundation for all plotting functionality
2. **tools.py** - Common utilities needed by other modules
3. **agg_plot.py** - Multi-panel functionality
4. **hist1d.py** - Single variable distributions
5. **hist2d.py** - Joint distributions and correlations
6. **scatter.py** - Correlation analysis plots
7. **select_data_from_figure.py** - Interactive capabilities
8. **spiral.py** - Specialized geometric calculations
9. **orbits.py** - Trajectory visualization
10. **labels/base.py** - Foundation for text formatting
11. **labels/special.py** - Scientific notation and symbols
12. **labels/chemistry.py** - Chemical species formatting
13. **labels/composition.py** - Abundance ratio formatting
14. **labels/datetime.py** - Time series formatting
15. **labels/elemental_abundance.py** - Element abundance scales
16. **histograms.py** - Legacy interface documentation
17. **labels/__init__.py** - Labels package integration
18. **__init__.py** - Main plotting package integration

### **Quality Assurance for Visualization**
1. **Visual Testing**: Plot examples generate expected outputs
2. **Interactive Testing**: User interaction features function correctly
3. **Publication Quality**: Plots meet scientific publication standards
4. **Performance Testing**: Efficient plotting for large datasets
5. **Accessibility Validation**: Color-blind and visually impaired compatibility

## **Validation and Testing Criteria**

### **Visualization Quality Standards**
- [ ] **Plot Generation**: All documented examples produce valid matplotlib figures
- [ ] **Style Consistency**: Uniform appearance across all plotting functions
- [ ] **Interactive Features**: User interaction capabilities work as documented
- [ ] **Publication Quality**: Plots suitable for scientific journals

### **Documentation Completeness**
- [ ] **Parameter Coverage**: All plotting parameters with types and defaults documented
- [ ] **Example Quality**: Practical examples with realistic scientific data
- [ ] **Customization Options**: Clear documentation of styling and formatting capabilities
- [ ] **Integration Guidance**: How plotting modules work together effectively

### **Scientific Standards**
- [ ] **Unit Handling**: Proper axis labeling with physical units
- [ ] **Color Schemes**: Scientific color maps with accessibility considerations  
- [ ] **Statistical Accuracy**: Correct implementation of statistical overlays
- [ ] **Performance Documentation**: Guidelines for plotting large datasets

## **Success Criteria**

### **Primary Visualization Goals**
- **Complete Plotting Documentation**: All 18 modules with comprehensive visualization guidance
- **Publication Quality**: Professional scientific plotting standards throughout
- **Interactive Capabilities**: Well-documented user interaction features
- **Accessibility Standards**: Color-blind and visually impaired accommodations

### **Quality Metrics**
- **Visual Validation**: 100% of documented examples generate expected plots
- **NumPy Compliance**: Perfect adherence to docstring conventions
- **Performance Standards**: Efficient plotting documented for large datasets
- **Integration Success**: Seamless module interaction documentation

## **Integration with Overall Plan**

### **Dependencies from Previous Phases**
- **Mathematical Framework**: LaTeX standards from fitfunctions modules
- **Scientific Context**: Physics applications from core modules  
- **Infrastructure**: Validation tools and documentation standards

### **Contributions to Final Success**
- **User Experience**: High-quality visualization enhances package usability
- **Scientific Impact**: Publication-quality plots support research dissemination
- **Developer Tools**: Comprehensive plotting framework for future development

This comprehensive enhancement of plotting modules establishes professional visualization standards, ensuring SolarWindPy provides publication-quality scientific plotting capabilities with excellent documentation, accessibility features, and integration with the broader plasma physics analysis framework.