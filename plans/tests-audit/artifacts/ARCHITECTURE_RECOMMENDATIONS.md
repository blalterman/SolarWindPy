# Architecture Test Recommendations - SolarWindPy Enhancement

## Executive Summary

Based on the Architecture Compliance Analysis (Grade: B+), this document provides **actionable recommendations for 42 specific architecture tests** that will enhance DataFrame structure validation, memory efficiency, and performance benchmarking in the SolarWindPy test suite.

**Target Coverage Increase**: +5-6% (from 77.1% to 82-83%)  
**Estimated Implementation**: 8-12 hours  
**Priority**: High (foundational architecture validation)

---

## 1. MultiIndex Structure Validation Tests (12 tests)

### 1.1 Core Structure Tests (4 tests)

**File**: `tests/core/test_multiindex_validation.py` (NEW)

#### Test 1: `test_multiindex_column_names_required`
```python
def test_multiindex_column_names_required():
    """Test that MultiIndex columns must have correct names."""
    # Test with missing names
    tuples = [("v", "x", "p1"), ("b", "y", "")]
    bad_index = pd.MultiIndex.from_tuples(tuples)  # No names
    
    # Should warn or fail when creating DataFrame with unnamed levels
    with pytest.warns(UserWarning, match="MultiIndex levels should be named"):
        # Test DataFrame creation validation
        pass
```

#### Test 2: `test_multiindex_level_order_validation`  
```python
def test_multiindex_level_order_validation():
    """Test that MultiIndex levels must be in correct order."""
    # Test incorrect level order (S, C, M instead of M, C, S)
    tuples = [("p1", "x", "v"), ("", "y", "b")]
    wrong_order = pd.MultiIndex.from_tuples(tuples, names=["S", "C", "M"])
    
    # Should detect incorrect level ordering
    with pytest.raises(ValueError, match="MultiIndex levels must be in order"):
        # Test validation function
        pass
```

#### Test 3: `test_multiindex_empty_component_scalar_validation`
```python
def test_multiindex_empty_component_scalar_validation():
    """Test proper handling of empty components for scalar measurements."""
    # Density (scalar) should have empty component
    density_tuples = [("n", "", "p1"), ("n", "", "p2")]
    
    # Velocity (vector) should not have empty component
    with pytest.raises(ValueError, match="Vector measurements require components"):
        velocity_tuples = [("v", "", "p1")]  # Invalid: missing component
```

#### Test 4: `test_multiindex_empty_species_bfield_validation`
```python
def test_multiindex_empty_species_bfield_validation():
    """Test proper handling of empty species for magnetic field."""
    # Magnetic field should have empty species
    bfield_tuples = [("b", "x", ""), ("b", "y", ""), ("b", "z", "")]
    
    # Ion measurements should not have empty species
    with pytest.raises(ValueError, match="Ion measurements require species"):
        ion_tuples = [("n", "", "")]  # Invalid: missing species
```

### 1.2 Hierarchy Consistency Tests (4 tests)

#### Test 5: `test_measurement_component_consistency`
```python
def test_measurement_component_consistency():
    """Test M-C level consistency rules."""
    # Scalar measurements (n, w scalar) must have empty C
    # Vector measurements (v, b) must have x,y,z components
    # Tensor measurements (w tensor) must have par,per components
    
    valid_combinations = [
        ("n", "", "p1"),      # Valid: scalar density
        ("v", "x", "p1"),     # Valid: vector velocity
        ("w", "par", "p1"),   # Valid: tensor thermal speed
        ("b", "z", ""),       # Valid: vector magnetic field
    ]
    
    invalid_combinations = [
        ("n", "x", "p1"),     # Invalid: scalar with component
        ("v", "", "p1"),      # Invalid: vector without component
        ("b", "par", ""),     # Invalid: wrong component for B-field
    ]
```

