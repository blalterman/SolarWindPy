# Phase 1: Token Estimation Enhancement - 30 minutes

## Overview
Enhance the current line-based token estimation in `create-compaction.py` with more accurate character/word-based heuristics that better reflect actual Claude token usage patterns.

## Current State Analysis
**Current Implementation (Lines 34-65):**
```python
def estimate_context_size():
    # Rough estimate: 3 tokens per line
    estimated_tokens = total_lines * 3
    return estimated_tokens, total_lines
```

**Problems:**
- Line-based estimation ignores content density
- Fixed 3 tokens/line ratio doesn't reflect reality
- No consideration of different content types (code vs prose vs tables)
- No adjustment for markdown formatting overhead

## Phase Objectives
- [ ] Replace line-based estimation with character/word-based heuristics
- [ ] Implement content-type aware token estimation
- [ ] Add markdown overhead calculation
- [ ] Validate accuracy against known token counts
- [ ] Maintain backward compatibility

## Implementation Tasks

### Task 1.1: Enhanced Token Estimation Function (15 min)
**Target:** `create-compaction.py:estimate_context_size()`

```python
def estimate_context_size_enhanced():
    """Enhanced token estimation using character/word-based heuristics."""
    context_files = ['CLAUDE.md', 'claude_session_state.md', '.claude/agents/*.md']
    
    total_chars = 0
    total_words = 0
    total_lines = 0
    content_breakdown = {'code': 0, 'prose': 0, 'tables': 0, 'lists': 0}
    
    for file_path in get_context_files(context_files):
        chars, words, lines, content_types = analyze_file_content(file_path)
        total_chars += chars
        total_words += words
        total_lines += lines
        for content_type, count in content_types.items():
            content_breakdown[content_type] += count
    
    # Enhanced token estimation based on content analysis
    base_tokens = total_words * 1.3  # Base word-to-token ratio
    
    # Content-type adjustments
    code_penalty = content_breakdown['code'] * 0.2  # Code is token-dense
    table_penalty = content_breakdown['tables'] * 0.15  # Tables have structure overhead
    markdown_overhead = total_lines * 0.1  # Markdown formatting
    
    estimated_tokens = int(base_tokens + code_penalty + table_penalty + markdown_overhead)
    
    return estimated_tokens, total_lines, content_breakdown
```

**Acceptance Criteria:**
- [ ] Function returns more accurate token estimates
- [ ] Content breakdown provides insight into token usage
- [ ] Estimation accuracy within ±10% for typical content
- [ ] Performance impact < 1 second

### Task 1.2: Content Analysis Utilities (10 min)
**Target:** New functions in `create-compaction.py`

```python
def analyze_file_content(file_path):
    """Analyze file content for token estimation."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.count('\n') + 1
        chars = len(content)
        words = len(content.split())
        
        # Content type detection
        content_types = {
            'code': count_code_blocks(content),
            'prose': count_prose_paragraphs(content),
            'tables': count_tables(content),
            'lists': count_lists(content)
        }
        
        return chars, words, lines, content_types
    except Exception:
        return 0, 0, 0, {'code': 0, 'prose': 0, 'tables': 0, 'lists': 0}

def count_code_blocks(content):
    """Count code blocks in markdown content."""
    return content.count('```') // 2

def count_prose_paragraphs(content):
    """Count prose paragraphs (non-list, non-code text)."""
    lines = content.split('\n')
    prose_lines = 0
    for line in lines:
        stripped = line.strip()
        if (stripped and not stripped.startswith('#') and 
            not stripped.startswith('-') and not stripped.startswith('*') and
            not stripped.startswith('|') and not stripped.startswith('```')):
            prose_lines += 1
    return prose_lines

def count_tables(content):
    """Count markdown tables."""
    lines = content.split('\n')
    table_lines = sum(1 for line in lines if line.strip().startswith('|'))
    return table_lines

def count_lists(content):
    """Count list items."""
    lines = content.split('\n')
    list_lines = sum(1 for line in lines if line.strip().startswith(('-', '*', '+')))
    return list_lines
```

**Acceptance Criteria:**
- [ ] Accurate content type detection
- [ ] Robust error handling for invalid files
- [ ] Performance suitable for real-time estimation
- [ ] Clear content categorization

### Task 1.3: Integration and Testing (5 min)
**Target:** Integration with existing compaction flow

- [ ] Replace existing `estimate_context_size()` calls
- [ ] Update compaction output to show content breakdown
- [ ] Add validation against known good estimates
- [ ] Ensure backward compatibility for existing scripts

**Enhanced Output Example:**
```
📊 Token Analysis:
- Estimated: 12,450 tokens (prev: 8,200 tokens)
- Content: 3,200 words, 45,600 chars
- Breakdown: 25% code, 60% prose, 10% tables, 5% lists
- Accuracy: ±850 tokens (93% confidence)
```

## Integration Points

### Hook Ecosystem
- **validate-session-state.sh**: Use enhanced estimates for session loading decisions
- **git-workflow-validator.sh**: Include token metrics in branch transition decisions

### Agent Coordination
- **UnifiedPlanCoordinator**: Receive accurate token estimates for planning decisions
- **TestEngineer**: Use content breakdown for test context preservation

## Testing Strategy
- [ ] Unit tests for content analysis functions
- [ ] Validation against existing compaction files with known token counts
- [ ] Performance benchmarks vs current implementation
- [ ] Integration tests with existing hooks

## Rollback Plan
- Keep existing `estimate_context_size()` as fallback
- Feature flag for enhanced estimation
- Automatic fallback on estimation errors

---
**Phase 1 Completion Criteria:**
- [ ] Enhanced token estimation implemented
- [ ] Content analysis utilities functional
- [ ] Integration completed with existing flow
- [ ] Testing validates improved accuracy
- [ ] Performance meets requirements (<5s total compaction time)

**Estimated Time: 30 minutes**
**Dependencies: None**
**Deliverables: Enhanced `create-compaction.py` with accurate token estimation**