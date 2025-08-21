# Phase 1: Discovery & Inventory

## Phase Metadata
- **Status**: ✅ Completed
- **Estimated Duration**: 2 hours
- **Actual Duration**: 2 hours
- **Completion Date**: 2025-08-21
- **Git Commit**: <checksum>
- **Branch**: plan/documentation-code-audit

## 🎯 Objective
Conduct comprehensive discovery and inventory of all code examples across SolarWindPy documentation to identify broken examples, deprecated APIs, missing imports, and compliance issues.

## 📋 Tasks Checklist
- [x] **Scan RST documentation files** (45 min)
  - [x] `docs/source/usage.rst` - 7 code blocks identified
  - [x] `docs/source/tutorial/quickstart.rst` - 2 code blocks identified  
  - [x] `docs/source/installation.rst` - 5 code blocks identified
  - [x] `README.rst` - 6 code blocks identified

- [x] **Analyze Python module docstrings** (60 min)
  - [x] `solarwindpy/core/plasma.py` - 8 doctest examples
  - [x] `solarwindpy/core/ions.py` - 1 doctest example
  - [x] `solarwindpy/fitfunctions/tex_info.py` - 1 doctest example  
  - [x] `solarwindpy/tools/__init__.py` - 3 doctest examples
  - [x] Additional modules requiring detailed analysis identified

- [x] **Categorize issues by severity** (10 min)
  - [x] Critical: Deprecated API usage (Plasma constructor)
  - [x] Critical: Non-existent methods (add_ion_species, validate_physics)
  - [x] High: Missing imports and undefined variables (80% of examples)
  - [x] Medium: Inconsistent import aliases (sw vs swp)
  - [x] Medium: Missing MultiIndex data structure setup

- [x] **Create comprehensive inventory document** (5 min)
  - [x] JSON format with detailed issue categorization
  - [x] Line-by-line tracking of all code examples
  - [x] Dependencies and issue classification
  - [x] Priority recommendations for remediation

## 📁 Deliverables
- ✅ **docs_audit_inventory.json**: Comprehensive inventory of 47 examples across 13 files
- ✅ **Issue categorization**: Critical, High, Medium, Low severity classifications
- ✅ **Pattern analysis**: Common import patterns, data access patterns, operations
- ✅ **Next phase priorities**: Actionable priority list for systematic remediation

## 🔍 Key Findings

### Critical Issues Discovered
1. **Deprecated Plasma Constructor**: `Plasma(epoch=)` usage in usage.rst
2. **Non-existent Methods**: `add_ion_species()`, `validate_physics()` referenced but don't exist
3. **Broken Import References**: `solarwindpy.plotting.time_series`, `solarwindpy.instabilities.beta_ani_inst`

### High-Impact Issues
4. **Missing Data Setup**: 80% of examples assume complex MultiIndex data without initialization
5. **Undefined Variables**: `data`, `df`, `temperature_data` variables used without definition
6. **Incomplete Examples**: Ellipsis (`...`) in DataFrame construction examples

### Consistency Issues
7. **Import Alias Inconsistency**: Mixed usage of `import solarwindpy as sw` vs `import solarwindpy as swp`
8. **Missing Dependencies**: Examples reference modules without proper imports

### Statistics Summary
- **Total Examples Found**: 47
- **Files with Examples**: 13
- **Examples with Issues**: 42 (89%)
- **Critical Issues**: 8
- **High-Impact Issues**: 15
- **Medium Issues**: 19

## 🔄 Impact Analysis

### User Experience Impact
- **New User Friction**: Broken examples create immediate adoption barriers
- **Documentation Credibility**: 89% failure rate undermines package reliability
- **Support Burden**: Broken examples generate user support requests
- **Research Productivity**: Scientists waste time debugging instead of doing research

### Development Impact
- **Maintenance Overhead**: Manual validation required for all documentation changes
- **Quality Assurance**: No automated validation of example correctness
- **Contributor Confusion**: Inconsistent patterns make contribution difficult
- **Technical Debt**: Accumulated broken examples require systematic remediation