#### Test 6: `test_species_measurement_consistency`
```python
def test_species_measurement_consistency():
    """Test M-S level consistency rules."""
    # Magnetic field (b) must have empty species
    # Ion measurements must have valid species
    # Multi-species combinations validation
    
    valid_species = ["p1", "p2", "a", "e"]
    invalid_species = ["", "x", "invalid"]
```

#### Test 7: `test_multiindex_dataframe_creation_validation`
```python
def test_multiindex_dataframe_creation_validation():
    """Test DataFrame creation with various MultiIndex configurations."""
    # Test successful creation with proper structure
    # Test failure modes with invalid structures
    # Test warning generation for questionable structures
```

#### Test 8: `test_multiindex_level_access_patterns`
```python
def test_multiindex_level_access_patterns():
    """Test proper level access methods."""
    # Test level="M" vs level=0 (should prefer level name)
    # Test xs() vs iloc/loc patterns
    # Test IndexSlice usage patterns
```

### 1.3 Integration Tests (4 tests)

#### Test 9: `test_plasma_multiindex_integration`
```python
def test_plasma_multiindex_integration():
    """Test Plasma class MultiIndex requirements."""
    # Test Plasma object creation with various MultiIndex configurations
    # Test validation of input DataFrames
    # Test error handling for invalid structures
```

#### Test 10: `test_ion_multiindex_integration`
```python
def test_ion_multiindex_integration():
    """Test Ion class MultiIndex requirements."""
    # Test Ion object creation with species-specific data
    # Test validation of M-C level consistency for ions
    # Test error handling for invalid ion data structures
```

#### Test 11: `test_spacecraft_multiindex_integration`
```python
def test_spacecraft_multiindex_integration():
    """Test spacecraft data MultiIndex patterns."""
    # Test coordinate system MultiIndex structures
    # Test position/velocity MultiIndex validation
    # Test spacecraft data integration with plasma data
```

#### Test 12: `test_cross_module_multiindex_consistency`
```python
def test_cross_module_multiindex_consistency():
    """Test MultiIndex consistency across modules."""
    # Test data exchange between Plasma, Ion, Spacecraft
    # Test MultiIndex preservation during operations
    # Test consistency validation across module boundaries
```

---

## 2. Memory Efficiency Tests (10 tests)

### 2.1 View vs Copy Tests (4 tests)

**File**: `tests/core/test_dataframe_memory.py` (NEW)

#### Test 13: `test_xs_returns_view_not_copy`
```python
def test_xs_returns_view_not_copy():
    """Test that xs() operations return views, not copies."""
    data = create_test_plasma_data()
    
    # Test that xs() returns view
    view = data.xs("v", level="M")
    original_value = data.iloc[0, 0]
    
    # Modify view
    view.iloc[0, 0] = original_value + 1000
    
    # Original should be modified (proving it's a view)
    assert data.iloc[0, 0] == original_value + 1000
```

#### Test 14: `test_memory_usage_comparison_view_vs_copy`
```python
def test_memory_usage_comparison_view_vs_copy():
    """Compare memory usage of view vs copy operations."""
    large_data = create_large_test_data(n_points=50000)
    
    # Measure view memory
    view = large_data.xs("v", level="M")
    view_memory = view.memory_usage(deep=True).sum()
    
    # Measure copy memory  
    copy = large_data.xs("v", level="M").copy()
    copy_memory = copy.memory_usage(deep=True).sum()
    
    # View should use significantly less memory
    assert view_memory < copy_memory * 0.1  # View should be <10% of copy
```

#### Test 15: `test_chained_xs_operations_memory`
```python
def test_chained_xs_operations_memory():
    """Test memory efficiency of chained xs() operations."""
    data = create_test_plasma_data()
    
    # Single operation
    single_op = data.xs("v", level="M").xs("p1", level="S")
    
    # Chained operations should not create intermediate copies
    memory_before = get_process_memory()
    result = data.xs("v", level="M").xs("p1", level="S")
    memory_after = get_process_memory()
    
    memory_increase = memory_after - memory_before
    assert memory_increase < 1.0  # Less than 1MB increase
```

