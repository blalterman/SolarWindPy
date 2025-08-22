# Excessive Documentation Archive

This directory contains documentation files that were cleaned up during Phase 3 of the PR #270 documentation validation fixes plan (Framework Right-Sizing).

## Reason for Archiving

These files were part of the over-engineered validation framework and documentation process that was not appropriate for SolarWindPy's scale:

**Files Archived:**
- Multiple physics validation scripts and reports
- Complex compliance tracking documents  
- Excessive phase completion reports
- Over-detailed troubleshooting guides
- Enterprise-scale quality assurance processes
- Redundant contributor guidelines

**Problem Analysis:**
- **Documentation complexity**: Too much process overhead for 47 examples
- **Maintenance burden**: Required excessive contributor effort
- **Focus misalignment**: Process-heavy rather than science-focused
- **Scale mismatch**: Enterprise patterns for research package

## Sustainable Approach

**Replaced with:**
- Updated CONTRIBUTING.md with simple 3-step workflow
- Simplified validation framework (scripts/simple_doc_validation/)
- Essential metrics only in CI/CD
- Focus on physics correctness over comprehensive documentation

**Maintained:**
- Core scientific documentation in docs/
- Essential contributor guidelines in CONTRIBUTING.md
- README.rst with development setup
- CLAUDE.md with package-appropriate guidance

## Archive Date
2025-08-22 - Phase 3: Sustainable Documentation Process