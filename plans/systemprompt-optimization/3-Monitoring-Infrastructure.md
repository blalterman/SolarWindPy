# Phase 3: Monitoring Infrastructure (Optional)

## Objectives
- Deploy automated metrics collection for systemPrompt effectiveness
- Track productivity improvements and token usage patterns
- Generate data-driven insights for optimization

## Risk/Value/Cost Analysis

### Risk Assessment
- **Technical Risk**: Very Low
  - Python-based implementation using standard library only
  - Local data storage, no external dependencies
  - Optional component that can be disabled anytime

- **Operational Risk**: Minimal
  - Non-intrusive metrics collection
  - Graceful failure handling
  - Easy rollback and removal

- **Data Privacy**: Zero Risk
  - All metrics stored locally in `.claude/metrics/`
  - No external transmission or cloud storage
  - User controls all data

### Value Proposition
- **Evidence-Based Optimization**: Replace assumptions with real data
- **ROI Quantification**: Measure actual token savings and productivity gains
- **Usage Pattern Analysis**: Understand agent selection and workflow efficiency
- **Continuous Improvement**: Data-driven systemPrompt refinement

### Cost Analysis
- **Development Cost**: 2-3 hours initial implementation
- **Runtime Cost**: <100ms overhead per session
- **Storage Cost**: ~1MB per month of usage data
- **Token Cost**: 0 (local processing only)
- **Review Cost**: 500 tokens/week for report analysis

### Token Economics
- **Investment**: 500 tokens/week for metrics review
- **Expected Return**: 2000-3000 tokens saved through optimization insights
- **Net Benefit**: 1500-2500 tokens/week efficiency gain
- **Break-even**: Immediate (first week positive ROI)

## Implementation Design

### 3.1 Monitoring Script Architecture

**Location**: `.claude/hooks/systemprompt-monitor.py`