#### Test 16: `test_dataframe_slice_memory_efficiency`
```python
def test_dataframe_slice_memory_efficiency():
    """Test memory efficiency of different slicing methods."""
    data = create_test_plasma_data()
    
    # Compare memory usage of different access patterns
    patterns = [
        lambda df: df.xs("v", level="M"),
        lambda df: df.loc[:, pd.IndexSlice["v", :, :]],
        lambda df: df[df.columns[df.columns.get_level_values("M") == "v"]],
    ]
    
    # Test that xs() is most memory efficient
```

### 2.2 Large Dataset Tests (3 tests)

#### Test 17: `test_large_multiindex_dataframe_memory`
```python
def test_large_multiindex_dataframe_memory():
    """Test memory usage with large MultiIndex DataFrames."""
    sizes = [1000, 10000, 100000]
    memory_usages = []
    
    for size in sizes:
        data = create_test_data(n_points=size)
        memory = data.memory_usage(deep=True).sum()
        memory_usages.append(memory)
    
    # Memory should scale linearly with data size
    assert_linear_scaling(sizes, memory_usages, tolerance=0.2)
```

#### Test 18: `test_memory_usage_by_data_type`
```python
def test_memory_usage_by_data_type():
    """Test memory usage with different data types."""
    dtypes = [np.float32, np.float64, np.int32, np.int64]
    
    for dtype in dtypes:
        data = create_test_data(dtype=dtype)
        memory = data.memory_usage(deep=True).sum()
        
        # Verify expected memory usage based on dtype
        expected_memory = calculate_expected_memory(data.shape, dtype)
        assert abs(memory - expected_memory) / expected_memory < 0.1
```

#### Test 19: `test_memory_cleanup_after_operations`
```python
def test_memory_cleanup_after_operations():
    """Test that temporary DataFrames are properly cleaned up."""
    initial_memory = get_process_memory()
    
    # Perform operations that create temporary objects
    for i in range(100):
        data = create_test_data()
        result = data.xs("v", level="M").xs("p1", level="S")
        processed = result.groupby(level=0).mean()
        del data, result, processed
    
    gc.collect()
    final_memory = get_process_memory()
    
    # Memory should return close to initial level
    memory_increase = final_memory - initial_memory
    assert memory_increase < 10.0  # Less than 10MB permanent increase
```

### 2.3 Memory Profiling Tests (3 tests)

#### Test 20: `test_multiindex_operation_memory_profile`
```python
@memory_profiler.profile
def test_multiindex_operation_memory_profile():
    """Profile memory usage of common MultiIndex operations."""
    data = create_large_test_data()
    
    # Profile common operations
    operations = [
        lambda: data.xs("v", level="M"),
        lambda: data.loc[:, pd.IndexSlice["v", :, "p1"]],
        lambda: data.groupby(level=["M", "S"]).mean(),
        lambda: data.reindex(columns=data.columns.sort_values()),
    ]
    
    for op in operations:
        memory_before = get_process_memory()
        result = op()
        memory_after = get_process_memory()
        
        # Log memory usage for each operation
        memory_delta = memory_after - memory_before
        assert memory_delta < 100.0  # Reasonable memory usage
```

#### Test 21: `test_memory_leak_detection`
```python
def test_memory_leak_detection():
    """Test for memory leaks in DataFrame operations."""
    baseline_memory = get_process_memory()
    
    # Repeat operations many times
    for iteration in range(1000):
        data = create_test_data()
        
        # Perform various operations
        v_data = data.xs("v", level="M")
        species_data = v_data.xs("p1", level="S")
        stats = species_data.describe()
        
        # Clean up explicitly
        del data, v_data, species_data, stats
        
        # Check memory every 100 iterations
        if iteration % 100 == 0:
            gc.collect()
            current_memory = get_process_memory()
            memory_growth = current_memory - baseline_memory
            
            # Should not have significant memory growth
            assert memory_growth < 50.0  # Less than 50MB growth
```

