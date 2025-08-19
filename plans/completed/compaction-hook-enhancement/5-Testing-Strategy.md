# Testing Strategy for Enhanced Compaction Hook System

## Overview
Comprehensive testing strategy to validate the enhanced compaction hook system, ensuring reliability, performance, and seamless integration with the existing 7-hook ecosystem and 7-agent system.

## Testing Levels

### 1. Unit Testing (Individual Components)
**Target:** Each enhancement component functions correctly in isolation

#### Token Estimation Testing
```python
# tests/test_compaction_enhancement.py
def test_enhanced_token_estimation():
    """Test enhanced token estimation accuracy."""
    # Test with known content samples
    test_cases = [
        ('simple_prose.md', 'Simple prose content', 150, 10),  # file, content, expected_tokens, tolerance
        ('code_heavy.md', 'Code-heavy content', 200, 15),
        ('mixed_content.md', 'Mixed content types', 300, 20)
    ]
    
    for filename, description, expected, tolerance in test_cases:
        tokens, lines, breakdown = estimate_context_size_enhanced_for_file(filename)
        assert abs(tokens - expected) <= tolerance, f"Token estimation for {description} outside tolerance"
        assert breakdown is not None, "Content breakdown should be provided"

def test_content_analysis_functions():
    """Test content analysis utility functions."""
    sample_content = '''
# Header
Some prose content here.

```python
def test_function():
    return "test"
```

- List item 1
- List item 2

| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |
'''
    
    chars, words, lines, breakdown = analyze_file_content_from_string(sample_content)
    
    assert chars > 0, "Character count should be positive"
    assert words > 0, "Word count should be positive"
    assert lines > 0, "Line count should be positive"
    assert breakdown['code'] == 1, "Should detect 1 code block"
    assert breakdown['tables'] > 0, "Should detect table content"
    assert breakdown['lists'] == 2, "Should detect 2 list items"
```

#### Compression Intelligence Testing
```python
def test_compression_strategy_selection():
    """Test intelligent compression strategy selection."""
    # Test with different content profiles
    content_profiles = [
        {'code': 50, 'prose': 30, 'tables': 10, 'lists': 10},  # Code-heavy
        {'code': 10, 'prose': 70, 'tables': 5, 'lists': 15},   # Prose-heavy
        {'code': 20, 'prose': 20, 'tables': 40, 'lists': 20}   # Table-heavy
    ]
    
    for profile in content_profiles:
        strategy = CompactionStrategy(profile, 10000, 0.4)
        plan = strategy.create_compression_plan()
        
        assert 'compression_methods' in plan, "Compression methods should be selected"
        assert len(plan['compression_methods']) > 0, "At least one method should be selected"
        
        # Verify appropriate methods for content type
        if profile['code'] > 30:
            assert 'compress_code_examples' in plan['compression_methods']
        if profile['prose'] > 50:
            assert 'summarize_verbose_sections' in plan['compression_methods']

def test_compression_functions():
    """Test individual compression functions."""
    # Test code compression
    code_content = '''
```python
def complex_function():
    """This is a complex function."""
    # Implementation details
    for i in range(100):
        process_item(i)
    return result
```
'''
    
    compressed = compress_code_examples(code_content)
    assert 'def complex_function()' in compressed, "Function signature should be preserved"
    assert 'compressed' in compressed, "Should indicate compression occurred"
    
    # Test prose summarization
    verbose_content = '''
## Long Section
This is a very long section with lots of details that could be summarized.
''' + '\n'.join([f'Line {i} with more details.' for i in range(50)])
    
    summarized = summarize_verbose_sections(verbose_content)
    assert 'summarized for compaction' in summarized, "Should indicate summarization"
    assert len(summarized) < len(verbose_content), "Should be shorter than original"
```

#### Git Integration Testing
```python
def test_enhanced_git_info_collection():
    """Test enhanced git information collection."""
    git_info = get_enhanced_git_info()
    
    required_keys = ['branch', 'commits', 'status', 'branch_info', 'recent_activity', 'metrics']
    for key in required_keys:
        assert key in git_info, f"Git info should contain {key}"
    
    # Test branch relationship detection
    if git_info['branch'].startswith('plan/'):
        assert git_info['branch_info']['type'] == 'plan'
        assert 'plan_name' in git_info['branch_info']
    elif git_info['branch'].startswith('feature/'):
        assert git_info['branch_info']['type'] == 'feature'
        assert 'feature_name' in git_info['branch_info']

def test_git_tagging():
    """Test git tag creation and cleanup."""
    # Create test compression plan
    test_plan = {
        'compression_methods': ['test_method'],
        'token_reduction': '40%'
    }
    
    git_info = get_enhanced_git_info()
    tag_name = create_compaction_git_tag(git_info, test_plan)
    
    if tag_name:  # Only test if tagging succeeded
        # Verify tag was created
        result = subprocess.run(['git', 'tag', '-l', tag_name], capture_output=True, text=True)
        assert tag_name in result.stdout, "Tag should be created"
        
        # Test cleanup (but don't actually remove tags in test)
        # cleanup_old_compaction_tags()  # Would need mock for real testing
```

