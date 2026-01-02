# Documentation Update Prompt - Feature Integration Corrections

**Created:** 2025-10-23
**Status:** Ready for execution
**Target:** `.claude/docs/feature_integration/` documentation

---

## Purpose

This document contains the comprehensive prompt for updating the feature_integration documentation to correct 5 identified issues. Use this prompt to execute the documentation updates after session resumption.

---

## Issues to Address

1. **Memory Hierarchy** - Project memory ONLY (remove User/Local/Enterprise references)
2. **MCS Specification** - Correct format with proper capitalization and temperature components
3. **Composition Labels** - Ion vs ChargeStateRatio with correct signatures
4. **Component Capitalization** - RTN uppercase, temperature components (par/per/scalar)
5. **Isotope References** - Remove (not supported in SolarWindPy)

---

## Complete Prompt

```
Update the "Detailed Documentation Update Plan" to address 5 newly identified issues before implementation:

ISSUE 1: Memory Hierarchy - Project Memory ONLY
**Problem:** Plan references multiple memory tiers (Enterprise, User, Local), but SolarWindPy uses ONLY Project memory.

**Incorrect Current Documentation:**
- References to 4-tier hierarchy (Enterprise → Project → User → Local)
- References to 3-tier hierarchy (Project → User → Local)
- References to 2-tier hierarchy (Project → User)
- Any mention of `./CLAUDE.local.md`
- Any mention of `~/.claude/CLAUDE.md` (User memory)
- Any mention of Enterprise memory locations
- "Local" or "User" tiers anywhere

**Correct Memory Architecture for SolarWindPy:**
SolarWindPy uses **ONLY** Project memory:
- **Project Memory** (`./CLAUDE.md` or `./.claude/CLAUDE.md`)
  - Team-shared, committed to git
  - Contains ALL SolarWindPy conventions, rules, and configurations
  - Single source of truth for the project

**Why Project Memory Only:**
- **Consistency:** All team members work with identical configuration
- **Version Control:** Memory evolves with codebase, tracked in git
- **No User Fragmentation:** No personal overrides that create inconsistent behavior
- **Simplified Architecture:** One location for all project knowledge

**What Project Memory Contains:**
- Physics constants and formulas (thermal speed, units, etc.)
- MCS index structure and conventions
- Testing requirements (≥95% coverage)
- DataFrame patterns (MultiIndex best practices)
- Git workflows (branch naming, commit conventions)
- Hook system documentation
- Agent and skill usage patterns

**Required Actions:**
1. **Remove ALL Non-Project Memory References:**
   ```bash
   grep -rn "User.*memory\|Local.*memory\|Enterprise.*memory\|~/.claude/CLAUDE.md\|CLAUDE.local.md\|four-tier\|three-tier\|two-tier" .claude/docs/feature_integration/
   ```
   Delete every reference to:
   - User memory tier (`~/.claude/CLAUDE.md`)
   - Local memory tier (`./CLAUDE.local.md`)
   - Enterprise memory tier (various paths)
   - Multi-tier hierarchy descriptions
   - "(deprecated)" notes about other memory tiers

2. **Update to Single-Tier (Project Only):**
   - Change: "Enterprise → Project → User → Local" or any variant
   - To: "Project memory only"
   - Change: "four-tier", "three-tier", "two-tier", "cascading"
   - To: "single project-level memory"
   - Remove: All cascading/priority language (no hierarchy needed)

3. **Simplify Memory Documentation:**
   In 01_memory_hierarchy.md, replace existing hierarchy with:
   ```markdown
   ## Project Memory (Single Tier)

   SolarWindPy uses **project-level memory only** for maximum consistency and simplicity.

   **Location:** `./CLAUDE.md` or `./.claude/CLAUDE.md`

   **Purpose:**
   - Team-shared via git version control
   - Single source of truth for all SolarWindPy conventions
   - No personal overrides or local configurations

   **Contents:**
   - Physics constants (thermal speed formula, unit conventions)
   - MCS index structure (M/C/S format, capitalization rules)
   - Testing requirements (≥95% coverage, physics validation)
   - DataFrame patterns (MultiIndex best practices)
   - Git workflows (branch protection, commit format)
   - Hook system configuration
   - Agent and skill usage guidelines

   **Modular Structure:**
   Project memory uses imports for organization:
   ```
   CLAUDE.md (orchestrator)
   ├── @.claude/memory/critical-rules.md
   ├── @.claude/memory/physics-constants.md
   ├── @.claude/memory/dataframe-patterns.md
   ├── @.claude/memory/testing-templates.md
   └── @.claude/memory/git-workflows.md
   ```

   **No User or Local Memory:**
   - SolarWindPy does NOT use `~/.claude/CLAUDE.md` (User memory)
   - SolarWindPy does NOT use `./CLAUDE.local.md` (Local memory)
   - All configuration is project-level and team-shared
   ```

4. **Update INDEX.md:**
   - Feature 01 description line should say "Project memory only" not "cascading tiers"
   - Remove any multi-tier language

---

ISSUE 2: MCS Specification Correction
**Problem:** Throughout documentation, MCS examples are WRONG. Mixing measurement types with species, incorrect capitalization, temperature should be uppercase "T", and temperature has special components (par/per/scalar).

**Incorrect Examples Found:**
- Feature 08 draft: `TeXlabel("Vp", "x", "p")` - "Vp" is NOT a measurement
- Component lowercase: "r", "t", "n" should be "R", "T", "N" (RTN coordinates)
- Using lowercase "t" for temperature (should be uppercase "T")
- Missing temperature-specific components (par, per, scalar)
- M element using capital letters except "T" (should be lowercase except "T")

**Correct MCS Format:**
- **M (Measurement):**
  - Lowercase: "v" (velocity), "n" (number density), "p" (pressure), etc.
  - **Exception:** "T" (temperature) - UPPERCASE

- **C (Component):**
  - **Spatial (velocity, etc.):**
    - Cartesian: "x", "y", "z" - lowercase
    - RTN coordinates: "R", "T", "N" - UPPERCASE (radial, tangential, normal)
  - **Temperature-specific:** "par", "per", "scalar" - lowercase
    - "par" = parallel temperature (to magnetic field)
    - "per" = perpendicular temperature (to magnetic field)
    - "scalar" = scalar temperature (isotropic)

- **S (Species):** "p" (proton), "a" (alpha), "e" (electron), "he" (helium)

**Examples of CORRECT Usage:**
```python
# VELOCITY examples
# Proton x-velocity (Cartesian)
TeXlabel("v", "x", "p")  # NOT TeXlabel("Vp", "x", "p")

