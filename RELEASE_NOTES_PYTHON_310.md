# Python 3.10+ Migration

## Summary
SolarWindPy now requires Python 3.10 or later.

## Background
- Dependencies (NumPy 2.x, Astropy 7.x) already require Python 3.10+
- Python 3.8 reaches end-of-life October 2024
- Reduces CI overhead by 40%

## Changes
- Updated `requires-python` to `>=3.10,<4`
- Removed Python 3.8/3.9 from CI matrix
- Removed compatibility code for older Python versions
- Modernized type hints where applicable

## Migration
For users on Python 3.8/3.9:
1. Update Python to 3.10 or later
2. Update dependencies: `pip install -U solarwindpy`

## Benefits
- 40% CI efficiency improvement
- Cleaner codebase without compatibility layers
- Access to Python 3.10+ performance improvements
- Alignment with scientific Python ecosystem
