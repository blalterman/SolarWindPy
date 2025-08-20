# Coverage Monitor Fix Implementation Plan

## Overview
Fix the "⏺ Stop [.claude/hooks/coverage-monitor.py] failed with non-blocking status code 1" error by properly managing pytest-cov dependency and making the hook resilient.

## Problem Analysis
- **Root Cause**: pytest-cov is used in CI/CD but not declared in local dev requirements
- **Impact**: Hook fails silently when pytest-cov is missing
- **Frequency**: Every session stop event
- **Severity**: Low (non-blocking) but confusing to users

## Solution Strategy
1. **Add pytest-cov to requirements** - Make dependency explicit
2. **Make hook resilient** - Gracefully handle missing pytest-cov
3. **Update documentation** - Clear testing requirements
4. **Maintain backward compatibility** - No breaking changes

## Implementation Plan

### Phase 1: Requirements File Updates (20 minutes)

#### Step 1.1: Update requirements-dev.txt
**File**: `/Users/balterma/observatories/code/SolarWindPy/requirements-dev.txt`
**Change**: Add `pytest-cov>=4.1.0` after line 12 (pytest)

**Before:**
```
pytest
black
```

**After:**
```
pytest
pytest-cov>=4.1.0
black
```

**Rationale**: This is the canonical source for development dependencies that CI/CD already uses.

#### Step 1.2: Update Conda Environment Files
**Files**: 
- `solarwindpy-dev-20250729.yml`
- `solarwindpy-dev-20250729b.yml`

**Change**: Add `- pytest-cov` to dependencies list

**Rationale**: Ensure conda users get the same dependencies as pip users.

#### Step 1.3: Update pyproject.toml (Optional Enhancement)
**File**: `/Users/balterma/observatories/code/SolarWindPy/pyproject.toml`
**Change**: Add optional-dependencies section

**Addition:**
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.4",
    "pytest-cov>=4.1.0", 
    "black",
    "flake8",
    "doc8",
    "flake8-docstrings",
    "pydocstyle",
    "numpydoc",
]
test = [
    "pytest>=7.4.4",
    "pytest-cov>=4.1.0",
]
```

**Benefit**: Modern Python packaging, enables `pip install solarwindpy[dev]`

### Phase 2: Fix Coverage Monitor Hook (15 minutes)

#### Step 2.1: Make pytest-cov Optional in Hook
**File**: `/Users/balterma/observatories/code/SolarWindPy/.claude/hooks/coverage-monitor.py`

**Changes to `run_coverage_analysis()` function (lines 13-40):**

```python
def run_coverage_analysis():
    """Run coverage analysis and return results."""
    
    print("📊 Running comprehensive coverage analysis...")
    
    # Check if pytest-cov is available
    try:
        import pytest_cov
        use_coverage = True
    except ImportError:
        print("⚠️  pytest-cov not installed. Running tests without coverage.")
        print("   Install with: pip install pytest-cov")
        use_coverage = False
    
    try:
        if use_coverage:
            # Run pytest with coverage
            result = subprocess.run([
                "pytest", 
                "--cov=solarwindpy", 
                "--cov-report=json",
                "--cov-report=term-missing",
                "-q"
            ], capture_output=True, text=True, timeout=60)
        else:
            # Run pytest without coverage
            result = subprocess.run([
                "pytest", "-q"
            ], capture_output=True, text=True, timeout=60)
            print("ℹ️  Tests completed without coverage analysis")
            return True  # Don't fail if pytest-cov missing
        
        if result.returncode != 0:
            print(f"⚠️  Some tests failed during coverage analysis:")
            print(result.stdout)
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏱️  Coverage analysis timed out (>60s)")
        return False
    except FileNotFoundError:
        print("❌ pytest not found. Install with: pip install pytest", file=sys.stderr)
        return False
```

#### Step 2.2: Fix Main Function Error Handling
**Changes to `main()` function (lines 178-202):**

```python
def main():
    """Main entry point for coverage monitoring."""
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Quick mode: just run basic coverage
        success = run_coverage_analysis()
        sys.exit(0 if success else 1)
    
    # Full analysis mode
    print("🔍 Starting comprehensive coverage monitoring...")
    
    # Run coverage analysis
    success = run_coverage_analysis()
    
    if success:
        # Only run detailed analysis if we have coverage data
        try:
            import pytest_cov
            # Detailed analysis
            analyze_coverage_by_module()
            check_critical_coverage()
        except ImportError:
            print("ℹ️  Skipping detailed coverage analysis (pytest-cov not available)")
        
        print("\n✅ Coverage monitoring completed")
        print("💡 Use 'pytest --cov=solarwindpy --cov-report=html' for interactive report")
        sys.exit(0)  # Always exit 0 for non-blocking hook
    else:
        print("\n❌ Test execution failed")
        print("💡 Fix test failures before analyzing coverage")
        sys.exit(1)  # Exit 1 only for actual test failures
