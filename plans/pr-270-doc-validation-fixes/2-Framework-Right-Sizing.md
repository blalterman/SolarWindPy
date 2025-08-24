# Phase 2: Framework Right-Sizing

## Overview
**Goal**: Consolidate over-engineered documentation validation framework from 3000+ lines to appropriate ~300 lines
**Estimated Time**: 2-3 hours
**Prerequisites**: Phase 1 completed (PR checks fixed)
**Outputs**: Streamlined validation framework, archived over-engineering

## Context
The current documentation validation framework is over-engineered for SolarWindPy's needs:
- **Current**: 3000+ lines of validation code for 47 examples
- **Target**: ~300 lines for essential validation
- **Problem**: 85.7% failure rate indicates framework complexity exceeds requirements
- **Solution**: Right-size to scientific package appropriate complexity

## Tasks

### Task 2.1: Framework Analysis and Consolidation Planning
**Estimated Time**: 45-60 minutes
- [ ] **Analyze current validation framework structure**
  - [ ] Map all files in `scripts/doc_validation/` and `scripts/validation_framework/`
  - [ ] Identify essential vs. over-engineered components
  - [ ] Measure current lines of code: `find scripts/ -name '*.py' -path '*validation*' | xargs wc -l`
  - [ ] Document dependency relationships
- [ ] **Identify consolidation targets**
  - [ ] Essential: doctest execution, basic validation, CI integration
  - [ ] Over-engineered: complex reporting, enterprise-scale validation, advanced analytics
  - [ ] Archive candidates: unused frameworks, experimental features
- [ ] **Design simplified architecture**
  - [ ] Core validation: ~100 lines (doctest runner + basic checks)
  - [ ] CI integration: ~100 lines (GitHub Actions integration)
  - [ ] Utilities: ~100 lines (reporting, formatting, helpers)
  - [ ] Total target: ~300 lines

### Task 2.2: Create Consolidated Validation Framework
**Estimated Time**: 60-90 minutes
- [ ] **Create new simplified structure**
  - [ ] Design `scripts/simple_doc_validation/` directory
  - [ ] Create `doctest_runner.py` (~100 lines) - core doctest execution
  - [ ] Create `ci_integration.py` (~100 lines) - GitHub Actions interface
  - [ ] Create `validation_utils.py` (~100 lines) - reporting and utilities
- [ ] **Implement essential functionality**
  - [ ] Doctest discovery and execution for physics examples
  - [ ] Basic result reporting (pass/fail counts, example status)
  - [ ] CI/CD integration points (exit codes, artifact generation)
  - [ ] Error handling and logging appropriate for scientific package
- [ ] **Preserve critical features**
  - [ ] Python 3.9-3.11 compatibility
  - [ ] Physics example validation (core requirement)
  - [ ] Integration with existing CI/CD workflows
  - [ ] Basic reporting for debugging failures

### Task 2.3: Archive Over-Engineered Components
**Estimated Time**: 30-45 minutes
- [ ] **Create archive structure**
  - [ ] Create `scripts/archived/doc_validation_v1/` directory
  - [ ] Move over-engineered components to archive
  - [ ] Preserve complete audit trail of original implementation
- [ ] **Archive systematically**
  - [ ] Move `scripts/validation_framework/` → `scripts/archived/doc_validation_v1/validation_framework/`
  - [ ] Move complex components from `scripts/doc_validation/` → archive
  - [ ] Keep only essential components in active use
- [ ] **Document archive rationale**
  - [ ] Create `scripts/archived/doc_validation_v1/README.md`
  - [ ] Explain why components were over-engineered
  - [ ] Document lessons learned for future reference
  - [ ] Preserve migration path if ever needed

### Task 2.4: Update CI/CD Integration
**Estimated Time**: 30-45 minutes
- [ ] **Update GitHub Actions workflows**
  - [ ] Modify `.github/workflows/doctest-validation.yml` to use simplified framework
  - [ ] Update script paths and execution commands
  - [ ] Simplify workflow logic to match reduced complexity
- [ ] **Streamline execution pipeline**
  - [ ] Remove unnecessary validation steps
  - [ ] Focus on essential physics example validation
  - [ ] Optimize for speed and reliability over comprehensive analysis
- [ ] **Verify integration**
  - [ ] Test simplified workflow locally
  - [ ] Ensure all essential validation still occurs
  - [ ] Confirm reduced execution time and complexity

## Validation Criteria
- [ ] Framework reduced from 3000+ to ~300 lines of code
- [ ] Essential doctest functionality preserved
- [ ] Physics examples continue to validate correctly
- [ ] CI/CD integration maintains reliability
- [ ] 90% reduction in framework complexity achieved
- [ ] Archive preserves complete audit trail
- [ ] Performance improvement in validation execution time

## Implementation Notes
**Right-Sizing Philosophy:**
- Scientific packages need proportional tooling complexity
- 47 examples ≠ 1000+ examples validation requirements
- Maintenance burden must match team capacity
- Focus on essential functionality, not enterprise features

**Consolidation Strategy:**
- Preserve essential physics validation capabilities
- Remove enterprise-scale features (complex reporting, analytics)
- Maintain CI/CD integration for automated validation
- Archive (don't delete) for audit trail and learning

**Performance Targets:**
- Faster validation execution (less overhead)
- Simpler debugging (fewer layers of abstraction)
- Easier maintenance (fewer files, clearer purpose)
- Sustainable complexity for research package team

## Git Commit
**At phase completion, commit with:**
```bash
git add .
git commit -m "refactor: right-size documentation validation framework

- Consolidate validation code from 3000+ to ~300 lines
- Archive over-engineered components to scripts/archived/
- Create simplified validation framework appropriate for 47 examples
- Maintain essential doctest functionality and CI/CD integration
- Achieve 90% reduction in framework complexity
- Focus on scientific package appropriate tooling

Checksum: <checksum>"
```

## Next Phase
Proceed to [Phase 3: Sustainable Documentation Process](./3-Sustainable-Documentation.md) to establish long-term maintenance approach.