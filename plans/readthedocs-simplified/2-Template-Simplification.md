# Phase 2: Template Simplification

## Phase Metadata
- **Phase**: 2/4
- **Estimated Duration**: 30 minutes
- **Dependencies**: Phase 1 (clean doc8 validation)
- **Status**: Not Started

## 🎯 Phase Objective
Preserve the essential template infrastructure for API documentation persistence while removing unnecessary complexity. Maintain the **only mechanism** for customizing ephemeral API documentation files.

## 🧠 Phase Context

### Why Templates Are Essential (Not Optional)
The documentation build process works as follows:
1. `sphinx-apidoc` generates RST files in `docs/source/api/` 
2. These files are **ephemeral** (destroyed on every build)
3. These files are **git-ignored** (line 75 in `.gitignore`)
4. Templates provide the **only way** to customize these generated files

**Without templates**: 100% of API documentation customizations are lost on every build.

### Current Template Infrastructure
```
docs/source/_templates/autosummary/
├── module.rst      # Template for module-level documentation
└── class.rst       # Template for class-level documentation
```

**Post-processing**: `docs/add_no_index.py` adds `:no-index:` directives after generation.

## 📋 Implementation Tasks

### Task 2.1: Template Infrastructure Audit (5 minutes)

**Examine current template system**:
```bash
cd docs/source/_templates/autosummary/
ls -la
cat module.rst
cat class.rst
```

**Document current capabilities**:
- Template syntax and variables available
- Post-processing workflow integration
- Sphinx configuration dependencies

**Check build integration**:
```bash
cd docs
grep -r "autosummary" source/conf.py
grep -r "_templates" source/conf.py
```

### Task 2.2: Review Current Templates (10 minutes)

**Analyze module.rst template**:
```bash
cd docs/source/_templates/autosummary/
cat module.rst
```

**Current content** (as of audit):
```rst
{{ fullname | escape | underline}}

.. automodule:: {{ fullname }}
   :members:
   :show-inheritance:
   :undoc-members:
   :no-index:
```

**Assess complexity level**:
- ✅ **Simple, standard format** - Good baseline
- ✅ **Essential directives present** - Maintains functionality
- ✅ **No over-engineering** - Already simplified

**Analyze class.rst template**:
```bash
cat class.rst
```

**Document any complexity** that should be simplified.

### Task 2.3: Template Enhancement Strategy (10 minutes)

**Keep Essential Elements**:
1. **Basic template structure** - Required for persistence
2. **Standard Sphinx directives** - `:members:`, `:show-inheritance:`
3. **Post-processing compatibility** - `:no-index:` directive support

**Remove/Avoid Complex Elements**:
1. **Physics-specific sections** - Defer to future enhancement
2. **Conditional logic** - Keep templates simple
3. **Advanced formatting** - Standard autosummary sufficient
4. **Custom validation** - Rely on Sphinx warnings

**Document Template Usage**:
Create `docs/template-usage.md` with:
- How to customize API documentation
- Template file locations and purpose
- Build process integration
- When to edit templates vs docstrings

### Task 2.4: Post-Processing Validation (3 minutes)

**Verify post-processing workflow**:
```bash
cd docs
cat add_no_index.py
```

**Test post-processing script**:
```bash
# Generate API docs
make api

# Check that :no-index: is added
grep -r "no-index" source/api/ | head -5
```

**Ensure integration works**:
- Post-processing runs after template application
- `:no-index:` directives added correctly
- No conflicts with template customizations

### Task 2.5: Template Documentation (2 minutes)

**Create template usage guide**:

**Target**: `docs/template-usage.md`

```markdown
# Template Usage Guide

## Overview
Templates in `docs/source/_templates/autosummary/` control the format of auto-generated API documentation.

## Why Templates Matter
- API files in `docs/source/api/` are ephemeral (regenerated on every build)
- Templates provide the ONLY way to customize API documentation
- Changes to templates persist across rebuilds

## Template Files
- `module.rst` - Controls module-level documentation format
- `class.rst` - Controls class-level documentation format

## Editing Process
1. Edit template files in `docs/source/_templates/autosummary/`
2. Run `make api` to regenerate API documentation
3. Run `make html` to build full documentation
4. Verify changes appear in generated documentation

## Build Process
1. `sphinx-apidoc` generates RST files using templates
2. `add_no_index.py` post-processes files (adds :no-index:)
3. Sphinx builds final HTML documentation

## Important Notes
- NEVER edit files in `docs/source/api/` directly (they're regenerated)
- All API customizations must go in templates
- Templates use Jinja2 syntax with Sphinx variables
```

