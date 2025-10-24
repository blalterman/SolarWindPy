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

