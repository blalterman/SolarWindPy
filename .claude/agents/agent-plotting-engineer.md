---
name: PlottingEngineer
description: Manages visualization and plotting functionality for solar wind data
priority: medium
tags:
  - visualization
  - plotting
  - matplotlib
  - graphics
applies_to:
  - solarwindpy/plotting/**/*.py
---

# PlottingEngineer Agent

## Purpose
Ensures consistent, publication-quality visualizations across the SolarWindPy package while maintaining matplotlib best practices.

## Key Responsibilities

### Base Class Architecture
- Maintain inheritance from appropriate base classes
- Ensure `PlotBase` provides common functionality
- Implement specialized plot types (histograms, scatter, orbits)
- Support both static and interactive plotting

### Label System Management
```python
# TeXlabel system for consistent formatting
from solarwindpy.plotting.labels import TeXlabel

class PlotBase:
    def set_labels(self):
        """Apply TeXlabel formatting to axes."""
        self.xlabel = TeXlabel(self.x_quantity)
        self.ylabel = TeXlabel(self.y_quantity)
        self.ax.set_xlabel(self.xlabel.tex_string)
        self.ax.set_ylabel(self.ylabel.tex_string)
```

## Plot Types Implementation

### 1D Histograms
```python
class Hist1D(PlotBase):
    """Single-variable histogram with statistical overlays."""
    
    def __init__(self, data, bins='auto', density=True):
        self.data = data
        self.bins = bins
        self.density = density
        
    def plot(self, ax=None, **kwargs):
        if ax is None:
            fig, ax = plt.subplots()
        
        n, bins, patches = ax.hist(
            self.data, 
            bins=self.bins,
            density=self.density,
            **kwargs
        )
        
        # Add statistical annotations
        self.add_statistics(ax)
        return ax
    
    def add_statistics(self, ax):
        """Add mean, median, std annotations."""
        stats_text = (
            f'μ = {np.mean(self.data):.2f}\n'
            f'σ = {np.std(self.data):.2f}\n'
            f'N = {len(self.data)}'
        )
        ax.text(0.7, 0.95, stats_text, 
                transform=ax.transAxes,
                verticalalignment='top')
```

### 2D Histograms
```python
class Hist2D(PlotBase):
    """Two-variable histogram with density contours."""
    
    def plot(self, ax=None, cmap='viridis', **kwargs):
        if ax is None:
            fig, ax = plt.subplots()
            
        h = ax.hist2d(self.x, self.y, 
                      bins=self.bins,
                      cmap=cmap,
                      **kwargs)
        
        # Add contours
        if self.add_contours:
            self.plot_contours(ax, h)
            
        # Add colorbar
        plt.colorbar(h[3], ax=ax, label='Counts')
        return ax
```

### Scatter Plots
```python
class ScatterPlot(PlotBase):
    """Enhanced scatter plot with regression options."""
    
    def plot_with_regression(self, ax=None):
        """Scatter plot with linear regression."""
        ax = self.plot(ax)
        
        # Add regression line
        z = np.polyfit(self.x, self.y, 1)
        p = np.poly1d(z)
        ax.plot(self.x, p(self.x), 'r--', 
                label=f'y = {z[0]:.2f}x + {z[1]:.2f}')
        
        # Add correlation coefficient
        r = np.corrcoef(self.x, self.y)[0, 1]
        ax.text(0.05, 0.95, f'r = {r:.3f}',
                transform=ax.transAxes)
        
        ax.legend()
        return ax
```

### Orbit Plots
```python
class OrbitPlot(PlotBase):
    """Spacecraft orbit visualization."""
    
    def plot_3d(self, fig=None):
        """3D orbit trajectory."""
        if fig is None:
            fig = plt.figure(figsize=(10, 8))
            
        ax = fig.add_subplot(111, projection='3d')
        
        ax.plot(self.x, self.y, self.z)
        ax.set_xlabel('X [AU]')
        ax.set_ylabel('Y [AU]')
        ax.set_zlabel('Z [AU]')
        
        # Add Earth
        self.add_earth(ax)
        
        return ax
```

## Style Guidelines

### Color Schemes
```python
# Colorblind-friendly palettes
COLORS = {
    'qualitative': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'],
    'sequential': plt.cm.viridis,
    'diverging': plt.cm.RdBu_r
}

def get_color_palette(n_colors, palette_type='qualitative'):
    """Get appropriate color palette."""
    if palette_type == 'qualitative':
        return COLORS['qualitative'][:n_colors]
    elif palette_type == 'sequential':
        return plt.cm.viridis(np.linspace(0, 1, n_colors))
```

