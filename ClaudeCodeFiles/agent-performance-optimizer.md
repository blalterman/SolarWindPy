---
name: PerformanceOptimizer
description: Optimizes computational performance using numba, vectorization, and efficient algorithms
priority: medium
tags:
  - performance
  - optimization
  - numba
  - profiling
applies_to:
  - solarwindpy/core/**/*.py
  - solarwindpy/tools/**/*.py
---

# PerformanceOptimizer Agent

## Purpose
Ensures optimal computational performance across the SolarWindPy package through profiling, optimization, and efficient algorithm selection.

## Key Responsibilities

### Numba Optimization
```python
from numba import jit, njit, prange
import numpy as np

@njit(parallel=True, cache=True)
def calculate_coulomb_number(n, T, v_rel, m1, m2, Z1, Z2):
    """Optimized Coulomb number calculation."""
    # Constants
    epsilon_0 = 8.854e-12
    k_B = 1.381e-23
    e = 1.602e-19
    
    # Vectorized operations
    result = np.empty(len(n))
    for i in prange(len(n)):
        # Coulomb logarithm
        lambda_D = np.sqrt(epsilon_0 * k_B * T[i] / (n[i] * e**2))
        b_90 = Z1 * Z2 * e**2 / (4 * np.pi * epsilon_0 * m1 * v_rel[i]**2)
        ln_lambda = np.log(lambda_D / b_90)
        
        # Collision frequency
        nu = 4 * np.pi * n[i] * (Z1 * Z2 * e**2)**2 * ln_lambda
        nu /= (4 * np.pi * epsilon_0)**2 * m1**2 * v_rel[i]**3
        
        # Coulomb number
        result[i] = v_rel[i] / (nu * 1e6)  # Convert to AU
    
    return result
```

### Vectorization Patterns
```python
# Bad: Loop-based calculation
def calculate_beta_slow(n, T, B):
    beta = []
    for i in range(len(n)):
        pressure = n[i] * k_B * T[i]
        mag_pressure = B[i]**2 / (2 * mu_0)
        beta.append(pressure / mag_pressure)
    return np.array(beta)

# Good: Vectorized calculation
def calculate_beta_fast(n, T, B):
    pressure = n * k_B * T
    mag_pressure = B**2 / (2 * mu_0)
    return pressure / mag_pressure
```

### Memory Management
```python
class MemoryEfficientDataFrame:
    """Optimize DataFrame memory usage."""
    
    @staticmethod
    def optimize_dtypes(df):
        """Convert to efficient dtypes."""
        for col in df.columns:
            col_type = df[col].dtype
            
            if col_type != 'object':
                c_min = df[col].min()
                c_max = df[col].max()
                
                # Integer optimization
                if str(col_type)[:3] == 'int':
                    if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                        df[col] = df[col].astype(np.int8)
                    elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                        df[col] = df[col].astype(np.int16)
                    elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                        df[col] = df[col].astype(np.int32)
                
                # Float optimization
                else:
                    if c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                        df[col] = df[col].astype(np.float32)
        
        return df
```

## Profiling Strategies

### Function-Level Profiling
```python
import cProfile
import pstats
from functools import wraps

def profile(func):
    """Decorator for profiling functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        result = func(*args, **kwargs)
        profiler.disable()
        
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        stats.print_stats(10)  # Top 10 time consumers
        
        return result
    return wrapper

@profile
def expensive_calculation():
    # Function to profile
    pass
```

### Line-Level Profiling
```python
# Use line_profiler for detailed analysis
# pip install line_profiler

# @profile decorator for line_profiler
@profile
def detailed_function():
    data = load_data()  # Line 1
    processed = process(data)  # Line 2
    result = calculate(processed)  # Line 3
    return result

# Run with: kernprof -l -v script.py
```

## Caching Strategies

### Function Memoization
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_pure_function(param1, param2):
    """Cache results of expensive calculations."""
    # Complex calculation
    return result

# Clear cache when needed
expensive_pure_function.cache_clear()
```

### Property Caching
```python
class Plasma:
    def __init__(self, data):
        self.data = data
        self._beta = None
    
    @property
    def beta(self):
        """Lazy calculation with caching."""
        if self._beta is None:
            self._beta = self._calculate_beta()
        return self._beta
    
    def _calculate_beta(self):
        # Expensive calculation
        return result
