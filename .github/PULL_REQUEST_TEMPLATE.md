## Pull Request Description

<!-- Provide a brief description of changes -->

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that causes existing functionality to change)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing

- [ ] All tests pass locally (`pytest -q`)
- [ ] Test coverage ≥95% (`pytest --cov=solarwindpy --cov-report=term`)
- [ ] Physics validation passed (`.claude/hooks/test-runner.sh --physics`)
- [ ] New tests added for new functionality

## Code Quality

- [ ] Code follows NumPy docstring conventions
- [ ] Formatted with black (`black solarwindpy/ tests/`)
- [ ] Linted with flake8 (`flake8 solarwindpy/ tests/`)
- [ ] Conventional commit messages used
- [ ] Documentation built locally without warnings (`cd docs && make html`)
- [ ] `doc8` check passed

## Attribution & Documentation

- [ ] External code properly attributed (source, license, modifications in comments)
- [ ] Scientific algorithms cite papers in docstrings (DOI/arXiv where applicable)
- [ ] AI-assisted code includes "Generated with Claude Code" in commits
- [ ] No code with incompatible licenses (GPL, proprietary, unknown)
- [ ] Documentation updated (README, CHANGELOG, docstrings)

See [Attribution Guidelines](.claude/docs/ATTRIBUTION.md) for details.

## Breaking Changes

<!-- If applicable, describe breaking changes and migration path -->

## Additional Context

<!-- Add any other context about the PR here -->
