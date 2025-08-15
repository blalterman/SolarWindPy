# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Workflow

### Primary Workflow - Enhanced Hook System
Use `Task` tool with specialized agents for domain work:
- **UnifiedPlanCoordinator**: All planning, implementation, and status coordination
- **PhysicsValidator**: Physics correctness and unit validation
- **DataFrameArchitect**: MultiIndex data structure management
- **NumericalStabilityGuard**: Numerical validation and edge cases
- **PlottingEngineer**: Visualization and matplotlib operations
- **FitFunctionSpecialist**: Curve fitting and statistical analysis
- **TestEngineer**: Test coverage and quality assurance

### Automated Validation
Hook system provides automatic validation:
- **Session startup**: Branch validation and context loading
- **Git operations**: Workflow enforcement and branch protection
- **Physics edits**: Unit consistency and constraint checking
- **Token limits**: Automatic compaction and state preservation

## Environment Setup

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

## Core Architecture

### Data Model
The package uses hierarchical `pandas.DataFrame` with three-level `MultiIndex` columns ("M", "C", "S"):
- **M**: Measurement type (n, v, w, b, etc.)
- **C**: Component (x, y, z for vectors, empty for scalars)  
- **S**: Species (p1, p2, a, etc., empty for magnetic field)

### Key Classes
- **Plasma** (`core/plasma.py`): Central container for ions, magnetic field, spacecraft data
- **Ion** (`core/ions.py`): Individual ion species with moments and properties
- **Base** (`core/base.py`): Abstract base providing logging, units, constants

### Module Organization
- `core/`: Physics classes (plasma, ions, vectors, tensors, spacecraft)
- `fitfunctions/`: Data fitting with abstract `FitFunction` base class
- `plotting/`: Visualization tools and specialized labels
- `instabilities/`: Plasma instability calculations
- `tools/`: Utility functions including `units_constants`

## Development Standards

### Physics Rules (Automated via Hooks)
- **Units**: SI internally, convert only for display
- **Thermal speed**: mw² = 2kT convention
- **Missing data**: NaN (never 0 or -999)
- **Time series**: Maintain chronological order
- **Alfvén speed**: V_A = B/√(μ₀ρ) with ion composition

### Data Patterns (DataFrameArchitect Agent)
- Use `.xs()` for DataFrame views, not copies
- DateTime indices named "Epoch"
- MultiIndex access via level names: `df.xs('v', level='M')`

### Testing (TestEngineer Agent)
- **Coverage**: ≥95% required
- **Structure**: `/tests/` mirrors source structure  
- **Quality**: Edge cases, physics constraints, numerical stability

### Git Workflow (Automated via Hooks)
- **Branches**: `plan/<name>` for planning, `feature/<name>` for implementation
- **Protection**: No direct master commits (enforced by hooks)
- **Commits**: Conventional format with physics validation
- **Quality**: Tests pass before commits (automated)

## Common Aliases

- `swp.Plasma` → `solarwindpy.core.plasma.Plasma`
- `swp.pp` → `solarwindpy.plotting`
- `swp.sa` → `solarwindpy.solar_activity`
- `swp.sc` → `solarwindpy.spacecraft`

## Quick Commands

```bash
# Quality checks (automated via hooks):
pytest -q              # Run tests
black solarwindpy/     # Format code  
flake8                 # Check linting

# Recipe management:
python scripts/update_conda_recipe.py
```

## Agent Usage Examples

```python
# Planning and implementation
"Use UnifiedPlanCoordinator to create plan for dark mode implementation"

# Domain-specific work  
"Use PhysicsValidator to verify thermal speed calculations"
"Use DataFrameArchitect to optimize MultiIndex operations"
"Use PlottingEngineer to create publication-quality figures"
```

The hook system handles routine validation automatically, while agents provide domain expertise for complex tasks. This ensures both efficiency and quality throughout the development process.