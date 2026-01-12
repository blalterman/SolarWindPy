# SolarWindPy Test Patterns Guide

This guide documents test quality patterns established through practical test auditing.
These patterns ensure tests verify their claimed behavior, not just "something works."

## Test Quality Audit Criteria

When reviewing or writing tests, verify:

1. **Name accuracy**: Does the test name describe what is actually tested?
2. **Assertion validity**: Do assertions verify the claimed behavior?
3. **Parameter verification**: Are parameters verified to reach their targets?

---

## Core Patterns

### 1. Mock-with-Wraps for Method Dispatch Verification

Proves the correct internal method was called while still executing real code:

```python
from unittest.mock import patch

# GOOD: Verifies _interpolate_with_rbf is called when method="rbf"
with patch.object(
    instance, "_interpolate_with_rbf",
    wraps=instance._interpolate_with_rbf
) as mock:
    result = instance.plot_contours(ax=ax, method="rbf")
    mock.assert_called_once()
```

**Why `wraps`?** Without `wraps`, the mock replaces the method entirely. With `wraps`,
the real method executes but we can verify it was called and inspect arguments.

### 2. Parameter Passthrough Verification

Use **distinctive non-default values** to prove parameters reach their targets:

```python
# GOOD: Use 77 (not default) and verify it arrives
with patch.object(instance, "_interpolate_with_rbf",
                  wraps=instance._interpolate_with_rbf) as mock:
    instance.plot_contours(ax=ax, rbf_neighbors=77)
    mock.assert_called_once()
    assert mock.call_args.kwargs["neighbors"] == 77, (
        f"Expected neighbors=77, got {mock.call_args.kwargs['neighbors']}"
    )

# BAD: Uses default value - can't tell if parameter was ignored
instance.plot_contours(ax=ax, rbf_neighbors=20)  # 20 might be default!
```

### 3. Patch Where Defined, Not Where Imported

When a function is imported locally (`from .tools import func`), patch at the definition site:

```python
# GOOD: Patch at definition site
with patch("solarwindpy.plotting.tools.nan_gaussian_filter",
           wraps=nan_gaussian_filter) as mock:
    ...

# BAD: Patch where it's used (AttributeError if imported locally)
with patch("solarwindpy.plotting.spiral.nan_gaussian_filter", ...):  # fails
    ...
```

### 4. Three-Layer Assertion Pattern

Every method test should verify three things:

```python
def test_method_respects_parameter(self, instance):
    # Layer 1: Method dispatch (mock verifies correct path)
    with patch.object(instance, "_helper", wraps=instance._helper) as mock:
        result = instance.method(param=77)
        mock.assert_called_once()

        # Layer 2: Return type verification
        assert isinstance(result, ExpectedType)

        # Layer 3: Behavior claim (what test name promises)
        assert mock.call_args.kwargs["param"] == 77
```

### 5. Test Name Must Match Assertions

If test is named `test_X_respects_Y`, the assertions MUST verify Y reaches X:

```python
# Test name: test_grid_respects_gaussian_filter_std
# MUST verify gaussian_filter_std parameter reaches the filter
# NOT just "output exists"
```

---

## Type Verification Patterns

### 6. Return Type Verification

```python
# Tuple length with descriptive message
assert len(result) == 4, "Should return 4-tuple"

# Unpack and check each element
ret_ax, lbls, cbar, qset = result
assert isinstance(ret_ax, matplotlib.axes.Axes), "First element should be Axes"
```

### 7. Conditional Type Checking for Optional Values

```python
# Handle None and empty cases properly
if lbls is not None:
    assert isinstance(lbls, list), "Labels should be a list"
    if len(lbls) > 0:
        assert all(
            isinstance(lbl, matplotlib.text.Text) for lbl in lbls
        ), "All labels should be Text objects"
```

### 8. hasattr for Duck Typing

When exact type is unknown or multiple types are valid:

```python
# Verify interface, not specific type
assert hasattr(qset, "levels"), "qset should have levels attribute"
assert hasattr(qset, "allsegs"), "qset should have allsegs attribute"
```

### 9. Identity Assertions for Same-Object Verification

