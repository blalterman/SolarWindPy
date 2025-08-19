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

### Plan Development Requirements
**All plans MUST include comprehensive propositions analysis using `plans/0-overview-template.md`:**
- **Risk Proposition**: Technical, scientific, and operational risk assessment with mitigation strategies
- **Value Proposition**: Quantified scientific, developer, and user benefits with ROI timeline
- **Cost Proposition**: Development time, testing effort, maintenance costs, and opportunity cost analysis
- **Token Proposition**: AI-assisted development efficiency with planning/implementation token estimates and future savings
- **Usage Proposition**: Target users, adoption requirements, and coverage scope for research impact assessment

### Automated Validation
Hook system provides automatic validation:
- **Session startup**: Branch validation and context loading
- **Git operations**: Workflow enforcement and branch protection
- **Physics edits**: Unit consistency and constraint checking
- **Token limits**: Automatic compaction and state preservation
- **Plan completion**: Automatic closeout documentation generation

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

### Testing (Automated + TestEngineer Agent)
- **Coverage**: ≥95% required (enforced by pre-commit hook)
- **Structure**: `/tests/` mirrors source structure
- **Automation**: Smart test execution via `.claude/hooks/test-runner.sh`
- **Quality**: Physics constraints, numerical stability, scientific validation
- **Templates**: Use `.claude/scripts/generate-test.py` for test scaffolding

### Git Workflow (Automated via Hooks)
- **Branches**: `plan/<name>` for planning, `feature/<name>` for implementation
- **PR Workflow**: PRs MUST be created from plan/* branches to master
  - Feature branches merge to plan branches
  - Plan branches create PRs to master
  - Workflow: feature → plan → PR → master
- **Protection**: No direct master commits (enforced by hooks)
- **Validation**: PR source branch validated (plan/* only)
- **Commits**: Conventional format with physics validation
- **Quality**: Tests pass before commits (automated)
- **Plan Completion**: Automatic closeout documentation via `plans/closeout-template.md`
  - Generated before archival to `plans/completed/`
  - Captures implementation decisions and lessons learned
  - Populates velocity metrics for future estimation improvements

### Git Tag Conventions
Two distinct tag namespaces maintain separation between operational and release concerns:

#### Release Tags (Semantic Versioning)
- **Pattern**: `v{major}.{minor}.{patch}[-{prerelease}]`
- **Examples**: `v1.0.0`, `v2.1.3-alpha`, `v1.5.0-beta.2`
- **Purpose**: Official package releases, PyPI distribution
- **Automation**: GitHub workflow creates these for releases
- **Used by**: setuptools_scm for version detection

#### Compaction Tags (Operational)
- **Pattern**: `claude/compaction/{date}-{compression}pct`
- **Examples**: `claude/compaction/2025-08-19-20pct`
- **Purpose**: Session state preservation at token boundaries
- **Automation**: Created by `.claude/hooks/create-compaction.py`
- **Used by**: Claude session management and rollback

**Important**: setuptools_scm is configured to only recognize `v*` tags for versioning, preventing compaction tags from interfering with package version detection.

## Common Aliases

- `swp.Plasma` → `solarwindpy.core.plasma.Plasma`
- `swp.pp` → `solarwindpy.plotting`
- `swp.sa` → `solarwindpy.solar_activity`
- `swp.sc` → `solarwindpy.spacecraft`

## Quick Commands

```bash
# Testing (enhanced automation):
.claude/hooks/test-runner.sh --changed    # Test changed files
.claude/hooks/test-runner.sh --physics    # Physics validation tests
.claude/hooks/coverage-monitor.py         # Detailed coverage analysis
.claude/scripts/generate-test.py          # Generate test scaffolding

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
"Use TestEngineer to design physics-specific test strategies"
```

## Testing Workflow Integration

The testing system combines automation with domain expertise:
- **Hooks**: Handle routine execution, coverage, and validation automatically
- **TestEngineer Agent**: Provides scientific testing strategies and complex test design
- **Templates**: Enable consistent test patterns across physics modules
- **Smart Tools**: Context-aware test execution and coverage monitoring

This ensures both efficiency and scientific rigor throughout the development process.