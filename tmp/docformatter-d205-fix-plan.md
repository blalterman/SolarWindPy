# Fix D205 Docstring Errors with docformatter and Black

## Current Status
- 7 D205 errors remain in solarwindpy package (down from original 56)
- CI/CD pipeline blocked due to linting failures
- Need to deploy v0.1.0rc9 to TestPyPI

## Phase 1: Fix Main Package (solarwindpy/)

### Step 1: Install docformatter (2 minutes)
```bash
pip install docformatter
```

### Step 2: Run docformatter with --black option on main package (3 minutes)
```bash
docformatter --in-place --recursive --black solarwindpy/
```

### Step 3: Run Black formatter on main package (2 minutes)
```bash
black solarwindpy/
```

### Step 4: Verify all D205 errors are fixed in main package (1 minute)
```bash
flake8 solarwindpy/ --select=D205
```

### Step 5: Test the full linting suite on main package (1 minute)
```bash
flake8 solarwindpy/
```

### Step 6: Commit changes (NO TAG) (2 minutes)
```bash
git add solarwindpy/
git commit -m "fix: resolve D205 docstring errors with docformatter

- Applied docformatter with --black flag to solarwindpy/
- Ensures PEP 257 compliance with blank lines between summary and description
- Followed by black formatting for consistency
- All D205 errors in main package resolved"
```

## Phase 2: Test docformatter on tests/ and .claude/

### Step 7: Apply docformatter and black to tests/ (3 minutes)
```bash
docformatter --in-place --recursive --black tests/
black tests/
```

### Step 8: Check if tests/ linting issues are resolved (1 minute)
```bash
flake8 tests/ | wc -l  # Count remaining errors
flake8 tests/ | head -20  # Sample errors to see what remains
```

### Step 9: Apply docformatter and black to .claude/ (3 minutes)
```bash
docformatter --in-place --recursive --black .claude/
black .claude/
```

### Step 10: Check if .claude/ linting issues are resolved (1 minute)
```bash
flake8 .claude/ | wc -l  # Count remaining errors
flake8 .claude/ | head -20  # Sample errors to see what remains
```

## Phase 3: Decision Point and Final Steps

### Step 11: Evaluate results and decide on CI workflow (2 minutes)
Based on the results from Steps 8 and 10:

**If tests/ and .claude/ are clean (0 or very few errors):**
- Update `.github/workflows/publish.yml` to change from `flake8 solarwindpy/` back to `flake8` (full project linting)
- Commit with message: "ci: re-enable full project linting after docformatter fixes"

**If tests/ and .claude/ still have many errors:**
- Do NOT change the CI workflow
- Keep it as `flake8 solarwindpy/` (only lint main package)
- Commit any improvements with message: "style: apply docformatter to tests and development files"

### Step 12: Create release candidate tag (1 minute)
```bash
git push origin master
git tag v0.1.0rc9
git push origin v0.1.0rc9
```

## Summary
- **Total time**: ~23 minutes
- **Main goal**: Fix D205 errors in production code to unblock TestPyPI deployment
- **Secondary goal**: Test if docformatter can clean up tests/ and .claude/ directories
- **Decision-based approach**: Only update CI workflow if tests/ and .claude/ become clean
- **Safe approach**: Commit before tagging, allowing for verification

## Expected Outcomes
1. **solarwindpy/**: All D205 errors fixed, ready for deployment
2. **tests/**: Likely partial improvement (may still have F401, F841 unused imports/variables)
3. **.claude/**: Likely clean or nearly clean (mostly formatting issues)
4. **CI/CD**: Will pass and deploy to TestPyPI with v0.1.0rc9 tag

## Execution Log
(To be filled in during execution)

### Phase 1 Results:
- [ ] docformatter installed
- [ ] docformatter applied to solarwindpy/
- [ ] black applied to solarwindpy/
- [ ] D205 errors verified fixed
- [ ] Full linting passed
- [ ] Changes committed

### Phase 2 Results:
- [ ] tests/ formatted - Errors before: ___ Errors after: ___
- [ ] .claude/ formatted - Errors before: ___ Errors after: ___

### Phase 3 Results:
- [ ] CI workflow decision: ___
- [ ] Final commit pushed
- [ ] v0.1.0rc9 tag created and pushed