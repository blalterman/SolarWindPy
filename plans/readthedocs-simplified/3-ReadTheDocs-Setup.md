# Phase 3: ReadTheDocs Setup

## Phase Metadata
- **Phase**: 3/4
- **Estimated Duration**: 40 minutes
- **Dependencies**: Phase 1 (clean builds), Phase 2 (working templates)
- **Status**: Not Started

## 🎯 Phase Objective
Configure minimal ReadTheDocs integration to deploy SolarWindPy documentation online with standard HTML output. Focus on working deployment quickly rather than advanced features.

## 🧠 Phase Context

### ReadTheDocs Integration Strategy
- **Minimal configuration**: Use standard, proven patterns
- **HTML output only**: Skip PDF/EPUB for simplicity
- **Manual setup**: Avoid complex webhook automation initially
- **Standard theme**: Use sphinx_rtd_theme (ReadTheDocs default)

### What We're NOT Building
- ❌ **Multiple output formats** (PDF/EPUB) - HTML sufficient
- ❌ **Complex build hooks** - Standard Python package build
- ❌ **Advanced webhook integration** - Manual deployment acceptable
- ❌ **Custom styling** - Default theme works fine

## 📋 Implementation Tasks

### Task 3.1: ReadTheDocs Configuration File (15 minutes)

**Create minimal `.readthedocs.yaml`**:

**Target**: `.readthedocs.yaml` (repository root)

```yaml
version: 2

build:
  os: ubuntu-22.04
  tools:
    python: "3.11"

python:
  install:
    - requirements: requirements.txt
    - requirements: docs/requirements.txt
    - method: pip
      path: .

sphinx:
  configuration: docs/source/conf.py
  builder: html
```

**Configuration rationale**:
- **Ubuntu 22.04**: Latest stable ReadTheDocs environment
- **Python 3.11**: Modern Python version with good package compatibility
- **requirements.txt**: Standard package dependencies
- **docs/requirements.txt**: Documentation-specific dependencies
- **HTML builder only**: Simplest, most reliable output format

### Task 3.2: Documentation Requirements File (5 minutes)

**Check if `docs/requirements.txt` exists**:
```bash
ls -la docs/requirements.txt
```

**If missing, create `docs/requirements.txt`**:
```txt
sphinx>=4.0
sphinx-rtd-theme
```

**If exists, verify contents include**:
- sphinx (version 4.0 or higher)
- sphinx-rtd-theme
- Any other documentation dependencies

**Validate requirements**:
```bash
pip install -r docs/requirements.txt
```

### Task 3.3: Sphinx Configuration for ReadTheDocs (10 minutes)

**Check current `docs/source/conf.py` for ReadTheDocs compatibility**:

**Add ReadTheDocs detection (if not present)**:
```python
import os

# ReadTheDocs environment detection
on_rtd = os.environ.get('READTHEDOCS') == 'True'

if on_rtd:
    # ReadTheDocs-specific settings
    html_theme = 'sphinx_rtd_theme'
else:
    # Local development (use same theme for consistency)
    html_theme = 'sphinx_rtd_theme'
```

**Verify essential configuration**:
```python
# Ensure these settings exist
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',  # If using NumPy/Google docstrings
]

autosummary_generate = True
```

**Test configuration locally**:
```bash
cd docs
make clean
make html
# Should build successfully with sphinx_rtd_theme
```

### Task 3.4: Manual ReadTheDocs Project Setup (10 minutes)

**ReadTheDocs account setup steps**:

1. **Access ReadTheDocs**:
   - Go to https://readthedocs.org/dashboard/import/
   - Sign in with GitHub account

2. **Import repository**:
   - Select SolarWindPy repository from GitHub
   - Use repository URL: https://github.com/space-physics/solarwindpy
   - Or appropriate repository URL

3. **Project configuration**:
   ```
   Project name: solarwindpy
   Project slug: solarwindpy
   Repository URL: [GitHub URL]
   Default branch: master
   Language: English
   Programming language: Python
   ```

4. **Build settings**:
   ```
   Configuration file: .readthedocs.yaml
   Documentation type: Sphinx Html
   Python version: 3.11
   ```

5. **Advanced settings**:
   ```
   Install project: Yes
   Requirements file: requirements.txt
   Python interpreter: CPython 3.11
   ```

**Manual verification needed** (cannot be automated):
- ReadTheDocs account access required
- GitHub repository permissions
- Manual configuration through web interface

## ✅ Phase Acceptance Criteria

### Configuration Files
- [ ] `.readthedocs.yaml` created with minimal, working configuration
- [ ] `docs/requirements.txt` exists with necessary dependencies
- [ ] `docs/source/conf.py` compatible with ReadTheDocs environment
- [ ] Local build succeeds with ReadTheDocs-compatible settings

