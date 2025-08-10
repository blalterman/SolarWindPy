# Planning Agents Variants Guide

## Overview
The Planning Agents system includes multiple variants of both Plan Manager and Plan Implementer agents, optimized for different development contexts and team sizes.

## Plan Manager Variants

### 📋 agent-plan-manager-full.md (Comprehensive)
**Use for:** Complex projects requiring detailed guidance and comprehensive planning features

**Features:**
- ✅ Detailed behavioral guidelines and usage patterns
- ✅ Comprehensive error handling documentation
- ✅ Extensive examples and workflow explanations
- ✅ Advanced features documentation with detailed explanations

**Token Count:** ~3,000 tokens

**Ideal for:**
- New teams learning the planning system
- Complex multi-phase projects with many dependencies
- Situations requiring comprehensive documentation and guidance

### ⚡ agent-plan-manager.md (Token Optimized)
**Use for:** Most development scenarios where token efficiency is important

**Features:**
- ✅ All core planning capabilities preserved
- ✅ Concise documentation focused on essential information
- ✅ Same functionality with 66% fewer tokens
- ✅ Faster response times and lower token costs

**Token Count:** ~1,000 tokens

**Ideal for:**
- Regular development work and ongoing projects
- Token-constrained environments
- Teams familiar with the planning system
- Most SolarWindPy development scenarios

### 🔧 agent-plan-manager-minimal.md (Lightweight)
**Use for:** Simple projects, prototypes, and learning environments

**Features:**
- ✅ Basic plan creation and task tracking
- ✅ Simple time estimation (hour-based)
- ✅ Essential progress calculation
- ❌ No cross-plan coordination
- ❌ No advanced time estimation intelligence
- ❌ No multi-team coordination
- ❌ No comprehensive error handling

**Token Count:** ~300 tokens

**Ideal for:**
- Personal projects and prototypes
- Learning environments and tutorials
- Simple automation tasks
- Ultra token-constrained scenarios

## Plan Implementer Variants

## Variant Selection Guide

### 🔬 agent-plan-implementer.md (Research Optimized)
**Use for:** Scientific research software development, academic projects, small teams (1-5 developers)

**Features:**
- ✅ Cross-branch coordination with plan-per-branch architecture
- ✅ Sub-plan coordination and dependency management
- ✅ Scientific domain specialist integration (PhysicsValidator, NumericalStabilityGuard)
- ✅ QA integration (pytest, flake8, coverage validation)
- ✅ Performance monitoring for research workflows
- ✅ Merge workflow (feature → plan → master)
- ✅ Critical error handling and recovery

**Token Count:** ~1,400-1,800 tokens

**Ideal for:**
- SolarWindPy development
- Academic research codebases
- Physics/astronomy software
- Data analysis packages
- Small collaborative projects

### 🏢 agent-plan-implementer-full.md (Enterprise Complete)
**Use for:** Large-scale enterprise development, multi-team projects, complex organizational workflows

**Features:**
- ✅ All research optimized features PLUS:
- ✅ Multi-developer coordination and resource conflict detection
- ✅ Enterprise workflow management (approval gates, compliance tracking)
- ✅ Advanced error recovery and disaster recovery procedures
- ✅ Stakeholder communication and management reporting
- ✅ Risk management and audit trail maintenance
- ✅ Comprehensive behavioral guidelines and protocols

**Token Count:** ~2,800-3,200 tokens

**Ideal for:**
- Fortune 500 software development
- Regulated industries (finance, healthcare, aerospace)
- Large open source projects (100+ contributors)
- Multi-team coordinated releases
- Mission-critical systems

### ⚡ agent-plan-implementer-minimal.md (Lightweight)
**Use for:** Simple projects, quick prototypes, single-developer work

**Features:**
- ✅ Basic task execution and checksum management
- ✅ Simple progress tracking
- ✅ Essential error handling
- ❌ No sub-plan coordination
- ❌ No domain specialist integration
- ❌ No QA automation
- ❌ No performance monitoring

**Token Count:** ~200-300 tokens

**Ideal for:**
- Personal projects and scripts
- Rapid prototyping
- Learning environments
- Simple automation tasks
- Token-constrained environments

