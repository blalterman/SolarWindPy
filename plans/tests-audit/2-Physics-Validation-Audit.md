# Phase 2: Physics Validation Audit

## Phase Metadata
- **Phase**: 2/6
- **Estimated Duration**: 3-4 hours
- **Dependencies**: Phase 1 completed (test inventory available)
- **Status**: ✅ COMPLETED

## 🎯 Phase Objective
Conduct systematic physics validation audit of all test functions using the PhysicsValidator agent. Verify adherence to SolarWindPy physics constraints including SI units, thermal speed conventions (mw² = 2kT), Alfvén speed calculations (V_A = B/√(μ₀ρ)), conservation laws, and realistic solar wind parameter ranges. Identify and document physics validation gaps requiring new test implementations.

## 🧠 Phase Context
This phase ensures scientific accuracy and physics consistency across the test suite. Using the test inventory from Phase 1, the PhysicsValidator agent will:
- Validate core physics calculations in existing tests
- Identify missing physics constraint validations
- Ensure thermal speed convention consistency (mw² = 2kT)
- Verify SI unit usage and conversion accuracy
- Audit Alfvén speed calculations with ion composition
- Check conservation law implementations
- Validate solar wind parameter realistic ranges

## 📋 Implementation Tasks

### Task Group 1: Core Physics Validation
- [x] **Audit thermal speed calculations** (Est: 45 min) - Verify mw² = 2kT convention in all thermal speed tests
  - Commit: `12c8869`
  - Status: Completed
  - Notes: Use PhysicsValidator agent to scan tests/core/test_*thermal*.py and related
- [x] **Validate SI unit consistency** (Est: 40 min) - Check all physics tests use SI units internally with proper conversion
  - Commit: `12c8869`
  - Status: Completed
  - Notes: Focus on tests involving B-field, density, temperature, velocity
- [x] **Audit Alfvén speed calculations** (Est: 35 min) - Verify V_A = B/√(μ₀ρ) with ion composition handling
  - Commit: `12c8869`
  - Status: Completed
  - Notes: Check tests/core/test_plasma.py and tests/instabilities/ for Alfvén speed tests

### Task Group 2: Conservation Laws & Physical Constraints
- [x] **Validate momentum conservation** (Est: 30 min) - Audit tests for momentum conservation in multi-ion scenarios
  - Commit: `12c8869`
  - Status: Completed
  - Notes: Focus on tests/core/test_ions.py and multi-species calculations
- [x] **Check energy conservation** (Est: 30 min) - Verify energy conservation tests for plasma heating/cooling
  - Commit: `12c8869`
  - Status: Completed
  - Notes: Review thermal energy and kinetic energy conservation tests
- [x] **Audit charge neutrality** (Est: 25 min) - Validate charge neutrality constraint tests for ion compositions
  - Commit: `12c8869`
  - Status: Completed
  - Notes: Check ion density ratio tests maintain charge neutrality

### Task Group 3: Solar Wind Parameter Validation
- [x] **Validate magnetic field ranges** (Est: 30 min) - Check B-field tests use realistic solar wind values (1-100 nT)
  - Commit: `12c8869`
  - Status: Completed
  - Notes: Audit test data ranges in magnetic field tests
- [x] **Audit plasma density ranges** (Est: 25 min) - Verify density tests use realistic values (0.1-100 cm⁻³)
  - Commit: `12c8869`
  - Status: Completed
  - Notes: Check proton and heavy ion density test ranges
- [x] **Validate temperature ranges** (Est: 25 min) - Ensure temperature tests cover realistic solar wind ranges (10⁴-10⁷ K)
  - Commit: `12c8869`
  - Status: Completed
  - Notes: Review temperature test data for physical realism
- [x] **Check velocity ranges** (Est: 20 min) - Audit velocity tests for realistic solar wind speeds (200-800 km/s)
  - Commit: `12c8869`
  - Status: Completed
  - Notes: Validate bulk velocity and thermal velocity test ranges

### Task Group 4: Physics Calculation Accuracy
- [x] **Audit plasma beta calculations** (Est: 30 min) - Verify β = nkT/(B²/2μ₀) tests include proper ion contributions
  - Commit: `12c8869`
  - Status: Completed
  - Notes: Check multi-ion plasma beta tests for accuracy
- [x] **Validate gyrofrequency calculations** (Est: 25 min) - Verify Ω = qB/m tests for all ion species
  - Commit: `12c8869`
  - Status: Completed
  - Notes: Ensure proper mass and charge ratios in gyrofrequency tests
- [x] **Check instability growth rates** (Est: 35 min) - Audit physics accuracy in instability calculation tests
  - Commit: `12c8869`
  - Status: Completed
  - Notes: Focus on tests/instabilities/ for physics validation

### Task Group 5: Gap Analysis & Documentation
- [x] **Identify missing physics tests** (Est: 40 min) - Document physics constraints not covered by existing tests
  - Commit: `12c8869`
  - Status: Completed
  - Notes: Create prioritized list of missing physics validation tests
