# Phase 3: Git Integration & Enhanced Metadata - 30 minutes

## Overview
Strengthen git integration with better tagging, enhanced metadata tracking, and improved coordination with the git-workflow-validator.sh hook for comprehensive session and plan state management.

## Current State Analysis
**Current Implementation (Lines 15-31, 94-99):**
```python
def get_git_info():
    branch = subprocess.check_output(['git', 'branch', '--show-current'])
    commits = subprocess.check_output(['git', 'log', '--oneline', '-5'])
    status = subprocess.check_output(['git', 'status', '--short'])
    return branch, commits, status

# Simple timestamp in compaction
timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
```

**Problems:**
- Basic git information capture without context
- No integration with git-workflow-validator.sh metrics
- Missing git tagging for compaction points
- No branch relationship tracking
- Limited metadata for session reconstruction

## Phase Objectives
- [ ] Enhance git information collection
- [ ] Implement git tagging for compaction milestones
- [ ] Integrate with git-workflow-validator.sh metrics
- [ ] Add branch relationship tracking
- [ ] Create comprehensive metadata structure

## Implementation Tasks

### Task 3.1: Enhanced Git Information Collection (15 min)
**Target:** Enhanced `get_git_info()` and new git utilities

```python
def get_enhanced_git_info():
    """Collect comprehensive git information for compaction."""
    try:
        # Basic information
        branch = subprocess.check_output(['git', 'branch', '--show-current'], text=True).strip()
        commits = subprocess.check_output(['git', 'log', '--oneline', '-5'], text=True).strip()
        status = subprocess.check_output(['git', 'status', '--short'], text=True).strip()
        
        # Enhanced information
        branch_info = get_branch_relationship_info(branch)
        recent_activity = get_recent_activity_summary()
        metrics_info = load_git_workflow_metrics()
        
        return {
            'branch': branch,
            'commits': commits,
            'status': status,
            'branch_info': branch_info,
            'recent_activity': recent_activity,
            'metrics': metrics_info
        }
    except subprocess.CalledProcessError as e:
        return create_fallback_git_info(str(e))

def get_branch_relationship_info(current_branch):
    """Get branch relationship and tracking information."""
    info = {'type': 'unknown', 'parent': 'unknown', 'tracking': None}
    
    try:
        # Determine branch type
        if current_branch.startswith('plan/'):
            info['type'] = 'plan'
            info['plan_name'] = current_branch[5:]
        elif current_branch.startswith('feature/'):
            info['type'] = 'feature'
            info['feature_name'] = current_branch[8:]
            # Look for corresponding plan branch
            plan_branch = f"plan/{current_branch[8:]}"
            if branch_exists(plan_branch):
                info['parent'] = plan_branch
        elif current_branch == 'master':
            info['type'] = 'master'
        
        # Get tracking information
        try:
            tracking = subprocess.check_output(
                ['git', 'rev-parse', '--abbrev-ref', f'{current_branch}@{{upstream}}'],
                text=True, stderr=subprocess.DEVNULL
            ).strip()
            info['tracking'] = tracking
        except subprocess.CalledProcessError:
            info['tracking'] = None
        
        # Get ahead/behind information
        if info['tracking']:
            try:
                ahead_behind = subprocess.check_output(
                    ['git', 'rev-list', '--left-right', '--count', f'{info["tracking"]}...HEAD'],
                    text=True
                ).strip().split('\t')
                info['behind'] = int(ahead_behind[0])
                info['ahead'] = int(ahead_behind[1])
            except (subprocess.CalledProcessError, ValueError, IndexError):
                info['behind'] = 0
                info['ahead'] = 0
        
        return info
    except Exception as e:
        return {'type': 'unknown', 'error': str(e)}

def get_recent_activity_summary():
    """Get summary of recent git activity."""
    try:
        # Get commits from last 24 hours
        since_yesterday = subprocess.check_output([
            'git', 'log', '--since="24 hours ago"', '--oneline'
        ], text=True).strip()
        
        # Get modified files in recent commits
        recent_files = subprocess.check_output([
            'git', 'diff', '--name-only', 'HEAD~3..HEAD'
        ], text=True).strip()
        
        return {
            'commits_24h': len(since_yesterday.split('\n')) if since_yesterday else 0,
            'recent_files': recent_files.split('\n') if recent_files else [],
            'last_commit_time': get_last_commit_time()
        }
    except subprocess.CalledProcessError:
        return {'commits_24h': 0, 'recent_files': [], 'last_commit_time': None}

def load_git_workflow_metrics():
    """Load metrics from git-workflow-validator.sh."""
    metrics_file = Path('.claude/velocity-metrics.log')
    if not metrics_file.exists():
        return {'plans_completed': 0, 'avg_commits_per_plan': 0, 'recent_plans': []}
    
    try:
        with open(metrics_file, 'r') as f:
            lines = f.readlines()
        
        recent_plans = []
        for line in lines[-10:]:  # Last 10 entries
            parts = line.strip().split(',')
            if len(parts) >= 4:
                recent_plans.append({
                    'timestamp': parts[0],
                    'plan_name': parts[1],
                    'action': parts[2],
                    'commit_count': parts[3]
                })
        
        return {
            'total_entries': len(lines),
            'recent_plans': recent_plans,
            'plans_completed': len([p for p in recent_plans if p['action'] == 'merge'])
        }
    except Exception:
        return {'error': 'Could not load metrics'}
```

**Acceptance Criteria:**
- [ ] Comprehensive git information collection
- [ ] Branch relationship tracking
- [ ] Integration with git-workflow-validator.sh metrics
- [ ] Robust error handling

### Task 3.2: Git Tagging and Milestones (10 min)
**Target:** Git tagging system for compaction milestones

