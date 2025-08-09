# Agent Selection Matrix - SolarWindPy Development

## Overview

This matrix provides optimal planning and implementation agent combinations for different development contexts in SolarWindPy. Each pairing is optimized for token efficiency while maintaining quality and capability standards.

## Agent Portfolio

### Planning Agents
- **PlanManager-Full** (1,207 tokens) - Enterprise-grade comprehensive planning
- **PlanManager-Streamlined** (976 tokens) - Balanced planning optimized for efficiency  
- **PlanManager-Minimal** (553 tokens) - Lightweight planning for simple tasks

### Implementation Agents
- **PlanImplementer-Full** (1,519 tokens) - Complete enterprise implementation
- **PlanImplementer** (Research-Optimized, 1,400 tokens) - Development-focused implementation
- **PlanImplementer-Minimal** (278 tokens) - Quick task execution

### Universal Service
- **CompactionAgent** (2,800 tokens) - Context compression and session continuity

## Context-Based Selection Matrix

### 🏗️ Infrastructure & CI/CD Work
**Use Case:** Requirements management, workflow optimization, build system changes
- **Planning Agent:** `PlanManager-Streamlined` (976 tokens)
- **Implementation Agent:** `PlanImplementer` (Research-Optimized, 1,400 tokens) 
- **Compaction Strategy:** Medium-complexity processing (50-70% reduction)
- **Total Token Budget:** ~2,376 tokens before compaction
- **Why This Pairing:**
  - Streamlined planning handles system integration complexity
  - Research-optimized implementation excels at CI/CD and tooling work
  - Medium compaction preserves technical details while reducing overhead

### 🚀 Complex Multi-Phase Projects  
**Use Case:** Major feature development, architectural changes, multi-module refactoring
- **Planning Agent:** `PlanManager-Full` (1,207 tokens)
- **Implementation Agent:** `PlanImplementer-Full` (1,519 tokens)
- **Compaction Strategy:** High-complexity processing (40-60% reduction)
- **Total Token Budget:** ~2,726 tokens before compaction  
- **Why This Pairing:**
  - Full planning provides comprehensive project management capabilities
  - Full implementation handles complex enterprise-level development
  - High-complexity compaction preserves detailed project context

### 🎯 Feature Development
**Use Case:** Single module features, analysis tools, plotting enhancements
- **Planning Agent:** `PlanManager-Streamlined` (976 tokens)
- **Implementation Agent:** `PlanImplementer` (Research-Optimized, 1,400 tokens)
- **Compaction Strategy:** Medium-complexity processing (50-70% reduction)
- **Total Token Budget:** ~2,376 tokens before compaction
- **Why This Pairing:**
  - Balanced planning appropriate for focused feature work
  - Research-optimized implementation ideal for scientific computing features
  - Optimal balance of capability and efficiency

### 🔧 Bug Fixes & Maintenance
**Use Case:** Defect resolution, small improvements, code cleanup
- **Planning Agent:** `PlanManager-Minimal` (553 tokens)
- **Implementation Agent:** `PlanImplementer-Minimal` (278 tokens)
- **Compaction Strategy:** Low-complexity processing (maintain efficiency ceiling)
- **Total Token Budget:** ~831 tokens before compaction
- **Why This Pairing:**
  - Minimal planning sufficient for targeted fixes
  - Minimal implementation provides quick task execution
  - Ultra-efficient for rapid development cycles

### 🧪 Testing & Validation Projects
**Use Case:** Test suite expansion, validation framework development
- **Planning Agent:** `PlanManager-Streamlined` (976 tokens)
- **Implementation Agent:** `PlanImplementer` (Research-Optimized, 1,400 tokens)
- **Compaction Strategy:** Medium-complexity processing (50-70% reduction)
- **Total Token Budget:** ~2,376 tokens before compaction
- **Why This Pairing:**
  - Streamlined planning handles test architecture effectively
  - Research-optimized implementation excels at testing frameworks
  - Medium compaction balances test context preservation with efficiency