## Selection Matrix

### Plan Manager Selection
| Project Characteristic | Minimal | Streamlined | Comprehensive |
|----------------------|---------|-------------|---------------|
| Team Size | 1 | 1-5 | 5+ |
| Project Complexity | Simple | Moderate | Complex |
| Planning Experience | Beginner | Experienced | New to system |
| Token Budget | Strict | Moderate | Flexible |
| Documentation Needs | Basic | Standard | Extensive |
| **Claude Pro Usage** | **Light** | **Regular** | **Heavy/Max Plan** |

### Plan Implementer Selection
| Project Characteristic | Minimal | Research | Enterprise |
|----------------------|---------|----------|------------|
| Team Size | 1 | 1-5 | 5+ |
| Codebase Size | <1K lines | 1K-50K lines | 50K+ lines |
| Physics/Science Focus | No | Yes | Optional |
| QA Requirements | Basic | High | Critical |
| Compliance Needs | None | Academic | Regulatory |
| Multi-team Coordination | No | No | Yes |
| Budget/Token Constraints | Strict | Moderate | Flexible |
| **Claude Pro Usage** | **Light** | **Regular** | **Heavy/Max Plan** |

## Usage Examples

### Personal Project Context - IDEAL FOR HEAVY PRO USAGE
```bash
# Planning: Use minimal for basic task tracking
agent: agent-plan-manager-minimal

# Implementation: Use minimal for simple execution
agent: agent-plan-implementer-minimal

# Benefits: Ultra-low token usage, fast execution, simple workflow
# Perfect for prototypes and personal projects
# Claude Pro Optimized: ~500-600 total tokens, maximizes session capacity
# Session Strategy: Multiple short sessions, frequent checkpointing
```

### Research Context (SolarWindPy) - RECOMMENDED FOR PRO USERS
```bash
# Planning: Use streamlined for efficient planning
agent: agent-plan-manager

# Implementation: Use research-optimized version
agent: agent-plan-implementer

# Benefits: Physics validation, QA integration, performance monitoring
# Perfect for plasma physics calculations and scientific reproducibility
# Claude Pro Optimized: ~2,400-2,800 total tokens, ideal for regular usage
# Session Strategy: 2-3 hour focused sessions with checkpointing
```

### Enterprise Context - REQUIRES MAX PLAN OR LIGHT USAGE
```bash
# Planning: Use comprehensive for detailed guidance
agent: agent-plan-manager

# Implementation: Use full enterprise version
agent: agent-plan-implementer-full

# Benefits: Multi-team coordination, compliance tracking, advanced error recovery
# Essential for regulated industries and large-scale development
# Claude Pro Consideration: ~6,000+ total tokens, requires Max Plan or light usage
# Session Strategy: Long planning sessions, enterprise Max Plan recommended
```

### Prototype Context - MAXIMUM PRO EFFICIENCY
```bash
# Planning: Use minimal for basic planning
agent: agent-plan-manager-minimal

# Implementation: Use minimal lightweight version  
agent: agent-plan-implementer-minimal

# Benefits: Fast execution, low token usage, simple workflow
# Perfect for quick experiments and personal projects
# Claude Pro Optimized: ~500-600 total tokens, maximum message capacity
# Session Strategy: Rapid iteration, minimal context overhead
```

## Migration Between Variants

### Upgrading from Minimal → Research
**When:** Project grows in complexity, adds team members, requires QA
**Considerations:** Add physics validation, set up testing infrastructure, implement performance monitoring

### Upgrading from Research → Enterprise
**When:** Multi-team coordination needed, compliance requirements, regulatory oversight
**Considerations:** Implement approval workflows, set up stakeholder reporting, add audit procedures

### Downgrading Enterprise → Research
**When:** Simplifying workflows, reducing overhead, focusing on core functionality
**Considerations:** Remove compliance procedures, simplify coordination, focus on scientific validation

### Downgrading Research → Minimal
**When:** Simplifying for prototypes, reducing token usage, single-developer focus
**Considerations:** Remove automated QA, eliminate specialist coordination, keep basic functionality

## Claude Pro Usage Pattern Guidelines

