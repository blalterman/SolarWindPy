# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Agent-Driven Development Protocol

### Primary Workflow
**ALL development work should use agents:**

1. **Complex Tasks**: Use `Task` tool with PlanManager → creates plan → PlanImplementer executes
2. **Git Operations**: GitIntegration agent handles all branch/commit operations  
3. **Testing**: TestEngineer agent ensures comprehensive coverage
4. **Domain Work**: Use specialized agents (PhysicsValidator, PlottingEngineer, etc.)

### Agent Selection
- **Check**: @.claude/agents/agents-index.md for complete agent catalog
- **Coordinate**: Agents handle their domains; avoid manual operations  
- **Escalate**: Use CompactionAgent for session continuity

## Development Commands

### Environment Setup
```bash
# Create and activate conda environment:
conda env create -f solarwindpy-20250403.yml
conda activate solarwindpy-20250403
pip install -e .

# Alternative: generate environment from requirements-dev.txt:
python scripts/requirements_to_conda_env.py --name solarwindpy-dev
conda env create -f solarwindpy-dev.yml
conda activate solarwindpy-dev
pip install -e .
```

### Quality Commands (Agent-Coordinated)
```bash
# These should normally be handled by agents:
pytest -q              # TestEngineer validates
black solarwindpy/     # PerformanceOptimizer formats  
flake8                 # TestEngineer checks
```

### Conda Recipe Management
```bash
# Update recipe when version or dependencies change
python scripts/update_conda_recipe.py
```

## Architecture Overview

### Core Data Model
The package uses a hierarchical data structure centered around `pandas.DataFrame` with three-level `MultiIndex` columns labeled ("M", "C", "S") for measurement, component, and species:
- **Plasma** (`core/plasma.py`): Central container holding ions, magnetic field, and spacecraft data
- **Ion** (`core/ions.py`): Individual ion species with moments and properties
- **Base** (`core/base.py`): Abstract base providing logging, units, and constants to all objects
- **Spacecraft** (`core/spacecraft.py`): Trajectory and velocity information

### Module Organization
- `core/`: Fundamental physics classes (plasma, ions, vectors, tensors, spacecraft)
- `fitfunctions/`: Data fitting tools with abstract `FitFunction` base class
- `plotting/`: Visualization tools including histograms, scatter plots, and specialized labels
- `solar_activity/`: Solar indices tracking (LISIRD interface, sunspot numbers)
- `instabilities/`: Plasma instability calculations
- `tools/`: Utility functions

### Data Access Patterns
- Plasma objects provide convenient attribute access: `plasma.a` returns alpha particle Ion
- All data stored in DataFrames with datetime indices (typically "Epoch")
- Heavy use of DataFrame views via `.xs()` to minimize memory usage

## Key Development Patterns

### Testing Strategy  
**Use TestEngineer agent** - maintains `/tests/` structure, ≥95% coverage, fixtures
See @.claude/agents/agent-test-engineer.md for testing protocols

### Documentation
**Use DocumentationMaintainer agent** - NumPy docstrings, Sphinx docs, examples

### Git Operations
**Use GitIntegration agent** - `plan/` and `feature/` branch management, commit tracking

### Physics and Data Processing Rules
- Preserve SI units internally, convert only for display
- Missing data indicated by NaN, not zero or -999
- Time series must maintain chronological order
- Quality flags carried through analysis pipeline
- Instability thresholds depend on plasma beta and anisotropy

## Special Considerations

### Physical Units
- The `units_constants` module provides conversion factors and physical constants
- Thermal speeds assume mw² = 2kT
- Careful handling of unit conversions throughout calculations

### Performance
- Uses numba for performance-critical calculations
- Leverages pandas/numpy vectorization where possible
- Memory optimization through DataFrame views rather than copies

## Common Aliases

The package provides convenient aliases in the main namespace:
- `swp.Plasma` → `solarwindpy.core.plasma.Plasma`
- `swp.pp` → `solarwindpy.plotting`
- `swp.sa` → `solarwindpy.solar_activity`
- `swp.sc` → `solarwindpy.spacecraft`
- `swp.at` → `solarwindpy.alfvenic_turbulence`

### Commit Standards
Follow Conventional Commits format:
- `feat(module):` for new features
- `fix(module):` for bug fixes
- `test(module):` for test additions/changes
- `docs:` for documentation updates
- Reference issues when applicable

## Current Status and Context

For current development priorities and agent coordination:
@claude_session_state.md
@.claude/agents/agents-index.md