## 📊 Remediation Priority Matrix

### Phase 2 Immediate Priorities
1. **Environment Setup**: Create testing infrastructure for example validation
2. **Critical API Fixes**: Address deprecated Plasma constructor immediately
3. **Import Standardization**: Establish consistent `swp` alias usage

### Phase 3-4 Core Remediation
4. **Data Structure Examples**: Create reusable MultiIndex setup patterns
5. **Method Validation**: Verify all referenced methods exist and work correctly
6. **Missing Imports**: Systematic addition of required imports to all examples

### Phase 5-6 Quality Assurance
7. **Physics Compliance**: Ensure examples follow thermal speed and unit conventions
8. **Automated Testing**: Integrate doctest and example validation into CI/CD

## 🔗 Dependencies for Next Phase
- **Testing Environment**: Conda environment with full SolarWindPy installation
- **Validation Scripts**: Tools to extract and execute RST code blocks
- **Physics Validation**: Integration with existing physics constraint checking
- **CI/CD Integration**: Hooks for automated example testing

## 📝 Implementation Notes

### Discovery Process
1. **Systematic File Scanning**: Used grep and manual analysis to identify all code blocks
2. **Issue Classification**: Categorized issues by type and severity for prioritization
3. **Pattern Recognition**: Identified common problems for batch remediation strategies
4. **Dependency Mapping**: Tracked import requirements and missing dependencies

### Documentation Structure Analysis
- **RST Files**: Mix of `code-block:: python` and `code-block:: bash` directives
- **Docstring Examples**: Standard Python doctest format with `>>>` prompts
- **Complexity Range**: From simple imports to complex MultiIndex data manipulation
- **Scientific Domain**: Physics calculations, data analysis, visualization examples

### Key Patterns Identified
```python
# Common import patterns found:
import solarwindpy as swp        # Preferred standard
import solarwindpy as sw         # Inconsistent usage
import solarwindpy.plotting as swpp
from solarwindpy.fitfunctions import Gaussian
from solarwindpy.instabilities import beta_ani_inst  # Broken

# Common data access patterns:
plasma.data.xs('n', level='M')   # Number density
plasma.data.xs('v', level='M')   # Velocity
plasma.p1.n                      # Proton density shorthand
plasma.get_ion('p1')             # Ion access method
```

## ✅ Completion Criteria Met
- ✅ All documentation files systematically analyzed
- ✅ Complete inventory with line-by-line tracking
- ✅ Issues categorized by severity and type
- ✅ Remediation priorities established
- ✅ Next phase dependencies identified
- ✅ Comprehensive JSON inventory document created

## 🔄 Transition to Phase 2
**Ready for Phase 2: Execution Environment Setup**
- Inventory complete with 47 examples catalogued
- Critical issues identified and prioritized
- Testing infrastructure requirements defined
- Validation strategy framework established

**Next Actions:**
1. Set up isolated testing environment
2. Create example extraction and execution tools
3. Establish validation criteria and success metrics
4. Begin systematic validation of highest-priority examples

---

**📝 User Action Required**: After reviewing this completed phase, run:
```bash
git add plans/documentation-code-audit/1-Discovery-Inventory.md docs_audit_inventory.json
git commit -m "docs: complete Phase 1 discovery and inventory for documentation code audit

- Comprehensive inventory of 47 examples across 13 files
- Identified critical issues: deprecated APIs, broken imports, missing data
- Categorized issues by severity with remediation priorities
- Created docs_audit_inventory.json with detailed findings
- Ready for Phase 2: Execution Environment Setup

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Then create compacted state for session continuity:**
```bash
python .claude/hooks/create-compaction.py \
  --trigger "Phase 1 completion - comprehensive discovery and inventory complete" \
  --context "47 examples catalogued, ready for Phase 2 environment setup"
```

**Phase 1 Complete** ✅