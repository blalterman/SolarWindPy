# Code Attribution Guidelines for SolarWindPy

## Overview

This document provides comprehensive guidelines for properly attributing code sources in SolarWindPy, including AI-generated code, external sources, and scientific algorithms.

**Core Principles:**
- **Transparency**: Always acknowledge AI assistance and external sources
- **Respect**: Honor original authors and license terms
- **Quality**: Expert validation of all AI-generated physics code
- **Scientific Integrity**: Maintain academic standards for software

---

## Attribution Requirements

### 1. AI-Generated Code (REQUIRED)

All commits containing AI-generated or AI-modified code MUST include:

```
🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**When to use:**
- Code written with Claude Code assistance
- Substantial refactoring guided by AI
- AI-suggested implementations

**Example commit:**
```bash
git commit -m "$(cat <<'EOF'
feat(plasma): add ion composition analysis

Implement multi-species ion composition calculations with
mass-weighted averaging for mixed plasma populations.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### 2. External Code Sources (REQUIRED)

When incorporating code from external sources, add attribution comments in the source file:

**Attribution Format:**
```python
# Source: [Origin description or author]
# URL: [Link to source]
# License: [License name]
# Modifications: [Brief description of changes]
```

**Requires Attribution:**
- Code copied or adapted from Stack Overflow, GitHub, or public repositories
- Modified third-party code snippets
- Substantial code patterns from documentation examples (beyond basic API usage)
- Algorithm implementations closely following specific external implementations

**Does NOT Require Attribution:**
- Standard library usage (NumPy, SciPy, pandas, matplotlib API calls)
- Common programming patterns and idioms (error handling, validation, logging)
- Standard scientific computing patterns (vectorization, broadcasting, indexing)
- Generic test structures and fixtures
- Code generated from scratch based on requirements and specifications
- Refactoring and modifications of existing SolarWindPy code
- Standard algorithms from textbooks (binary search, sorting, etc.)

### 3. Scientific Algorithm Citations (REQUIRED)

Physics and mathematical implementations MUST cite source material in docstrings using the **References** section:

**Citation Format:**
```python
def calculate_parameter(inputs):
    """Calculate [physical parameter].

    [Description of what it calculates]

    Parameters
    ----------
    inputs : array-like
        [Description with units]

    Returns
    -------
    [type]
        [Description with units]

    References
    ----------
    .. [1] Author, A., & Author, B. (Year). "Title of Paper".
           Journal Name, Volume(Issue), pages.
           DOI: XX.XXXX/journal.year.article

    Notes
    -----
    Algorithm follows Author et al. (Year), Equation X.
    [Any physics assumptions or conventions]
    """
    # Implementation
```

**When Scientific Citation is Required:**
- Implementing specific equations from papers
- Following published algorithms or methods
- Using domain-specific formulas or conventions
- Adapting research code or techniques

**For Well-Established Physics:**
A general textbook reference is sufficient:
```python
"""
Standard plasma physics definition.
See, e.g., Chen (2016), "Introduction to Plasma Physics", 3rd ed.
"""
```

---

## License Compatibility

### SolarWindPy License: BSD 3-Clause

**Key Points:**
- Permissive open-source license
- Allows modification and redistribution
- Requires preservation of copyright notices
- No copyleft provisions

### Compatible Licenses (for CODE COPYING)

Can incorporate code from these licenses **with proper attribution**:

| License | Requirements | Notes |
|---------|-------------|-------|
| MIT | Preserve copyright notice | Very compatible |
| BSD 2-Clause | Preserve copyright notice | Very compatible |
| BSD 3-Clause | Preserve copyright notice | Same as SolarWindPy |
| Apache 2.0 | Preserve notices, state changes | Document modifications |
| CC0 / Public Domain | None legally required | Cite for transparency |

**Format for compatible licensed code:**
```python
# Original Copyright (c) [Year] [Author]
# Licensed under [License Name]
# Source: [URL]
# Modifications for SolarWindPy: [description]
```

### Incompatible Licenses (for CODE COPYING)

**DO NOT copy code from these licenses into SolarWindPy source files:**