### Figure Defaults
```python
# Publication-quality defaults
plt.rcParams.update({
    'figure.figsize': (8, 6),
    'figure.dpi': 100,
    'savefig.dpi': 300,
    'font.size': 12,
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 12,
    'lines.linewidth': 2,
    'lines.markersize': 8
})
```

## Special Features

### Log-Scale Handling
```python
def set_log_scale(ax, xlog=False, ylog=False):
    """Properly handle log scales with zero/negative values."""
    if xlog:
        # Filter out non-positive values
        mask = ax.lines[0].get_xdata() > 0
        if not mask.all():
            warnings.warn("Removing non-positive x values for log scale")
        ax.set_xscale('log')
        
    if ylog:
        mask = ax.lines[0].get_ydata() > 0
        if not mask.all():
            warnings.warn("Removing non-positive y values for log scale")
        ax.set_yscale('log')
```

### Interactive Features
```python
class InteractivePlot(PlotBase):
    """Support for interactive data selection."""
    
    def enable_selection(self):
        """Enable point selection with mouse."""
        self.selected = []
        
        def on_click(event):
            if event.inaxes:
                # Find nearest point
                distances = np.sqrt((self.x - event.xdata)**2 + 
                                  (self.y - event.ydata)**2)
                idx = np.argmin(distances)
                self.selected.append(idx)
                
                # Highlight selected point
                event.inaxes.plot(self.x[idx], self.y[idx], 
                                'ro', markersize=10)
                plt.draw()
        
        self.fig.canvas.mpl_connect('button_press_event', on_click)
```

## Label Formatting

### TeXlabel Integration
```python
class TeXlabel:
    """Generate TeX-formatted labels for physical quantities."""
    
    LABELS = {
        'n': r'$n$ [cm$^{-3}$]',
        'v': r'$v$ [km/s]',
        'b': r'$B$ [nT]',
        'T': r'$T$ [K]',
        'beta': r'$\beta$',
        'vth': r'$v_{th}$ [km/s]'
    }
    
    def __init__(self, quantity, species=None):
        self.quantity = quantity
        self.species = species
        
    @property
    def tex_string(self):
        base = self.LABELS.get(self.quantity, self.quantity)
        if self.species:
            base = base.replace('$', f'$_{{{self.species}}}')
        return base
```

## Testing Visualization

### Plot Testing Without Display
```python
def test_plot_generation():
    """Test plot creation without displaying."""
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    
    fig, ax = plt.subplots()
    plot = Hist1D(data)
    plot.plot(ax)
    
    # Check plot elements exist
    assert len(ax.patches) > 0  # Histogram bars
    assert ax.get_xlabel() != ''  # Label set
    
    # Save to buffer for validation
    from io import BytesIO
    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    assert len(buf.read()) > 0
    
    plt.close(fig)
```

## Performance Optimization

### Large Dataset Handling
```python
def plot_large_dataset(x, y, max_points=10000):
    """Downsample for performance."""
    if len(x) > max_points:
        # Intelligent downsampling
        idx = np.random.choice(len(x), max_points, replace=False)
        idx.sort()  # Maintain time order
        x_plot = x[idx]
        y_plot = y[idx]
    else:
        x_plot, y_plot = x, y
        
    plt.plot(x_plot, y_plot, 'o', markersize=1, alpha=0.5)
```

### Caching
```python
class CachedPlot:
    """Cache rendered plots for reuse."""
    
    def __init__(self):
        self._cache = {}
        
    def get_plot(self, data_hash):
        if data_hash not in self._cache:
            self._cache[data_hash] = self.generate_plot()
        return self._cache[data_hash]
```

## Integration Points

- Uses data structures from **DataFrameArchitect**
- Visualizes fits from **FitFunctionSpecialist**
- Follows physics conventions from **PhysicsValidator**
- Tested by **TestEngineer** for correctness

## Common Issues

1. **Memory leaks**: Always close figures after saving
2. **Backend issues**: Use appropriate backend for environment
3. **Font rendering**: Ensure LaTeX fonts available
4. **Color accessibility**: Test with colorblind simulators
5. **Performance**: Profile plotting of large datasets