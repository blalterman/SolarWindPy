#!/usr/bin/env python3
"""
Compaction Creation Hook for SolarWindPy
Creates structured compaction preserving plan state at token boundaries.
"""

import sys
import os
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def get_git_info():
    """Get current git branch and recent commits."""
    try:
        branch = subprocess.check_output(['git', 'branch', '--show-current'], 
                                       text=True).strip()
        
        # Get recent commits
        commits = subprocess.check_output(['git', 'log', '--oneline', '-5'], 
                                        text=True).strip()
        
        # Get current status
        status = subprocess.check_output(['git', 'status', '--short'], 
                                       text=True).strip()
        
        return branch, commits, status
    except subprocess.CalledProcessError:
        return "unknown", "", ""


def estimate_context_size():
    """Estimate current context token usage."""
    
    context_files = [
        'CLAUDE.md',
        'claude_session_state.md',
        '.claude/agents/*.md'
    ]
    
    total_lines = 0
    for pattern in context_files:
        if '*' in pattern:
            # Handle glob patterns
            directory = Path(pattern).parent
            file_pattern = Path(pattern).name
            try:
                for file_path in directory.glob(file_pattern):
                    if file_path.is_file():
                        with open(file_path, 'r') as f:
                            total_lines += len(f.readlines())
            except:
                pass
        else:
            try:
                with open(pattern, 'r') as f:
                    total_lines += len(f.readlines())
            except:
                pass
    
    # Rough estimate: 3 tokens per line
    estimated_tokens = total_lines * 3
    return estimated_tokens, total_lines


def find_active_plan():
    """Find the currently active plan directory."""
    branch, _, _ = get_git_info()
    
    if branch.startswith('plan/'):
        plan_name = branch[5:]  # Remove 'plan/' prefix
        plan_dir = Path(f'plans/{plan_name}')
        if plan_dir.exists():
            return plan_name, plan_dir
    
    # Fallback: look for most recent plan
    plans_dir = Path('plans')
    if plans_dir.exists():
        for item in plans_dir.iterdir():
            if item.is_dir() and item.name != 'completed':
                return item.name, item
    
    return None, None


def create_compaction():
    """Create a compacted state file for the current session."""
    
    print("🗜️  Creating compaction at token boundary...")
    
    # Get current state
    branch, commits, status = get_git_info()
    tokens, lines = estimate_context_size()
    plan_name, plan_dir = find_active_plan()
    
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Determine compaction target
    if tokens > 15000:
        target = "high (40-60% reduction)"
        target_tokens = int(tokens * 0.5)
    elif tokens > 8000:
        target = "medium (30-50% reduction)"
        target_tokens = int(tokens * 0.65)
    else:
        target = "light (maintain efficiency)"
        target_tokens = tokens
    
    compaction_content = f"""# Compacted Context State - {timestamp}

## Compaction Metadata
- **Timestamp**: {timestamp}
- **Branch**: {branch}
- **Plan**: {plan_name or 'No active plan'}
- **Pre-Compaction Context**: ~{tokens:,} tokens ({lines:,} lines)
- **Target Compression**: {target}
- **Target Tokens**: ~{target_tokens:,} tokens

## Git State
### Current Branch: {branch}
### Recent Commits:
```
{commits}
```

### Working Directory Status:
```
{status if status else 'Clean working directory'}
```

## Session Context Summary
"""

    # Add plan-specific context if available
    if plan_dir and plan_dir.exists():
        overview_file = plan_dir / '0-Overview.md'
        if overview_file.exists():
            try:
                with open(overview_file, 'r') as f:
                    overview_content = f.read()
                
                # Extract key metadata
                metadata_match = None
                if '## Plan Metadata' in overview_content:
                    metadata_start = overview_content.find('## Plan Metadata')
                    metadata_end = overview_content.find('\n## ', metadata_start + 1)
                    if metadata_end == -1:
                        metadata_end = len(overview_content)
                    metadata_section = overview_content[metadata_start:metadata_end]
                    
                    compaction_content += f"""
### Active Plan: {plan_name}
{metadata_section}

### Plan Progress Summary
- Plan directory: {plan_dir}
- Last modified: {datetime.fromtimestamp(overview_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M')}
"""
            except Exception as e:
                compaction_content += f"\\n### Plan Status: Could not read overview ({e})"
    
    # Add session resumption instructions
    compaction_content += f"""
## Resumption Instructions
### Next Session Priorities
1. **Context Recovery**: Load this compacted state
2. **Branch Validation**: Ensure correct branch ({branch})
3. **Plan Continuation**: {"Resume " + plan_name if plan_name else "Identify or create plan"}

### Quick Actions Available
- Continue current work on {branch}
- Review plan status in {plan_dir if plan_dir else 'plans/'}
- Check for uncommitted changes

### Token Budget
- Pre-compaction: {tokens:,} tokens
- Target: {target_tokens:,} tokens  
- Savings: {tokens - target_tokens:,} tokens ({((tokens - target_tokens) / tokens * 100):.1f}%)

---
*Automated compaction at token boundary - {timestamp}*
"""

    # Write compaction file
    compaction_file = Path('.claude/compacted_state.md')
    with open(compaction_file, 'w') as f:
        f.write(compaction_content)
    
    # Also write to plan directory if available
    if plan_dir:
        plan_compaction = plan_dir / 'compacted_state.md'
        with open(plan_compaction, 'w') as f:
            f.write(compaction_content)
        print(f"✅ Compaction saved to: {plan_compaction}")
    
    print(f"✅ Compaction created: {compaction_file}")
    print(f"📊 Token reduction: {tokens:,} → {target_tokens:,} ({((tokens - target_tokens) / tokens * 100):.1f}% savings)")


def main():
    """Main entry point for compaction hook."""
    
    # Check if we're in a git repository
    if not Path('.git').exists():
        print("⚠️  Not in a git repository, skipping compaction")
        return
    
    print("🔍 Compaction hook triggered")
    create_compaction()


if __name__ == "__main__":
    main()