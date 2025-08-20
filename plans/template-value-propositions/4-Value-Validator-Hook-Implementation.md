# Phase 4: Value Validator Hook Implementation

## Phase Metadata
- **Phase**: 4 of 6
- **Title**: Value Validator Hook Implementation
- **Estimated Time**: 2-3 hours
- **Status**: Planning
- **Dependencies**: Phase 1, 2, 3 completed
- **Checksum**: `<checksum-placeholder>`

## 🎯 Phase Objective
Implement `.claude/hooks/plan-value-validator.py` - an optional validation hook that ensures all value proposition sections are present, complete, and accurate. Integrates with the plan completion workflow.

## 📋 Phase Tasks

### Task 4.1: Validation Framework Implementation (60 minutes)
- [ ] **Create Validator Hook Structure**
  ```python
  #!/usr/bin/env python3
  """
  SolarWindPy Plan Value Proposition Validator
  Validates completeness and accuracy of plan value propositions
  """
  
  import argparse
  import re
  from pathlib import Path
  from typing import Dict, List, Tuple, Optional
  ```

- [ ] **Command Line Interface**
  - `--plan-file`: Path to plan overview file to validate
  - `--strict`: Enable strict validation mode
  - `--report-format`: text (default), json, or markdown
  - `--fix-issues`: Attempt to fix minor validation issues

### Task 4.2: Value Proposition Section Validation (75 minutes)

#### Required Section Checker
- [ ] **Section Presence Validation**
  ```python
  def validate_required_sections(plan_content: str) -> Dict[str, bool]:
      """Check if all required value proposition sections are present."""
      
      required_sections = {
          'value_proposition_analysis': r'## 📊 Value Proposition Analysis',
          'resource_cost_analysis': r'## 💰 Resource & Cost Analysis', 
          'risk_assessment': r'## ⚠️ Risk Assessment & Mitigation',
          'security_proposition': r'## 🔒 Security Proposition',
          'token_optimization': r'## 💾 Token Usage Optimization',
          'time_analysis': r'## ⏱️ Time Investment Analysis',
          'usage_metrics': r'## 🎯 Usage & Adoption Metrics'
      }
      
      validation_results = {}
      
      for section_key, pattern in required_sections.items():
          validation_results[section_key] = bool(re.search(pattern, plan_content, re.IGNORECASE))
      
      return validation_results
  ```

#### Content Quality Validation
- [ ] **Security Section Validation**
  ```python
  def validate_security_section(plan_content: str) -> Tuple[bool, List[str]]:
      """Validate security proposition completeness and scope."""
      
      issues = []
      security_section = extract_section(plan_content, 'Security Proposition')
      
      if not security_section:
          return False, ['Security section missing entirely']
      
      # Check for required security components (code-level only)
      required_components = {
          'dependency': ['dependency', 'package', 'vulnerability'],
          'authentication': ['auth', 'access', 'control', 'permission'], 
          'attack_surface': ['exposure', 'interface', 'attack', 'surface'],
          'development_security': ['workflow', 'ci/cd', 'development']
      }
      
      for component, keywords in required_components.items():
          if not any(keyword in security_section.lower() for keyword in keywords):
              issues.append(f'Missing {component} assessment in security section')
      
      # Check for excluded FAIR data compliance
      fair_keywords = ['fair', 'metadata', 'persistent identifier', 'ontology']
      if any(keyword in security_section.lower() for keyword in fair_keywords):
          issues.append('Security section includes FAIR data compliance (should be excluded)')
      
      return len(issues) == 0, issues
  ```

### Task 4.3: Token Optimization Validation (45 minutes)
- [ ] **Token Calculation Verification**
  ```python
  def validate_token_calculations(plan_content: str) -> Tuple[bool, List[str]]:
      """Verify token usage calculations are reasonable and present."""
      
      issues = []
      token_section = extract_section(plan_content, 'Token Usage Optimization')
      
      if not token_section:
          issues.append('Token optimization section missing')
          return False, issues
      
      # Extract token numbers from section
      token_numbers = re.findall(r'(\d{1,5})\s*tokens?', token_section)
      
      if not token_numbers:
          issues.append('No token usage numbers found in token section')
      
      # Validate reasonable ranges
      for token_str in token_numbers:
          tokens = int(token_str)
          if tokens < 50:
              issues.append(f'Token estimate {tokens} seems too low')
          elif tokens > 10000:
              issues.append(f'Token estimate {tokens} seems too high for single plan')
      
      # Check for savings calculation
      savings_pattern = r'(\d{1,3})%\s*(?:reduction|savings?)'
      savings_match = re.search(savings_pattern, token_section, re.IGNORECASE)
      
      if savings_match:
          savings_percent = int(savings_match.group(1))
          if savings_percent < 30 or savings_percent > 90:
              issues.append(f'Token savings {savings_percent}% outside reasonable range (30-90%)')
      else:
          issues.append('No token savings percentage found')
      
      return len(issues) == 0, issues
  ```

