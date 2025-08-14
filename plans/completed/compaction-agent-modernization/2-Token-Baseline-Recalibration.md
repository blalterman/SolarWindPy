# Phase 2: Token Baseline Recalibration

## Metadata
- **Phase**: 2 of 7
- **Estimated Time**: 60 minutes
- **Dependencies**: Phase 1 (Architecture Audit)
- **Status**: Pending
- **Completion**: 0%

## Objective
Update CompactionAgent token baselines from obsolete 12,300-token (6-agent) system to current 2,400-token (2-agent) streamlined architecture, recalibrating all compression targets and efficiency calculations.

## Current vs Target Token Architecture

### Obsolete Baseline (Pre-Modernization)
```
CompactionAgent Current Assumptions:
- "High-Complexity Sources": 3,000 tokens (Plan Manager Full, Plan Implementer Full)
- "Medium-Complexity Sources": 1,400 tokens (Streamlined, Research-Optimized) 
- "Low-Complexity Sources": 200-300 tokens (Minimal variants)
- Total ecosystem: ~12,300 tokens across 6 planning agents

Compression Targets:
- High: 3000→1200 tokens (60% reduction)
- Medium: 1400→420 tokens (70% reduction)
- Low: maintain 200-300 tokens
```

### Current Streamlined Reality
```
Actual Agent Token Distribution:
- PlanManager: 1,200 tokens (strategic planning)
- PlanImplementer: 1,200 tokens (execution with git integration)
- PlanStatusAggregator: ~400 tokens (monitoring)
- Total active system: 2,400 tokens (80% reduction already achieved)

Required Compression Targets:
- PlanManager: 1200→600-800 tokens (33-50% reduction)
- PlanImplementer: 1200→600-800 tokens (33-50% reduction)
- StatusAggregator: 400→200-300 tokens (25-50% reduction)
```

## Token Recalibration Tasks

### Core Architecture Updates
- [ ] **T2.1**: Replace "6 planning agent variants" with "3 current agents" (Lines 25, 272) - 10 min
- [ ] **T2.2**: Update token distribution table from 12,300 to 2,400 baseline (Lines 37-44) - 15 min
- [ ] **T2.3**: Recalibrate compression targets from 60-70% to 33-50% (Lines 34-46) - 15 min
- [ ] **T2.4**: Update efficiency calculations and token savings projections (Lines 87-92) - 10 min
- [ ] **T2.5**: Revise performance metrics and overhead targets (Lines 220-231) - 10 min

### Specific Line Updates

#### Lines 29-47: Tiered Compression Processing
```markdown
# CURRENT (OBSOLETE):
- **High-Complexity Sources** (Plan Manager Full, Plan Implementer Full):
  - Target: 40-60% compression (3000→1200, 2800→1120 tokens)

# UPDATED (MODERNIZED):
- **PlanManager Processing** (Strategic planning with velocity tracking):
  - Target: 33-50% compression (1200→600-800 tokens)
  - Focus: Preserve plan discovery, time estimation, status tracking
```

#### Lines 87-92: Expected Token Savings
```markdown
# CURRENT (OBSOLETE):
CompactionAgent: ~800 tokens (comprehensive operations)
Per-Agent Integration: ~50 tokens each (6 agents = 300 tokens)
TOTAL POST-CONSOLIDATION: ~1,100 tokens
NET SAVINGS: ~6,900 tokens (86% reduction in context logic)

# UPDATED (MODERNIZED):  
CompactionAgent: ~400 tokens (streamlined operations)
Per-Agent Integration: ~50 tokens each (3 agents = 150 tokens)
TOTAL POST-CONSOLIDATION: ~550 tokens
NET SAVINGS: Enables 2-3x longer sessions within 2,400 token baseline
```

#### Lines 220-231: Performance Metrics
```markdown
# CURRENT (OBSOLETE):
Token Efficiency Targets:
- System Overhead: <100 tokens per compaction operation
- Compression Ratios: Achieve target reductions without quality loss

# UPDATED (MODERNIZED):
Token Efficiency Targets:
- System Overhead: <50 tokens per compaction operation (2% of baseline)
- Compression Ratios: 33-50% reduction maintaining workflow continuity
- Session Extension: Enable 3,600-7,200 token effective capacity
```

### Compression Algorithm Recalibration

#### Realistic Targets for Current Architecture
```python
# Current Agent → Compressed Target (Reduction %)
PlanManager: 1,200 → 600-800 tokens (33-50%)
PlanImplementer: 1,200 → 600-800 tokens (33-50%) 
PlanStatusAggregator: 400 → 200-300 tokens (25-50%)

# Combined System Efficiency
Uncompressed: 2,400 tokens → Compressed: 1,400-1,900 tokens
Effective Capacity: 3,600-4,800 tokens (1.5-2x session extension)
```

## Implementation Checklist

### Token Reference Updates
- [ ] **Lines 34-46**: Update compression processing tiers
- [ ] **Lines 87-92**: Recalculate token savings projections  
- [ ] **Lines 220-231**: Revise performance targets
- [ ] **Lines 261-275**: Update integration efficiency claims
- [ ] **Overview file**: Sync token estimates with recalibrated values

### Algorithm Efficiency Validation
- [ ] **Compression Ratios**: Validate 33-50% targets are achievable
- [ ] **Quality Preservation**: Ensure reduced compression maintains continuity
- [ ] **Overhead Minimization**: Target <50 token operational overhead
- [ ] **Session Extension**: Calculate actual session length improvements

## Success Criteria
- [ ] All token references updated from 12,300 to 2,400 baseline
- [ ] Compression targets recalibrated to realistic 33-50% reduction
- [ ] Performance metrics aligned with streamlined architecture
- [ ] Token savings projections accurate for current system
- [ ] Algorithm efficiency validated for modernized targets
- [ ] Session extension capabilities clearly quantified

## Validation Requirements
- [ ] No references to obsolete token counts (3000, 1400, 12,300)
- [ ] All compression targets achievable with current agent sizes
- [ ] Performance overhead stays below 2% of token baseline
- [ ] Session extension provides meaningful productivity gains

## Risk Mitigation
- **Aggressive Targets**: 33-50% reduction is more conservative than obsolete 60-70%
- **Quality Preservation**: Lower compression maintains better continuity
- **Realistic Expectations**: Align with actual agent capabilities
- **Validation Testing**: Phase 7 will validate actual compression achieved

## Next Phase Dependencies
Phase 3 (Agent Reference Updates) depends on:
- Completed token baseline corrections
- Validated compression targets  
- Updated performance metrics
- Aligned efficiency calculations

**Estimated Completion**: 648681b
**Time Invested**: 0.75h of 1h
**Status**: Completed