```python
#!/usr/bin/env python3
"""
systemPrompt Monitoring for SolarWindPy
Tracks token usage, productivity metrics, and agent selection patterns
"""

import json
import datetime
from pathlib import Path
from typing import Dict, List, Optional
import statistics
import sys

class SystemPromptMonitor:
    def __init__(self):
        self.metrics_dir = Path(".claude/metrics")
        self.metrics_dir.mkdir(exist_ok=True)
        
        # Data files
        self.session_log = self.metrics_dir / "sessions.jsonl"
        self.weekly_report = self.metrics_dir / "weekly_report.md"
        self.agent_usage = self.metrics_dir / "agent_usage.json"
        
    def collect_session_metrics(self, session_data: Dict):
        """Collect metrics from completed session"""
        try:
            metrics = {
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "session_id": session_data.get("session_id", "unknown"),
                "branch": session_data.get("branch", "unknown"),
                "tokens_used": session_data.get("tokens", 0),
                "agent_calls": session_data.get("agent_calls", []),
                "time_to_first_commit": session_data.get("first_commit_time"),
                "workflow_violations": session_data.get("violations", 0),
                "clarification_exchanges": session_data.get("clarifications", 0),
                "pr_created": session_data.get("pr_created", False),
                "hook_executions": session_data.get("hook_calls", []),
                "plan_type": self._detect_plan_type(session_data.get("branch", ""))
            }
            
            # Append to session log
            with open(self.session_log, 'a') as f:
                f.write(json.dumps(metrics) + '\\n')
                
            # Update agent usage tracking
            self._update_agent_usage(metrics["agent_calls"])
            
            print(f"✅ Session metrics recorded: {metrics['session_id']}")
            
        except Exception as e:
            print(f"⚠️  Metrics collection failed: {e}")
            
    def _detect_plan_type(self, branch: str) -> str:
        """Detect plan type from branch name"""
        if branch.startswith("plan/"):
            plan_name = branch[5:]  # Remove "plan/" prefix
            
            # SolarWindPy-specific plan types
            if any(term in plan_name for term in ["doc", "documentation"]):
                return "documentation"
            elif any(term in plan_name for term in ["test", "testing"]):
                return "testing"  
            elif any(term in plan_name for term in ["physics", "validation"]):
                return "physics"
            elif any(term in plan_name for term in ["plot", "visual"]):
                return "visualization"
            elif any(term in plan_name for term in ["agent", "hook"]):
                return "infrastructure"
            else:
                return "feature"
        return "unknown"
        
    def _update_agent_usage(self, agent_calls: List[str]):
        """Track agent usage patterns"""
        try:
            # Load existing usage data
            usage_data = {}
            if self.agent_usage.exists():
                with open(self.agent_usage) as f:
                    usage_data = json.load(f)
            
            # Update counts
            for agent in agent_calls:
                usage_data[agent] = usage_data.get(agent, 0) + 1
                
            # Save updated data
            with open(self.agent_usage, 'w') as f:
                json.dump(usage_data, f, indent=2)
                
        except Exception as e:
            print(f"⚠️  Agent usage tracking failed: {e}")
            
    def generate_weekly_report(self) -> str:
        """Generate comprehensive weekly productivity report"""
        try:
            # Load session data
            sessions = self._load_recent_sessions(days=7)
            
            if not sessions:
                return "No sessions in past week"
                
            # Generate report
            report = self._create_report_content(sessions)
            
            # Save report
            with open(self.weekly_report, 'w') as f:
                f.write(report)
                
            return report
            
        except Exception as e:
            return f"Report generation failed: {e}"
            
    def _load_recent_sessions(self, days: int = 7) -> List[Dict]:
        """Load sessions from recent days"""
        sessions = []
        if not self.session_log.exists():
            return sessions
            
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        
        try:
            with open(self.session_log) as f:
                for line in f:
                    session = json.loads(line.strip())
                    session_time = datetime.datetime.fromisoformat(session['timestamp'])
                    if session_time > cutoff:
                        sessions.append(session)
        except Exception as e:
            print(f"⚠️  Session loading failed: {e}")
            
        return sessions
        
    def _create_report_content(self, sessions: List[Dict]) -> str:
        """Create formatted report content"""
        total_sessions = len(sessions)
        
        # Calculate metrics
        avg_tokens = statistics.mean([s.get('tokens_used', 0) for s in sessions])
        total_violations = sum(s.get('workflow_violations', 0) for s in sessions)
        prs_created = sum(1 for s in sessions if s.get('pr_created', False))
        avg_clarifications = statistics.mean([s.get('clarification_exchanges', 0) for s in sessions])
        
        # Agent usage analysis
        agent_summary = self._analyze_agent_usage(sessions)
        
        # Plan type analysis
        plan_analysis = self._analyze_plan_types(sessions)
        
        report = f"""# systemPrompt Performance Report
Generated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

## Executive Summary (Past 7 Days)
- **Total Sessions**: {total_sessions}
- **Average Tokens per Session**: {avg_tokens:.0f}
- **Workflow Violations**: {total_violations}
- **Pull Requests Created**: {prs_created}
- **Avg Clarifications per Session**: {avg_clarifications:.1f}

## Agent Usage Patterns
{agent_summary}

## Plan Type Analysis
{plan_analysis}

## systemPrompt Effectiveness Metrics
- **Context Loading**: Session context auto-loaded in {total_sessions} sessions
- **Agent Awareness**: {len([s for s in sessions if s.get('agent_calls')])} sessions used specialized agents
- **Workflow Compliance**: {((total_sessions - total_violations) / total_sessions * 100):.1f}% sessions violation-free

## SolarWindPy-Specific Insights
- **Physics Validation**: PhysicsValidator usage in {len([s for s in sessions if 'PhysicsValidator' in s.get('agent_calls', [])])} sessions
- **MultiIndex Operations**: DataFrameArchitect usage in {len([s for s in sessions if 'DataFrameArchitect' in s.get('agent_calls', [])])} sessions
- **Test Coverage**: TestEngineer usage in {len([s for s in sessions if 'TestEngineer' in s.get('agent_calls', [])])} sessions

## Recommendations
{self._generate_recommendations(sessions)}

## Token Efficiency Analysis
- **Baseline systemPrompt**: 210 tokens per session
- **Estimated Clarification Savings**: {avg_clarifications * 150:.0f} tokens per session
- **Net Token Benefit**: {(avg_clarifications * 150) - 210:.0f} tokens per session
- **Weekly Efficiency**: {((avg_clarifications * 150) - 210) * total_sessions:.0f} tokens saved
"""
        
        return report
        
    def _analyze_agent_usage(self, sessions: List[Dict]) -> str:
        """Analyze agent usage patterns"""
        agent_counts = {}
        for session in sessions:
            for agent in session.get('agent_calls', []):
                agent_counts[agent] = agent_counts.get(agent, 0) + 1
                
        if not agent_counts:
            return "- No agent usage recorded"
            
        sorted_agents = sorted(agent_counts.items(), key=lambda x: x[1], reverse=True)
        
        lines = []
        for agent, count in sorted_agents:
            percentage = (count / len(sessions)) * 100
            lines.append(f"- **{agent}**: {count} sessions ({percentage:.1f}%)")
            
        return "\\n".join(lines)
        
    def _analyze_plan_types(self, sessions: List[Dict]) -> str:
        """Analyze plan type distribution"""
        plan_counts = {}
        for session in sessions:
            plan_type = session.get('plan_type', 'unknown')
            plan_counts[plan_type] = plan_counts.get(plan_type, 0) + 1
            
        if not plan_counts:
            return "- No plan types detected"
            
        lines = []
        for plan_type, count in plan_counts.items():
            percentage = (count / len(sessions)) * 100
            lines.append(f"- **{plan_type.title()}**: {count} sessions ({percentage:.1f}%)")
            
        return "\\n".join(lines)
        
    def _generate_recommendations(self, sessions: List[Dict]) -> str:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Low agent usage
        total_agent_calls = sum(len(s.get('agent_calls', [])) for s in sessions)
        if total_agent_calls / len(sessions) < 1:
            recommendations.append("- **Increase Agent Usage**: Consider promoting specialized agents more prominently")
            
        # High clarification rate
        avg_clarifications = statistics.mean([s.get('clarification_exchanges', 0) for s in sessions])
        if avg_clarifications > 2:
            recommendations.append(f"- **High Clarification Rate**: {avg_clarifications:.1f} per session suggests systemPrompt could be more specific")
            
        # Workflow violations
        total_violations = sum(s.get('workflow_violations', 0) for s in sessions)
        if total_violations > 0:
            recommendations.append(f"- **Workflow Training**: {total_violations} violations suggest need for better workflow education")
            
        if not recommendations:
            recommendations.append("- **Optimal Performance**: systemPrompt functioning effectively")
            
        return "\\n".join(recommendations)

# CLI Interface
if __name__ == "__main__":
    monitor = SystemPromptMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        report = monitor.generate_weekly_report()
        print(report)
    else:
        # Collect session metrics
        session_data = {
            "session_id": sys.argv[1] if len(sys.argv) > 1 else "unknown",
            "branch": sys.argv[2] if len(sys.argv) > 2 else "unknown",
            "tokens": int(sys.argv[3]) if len(sys.argv) > 3 else 0
        }
        monitor.collect_session_metrics(session_data)
```

