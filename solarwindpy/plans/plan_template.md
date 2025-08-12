# ⚠️ DEPRECATED: Plan Template for Claude Code Development

**⚠️ LEGACY TEMPLATE - NO LONGER RECOMMENDED**

This template is deprecated as of 2025-08-12. Use the following templates instead:

- **For new plans**: Use [0-overview-template.md](./0-overview-template.md) for plan overview
- **For phase files**: Use [N-phase-template.md](./N-phase-template.md) for individual phase implementation

**Migration Path**: Convert existing single-file plans to multi-phase structure using:
1. Create plan directory with 0-Overview.md (using 0-overview-template.md)
2. Split implementation sections into numbered phase files (using N-phase-template.md)
3. Update phase files with proper cross-linking

---

# Original Template Content (DEPRECATED)

## Plan Metadata
- **Plan Name**: [Short descriptive name]
- **Created**: [Date]
- **Branch**: plan/[plan-name]
- **Implementation Branch**: feature/[plan-name]
- **PlanManager**: [PlanManager | PlanManager-Full | PlanManager-Minimal]
- **PlanImplementer**: [PlanImplementer | PlanImplementer-Full | PlanImplementer-Minimal]
- **Structure**: [Multi-Phase | Single-File]
- **Dependencies**: [List of prerequisite plans, if any]
- **Affects**: [Files/modules that will be modified]
- **Estimated Duration**: [Total time estimate]
- **Status**: [Planning | In Progress | Paused | Completed]

## 🎯 Objective
<!-- Clear statement of what this plan aims to accomplish -->

## 🧠 Context
<!-- Background information, motivation, and relevant links -->

## 🔧 Technical Requirements
<!-- Frameworks, dependencies, versions, and constraints -->

## 📂 Affected Areas
<!-- Files, directories, modules that will be modified -->

## 📋 Implementation Plan

### Phase 1: [Phase Name] (Estimated: [time])
- [ ] **[Task 1]** (Est: [time]) - [Description]
  - Commit: `<checksum>` 
  - Status: [Pending | In Progress | Completed]
- [ ] **[Task 2]** (Est: [time]) - [Description]  
  - Commit: `<checksum>`
  - Status: [Pending | In Progress | Completed]

### Phase 2: [Phase Name] (Estimated: [time])
- [ ] **[Task 3]** (Est: [time]) - [Description]
  - Commit: `<checksum>`
  - Status: [Pending | In Progress | Completed]
- [ ] **[Task 4]** (Est: [time]) - [Description]
  - Commit: `<checksum>`
  - Status: [Pending | In Progress | Completed]

## ✅ Acceptance Criteria
<!-- Define success criteria for completion -->
- [ ] [Criterion 1]
- [ ] [Criterion 2] 
- [ ] All tests pass
- [ ] Code coverage maintained ≥ 95%
- [ ] Documentation updated

## 🧪 Testing Strategy
<!-- How will changes be validated -->

## 📊 Progress Tracking

### Overall Status
- **Phases Completed**: 0/[total]
- **Tasks Completed**: 0/[total]
- **Time Invested**: 0h of [estimated]h
- **Last Updated**: [Date]

### Implementation Notes
<!-- Running log of implementation decisions, blockers, changes -->

## 🔗 Related Plans
<!-- Links to dependent or related plans -->

## 💬 Notes & Considerations
<!-- Additional context, risks, alternatives considered -->

---
*This plan follows the plan-per-branch architecture where implementation occurs on feature/[plan-name] branch with progress tracked via commit checksums.*