| License | Why Incompatible | Action |
|---------|------------------|--------|
| GPL v2/v3 | Copyleft - requires SolarWindPy to become GPL | Reimplement from scratch |
| LGPL | Copyleft on modifications - incompatible for copied code | Reimplement from scratch |
| Proprietary | Closed source, all rights reserved | Cannot use |
| Unknown/Missing | Legal risk | Ask author or reimplement |

### Important Distinction: CODE COPYING vs. DEPENDENCIES

**Different rules apply:**

| Context | GPL | LGPL | MIT/BSD/Apache |
|---------|-----|------|----------------|
| **Copying code into SolarWindPy** | ❌ Incompatible (copyleft) | ❌ Incompatible (copyleft) | ✅ Compatible |
| **Using as dependency** | ⚠️ Complex (avoid) | ✅ Generally OK | ✅ Fully compatible |

**Key Point:**
- **Copying code** = Incorporating source into SolarWindPy files → License applies to SolarWindPy
- **Using dependency** = Importing external library via `import` → Different rules apply

**For Dependencies:**
- LGPL libraries are generally fine as dependencies (LGPL designed for library use)
- GPL dependencies are complex (legal debate about dynamic linking)
- SolarWindPy currently uses only BSD/permissive dependencies

**When in doubt:** For dependencies, consult maintainer. For code copying, stick to compatible licenses.

### Standard Scientific Python Stack (All Compatible)

These dependencies require no special attribution beyond standard `import` statements:
- NumPy: BSD 3-Clause
- SciPy: BSD 3-Clause
- pandas: BSD 3-Clause
- matplotlib: PSF-like (permissive)
- Astropy: BSD 3-Clause

---

## Code Generation Guidelines

### Writing Original Code (PREFERRED)

**Default Approach:**
1. **Understand requirements**: What problem are we solving?
2. **Design solution**: How does it fit SolarWindPy architecture?
3. **Implement from scratch**: Write code based on requirements, not external examples
4. **Validate**: Test against known results, check physics constraints

**Example workflow:**
```
User request: "Calculate plasma beta parameter"
↓
Research physics definition: β = 2μ₀nkT/B²
↓
Design: Input validation, unit handling, vectorization
↓
Implement: Write from equation and specifications
↓
Validate: Physics hook, unit tests, compare to literature values
```

**This code is ORIGINAL and needs no external attribution** (though physics equation should cite source).

### Adapting Existing Code

**Internal SolarWindPy Code** (freely reusable):
- Copy and adapt patterns from other SolarWindPy modules
- Maintain consistency with project conventions
- No attribution needed (same project)

**External Code** (requires attribution):
- Follow external source attribution format
- Document modifications clearly
- Verify license compatibility
- When in doubt, ask user or reimplement

### Prohibited Actions

❌ **Never do these:**

1. **Copy substantial code blocks without attribution**
2. **Mix code under incompatible licenses** (e.g., GPL code in BSD project)
3. **Use code with unknown provenance**
4. **Claim AI-generated code is original human work** (omit "Generated with Claude Code")
5. **Ignore license terms** (remove copyright notices from attributed code)

---

## SolarWindPy Unit Handling Pattern

### Overview

SolarWindPy uses a **two-layer unit system**:
- **Storage units**: Data stored in DataFrames (km/s, cm^-3, nT, pPa, 10^5 K, etc.)
- **Calculation units**: Physics calculations in SI (m/s, m^-3, T, Pa, K, etc.)

All conversions handled via the `self.units` class attribute.

### Canonical Pattern

**Based on actual SolarWindPy code** (see `solarwindpy/core/ions.py`):

