# Phase 2: Configuration Setup

## Objective
Create robust doc8 configuration to standardize documentation formatting rules and prevent future linting failures.

## Rationale

### Why Configuration Matters
- **Consistency**: Uniform rules across all documentation
- **Clarity**: Explicit standards for contributors
- **Flexibility**: Customizable for project needs
- **Prevention**: Catches issues before they reach CI/CD

### Current State
- No `.doc8` configuration file exists
- Using doc8 defaults which may be too strict
- No documentation of formatting standards
- Inconsistent application of rules

## Configuration Design

### 2.1 Create `.doc8` Configuration File

**File location**: `/.doc8` (repository root)

**Recommended configuration**:
```ini
[doc8]
# Maximum line length for RST files
max-line-length = 100

# File encoding
file-encoding = utf-8

# Ignore certain error codes if needed
# D000 - Generic error (usually parsing issues)
# D001 - Line too long (controlled by max-line-length)
ignore = D000

# Paths to ignore during checking
# These are auto-generated or third-party files
ignore-path = docs/build,docs/source/api,docs/_build,.tox,venv

# File extensions to check
extensions = .rst,.txt

# Allow long lines in specific cases
# This helps with tables and URLs that can't be broken
allow-long-titles = true

# Ignore files matching these patterns
ignore-path-errors = docs/source/solarwindpy.solar_activity.tests.rst;D001
```

### 2.2 Alternative: Setup.cfg Configuration

If preferring `setup.cfg` over `.doc8`:

**Addition to `/setup.cfg`**:
```ini
[doc8]
max-line-length = 100
file-encoding = utf-8
ignore = D000
ignore-path = docs/build,docs/source/api,docs/_build,.tox,venv
extensions = .rst,.txt
```

### 2.3 Configuration Options Explained

| Option | Value | Justification |
|--------|-------|---------------|
| `max-line-length` | 100 | Balance between readability and flexibility for documentation |
| `file-encoding` | utf-8 | Standard encoding, prevents character issues |
| `ignore` | D000 | Skip generic parsing errors that may not be real issues |
| `ignore-path` | build dirs, api | Skip auto-generated and build artifacts |
| `extensions` | .rst,.txt | Focus on documentation files only |
| `allow-long-titles` | true | Titles/headers often need to be longer |

## Implementation Steps

### Step 2.1: Create Configuration File (3 minutes)

**Create `.doc8` file**:
```bash
cat > .doc8 << 'EOF'
[doc8]
# SolarWindPy Documentation Linting Configuration
# This file configures doc8 to check RST documentation formatting

# Maximum line length for RST files
# We use 100 as it's reasonable for documentation while fitting most screens
max-line-length = 100

# File encoding (utf-8 is standard)
file-encoding = utf-8

# Ignore certain error codes
# D000 - Generic error (often false positives)
ignore = D000

# Paths to ignore during checking
# docs/build - Sphinx build output
# docs/source/api - Auto-generated API documentation
# docs/_build - Alternative build directory
# .tox, venv - Virtual environments
ignore-path = docs/build,docs/source/api,docs/_build,.tox,venv

# File extensions to check
extensions = .rst,.txt

# Allow long titles (headers often need to be descriptive)
allow-long-titles = true

# Specific file error ignores (path;error_code)
# For files that have unavoidable issues
ignore-path-errors = docs/source/solarwindpy.solar_activity.tests.rst;D001
EOF
```

### Step 2.2: Update .gitignore (1 minute)

**Ensure `.doc8` is tracked**:
```bash
# Check if .doc8 is ignored
grep -q "^\.doc8$" .gitignore && echo ".doc8 is ignored" || echo ".doc8 will be tracked"

# If ignored, remove from .gitignore
sed -i '/^\.doc8$/d' .gitignore
```

### Step 2.3: Test Configuration (2 minutes)

**Validation commands**:
```bash
# Test with new configuration
doc8 --config .doc8 docs

# Test specific problem files
doc8 --config .doc8 docs/source/index.rst
doc8 --config .doc8 docs/source/_templates/

# Verbose output for debugging
doc8 --config .doc8 --verbose docs
```

**Expected output**:
```
Scanning...
docs/source/index.rst
docs/source/api_reference.rst
...
Total files scanned = 12
Total accumulated errors = 0
```

### Step 2.4: Document Configuration (2 minutes)

**Create `docs/FORMATTING.md`**:
```markdown
# Documentation Formatting Standards

This project uses `doc8` to enforce consistent RST documentation formatting.

## Configuration

See `.doc8` for the complete configuration. Key rules:

- **Line length**: Maximum 100 characters
- **File encoding**: UTF-8
- **Newlines**: Files must end with a newline
- **Whitespace**: No trailing whitespace
- **Extensions**: Checks .rst and .txt files

## Running Locally

```bash
# Install doc8
pip install doc8

# Check all documentation
doc8 docs

# Check specific file
doc8 docs/source/index.rst
```

## Common Issues and Fixes

### Line too long (D001)
Break long lines at natural points (commas, operators).

### No newline at end of file (D005)
Add a blank line at the end of the file.

### Trailing whitespace (D002)
Remove spaces at the end of lines.

## Exceptions

Auto-generated files in `docs/source/api/` are excluded from checking.
```

### Step 2.5: Integration with CI/CD (2 minutes)

**Update workflow to use configuration**:

In `.github/workflows/docs.yml`, update line 41:
```yaml
- name: Lint documentation with doc8
  run: |
    # Use project configuration
    doc8 --config .doc8 README.rst docs CITATION.rst
```

## Validation Checklist

### Configuration Testing
- [ ] `.doc8` file created and valid
- [ ] Configuration parses without errors
- [ ] doc8 runs successfully with config
- [ ] Appropriate files are checked
- [ ] Appropriate files are ignored

### Rule Validation
- [ ] Line length limit is appropriate (100 chars)
- [ ] Build directories are excluded
- [ ] Auto-generated API docs are excluded
- [ ] File encoding is correct

### Documentation
- [ ] Configuration is documented
- [ ] Team is aware of standards
- [ ] Local testing instructions provided

## Success Metrics

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Configuration files | 0 | 1 | ✅ |
| Documented standards | No | Yes | ✅ |
| Consistent rules | No | Yes | ✅ |
| False positives | High | Low | ✅ |
| Developer clarity | Low | High | ✅ |

## Rollback Plan

If configuration causes issues:

```bash
# Remove configuration file
rm .doc8

# Or rename to disable
mv .doc8 .doc8.disabled

# Revert workflow changes
git checkout -- .github/workflows/docs.yml
```

## Configuration Maintenance

### Regular Reviews (Quarterly)
- Review error patterns
- Adjust line length if needed
- Update ignore patterns
- Document exceptions

### When to Update Configuration
- New documentation structure added
- Team feedback on rules
- Tool updates with new checks
- False positive patterns identified

## Expected Outcomes

### Immediate
- ✅ Consistent linting rules applied
- ✅ Fewer false positives
- ✅ Clear standards for contributors

### Long-term
- ✅ Reduced formatting issues
- ✅ Faster PR reviews
- ✅ Better documentation quality
- ✅ Less time spent on formatting

## Next Steps

1. Implement configuration file
2. Test with current documentation
3. Update CI/CD to use configuration
4. Document standards for team
5. Proceed to Phase 3 (Pre-commit hooks)

---

*This phase establishes the foundation for consistent documentation formatting standards.*