#### Test 22: `test_dataframe_copy_detection`
```python
def test_dataframe_copy_detection():
    """Test detection of unexpected DataFrame copies."""
    data = create_test_data()
    original_id = id(data._mgr)  # Access internal data manager
    
    # Operations that should return views
    view_ops = [
        lambda: data.xs("v", level="M"),
        lambda: data.loc[:10],
        lambda: data.iloc[:10],
    ]
    
    for op in view_ops:
        result = op()
        # Verify result shares data with original (implementation dependent)
        # This test helps identify when operations unexpectedly create copies
```

---

## 3. Performance Benchmark Tests (8 tests)

### 3.1 Access Pattern Benchmarks (3 tests)

**File**: `tests/core/test_dataframe_performance.py` (NEW)

#### Test 23: `test_multiindex_access_performance`
```python
def test_multiindex_access_performance():
    """Benchmark different MultiIndex access patterns."""
    data = create_large_test_data(n_points=100000)
    
    # Test access methods
    access_methods = {
        'xs_method': lambda: data.xs("v", level="M"),
        'loc_indexslice': lambda: data.loc[:, pd.IndexSlice["v", :, :]],
        'boolean_mask': lambda: data[data.columns.get_level_values("M") == "v"],
    }
    
    # Benchmark each method
    results = {}
    for name, method in access_methods.items():
        times = []
        for _ in range(10):
            start = time.time()
            result = method()
            end = time.time()
            times.append(end - start)
        
        results[name] = np.mean(times)
    
    # xs() should be fastest
    assert results['xs_method'] < results['boolean_mask']
    assert results['xs_method'] < results['loc_indexslice']
```

#### Test 24: `test_hierarchical_groupby_performance`
```python
def test_hierarchical_groupby_performance():
    """Test performance of groupby operations on MultiIndex."""
    data = create_large_test_data(n_points=100000)
    
    groupby_operations = [
        lambda: data.groupby(level="M").mean(),
        lambda: data.groupby(level=["M", "S"]).mean(),  
        lambda: data.groupby(level=["M", "C", "S"]).mean(),
    ]
    
    # Test that performance scales reasonably with groupby complexity
    for i, op in enumerate(groupby_operations):
        start = time.time()
        result = op()
        duration = time.time() - start
        
        # More complex groupbys should take longer but reasonably so
        assert duration < 10.0  # Should complete within 10 seconds
```

#### Test 25: `test_multiindex_sorting_performance`
```python
def test_multiindex_sorting_performance():
    """Test performance of MultiIndex sorting operations."""
    # Create unsorted data
    data = create_test_data(sorted=False)
    
    sorting_operations = [
        lambda: data.sort_index(axis=1),
        lambda: data.sort_index(axis=1, level="M"),
        lambda: data.sort_index(axis=1, level=["M", "C", "S"]),
    ]
    
    # Test sorting performance
    for op in sorting_operations:
        start = time.time()
        result = op()
        duration = time.time() - start
        
        assert duration < 5.0  # Should complete within 5 seconds
        assert result.columns.is_monotonic_increasing
```

### 3.2 Scalability Tests (3 tests)

#### Test 26: `test_dataframe_size_scalability`
```python
def test_dataframe_size_scalability():
    """Test DataFrame operation performance at different scales."""
    sizes = [1000, 10000, 100000]
    operation_times = []
    
    for size in sizes:
        data = create_test_data(n_points=size)
        
        start = time.time()
        # Standard operations
        v_data = data.xs("v", level="M")
        p1_data = v_data.xs("p1", level="S")
        stats = p1_data.describe()
        end = time.time()
        
        operation_times.append(end - start)
    
    # Performance should scale sub-quadratically
    assert_subquadratic_scaling(sizes, operation_times)
```