```python
def create_compaction_git_tag(git_info, compression_plan):
    """Create git tag for compaction milestone."""
    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        tag_name = f"compaction/{git_info['branch']}/{timestamp}"
        
        # Create tag with metadata
        tag_message = create_tag_message(git_info, compression_plan)
        
        subprocess.run([
            'git', 'tag', '-a', tag_name, '-m', tag_message
        ], check=False)  # Don't fail compaction if tagging fails
        
        return tag_name
    except Exception as e:
        print(f"⚠️  Could not create git tag: {e}")
        return None

def create_tag_message(git_info, compression_plan):
    """Create comprehensive tag message for compaction."""
    return f"""Compaction Milestone - {git_info['branch']}

Branch: {git_info['branch']}
Type: {git_info['branch_info']['type']}
Token Reduction: {compression_plan.get('token_reduction', 'unknown')}
Methods: {', '.join(compression_plan.get('compression_methods', []))}
Plan: {git_info['branch_info'].get('plan_name', 'N/A')}

Commits included:
{git_info['commits']}

Tracking: {git_info['branch_info'].get('tracking', 'none')}
Ahead/Behind: +{git_info['branch_info'].get('ahead', 0)}/-{git_info['branch_info'].get('behind', 0)}

Automated compaction tag - preserves session state"""

def cleanup_old_compaction_tags():
    """Clean up old compaction tags (keep last 10)."""
    try:
        # Get all compaction tags
        tags_output = subprocess.check_output([
            'git', 'tag', '-l', 'compaction/*'
        ], text=True).strip()
        
        if not tags_output:
            return
        
        tags = tags_output.split('\n')
        if len(tags) > 10:
            # Remove oldest tags
            tags_to_remove = tags[:-10]
            for tag in tags_to_remove:
                subprocess.run(['git', 'tag', '-d', tag], check=False)
            print(f"🧹 Cleaned up {len(tags_to_remove)} old compaction tags")
    except Exception as e:
        print(f"⚠️  Could not cleanup old tags: {e}")
```

**Acceptance Criteria:**
- [ ] Git tags created for compaction milestones
- [ ] Comprehensive tag messages with metadata
- [ ] Automatic cleanup of old tags
- [ ] Non-blocking tag creation (doesn't fail compaction)

### Task 3.3: Enhanced Metadata Structure (5 min)
**Target:** Comprehensive metadata in compaction files

```python
def create_enhanced_compaction_metadata(git_info, compression_plan, tokens_before, tokens_after):
    """Create enhanced metadata section for compaction."""
    metadata = f"""## Enhanced Compaction Metadata
- **Timestamp**: {datetime.now(timezone.utc).isoformat()}
- **Git Tag**: {compression_plan.get('git_tag', 'none')}
- **Branch**: {git_info['branch']} ({git_info['branch_info']['type']})
- **Plan**: {git_info['branch_info'].get('plan_name', 'N/A')}
- **Tracking**: {git_info['branch_info'].get('tracking', 'none')}
- **Position**: +{git_info['branch_info'].get('ahead', 0)}/-{git_info['branch_info'].get('behind', 0)}

### Token Analysis
- **Pre-Compaction**: {tokens_before:,} tokens
- **Post-Compaction**: {tokens_after:,} tokens
- **Reduction**: {tokens_before - tokens_after:,} tokens ({((tokens_before - tokens_after) / tokens_before * 100):.1f}%)
- **Compression Methods**: {', '.join(compression_plan.get('compression_methods', ['none']))}

### Git Context
- **Recent Activity**: {git_info['recent_activity']['commits_24h']} commits in 24h
- **Modified Files**: {len(git_info['recent_activity']['recent_files'])} files recently changed
- **Last Commit**: {git_info['recent_activity'].get('last_commit_time', 'unknown')}

### Session Continuity
- **Critical Sections Preserved**: {len(compression_plan.get('preserve_sections', []))}
- **Restoration Confidence**: {compression_plan.get('restoration_confidence', 'high')}
- **Next Session Setup Time**: <2s estimated

### Workflow Integration
- **Hook Ecosystem**: Integrated with {len(get_active_hooks())} hooks
- **Agent Coordination**: Compatible with all 7 domain agents
- **Metrics Integration**: Linked to git-workflow-validator.sh tracking
"""
    return metadata
```

**Acceptance Criteria:**
- [ ] Comprehensive metadata structure
- [ ] Git integration information
- [ ] Session continuity details
- [ ] Workflow integration status

## Integration Points

### Hook Ecosystem
- **git-workflow-validator.sh**: Share metrics and branch information
- **validate-session-state.sh**: Use enhanced metadata for session restoration
- **pre-commit-tests.sh**: Coordinate with compaction timing

### Agent Coordination
- **UnifiedPlanCoordinator**: Receive comprehensive git context
- **All domain agents**: Access to branch relationship and workflow status

## Testing Strategy
- [ ] Unit tests for git information collection
- [ ] Integration tests with git-workflow-validator.sh
- [ ] Tag creation and cleanup validation
- [ ] Metadata structure verification

## Configuration
- [ ] Configurable tag retention (default: 10)
- [ ] Optional git tag creation
- [ ] Metadata verbosity levels

---
**Phase 3 Completion Criteria:**
- [ ] Enhanced git information collection implemented
- [ ] Git tagging system functional
- [ ] Integration with git-workflow-validator.sh established
- [ ] Comprehensive metadata structure created
- [ ] Testing validates git integration

**Estimated Time: 30 minutes**
**Dependencies: Phase 2 (Compression Intelligence)**
**Deliverables: Enhanced git integration in `create-compaction.py` with tagging and metadata**