# Phase 3: Value Generator Hook Implementation

## Phase Metadata
- **Phase**: 3 of 6
- **Title**: Value Generator Hook Implementation
- **Estimated Time**: 3-4 hours
- **Status**: Planning
- **Dependencies**: Phase 1, 2 completed
- **Checksum**: `<checksum-placeholder>`

## 🎯 Phase Objective
Implement `.claude/hooks/plan-value-generator.py` - the core hook that programmatically generates comprehensive value propositions for SolarWindPy plans, focusing on practical assessments without requiring FAIR data compliance.

## 📋 Phase Tasks

### Task 3.1: Hook Architecture and Core Framework (60 minutes)
- [ ] **Create Basic Hook Structure**
  ```python
  #!/usr/bin/env python3
  """
  SolarWindPy Plan Value Proposition Generator
  Generates comprehensive value propositions for scientific software plans
  """
  
  import argparse
  import json
  import re
  from pathlib import Path
  from typing import Dict, List, Optional
  ```

- [ ] **Implement Command Line Interface**
  - `--plan-file`: Path to plan overview file
  - `--plan-data`: JSON string with plan metadata
  - `--output-format`: markdown (default) or json
  - `--include-all`: Include all proposition types
  - `--exclude-fair`: Explicitly exclude FAIR compliance (default)

### Task 3.2: Value Proposition Generation Logic (90 minutes)

#### Scientific Software Development Value Generator
- [ ] **Research Efficiency Assessment**
  ```python
  def generate_research_efficiency_value(plan_data: Dict) -> str:
      """Generate research efficiency improvements analysis."""
      
      efficiency_factors = {
          'core/': 'High impact on fundamental physics calculations',
          'plotting/': 'Medium impact on data visualization workflows',
          'fitfunctions/': 'High impact on statistical analysis capabilities',
          'instabilities/': 'Critical impact on plasma physics research',
          'tools/': 'Low to medium impact on utility functions'
      }
      
      # Analyze affected areas
      affected_areas = plan_data.get('affects', '')
      efficiency_impacts = []
      
      for area, impact in efficiency_factors.items():
          if area in affected_areas:
              efficiency_impacts.append(f"- **{area}**: {impact}")
      
      return format_efficiency_analysis(efficiency_impacts, plan_data)
  ```

#### Developer Productivity Value Generator
- [ ] **Token Usage Calculator**
  ```python
  def calculate_token_optimization(plan_data: Dict) -> Dict:
      """Calculate token usage optimization metrics."""
      
      # Base token costs for manual proposition writing
      manual_tokens = {
          'simple_plan': 1200,
          'moderate_plan': 1800,
          'complex_plan': 2500,
          'physics_plan': 3000  # Extra context for physics validation
      }
      
      # Automated generation costs
      automated_tokens = {
          'hook_execution': 100,
          'content_insertion': 150,
          'validation': 50
      }
      
      plan_complexity = assess_plan_complexity(plan_data)
      current_cost = manual_tokens[plan_complexity]
      optimized_cost = sum(automated_tokens.values())
      
      return {
          'current_usage': current_cost,
          'optimized_usage': optimized_cost,
          'savings': current_cost - optimized_cost,
          'savings_percent': ((current_cost - optimized_cost) / current_cost) * 100
      }
  ```

### Task 3.3: Security Proposition Generator (75 minutes)
- [ ] **Code-Level Security Assessment** (No FAIR Data)
  ```python
  def generate_security_proposition(plan_data: Dict) -> str:
      """Generate practical security assessment for scientific software."""
      
      security_assessment = {
          'dependency_scan': assess_dependency_security(plan_data),
          'auth_impact': analyze_authentication_changes(plan_data),
          'attack_surface': evaluate_code_exposure(plan_data),
          'workflow_security': check_development_security(plan_data)
      }
      
      # Explicitly exclude FAIR data assessments
      excluded_areas = [
          'metadata_security',
          'data_format_integrity', 
          'persistent_identifier_management',
          'fair_compliance_checking'
      ]
      
      return format_security_markdown(security_assessment, excluded_areas)
  ```

- [ ] **Dependency Vulnerability Scanner**
  ```python
  def assess_dependency_security(plan_data: Dict) -> Dict:
      """Scan for dependency security issues."""
      
      # Check if plan introduces new dependencies
      new_deps = extract_dependencies(plan_data.get('description', ''))
      
      # Common scientific Python packages with known considerations
      security_notes = {
          'numpy': 'Generally secure, check version for known CVEs',
          'scipy': 'Trusted scientific package, minimal risk',
          'matplotlib': 'Visualization library, low security risk',
          'pandas': 'Check for CSV parsing vulnerabilities',
          'requests': 'Network library, validate SSL/TLS usage',
          'jupyter': 'Development tool, consider execution risks'
      }
      
      vulnerability_assessment = []
      for dep in new_deps:
          if dep.lower() in security_notes:
              vulnerability_assessment.append({
                  'package': dep,
                  'assessment': security_notes[dep.lower()],
                  'action_required': 'Version check and security review'
              })
      
      return {
          'new_dependencies': new_deps,
          'assessments': vulnerability_assessment,
          'overall_risk': calculate_dependency_risk(new_deps)
      }
  ```

