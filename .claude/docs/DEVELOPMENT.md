# Development Standards

Development guidelines and standards for SolarWindPy scientific software.

## Physics Rules (Automated via Hooks)
- **Units**: SI internally, convert only for display
- **Thermal speed**: mw² = 2kT convention
- **Missing data**: NaN (never 0 or -999)
- **Time series**: Maintain chronological order
- **Alfvén speed**: V_A = B/√(μ₀ρ) with ion composition

## Data Patterns (DataFrameArchitect Agent)
- Use `.xs()` for DataFrame views, not copies
- DateTime indices named "Epoch"
- MultiIndex access via level names: `df.xs('v', level='M')`

## Testing (Automated + TestEngineer Agent)
- **Coverage**: ≥95% required (enforced by pre-commit hook)
- **Structure**: `/tests/` mirrors source structure
- **Automation**: Smart test execution via `.claude/hooks/test-runner.sh`
- **Quality**: Physics constraints, numerical stability, scientific validation
- **Templates**: Use `.claude/scripts/generate-test.py` for test scaffolding

## Git Workflow (Automated via Hooks)
- **Planning**: GitHub Issues with comprehensive propositions framework
- **Branches**: `feature/<name>` for implementation directly from GitHub Issues
- **PR Workflow**: PRs created directly from feature/* branches to master
  - GitHub Issues provide planning structure
  - Workflow: GitHub Issues → feature → PR → master
- **Protection**: No direct master commits, feature branch validation
- **Multi-computer sync**: Instant plan access across all development machines
- **Commits**: Conventional format with physics validation
- **Quality**: Tests pass before commits (automated)

## Environment Setup

```bash
# Create and activate conda environment:
conda env create -f solarwindpy.yml
conda activate solarwindpy
pip install -e .

# Alternative: generate environment from requirements-dev.txt:
python scripts/requirements_to_conda_env.py --name solarwindpy-dev
conda env create -f solarwindpy-dev.yml
conda activate solarwindpy-dev
pip install -e .
```

## Code Quality Standards
- **Formatting**: Black for code formatting
- **Linting**: Flake8 for style checking
- **Documentation**: NumPy-style docstrings
- **Commits**: Conventional Commits format with 'Generated with Claude Code'
- **Testing**: All tests must pass before committing

## Module Organization
- `core/`: Physics classes (plasma, ions, vectors, tensors, spacecraft)
- `fitfunctions/`: Data fitting with abstract `FitFunction` base class
- `plotting/`: Visualization tools and specialized labels
- `instabilities/`: Plasma instability calculations
- `tools/`: Utility functions including `units_constants`

## Common Aliases
- `swp.Plasma` → `solarwindpy.core.plasma.Plasma`
- `swp.pp` → `solarwindpy.plotting`
- `swp.sa` → `solarwindpy.solar_activity`
- `swp.sc` → `solarwindpy.spacecraft`