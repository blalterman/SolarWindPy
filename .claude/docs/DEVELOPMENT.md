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
- **Formatting**: Black for code formatting (88 characters)
- **Linting**: Flake8 for style checking (88 characters)
- **Documentation**: NumPy-style docstrings with doc8 validation (100 characters)
- **Commits**: Conventional Commits format with 'Generated with Claude Code'
- **Testing**: All tests must pass before committing

## Code Attribution

All code incorporated into SolarWindPy must follow proper attribution practices.

**See comprehensive guidelines:** [ATTRIBUTION.md](./ATTRIBUTION.md)

### Quick Reference

**AI-Generated Code:**
```bash
# Include in commit message:
🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**External Code:**
```python
# Add in source file:
# Source: [Description or author]
# URL: [Link]
# License: [License type]
# Modifications: [What changed]
```

**Scientific Algorithms:**
```python
"""
References
----------
.. [1] Author, A., & Author, B. (Year). "Title".
       Journal, Volume(Issue), pages.
       DOI: XX.XXXX/journal.year.article
"""
```

**License Compatibility:**
- ✅ Compatible (can copy code): MIT, BSD, Apache 2.0, Public Domain
- ❌ Incompatible (cannot copy code): GPL, LGPL, proprietary, unknown
- ⚠️ Dependencies: LGPL libraries OK as dependencies, GPL complex (avoid)

**When Uncertain:**
- External code → Ask maintainer or reimplement from scratch
- Algorithms → Cite paper in docstring References section
- Standard patterns → No attribution needed (NumPy/pandas idioms, common practices)

### Documentation Standards (doc8)

**Line Length Guidelines**:
- **Code lines**: 88 characters (black/flake8)
- **Documentation lines**: 100 characters (doc8)

**Scientific Documentation Best Practices**:
```python
def plasma_beta(n, T, B):
    r"""Calculate plasma beta for magnetized plasma.
    
    Uses the standard definition β = 8π n k_B T / B² where thermal
    pressure dominates over magnetic pressure when β > 1.
    
    Parameters
    ----------
    n : float or array-like
        Ion number density in cm⁻³
    T : float or array-like  
        Ion temperature in K
    B : float or array-like
        Magnetic field strength in nT
        
    Notes
    -----
    Long mathematical expressions should be broken naturally:
    
    .. math::
        β = \\frac{8π n k_B T}{B²}
    """
```

**Handling Long Lines**:
- URLs and DOIs: Use `# noqa: D001` if necessary
- Mathematical formulas: Break at logical operators
- Parameter lists: Use line continuations
- Example arrays: Format for readability

**Common doc8 Commands**:
```bash
# Check all documentation
doc8 solarwindpy/ --extension .py

# Check specific files
doc8 README.rst docs/

# Skip line length check for specific files
doc8 --ignore D001 file_with_long_formulas.py
```

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