## ✅ Phase Acceptance Criteria

### Template Infrastructure
- [ ] Existing templates preserved and functional
- [ ] Template complexity remains minimal (no physics enhancements)
- [ ] Post-processing integration working correctly
- [ ] Template usage clearly documented

### Build Process
- [ ] `make api` generates API documentation using templates
- [ ] `make html` builds complete documentation successfully
- [ ] Post-processing adds `:no-index:` directives correctly
- [ ] No template-related Sphinx warnings

### Documentation Quality
- [ ] Generated API documentation maintains professional quality
- [ ] All modules and classes properly documented
- [ ] Navigation and cross-references working
- [ ] Consistent formatting across all API documentation

## 🧪 Phase Testing Strategy

### Template Persistence Test
1. **Make template customization**: Add comment to module.rst
2. **Regenerate documentation**: Run `make api && make html`
3. **Verify persistence**: Confirm customization appears in generated docs
4. **Repeat build**: Verify customization survives multiple rebuilds

### Build Integration Test
1. **Clean build**: `make clean && make api && make html`
2. **Check for errors**: No template-related warnings
3. **Verify output**: All API modules properly documented
4. **Post-processing check**: `:no-index:` directives present

## 📊 Expected Results

### Template System Status
- **Complexity**: Minimal (basic templates only)
- **Functionality**: Full persistence capability preserved
- **Maintainability**: Simple, standard patterns
- **Documentation**: Clear usage guidelines

### Build Performance
- **Generation time**: Fast (no complex template processing)
- **Error rate**: Low (simple templates, fewer failure points)
- **Output quality**: Professional, consistent formatting

## 🔗 Phase Dependencies

### Requires from Phase 1
- **Clean doc8 validation**: No linting errors blocking builds
- **Working documentation build**: `make html` succeeds

### Provides for Phase 3
- **Stable template system**: ReadTheDocs can use templates reliably
- **Documented process**: Clear understanding of customization workflow
- **Baseline functionality**: API documentation generation working

## ⚠️ Risk Assessment

### Low Risk Elements
- **Template preservation**: Existing system already works
- **Minimal changes**: Avoiding complex modifications
- **Standard patterns**: Using established Sphinx/autosummary features

### Risk Mitigation
- **Incremental testing**: Test each template change individually
- **Backup current templates**: Save originals before any modifications
- **Document all changes**: Clear record of modifications made

## 💬 Implementation Notes

### Simplification Philosophy
1. **Preserve core functionality**: Templates must enable persistence
2. **Avoid premature optimization**: Physics enhancements can wait
3. **Standard patterns**: Use established Sphinx conventions
4. **Clear documentation**: Enable future developers to understand system

### Template Enhancement Path
If physics-specific documentation is needed later:
1. **Incremental addition**: Add features one at a time
2. **Conditional logic**: Use template conditionals for module-specific content
3. **Testing framework**: Validate enhancements don't break builds
4. **Separate plan**: Major enhancements deserve their own implementation plan

---

## Phase Completion

### Commit Message
```
refactor: simplify documentation templates for maintainability

- Preserve essential template infrastructure for API doc persistence
- Document template usage and customization process
- Maintain post-processing integration (add_no_index.py)
- Remove complex enhancements to focus on core functionality

Phase 2 of readthedocs-simplified plan: Template system simplified
```

### Success Verification
- [ ] Templates generate API documentation correctly
- [ ] Post-processing adds `:no-index:` directives
- [ ] Template customizations persist across rebuilds
- [ ] Documentation build completes without template errors
- [ ] Template usage guide created and accurate
- [ ] Ready to proceed to Phase 3 (ReadTheDocs Setup)

---

*Phase 2 Priority: Maintain essential template persistence while keeping complexity minimal*