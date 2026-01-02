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
/physics [file]              # Physics validation (units conversion, NaN)
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

### Stopping Conditions

#### Rate Limiting

**Skills (activations per hour):**
```bash
# Check skill activation count
grep "physics-validator" .claude/logs/activity.log | tail -n 20

# Limits:
physics-validator: 10/hour
multiindex-architect: 8/hour
test-generator: 12/hour
plan-executor: 5/hour

# Override: Explicit user request bypasses rate limit
"Yes, validate physics in all 20 files"
```

**Memory Imports (per session):**
```bash
# Check memory import count
grep "@.claude/memory/" .claude/logs/session-*.log | wc -l

# Limit: Maximum 20 memory file imports per session
# Warning at: 15 imports (75% of limit)
# Error at: 20 imports (100% of limit)

# Override: Explicit request "Import all physics memory files"
```

#### Budget Guards

**Context Budgets:**
```bash
# Total session budget: 200,000 tokens

# Allocations:
Memory:       ≤10% (20K tokens max)
Subagents:    25% per subagent (50K tokens)
Conversation: 40% (80K tokens)
Tools:        30% (60K tokens)

# Check current usage (approximation)
echo "Current conversation: ~$(wc -w .claude/logs/session-*.log | awk '{print $1*1.3}') tokens"
```

**Warning Thresholds:**
```bash
# 75% (150K tokens): "Approaching session budget limit..."
# 90% (180K tokens): "Session budget critical, prioritize completion..."
# 100% (200K tokens): Session may be truncated, save state

# Subagent specific:
# 75% (37.5K): "DataFrameArchitect approaching budget..."
# 90% (45K): "DataFrameArchitect budget critical..."
# 100% (50K): Block activation
```

#### Approval Gates

**Subagent Approval Thresholds:**
```bash
# Thresholds (estimated tokens):
DataFrameArchitect: >800 tokens (deep multi-file refactoring)
DataFrameArchitect: >600 tokens (multi-file refactoring)
PlottingEngineer: >400 tokens (multi-figure generation)
FitFunctionSpecialist: >700 tokens (complex multi-parameter fitting)

# Approval Prompt Format:
⚠️ DataFrameArchitect Activation Request
   Estimated tokens: 5,000 (10% of session budget)
   Estimated time: 8-12 minutes (timeout: 15 min)

   💾 Checkpoint: Automatic before operation
   🔄 Rollback: Available via checkpoint rewind

   [Proceed] [Skip] [Reduce Scope]
```

**Disabling Approval Gates (use with caution):**
```bash
# Per-request override:
"Yes, validate all physics files" → Bypasses approval gate

# NOT RECOMMENDED: Permanent disable
# (Removes safety mechanism for expensive operations)
```

#### Session Timeouts

**Slash Command Timeouts:**
```bash
/coverage: 5 min   # Large test suites ~300 tests
/physics: 3 min    # Physics validation script execution
/test: 10 min      # Full test suite with slow tests
/review: 5 min     # Code review analysis
/refactor: 8 min   # Multi-file refactoring
/commit: 2 min     # Git operations
/branch: 2 min     # Git branch creation

# Override:
TIMEOUT=600 /coverage  # 10 minutes instead of 5
```

**Subagent Timeouts:**
```bash
DataFrameArchitect: 12 min    # Complex DataFrame refactoring
FitFunctionSpecialist: 25 min  # Iterative optimization
PlottingEngineer: 10 min    # Multi-figure generation

# Warning Messages:
# 75%: "11 min elapsed (75%), continue normally"
# 90%: "13.5 min elapsed (90%), finish soon"
# 100%: "15 min elapsed, operation terminated"

# Override:
SUBAGENT_TIMEOUT=30m  # 30 minutes for deep codebase analysis
```

---