```python
@property
def physical_quantity(self) -> pd.DataFrame:
    """Calculate [quantity name] using [formula].

    The [quantity] is calculated as:

    .. math::
        [LaTeX formula]

    Returns
    -------
    pd.DataFrame or pd.Series
        [Quantity description] in [storage units].

    Notes
    -----
    [Any physics assumptions, e.g., "Assumes mw² = 2kT"]

    References
    ----------
    .. [1] Author, A., & Author, B. (Year). "Title".
           Journal Name, Volume(Issue), pages.
           DOI: XX.XXXX/journal.year.article
    """
    # Step 1: Get input quantities from storage (in storage units)
    input1 = self.property1  # e.g., self.rho (mass density in storage units)
    input2 = self.property2  # e.g., self.w.data (thermal speed in storage units)

    # Step 2: Convert to SI units for calculation
    input1_si = input1 * self.units.input1  # storage → SI
    input2_si = input2 * self.units.input2  # storage → SI

    # Step 3: Get physical constants (already in SI)
    constant = self.constants.constant_name  # e.g., k_B, m_p

    # Step 4: Perform calculation in SI units
    result_si = [physics formula using SI quantities]

    # Step 5: Convert back to storage units
    result = result_si / self.units.physical_quantity  # SI → storage

    # Step 6: Set descriptive name
    result.name = "abbreviation"

    return result
```

### Real Example: Thermal Pressure

**From `solarwindpy/core/ions.py` (lines 227-239):**

```python
@property
def pth(self) -> pd.DataFrame:
    """Calculate thermal pressure p_th = 0.5 * ρ * w^2.

    Returns
    -------
    pd.DataFrame
        Thermal pressure in pPa (pico-Pascals).
    """
    # Get from storage: mass density and thermal speed
    rho = self.rho  # Storage units (cm^-3 equivalent → kg/m^3)
    w = self.w.data  # Storage units (km/s)

    # Convert to SI for calculation
    rho_si = rho * self.units.rho  # → kg/m^3
    w_si = w.multiply(self.units.w)  # → m/s

    # Calculate in SI units
    pth_si = 0.5 * w_si.pow(2).multiply(rho_si, axis=0)  # → Pa

    # Convert back to storage units
    pth = pth_si / self.units.pth  # → pPa
    pth.name = "pth"

    return pth
```

### Unit Conventions

**Storage Units (DataFrame columns):**
- Magnetic field: nT (nanotesla)
- Velocity: km/s
- Thermal speed: km/s
- Number density: cm^-3
- Temperature: 10^5 K
- Pressure: pPa (pico-Pascals)

**SI Calculation Units:**
- Magnetic field: T (tesla)
- Velocity: m/s
- Density: m^-3
- Temperature: K
- Pressure: Pa

**Conversion Infrastructure:**
- `self.units.[quantity]`: Conversion factor from storage → SI
- `result / self.units.[quantity]`: Conversion from SI → storage
- `self.constants.[constant]`: Physical constants in SI

---

## Examples

### Example 1: Scientific Citation (REAL - from SolarWindPy)

**File:** `solarwindpy/alfvenic/alfvenic_turbulence.py`

This module demonstrates proper scientific citation format:

```python
"""
Module for analyzing alfvénic turbulence in solar wind.

This module provides functionality for identifying and analyzing
alfvénic fluctuations following the methodology of Bruno & Carbone (2013).

References
----------
.. [1] Bruno, R., & Carbone, V. (2013). "The Solar Wind as a Turbulence
       Laboratory". Living Reviews in Solar Physics, 10(1), 2.
       DOI: 10.12942/lrsp-2013-2

.. [2] Woodham, L. D., et al. (2018). "Enhanced proton parallel temperature
       inside patches of switchbacks in the inner heliosphere".
       Astronomy & Astrophysics, 650, L1.
       DOI: 10.1051/0004-6361/202039415
```

**Key features:**
- Clear References section with numbered citations
- Full citation information (authors, year, title, journal, volume, pages)
- DOI links for verification
- Multiple sources when applicable

**To see full context:** Read the complete file in the repository.

---

### Example 2: External Code Attribution (TEMPLATE)

**⚠️ TEMPLATE - Not actual SolarWindPy code ⚠️**

Format for attributing external code:

```python
def template_moving_average(data, window):
    """Calculate moving average using convolution.

    Source: NumPy documentation example
    URL: https://numpy.org/doc/stable/reference/generated/numpy.convolve.html
    License: BSD 3-Clause (NumPy project)
    Modifications: Added input validation for SolarWindPy DataFrames

    Parameters
    ----------
    data : array-like
        Input data
    window : int
        Window size for averaging

    Returns
    -------
    array-like
        Smoothed data
    """
    # Validation (added for SolarWindPy)
    if window < 1:
        raise ValueError("Window must be positive")

    # Original NumPy pattern
    kernel = np.ones(window) / window
    return np.convolve(data, kernel, mode='valid')
```