#### Test 27: `test_multiindex_column_count_scalability`
```python
def test_multiindex_column_count_scalability():
    """Test performance with increasing column counts."""
    column_counts = [10, 50, 100, 500]
    access_times = []
    
    for count in column_counts:
        data = create_test_data(n_columns=count)
        
        start = time.time()
        result = data.xs("v", level="M")
        duration = time.time() - start
        
        access_times.append(duration)
    
    # Access time should scale linearly with column count
    assert_linear_scaling(column_counts, access_times, tolerance=0.3)
```

#### Test 28: `test_datetime_index_scalability`
```python
def test_datetime_index_scalability():
    """Test performance with large datetime indices."""
    durations = ['1D', '7D', '30D', '365D']  # Data spanning different periods
    
    for duration in durations:
        data = create_time_series_data(duration=duration, freq='1min')
        
        start = time.time()
        # Common time series operations
        hourly = data.resample('1H').mean()
        daily = data.resample('1D').mean() 
        end = time.time()
        
        operation_time = end - start
        assert operation_time < 30.0  # Should complete within 30 seconds
```

### 3.3 Regression Tests (2 tests)

#### Test 29: `test_performance_regression_baseline`
```python
def test_performance_regression_baseline():
    """Establish performance baselines for regression testing."""
    # Standard test data
    data = create_standard_test_data()
    
    # Baseline operations with expected completion times
    baselines = {
        'xs_access': (lambda: data.xs("v", level="M"), 0.01),  # 10ms
        'species_select': (lambda: data.xs("p1", level="S"), 0.01),  # 10ms  
        'component_select': (lambda: data.xs("x", level="C"), 0.01),  # 10ms
        'groupby_mean': (lambda: data.groupby(level="M").mean(), 0.1),  # 100ms
    }
    
    for name, (operation, max_time) in baselines.items():
        times = []
        for _ in range(5):
            start = time.time()
            result = operation()
            end = time.time()
            times.append(end - start)
        
        avg_time = np.mean(times)
        assert avg_time < max_time, f"{name} took {avg_time:.3f}s, expected <{max_time}s"
```

#### Test 30: `test_memory_usage_regression_baseline`
```python
def test_memory_usage_regression_baseline():
    """Establish memory usage baselines for regression testing."""
    # Standard operations with expected memory usage
    data = create_standard_test_data()
    
    memory_baselines = {
        'full_dataframe': (lambda: data, 10.0),  # 10MB
        'velocity_data': (lambda: data.xs("v", level="M"), 2.0),  # 2MB
        'single_species': (lambda: data.xs("p1", level="S"), 5.0),  # 5MB
    }
    
    for name, (operation, max_mb) in memory_baselines.items():
        result = operation()
        memory_mb = result.memory_usage(deep=True).sum() / 1024**2
        
        assert memory_mb < max_mb, f"{name} used {memory_mb:.1f}MB, expected <{max_mb}MB"
```

---

## 4. Edge Case & Integration Tests (7 tests)

### 4.1 Index Consistency Tests (3 tests)

**File**: `tests/core/test_dataframe_edge_cases.py` (NEW)

#### Test 31: `test_datetime_index_validation`
```python
def test_datetime_index_validation():
    """Test DateTime index validation and naming."""
    # Test proper datetime index
    good_index = pd.date_range('2020-01-01', periods=100, freq='1min')
    good_index.name = 'Epoch'
    data = create_test_data(index=good_index)
    
    # Test invalid indices
    bad_indices = [
        pd.RangeIndex(100),  # Non-datetime
        pd.date_range('2020-01-01', periods=100)[::-1],  # Non-monotonic
        pd.date_range('2020-01-01', periods=100, name='time'),  # Wrong name
    ]
    
    for bad_index in bad_indices:
        with pytest.warns(UserWarning):
            invalid_data = create_test_data(index=bad_index)
```

#### Test 32: `test_multiindex_duplicate_handling`
```python
def test_multiindex_duplicate_handling():
    """Test handling of duplicate MultiIndex columns."""
    # Create data with duplicate columns
    tuples = [("v", "x", "p1"), ("v", "x", "p1"), ("b", "y", "")]
    duplicate_columns = pd.MultiIndex.from_tuples(tuples, names=["M", "C", "S"])
    
    # Test detection and handling of duplicates
    with pytest.raises(ValueError, match="Duplicate columns detected"):
        data = pd.DataFrame(np.random.randn(100, 3), columns=duplicate_columns)
        validate_multiindex_structure(data)
```