# Alpha particle radial velocity (RTN)
TeXlabel("v", "R", "a")  # Capital R for radial

# Proton tangential velocity (RTN)
TeXlabel("v", "T", "p")  # Capital T for tangential (NOT temperature)

# Proton normal velocity (RTN)
TeXlabel("v", "N", "p")  # Capital N for normal

# TEMPERATURE examples
# Proton parallel temperature
TeXlabel("T", "par", "p")  # Parallel to magnetic field

# Electron perpendicular temperature
TeXlabel("T", "per", "e")  # Perpendicular to magnetic field

# Alpha scalar temperature
TeXlabel("T", "scalar", "a")  # Isotropic/scalar

# Proton temperature (no component - total/scalar implied)
TeXlabel("T", None, "p")

# OTHER measurements
# Proton number density (no component)
TeXlabel("n", None, "p")  # Lowercase n for density
```

**Critical Distinction - "T" in Different Contexts:**
1. **"T" as Measurement (uppercase):** Temperature measurement
   - Example: `TeXlabel("T", "par", "p")` - Parallel temperature
   - Components: "par", "per", "scalar", or None

2. **"T" as Component (uppercase):** Tangential direction in RTN coordinates
   - Example: `TeXlabel("v", "T", "p")` - Tangential velocity
   - Measurement: "v" (velocity), not "T" (temperature)

3. **Context distinguishes them:** Position in MCS tuple
   - First element (M): Measurement type
   - Second element (C): Component
   - Third element (S): Species

**Required Actions:**
1. **Grep Strategy:** Find all MCS examples and component references
   - Search patterns: `TeXlabel\(`, `MCS`, `(".*", ".*", ".*")`, `"r".*"t".*"n"`
   - Search for: lowercase "t" in temperature context
   - Search for: lowercase "r", "t", "n" in component context
   - Search for: temperature examples without par/per/scalar components
   - Search files: All feature_integration/ files

2. **Systematic Correction:**
   - Update EVERY MCS example to use correct format
   - Change temperature measurement from lowercase "t" to uppercase "T"
   - Add temperature component examples using "par", "per", "scalar"
   - Change all RTN component references from lowercase to uppercase
   - Distinguish Cartesian (lowercase x,y,z) from RTN (uppercase R,T,N)
   - Distinguish temperature "T" (measurement) from tangential "T" (component)

3. **Validation:** Verify corrected examples match `solarwindpy/plotting/labels/base.py` implementation

---

ISSUE 3: Composition Label Signatures - Ion vs ChargeStateRatio
**Problem:** Documentation shows incorrect Composition subclass usage. ChargeState has been renamed to ChargeStateRatio with different signature.

**SolarWindPy Has Two DISTINCT Composition Classes:**

1. **Ion** - Single ion species with charge state
2. **ChargeStateRatio** - Ratio between two charge states (NOT just ChargeState)

**Current (WRONG):**
```python
ion_label = Ion("O")  # Missing charge state!
charge_label = ChargeState("O", 6)  # Class doesn't exist - it's ChargeStateRatio
```

**Required Research:**
Read the implementation to determine exact signatures:
```bash
Read solarwindpy/plotting/labels/composition.py
```

**Expected Correct Usage (verify against code):**
```python
# Ion label (single species + charge)
ion_label = Ion("O", 6)  # O^6+ (oxygen with +6 charge)

# ChargeStateRatio label (ratio of two charge states)
ratio_label = ChargeStateRatio("O", 6, 7)  # O^6+/O^7+ ratio
# OR potentially different signature - MUST VERIFY
```

**Required Actions:**
1. **Read Implementation:**
   ```bash
   Read solarwindpy/plotting/labels/composition.py
   ```
   Determine exact signatures for:
   - `Ion.__init__()` - parameters and usage
   - `ChargeStateRatio.__init__()` - parameters and usage
   - Verify the distinction between the two classes

2. **Update Feature 08 Examples:**
   - Correct all Ion examples with proper signature
   - Correct all ChargeStateRatio examples (NOT ChargeState)
   - Show BOTH classes with clear distinction
   - Use realistic solar wind charge states:
     - O^6+, O^7+ (common oxygen charge states)
     - Fe^10+, Fe^11+ (iron charge states)
     - C^5+, C^6+ (carbon charge states)

3. **Add Distinction Documentation:**
   ```markdown
   ### Composition Labels

   **Ion:** Single ion species with charge state
   - Usage: `Ion("O", 6)` → O^6+
   - Purpose: Label for individual ion measurements

   **ChargeStateRatio:** Ratio between two charge states
   - Usage: `ChargeStateRatio("O", 6, 7)` → O^6+/O^7+
   - Purpose: Diagnostic ratios for freeze-in temperature analysis
   ```

4. **Solar Wind Physics Context:**
   - Explain why charge state ratios matter (freeze-in temperature diagnostics)
   - Typical ratios used in solar wind research
   - Different from elemental abundance ratios

---

ISSUE 4: Component Capitalization and Temperature Components
**Problem:** RTN coordinate components incorrectly shown as lowercase, and temperature components not documented.

**Current (WRONG):**
- Spatial: "r" (radial), "t" (tangential), "n" (normal) - should be uppercase
- Missing: Temperature components (par, per, scalar)
- Confusion: "t" vs "T" in different contexts

**Correct Component Specification:**

**Spatial Components (for velocity, etc.):**
- Cartesian: "x", "y", "z" - lowercase
- RTN: "R", "T", "N" - UPPERCASE
  - "R" = radial
  - "T" = tangential (NOT temperature!)
  - "N" = normal

**Temperature Components (for temperature only):**
- "par" = parallel (to magnetic field) - lowercase
- "per" = perpendicular (to magnetic field) - lowercase
- "scalar" = scalar/isotropic - lowercase
- None = total/scalar temperature (when component omitted)

**Context Matters - Multiple Meanings of "T":**
1. **Measurement:** Temperature (uppercase "T" in M position)
2. **Component:** Tangential direction (uppercase "T" in C position)
3. **Examples:**
   - `TeXlabel("T", "par", "p")` - Parallel TEMPERATURE of protons
   - `TeXlabel("v", "T", "p")` - TANGENTIAL velocity of protons
   - Position in tuple distinguishes meaning

**Rationale:**
- RTN is standard solar wind coordinate system (capitalized)
- Temperature anisotropy (parallel vs perpendicular to B-field) is fundamental to plasma physics
- Different measurements have different valid components

**Impact Areas:**
- Feature 08 examples using RTN coordinates
- Feature 08 temperature examples
- Any MCS component documentation
- Component lists/tables showing available options

**Required Actions:**
1. **Find All Component References:**
   ```bash
   grep -rn '"r".*radial\|"t".*tangential\|"n".*normal' .claude/docs/feature_integration/
   grep -rn 'Component.*x.*y.*z.*r.*t.*n' .claude/docs/feature_integration/
   grep -rn 'temperature.*component' .claude/docs/feature_integration/
   ```

2. **Update Component Lists:**
   Old (incomplete):
   ```
   Components: "x", "y", "z", "r", "t", "n"
   ```

   New (complete):
   ```
   Spatial Components:
   - Cartesian: "x", "y", "z" (lowercase)
   - RTN: "R", "T", "N" (uppercase - radial, tangential, normal)

   Temperature Components:
   - "par" (parallel to B-field)
   - "per" (perpendicular to B-field)
   - "scalar" (isotropic)
   - None (total/scalar when omitted)
   ```

3. **Update All Examples:**
   - Any example using radial/tangential/normal must use uppercase R, T, N
   - Preserve lowercase for Cartesian x, y, z
   - Add temperature examples showing par, per, scalar components
   - Add clear note distinguishing temperature "T" (M element) from tangential "T" (C element)

4. **Create Component Reference Table:**
   ```markdown
   ## MCS Component Reference

   | Measurement Type | Valid Components | Example |
   |------------------|------------------|---------|
   | Velocity ("v") | x, y, z, R, T, N | TeXlabel("v", "R", "p") |
   | Number Density ("n") | None | TeXlabel("n", None, "p") |
   | Temperature ("T") | par, per, scalar, None | TeXlabel("T", "par", "p") |
   | Pressure ("p") | None | TeXlabel("p", None, "p") |

   **Note:** "T" appears in two contexts:
   - As measurement: "T" = temperature
   - As component: "T" = tangential (RTN coordinate)
   ```

---

ISSUE 5: Remove Isotope References
**Problem:** Documentation references isotope handling, but SolarWindPy does NOT handle isotopes - only charge states.

**Incorrect References to Remove:**
- Any mention of isotopes (³He, ⁴He, ¹²C, etc.)
- Isotope-related examples in TeXlabel
- Species codes like "3He", "4He", "12C", etc.

**Context from Code Review:**
In `solarwindpy/plotting/labels/base.py`, lines 14-64 show isotope templates but they're COMMENTED OUT.

**What SolarWindPy DOES Handle:**
- **Charge states:** O^6+, Fe^10+, C^5+, etc.
- **Species:** p (proton), a (alpha), e (electron), he (helium), elemental symbols
- **Charge state ratios:** O^6+/O^7+, Fe^10+/Fe^11+, etc.
- **NOT isotopes:** No ³He vs ⁴He distinction, no mass-based differentiation

**Required Actions:**
1. **Remove from Feature 08 Draft:**
   - Delete any isotope examples
   - Remove "isotope" from capability descriptions
   - Focus documentation on charge state handling

2. **Search for Isotope References:**
   ```bash
   grep -rn "isotope\|³He\|⁴He\|¹²C\|3He\|4He\|12C" .claude/docs/feature_integration/
   ```

3. **Replace with Charge State Examples:**
   - Instead of: "Handles isotopes like ³He"
   - Use: "Handles charge states like O^6+, Fe^10+, C^5+"
   - Add: "Handles charge state ratios like O^6+/O^7+ for temperature diagnostics"

---

DELIVERABLES:

**Phase 1: Research**
1. Read `solarwindpy/plotting/labels/composition.py` for exact Ion and ChargeStateRatio signatures
2. Read `solarwindpy/plotting/labels/base.py` to verify temperature component handling
3. Identify all MCS examples in current documentation
4. Find all RTN component references (lowercase r,t,n → uppercase R,T,N)
5. Find all temperature "t" references (lowercase → uppercase "T")
6. Find temperature examples missing par/per/scalar components
7. Find all isotope references to remove
8. Find all User/Local/Enterprise memory references to remove

**Phase 2: Update Plan Revisions**

**Update 1 (Memory Hierarchy):**
- Remove all User/Local/Enterprise memory references
- Update to single-tier Project memory only
- Add explanation of why Project memory only

**Update 2 (Unit Specifications):**
- No changes (separate issue)

**Update 3 (TeXlabel Feature 08):**
- Correct all MCS format examples
- Add temperature component examples (par/per/scalar)
- Fix RTN component capitalization
- Update Composition class examples (Ion, ChargeStateRatio)
- Remove all isotope references
- Add comprehensive component reference table

**Phase 3: Validation Checklist**

Before implementation:
- [ ] All User/Local/Enterprise memory references removed
- [ ] Project memory documented as single tier
- [ ] Ion and ChargeStateRatio signatures verified
- [ ] Temperature component handling verified
- [ ] All MCS examples use correct format
- [ ] All temperature measurement uses uppercase "T"
- [ ] Temperature examples include par/per/scalar components
- [ ] All RTN spatial components use uppercase R, T, N
- [ ] All Cartesian components remain lowercase x, y, z
- [ ] Temperature "T" vs tangential "T" distinction documented
- [ ] All Composition examples use correct signatures
- [ ] All isotope references removed
- [ ] Component reference table created
- [ ] All corrections verified against solarwindpy code
```

---

## Summary Table

| Issue | Current (Wrong) | Corrected | Files Affected |
|-------|----------------|-----------|----------------|
| 1. Memory | Multi-tier (Enterprise/Project/User/Local) | Single-tier (Project only) | 01_memory_hierarchy.md, INDEX.md |
| 2. MCS Format | "Vp", lowercase "t" for temp, missing temp components | ("v","x","p"), uppercase "T", par/per/scalar | All files with MCS examples |
| 3. Composition | Ion("O"), ChargeState | Ion("O",6), ChargeStateRatio("O",6,7) | Feature 08 |
| 4. Components | "r","t","n" lowercase | Spatial: R,T,N uppercase; Temp: par,per,scalar | All component lists |
| 5. Isotopes | Referenced as capability | Removed entirely | Feature 08 |

---

## Next Steps

1. Review this prompt
2. Execute Phase 1 (Research) to gather exact signatures
3. Create detailed file-by-file update specification
4. Implement all corrections
5. Validate with grep patterns
6. Commit changes

---

**Document Version:** 1.0
**Last Updated:** 2025-10-23
