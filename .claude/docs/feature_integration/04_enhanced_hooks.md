# Enhanced Hooks System

**Feature Type:** Automatic
**Priority:** LOW-MEDIUM
**Effort:** 4-6 hours
**ROI Break-even:** 4-6 weeks

[← Back to Index](./INDEX.md) | [Previous: Subagents ←](./03_subagents.md) | [Next: Checkpointing →](./05_checkpointing.md)

---

**⚠️ OFFICIAL PLUGIN FEATURE - Partial Support**

**What's Supported in Plugins:**
- ✅ Hook configurations (`hooks.json`) - Event definitions, matchers, timeouts
- ✅ Hook metadata and documentation

**What Requires Local Installation:**
- ⚠️ Executable shell scripts (`.sh` files) - Must be installed to `.claude/hooks/` manually for security

**Rationale:** Plugin system can distribute configurations, but executable scripts need user trust verification.

**Two-Tier Installation:**
1. Plugin provides `hooks.json` (automatic via `/plugin install`)
2. User installs scripts to `.claude/hooks/` (manual, documented in plugin README)

See: [Plugin Packaging](./08_plugin_packaging.md#hooks) for complete details.

---

## Feature 4: Enhanced Hooks System

### 1. Feature Overview

**What It Is:**
Claude Code's hook system provides 9 event lifecycle triggers for executing shell commands at designated points. The enhanced system includes newer events (Notification, SubagentStop, SessionEnd) beyond what SolarWindPy currently uses.

**Core Capabilities:**
- **9 Event Types:** PreToolUse, PostToolUse, UserPromptSubmit, Notification, Stop, SubagentStop, PreCompact, SessionStart, SessionEnd
- **Conditional execution** - JavaScript-like conditions (e.g., `${command.startsWith('git ')}`)
- **Tool matchers** - Target specific tools (Bash, Edit, Write) or all (*)
- **Timeout control** - Per-hook timeout limits (5-120 seconds)
- **Blocking capability** - Hooks can prevent tool execution (PreToolUse)

**Current SolarWindPy Usage:**
✅ Using: SessionStart, UserPromptSubmit, PreToolUse, PostToolUse, PreCompact, Stop
❌ Not using: Notification, SubagentStop, SessionEnd

**Maturity & Prerequisites:**
- ✅ Production-ready core feature
- ✅ Currently implemented in `.claude/settings.json`
- ✅ 6/9 events already in use
- 🆕 3 new events available for adoption

### 2. Value Proposition

**Pain Points Addressed:**

✅ **Repetitive Task Automation (MEDIUM IMPACT)**
*Current state:* Manual monitoring of skill/subagent activity
*With Enhanced Hooks:* Automatic logging via Notification and SubagentStop hooks
*Improvement:* 100% automated tracking, zero manual logging overhead

✅ **Context Preservation (LOW-MEDIUM IMPACT)**
*Current state:* Session end cleanup is ad-hoc
*With Enhanced Hooks:* SessionEnd hook for final state preservation
*Improvement:* Consistent session archival, better cross-session continuity

✅ **Token Usage Optimization (LOW IMPACT)**
*Current state:* PreCompact hook handles token boundary compression
*With Enhanced Hooks:* Additional metrics and monitoring
*Improvement:* Better visibility into compaction effectiveness

**Productivity Improvements:**
- Automated activity logging (skills, subagents, notifications)
- Session lifecycle management (SessionEnd cleanup)
- Real-time monitoring without manual intervention

**Research Workflow Enhancements:**
- Audit trail for all skill/subagent activations
- Session summaries for research notebooks
- Automated metrics collection

### 3. Integration Strategy

**Architecture Fit:**

Enhanced hooks build on existing SolarWindPy hook infrastructure:

```
Current Hooks (6/9):
✅ SessionStart → validate-session-state.sh
✅ UserPromptSubmit → git-workflow-validator.sh
✅ PreToolUse → physics-validation.py, git-workflow-validator.sh
✅ PostToolUse → test-runner.sh --changed
✅ PreCompact → create-compaction.py
✅ Stop → coverage-monitor.py

New Hooks (3/9):
🆕 Notification → activity-logger.sh (NEW)
🆕 SubagentStop → subagent-report.sh (NEW)
🆕 SessionEnd → session-archival.sh (NEW)
```

**Relationship to Existing Systems:**

| System Component | Integration Approach |
|------------------|---------------------|
| **Skills** | Notification hook logs skill activations |
| **Subagents** | SubagentStop hook captures completion reports |
| **Memory** | SessionEnd hook updates session history |
| **Coverage Monitoring** | SessionEnd hook creates final coverage snapshot |
| **Plan System** | Notification hook tracks plan-related events |

**Backward Compatibility:**
✅ **Fully compatible** - New hooks are additive
✅ **Optional adoption** - Existing 6 hooks continue unchanged
✅ **No breaking changes**

### 3.5. Risk Assessment

#### Technical Risks

**Risk: Hook Script Execution Failures**
- **Likelihood:** Medium
- **Impact:** Medium (monitoring gaps, workflow interruptions)
- **Mitigation:**
  - Add error handling to all hook scripts
  - Log failures to `.claude/logs/hook-errors.log`
  - Set reasonable timeouts (5-15 seconds max)
  - Test scripts independently before hooking
  - Provide graceful fallback (continue even if hook fails)

**Risk: Hook Execution Latency**
- **Likelihood:** Medium
- **Impact:** Low-Medium (workflow slowdowns)
- **Mitigation:**
  - Keep hook scripts under 1 second execution time
  - Use background processes for slow operations
  - Profile hook execution times
  - Disable non-critical hooks if latency detected
  - Optimize script efficiency (avoid redundant operations)

**Risk: Plugin Packaging Limitations**
- **Likelihood:** High
- **Impact:** Medium (hooks work locally but not in plugins)
- **Mitigation:**
  - Use two-tier approach: plugin provides `hooks.json`, local installs scripts
  - Document manual script installation requirements
  - Consider migrating to Skills with code execution instead
  - Provide installation scripts in plugin documentation
  - Test plugin distribution across different environments

**Risk: Log File Management Overhead**
- **Likelihood:** Low-Medium
- **Impact:** Low (disk space, clutter)
- **Mitigation:**
  - Implement log rotation (daily/weekly)
  - Set retention policies (30 days default)
  - Add cleanup script: `.claude/scripts/cleanup-logs.sh`
  - Monitor log directory size
  - Compress old logs automatically

#### Adoption Risks

**Risk: Hook Configuration Complexity**
- **Likelihood:** Medium
- **Impact:** Low-Medium (adoption friction)
- **Mitigation:**
  - Provide complete `.claude/settings.json` examples
  - Document common hook patterns
  - Create hook generator script
  - Offer minimal viable configuration (start with 1-2 hooks)
  - Include troubleshooting guide

**Risk: Hook Maintenance Burden**
- **Likelihood:** Medium
- **Impact:** Medium (outdated scripts, broken hooks)
- **Mitigation:**
  - Include hooks in pre-commit validation
  - Test hooks as part of CI/CD
  - Version control all hook scripts
  - Document hook dependencies clearly
  - Schedule quarterly hook audits

**Risk: Over-Logging Creates Noise**
- **Likelihood:** Medium
- **Impact:** Low (hard to find useful information)
- **Mitigation:**
  - Use structured logging formats (JSON)
  - Separate log files by hook type
  - Implement log level filtering (INFO, WARN, ERROR)
  - Create log analysis tools
  - Document what each hook logs and why

#### Performance Risks

**Risk: SessionEnd Hook Timeout on Large Sessions**
- **Likelihood:** Low
- **Impact:** Medium (archival incomplete)
- **Mitigation:**
  - Increase timeout for SessionEnd hooks (30s+)
  - Compress archives in background
  - Split large sessions before archiving
  - Test with realistic session sizes
  - Provide progress indicators

**Risk: Notification Hook Spam**
- **Likelihood:** Medium
- **Impact:** Low (frequent interruptions)
- **Mitigation:**
  - Use specific matchers, not wildcards
  - Rate-limit notification frequency
  - Batch related notifications
  - Make notifications async/non-blocking
  - Allow per-hook disable flags

### 4. Implementation Specification

#### Enhanced Hook Configuration

**Updated `.claude/settings.json`** (additions only):

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "*skill*",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/activity-logger.sh skill",
            "timeout": 5
          }
        ]
      },
      {
        "matcher": "*plan*",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/activity-logger.sh plan",
            "timeout": 5
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/subagent-report.sh",
            "args": ["${subagent_name}", "${duration}"],
            "timeout": 10
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/session-archival.sh",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

#### New Hook Scripts

##### Hook Script 1: Activity Logger

**File:** `.claude/hooks/activity-logger.sh`

```bash
#!/usr/bin/env bash
# Activity Logger Hook
# Logs skill activations, plan events, and notifications

set -euo pipefail

ACTIVITY_TYPE="${1:-unknown}"
LOG_DIR=".claude/logs"
LOG_FILE="${LOG_DIR}/activity.log"

# Create log directory if needed
mkdir -p "${LOG_DIR}"

# Timestamp
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Log entry
case "${ACTIVITY_TYPE}" in
    skill)
        echo "[${TIMESTAMP}] [SKILL ACTIVATED] Context: ${2:-unknown}" >> "${LOG_FILE}"
        ;;
    plan)
        echo "[${TIMESTAMP}] [PLAN EVENT] Context: ${2:-unknown}" >> "${LOG_FILE}"
        ;;
    *)
        echo "[${TIMESTAMP}] [NOTIFICATION] ${ACTIVITY_TYPE}" >> "${LOG_FILE}"
        ;;
esac

# Optional: Keep only last 1000 lines
tail -n 1000 "${LOG_FILE}" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "${LOG_FILE}"

exit 0
```

**Purpose:** Track skill activations, plan-related events, and general notifications for activity monitoring.

##### Hook Script 2: Subagent Report

**File:** `.claude/hooks/subagent-report.sh`

```bash
#!/usr/bin/env bash
# Subagent Report Hook
# Logs subagent completions with timing and context

set -euo pipefail

SUBAGENT_NAME="${1:-unknown}"
DURATION="${2:-0}"
LOG_DIR=".claude/logs"
LOG_FILE="${LOG_DIR}/subagent-activity.log"

mkdir -p "${LOG_DIR}"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Log subagent completion
echo "[${TIMESTAMP}] [SUBAGENT COMPLETED] Name: ${SUBAGENT_NAME} | Duration: ${DURATION}s" >> "${LOG_FILE}"

# Optional: Generate metrics
TOTAL_INVOCATIONS=$(grep -c "\[SUBAGENT COMPLETED\]" "${LOG_FILE}" 2>/dev/null || echo "0")
AVG_DURATION=$(grep "\[SUBAGENT COMPLETED\]" "${LOG_FILE}" | \
    grep -oP 'Duration: \K[0-9]+' | \
    awk '{sum+=$1; count++} END {if(count>0) print sum/count; else print 0}')

# Update metrics file
cat > "${LOG_DIR}/subagent-metrics.txt" <<EOF
Total Subagent Invocations: ${TOTAL_INVOCATIONS}
Average Duration: ${AVG_DURATION}s
Last Update: ${TIMESTAMP}
EOF

exit 0
```

**Purpose:** Track subagent usage patterns, measure execution time, maintain metrics.

##### Hook Script 3: Session Archival

**File:** `.claude/hooks/session-archival.sh`

```bash
#!/usr/bin/env bash
# Session Archival Hook
# Creates session summary and archives state at session end

set -euo pipefail

ARCHIVE_DIR=".claude/logs/sessions"
TIMESTAMP=$(date -u +"%Y%m%d-%H%M%S")
SESSION_FILE="${ARCHIVE_DIR}/session-${TIMESTAMP}.md"

mkdir -p "${ARCHIVE_DIR}"

# Gather session summary
cat > "${SESSION_FILE}" <<EOF
# Session Summary

**Date:** $(date -u +"%Y-%m-%d %H:%M:%S UTC")
**Branch:** $(git branch --show-current 2>/dev/null || echo "unknown")

## Changes
\`\`\`
$(git status --short 2>/dev/null || echo "No git repository")
\`\`\`

## Test Coverage
EOF

# Append coverage if available
if [ -f "coverage.json" ]; then
    COVERAGE=$(python -c "import json; print(json.load(open('coverage.json'))['totals']['percent_covered'])" 2>/dev/null || echo "N/A")
    echo "**Coverage:** ${COVERAGE}%" >> "${SESSION_FILE}"
fi

# Append activity summary if logs exist
if [ -f ".claude/logs/activity.log" ]; then
    echo -e "\n## Activity Summary" >> "${SESSION_FILE}"
    echo "\`\`\`" >> "${SESSION_FILE}"
    tail -n 20 ".claude/logs/activity.log" >> "${SESSION_FILE}"
    echo "\`\`\`" >> "${SESSION_FILE}"
fi

# Cleanup old sessions (keep last 30)
ls -t "${ARCHIVE_DIR}"/session-*.md 2>/dev/null | tail -n +31 | xargs rm -f 2>/dev/null || true

echo "✅ Session archived: ${SESSION_FILE}"

exit 0
```

**Purpose:** Create comprehensive session summaries for research notebooks and cross-session continuity.

#### Migration Path

**Phase 1: Add New Hooks (Week 1)**
1. Create 3 new hook scripts (activity-logger, subagent-report, session-archival)
2. Make scripts executable: `chmod +x .claude/hooks/*.sh`
3. Add hook configurations to `.claude/settings.json`
4. Test individual hooks with simple scenarios

**Phase 2: Validate Integration (Week 2)**
1. Monitor activity logs for skill activations
2. Check subagent metrics after several invocations
3. Review session archival quality
4. Adjust log retention and format as needed

**Phase 3: Optimization (Week 3+)**
1. Refine log formats based on usage
2. Add custom metrics (e.g., token usage per skill)
3. Create analytics dashboard from log data
4. Document hook system enhancements

**Rollback Strategy:**

*Immediate Disable (Single Hook):*
1. Edit `.claude/settings.json`
2. Comment out or remove specific hook configuration (Notification, SubagentStop, or SessionEnd)
3. Save file (changes take effect immediately in new sessions)
4. Existing 6 hooks unaffected

*Full Rollback (All Enhanced Hooks):*
1. `git diff .claude/settings.json` to see what was added
2. Remove all new hook entries (Notification, SubagentStop, SessionEnd)
3. `git checkout .claude/settings.json` if needed (restore to pre-enhanced state)
4. Delete new hook scripts: `rm .claude/hooks/activity-logger.sh .claude/hooks/subagent-report.sh .claude/hooks/session-archival.sh`
5. Existing 6 hooks continue working unchanged

*Rollback Hook Scripts Only (Keep Configurations):*
1. Delete/rename hook scripts: `mv .claude/hooks/*.sh .claude/hooks/disabled/`
2. Hooks configured but scripts won't execute (harmless failures)
3. Review logs to confirm no adverse effects
4. Re-enable selectively by moving scripts back

*Clean Up Logs (Optional):*
1. `rm -rf .claude/logs/activity.log`
2. `rm -rf .claude/logs/subagent-metrics.txt`
3. `rm -rf .claude/archives/session-*.tar.gz`
4. Reclaim disk space if needed

*Rollback Verification Steps:*
- ✅ `.claude/settings.json` has only original 6 hooks
- ✅ No new hook scripts in `.claude/hooks/`
- ✅ No error messages in Claude Code output
- ✅ Existing workflows unaffected
- ✅ Original 6 hooks still functioning

*Risk:** Very low - Enhanced hooks are additive configuration. Removal is trivial, no dependencies.

### 4.5. Alternatives Considered

#### Alternative 1: No Additional Hooks (Status Quo)

**Description:** Continue using existing 6 hooks without adding Notification, SubagentStop, or SessionEnd.

**Pros:**
- ✅ Zero implementation effort
- ✅ No risk of new hook failures
- ✅ Simpler configuration
- ✅ No log management overhead

**Cons:**
- ❌ Miss skill/subagent activity visibility
- ❌ No automatic session archival
- ❌ Manual tracking of workflow events
- ❌ Harder to debug issues retrospectively

**Decision:** **Rejected** - Observability benefits (especially for skills/subagents) justify modest effort.

#### Alternative 2: Skills for Logging Instead of Hooks

**Description:** Create logging skills that activate on relevant events instead of using hooks.

**Pros:**
- ✅ Plugin-packageable (no local script installation)
- ✅ Context-aware (skills understand semantic events)
- ✅ Progressive disclosure (load only when needed)

**Cons:**
- ❌ Not event-driven (relies on manual/automatic activation)
- ❌ Can't guarantee execution at critical moments
- ❌ Skills are for actions, not passive monitoring
- ❌ Overhead of skill invocation vs. lightweight hook

**Decision:** **Complementary** - Use skills for analysis, hooks for guaranteed event capture.

#### Alternative 3: External Monitoring Tools

**Description:** Integrate third-party observability platforms (Datadog, Sentry, etc.).

**Pros:**
- ✅ Enterprise-grade features
- ✅ Advanced analytics and dashboards
- ✅ Mature ecosystem
- ✅ Cross-project visibility

**Cons:**
- ❌ Costly (licensing fees)
- ❌ Overkill for single-project needs
- ❌ External dependencies
- ❌ Data privacy concerns (sending session data externally)
- ❌ Complex integration

**Decision:** **Rejected** - Lightweight local hooks sufficient for SolarWindPy's needs. Revisit if scaling to multi-project.

#### Alternative 4: Manual Logging in Workflow

**Description:** Manually add logging statements when needed instead of automatic hooks.

**Pros:**
- ✅ Full control over what gets logged
- ✅ No hook configuration needed
- ✅ Zero overhead when not needed

**Cons:**
- ❌ Easy to forget
- ❌ Inconsistent coverage
- ❌ High cognitive load
- ❌ Doesn't capture unexpected events
- ❌ Manual effort every session

**Decision:** **Rejected** - Automation prevents human error and ensures comprehensive coverage.

#### Alternative 5: Git-Based Session History Only

**Description:** Rely solely on git commit history for session tracking.

**Pros:**
- ✅ Already using git
- ✅ Zero additional infrastructure
- ✅ Natural for code-focused work

**Cons:**
- ❌ Doesn't capture uncommitted work
- ❌ No skill/subagent activity
- ❌ Missing context (prompts, reasoning, decisions)
- ❌ Can't track failed experiments
- ❌ Coarse-grained (commit-level, not event-level)

**Decision:** **Complementary** - Git provides code history, hooks provide workflow history.

#### Selected Approach: Enhanced Hook System

**Rationale:**
- Lightweight, local-first observability
- Event-driven automation (no manual overhead)
- Complements existing 6 hooks naturally
- Plugin-friendly (configurations distribute, scripts install locally)
- Low complexity, high value (especially for skills/subagents)

**Trade-offs Accepted:**
- Manual script installation for plugin users (mitigated by clear docs)
- Log management overhead (mitigated by rotation/retention policies)
- Slight execution latency (mitigated by performance optimization)

### 5. Priority & Effort Estimation

**Impact Level:** 🟢 **LOW-MEDIUM**

| Metric | Score | Justification |
|--------|-------|---------------|
| Repetitive automation | 4/5 | 100% automated logging |
| Context preservation | 3/5 | Better session continuity |
| Agent coordination | 2/5 | Indirect benefit (activity tracking) |
| Token optimization | 2/5 | Metrics visibility only |
| Plan efficiency | 2/5 | Plan event tracking |

**Implementation Complexity:** 🟢 **2/5 (Low)**

| Aspect | Complexity | Notes |
|--------|------------|-------|
| Hook script creation | 2/5 | Simple bash scripts |
| Settings.json updates | 1/5 | JSON configuration additions |
| Testing | 2/5 | Verify hooks trigger correctly |
| Documentation | 1/5 | Update HOOKS.md with new events |
| Maintenance | 2/5 | Log file management, retention |

**Dependencies:**
- ✅ None - Hooks are core feature
- ✅ No external tools required
- ✅ Bash scripts only (portable)

**Estimated Effort:**
- Hook script creation: **2-3 hours** (3 scripts × 40-60 min)
- Settings configuration: **30 minutes**
- Testing & validation: **1-2 hours**
- Documentation update: **30 minutes**
- **Total: 4-6 hours**

**Break-even Analysis:**
- Time saved per week: ~30-60 minutes (automated logging vs manual tracking)
- Break-even: **4-6 weeks**
- Annual ROI: **25-50 hours** of time otherwise spent on manual activity tracking

### 6. Testing Strategy

**Validation Approach:**

#### Test 1: Notification Hook Activation
```
Scenario: Skill activation (e.g., physics-validator)
Expected: activity-logger.sh logs "[SKILL ACTIVATED]"
Validation: Check .claude/logs/activity.log for entry
```

#### Test 2: SubagentStop Hook
```
Scenario: Complete subagent task (physics-validator subagent)
Expected: subagent-report.sh logs completion with duration
Validation: Check .claude/logs/subagent-activity.log and metrics file
```

#### Test 3: SessionEnd Hook
```
Scenario: End Claude Code session
Expected: session-archival.sh creates session summary
Validation: Check .claude/logs/sessions/ for new summary file
```

#### Test 4: Log Retention
```
Scenario: Generate 35+ sessions
Expected: Only last 30 session files retained
Validation: Verify old session files automatically deleted
```

#### Test 5: Hook Timeout
```
Scenario: Hook takes longer than timeout
Expected: Hook terminates gracefully, main workflow continues
Validation: Session doesn't hang on slow hooks
```

**Success Criteria:**
- ✅ All 3 new hooks trigger correctly at designated events
- ✅ Log files created and populated with expected format
- ✅ Log retention policies enforce (1000 lines for activity, 30 files for sessions)
- ✅ Hooks complete within timeout limits
- ✅ No degradation in main workflow performance

**Monitoring:**
```bash
# View recent activity
tail -f .claude/logs/activity.log

# Check subagent metrics
cat .claude/logs/subagent-metrics.txt

# Review last session
ls -t .claude/logs/sessions/ | head -1 | xargs cat
```

---


**Last Updated:** 2025-10-31
**Document Version:** 1.1
**Plugin Ecosystem:** Integrated (Anthropic Oct 2025 release)
