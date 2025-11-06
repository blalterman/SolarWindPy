# Quick Reference Commands

[← Back to Index](../INDEX.md)

---
## Appendix A: Quick Reference Commands

### Skills
```bash
# Skills auto-activate, no commands needed
# Location: .claude/skills/<skill-name>/SKILL.md
```

### Memory
```bash
# Add memory entry quickly
claude
> #[Enter text, select destination]

# Edit memory files
claude
> /memory

# Initialize project memory
claude
> /init
```

### Subagents
```bash
# Subagents invoke automatically or explicitly
# Location: .claude/agents/<agent-name>.md
```

### Slash Commands
```bash
# Testing & Quality
/coverage                    # Quick coverage check (highlight <95% files)
/physics [file]              # Physics validation (SI units, thermal speed, NaN)
/test [args]                 # Smart test runner (changed files or all)

# Code Review
/review [file]              # Code review checklist (physics, tests, MultiIndex)
/refactor [file]            # Refactoring assistant (patterns, edge cases)

# Planning
/plan-create <title>        # Create GitHub Issues plan with value proposition
/plan-phases <issue>        # Add phases to existing plan (batch mode)
/plan-status                # Show current plan status and progress

# Git Workflow
/commit                      # Smart commit helper (conventional commits + Claude attribution)
/branch <name>              # Smart branch creation (feature/fix/docs prefix)

# Usage
# Example: /coverage
# Example: /physics solarwindpy/core/ion.py
# Example: /plan-create "API Refactoring"

# Location: .claude/commands/<command-name>.md OR via plugin
```

### Hooks
```bash
# Hook configuration in .claude/settings.json
# View activity logs
tail -f .claude/logs/activity.log

# View subagent metrics
cat .claude/logs/subagent-metrics.txt
```

### Checkpointing
```bash
# Automatic - no commands needed
# Use Claude Code UI to revert to checkpoints
```

### Output Styles
```bash
# List available styles
claude
> /output-style

# Switch style
claude
> /output-style physics-focused

# Create new style
claude
> /output-style:new <description>
```

---

