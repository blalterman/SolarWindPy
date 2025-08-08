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

### Branch-First Development (NEW!)

**CRITICAL:** Claude now uses a branch-first development workflow:

1. **Before any development**, Claude lists unmerged branches: `git branch -r --no-merged master`
2. **Asks user** to specify branch, search for appropriate branch, or create new branch
3. **Never works directly on master** - all development happens on feature branches
4. **Creates descriptive branches** using pattern: `claude/YYYY-MM-DD-HH-MM-SS-module-feature-description`

### Quality Requirements

The configuration enforces these requirements:
1. All tests must pass (`pytest -q`)
2. Code must be formatted (`black solarwindpy/`)
3. No linting errors (`flake8`)
4. NumPy-style docstrings required
5. Target ≥95% code coverage
6. **NEW:** Include "Generated with Claude Code" in commit messages

### File Overview

- **`settings.json`**: Updated with branch-first workflow systemPrompt
- **`agents.md`**: Enhanced with git workflow requirements for all agents
- **`CLAUDE.md`**: Comprehensive branching workflow documentation
- **`WORKFLOW_TEMPLATE.md`**: Step-by-step template for feature development
- **`README.md`**: This overview file

See `CLAUDE.md` for complete branching workflow and `WORKFLOW_TEMPLATE.md` for detailed development process.