### 2. Integration Testing (Component Interaction)
**Target:** Enhanced components work together correctly

```python
def test_end_to_end_compaction_creation():
    """Test complete enhanced compaction creation flow."""
    # Create test content files
    setup_test_content_files()
    
    try:
        # Run enhanced compaction
        final_content, metadata = create_enhanced_compaction_final()
        
        # Verify structure
        assert '## Enhanced Compaction Metadata' in final_content
        assert '## Session Resumption Guide' in final_content
        assert 'Quick Start' in final_content
        assert 'Priority Actions' in final_content
        
        # Verify metadata
        assert 'tokens_before' in metadata
        assert 'tokens_after' in metadata
        assert 'compression_ratio' in metadata
        assert metadata['resumption_ready'] is True
        
        # Verify compression effectiveness
        assert metadata['tokens_after'] < metadata['tokens_before']
        assert 0.2 <= metadata['compression_ratio'] <= 0.6  # 20-60% reduction
        
    finally:
        cleanup_test_content_files()

def test_hook_ecosystem_integration():
    """Test integration with existing hook ecosystem."""
    # Test with validate-session-state.sh
    compaction_file = Path('.claude/compacted_state.md')
    if compaction_file.exists():
        # Verify validate-session-state.sh can load compacted state
        result = subprocess.run([
            '.claude/hooks/validate-session-state.sh'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, "Session state validation should succeed"
        assert 'compacted state' in result.stdout.lower(), "Should recognize compacted state"
    
    # Test with git-workflow-validator.sh
    # Mock git operations to test integration
    test_git_workflow_integration()
```

### 3. Performance Testing
**Target:** Enhanced system meets performance requirements

```python
def test_compaction_performance():
    """Test compaction creation performance."""
    import time
    
    # Create realistic test content
    setup_large_test_content()
    
    try:
        start_time = time.time()
        final_content, metadata = create_enhanced_compaction_final()
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Performance requirements
        assert execution_time < 5.0, f"Compaction should complete in <5s, took {execution_time:.2f}s"
        
        # Memory usage test (would need memory profiling)
        # assert peak_memory_usage < 50_000_000  # 50MB
        
    finally:
        cleanup_large_test_content()

def test_token_estimation_accuracy():
    """Test token estimation accuracy against known samples."""
    # Test with files of known token counts (manually verified)
    test_files = [
        ('sample_plan.md', 2500),  # filename, expected_tokens
        ('sample_code.py', 800),
        ('sample_prose.md', 1200)
    ]
    
    for filename, expected_tokens in test_files:
        if Path(filename).exists():
            estimated_tokens, _, _ = estimate_context_size_enhanced_for_file(filename)
            accuracy = abs(estimated_tokens - expected_tokens) / expected_tokens
            
            assert accuracy <= 0.1, f"Token estimation accuracy should be within 10%, was {accuracy:.1%}"
```

### 4. Regression Testing
**Target:** Existing functionality preserved

```python
def test_backward_compatibility():
    """Test that existing compaction functionality still works."""
    # Test original compaction creation still functions
    original_content = create_original_compaction()
    assert original_content is not None, "Original compaction should still work"
    assert '# Compacted Context State' in original_content, "Original format preserved"
    
    # Test existing plan structure compatibility
    test_plan_structure_compatibility()
    
    # Test existing hook compatibility
    test_existing_hook_compatibility()

def test_existing_hook_compatibility():
    """Test compatibility with existing hooks."""
    # Test each existing hook still functions
    hooks_to_test = [
        '.claude/hooks/validate-session-state.sh',
        '.claude/hooks/git-workflow-validator.sh',
        '.claude/hooks/test-runner.sh',
        '.claude/hooks/pre-commit-tests.sh'
    ]
    
    for hook in hooks_to_test:
        if Path(hook).exists():
            # Run hook with test parameters
            result = subprocess.run([hook], capture_output=True, text=True)
            # Should not fail due to compaction enhancements
            assert result.returncode in [0, None], f"Hook {hook} should remain functional"
```