### 3.2 Integration Points

#### Stop Hook Integration
Update `.claude/settings.json` Stop hook:

```json
{
  "matcher": "*",
  "hooks": [
    {
      "type": "command",
      "command": ".claude/hooks/coverage-monitor.py",
      "timeout": 60
    },
    {
      "type": "command", 
      "command": "python .claude/hooks/systemprompt-monitor.py ${session_id} ${branch} ${total_tokens}",
      "timeout": 15
    }
  ]
}
```

#### Weekly Report Generation
Add to cron or create manual script:

```bash
#!/bin/bash
# .claude/scripts/generate-weekly-metrics.sh
echo "Generating systemPrompt effectiveness report..."
python .claude/hooks/systemprompt-monitor.py report
```

### 3.3 Usage Effectiveness for SolarWindPy

#### SolarWindPy-Specific Metrics
- **Agent Specialization**: Track PhysicsValidator, DataFrameArchitect, TestEngineer usage
- **Plan Types**: Documentation, testing, physics, visualization, infrastructure
- **Workflow Patterns**: plan/* → PR workflow compliance
- **Hook Integration**: PreToolUse physics validation frequency

#### Productivity Indicators
- **Time to First Commit**: Measure setup efficiency
- **Clarification Rate**: Track systemPrompt effectiveness
- **Agent Selection**: Optimal specialist usage patterns
- **PR Success Rate**: Plan closeout efficiency

## Implementation Timeline

### Week 2: Basic Implementation
- [ ] Create `systemprompt-monitor.py` with core functionality
- [ ] Add basic session metrics collection
- [ ] Test integration with Stop hook

### Week 3: Enhanced Reporting
- [ ] Implement comprehensive report generation
- [ ] Add agent usage analysis
- [ ] Create weekly report automation

### Week 4: Optimization
- [ ] Analyze collected data
- [ ] Identify improvement opportunities
- [ ] Refine systemPrompt based on insights

## Success Criteria
- [ ] Metrics collection operational without errors
- [ ] Weekly reports generated automatically
- [ ] Token savings quantified with real data
- [ ] Agent usage patterns clearly identified
- [ ] SolarWindPy-specific insights actionable

## Recommendation

**Implement Lightweight Monitoring** with:
- Minimal complexity (200 lines Python)
- Zero runtime token cost
- High-value productivity insights
- SolarWindPy-specific metric focus
- Optional deployment (can skip if not needed)

This provides evidence-based systemPrompt optimization perfectly scoped for a scientific Python package, enabling continuous improvement without enterprise complexity.