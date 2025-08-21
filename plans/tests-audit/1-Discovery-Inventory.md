# Phase 1: Discovery & Inventory

## Phase Metadata
- **Phase**: 1/6
- **Estimated Duration**: 2-3 hours
- **Dependencies**: None
- **Status**: Not Started

## 🎯 Phase Objective
Systematically discover, enumerate, and classify all 1,132 test functions across 63 test files in the SolarWindPy test suite. Create comprehensive inventory artifacts (TEST_INVENTORY.csv and TEST_INVENTORY.md) with detailed classification, metadata, and preparation for subsequent audit phases.

## 🧠 Phase Context
This foundational phase establishes the complete baseline for the test suite audit. The inventory will:
- Provide accurate test count verification (targeting 1,132 functions across 63 files)
- Enable systematic classification for targeted improvements
- Identify test coverage gaps and patterns
- Support agent coordination for specialized audit work
- Create structured artifacts for cross-phase tracking

## 📋 Implementation Tasks

### Task Group 1: Test Discovery & Enumeration
- [ ] **Enumerate all test files** (Est: 20 min) - Scan tests/ directory and subdirectories for test_*.py files
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Use find command and verify against expected 63 files
- [ ] **Extract test function definitions** (Est: 30 min) - Parse each file to identify test functions (def test_*)
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Include function signatures, line numbers, and basic metadata
- [ ] **Verify test count accuracy** (Est: 15 min) - Confirm discovered count matches expected 1,132 functions
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Document any discrepancies and investigate if count differs

### Task Group 2: Test Classification & Metadata
- [ ] **Classify test types** (Est: 45 min) - Categorize each test function by type (unit, physics, edge, integration, performance)
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Use function names, docstrings, and code patterns for classification
- [ ] **Extract physics domain mapping** (Est: 30 min) - Map tests to physics modules (plasma, ions, magnetic field, instabilities)
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Identify core physics functions being tested
- [ ] **Analyze test complexity** (Est: 25 min) - Assess test complexity (simple, moderate, complex) based on code structure
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Consider number of assertions, setup complexity, data requirements

### Task Group 3: Coverage Analysis & Gap Identification
- [ ] **Generate current coverage report** (Est: 20 min) - Run pytest --cov to establish baseline coverage metrics
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Document current 77.1% coverage and identify uncovered modules
- [ ] **Identify coverage gaps** (Est: 30 min) - Map uncovered code to required test additions for ≥95% target
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Estimate ~200 additional tests needed based on coverage analysis
- [ ] **Document physics validation gaps** (Est: 25 min) - Identify missing physics constraint tests (SI units, thermal speed, etc.)
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Prepare for Phase 2 PhysicsValidator agent work

### Task Group 4: Inventory Artifact Generation
- [ ] **Create TEST_INVENTORY.csv** (Est: 20 min) - Generate structured CSV with all test metadata for programmatic access
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Include file, function, type, domain, complexity, line_number fields
- [ ] **Create TEST_INVENTORY.md** (Est: 25 min) - Generate human-readable Markdown summary with statistics and insights
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Include test distribution charts, gap analysis, and next phase preparation
- [ ] **Validate inventory completeness** (Est: 15 min) - Cross-check artifacts against discovery results for accuracy
  - Commit: `<checksum>`
  - Status: Pending
  - Notes: Ensure no tests missed and classifications are consistent

## ✅ Phase Acceptance Criteria
- [ ] All 63 test files discovered and catalogued
- [ ] All 1,132 test functions enumerated with metadata
- [ ] Test classification completed (unit, physics, edge, integration, performance)
- [ ] Physics domain mapping established for core modules
- [ ] Current coverage baseline documented (77.1%)
- [ ] Coverage gaps identified with ~200 test estimate for ≥95% target
- [ ] TEST_INVENTORY.csv generated with complete metadata
- [ ] TEST_INVENTORY.md created with summary analysis
- [ ] Inventory artifacts validated for accuracy and completeness
- [ ] TestEngineer agent coordination documented for Phase 2 handoff

## 🧪 Phase Testing Strategy
- **Inventory Validation**: Cross-check discovered tests against pytest --collect-only output
- **Classification Accuracy**: Spot-check test classifications using function analysis
- **Artifact Integrity**: Validate CSV/MD artifacts contain all discovered tests
- **Coverage Baseline**: Confirm coverage report matches documented 77.1% baseline

## 🔧 Phase Technical Requirements
- **Dependencies**: pytest, pytest-cov, pandas (for CSV generation), Python AST parsing
- **Environment**: SolarWindPy development environment with all test dependencies
- **Constraints**: Must maintain existing test functionality during discovery
- **Tools**: find, grep, Python AST, pytest collection utilities

## 📂 Phase Affected Areas
- `tests/` - Read-only analysis of all test files
- `.claude/artifacts/tests-audit/` - Create inventory artifacts directory
- `plans/tests-audit/` - Update phase documentation with progress
- Coverage reports and baseline documentation

## 📊 Phase Progress Tracking

### Current Status
- **Tasks Completed**: 0/12
- **Time Invested**: 0h of 2-3h
- **Completion Percentage**: 0%
- **Last Updated**: 2025-08-21

### Blockers & Issues
- None currently identified
- Potential blocker: Test count mismatch requiring investigation
- Potential blocker: Complex test classification requiring manual review

### Next Actions
- Start with Task Group 1: Test Discovery & Enumeration
- Set up artifacts directory: `.claude/artifacts/tests-audit/`
- Coordinate with TestEngineer agent for systematic test analysis
- Begin baseline coverage analysis

## 💬 Phase Implementation Notes

### Implementation Decisions
- Use Python AST parsing for reliable test function extraction
- Classify tests using function names, docstrings, and code patterns
- Store artifacts in dedicated directory for cross-phase access
- Generate both CSV (programmatic) and MD (human-readable) formats

### Lessons Learned
- [To be populated during implementation]
- [Test discovery patterns and classification approaches]

### Phase Dependencies Resolution
- No dependencies from previous phases (foundational phase)
- Provides comprehensive test inventory for all subsequent phases
- Establishes baseline metrics for coverage and quality improvements

## 🔄 Phase Completion Protocol

### Git Commit Instructions
Upon completion of all Phase 1 tasks:
1. **Stage all changes**: `git add .claude/artifacts/tests-audit/ plans/tests-audit/1-Discovery-Inventory.md`
2. **Create atomic commit**: `git commit -m "feat(tests): complete Phase 1 - test discovery and inventory
   
   - Enumerated all 1,132 test functions across 63 test files
   - Created comprehensive test classification and metadata
   - Generated TEST_INVENTORY.csv and TEST_INVENTORY.md artifacts
   - Established baseline coverage metrics (77.1%)
   - Identified ~200 additional tests needed for ≥95% target
   
   🤖 Generated with Claude Code
   Co-Authored-By: Claude <noreply@anthropic.com>"`

### Context Compaction Prompt
**⚡ IMPORTANT**: After committing Phase 1, **immediately prompt user to compact context**:
```
Phase 1 (Discovery & Inventory) is complete with atomic git commit. 
Context is now at token boundary - please run `/compact` to preserve session state 
and prepare for Phase 2 (Physics Validation Audit).
```

---
*Phase 1 of 6 - Physics-Focused Test Suite Audit - Last Updated: 2025-08-21*
*See [0-Overview.md](./0-Overview.md) for complete plan context and cross-phase coordination.*