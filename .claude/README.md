# SolarWindPy Claude Code Configuration

This directory contains project-specific configuration for Claude Code that is shared across the team.

## Files

- **`settings.json`**: Team-shared Claude Code settings including permissions, system prompt, and tool configuration
- **`CLAUDE.md`**: Quick reference for development commands and workflows  
- **`agents.md`**: Comprehensive agent system for specialized development roles and validation
- **`README.md`**: This file

## Usage

When working in this repository, Claude Code will automatically load the configuration from this directory, providing:

1. **Pre-configured development commands** (pytest, black, flake8, conda, git)
2. **Security settings** that protect sensitive files (.env, secrets, tokens)
3. **Specialized development agents** for physics validation, data architecture, testing, and more
4. **Project-specific system prompt** with SolarWindPy context

## Configuration Benefits

- **Consistent behavior** across all team members and computers
- **Version controlled** configuration that evolves with the project
- **Security-focused** permissions that protect sensitive data
- **Domain-specific** guidance for solar wind physics and scientific computing
- **Automated quality assurance** with testing and formatting requirements

## Development Workflow

The configuration enforces these requirements:
1. All tests must pass (`pytest -q`)
2. Code must be formatted (`black .`)
3. No linting errors (`flake8`)
4. NumPy-style docstrings required
5. Target ≥95% code coverage

See the main project `CLAUDE.md` file for complete development guidelines.