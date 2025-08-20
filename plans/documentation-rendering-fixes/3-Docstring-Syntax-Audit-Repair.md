# Phase 3: Docstring Syntax Audit and Repair

## Phase Metadata
- **Phase**: 3/6
- **Estimated Duration**: 3.5 hours
- **Dependencies**: Phase 2 (infrastructure fixes)
- **Status**: Not Started

## 🎯 Phase Objective
Systematically audit and repair docstring syntax errors across all SolarWindPy modules to eliminate Sphinx warnings and ensure proper API documentation generation. Focus on modules with known HTML rendering issues.

## 🧠 Phase Context
With infrastructure fixes from Phase 2, docstring syntax errors are now the primary barrier to proper HTML rendering. This phase systematically fixes docstring issues in all modules, with priority on problematic modules identified in Phase 1.

## 📋 Implementation Tasks

### Task Group 1: Core Module Docstring Repair
- [ ] **Audit and Fix solarwindpy.core Module** (Est: 45 min) - Repair docstring syntax in core/*.py files (plasma.py, ions.py, base.py, etc.)
  - Commit: `<checksum>` 
  - Status: Pending
  - Notes: Focus on modules causing solarwindpy.core.html rendering issues
- [ ] **Audit and Fix solarwindpy.fitfunctions Module** (Est: 40 min) - Repair docstring syntax in fitfunctions/*.py files
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Priority module due to solarwindpy.fitfunctions.html rendering failures
- [ ] **Audit and Fix solarwindpy.instabilities Module** (Est: 25 min) - Repair docstring syntax in instabilities/*.py files
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Address solarwindpy.instabilities.html rendering issues

### Task Group 2: Solar Activity and Plotting Module Fixes
- [ ] **Audit and Fix solarwindpy.solar_activity Module** (Est: 35 min) - Repair docstring syntax in solar_activity/ hierarchy
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Fix solarwindpy.solar_activity.html rendering and submodule documentation
- [ ] **Audit and Fix solarwindpy.plotting Module** (Est: 30 min) - Repair docstring syntax in plotting/ hierarchy including labels/
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Ensure plotting documentation renders properly with visual elements
- [ ] **Audit and Fix solarwindpy.tools Module** (Est: 15 min) - Repair docstring syntax in tools/*.py files
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Smaller module, fewer expected issues

### Task Group 3: Docstring Quality and Standards
- [ ] **Standardize Docstring Format** (Est: 20 min) - Ensure consistent NumPy/Google docstring format across all modules
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Apply consistent formatting standards for professional documentation
- [ ] **Fix Cross-Reference Syntax** (Est: 15 min) - Repair Sphinx cross-reference syntax (:class:, :func:, :meth:, etc.)
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Fix broken internal links and references
- [ ] **Validate Mathematical Notation** (Est: 10 min) - Ensure LaTeX math expressions render properly in docstrings
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Critical for scientific software documentation

### Task Group 4: Validation and Testing
- [ ] **Execute Post-Fix Build** (Est: 15 min) - Run clean Sphinx build to validate docstring fixes
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Verify docstring repairs eliminate warnings
- [ ] **Spot Check API Documentation** (Est: 10 min) - Review generated API documentation for completeness and accuracy
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Ensure docstring fixes result in proper API documentation

## ✅ Phase Acceptance Criteria
- [ ] All docstring syntax errors eliminated across target modules
- [ ] Consistent docstring format applied throughout codebase
- [ ] Cross-references and internal links functioning correctly
- [ ] Mathematical notation rendering properly in documentation
- [ ] Sphinx build produces significantly fewer warnings
- [ ] API documentation generated correctly for all public functions/classes
- [ ] HTML pages show proper content organization with descriptions

## 🧪 Phase Testing Strategy
- **Module-by-Module Validation**: Test each module after docstring fixes
- **Syntax Verification**: Use Sphinx's strict mode to catch remaining syntax issues
- **Cross-Reference Testing**: Validate all internal documentation links
- **API Coverage**: Ensure all public APIs have proper documentation

## 🔧 Phase Technical Requirements
- **Docstring Standards**: NumPy/Google docstring format
- **Sphinx Syntax**: Proper reStructuredText and Sphinx directive usage
- **Mathematical Notation**: LaTeX math expressions for scientific content
- **Cross-References**: Sphinx intersphinx and autodoc linking

## 📂 Phase Affected Areas
- `solarwindpy/core/*.py` - All core module docstrings
- `solarwindpy/fitfunctions/*.py` - All fitfunctions module docstrings
- `solarwindpy/instabilities/*.py` - All instabilities module docstrings
- `solarwindpy/solar_activity/**/*.py` - All solar activity module docstrings
- `solarwindpy/plotting/**/*.py` - All plotting module docstrings
- `solarwindpy/tools/*.py` - All tools module docstrings

## 📊 Phase Progress Tracking

### Current Status
- **Tasks Completed**: 0/11
- **Time Invested**: 0h of 3.5h
- **Completion Percentage**: 0%
- **Last Updated**: 2025-08-13

### Blockers & Issues
- Dependent on stable Sphinx configuration from Phase 2
- May discover complex docstring issues requiring additional time

### Next Actions
- Begin with core module docstring audit
- Prioritize modules with known HTML rendering failures
- Apply systematic docstring syntax fixes

## 💬 Phase Implementation Notes

### Implementation Decisions
- Focus on modules with known HTML rendering issues first
- Apply consistent docstring standards across all modules
- Use DocumentationMaintainer agent for docstring syntax expertise

### Lessons Learned
[To be populated during implementation]

### Phase Dependencies Resolution
- Requires stable Sphinx infrastructure from Phase 2
- Provides clean docstrings for HTML rendering validation in Phase 4

---
*Phase 3 of 6 - Documentation Rendering Fixes - Last Updated: 2025-08-13*
*See [0-Overview.md](./0-Overview.md) for complete plan context and cross-phase coordination.*