#### Test 33: `test_missing_level_handling`
```python
def test_missing_level_handling():
    """Test handling of missing MultiIndex levels."""
    # Test missing M level
    tuples = [("", "x", "p1"), ("", "y", "p1")]
    missing_m = pd.MultiIndex.from_tuples(tuples, names=["M", "C", "S"])
    
    # Test missing C level  
    tuples = [("v", "", "p1"), ("v", "", "p2")]
    missing_c = pd.MultiIndex.from_tuples(tuples, names=["M", "C", "S"])
    
    # Test validation of missing required levels
    for invalid_index in [missing_m, missing_c]:
        with pytest.raises(ValueError, match="Required level values missing"):
            validate_multiindex_structure(pd.DataFrame(columns=invalid_index))
```

### 4.2 Data Type Edge Cases (2 tests)

#### Test 34: `test_mixed_data_types_multiindex`
```python
def test_mixed_data_types_multiindex():
    """Test MultiIndex with mixed data types."""
    # Create DataFrame with mixed types
    data = pd.DataFrame({
        ('n', '', 'p1'): np.random.randn(100).astype(np.float32),
        ('v', 'x', 'p1'): np.random.randn(100).astype(np.float64),
        ('w', 'par', 'p1'): np.random.randn(100).astype(np.int32),
    })
    data.columns = pd.MultiIndex.from_tuples(data.columns, names=["M", "C", "S"])
    
    # Test that operations work correctly with mixed types
    result = data.xs("p1", level="S")
    assert isinstance(result, pd.DataFrame)
    
    # Test type preservation
    assert data[('n', '', 'p1')].dtype == np.float32
    assert data[('v', 'x', 'p1')].dtype == np.float64
```

#### Test 35: `test_nan_handling_multiindex_operations`
```python
def test_nan_handling_multiindex_operations():
    """Test NaN handling in MultiIndex operations."""
    data = create_test_data()
    
    # Introduce NaN values
    data.iloc[10:20, :] = np.nan
    data.iloc[:, 2] = np.nan  # Entire column
    
    # Test that MultiIndex operations handle NaN correctly
    v_data = data.xs("v", level="M")
    assert v_data.isna().any().any()  # Should contain NaN
    
    # Test statistics with NaN
    stats = v_data.describe()
    assert not stats.isna().all().any()  # Should compute valid statistics
    
    # Test groupby with NaN
    grouped = data.groupby(level="M").mean()
    assert isinstance(grouped, pd.DataFrame)
```

### 4.3 Integration Edge Cases (2 tests)

#### Test 36: `test_cross_module_dataframe_compatibility`
```python
def test_cross_module_dataframe_compatibility():
    """Test DataFrame compatibility across modules."""
    # Create data in plasma format
    plasma_data = create_test_plasma_data()
    
    # Test Ion object creation
    ion_data = plasma_data.xs("p1", level="S")
    ion = ions.Ion(ion_data, "p1")
    assert isinstance(ion, ions.Ion)
    
    # Test Spacecraft data integration
    sc_data = create_test_spacecraft_data()
    combined = pd.concat([plasma_data, sc_data], axis=1)
    
    # Test that combined data maintains MultiIndex structure
    assert combined.columns.nlevels == 3
    assert list(combined.columns.names) == ["M", "C", "S"]
```