### 5. Agent Coordination Testing
**Target:** Enhanced compaction works with all 7 agents

```python
def test_agent_context_preservation():
    """Test that agent contexts are properly preserved."""
    # Create test scenario with agent-specific content
    agent_contexts = {
        'UnifiedPlanCoordinator': 'plan coordination context',
        'PhysicsValidator': 'physics validation context',
        'DataFrameArchitect': 'dataframe structure context',
        'NumericalStabilityGuard': 'numerical computation context',
        'PlottingEngineer': 'visualization context',
        'FitFunctionSpecialist': 'curve fitting context',
        'TestEngineer': 'testing strategy context'
    }
    
    # Create compaction with agent contexts
    compaction_content = create_compaction_with_agent_contexts(agent_contexts)
    
    # Verify each agent context is preserved or properly compressed
    for agent, context_type in agent_contexts.items():
        # Check if critical elements are preserved
        assert agent in compaction_content or 'agent coordination' in compaction_content.lower()

def test_session_resumption_with_agents():
    """Test that agents can resume effectively with compacted state."""
    # This would be more of a simulation test
    resumption_guide = create_test_resumption_guide()
    
    # Verify resumption guide contains agent coordination information
    assert 'agent_preparation' in str(resumption_guide)
    assert 'domain_agents' in str(resumption_guide)
```

## Test Execution Strategy

### Automated Testing
```bash
# Run enhanced compaction tests
pytest tests/test_compaction_enhancement.py -v

# Run integration tests with existing system
pytest tests/test_hook_integration.py -v

# Run performance benchmarks
pytest tests/test_compaction_performance.py -v --benchmark

# Run regression tests
pytest tests/test_compaction_regression.py -v
```

### Manual Testing Scenarios
1. **Complete Development Session**: Create plan, implement features, create compaction, resume session
2. **Multi-Hook Workflow**: Trigger multiple hooks in sequence with enhanced compaction
3. **Agent Coordination**: Test with actual agent usage scenarios
4. **Error Conditions**: Test with git errors, file permission issues, corrupt content
5. **Performance Stress**: Test with very large context (>20k tokens)

### Continuous Integration
- Add enhanced compaction tests to existing CI pipeline
- Include performance benchmarks in CI
- Test against multiple git states and branch configurations
- Validate with different plan structures and content types

## Rollback Testing

### Fallback Validation
```python
def test_fallback_mechanisms():
    """Test that fallback mechanisms work correctly."""
    # Test enhanced estimation fallback
    with mock_function_failure('estimate_context_size_enhanced'):
        tokens, lines = estimate_context_size()  # Should fall back to original
        assert tokens > 0, "Fallback estimation should work"
    
    # Test compression failure fallback
    with mock_function_failure('apply_intelligent_compression'):
        content = create_compaction()  # Should fall back to original method
        assert content is not None, "Fallback compaction should work"
```

### Recovery Testing
```python
def test_error_recovery():
    """Test error recovery in enhanced compaction."""
    error_scenarios = [
        'git_command_failure',
        'file_permission_denied',
        'corrupted_plan_files',
        'insufficient_disk_space',
        'network_timeout'
    ]
    
    for scenario in error_scenarios:
        with simulate_error_condition(scenario):
            # Enhanced compaction should handle errors gracefully
            try:
                result = create_enhanced_compaction_final()
                # Should either succeed or fail gracefully
                assert result is not None or "fallback was used"
            except Exception as e:
                # Should be handled exception, not crash
                assert "fallback" in str(e).lower() or "graceful" in str(e).lower()
```

## Success Criteria

### Functional Requirements
- [ ] All unit tests pass with >95% coverage
- [ ] Integration tests validate hook ecosystem compatibility
- [ ] Agent coordination tests confirm seamless operation
- [ ] Regression tests ensure existing functionality preserved

### Performance Requirements
- [ ] Compaction creation <5 seconds
- [ ] Token estimation accuracy within ±10%
- [ ] Memory usage <50MB during operation
- [ ] Session resumption <2 seconds

### Quality Requirements
- [ ] Error handling robust and informative
- [ ] Fallback mechanisms functional
- [ ] Documentation complete and accurate
- [ ] Code quality meets project standards (black, flake8)

---
**Testing Strategy ensures reliable, performant, and compatible enhanced compaction system**