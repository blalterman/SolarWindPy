# AGENTS for SolarWindPy

# General
Applies to: *
Instructions:
- Use Python 3.11+; install dev deps via `pip install -r requirements-dev.txt`.
- Run tests with `pytest -q`; all must pass—don’t skip or disable failures.
- Format code with `black`; lint with `flake8`.
- Write docstrings in NumPy style.
- Commit messages: concise, descriptive, reference issues.

# RefactorBot
Applies to: src/**/*.py
Instructions:
- Refactor large functions into smaller, reusable components.
- Remove unused variables and dead code.
- Preserve public APIs; ensure all changes pass existing tests.

# TestWriter
Applies to: tests/**/*.py
Instructions:
- Add tests for uncovered public functions using `pytest`.
- Maintain ≥ 95% coverage; isolate tests (avoid unnecessary mocks).

# DocAgent
Applies to: docs/**/*.md, README.md, src/**/*.py
Instructions:
- Improve clarity and consistency; preserve code examples.
- For docstrings, strictly follow NumPy style.

# LinterBot
Applies to: src/**/*.py, tests/**/*.py
Instructions:
- Enforce PEP 8 via `flake8`; use inline disables only when unavoidable.

# DependencyGuardian
Applies to: requirements*.txt, pyproject.toml
Instructions:
- Do not un-pin dependencies; minimize version upgrades.
