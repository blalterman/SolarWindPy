# Merge Conflict Resolution Plan for CI/CD Implementation

**Date**: 2025-08-25  
**Purpose**: Resolve Python syntax conflicts and continue Phase 4 RC testing  
**Context**: Currently in merge state with conflicts in 3 test files  

## Current Situation

- **Branch**: master (in merge state)
- **Conflicts**: 3 test files with Python context manager syntax differences
- **Goal**: Complete merge and proceed with v0.1.0-rc5 RC testing

## Files with Conflicts

1. `tests/solar_activity/sunspot_number/test_sidc.py`
2. `tests/solar_activity/sunspot_number/test_ssn_extrema.py` 
3. `tests/test_statusline.py`

## Resolution Strategy

### 1. **Accept Python 3.10+ Syntax (REMOTE)**

**Rationale**: 
- Project requires Python 3.10+ (`pyproject.toml`: `requires-python = ">=3.10,<4"`)
- CI workflows use Python 3.10-3.12 matrix only
- REMOTE uses parenthesized context managers (Python 3.10+ feature)

**Example Change**:
```python
# OLD (LOCAL/HEAD) - Python 3.9 compatible
with patch.object(SIDC, "_init_logger"), patch.object(
    SIDC, "calculate_extrema_kind"
), patch.object(SIDC, "calculate_edge"):

# NEW (REMOTE) - Python 3.10+ required  
with (
    patch.object(SIDC, "_init_logger"),
    patch.object(SIDC, "calculate_extrema_kind"),
    patch.object(SIDC, "calculate_edge"),
):
```

### 2. **File-Specific Resolutions**

#### **test_sidc.py** (Most Complex)
- **Lines 68-113**: Remove duplicate fixtures (keep only module-level fixtures)
- **Lines 428-451**: Keep REMOTE's `test_normalized_property_without_nssn_column`
- **Lines 468-482**: Keep LOCAL's `test_data_property_access` 
- **All other conflicts**: Accept REMOTE syntax

#### **test_ssn_extrema.py**
- **All conflicts**: Accept REMOTE version (syntax-only changes)
- **12 conflict sections**: All use Python 3.10+ parenthesized context managers

#### **test_statusline.py**
- **All conflicts**: Accept REMOTE version (syntax-only changes)
- **5 conflict sections**: All use Python 3.10+ parenthesized context managers

### 3. **CI/CD Pipeline Correction**

**Issue Found**: The `release-pipeline.yml` from Phase 1 incorrectly includes Python 3.9

**Required Fix**:
```yaml
# CURRENT (INCORRECT)
python-version: ['3.9', '3.10', '3.11', '3.12']

# CORRECTED
python-version: ['3.10', '3.11', '3.12']
```

## Implementation Steps

### Phase 1: Resolve Merge Conflicts
1. Edit `tests/solar_activity/sunspot_number/test_sidc.py`:
   - Accept REMOTE syntax for context managers
   - Remove duplicate fixtures (lines 70-111)
   - Preserve both unique tests
   
2. Edit `tests/solar_activity/sunspot_number/test_ssn_extrema.py`:
   - Accept ALL REMOTE changes

3. Edit `tests/test_statusline.py`:
   - Accept ALL REMOTE changes

4. Resolve `.claude/compacted_state.md` conflict

### Phase 2: Fix Python Version Requirements
1. Update `release-pipeline.yml` Python matrix to exclude 3.9
2. Ensure consistency with project's Python 3.10+ requirement

### Phase 3: Validation
1. Syntax validation: `python -m py_compile` on test files
2. Run tests: `pytest tests/solar_activity/sunspot_number/ tests/test_statusline.py -v`
3. Verify no duplicate fixtures: `grep -n "@pytest.fixture" tests/solar_activity/sunspot_number/test_sidc.py`

### Phase 4: Complete Merge
1. Add resolved files: `git add`
2. Complete merge commit
3. Continue with CI/CD Phase 4: v0.1.0-rc5 testing

## Risk Assessment

**Low Risk**:
- Changes are syntax-only in test files (no production code impact)
- REMOTE version already tested with Python 3.10+
- Aligns with project's official Python version requirements

**Benefits**:
- Consistent with Python 3.10+ migration
- Cleaner, more maintainable test code
- No impact on CI/CD deployment functionality

## Expected Outcome

- Clean merge with modern Python syntax
- Preserved test coverage (both unique tests kept)
- Ready to proceed with Phase 4: RC Testing
- CI/CD workflows aligned with Python 3.10+ requirement

## Success Criteria

- [ ] All 3 test files resolved with Python 3.10+ syntax
- [ ] No duplicate fixtures in test_sidc.py  
- [ ] All tests pass: `pytest tests/solar_activity/sunspot_number/ tests/test_statusline.py -v`
- [ ] Merge completed successfully
- [ ] Ready for v0.1.0-rc5 tag creation and testing

---
*This plan ensures Python 3.10+ compliance and maintains the CI/CD implementation timeline.*