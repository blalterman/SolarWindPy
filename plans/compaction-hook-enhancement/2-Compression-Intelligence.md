# Phase 2: Compression Intelligence - 45 minutes

## Overview
Implement content-aware compression strategies that intelligently reduce context size while preserving critical information for session continuity. Focus on semantic preservation rather than simple truncation.

## Current State Analysis
**Current Implementation (Lines 100-110):**
```python
if tokens > 15000:
    target = "high (40-60% reduction)"
    target_tokens = int(tokens * 0.5)
elif tokens > 8000:
    target = "medium (30-50% reduction)"
    target_tokens = int(tokens * 0.65)
else:
    target = "light (maintain efficiency)"
    target_tokens = tokens
```

**Problems:**
- Simple percentage-based reduction without content awareness
- No preservation of critical context elements
- No semantic understanding of what to compress vs preserve
- Manual targeting without adaptive intelligence

## Phase Objectives
- [ ] Implement content-aware compression strategies
- [ ] Add semantic preservation for critical context
- [ ] Create adaptive compression targeting
- [ ] Develop compression utility functions
- [ ] Integrate with enhanced token estimation

## Implementation Tasks

### Task 2.1: Compression Strategy Engine (20 min)
**Target:** New `CompactionStrategy` class in `create-compaction.py`

```python
class CompactionStrategy:
    """Intelligent compaction strategy based on content analysis."""
    
    def __init__(self, content_breakdown, total_tokens, target_reduction=0.4):
        self.content_breakdown = content_breakdown
        self.total_tokens = total_tokens
        self.target_reduction = target_reduction
        self.critical_patterns = [
            r'## Plan Metadata',
            r'### Phase \d+:',
            r'\[x\].*',  # Completed tasks
            r'- \[\s\].*in_progress',  # Active tasks
            r'git branch.*',
            r'Acceptance Criteria',
            r'Next Actions'
        ]
        
    def create_compression_plan(self):
        """Create intelligent compression plan."""
        plan = {
            'preserve_sections': self._identify_critical_sections(),
            'compress_sections': self._identify_compressible_sections(),
            'compression_methods': self._select_compression_methods(),
            'target_tokens': int(self.total_tokens * (1 - self.target_reduction))
        }
        return plan
    
    def _identify_critical_sections(self):
        """Identify sections that must be preserved."""
        return [
            'Plan Metadata',
            'Phase Overview with status',
            'Current git state',
            'Active tasks and progress',
            'Next Actions',
            'Acceptance Criteria',
            'Recent commits (last 3)',
            'Agent coordination points'
        ]
    
    def _identify_compressible_sections(self):
        """Identify sections suitable for compression."""
        return [
            'Completed task details',
            'Historical context beyond 1 week',
            'Verbose descriptions (keep summaries)',
            'Repeated documentation',
            'Example code (keep signatures)',
            'Long file listings',
            'Detailed error traces (keep summaries)'
        ]
    
    def _select_compression_methods(self):
        """Select appropriate compression methods."""
        methods = []
        
        if self.content_breakdown['code'] > 30:
            methods.append('compress_code_examples')
        if self.content_breakdown['prose'] > 50:
            methods.append('summarize_verbose_sections')
        if self.content_breakdown['lists'] > 20:
            methods.append('compact_lists')
        if self.content_breakdown['tables'] > 10:
            methods.append('optimize_tables')
            
        return methods
```

**Acceptance Criteria:**
- [ ] Intelligent section identification
- [ ] Adaptive compression method selection
- [ ] Configurable critical pattern preservation
- [ ] Content-type aware compression strategies

### Task 2.2: Compression Implementation Functions (15 min)
**Target:** New utility functions for actual content compression

