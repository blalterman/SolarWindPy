# SolarWindPy Plan Template Usage Guide

## Template Architecture Overview

The SolarWindPy planning system uses a **unified multi-phase architecture** for structured development planning with git branch coordination.

### Template Hierarchy

```
solarwindpy/plans/
├── 0-overview-template.md      # Master template for plan coordination
├── N-phase-template.md         # Standard template for individual phases
├── closeout-template.md        # Template for plan completion documentation
├── plan_template.md           # ⚠️ DEPRECATED - Legacy single-file format
└── TEMPLATE-USAGE-GUIDE.md    # This guide
```

## 🎯 Template Selection Guide

### Default Recommendation: Multi-Phase Architecture

**Use multi-phase structure (0-overview-template.md + N-phase-template.md) for:**

- ✅ **All plans ≥4 hours estimated duration**
- ✅ **Any plan with ≥3 distinct work areas or phases**
- ✅ **Plans requiring multi-session development**
- ✅ **Plans with potential collaboration**
- ✅ **Plans with cross-plan dependencies**
- ✅ **Any plan targeting production systems**

### When Multi-Phase is NOT Suitable:

- ⚠️ **Quick fixes** (<2 hours, single file changes)
- ⚠️ **Proof-of-concept exploration** (rapid iteration needed)
- ⚠️ **Emergency hotfixes** (immediate single-session completion required)

*Note: Even for these cases, consider if the work might expand beyond initial scope*

## 📋 Template Usage Instructions

### Step 1: Create Plan Directory Structure

```bash
# Create plan directory
mkdir solarwindpy/plans/[plan-name]/

# Copy and customize overview template
cp solarwindpy/plans/0-overview-template.md solarwindpy/plans/[plan-name]/0-Overview.md

# Create phase files using N-phase-template.md
cp solarwindpy/plans/N-phase-template.md solarwindpy/plans/[plan-name]/1-Phase-Name.md
cp solarwindpy/plans/N-phase-template.md solarwindpy/plans/[plan-name]/2-Phase-Name.md
# ... repeat for all phases
```

### Step 2: Customize 0-Overview.md

**Required Customizations:**
1. **Plan Name**: Clear, descriptive name
2. **Created**: Use YYYY-MM-DD format  
3. **Branch Names**: Follow plan/[name] and feature/[name] convention
4. **Agent Selection**: Use PlanManager and PlanImplementer
5. **Total Phases**: Must match number of phase files created
6. **Dependencies**: List prerequisite plans or "None"
7. **Affects**: List all files/directories that will be modified
8. **Phase Overview**: One-line description per phase
9. **Phase Files**: Update links to match actual filenames

**Critical Fields:**
- **Dependencies**: Enables cross-plan coordination
- **Affects**: Prevents resource conflicts
- **Total Phases**: Enables progress tracking
- **Estimated Duration**: Supports session planning

### Step 3: Customize Phase Files

**For each N-Phase-Name.md file:**
1. **Phase Metadata**: Update phase number, duration, dependencies
2. **Phase Objective**: Specific goals for this phase
3. **Implementation Tasks**: Break into logical task groups
4. **Task Tracking**: Use commit checksum tracking for git integration
5. **Acceptance Criteria**: Phase-specific success metrics
6. **Cross-References**: Link back to 0-Overview.md

### Step 4: Add Closeout Phase (Final Phase)

**When plan implementation is complete:**
```bash
# Copy closeout template
cp solarwindpy/plans/closeout-template.md solarwindpy/plans/[plan-name]/[N]-Closeout.md
```

**Required Customizations:**
1. **Plan Name**: Match the plan being closed out
2. **Completion Metadata**: Actual duration, phases completed, success rate
3. **Objectives Achievement**: Status of primary objectives from 0-Overview.md
4. **Phase-by-Phase Learnings**: Document key challenges and solutions for each phase
5. **Velocity Intelligence**: Actual vs estimated time for future planning accuracy
6. **Lessons Learned**: Capture reusable patterns and improvement opportunities