```python
# Verify same object returned, not just equal value
assert mappable is qset, "With cbar=False, should return qset as third element"
```

### 10. Positive AND Negative isinstance (Mutual Exclusion)

When behavior differs based on return type:

```python
# Verify IS the expected type
assert isinstance(mappable, matplotlib.contour.ContourSet), (
    "mappable should be ContourSet when cbar=False"
)
# Verify is NOT the alternative type
assert not isinstance(mappable, matplotlib.colorbar.Colorbar), (
    "mappable should not be Colorbar when cbar=False"
)
```

---

## Quality Patterns

### 11. Error Messages with Context

Include actual vs expected for debugging:

```python
assert call_kwargs["neighbors"] == 77, (
    f"Expected neighbors=77, got neighbors={call_kwargs['neighbors']}"
)
```

### 12. Testing Behavior Attributes

Verify state, not just type:

```python
# qset.filled is True for contourf, False for contour
assert qset.filled, "use_contourf=True should produce filled contours"
```

### 13. pytest.raises with Pattern Match

Verify error type AND message content:

```python
with pytest.raises(ValueError, match="Invalid method"):
    instance.plot_contours(ax=ax, method="invalid_method")
```

### 14. Fixture Patterns

```python
@pytest.fixture
def spiral_plot_instance(self):
    """Minimal SpiralPlot2D with initialized mesh."""
    # Controlled randomness for reproducibility
    np.random.seed(42)
    x = pd.Series(np.random.uniform(1, 100, 500))
    y = pd.Series(np.random.uniform(1, 100, 500))
    z = pd.Series(np.sin(x / 10) * np.cos(y / 10))
    splot = SpiralPlot2D(x, y, z, initial_bins=5)
    splot.initialize_mesh(min_per_bin=10)
    splot.build_grouped()
    return splot

# Derived fixtures build on base fixtures
@pytest.fixture
def spiral_plot_with_nans(self, spiral_plot_instance):
    """SpiralPlot2D with NaN values in z-data."""
    data = spiral_plot_instance.data.copy()
    data.loc[data.index[::10], "z"] = np.nan
    spiral_plot_instance._data = data
    spiral_plot_instance.build_grouped()
    return spiral_plot_instance
```

### 15. Resource Cleanup

Always close matplotlib figures to prevent resource leaks:

```python
def test_something(self, instance):
    fig, ax = plt.subplots()
    # ... test code ...
    plt.close()  # Always cleanup
```

### 16. Integration Test as Smoke Test

Loop through variants to verify all code paths execute:

```python
def test_all_methods_produce_output(self, instance):
    """Smoke test: all methods run without error."""
    for method in ["rbf", "grid", "tricontour"]:
        result = instance.plot_contours(ax=ax, method=method)
        assert result is not None, f"{method} should return result"
        assert len(result[3].levels) > 0, f"{method} should produce levels"
    plt.close()
```

---

## Anti-Patterns to Avoid

### Trivial/Meaningless Assertions

```python
# BAD: Trivially true, doesn't test behavior
assert result is not None
assert ax is not None  # Axes are always returned
assert qset is not None  # Doesn't verify it's the expected type

# BAD: Proves nothing about correctness
assert len(output) > 0  # Without type check
```

### Missing Verification of Code Path

```python
# BAD: Output exists, but was correct method used?
def test_rbf_method(self, instance):
    result = instance.method(method="rbf")
    assert result is not None  # Doesn't prove RBF was used!
```

### Using Default Parameter Values

```python
# BAD: Can't distinguish if parameter was ignored
instance.method(neighbors=20)  # If 20 is default, test proves nothing
```

### Missing Resource Cleanup

```python
# BAD: Resource leak in test suite
def test_plot(self):
    fig, ax = plt.subplots()
    # ... test ...
    # Missing plt.close()!
```

### Assertions Without Error Messages

```python
# BAD: Hard to debug failures
assert x == 77

# GOOD: Clear failure message
assert x == 77, f"Expected 77, got {x}"
```

---

## SolarWindPy-Specific Types Reference

Common types to verify with `isinstance`:

