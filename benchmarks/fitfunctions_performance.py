#!/usr/bin/env python
"""Benchmark Phase 4 performance optimizations."""

import time
import numpy as np
import pandas as pd
import sys
import os

# Add the parent directory to sys.path to import solarwindpy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from solarwindpy.fitfunctions import Gaussian
from solarwindpy.fitfunctions.trend_fits import TrendFit


def benchmark_trendfit(n_fits=50):
    """Compare sequential vs parallel TrendFit performance."""
    print(f"\nBenchmarking with {n_fits} fits...")
    
    # Create synthetic data that's realistic for fitting
    np.random.seed(42)
    x = np.linspace(0, 10, 100)
    data = pd.DataFrame({
        f'col_{i}': 5 * np.exp(-(x-5)**2/2) + np.random.normal(0, 0.1, 100)
        for i in range(n_fits)
    }, index=x)
    
    # Sequential execution
    print("  Running sequential...")
    tf_seq = TrendFit(data, Gaussian, ffunc1d=Gaussian)
    tf_seq.make_ffunc1ds()
    
    start = time.perf_counter()
    tf_seq.make_1dfits(n_jobs=1)
    seq_time = time.perf_counter() - start
    
    # Parallel execution
    print("  Running parallel...")
    tf_par = TrendFit(data, Gaussian, ffunc1d=Gaussian)
    tf_par.make_ffunc1ds()
    
    start = time.perf_counter()
    tf_par.make_1dfits(n_jobs=-1)
    par_time = time.perf_counter() - start
    
    speedup = seq_time / par_time
    print(f"  Sequential: {seq_time:.2f}s")
    print(f"  Parallel:   {par_time:.2f}s")
    print(f"  Speedup:    {speedup:.1f}x")
    
    # Verify results match
    print("  Verifying results match...")
    successful_fits = 0
    for key in tf_seq.ffuncs.index:
        if key in tf_par.ffuncs.index:  # Both succeeded
            seq_popt = tf_seq.ffuncs[key].popt
            par_popt = tf_par.ffuncs[key].popt
            for param in seq_popt:
                np.testing.assert_allclose(
                    seq_popt[param], par_popt[param], 
                    rtol=1e-10, atol=1e-10
                )
            successful_fits += 1
    
    print(f"  ✓ {successful_fits} fits verified identical")
    
    return speedup, successful_fits


def benchmark_single_fitfunction():
    """Benchmark single FitFunction to understand baseline performance."""
    print("\nBenchmarking single FitFunction...")
    
    np.random.seed(42)
    x = np.linspace(0, 10, 100)
    y = 5 * np.exp(-(x-5)**2/2) + np.random.normal(0, 0.1, 100)
    
    # Time creation and fitting
    start = time.perf_counter()
    ff = Gaussian(x, y)
    creation_time = time.perf_counter() - start
    
    start = time.perf_counter()
    ff.make_fit()
    fit_time = time.perf_counter() - start
    
    total_time = creation_time + fit_time
    
    print(f"  Creation time: {creation_time*1000:.1f}ms")
    print(f"  Fitting time:  {fit_time*1000:.1f}ms")
    print(f"  Total time:    {total_time*1000:.1f}ms")
    
    return total_time


def check_joblib_availability():
    """Check if joblib is available for parallel processing."""
    try:
        import joblib
        print(f"✓ joblib {joblib.__version__} available")
        
        # Check number of cores
        import os
        n_cores = os.cpu_count()
        print(f"✓ {n_cores} CPU cores detected")
        return True
    except ImportError:
        print("✗ joblib not available - only sequential benchmarks will run")
        return False


if __name__ == "__main__":
    print("FitFunctions Phase 4 Performance Benchmark")
    print("=" * 50)
    
    # Check system capabilities
    has_joblib = check_joblib_availability()
    
    # Single fit baseline
    single_time = benchmark_single_fitfunction()
    
    # TrendFit scaling benchmarks
    speedups = []
    fit_counts = []
    
    test_sizes = [10, 25, 50, 100]
    if has_joblib:
        # Only run larger tests if joblib is available
        test_sizes.extend([200])
    
    for n in test_sizes:
        expected_seq_time = single_time * n
        print(f"\nExpected sequential time for {n} fits: {expected_seq_time:.1f}s")
        
        try:
            speedup, n_successful = benchmark_trendfit(n)
            speedups.append(speedup)
            fit_counts.append(n_successful)
        except Exception as e:
            print(f"  ✗ Benchmark failed: {e}")
            speedups.append(1.0)
            fit_counts.append(0)
    
    # Summary report
    print("\n" + "=" * 50)
    print("BENCHMARK SUMMARY")
    print("=" * 50)
    
    print(f"Single fit baseline: {single_time*1000:.1f}ms")
    
    if speedups:
        print("\nTrendFit Scaling Results:")
        print("Fits | Successful | Speedup")
        print("-" * 30)
        for i, n in enumerate(test_sizes):
            if i < len(speedups):
                print(f"{n:4d} | {fit_counts[i]:10d} | {speedups[i]:7.1f}x")
        
        if has_joblib:
            avg_speedup = np.mean(speedups)
            best_speedup = max(speedups)
            print(f"\nAverage speedup: {avg_speedup:.1f}x")
            print(f"Best speedup:    {best_speedup:.1f}x")
            
            # Efficiency analysis
            if avg_speedup > 1.5:
                print("✓ Parallelization provides significant benefit")
            else:
                print("⚠ Parallelization benefit limited (overhead or few cores)")
        else:
            print("\nInstall joblib for parallel processing:")
            print("  pip install joblib")
            print("  or")
            print("  pip install solarwindpy[performance]")
    
    print("\nTo use parallel fitting in your code:")
    print("  tf.make_1dfits(n_jobs=-1)  # Use all cores")
    print("  tf.make_1dfits(n_jobs=4)   # Use 4 cores")