```

## Parallel Processing

### Multiprocessing for Independent Tasks
```python
from multiprocessing import Pool
import numpy as np

def process_time_window(args):
    """Process single time window."""
    data, start, end = args
    window = data[start:end]
    return calculate_statistics(window)

def parallel_analysis(data, window_size=1000):
    """Parallel processing of time series."""
    n_windows = len(data) // window_size
    
    # Prepare arguments for parallel processing
    args = [(data, i*window_size, (i+1)*window_size) 
            for i in range(n_windows)]
    
    # Process in parallel
    with Pool() as pool:
        results = pool.map(process_time_window, args)
    
    return np.concatenate(results)
```

### Numba Parallel Loops
```python
@njit(parallel=True)
def parallel_distance_matrix(positions):
    """Calculate distance matrix in parallel."""
    n = len(positions)
    distances = np.zeros((n, n))
    
    for i in prange(n):
        for j in range(i+1, n):
            dist = np.sqrt(np.sum((positions[i] - positions[j])**2))
            distances[i, j] = dist
            distances[j, i] = dist
    
    return distances
```

## Algorithm Selection

### Choosing Efficient Algorithms
```python
# Bad: O(n²) algorithm
def find_duplicates_slow(array):
    duplicates = []
    for i in range(len(array)):
        for j in range(i+1, len(array)):
            if array[i] == array[j]:
                duplicates.append(array[i])
    return duplicates

# Good: O(n) algorithm using hash table
def find_duplicates_fast(array):
    seen = set()
    duplicates = set()
    for item in array:
        if item in seen:
            duplicates.add(item)
        seen.add(item)
    return list(duplicates)
```

### Sparse Matrix Operations
```python
from scipy.sparse import csr_matrix

def efficient_sparse_operations(data):
    """Use sparse matrices for mostly-zero data."""
    # Convert to sparse if density < 10%
    density = np.count_nonzero(data) / data.size
    
    if density < 0.1:
        sparse_data = csr_matrix(data)
        # Efficient sparse operations
        result = sparse_data.dot(sparse_data.T)
        return result.toarray()
    else:
        # Regular dense operations
        return data @ data.T
```

## Benchmarking Framework

```python
import time
import numpy as np
from contextlib import contextmanager

@contextmanager
def timer(name):
    """Context manager for timing code blocks."""
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    print(f"{name}: {elapsed:.4f} seconds")

# Usage
with timer("Data processing"):
    process_large_dataset()

class BenchmarkSuite:
    """Automated performance regression testing."""
    
    def __init__(self):
        self.results = {}
    
    def benchmark(self, func, *args, n_runs=100):
        """Benchmark a function."""
        times = []
        for _ in range(n_runs):
            start = time.perf_counter()
            func(*args)
            times.append(time.perf_counter() - start)
        
        self.results[func.__name__] = {
            'mean': np.mean(times),
            'std': np.std(times),
            'min': np.min(times),
            'max': np.max(times)
        }
    
    def compare_with_baseline(self, baseline):
        """Check for performance regressions."""
        for func_name, current in self.results.items():
            if func_name in baseline:
                ratio = current['mean'] / baseline[func_name]['mean']
                if ratio > 1.1:  # 10% slower
                    warnings.warn(
                        f"Performance regression in {func_name}: "
                        f"{ratio:.1%} slower than baseline"
                    )
```

## Memory Profiling

```python
from memory_profiler import profile as mem_profile

@mem_profile
def memory_intensive_function():
    """Monitor memory usage line by line."""
    large_array = np.zeros((10000, 10000))  # ~800 MB
    result = process(large_array)
    del large_array  # Explicit cleanup
    return result
```

## Integration Points

- Coordinates with **DataFrameArchitect** for memory-efficient structures
- Optimizes calculations from **PhysicsValidator**
- Improves plotting performance for **PlottingEngineer**
- Provides benchmarks for **TestEngineer**

## Performance Checklist

1. **Profile before optimizing** - Identify actual bottlenecks
2. **Vectorize operations** - Use NumPy/Pandas operations
3. **Cache expensive calculations** - Avoid redundant computation
4. **Use appropriate data structures** - Sparse matrices, efficient dtypes
5. **Parallelize independent tasks** - Multiprocessing/numba.prange
6. **Memory management** - Clean up large objects, use views
7. **Algorithm complexity** - Choose O(n) over O(n²) when possible
8. **JIT compilation** - Apply numba to numerical hotspots