### Matplotlib Types
- `matplotlib.axes.Axes` - Plot axes
- `matplotlib.figure.Figure` - Figure container
- `matplotlib.colorbar.Colorbar` - Colorbar object
- `matplotlib.contour.QuadContourSet` - Regular contour result
- `matplotlib.contour.ContourSet` - Base contour class
- `matplotlib.tri.TriContourSet` - Triangulated contour result
- `matplotlib.text.Text` - Text labels

### Pandas Types
- `pandas.DataFrame` - Data container
- `pandas.Series` - Single column
- `pandas.MultiIndex` - Hierarchical index (M/C/S structure)

### NumPy Types
- `numpy.ndarray` - Array data
- `numpy.floating` - Float scalar

---

## Real Example: TestSpiralPlot2DContours

From `tests/plotting/test_spiral.py`, a well-structured test:

```python
def test_rbf_respects_neighbors_parameter(self, spiral_plot_instance):
    """Test that RBF neighbors parameter is passed to interpolator."""
    fig, ax = plt.subplots()

    # Layer 1: Method dispatch verification
    with patch.object(
        spiral_plot_instance,
        "_interpolate_with_rbf",
        wraps=spiral_plot_instance._interpolate_with_rbf,
    ) as mock_rbf:
        spiral_plot_instance.plot_contours(
            ax=ax, method="rbf", rbf_neighbors=77,  # Distinctive value
            cbar=False, label_levels=False
        )
        mock_rbf.assert_called_once()

        # Layer 3: Parameter verification (what test name promises)
        call_kwargs = mock_rbf.call_args.kwargs
        assert call_kwargs["neighbors"] == 77, (
            f"Expected neighbors=77, got neighbors={call_kwargs['neighbors']}"
        )
    plt.close()
```

This test:
- Uses mock-with-wraps to verify method dispatch
- Uses distinctive value (77) to prove parameter passthrough
- Includes contextual error message
- Cleans up resources with plt.close()

---

## Automated Anti-Pattern Detection with ast-grep

Use ast-grep MCP tools to automatically detect anti-patterns across the codebase.
AST-aware patterns are far superior to regex for structural code analysis.

### Trivial Assertion Detection

```yaml
# Find all `assert X is not None` (potential anti-pattern)
id: trivial-not-none-assertion
language: python
rule:
  pattern: assert $X is not None
```

**Usage:**
```
ast-grep find_code --pattern "assert $X is not None" --language python
```

**Current state:** 133 instances in codebase (audit recommended)

### Mock Without Wraps Detection

```yaml
# Find patch.object WITHOUT wraps= (potential weak test)
id: mock-without-wraps
language: python
rule:
  pattern: patch.object($INSTANCE, $METHOD)
  not:
    has:
      pattern: wraps=$_
```

**Find correct usage:**
```yaml
# Find patch.object WITH wraps= (good pattern)
id: mock-with-wraps
language: python
rule:
  pattern: patch.object($INSTANCE, $METHOD, wraps=$WRAPPED)
```

**Current state:** 76 without wraps vs 4 with wraps (major improvement opportunity)

### Resource Leak Detection

```yaml
# Find plt.subplots() calls (verify each has plt.close())
id: plt-subplots-calls
language: python
rule:
  pattern: plt.subplots()
```

**Current state:** 59 instances (manual audit required for cleanup verification)

### Quick Audit Commands

```bash
# Count trivial assertions
ast-grep find_code -p "assert $X is not None" -l python tests/ | wc -l

# Find mocks missing wraps
ast-grep scan --inline-rules 'id: x
language: python
rule:
  pattern: patch.object($I, $M)
  not:
    has:
      pattern: wraps=$_' tests/

# Find good mock patterns (should increase over time)
ast-grep find_code -p "patch.object($I, $M, wraps=$W)" -l python tests/
```

### Integration with TestEngineer Agent

The TestEngineer agent uses ast-grep MCP for automated anti-pattern detection:
- `mcp__ast-grep__find_code` - Simple pattern searches
- `mcp__ast-grep__find_code_by_rule` - Complex YAML rules with constraints
- `mcp__ast-grep__test_match_code_rule` - Test rules before running

**Example audit workflow:**
1. Run anti-pattern detection rules
2. Review flagged code locations
3. Apply patterns from this guide to fix issues
4. Re-run detection to verify fixes
