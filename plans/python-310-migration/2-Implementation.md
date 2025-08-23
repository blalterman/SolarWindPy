# Phase 2: Implementation

**Duration**: 8 hours  
**Status**: Pending  
**Branch**: feature/python-310-migration

## 🎯 Phase Objectives
- Update Python version requirements to 3.10+ minimum
- Reduce CI matrix by 40% (remove Python 3.8/3.9)
- Remove compatibility code for older Python versions
- Modernize type hints and syntax where applicable

## 🔧 Prerequisites
- Phase 1 completed with plan documentation
- Understanding of current compatibility code locations
- CI matrix analysis completed

## 📋 Tasks

### Task 2.1: Feature Branch Creation (15 minutes)
**Deliverable**: Clean feature branch for implementation

#### Steps:
1. Create feature branch from plan branch:
   ```bash
   git checkout plan/python-310-migration
   git checkout -b feature/python-310-migration
   ```

#### Success Criteria:
- [ ] Feature branch created from plan branch
- [ ] Working directory clean
- [ ] Ready for implementation changes

### Task 2.2: Update Project Configuration (2 hours)
**Deliverable**: Updated project metadata and requirements

#### Files to Modify:
1. **`pyproject.toml`**:
   ```toml
   # Update Python requirement
   requires-python = ">=3.10,<4"
   
   # Remove old Python version classifiers
   classifiers = [
       # Remove: "Programming Language :: Python :: 3.8"
       # Remove: "Programming Language :: Python :: 3.9"
       "Programming Language :: Python :: 3.10",
       "Programming Language :: Python :: 3.11", 
       "Programming Language :: Python :: 3.12",
   ]
   ```

2. **`recipe/meta.yaml`** (if exists):
   ```yaml
   # Update conda recipe
   requirements:
     host:
       - python >=3.10
   ```

#### Success Criteria:
- [ ] `requires-python` updated to `>=3.10,<4`
- [ ] Python 3.8/3.9 classifiers removed
- [ ] Conda recipe updated (if applicable)
- [ ] No dependency conflicts introduced

### Task 2.3: Update CI/CD Configuration (1.5 hours)
**Deliverable**: Optimized CI matrix with 40% reduction

#### Files to Modify:
1. **`.github/workflows/ci.yml`**:
   ```yaml
   strategy:
     matrix:
       # Before: ['3.8', '3.9', '3.10', '3.11', '3.12'] = 15 combinations
       # After: ['3.10', '3.11', '3.12'] = 9 combinations (40% reduction)
       python-version: ['3.10', '3.11', '3.12']
   ```

2. **Other workflow files**:
   - Check `.github/workflows/docs.yml`
   - Update any hardcoded Python version references

#### Success Criteria:
- [ ] CI matrix reduced from 15 to 9 combinations
- [ ] All workflow files updated consistently
- [ ] No hardcoded Python version references remain
- [ ] 40% CI resource reduction achieved

### Task 2.4: Remove Compatibility Code (3 hours)
**Deliverable**: Clean codebase without Python < 3.10 compatibility

#### Areas to Address:
1. **`solarwindpy/__init__.py`**:
   ```python
   # Remove importlib_metadata fallback
   # Before:
   # try:
   #     from importlib.metadata import version
   # except ImportError:
   #     from importlib_metadata import version
   
   # After:
   from importlib.metadata import version
   ```

2. **Version checks**:
   - Remove `sys.version_info` checks for Python < 3.10
   - Remove conditional imports based on Python version

3. **Dependencies**:
   - Remove `importlib_metadata` from dependencies if present

#### Search and Replace Operations:
```bash
# Find compatibility code
grep -r "importlib_metadata" solarwindpy/
grep -r "sys.version_info" solarwindpy/
grep -r "version_info.*3\.[89]" solarwindpy/
```

#### Success Criteria:
- [ ] All `importlib_metadata` references removed
- [ ] No `sys.version_info` checks for Python < 3.10
- [ ] Clean import statements
- [ ] No conditional code for unsupported versions