### 📊 Analysis & Visualization Development
**Use Case:** New fitting functions, plotting tools, data analysis methods
- **Planning Agent:** `PlanManager-Streamlined` (976 tokens)
- **Implementation Agent:** `PlanImplementer` (Research-Optimized, 1,400 tokens)
- **Compaction Strategy:** Medium-complexity processing (50-70% reduction)
- **Total Token Budget:** ~2,376 tokens before compaction
- **Why This Pairing:**
  - Balanced planning for scientific feature development
  - Research-optimized implementation understands scientific computing needs
  - Preserves mathematical and algorithmic context during compaction

## Specialist Agent Integration

### High-Priority Specialists (Always Consider)
- **PhysicsValidator**: Essential for any plasma physics calculations
- **DataFrameArchitect**: Required for MultiIndex data structure work
- **TestEngineer**: Critical for comprehensive testing coverage
- **NumericalStabilityGuard**: Important for mathematical operations

### Context-Specific Specialists
- **FitFunctionSpecialist**: For curve fitting and optimization work
- **PlottingEngineer**: For visualization and publication-quality figures
- **PerformanceOptimizer**: For computational efficiency improvements
- **DocumentationMaintainer**: For documentation-heavy projects

## Compaction Strategy Details

### High-Complexity Processing (40-60% reduction)
**When to Use:** Complex projects with extensive context
- **Target Compression:** 3,000 → 1,200 tokens, 2,800 → 1,120 tokens
- **Preserved Context:** Complete workflow history, detailed dependencies, cross-agent coordination
- **Archived Context:** Verbose descriptions, auxiliary information, completed phase details

### Medium-Complexity Processing (50-70% reduction)
**When to Use:** Balanced feature development, infrastructure work
- **Target Compression:** 1,400 → 420 tokens, 1,000 → 300 tokens
- **Preserved Context:** Current + next phase focus, structured references, workflow continuity
- **Archived Context:** Historical phases, implementation details, exploration notes

### Low-Complexity Processing (Efficiency Ceiling)
**When to Use:** Quick fixes, simple maintenance tasks
- **Target Compression:** Maintain 200-300 token ceiling
- **Preserved Context:** Essential workflow state, immediate next tasks
- **Archived Context:** Completed task consolidation, minimal overhead

## Token Budget Planning

### Session Extension Calculations
- **Without Compaction:** ~3,000 token limit per session
- **With Medium Compaction:** ~7,000-9,000 effective tokens (2-3x extension)
- **With High Compaction:** ~10,000-12,000 effective tokens (3-4x extension)

### Budget Allocation Guidelines
- **Planning Phase:** 25-35% of pre-compaction budget
- **Implementation Phase:** 50-65% of pre-compaction budget
- **Specialist Coordination:** 10-15% of pre-compaction budget
- **Compaction Overhead:** <5% of total budget

## Selection Decision Tree

```
Development Context?
├── Infrastructure/CI → PlanManager-Streamlined + PlanImplementer + Medium Compaction
├── Complex Project → PlanManager-Full + PlanImplementer-Full + High Compaction
├── Feature Development → PlanManager-Streamlined + PlanImplementer + Medium Compaction
├── Bug Fix/Maintenance → PlanManager-Minimal + PlanImplementer-Minimal + Low Compaction
├── Testing Project → PlanManager-Streamlined + PlanImplementer + Medium Compaction
└── Analysis/Visualization → PlanManager-Streamlined + PlanImplementer + Medium Compaction
```

## Quality Assurance

### Validation Checklist
- [ ] Agent pairing appropriate for development context
- [ ] Token budget sufficient for planned work scope
- [ ] Compaction strategy matches context complexity
- [ ] Required specialist agents identified and available
- [ ] Session extension goals realistic and achievable

### Success Metrics
- **Context Preservation:** No critical information loss during compaction
- **Workflow Continuity:** Seamless session resumption after compaction
- **Development Velocity:** Maintained or improved development speed
- **Quality Standards:** No degradation in code quality or testing coverage

This agent selection matrix ensures optimal resource utilization while maintaining the high-quality development standards expected in the SolarWindPy scientific computing environment.