### Task 4.4: Integration with Plan Completion (30 minutes)
- [ ] **Plan Completion Manager Integration**
  ```python
  def integrate_with_completion_manager():
      """Integration hook for plan-completion-manager.py"""
      
      # This function will be called by plan-completion-manager.py
      # when checking if a plan can be marked as completed
      
      def validate_plan_for_completion(plan_dir: Path) -> Tuple[bool, str]:
          """Validate plan has complete value propositions before completion."""
          
          overview_file = plan_dir / '0-Overview.md'
          
          if not overview_file.exists():
              return False, 'No overview file found'
          
          with open(overview_file, 'r') as f:
              content = f.read()
          
          # Run all validations
          section_results = validate_required_sections(content)
          security_valid, security_issues = validate_security_section(content)
          token_valid, token_issues = validate_token_calculations(content)
          
          # Collect all issues
          all_issues = []
          
          missing_sections = [k for k, v in section_results.items() if not v]
          if missing_sections:
              all_issues.extend([f'Missing section: {s}' for s in missing_sections])
          
          if not security_valid:
              all_issues.extend(security_issues)
          
          if not token_valid:
              all_issues.extend(token_issues)
          
          if all_issues:
              return False, f"Value proposition validation failed: {'; '.join(all_issues)}"
          
          return True, "All value propositions validated successfully"
      
      return validate_plan_for_completion
  ```

### Task 4.5: Reporting and Fix Suggestions (30 minutes)
- [ ] **Validation Report Generator**
  ```python
  def generate_validation_report(validation_results: Dict) -> str:
      """Generate comprehensive validation report."""
      
      report_lines = []
      report_lines.append("# Plan Value Proposition Validation Report")
      report_lines.append(f"Generated: {datetime.now().isoformat()}")
      report_lines.append("")
      
      # Overall status
      all_passed = all(result.get('passed', False) for result in validation_results.values())
      status = "✅ PASSED" if all_passed else "❌ FAILED"
      report_lines.append(f"**Overall Status**: {status}")
      report_lines.append("")
      
      # Section-by-section results
      for section, results in validation_results.items():
          section_status = "✅" if results.get('passed', False) else "❌"
          report_lines.append(f"## {section_status} {section.replace('_', ' ').title()}")
          
          if results.get('issues'):
              report_lines.append("**Issues found:**")
              for issue in results['issues']:
                  report_lines.append(f"- {issue}")
          else:
              report_lines.append("No issues found.")
          
          report_lines.append("")
      
      return "\n".join(report_lines)
  ```

- [ ] **Auto-Fix Suggestions**
  ```python
  def suggest_fixes(validation_issues: List[str]) -> List[str]:
      """Suggest fixes for common validation issues."""
      
      fixes = []
      
      for issue in validation_issues:
          if 'Missing section' in issue:
              fixes.append(f"Add the {issue.split(':')[1].strip()} section to your plan")
          elif 'FAIR data compliance' in issue:
              fixes.append("Remove FAIR data references from security section (not implemented)")
          elif 'Token estimate' in issue and 'too low' in issue:
              fixes.append("Increase token estimates - typical plans use 500-3000 tokens")
          elif 'Token estimate' in issue and 'too high' in issue:
              fixes.append("Reduce token estimates - values above 10k tokens are unusual")
          elif 'No token savings' in issue:
              fixes.append("Add token savings percentage (typically 60-80% with hooks)")
          else:
              fixes.append(f"Review and address: {issue}")
      
      return fixes
  ```

## ✅ Phase Success Criteria
- [ ] Complete `plan-value-validator.py` hook implemented
- [ ] All required sections validated
- [ ] Security section validation (no FAIR compliance)
- [ ] Token calculation verification
- [ ] Integration with plan-completion-manager.py
- [ ] Validation reporting and fix suggestions
- [ ] Command line interface functional
- [ ] Performance acceptable (<3 seconds execution)

## 🔧 Testing Approach
- [ ] **Unit Tests**
  - Section presence detection
  - Security content validation  
  - Token calculation verification
  - Report generation
  
- [ ] **Integration Tests**
  - Plan completion workflow integration
  - Valid plan acceptance
  - Invalid plan rejection
  - Fix suggestion accuracy

## 🔄 Dependencies and Integration Points
- **Input**: Plans with value propositions from Phase 3
- **Output**: Validation reports and completion approval
- **Integration**: Works with plan-completion-manager.py
- **Performance**: Target <3 seconds validation time

## 🚧 Implementation Notes
*[Track validation logic, integration challenges, and testing results]*

---
**Previous Phase**: [3-Value-Generator-Hook-Implementation.md](./3-Value-Generator-Hook-Implementation.md)  
**Next Phase**: [5-Documentation-Agent-Updates.md](./5-Documentation-Agent-Updates.md)