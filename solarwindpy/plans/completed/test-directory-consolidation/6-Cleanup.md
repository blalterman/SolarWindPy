# Phase 6: Cleanup

## Phase Tasks
- [ ] **Remove old test directories** (Est: 10 min) - Clean up empty /solarwindpy/tests/ directory structure
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Update documentation references** (Est: 15 min) - Fix any documentation pointing to old test locations
  - Commit: `<checksum>`
  - Status: Pending
- [ ] **Final consolidation verification** (Est: 5 min) - Confirm complete migration and no orphaned files
  - Commit: `<checksum>`
  - Status: Pending

## Cleanup Operations

### Step 1: Remove Old Directory Structure
```bash
# Remove empty test directories (after confirming they're empty)
rmdir solarwindpy/tests/plotting/labels/
rmdir solarwindpy/tests/plotting/
rmdir solarwindpy/tests/data/
rmdir solarwindpy/tests/

# Remove any remaining test-related files in package
find solarwindpy/ -name "*test*" -type f
find solarwindpy/ -name "conftest.py" -type f
```

**Verification:**
- [ ] All test files successfully migrated
- [ ] No orphaned test files remain in package
- [ ] Directory structure completely removed
- [ ] Package structure is clean

### Step 2: Update Documentation References

#### Files to Check and Update:
1. **README.rst** - Update test running instructions
2. **CONTRIBUTING.md** - Update development setup instructions  
3. **docs/source/** - Update any testing documentation
4. **pyproject.toml** - Verify test discovery configuration
5. **setup.cfg** - Update pytest configuration if needed

#### Documentation Updates:

**Before:**
```markdown
Run tests: pytest solarwindpy/tests/
Test location: /solarwindpy/tests/
```

**After:**
```markdown
Run tests: pytest tests/ (or simply pytest -q)
Test location: /tests/
```

### Step 3: Configuration File Updates

#### pyproject.toml Testing Configuration
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
addopts = "--strict-markers --disable-warnings"
```

#### GitHub Actions Workflow
Verify `.github/workflows/` files use:
```yaml
- name: Run tests
  run: pytest -q
```
(Should already work with standard discovery)

### Step 4: Package Configuration Cleanup

#### setup.py / pyproject.toml
Ensure test files are properly excluded from package distribution:
```python
# In setup.py
packages=find_packages(exclude=["tests", "tests.*"])

# Or in pyproject.toml
[tool.setuptools.packages.find]
exclude = ["tests*"]
```

### Step 5: Final Verification

#### Complete Migration Checklist
- [ ] All 33 test files successfully migrated to /tests/
- [ ] No test files remain in /solarwindpy/
- [ ] Documentation updated with new test locations
- [ ] Configuration files reflect new structure
- [ ] CI/CD pipelines work with new structure
- [ ] Package distribution excludes test files

#### File Count Verification
```bash
# Count tests in new location
find tests/ -name "test_*.py" | wc -l
# Expected: 33 total test files

# Verify no tests remain in package
find solarwindpy/ -name "test_*.py" | wc -l  
# Expected: 0 test files
```

#### Final Test Run
```bash
# Complete test suite in new location
pytest -q
# Expected: All tests pass, ~170+ test cases

# Verify test discovery
pytest --collect-only | grep "test session starts"
# Expected: All tests discovered from /tests/
```

## Documentation Updates Summary

### Files Updated:
1. **README.rst**: Test running instructions
2. **CONTRIBUTING.md**: Development setup guidance
3. **docs/source/**: Any testing documentation
4. **pyproject.toml**: Test configuration (if needed)

### Key Changes:
- Test location: `/solarwindpy/tests/` → `/tests/`  
- Test commands: `pytest solarwindpy/tests/` → `pytest -q`
- Development setup: Updated directory references

## Success Criteria
- [ ] Complete directory cleanup with no orphaned files
- [ ] All documentation references updated
- [ ] Configuration files reflect new structure  
- [ ] Package properly excludes test files from distribution
- [ ] Final test suite passes completely
- [ ] CI/CD pipeline functions with new structure

## Post-Completion Benefits Achieved
✅ **Industry Standard Compliance**: Python packaging best practices implemented  
✅ **Clean Package Distribution**: Tests excluded from installations  
✅ **Superior Tooling Integration**: Standard pytest discovery working  
✅ **Clear Architecture**: Clean separation between source and tests  
✅ **CI/CD Compatibility**: Existing workflows maintained  
✅ **Reduced Package Size**: Test files no longer included in distributions

## Navigation
- **Previous Phase**: [5-Validation.md](./5-Validation.md)
- **Overview**: [0-Overview.md](./0-Overview.md)

---
**Plan Status**: Ready for systematic implementation with rollback capabilities