# Integration Checklist

[← Back to Index](../INDEX.md)

---
## Appendix B: Integration Checklist

**Pre-Integration:**
- [ ] Review current CLAUDE.md and `.claude/` structure
- [ ] Backup current configuration
- [ ] Ensure git repository clean state
- [ ] Review current pain points and prioritize features

**Phase 1: Memory Hierarchy (Weeks 1-3):**
- [ ] Create `.claude/memory/` directory structure
- [ ] Extract CLAUDE.md sections into dedicated memory files
- [ ] Update CLAUDE.md with imports (`@.claude/memory/...`)
- [ ] Test import resolution and context loading
- [ ] Measure token usage before/after
- [ ] Document memory structure in `.claude/docs/MEMORY.md`

**Phase 2: Skills System (Weeks 2-4):**
- [ ] Create `.claude/skills/` directory
- [ ] Implement 4 core skills (physics-validator, multiindex-architect, test-generator, plan-executor)
- [ ] Test skill activation with clear trigger phrases
- [ ] Monitor activation accuracy (target ≥85%)
- [ ] Refine skill descriptions based on usage
- [ ] Update CLAUDE.md with skill usage patterns

**Phase 3: Subagents (Weeks 4-7):**
- [ ] Create `.claude/agents/` directory
- [ ] Implement 4 subagents (physics-validator, dataframe-architect, plotting-engineer, fit-function-specialist)
- [ ] Test context isolation and tool restrictions
- [ ] Compare token usage (subagent vs Task agent)
- [ ] Document subagent vs Task vs Skill selection criteria
- [ ] Update `.claude/docs/AGENTS.md`

**Phase 4: Enhanced Hooks (Weeks 5-6):**
- [ ] Create 3 new hook scripts (activity-logger, subagent-report, session-archival)
- [ ] Add Notification, SubagentStop, SessionEnd hooks to settings.json
- [ ] Test hook triggering and log generation
- [ ] Verify log retention policies
- [ ] Update `.claude/docs/HOOKS.md`

**Phase 5: Checkpointing (Week 6):**
- [ ] Document checkpointing usage in `.claude/docs/DEVELOPMENT.md`
- [ ] Create checkpoint-validator hook (optional)
- [ ] Test checkpoint creation and reversion
- [ ] Verify limitations (bash commands, manual edits)

**Phase 6: Output Styles (Week 7):**
- [ ] Create `.claude/output-styles/physics-focused.md`
- [ ] Test style switching and response patterns
- [ ] Compare to Explanatory style
- [ ] Refine based on usage
- [ ] Document in `.claude/docs/`

**Post-Integration:**
- [ ] Measure cumulative token savings
- [ ] Track weekly time savings
- [ ] Gather subjective quality feedback
- [ ] Iterate on skill descriptions, memory organization
- [ ] Create advanced skills/subagents as needed
- [ ] Document lessons learned

---

**End of Document**

*Last Updated: 2025-10-23*
*Version: 1.0*
*Status: Planning & Design Phase*