```python
def apply_intelligent_compression(content, compression_plan):
    """Apply intelligent compression based on plan."""
    compressed_content = content
    
    for method in compression_plan['compression_methods']:
        if method == 'compress_code_examples':
            compressed_content = compress_code_examples(compressed_content)
        elif method == 'summarize_verbose_sections':
            compressed_content = summarize_verbose_sections(compressed_content)
        elif method == 'compact_lists':
            compressed_content = compact_lists(compressed_content)
        elif method == 'optimize_tables':
            compressed_content = optimize_tables(compressed_content)
    
    return compressed_content

def compress_code_examples(content):
    """Compress code examples while preserving signatures."""
    import re
    
    def compress_code_block(match):
        code = match.group(1)
        lines = code.split('\n')
        
        # Preserve function/class signatures and docstrings
        important_lines = []
        for line in lines:
            stripped = line.strip()
            if (stripped.startswith('def ') or stripped.startswith('class ') or
                stripped.startswith('"""') or stripped.startswith("'''") or
                stripped.startswith('#') or not stripped):
                important_lines.append(line)
            elif len(important_lines) < 10:  # Keep first 10 lines
                important_lines.append(line)
        
        if len(lines) > len(important_lines):
            important_lines.append(f'    # ... ({len(lines) - len(important_lines)} lines compressed)')
        
        return f'```\n{"\n".join(important_lines)}\n```'
    
    # Compress code blocks
    pattern = r'```(?:python|bash|\w+)?\n(.*?)\n```'
    return re.sub(pattern, compress_code_block, content, flags=re.DOTALL)

def summarize_verbose_sections(content):
    """Summarize verbose prose sections."""
    sections = content.split('\n## ')
    compressed_sections = []
    
    for section in sections:
        if len(section) > 1000:  # Long sections
            lines = section.split('\n')
            # Keep header and first 3 lines, summarize rest
            summary = '\n'.join(lines[:4])
            if len(lines) > 4:
                summary += f'\n\n*[{len(lines) - 4} additional lines summarized for compaction]*\n'
            compressed_sections.append(summary)
        else:
            compressed_sections.append(section)
    
    return '\n## '.join(compressed_sections)

def compact_lists(content):
    """Compact long lists while preserving structure."""
    import re
    
    def compact_list_block(match):
        list_content = match.group(0)
        lines = list_content.split('\n')
        
        if len(lines) > 10:
            # Keep first 5 and last 2 items
            kept_lines = lines[:5] + [f'   *[...{len(lines) - 7} items compacted...]*'] + lines[-2:]
            return '\n'.join(kept_lines)
        return list_content
    
    # Find list blocks
    pattern = r'(?:^[ ]*[-*+].*\n)+'
    return re.sub(pattern, compact_list_block, content, flags=re.MULTILINE)

def optimize_tables(content):
    """Optimize markdown tables for compaction."""
    import re
    
    def compress_table(match):
        table = match.group(0)
        lines = table.split('\n')
        
        if len(lines) > 8:  # Long tables
            # Keep header, separator, first 3 rows, and last row
            compressed = lines[:2] + lines[2:5] + [f'| ... | ({len(lines) - 6} rows) | ... |'] + lines[-1:]
            return '\n'.join(compressed)
        return table
    
    # Find table blocks
    pattern = r'(?:^\|.*\|\n)+'
    return re.sub(pattern, compress_table, content, flags=re.MULTILINE)
```

**Acceptance Criteria:**
- [ ] Code examples compressed while preserving key signatures
- [ ] Verbose sections summarized intelligently
- [ ] Lists compacted with structure preservation
- [ ] Tables optimized for space efficiency

### Task 2.3: Integration with Compaction Flow (10 min)
**Target:** Update main compaction creation function

```python
def create_compaction_with_intelligence():
    """Create intelligent compaction with content-aware compression."""
    # Get enhanced token estimation
    tokens, lines, content_breakdown = estimate_context_size_enhanced()
    
    # Determine compression strategy
    if tokens > 15000:
        target_reduction = 0.5
    elif tokens > 8000:
        target_reduction = 0.35
    else:
        target_reduction = 0.2
    
    # Create compression strategy
    strategy = CompactionStrategy(content_breakdown, tokens, target_reduction)
    compression_plan = strategy.create_compression_plan()
    
    # Apply intelligent compression to content
    raw_content = collect_session_content()
    compressed_content = apply_intelligent_compression(raw_content, compression_plan)
    
    # Create compaction with metadata
    final_content = create_compaction_content(compressed_content, compression_plan)
    
    return final_content, compression_plan
```

**Enhanced Compaction Output:**
```markdown
## Compression Analysis
- **Strategy**: Content-aware semantic preservation
- **Methods Applied**: compress_code_examples, summarize_verbose_sections
- **Critical Sections Preserved**: 8/8 (Plan Metadata, Phase Overview, Git State, Active Tasks)
- **Compression Ratio**: 12,450 → 7,200 tokens (42% reduction)
- **Semantic Preservation**: High (critical context maintained)
```

## Integration Points

### Hook Ecosystem
- **validate-session-state.sh**: Load compressed context with preserved structure
- **git-workflow-validator.sh**: Use compression metadata for branch decisions

### Agent Coordination
- **UnifiedPlanCoordinator**: Receive semantically preserved context
- **All domain agents**: Preserved critical patterns for their specializations

## Testing Strategy
- [ ] Unit tests for each compression method
- [ ] Integration tests with various content types
- [ ] Semantic preservation validation
- [ ] Performance benchmarks for compression operations

## Configuration
- [ ] Configurable critical patterns via `.claude/config/compaction-settings.json`
- [ ] Adjustable compression targets
- [ ] Method selection preferences

---
**Phase 2 Completion Criteria:**
- [ ] Intelligent compression strategies implemented
- [ ] Content-aware compression methods functional
- [ ] Semantic preservation validated
- [ ] Integration with enhanced token estimation
- [ ] Performance maintains <5s total compaction time

**Estimated Time: 45 minutes**
**Dependencies: Phase 1 (Enhanced Token Estimation)**
**Deliverables: Intelligent compression engine in `create-compaction.py`**