### Task 3.4: Resource & Cost Analysis Generator (45 minutes)
- [ ] **Development Time Estimation**
  ```python
  def estimate_development_cost(plan_data: Dict) -> Dict:
      """Generate development cost analysis."""
      
      # Time estimation based on plan complexity and SolarWindPy patterns
      base_hours = {
          'simple': 4,
          'moderate': 8,
          'complex': 16,
          'physics_heavy': 24
      }
      
      # Multipliers based on affected areas
      complexity_multipliers = {
          'core/': 1.5,  # Core physics requires extra validation
          'instabilities/': 1.8,  # Plasma physics complexity
          'plotting/': 0.9,  # Visualization usually straightforward
          'tests/': 1.2,  # Testing overhead
          'docs/': 0.8   # Documentation generally faster
      }
      
      plan_type = classify_plan_complexity(plan_data)
      base_estimate = base_hours[plan_type]
      
      # Apply multipliers based on affected areas
      affected = plan_data.get('affects', '')
      final_multiplier = 1.0
      
      for area, multiplier in complexity_multipliers.items():
          if area in affected:
              final_multiplier *= multiplier
      
      total_estimate = base_estimate * final_multiplier
      
      return {
          'base_estimate_hours': base_estimate,
          'complexity_multiplier': final_multiplier,
          'total_estimate_hours': total_estimate,
          'confidence_interval': f"{total_estimate * 0.8}-{total_estimate * 1.3}",
          'breakdown': generate_time_breakdown(plan_data, total_estimate)
      }
  ```

### Task 3.5: Integration and Utility Functions (30 minutes)
- [ ] **Plan Data Parser**
  ```python
  def parse_plan_metadata(plan_file: Path) -> Dict:
      """Extract plan metadata from overview file."""
      
      with open(plan_file, 'r') as f:
          content = f.read()
      
      metadata = {}
      
      # Extract key information using regex
      metadata['plan_name'] = extract_field(content, r'Plan Name\*\*:\s*(.+)')
      metadata['phases'] = count_phases(content)
      metadata['estimated_duration'] = extract_field(content, r'Estimated Duration\*\*:\s*(.+)')
      metadata['affects'] = extract_field(content, r'Affects\*\*:\s*(.+)')
      metadata['description'] = extract_objective(content)
      
      return metadata
  ```

- [ ] **Markdown Formatter**
  ```python
  def format_value_propositions(propositions: Dict) -> str:
      """Format all value propositions as markdown."""
      
      sections = []
      
      # Generate each section
      sections.append("## 📊 Value Proposition Analysis")
      sections.append(propositions['scientific_value'])
      sections.append(propositions['developer_value'])
      
      sections.append("## 💰 Resource & Cost Analysis")
      sections.append(propositions['cost_analysis'])
      
      sections.append("## ⚠️ Risk Assessment & Mitigation")
      sections.append(propositions['risk_assessment'])
      
      sections.append("## 🔒 Security Proposition")
      sections.append(propositions['security_assessment'])
      sections.append("**Note**: Code-level security only. No FAIR data compliance requirements.")
      
      sections.append("## 💾 Token Usage Optimization")
      sections.append(propositions['token_optimization'])
      
      sections.append("## ⏱️ Time Investment Analysis")
      sections.append(propositions['time_analysis'])
      
      sections.append("## 🎯 Usage & Adoption Metrics")
      sections.append(propositions['usage_metrics'])
      
      return "\n\n".join(sections)
  ```

## ✅ Phase Success Criteria
- [ ] Complete `plan-value-generator.py` hook implemented
- [ ] All value proposition types supported (except FAIR)
- [ ] Security assessment focused on code-level only
- [ ] Token optimization calculations accurate
- [ ] Command line interface functional
- [ ] Integration with template placeholders working
- [ ] SolarWindPy-specific logic included
- [ ] Performance acceptable (<5 seconds execution)

## 🔧 Testing Approach
- [ ] **Unit Tests for Core Functions**
  - Value proposition generation logic
  - Security assessment accuracy
  - Token calculation verification
  - Plan metadata parsing
  
- [ ] **Integration Tests**
  - Hook execution with sample plans
  - Template placeholder replacement
  - Command line interface validation
  - Error handling for invalid inputs

## 🔄 Dependencies and Integration Points
- **Input**: Enhanced templates from Phase 2
- **Output**: Generated value propositions ready for template insertion
- **Integration**: Must work with UnifiedPlanCoordinator agent workflow
- **Performance**: Target <5 seconds execution time

## 🚧 Implementation Notes
*[Track hook development, performance issues, and integration challenges]*

---
**Previous Phase**: [2-Plan-Template-Enhancement.md](./2-Plan-Template-Enhancement.md)  
**Next Phase**: [4-Value-Validator-Hook-Implementation.md](./4-Value-Validator-Hook-Implementation.md)