```

#### Step 2.3: Add sys Import
**Add at top of file after existing imports:**
```python
import sys
```

### Phase 3: Documentation Updates (10 minutes)

#### Step 3.1: Update CLAUDE.md
**File**: `/Users/balterma/observatories/code/SolarWindPy/CLAUDE.md`
**Section**: Add to environment setup section

**Addition:**
```markdown
### Testing Requirements
- **pytest >= 7.4.4** (required for running tests)
- **pytest-cov >= 4.1.0** (recommended for coverage analysis)
- **pytest-xdist** (optional for parallel testing)

Install all testing dependencies:
```bash
# Using pip
pip install -r requirements-dev.txt

# Using conda
conda env update -f solarwindpy-dev-20250729.yml

# Using pyproject.toml (modern approach)
pip install -e .[dev]
```

### Running Tests with Coverage
```bash
# Basic tests (no coverage)
pytest

# Tests with coverage
pytest --cov=solarwindpy

# Tests with HTML coverage report
pytest --cov=solarwindpy --cov-report=html
open htmlcov/index.html

# Hook testing
python .claude/hooks/coverage-monitor.py --quick
```
```

### Phase 4: Installation and Verification (5 minutes)

#### Step 4.1: Install pytest-cov
```bash
pip install pytest-cov>=4.1.0
```

#### Step 4.2: Verify Hook Works
```bash
# Test the hook directly
python .claude/hooks/coverage-monitor.py --quick

# Check exit code
echo $?  # Should be 0

# Test without pytest-cov (simulate missing dependency)
python -c "import sys; sys.modules['pytest_cov'] = None; exec(open('.claude/hooks/coverage-monitor.py').read())"
```

#### Step 4.3: Test Requirements Installation
```bash
# Test pip installation
pip install -r requirements-dev.txt

# Test conda environment (if available)
conda env update -f solarwindpy-dev-20250729.yml

# Verify pytest-cov is available
python -c "import pytest_cov; print('pytest-cov available')"
```

## Success Criteria
- [ ] pytest-cov listed in requirements-dev.txt
- [ ] Conda dev environments include pytest-cov
- [ ] Coverage monitor hook doesn't fail when pytest-cov missing
- [ ] Coverage analysis works when pytest-cov installed  
- [ ] Documentation updated with testing requirements
- [ ] CI/CD continues to work unchanged
- [ ] No breaking changes for existing workflows

## Risk Mitigation
- **Backward Compatibility**: Hook works with or without pytest-cov
- **Multiple Installers**: Support pip, conda, and pyproject.toml
- **Clear Documentation**: Users know what's required vs optional
- **Graceful Degradation**: Tests still run without coverage
- **Non-breaking**: All existing pytest commands continue to work

## Testing Strategy
1. **Before Changes**: Reproduce the error by running hook without pytest-cov
2. **After Changes**: Verify hook runs successfully both with and without pytest-cov
3. **Integration**: Test that coverage analysis works when pytest-cov is available
4. **Regression**: Ensure existing test workflows are unchanged

## Rollback Plan
If issues arise:
1. Remove pytest-cov from requirements-dev.txt
2. Revert coverage-monitor.py changes
3. Remove optional-dependencies from pyproject.toml
4. Update documentation to reflect pytest-cov as optional

## Complexity Analysis
- **Code Changes**: ~30 lines modified/added
- **Dependencies Added**: 1 primary (pytest-cov) + 1 transitive (coverage.py)
- **Size Impact**: +0.5MB (~0.13% of environment)
- **Maintenance Overhead**: Minimal (mature, stable tools)
- **User Impact**: Positive (eliminates confusing errors)

## Expected Outcomes
1. **Immediate**: No more "coverage-monitor.py failed" error messages
2. **Short-term**: Consistent development environment between local and CI
3. **Long-term**: Better test coverage visibility for scientific code quality

---
*Implementation Date: 2025-08-16*
*Estimated Duration: 50 minutes*
*Risk Level: Low*
*Impact: High (eliminates user confusion, enables quality metrics)*