**Critical Purpose:**
- **Knowledge Preservation**: Prevent loss of implementation insights
- **Velocity Learning**: Improve estimation accuracy for future plans
- **Pattern Documentation**: Capture reusable approaches for similar work
- **Cross-Plan Intelligence**: Share learnings across the planning ecosystem

## 🏗️ Architecture Benefits

- **Resource Conflict Detection**: "Affects" field prevents concurrent modifications
- **Dependency Management**: Clear prerequisite tracking
- **Quality Assurance**: Phase-level acceptance criteria ensure thoroughness
- **Template Consistency**: All plans follow identical structure

## 📊 Template Field Specifications

### Required Metadata Fields (0-Overview.md)

| Field | Format | Purpose | Example |
|-------|--------|---------|---------|
| **Plan Name** | String | Human-readable identifier | "Test Directory Consolidation" |
| **Created** | YYYY-MM-DD | Plan creation date | "2025-08-12" |
| **Branch** | plan/[name] | Planning branch name | "plan/test-consolidation" |
| **Implementation Branch** | feature/[name] | Development branch name | "feature/test-consolidation" |
| **PlanManager** | Fixed | Agent for planning coordination | "PlanManager" |
| **PlanImplementer** | Fixed | Agent for implementation | "PlanImplementer" |
| **Structure** | "Multi-Phase" | Fixed value for consistency | "Multi-Phase" |
| **Total Phases** | Integer | Number of implementation phases | "6" |
| **Dependencies** | List or "None" | Prerequisite plan names | "Requirements Management Consolidation" |
| **Affects** | Comma-separated | Files/directories modified | "/tests/, solarwindpy/tests/, conftest.py" |
| **Estimated Duration** | String | Total time estimate | "5.5 hours" |
| **Status** | Enum | Current plan state | "Planning \| In Progress \| Completed" |

### Required Phase Fields (N-Phase-Name.md)

| Field | Purpose | Best Practice |
|-------|---------|---------------|
| **Phase N/Total** | Progress indicator | Match 0-Overview.md total |
| **Estimated Duration** | Time planning | Should sum to overall estimate |
| **Dependencies** | Phase sequencing | Reference previous phases or external |
| **Status** | Phase tracking | Update as work progresses |
| **Task Groups** | Logical organization | Group related tasks together |
| **Commit Tracking** | Git integration | Update with actual commit hashes |

## 🔄 Migration Guidelines

### Converting Legacy Single-File Plans

**If you encounter plans using the deprecated plan_template.md structure:**

1. **Create Directory Structure**: 
   ```bash
   mkdir solarwindpy/plans/[plan-name]/
   ```

2. **Extract Metadata**: Copy plan metadata to new 0-Overview.md

3. **Split Implementation**: Break "Implementation Plan" section into logical phases

4. **Create Phase Files**: Use N-phase-template.md for each phase

5. **Update Cross-References**: Ensure phase files link back to overview

6. **Validate Consistency**: Check all metadata fields are populated

### Quality Checklist

**Before Using Any Plan:**
- [ ] All 12 required metadata fields populated in 0-Overview.md
- [ ] Phase count matches between overview and actual files
- [ ] Phase files follow N-phase-template.md structure
- [ ] "Affects" field comprehensively lists modified files
- [ ] Dependencies accurately reflect plan relationships
- [ ] Agent assignments use PlanManager + PlanImplementer


### Agent Usage

**All Plans**: Use PlanManager + PlanImplementer
- Planning coordination with velocity tracking
- Implementation execution with git integration
- Automatic time estimation learning

## 💡 Best Practices

### Plan Development
1. **Start with Overview**: Complete all metadata before creating phase files
2. **Realistic Estimates**: Base time estimates on similar completed plans
3. **Atomic Phases**: Each phase should have clear start/end points
4. **Progressive Refinement**: Update estimates and tasks as implementation progresses
5. **Branch Strategy**: Always follow plan/[name] → feature/[name] pattern

---

*This guide ensures consistent, efficient, and collaborative plan development across the SolarWindPy ecosystem. For questions or template improvements, update this guide and notify the team.*

**Template Version**: 2025-08-12  
**Last Updated**: 2025-08-12  
**Maintained By**: SolarWindPy Development Team