**Use this format when incorporating external code.**

---

### Example 3: Stack Overflow Attribution (TEMPLATE)

**⚠️ TEMPLATE - Not actual SolarWindPy code ⚠️**

```python
def template_outlier_detection(data, threshold=3.0):
    """Detect outliers using modified Z-score.

    Source: Stack Overflow answer by [username]
    URL: https://stackoverflow.com/a/[answer_id]
    License: CC BY-SA 4.0 (Stack Overflow content)
    Modifications: Adapted for SolarWindPy DataFrame structure

    Parameters
    ----------
    data : pd.Series
        Input data
    threshold : float
        Z-score threshold for outlier detection

    Returns
    -------
    pd.Series
        Boolean mask where True indicates outliers
    """
    median = data.median()
    mad = (data - median).abs().median()
    modified_z_score = 0.6745 * (data - median) / mad
    return modified_z_score.abs() > threshold
```

---

### Example 4: Algorithm with Citation (TEMPLATE)

**⚠️ TEMPLATE - Not actual SolarWindPy code ⚠️**

```python
def template_sound_speed(pressure, density):
    """Calculate adiabatic sound speed.

    The sound speed is calculated as:

    .. math::
        c_s = \\sqrt{\\gamma p_{th} / \\rho}

    where γ is the polytropic index (5/3 for monoatomic ideal gas).

    Parameters
    ----------
    pressure : pd.DataFrame
        Thermal pressure in pPa
    density : pd.Series
        Mass density in storage units

    Returns
    -------
    pd.Series
        Sound speed in km/s

    References
    ----------
    .. [1] Siscoe, G. L. (1983). Solar System Magnetohydrodynamics.
           pp. 11-100. DOI: 10.1007/978-94-009-7194-3_2

    Notes
    -----
    Follows SolarWindPy unit convention: calculations in SI,
    storage in km/s. See Units class for specifications.
    """
    # Convert to SI units
    p_si = pressure * self.units.pth  # pPa → Pa
    rho_si = density * self.units.rho  # storage → kg/m^3

    # Physical constant (SI)
    gamma = 5.0 / 3.0  # Monoatomic ideal gas

    # Calculate in SI
    cs_si = np.sqrt(gamma * p_si / rho_si)  # m/s

    # Convert to storage units
    return cs_si / self.units.cs  # m/s → km/s
```

---

### Example 5: Original Implementation (No Attribution Needed)

**✅ GOOD - Shows standard pattern without external attribution:**

```python
def flow_angle(v_radial, v_tangential):
    """Calculate flow angle from velocity components.

    The flow angle θ is defined as the angle between the velocity
    vector and the radial direction: θ = arctan(v_t / v_r).

    Parameters
    ----------
    v_radial : array-like
        Radial velocity component in km/s
    v_tangential : array-like
        Tangential velocity component in km/s

    Returns
    -------
    array-like
        Flow angle in radians, range [-π/2, π/2]

    Notes
    -----
    Standard spherical coordinate definition. Uses numpy.arctan2
    for proper quadrant handling.
    """
    return np.arctan2(v_tangential, v_radial)
```

**Why no attribution needed:**
- Original implementation from requirements
- Standard mathematical function
- Generic spherical coordinate geometry
- No external code copied

---

## Quality Assurance for Attributed Code

All code (attributed or original) must meet:

### 1. Test Coverage (≥95%)

```bash
pytest --cov=solarwindpy --cov-report=term
```

Enforced by pre-commit hook.

### 2. Physics Validation

```bash
.claude/hooks/test-runner.sh --physics
```

Automated hook checks:
- Thermal speed conventions (mw² = 2kT)
- Physical constraints (positive temperatures, densities)
- Unit consistency

### 3. Code Quality

```bash
black solarwindpy/ tests/
flake8 solarwindpy/ tests/
```

### 4. Expert Review