#### Test 37: `test_large_dataset_edge_cases`
```python
def test_large_dataset_edge_cases():
    """Test edge cases with large datasets."""
    # Create very large dataset
    large_data = create_test_data(n_points=1000000)  # 1M points
    
    # Test memory-efficient operations
    subset = large_data.iloc[::1000]  # Sample every 1000th point
    v_subset = subset.xs("v", level="M")
    
    # Test that operations complete without memory errors
    stats = v_subset.describe()
    assert isinstance(stats, pd.DataFrame)
    
    # Test chunked operations
    chunk_size = 10000
    chunk_stats = []
    for i in range(0, len(large_data), chunk_size):
        chunk = large_data.iloc[i:i+chunk_size]
        chunk_stat = chunk.xs("v", level="M").mean()
        chunk_stats.append(chunk_stat)
    
    # Verify chunked processing works
    assert len(chunk_stats) > 1
```

---

## 5. Specialized Architecture Tests (5 tests)

### 5.1 IndexSlice Pattern Tests (2 tests)

**File**: `tests/core/test_indexslice_patterns.py` (NEW)

#### Test 38: `test_indexslice_multiindex_selection`
```python
def test_indexslice_multiindex_selection():
    """Test IndexSlice patterns for MultiIndex selection."""
    data = create_test_data()
    
    # Test various IndexSlice patterns
    patterns = [
        pd.IndexSlice["v", :, :],           # All velocity data
        pd.IndexSlice["v", "x", :],         # All x-components of velocity
        pd.IndexSlice["v", :, "p1"],        # All velocity components for p1
        pd.IndexSlice[["v", "b"], :, :],    # Velocity and magnetic field
        pd.IndexSlice[:, ["x", "y"], :],    # x and y components only
    ]
    
    for pattern in patterns:
        result = data.loc[:, pattern]
        assert isinstance(result, pd.DataFrame)
        
        # Verify selection worked correctly
        if pattern == pd.IndexSlice["v", :, :]:
            assert all(result.columns.get_level_values("M") == "v")
```

#### Test 39: `test_complex_indexslice_combinations`
```python
def test_complex_indexslice_combinations():
    """Test complex IndexSlice combinations."""
    data = create_test_data()
    
    # Complex selection patterns
    complex_patterns = [
        # Velocity x,y components for protons
        (pd.IndexSlice["v", ["x", "y"], ["p1", "p2"]], 
         lambda df: (df.columns.get_level_values("M") == "v") & 
                   df.columns.get_level_values("C").isin(["x", "y"]) &
                   df.columns.get_level_values("S").isin(["p1", "p2"])),
        
        # All vector components (exclude scalars)
        (pd.IndexSlice[:, ["x", "y", "z"], :],
         lambda df: df.columns.get_level_values("C").isin(["x", "y", "z"])),
    ]
    
    for pattern, validator in complex_patterns:
        result = data.loc[:, pattern]
        expected_mask = validator(data)
        expected = data.loc[:, expected_mask]
        
        pd.testing.assert_frame_equal(result.sort_index(axis=1), 
                                    expected.sort_index(axis=1))
```

### 5.2 Performance Optimization Tests (3 tests)

#### Test 40: `test_multiindex_operation_optimization`
```python
def test_multiindex_operation_optimization():
    """Test optimization of common MultiIndex operations."""
    data = create_large_test_data()
    
    # Compare optimized vs unoptimized approaches
    approaches = {
        'optimized_xs': lambda: data.xs("v", level="M").xs("p1", level="S"),
        'chained_loc': lambda: data.loc[:, pd.IndexSlice["v", :, "p1"]],
        'boolean_filter': lambda: data[
            (data.columns.get_level_values("M") == "v") & 
            (data.columns.get_level_values("S") == "p1")
        ],
    }
    
    # Time each approach
    times = {}
    for name, approach in approaches.items():
        start = time.time()
        result = approach()
        times[name] = time.time() - start
    
    # Optimized approach should be fastest
    assert times['optimized_xs'] <= min(times.values()) * 1.1  # Within 10%
```

