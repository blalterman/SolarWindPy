# Phase 1: Structure Preparation

## Phase Tasks
- [ ] **Create organized directory structure** (Est: 30 min) - Set up /tests/ hierarchy matching package structure
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Plan conftest.py consolidation strategy** (Est: 20 min) - Analyze existing fixtures for merge strategy
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Identify all files requiring migration** (Est: 10 min) - Complete inventory of 22 test files + data files
  - Commit: `<checksum>`
  - Status: Pending

## Expected Directory Structure
```
/tests/
├── conftest.py                    # Consolidated fixtures
├── data/                          # Test data files
│   ├── epoch.csv
│   ├── plasma.csv
│   └── spacecraft.csv
├── fitfunctions/                  # Fitfunction tests (existing)
│   ├── conftest.py               # Fitfunction-specific fixtures
│   ├── test_core.py
│   ├── test_exponentials.py
│   ├── test_gaussians.py
│   ├── test_lines.py
│   ├── test_moyal.py
│   ├── test_plots.py
│   ├── test_power_laws.py
│   ├── test_tex_info.py
│   ├── test_trend_fit_properties.py
│   └── test_trend_fits.py
├── core/                          # Core module tests (migrated)
│   ├── test_alfvenic_turbulence.py
│   ├── test_base.py
│   ├── test_base_head_tail.py
│   ├── test_base_mi_tuples.py
│   ├── test_core_verify_datetimeindex.py
│   ├── test_ions.py
│   ├── test_plasma.py
│   ├── test_plasma_io.py
│   ├── test_quantities.py
│   ├── test_spacecraft.py
│   └── test_units_constants.py
├── plotting/                      # Plotting tests (migrated)
│   └── labels/
│       ├── test_base.py
│       ├── test_chemistry.py
│       ├── test_composition.py
│       ├── test_datetime.py
│       └── test_init.py
├── test_circular_imports.py       # Utility tests (migrated)
├── test_issue_titles.py
└── test_planning_agents_architecture.py
```

## Migration Inventory

### Files to Migrate (22 core + data files)
From `/solarwindpy/tests/`:
- 11 core module tests
- 5 plotting label tests  
- 3 utility tests
- 3 test data files (CSV format)
- 2 configuration files

### Files Already in Place (11 fitfunction tests)
In `/tests/fitfunctions/`:
- All fitfunction tests are correctly positioned
- Dedicated conftest.py with specialized fixtures
- Standard external package import patterns

## Consolidation Strategy
1. **Preserve fitfunction test structure** - Already follows best practices
2. **Mirror package hierarchy** - Create /tests/core/, /tests/plotting/ subdirectories
3. **Consolidate fixtures** - Merge conftest.py configurations intelligently
4. **Maintain test data integrity** - Relocate with proper path updates

## Navigation
- **Next Phase**: [2-File-Migration.md](./2-File-Migration.md)
- **Overview**: [0-Overview.md](./0-Overview.md)