**Additional scrutiny for AI-assisted code:**

✅ **Physics Correctness**
- Calculations follow SolarWindPy conventions
- Physical constraints validated
- Results match literature values for test cases

✅ **Architecture Fit**
- Follows MultiIndex DataFrame structure
- Uses `.xs()` for cross-sections appropriately
- Consistent with existing module organization

✅ **Documentation Quality**
- NumPy docstring format with all sections
- Parameter descriptions include units
- References to scientific sources where applicable

✅ **Test Coverage**
- Edge cases (empty arrays, single values, large arrays)
- Physics edge cases (zero temperature, infinite density)
- Integration with existing functionality

---

## Downstream Protection

### Why Attribution Matters

**Legal Compliance:**
- Respects original authors' license terms
- Prevents inadvertent license violations
- Protects SolarWindPy and downstream users from legal risk

**Scientific Integrity:**
- Maintains academic standards for scientific software
- Enables reproducibility through clear provenance
- Gives credit where credit is due

**User Trust:**
- Downstream users know code origins and licensing
- Clear provenance chain for implementations
- Transparent about AI assistance

**Collaboration:**
- Proper credit facilitates community engagement
- Encourages contributions and sharing
- Builds trust in open-source ecosystem

### For Downstream Users

**Using SolarWindPy:**
- BSD 3-Clause allows broad reuse (commercial, academic, modified)
- Must preserve SolarWindPy's copyright notice
- "Generated with Claude Code" provides transparency
- Scientific citations enable verification against published methods

**Dependency Chain:**
```
Your Project (any license compatible with BSD)
└── SolarWindPy (BSD 3-Clause)
    ├── NumPy (BSD 3-Clause)
    ├── SciPy (BSD 3-Clause)
    ├── pandas (BSD 3-Clause)
    ├── matplotlib (PSF-like)
    └── Astropy (BSD 3-Clause)
```

All compatible, permissive licenses throughout.

---

## When Uncertain

### Decision Tree

```
Is this code from an external source?
├─ YES → Add attribution comment
│   ├─ Check license compatibility
│   ├─ Document source, license, modifications
│   └─ Verify with user if unsure
│
├─ NO, it's original → No attribution needed
│   ├─ But cite algorithms/papers if applicable
│   └─ Use "Generated with Claude Code" in commit
│
└─ UNSURE → Ask user
    ├─ Describe the code and its origin
    ├─ Let user decide on attribution
    └─ When in doubt, prefer reimplementation
```

### Questions to Ask Yourself

**"Should I attribute this code?"**

1. Did I copy this from an external source? → **YES = Attribute**
2. Is this a substantial code block (>10 lines) that closely matches external code? → **YES = Attribute**
3. Is this a standard pattern/idiom used everywhere? → **NO = Don't attribute**
4. Is this an algorithm from a specific paper? → **YES = Cite paper**
5. Am I unsure of the origin? → **ASK USER**

**"How should I attribute?"**
- External code → Comment with source, license, modifications
- Algorithm → Docstring with paper citation, DOI
- AI-generated → Commit message with "Generated with Claude Code"

**"Can I use code with license X?"**
- Check license compatibility tables above
- When uncertain → Ask user before incorporating
- If incompatible → Reimplement from scratch

---

## References

### SolarWindPy Documentation
- [CLAUDE.md](../../CLAUDE.md): Essential rules and quick reference
- [DEVELOPMENT.md](./DEVELOPMENT.md): Development standards and conventions
- [AGENTS.md](./AGENTS.md): Specialized agent capabilities

### External Resources
- [Open Source Initiative](https://opensource.org/licenses): License information
- [Choose a License](https://choosealicense.com): License selection guide
- [SPDX License List](https://spdx.org/licenses/): Standardized license identifiers
- [GitHub Licensing Guide](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)

### Scientific Software Practices
- [Software Carpentry](https://software-carpentry.org): Best practices
- [Better Scientific Software (BSSw)](https://bssw.io): Resources and community
- [Journal of Open Source Software](https://joss.theoj.org): Publication standards

---

**Version:** 1.0
**Last Updated:** 2025-10-30
**Maintained by:** SolarWindPy project