### ReadTheDocs Integration
- [ ] ReadTheDocs project created and configured
- [ ] Repository successfully imported
- [ ] Initial build triggered and monitored
- [ ] HTML documentation accessible online

### Build Verification
- [ ] ReadTheDocs build completes without critical errors
- [ ] Generated documentation displays correctly
- [ ] Navigation and search functionality working
- [ ] API documentation appears in online version

## 🧪 Phase Testing Strategy

### Local ReadTheDocs Simulation
1. **Environment test**: Use Python 3.11 in clean environment
2. **Dependency test**: Install from requirements.txt only
3. **Build test**: Generate documentation with sphinx_rtd_theme
4. **Output verification**: Check HTML output matches expectations

### ReadTheDocs Platform Testing
1. **Manual build trigger**: Initiate first build through web interface
2. **Build log review**: Check for errors or warnings in ReadTheDocs logs
3. **Output verification**: Access generated documentation URL
4. **Navigation test**: Verify all sections accessible

## 📊 Expected Results

### Local Build Performance
- **Build time**: < 5 minutes for complete documentation
- **Output quality**: Professional appearance with sphinx_rtd_theme
- **Error rate**: Zero critical errors, minimal warnings
- **Functionality**: All links and navigation working

### ReadTheDocs Deployment
- **Deployment URL**: https://solarwindpy.readthedocs.io/
- **Update mechanism**: Manual builds initially (webhook setup optional)
- **Build success rate**: 100% for basic HTML generation
- **Documentation freshness**: Updated when manually triggered

## 🔗 Phase Dependencies

### Requires from Previous Phases
- **Phase 1**: Clean doc8 validation (no linting blocking builds)
- **Phase 2**: Working template system (API documentation generation)

### Provides for Phase 4
- **ReadTheDocs project**: Configured and accessible
- **Build baseline**: Known working configuration
- **Deployment target**: URL for testing and validation

## ⚠️ Risk Assessment

### Configuration Risks
- **Dependency conflicts**: requirements.txt incompatibility
- **Sphinx version issues**: Newer/older versions causing problems
- **Theme compatibility**: sphinx_rtd_theme integration issues

### Platform Risks
- **ReadTheDocs account access**: May require permissions setup
- **Repository permissions**: GitHub integration configuration
- **Build environment**: ReadTheDocs platform changes

### Mitigation Strategies
- **Test locally first**: Verify configuration works before ReadTheDocs
- **Standard dependencies**: Use well-established package versions
- **Incremental debugging**: Address one issue at a time

## 💬 Implementation Notes

### Minimal Configuration Philosophy
1. **Use defaults where possible**: ReadTheDocs has good standard settings
2. **Avoid premature optimization**: Advanced features can be added later
3. **Focus on reliability**: Working deployment is priority #1
4. **Document assumptions**: Make configuration decisions explicit

### ReadTheDocs Platform Notes
- **Build time limits**: Free accounts have build time restrictions
- **Concurrent builds**: May queue behind other projects
- **Environment consistency**: ReadTheDocs controls build environment
- **Debugging access**: Build logs available through web interface

### Future Enhancement Path
If advanced features are needed later:
1. **PDF/EPUB output**: Add to .readthedocs.yaml formats section
2. **Webhook automation**: Configure GitHub integration
3. **Custom domain**: Set up custom documentation URL
4. **Build optimization**: Add caching and dependency optimization

---

## Phase Completion

### Commit Message
```
feat: add basic ReadTheDocs configuration

- Create minimal .readthedocs.yaml for HTML documentation
- Ensure docs/requirements.txt includes necessary dependencies
- Configure Sphinx for ReadTheDocs compatibility
- Document manual ReadTheDocs project setup process

Phase 3 of readthedocs-simplified plan: ReadTheDocs deployment ready
```

### Success Verification
- [ ] `.readthedocs.yaml` committed to repository root
- [ ] `docs/requirements.txt` contains sphinx and sphinx_rtd_theme
- [ ] Local documentation builds with ReadTheDocs-compatible settings
- [ ] ReadTheDocs project configured and first build attempted
- [ ] Documentation accessible at readthedocs.io URL
- [ ] Ready to proceed to Phase 4 (Testing & Validation)

### Manual Setup Documentation
**Record ReadTheDocs project details for reference**:
```
Project URL: https://readthedocs.org/projects/solarwindpy/
Documentation URL: https://solarwindpy.readthedocs.io/
Build status: [Record first build result]
Configuration: Using .readthedocs.yaml from repository
```

---

*Phase 3 Priority: Get working documentation online with minimal configuration complexity*