### Task 2.5: Modernize Type Hints (1 hour)
**Deliverable**: Updated type hints using Python 3.10+ syntax

#### Modernization Targets:
1. **Union types**:
   ```python
   # Before: Union[str, int]
   # After: str | int
   ```

2. **Optional types**:
   ```python
   # Before: Optional[str]
   # After: str | None
   ```

#### Approach:
- Focus on commonly used files and public APIs
- Don't modify every file - target high-impact areas
- Ensure changes don't break functionality

#### Success Criteria:
- [ ] Public API type hints modernized
- [ ] Key modules updated with new syntax
- [ ] No functionality regressions
- [ ] Consistent style maintained

### Task 2.6: Update Environment Files (30 minutes)
**Deliverable**: Consistent Python requirements across environments

#### Files to Update:
1. Conda environment files (`*.yml`):
   ```yaml
   dependencies:
     - python>=3.10
   ```

2. Requirements files (if applicable):
   ```
   # Ensure compatibility with Python 3.10+
   ```

#### Success Criteria:
- [ ] All environment files specify Python 3.10+
- [ ] Consistent version requirements
- [ ] No conflicts with existing dependencies

## 🧪 Validation Steps

### Task 2.7: Implementation Validation (45 minutes)
**Deliverable**: Verified changes work correctly

#### Validation Commands:
```bash
# Physics validation (no changes to physics code)
python .claude/hooks/physics-validation.py solarwindpy/**/*.py

# Test runner on changed files
.claude/hooks/test-runner.sh --changed

# Basic import test
python -c "import solarwindpy; print('Import successful')"
```

#### Success Criteria:
- [ ] No physics validation errors
- [ ] Changed files pass basic tests
- [ ] Package imports successfully
- [ ] No obvious regressions

## 📝 Git Commit Strategy

### Single Cohesive Commit:
```bash
git add -A
git commit -m "feat: implement Python 3.10+ minimum support

- Update pyproject.toml requires-python to >=3.10
- Remove Python 3.8/3.9 from CI matrix (40% reduction)  
- Remove importlib_metadata compatibility code
- Modernize type hints to Python 3.10+ syntax
- Update conda recipe and environment files

Breaking change: Python 3.8 and 3.9 no longer supported
Aligns with NumPy 2.x and Astropy 7.x dependency requirements"
```

## 🔄 Compaction Point
After completing Phase 2:
```bash
python .claude/hooks/create-compaction.py --compression high --plan python-310-migration
```

**User Action Required**: Please manually compact the context using `/compact` after Phase 2 completes to preserve session state and reduce token usage before proceeding to Phase 3.

## 🔗 Dependencies
- Phase 1: Planning & Setup (completed)

## 🎯 Acceptance Criteria
- [ ] Feature branch created from plan branch
- [ ] `pyproject.toml` updated with Python 3.10+ requirement
- [ ] CI matrix reduced by 40% (15→9 combinations)
- [ ] All compatibility code removed
- [ ] Type hints modernized in key areas
- [ ] Environment files updated consistently
- [ ] Physics validation passes (no physics changes)
- [ ] Basic import/functionality verified
- [ ] Single cohesive commit with clear message

## 📊 Phase Outputs
1. **Updated Configuration**: pyproject.toml, CI workflows
2. **Clean Codebase**: Compatibility code removed
3. **Modern Syntax**: Python 3.10+ type hints
4. **Consistent Environments**: All files specify 3.10+
5. **Verified Changes**: Validation passes

## 🔄 Next Phase
Upon completion, proceed to **Phase 3: Testing & Validation** for comprehensive testing across all supported Python versions.

## 📝 Notes
- Focus on clean, minimal changes
- No version tagging in this phase
- Maintain all existing functionality
- Document any unexpected issues
- Use physics validation to ensure no scientific code changes

---
*Phase 2 implements the core technical changes for Python 3.10+ migration*