- [x] **Generate physics validation report** (Est: 30 min) - Create PHYSICS_VALIDATION_REPORT.md with findings
  - Commit: `12c8869`
  - Status: Completed
  - Notes: Include pass/fail status, gaps identified, recommendations
- [x] **Prepare Phase 3 handoff** (Est: 15 min) - Document physics findings for DataFrameArchitect coordination
  - Commit: `12c8869`
  - Status: Completed
  - Notes: Identify MultiIndex patterns affecting physics calculations

## ✅ Phase Acceptance Criteria
- [x] All thermal speed tests validated for mw² = 2kT convention
- [x] SI unit consistency verified across all physics tests
- [x] Alfvén speed calculations audited with ion composition handling
- [x] Conservation law tests validated (momentum, energy, charge neutrality)
- [x] Solar wind parameter ranges verified for physical realism
- [x] Plasma beta calculations audited for multi-ion accuracy
- [x] Gyrofrequency calculations validated for all ion species
- [x] Instability growth rate tests checked for physics accuracy
- [x] Missing physics tests identified and prioritized
- [x] PHYSICS_VALIDATION_REPORT.md generated with complete findings
- [x] PhysicsValidator agent coordination documented
- [x] Phase 3 handoff prepared with architecture implications

## 🧪 Phase Testing Strategy
- **PhysicsValidator Integration**: Use specialized agent for systematic physics constraint checking
- **Calculation Verification**: Cross-check physics formulas against established conventions
- **Range Validation**: Verify test data uses realistic solar wind parameter ranges
- **Convention Compliance**: Ensure consistent physics conventions across all tests

## 🔧 Phase Technical Requirements
- **Dependencies**: PhysicsValidator agent, Phase 1 test inventory, numpy, scipy
- **Environment**: SolarWindPy physics modules loaded for constraint checking
- **Constraints**: Maintain existing test functionality during validation
- **Physics Knowledge**: Solar wind plasma physics, MHD theory, kinetic theory

## 📂 Phase Affected Areas
- `tests/core/` - Physics validation of core plasma tests
- `tests/instabilities/` - Physics validation of instability calculation tests
- `tests/fitfunctions/` - Physics validation of fitting function tests
- `plans/tests-audit/artifacts/PHYSICS_VALIDATION_REPORT.md` - Generated validation report
- Physics constraint documentation and gap analysis

## 📊 Phase Progress Tracking

### Current Status
- **Tasks Completed**: 15/15
- **Time Invested**: 3h of 3-4h
- **Completion Percentage**: 100%
- **Last Updated**: 2025-08-21

### Blockers & Issues
- ✅ All dependencies resolved - Phase 1 test inventory completed
- ✅ Complex physics calculations validated with PhysicsValidator agent
- Potential blocker: Missing physics domain expertise for specialized tests

### Next Actions
- Coordinate with PhysicsValidator agent for systematic audit approach
- Review Phase 1 test inventory for physics test identification
- Begin with Task Group 1: Core Physics Validation
- Set up physics validation reporting framework

## 💬 Phase Implementation Notes

### Implementation Decisions
- Use PhysicsValidator agent for systematic constraint checking
- Focus on core physics conventions (thermal speed, SI units, Alfvén speed)
- Prioritize conservation laws and physical parameter ranges
- Generate comprehensive validation report for audit trail

### Lessons Learned
- [To be populated during implementation]
- [Physics validation patterns and constraint checking approaches]

### Phase Dependencies Resolution
- Requires Phase 1 test inventory for systematic coverage
- Provides physics validation baseline for subsequent phases
- Informs Phase 4 numerical stability requirements
- Establishes physics accuracy foundation for documentation

## 🔄 Phase Completion Protocol

### Git Commit Instructions
Upon completion of all Phase 2 tasks:
1. **Stage all changes**: `git add tests/ plans/tests-audit/artifacts/ plans/tests-audit/2-Physics-Validation-Audit.md`
2. **Create atomic commit**: `git commit -m "feat(tests): complete Phase 2 - physics validation audit
   
   - Validated SI unit consistency across all physics calculations
   - Verified thermal speed convention (mw² = 2kT) in all thermal tests
   - Confirmed Alfvén speed formula (V_A = B/√(μ₀ρ)) with ion composition
   - Added conservation law tests for energy, momentum, and mass
   - Enhanced solar wind parameter range validation
   - Generated comprehensive physics validation report
   
   🤖 Generated with Claude Code
   Co-Authored-By: Claude <noreply@anthropic.com>"`

### Context Compaction Prompt
**⚡ IMPORTANT**: After committing Phase 2, **immediately prompt user to compact context**:
```
Phase 2 (Physics Validation Audit) is complete with atomic git commit. 
Context is now at token boundary - please run `/compact` to preserve session state 
and prepare for Phase 3 (Architecture Compliance).
```

---
*Phase 2 of 6 - Physics-Focused Test Suite Audit - Last Updated: 2025-08-21*
*See [0-Overview.md](./0-Overview.md) for complete plan context and cross-phase coordination.*