### Usage Limit Context (2025)
- **Pro Plan**: 40-80 hours Sonnet 4 weekly, 5-hour cycles, ~45 messages per cycle
- **Session Length**: Optimize for 2-4 hour focused sessions
- **Context Window**: 200K tokens max, larger conversations reduce message capacity
- **Multi-Session**: Plan complex work across multiple sessions with checkpointing

### Variant Selection by Usage Pattern

#### Light Usage (< 20 hours/week)
**Recommended:** Any variant, optimize for functionality over efficiency
- **Planning:** Comprehensive or Streamlined for full features
- **Implementation:** Research or Enterprise for complete capabilities
- **Strategy:** Maximize functionality, minimal usage concern

#### Regular Usage (20-40 hours/week)  
**Recommended:** Streamlined + Research combination
- **Planning:** Streamlined (~1,000 tokens) for efficient planning
- **Implementation:** Research (~1,400-1,800 tokens) for scientific needs
- **Strategy:** Balance functionality with efficiency

#### Heavy Usage (40+ hours/week)
**Recommended:** Minimal variants or Max Plan upgrade
- **Planning:** Minimal (~300 tokens) for basic planning
- **Implementation:** Minimal (~200-300 tokens) for lightweight execution
- **Strategy:** Maximize session efficiency, consider Max Plan

### Session Management by Usage Pattern
```
Light Usage Pattern:
- Use comprehensive variants without concern
- Long planning sessions acceptable
- Single-session plan completion possible

Regular Usage Pattern (RECOMMENDED):
- Use streamlined + research combination
- Plan 2-3 hour focused sessions
- Checkpoint at natural boundaries
- Multi-session complex implementations

Heavy Usage Pattern:
- Use minimal variants exclusively
- Plan 1-2 hour focused sessions
- Frequent checkpointing required
- Consider Max Plan upgrade for complex work
```

## Token Efficiency Analysis

### Plan Manager Variants
| Variant | Token Range | Efficiency Rating | Use Case Fit | **Pro Usage Fit** |
|---------|-------------|------------------|--------------|-------------------|
| Minimal | ~300 | ⭐⭐⭐⭐⭐ | Simple projects | **Heavy usage** |
| Streamlined | ~1,000 | ⭐⭐⭐⭐ | Regular development | **Regular usage** |
| Comprehensive | ~3,000 | ⭐⭐⭐ | Complex projects | **Light usage** |

### Plan Implementer Variants  
| Variant | Token Range | Efficiency Rating | Use Case Fit | **Pro Usage Fit** |
|---------|-------------|------------------|--------------|-------------------|
| Minimal | 200-300 | ⭐⭐⭐⭐⭐ | Simple projects | **Heavy usage** |
| Research | 1,400-1,800 | ⭐⭐⭐⭐ | Scientific software | **Regular usage** |
| Enterprise | 2,800-3,200 | ⭐⭐⭐ | Large organizations | **Light usage** |

## Future Enhancements

### Planned Variants
- **agent-plan-implementer-classroom.md**: Educational environments with learning scaffolding
- **agent-plan-implementer-open-source.md**: Open source project coordination with community features
- **agent-plan-implementer-ci.md**: CI/CD optimized with pipeline integration

### Configuration-Based Loading (Future)
Eventually, we may implement dynamic loading where a single agent loads different capability modules based on project configuration:

```json
{
  "implementer_config": {
    "base": "research",
    "extensions": ["qa_integration", "performance_monitoring"],
    "excludes": ["enterprise_workflows", "multi_team_coordination"]
  }
}
```

## Best Practices

### Variant Selection
1. **Start conservative**: Begin with minimal, upgrade as needed
2. **Match context**: Scientific projects → research, enterprise → full
3. **Consider constraints**: Token budgets, team size, complexity
4. **Plan evolution**: Design for easy migration between variants

### Implementation Guidelines
1. **Document choice**: Record why specific variant was selected
2. **Monitor fit**: Regularly assess if variant still matches project needs
3. **Upgrade triggers**: Define criteria for moving to more capable variant
4. **Team training**: Ensure team understands variant capabilities and limitations

This guide ensures optimal agent selection for maximum productivity while maintaining appropriate capability levels for each development context.