#### Test 41: `test_dataframe_reindexing_performance`
```python
def test_dataframe_reindexing_performance():
    """Test performance of DataFrame reindexing operations."""
    data = create_test_data(sorted=False)
    
    # Test different reindexing strategies
    strategies = [
        lambda df: df.sort_index(axis=1),
        lambda df: df.reindex(columns=df.columns.sort_values()),
        lambda df: df[df.columns.sort_values()],
    ]
    
    results = []
    for strategy in strategies:
        start = time.time()
        result = strategy(data)
        duration = time.time() - start
        results.append((duration, result))
        
        # Verify result is correctly sorted
        assert result.columns.is_monotonic_increasing
    
    # All strategies should complete in reasonable time
    for duration, _ in results:
        assert duration < 1.0  # Less than 1 second
```

#### Test 42: `test_memory_efficient_aggregations`
```python
def test_memory_efficient_aggregations():
    """Test memory-efficient aggregation operations."""
    data = create_large_test_data()
    
    # Test aggregations that should be memory efficient
    aggregations = [
        ('mean_by_measurement', lambda df: df.groupby(level="M").mean()),
        ('std_by_species', lambda df: df.groupby(level="S").std()),
        ('sum_by_component', lambda df: df.groupby(level="C").sum()),
    ]
    
    for name, aggregation in aggregations:
        memory_before = get_process_memory()
        result = aggregation(data)
        memory_after = get_process_memory()
        
        memory_increase = memory_after - memory_before
        data_memory = data.memory_usage(deep=True).sum() / 1024**2
        
        # Memory increase should be reasonable compared to data size
        assert memory_increase < data_memory * 2  # Less than 2x data size
        assert isinstance(result, pd.DataFrame)
```

---

## 6. Implementation Plan

### 6.1 Phase 1: Core Infrastructure (Tests 1-12, 31-33)
**Duration**: 3-4 hours  
**Files**: 
- `tests/core/test_multiindex_validation.py`
- `tests/core/test_dataframe_edge_cases.py`

**Priority**: High - foundational validation

### 6.2 Phase 2: Memory & Performance (Tests 13-30)
**Duration**: 4-5 hours  
**Files**:
- `tests/core/test_dataframe_memory.py`  
- `tests/core/test_dataframe_performance.py`

**Priority**: High - performance bottleneck identification

### 6.3 Phase 3: Advanced Patterns (Tests 34-42)
**Duration**: 2-3 hours
**Files**:
- `tests/core/test_indexslice_patterns.py`
- Additional tests in existing files

**Priority**: Medium - optimization and edge cases

### 6.4 Integration & Validation
**Duration**: 1 hour
- Run full test suite
- Validate coverage increase
- Performance regression testing

---

## 7. Expected Outcomes

### 7.1 Coverage Metrics
- **Current**: 77.1% overall coverage
- **Target**: 82-83% overall coverage  
- **New Architecture Tests**: 42 tests
- **Estimated Coverage Increase**: +5-6%

### 7.2 Quality Improvements
- **Architecture Validation**: Comprehensive MultiIndex structure testing
- **Memory Efficiency**: Systematic memory usage validation
- **Performance Baselines**: Regression testing infrastructure
- **Edge Case Coverage**: Robust handling of boundary conditions

### 7.3 Maintenance Benefits
- **Regression Prevention**: Performance and memory baselines
- **Development Velocity**: Clear architecture compliance validation
- **Documentation**: Living examples of proper DataFrame usage
- **Onboarding**: Clear patterns for new developers

---

## 8. Metrics & Success Criteria

### 8.1 Quantitative Metrics
- [ ] 42 new architecture tests implemented
- [ ] Test suite coverage ≥82%
- [ ] Architecture compliance grade improves to A-
- [ ] Memory usage tests coverage ≥90%
- [ ] Performance regression tests established

### 8.2 Qualitative Metrics  
- [ ] Clear MultiIndex validation patterns documented
- [ ] Memory efficiency best practices established
- [ ] Performance baselines for regression testing
- [ ] Edge case handling comprehensively tested
- [ ] Integration patterns validated across modules

---

*Generated: 2025-08-21*  
*DataFrameArchitect Agent - Architecture Enhancement Recommendations*  
*SolarWindPy Test Suite Audit - Phase 3 Deliverable*