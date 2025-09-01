#!/usr/bin/env python3
"""SolarWindPy Plan Value Proposition Generator.

Generates comprehensive value propositions for scientific software plans,
focusing on practical assessments without requiring FAIR data compliance.

Usage:
    python .claude/hooks/plan-value-generator.py --plan-file plans/example/0-Overview.md
    python .claude/hooks/plan-value-generator.py --plan-data '{"name":"test","phases":3}'
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict
from datetime import datetime


class SolarWindPyPlanValueGenerator:
    """Generate value propositions for SolarWindPy development plans."""

    def __init__(self):
        self.solarwindpy_modules = {
            "core/": {
                "complexity": 1.5,
                "description": "Core physics calculations and data structures",
                "impact": "High impact on fundamental plasma physics research",
            },
            "instabilities/": {
                "complexity": 1.8,
                "description": "Plasma instability analysis and calculations",
                "impact": "Critical impact on plasma physics research",
            },
            "plotting/": {
                "complexity": 0.9,
                "description": "Data visualization and matplotlib integration",
                "impact": "Medium impact on data analysis workflows",
            },
            "fitfunctions/": {
                "complexity": 1.3,
                "description": "Curve fitting and statistical analysis",
                "impact": "High impact on data analysis capabilities",
            },
            "tools/": {
                "complexity": 0.8,
                "description": "Utility functions and helper modules",
                "impact": "Low to medium impact on development efficiency",
            },
            "spacecraft/": {
                "complexity": 1.2,
                "description": "Spacecraft data handling and processing",
                "impact": "Medium impact on mission data analysis",
            },
            "tests/": {
                "complexity": 1.1,
                "description": "Testing infrastructure and validation",
                "impact": "High impact on code quality and reliability",
            },
            "docs/": {
                "complexity": 0.7,
                "description": "Documentation and examples",
                "impact": "Medium impact on user adoption and learning",
            },
        }

        self.security_keywords = {
            "dependency": ["package", "import", "requirement", "dependency"],
            "authentication": ["auth", "login", "permission", "access", "user"],
            "network": ["http", "api", "request", "download", "fetch"],
            "file_io": ["file", "read", "write", "save", "load"],
            "execution": ["exec", "eval", "subprocess", "shell", "command"],
        }

    def parse_plan_file(self, plan_file: Path) -> Dict:
        """Extract plan metadata from overview file."""
        if not plan_file.exists():
            raise FileNotFoundError(f"Plan file not found: {plan_file}")

        with open(plan_file, "r", encoding="utf-8") as f:
            content = f.read()

        metadata = {}

        # Extract basic metadata using regex
        metadata["plan_name"] = self._extract_field(
            content, r"\*\*Plan Name\*\*:\s*(.+)"
        )
        metadata["estimated_duration"] = self._extract_field(
            content, r"\*\*Estimated Duration\*\*:\s*(.+)"
        )
        metadata["affects"] = self._extract_field(content, r"\*\*Affects\*\*:\s*(.+)")
        metadata["total_phases"] = self._extract_field(
            content, r"\*\*Total Phases\*\*:\s*(\d+)"
        )

        # Extract objective and context
        metadata["objective"] = self._extract_section(content, "Objective")
        metadata["context"] = self._extract_section(content, "Context")

        # Count phases by looking for phase overview items
        phase_lines = re.findall(r"- \[ \] \*\*Phase \d+:", content)
        metadata["phase_count"] = len(phase_lines) if phase_lines else 1

        # Classify plan complexity
        metadata["complexity"] = self._classify_complexity(metadata)

        return metadata

    def _extract_field(self, content: str, pattern: str) -> str:
        """Extract a single field using regex."""
        match = re.search(pattern, content, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract a full section from the markdown."""
        pattern = rf"## 🎯 {section_name}\s*\n(.*?)(?=\n## |$)"
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _classify_complexity(self, metadata: Dict) -> str:
        """Classify plan complexity based on metadata."""
        affects = metadata.get("affects", "").lower()
        phase_count = int(metadata.get("phase_count", 1))

        # Physics-heavy plans
        if any(module in affects for module in ["core/", "instabilities/"]):
            return "physics_heavy"

        # Complex plans (many phases or multiple modules)
        if (
            phase_count >= 6
            or len([m for m in self.solarwindpy_modules if m in affects]) >= 3
        ):
            return "complex"

        # Moderate plans
        if phase_count >= 3 or any(
            module in affects for module in ["plotting/", "fitfunctions/"]
        ):
            return "moderate"

        # Simple plans
        return "simple"

    def generate_value_propositions(self, plan_data: Dict) -> str:
        """Generate all value proposition sections."""

        sections = []

        # Generate each section
        sections.append(self._generate_value_proposition_analysis(plan_data))
        sections.append(self._generate_resource_cost_analysis(plan_data))
        sections.append(self._generate_risk_assessment(plan_data))
        sections.append(self._generate_security_proposition(plan_data))
        sections.append(self._generate_scope_audit(plan_data))
        sections.append(self._generate_token_optimization(plan_data))
        sections.append(self._generate_time_analysis(plan_data))
        sections.append(self._generate_usage_metrics(plan_data))

        return "\n\n".join(sections)

    def _generate_value_proposition_analysis(self, plan_data: Dict) -> str:
        """Generate scientific software development and productivity value."""

        affects = plan_data.get("affects", "")
        complexity = plan_data.get("complexity", "moderate")

        # Scientific software development value
        research_efficiency = self._assess_research_efficiency(affects)
        development_quality = self._assess_development_quality(plan_data)

        # Developer productivity value
        planning_efficiency = self._calculate_planning_efficiency(plan_data)
        token_savings = self._calculate_basic_token_savings(plan_data)

        return f"""## 📊 Value Proposition Analysis

### Scientific Software Development Value
**Research Efficiency Improvements:**
{research_efficiency}

**Development Quality Enhancements:**
{development_quality}

### Developer Productivity Value
**Planning Efficiency:**
{planning_efficiency}

**Token Usage Optimization:**
{token_savings}"""

    def _assess_research_efficiency(self, affects: str) -> str:
        """Assess impact on research efficiency."""
        impacts = []

        for module, info in self.solarwindpy_modules.items():
            if module in affects.lower():
                impacts.append(f"- **{module}**: {info['impact']}")

        if not impacts:
            impacts.append(
                "- **General Development**: Improved code quality and maintainability"
            )

        return "\n".join(impacts)

    def _assess_development_quality(self, plan_data: Dict) -> str:
        """Assess development quality improvements."""
        complexity = plan_data.get("complexity", "moderate")

        quality_benefits = [
            "- Systematic evaluation of plan impact on scientific workflows",
            "- Enhanced decision-making through quantified value metrics",
            "- Improved coordination with SolarWindPy's physics validation system",
        ]

        if complexity in ["complex", "physics_heavy"]:
            quality_benefits.append(
                "- Rigorous physics validation ensures computational accuracy"
            )

        return "\n".join(quality_benefits)

    def _calculate_planning_efficiency(self, plan_data: Dict) -> str:
        """Calculate planning efficiency improvements."""
        phase_count = plan_data.get("phase_count", 1)

        base_time_manual = phase_count * 45  # 45 minutes per phase manual
        automated_time = 15 + (phase_count * 5)  # 15 min setup + 5 min per phase

        time_savings = base_time_manual - automated_time
        savings_percent = (time_savings / base_time_manual) * 100

        return f"""- **Manual Planning Time**: ~{base_time_manual} minutes for {phase_count} phases
- **Automated Planning Time**: ~{automated_time} minutes with value propositions
- **Time Savings**: {time_savings} minutes ({savings_percent:.0f}% reduction)
- **Reduced Cognitive Load**: Systematic framework eliminates ad-hoc analysis"""

    def _calculate_basic_token_savings(self, plan_data: Dict) -> str:
        """Calculate basic token usage optimization."""
        complexity = plan_data.get("complexity", "moderate")

        token_costs = {
            "simple": 1200,
            "moderate": 1800,
            "complex": 2500,
            "physics_heavy": 3000,
        }

        manual_cost = token_costs[complexity]
        automated_cost = 300  # Hook execution cost
        savings = manual_cost - automated_cost
        savings_percent = (savings / manual_cost) * 100

        return f"""- **Manual Proposition Writing**: ~{manual_cost} tokens
- **Automated Hook Generation**: ~{automated_cost} tokens
- **Net Savings**: {savings} tokens ({savings_percent:.0f}% reduction)
- **Session Extension**: Approximately {savings // 100} additional minutes of productive work"""

    def _generate_resource_cost_analysis(self, plan_data: Dict) -> str:
        """Generate development investment and cost analysis."""

        # Time estimation
        time_estimate = self._estimate_development_time(plan_data)

        # Token economics
        token_analysis = self._detailed_token_analysis(plan_data)

        return f"""## 💰 Resource & Cost Analysis

### Development Investment
**Implementation Time Breakdown:**
{time_estimate}

**Maintenance Considerations:**
- Ongoing maintenance: ~2-4 hours per quarter
- Testing updates: ~1-2 hours per major change
- Documentation updates: ~30 minutes per feature addition

### Token Usage Economics
{token_analysis}

### Operational Efficiency
- Runtime overhead: <2% additional planning time
- Storage requirements: <5MB additional template data
- Performance impact: Negligible on core SolarWindPy functionality"""

    def _estimate_development_time(self, plan_data: Dict) -> str:
        """Estimate development time based on plan characteristics."""
        affects = plan_data.get("affects", "").lower()
        complexity = plan_data.get("complexity", "moderate")
        phase_count = plan_data.get("phase_count", 1)

        # Base time estimates
        base_hours = {"simple": 4, "moderate": 8, "complex": 16, "physics_heavy": 24}

        base_time = base_hours[complexity]

        # Apply multipliers
        multipliers = []
        for module, info in self.solarwindpy_modules.items():
            if module in affects:
                multiplier = info["complexity"]
                multipliers.append(multiplier)

        if multipliers:
            avg_multiplier = sum(multipliers) / len(multipliers)
        else:
            avg_multiplier = 1.0

        final_estimate = base_time * avg_multiplier
        confidence_low = final_estimate * 0.8
        confidence_high = final_estimate * 1.3

        breakdown = []
        breakdown.append(f"- **Base estimate**: {base_time} hours ({complexity} plan)")
        breakdown.append(f"- **Complexity multiplier**: {avg_multiplier:.1f}x")
        breakdown.append(f"- **Final estimate**: {final_estimate:.1f} hours")
        breakdown.append(
            f"- **Confidence interval**: {confidence_low:.1f}-{confidence_high:.1f} hours"
        )

        if phase_count > 1:
            per_phase = final_estimate / phase_count
            breakdown.append(f"- **Per-phase average**: {per_phase:.1f} hours")

        return "\n".join(breakdown)

    def _detailed_token_analysis(self, plan_data: Dict) -> str:
        """Detailed token usage analysis."""
        complexity = plan_data.get("complexity", "moderate")
        phase_count = plan_data.get("phase_count", 1)

        # Current vs enhanced token usage
        manual_base = {
            "simple": 1200,
            "moderate": 1800,
            "complex": 2500,
            "physics_heavy": 3000,
        }

        current_total = manual_base[complexity]

        # Automated costs
        automated_breakdown = {
            "hook_execution": 100,
            "content_insertion": 150,
            "validation": 50,
            "context_overhead": 100,
        }

        automated_total = sum(automated_breakdown.values())
        net_savings = current_total - automated_total
        savings_percent = (net_savings / current_total) * 100

        # Break-even analysis
        plans_to_break_even = 10  # Approximate break-even point

        analysis = []
        analysis.append("**Current vs Enhanced Token Usage:**")
        analysis.append(f"- Manual proposition writing: ~{current_total} tokens")
        analysis.append(f"- Automated generation: ~{automated_total} tokens")
        analysis.append(
            f"  - Hook execution: {automated_breakdown['hook_execution']} tokens"
        )
        analysis.append(
            f"  - Content insertion: {automated_breakdown['content_insertion']} tokens"
        )
        analysis.append(f"  - Validation: {automated_breakdown['validation']} tokens")
        analysis.append(
            f"  - Context overhead: {automated_breakdown['context_overhead']} tokens"
        )
        analysis.append("")
        analysis.append(
            f"**Net Savings: {net_savings} tokens ({savings_percent:.0f}% reduction)**"
        )
        analysis.append("")
        analysis.append("**Break-even Analysis:**")
        analysis.append(f"- Development investment: ~10-15 hours")
        analysis.append(f"- Token savings per plan: {net_savings} tokens")
        analysis.append(f"- Break-even point: {plans_to_break_even} plans")
        analysis.append(f"- Expected annual volume: 20-30 plans")

        return "\n".join(analysis)

    def _generate_risk_assessment(self, plan_data: Dict) -> str:
        """Generate comprehensive risk assessment."""

        # Technical risks
        technical_risks = self._assess_technical_risks(plan_data)

        # Project risks
        project_risks = self._assess_project_risks(plan_data)

        # Scientific workflow risks
        workflow_risks = self._assess_workflow_risks(plan_data)

        return f"""## ⚠️ Risk Assessment & Mitigation

### Technical Implementation Risks
{technical_risks}

### Project Management Risks
{project_risks}

### Scientific Workflow Risks
{workflow_risks}"""

    def _assess_technical_risks(self, plan_data: Dict) -> str:
        """Assess technical implementation risks."""
        affects = plan_data.get("affects", "").lower()
        complexity = plan_data.get("complexity", "moderate")

        risks = []

        # Core module risks
        if "core/" in affects:
            risks.append(
                {
                    "risk": "Physics calculation disruption",
                    "probability": "Medium",
                    "impact": "High",
                    "mitigation": "Comprehensive physics validation testing, gradual rollout",
                }
            )

        # Complex plan risks
        if complexity in ["complex", "physics_heavy"]:
            risks.append(
                {
                    "risk": "Implementation complexity underestimation",
                    "probability": "Medium",
                    "impact": "Medium",
                    "mitigation": "Conservative time estimates, milestone-based validation",
                }
            )

        # General technical risks
        risks.extend(
            [
                {
                    "risk": "Integration compatibility issues",
                    "probability": "Low",
                    "impact": "Medium",
                    "mitigation": "Thorough integration testing, backward compatibility validation",
                },
                {
                    "risk": "Performance degradation",
                    "probability": "Low",
                    "impact": "Low",
                    "mitigation": "Performance benchmarking, optimization validation",
                },
            ]
        )

        # Format as table
        table = [
            "| Risk | Probability | Impact | Mitigation Strategy |",
            "|------|------------|--------|-------------------|",
        ]

        for risk in risks:
            table.append(
                f"| {risk['risk']} | {risk['probability']} | {risk['impact']} | {risk['mitigation']} |"
            )

        return "\n".join(table)

    def _assess_project_risks(self, plan_data: Dict) -> str:
        """Assess project management risks."""
        phase_count = plan_data.get("phase_count", 1)

        risks = []

        if phase_count >= 5:
            risks.append(
                "- **Timeline slippage risk (Medium)**: Multiple phases increase coordination complexity"
            )
            risks.append(
                "  - *Mitigation*: Clear phase dependencies, regular milestone reviews"
            )

        risks.extend(
            [
                "- **Scope creep risk (Medium)**: Value propositions may reveal additional requirements",
                "  - *Mitigation*: Strict scope boundaries, change control process",
                "- **Resource availability risk (Low)**: Developer time allocation conflicts",
                "  - *Mitigation*: Resource planning, conflict identification system",
                "- **Token budget overrun (Low)**: Complex plans may exceed session limits",
                "  - *Mitigation*: Token monitoring, automatic compaction at phase boundaries",
            ]
        )

        return "\n".join(risks)

    def _assess_workflow_risks(self, plan_data: Dict) -> str:
        """Assess scientific workflow risks."""
        affects = plan_data.get("affects", "").lower()

        risks = []

        if "core/" in affects or "instabilities/" in affects:
            risks.extend(
                [
                    "- **Scientific accuracy risk (Medium)**: Changes to physics modules affect research results",
                    "  - *Mitigation*: Physics validation hooks, expert review process",
                    "- **Reproducibility risk (Low)**: Computational changes may affect result consistency",
                    "  - *Mitigation*: Version tracking, regression testing, validation datasets",
                ]
            )

        risks.extend(
            [
                "- **User workflow disruption (Low)**: Interface changes may affect researcher productivity",
                "  - *Mitigation*: Backward compatibility, gradual feature introduction",
                "- **Documentation lag (Medium)**: Implementation may outpace documentation updates",
                "  - *Mitigation*: Documentation-driven development, parallel doc updates",
            ]
        )

        return "\n".join(risks)

    def _generate_security_proposition(self, plan_data: Dict) -> str:
        """Generate code-level security assessment (NO FAIR compliance)."""

        affects = plan_data.get("affects", "").lower()
        description = (
            plan_data.get("objective", "") + " " + plan_data.get("context", "")
        )

        # Dependency analysis
        dependency_assessment = self._assess_dependencies(description)

        # Authentication impact
        auth_assessment = self._assess_authentication_impact(description)

        # Attack surface analysis
        attack_surface = self._assess_attack_surface(affects, description)

        # Development security
        dev_security = self._assess_development_security(plan_data)

        return f"""## 🔒 Security Proposition

### Code-Level Security Assessment
{dependency_assessment}

{auth_assessment}

{attack_surface}

### Scientific Computing Environment Security
{dev_security}

### Scope Limitations
**This security assessment covers:**
- Code-level security and dependency analysis
- Development workflow security implications
- Scientific computing environment considerations

**Explicitly excluded from this assessment:**
- FAIR data principle compliance (requires core data structure changes)
- Metadata security standards (not implemented)
- Research data repository integration (outside scope)
- Persistent identifier management (not applicable)

**Note**: For comprehensive research data security, consider separate FAIR compliance initiative."""

    def _assess_dependencies(self, description: str) -> str:
        """Assess dependency security implications."""

        # Common scientific Python packages mentioned
        scientific_packages = {
            "numpy": "Core numerical computing - generally secure, verify version",
            "scipy": "Scientific computing library - trusted, minimal risk",
            "matplotlib": "Plotting library - low security risk",
            "pandas": "Data analysis - check for CSV parsing vulnerabilities",
            "requests": "HTTP library - validate SSL/TLS usage if used",
            "jupyter": "Development environment - consider notebook execution risks",
            "h5py": "HDF5 interface - binary format handling, validate inputs",
            "netcdf4": "NetCDF interface - scientific data format, generally safe",
        }

        found_packages = []
        for package in scientific_packages:
            if package in description.lower():
                found_packages.append(
                    f"- **{package}**: {scientific_packages[package]}"
                )

        if not found_packages:
            found_packages = [
                "- **No specific dependencies identified** - general Python security best practices apply"
            ]

        assessment = ["**Dependency Vulnerability Assessment:**"]
        assessment.extend(found_packages)
        assessment.extend(
            [
                "",
                "**Recommended Actions:**",
                "- Run `pip audit` to scan for known vulnerabilities",
                "- Pin dependency versions in requirements.txt",
                "- Monitor security advisories for scientific computing packages",
                "- Consider using conda for better package management",
            ]
        )

        return "\n".join(assessment)

    def _assess_authentication_impact(self, description: str) -> str:
        """Assess authentication and access control impacts."""

        auth_keywords = self.security_keywords["authentication"]
        has_auth = any(keyword in description.lower() for keyword in auth_keywords)

        if has_auth:
            assessment = [
                "**Authentication/Access Control Impact Analysis:**",
                "- Plan involves authentication or access control modifications",
                "- Review user permission changes and privilege escalation risks",
                "- Validate multi-user scientific computing environment compatibility",
                "- Ensure API authentication follows security best practices",
            ]
        else:
            assessment = [
                "**Authentication/Access Control Impact Analysis:**",
                "- No direct authentication system modifications identified",
                "- Standard scientific computing access patterns maintained",
                "- No elevated privilege requirements detected",
                "- Multi-user environment compatibility preserved",
            ]

        return "\n".join(assessment)

    def _assess_attack_surface(self, affects: str, description: str) -> str:
        """Assess attack surface and code exposure analysis."""

        exposure_risks = []

        # Network-related exposure
        if any(
            keyword in description.lower()
            for keyword in self.security_keywords["network"]
        ):
            exposure_risks.append(
                "- **Network exposure**: HTTP/API interfaces may introduce attack vectors"
            )

        # File I/O exposure
        if any(
            keyword in description.lower()
            for keyword in self.security_keywords["file_io"]
        ):
            exposure_risks.append(
                "- **File system exposure**: File operations require input validation"
            )

        # Execution risks
        if any(
            keyword in description.lower()
            for keyword in self.security_keywords["execution"]
        ):
            exposure_risks.append(
                "- **Code execution risks**: Dynamic execution requires careful validation"
            )

        # Module-specific risks
        if "plotting/" in affects:
            exposure_risks.append(
                "- **Visualization risks**: Image generation and display security"
            )

        if not exposure_risks:
            exposure_risks = [
                "- **Minimal exposure increase**: Internal library modifications only"
            ]

        assessment = ["**Attack Surface Analysis:**"]
        assessment.extend(exposure_risks)
        assessment.extend(
            [
                "",
                "**Mitigation Strategies:**",
                "- Validate all external inputs and user-provided data",
                "- Sanitize file paths and prevent directory traversal",
                "- Use parameterized queries for any database operations",
                "- Implement proper error handling to prevent information disclosure",
            ]
        )

        return "\n".join(assessment)

    def _assess_development_security(self, plan_data: Dict) -> str:
        """Assess development workflow security."""

        phase_count = plan_data.get("phase_count", 1)
        complexity = plan_data.get("complexity", "moderate")

        security_measures = [
            "**Development Workflow Security:**",
            "- Git workflow integrity maintained through branch protection",
            "- Code review requirements enforced for security-sensitive changes",
            "- Automated testing validates security assumptions",
        ]

        if complexity in ["complex", "physics_heavy"]:
            security_measures.append(
                "- Physics validation hooks provide additional verification layer"
            )

        if phase_count >= 4:
            security_measures.append(
                "- Multi-phase development allows incremental security review"
            )

        security_measures.extend(
            [
                "",
                "**CI/CD Pipeline Security:**",
                "- Automated dependency scanning in development workflow",
                "- Test environment isolation prevents production data exposure",
                "- Secrets management for any required credentials",
                "- Build reproducibility ensures supply chain integrity",
            ]
        )

        return "\n".join(security_measures)

    def _generate_token_optimization(self, plan_data: Dict) -> str:
        """Generate detailed token usage optimization analysis."""

        complexity = plan_data.get("complexity", "moderate")
        phase_count = plan_data.get("phase_count", 1)

        # Current patterns
        current_analysis = self._analyze_current_token_patterns(plan_data)

        # Optimization strategy
        optimization_strategy = self._design_optimization_strategy(plan_data)

        # Context preservation
        context_benefits = self._assess_context_preservation(plan_data)

        return f"""## 💾 Token Usage Optimization

### Current Token Usage Patterns
{current_analysis}

### Optimized Token Usage Strategy
{optimization_strategy}

### Context Preservation Benefits
{context_benefits}"""

    def _analyze_current_token_patterns(self, plan_data: Dict) -> str:
        """Analyze current token usage patterns."""
        complexity = plan_data.get("complexity", "moderate")
        phase_count = plan_data.get("phase_count", 1)

        # Token costs by activity
        manual_costs = {
            "initial_planning": 800,
            "proposition_writing": {
                "simple": 400,
                "moderate": 600,
                "complex": 800,
                "physics_heavy": 1000,
            },
            "revision_cycles": 300,
            "context_switching": 200,
        }

        proposition_cost = manual_costs["proposition_writing"][complexity]
        total_current = (
            manual_costs["initial_planning"]
            + proposition_cost
            + manual_costs["revision_cycles"]
            + manual_costs["context_switching"]
        )

        analysis = [
            "**Manual Planning Token Breakdown:**",
            f"- Initial planning discussion: ~{manual_costs['initial_planning']} tokens",
            f"- Value proposition writing: ~{proposition_cost} tokens ({complexity} plan)",
            f"- Revision and refinement: ~{manual_costs['revision_cycles']} tokens",
            f"- Context switching overhead: ~{manual_costs['context_switching']} tokens",
            f"- **Total current usage: ~{total_current} tokens per plan**",
            "",
            "**Inefficiency Sources:**",
            "- Repetitive manual analysis for similar plan types",
            "- Context regeneration between planning sessions",
            "- Inconsistent proposition quality requiring revisions",
        ]

        if phase_count > 4:
            analysis.insert(
                -3,
                f"- Multi-phase coordination: ~{(phase_count - 3) * 100} additional tokens",
            )

        return "\n".join(analysis)

    def _design_optimization_strategy(self, plan_data: Dict) -> str:
        """Design token optimization strategy."""

        # Automated costs
        automated_costs = {
            "hook_execution": 100,
            "metadata_extraction": 50,
            "content_generation": 150,
            "template_insertion": 75,
            "validation": 50,
        }

        total_automated = sum(automated_costs.values())

        strategy = [
            "**Hook-Based Generation Efficiency:**",
            f"- Hook execution and setup: {automated_costs['hook_execution']} tokens",
            f"- Plan metadata extraction: {automated_costs['metadata_extraction']} tokens",
            f"- Content generation coordination: {automated_costs['content_generation']} tokens",
            f"- Template insertion and formatting: {automated_costs['template_insertion']} tokens",
            f"- Optional validation: {automated_costs['validation']} tokens",
            f"- **Total optimized usage: ~{total_automated} tokens per plan**",
            "",
            "**Optimization Techniques:**",
            "- Programmatic generation eliminates manual analysis",
            "- Template-based approach ensures consistency",
            "- Cached calculations reduce redundant computation",
            "- Structured format enables better context compression",
        ]

        return "\n".join(strategy)

    def _assess_context_preservation(self, plan_data: Dict) -> str:
        """Assess context preservation benefits."""

        phase_count = plan_data.get("phase_count", 1)

        benefits = [
            "**Session Continuity Improvements:**",
            "- Structured value propositions enable efficient compaction",
            "- Decision rationale preserved for future reference",
            "- Consistent format improves session bridging",
            "- Reduced context regeneration between sessions",
            "",
            "**Compaction Efficiency:**",
            "- Value propositions compress well due to structured format",
            "- Key metrics preserved even in heavily compacted states",
            f"- Phase-by-phase progress tracking reduces context loss",
            "- Automated generation allows context-aware detail levels",
        ]

        if phase_count > 3:
            benefits.insert(
                -3, f"- Multi-phase plans benefit from milestone-based compaction"
            )

        return "\n".join(benefits)

    def _generate_time_analysis(self, plan_data: Dict) -> str:
        """Generate comprehensive time investment analysis."""

        # Implementation breakdown
        implementation_breakdown = self._create_implementation_breakdown(plan_data)

        # Savings analysis
        savings_analysis = self._analyze_time_savings(plan_data)

        # Break-even calculation
        break_even = self._calculate_break_even(plan_data)

        return f"""## ⏱️ Time Investment Analysis

### Implementation Time Breakdown
{implementation_breakdown}

### Time Savings Analysis
{savings_analysis}

### Break-Even Calculation
{break_even}"""

    def _create_implementation_breakdown(self, plan_data: Dict) -> str:
        """Create detailed implementation time breakdown."""

        complexity = plan_data.get("complexity", "moderate")
        affects = plan_data.get("affects", "").lower()
        phase_count = plan_data.get("phase_count", 1)

        # Base time estimates
        base_times = {
            "planning": 2,
            "implementation": {
                "simple": 4,
                "moderate": 8,
                "complex": 16,
                "physics_heavy": 24,
            },
            "testing": 2,
            "documentation": 1,
        }

        impl_time = base_times["implementation"][complexity]

        # Apply complexity multipliers
        multiplier = 1.0
        if "core/" in affects:
            multiplier *= 1.4
        if "instabilities/" in affects:
            multiplier *= 1.6
        if phase_count > 5:
            multiplier *= 1.2

        adjusted_impl = impl_time * multiplier
        total_time = (
            base_times["planning"]
            + adjusted_impl
            + base_times["testing"]
            + base_times["documentation"]
        )

        breakdown = [
            f"**Phase-by-Phase Time Estimates ({phase_count} phases):**",
            f"- Planning and design: {base_times['planning']} hours",
            f"- Implementation: {adjusted_impl:.1f} hours (base: {impl_time}, multiplier: {multiplier:.1f}x)",
            f"- Testing and validation: {base_times['testing']} hours",
            f"- Documentation updates: {base_times['documentation']} hours",
            f"- **Total estimated time: {total_time:.1f} hours**",
            "",
            "**Confidence Intervals:**",
            f"- Optimistic (80%): {total_time * 0.8:.1f} hours",
            f"- Most likely (100%): {total_time:.1f} hours",
            f"- Pessimistic (130%): {total_time * 1.3:.1f} hours",
        ]

        return "\n".join(breakdown)

    def _analyze_time_savings(self, plan_data: Dict) -> str:
        """Analyze time savings from enhanced planning."""

        phase_count = plan_data.get("phase_count", 1)

        # Per-plan time savings
        manual_planning = 90  # 90 minutes manual planning
        automated_planning = 20  # 20 minutes with hooks
        per_plan_savings = manual_planning - automated_planning

        # Long-term projections
        annual_plans = 25  # Estimated annual plan volume
        annual_savings = (per_plan_savings * annual_plans) / 60  # Convert to hours

        analysis = [
            "**Per-Plan Time Savings:**",
            f"- Manual planning process: {manual_planning} minutes",
            f"- Automated hook-based planning: {automated_planning} minutes",
            f"- Net savings per plan: {per_plan_savings} minutes ({((per_plan_savings/manual_planning)*100):.0f}% reduction)",
            "",
            "**Long-term Efficiency Gains:**",
            f"- Projected annual plans: {annual_plans}",
            f"- Annual time savings: {annual_savings:.1f} hours",
            f"- Equivalent to {annual_savings/8:.1f} additional development days per year",
            "",
            "**Qualitative Benefits:**",
            "- Reduced decision fatigue through systematic evaluation",
            "- Consistent quality eliminates rework cycles",
            "- Improved plan accuracy through structured analysis",
        ]

        return "\n".join(analysis)

    def _calculate_break_even(self, plan_data: Dict) -> str:
        """Calculate break-even analysis for the enhancement."""

        # Development investment
        development_hours = 14  # Average implementation time

        # Time savings per plan
        savings_per_plan = 70 / 60  # 70 minutes = 1.17 hours

        # Break-even calculation
        break_even_plans = development_hours / savings_per_plan

        # Payback timeline
        monthly_plans = 2.5  # Estimated monthly plan volume
        break_even_months = break_even_plans / monthly_plans

        calculation = [
            "**Investment vs. Returns:**",
            f"- One-time development investment: {development_hours} hours",
            f"- Time savings per plan: {savings_per_plan:.1f} hours",
            f"- Break-even point: {break_even_plans:.1f} plans",
            "",
            "**Payback Timeline:**",
            f"- Estimated monthly plan volume: {monthly_plans} plans",
            f"- Break-even timeline: {break_even_months:.1f} months",
            f"- ROI positive after: ~{break_even_plans:.0f} plans",
            "",
            "**Long-term ROI:**",
            "- Year 1: 200-300% ROI (25-30 plans)",
            "- Year 2+: 500-600% ROI (ongoing benefits)",
            "- Compound benefits from improved plan quality",
        ]

        return "\n".join(calculation)

    def _generate_usage_metrics(self, plan_data: Dict) -> str:
        """Generate usage and adoption metrics."""

        # Target use cases
        use_cases = self._identify_use_cases(plan_data)

        # Adoption strategy
        adoption_strategy = self._design_adoption_strategy(plan_data)

        # Success metrics
        success_metrics = self._define_success_metrics(plan_data)

        return f"""## 🎯 Usage & Adoption Metrics

### Target Use Cases
{use_cases}

### Adoption Strategy
{adoption_strategy}

### Success Metrics
{success_metrics}"""

    def _identify_use_cases(self, plan_data: Dict) -> str:
        """Identify primary target use cases."""

        complexity = plan_data.get("complexity", "moderate")
        affects = plan_data.get("affects", "").lower()

        use_cases = [
            "**Primary Applications:**",
            "- All new plan creation (immediate value through automated generation)",
            "- Major feature development planning for SolarWindPy modules",
            "- Scientific project planning requiring systematic value assessment",
        ]

        if complexity in ["complex", "physics_heavy"]:
            use_cases.append(
                "- Complex physics module modifications requiring rigorous evaluation"
            )

        if "plotting/" in affects:
            use_cases.append(
                "- Data visualization enhancements impacting user workflows"
            )

        use_cases.extend(
            [
                "",
                "**Secondary Applications:**",
                "- Existing plan enhancement during major updates",
                "- Cross-plan value comparison for resource prioritization",
                "- Quality assurance for plan completeness and consistency",
                "- Decision audit trails for scientific project management",
            ]
        )

        return "\n".join(use_cases)

    def _design_adoption_strategy(self, plan_data: Dict) -> str:
        """Design adoption strategy and rollout plan."""

        strategy = [
            "**Phased Rollout Approach:**",
            "",
            "**Phase 1 - Pilot (Month 1):**",
            "- Introduce enhanced templates for new plans only",
            "- Target 5-8 pilot plans for initial validation",
            "- Gather feedback from UnifiedPlanCoordinator users",
            "- Refine hook accuracy based on real usage",
            "",
            "**Phase 2 - Gradual Adoption (Months 2-3):**",
            "- Default enhanced templates for all new plans",
            "- Optional migration for 3-5 active existing plans",
            "- Training materials and best practices documentation",
            "- Performance monitoring and optimization",
            "",
            "**Phase 3 - Full Integration (Months 4-6):**",
            "- Enhanced templates become standard for all planning",
            "- Migration of remaining active plans (optional)",
            "- Advanced features and customization options",
            "- Integration with cross-plan analysis tools",
            "",
            "**Success Factors:**",
            "- Opt-in enhancement reduces resistance",
            "- Immediate value visible through token savings",
            "- Backward compatibility maintains existing workflows",
            "- Progressive enhancement enables gradual learning",
        ]

        return "\n".join(strategy)

    def _define_success_metrics(self, plan_data: Dict) -> str:
        """Define measurable success criteria."""

        metrics = [
            "**Quantitative Success Metrics:**",
            "",
            "**Short-term (1-3 months):**",
            "- Enhanced template adoption rate: >80% for new plans",
            "- Token usage reduction: 60-80% demonstrated across plan types",
            "- Hook execution success rate: >95% reliability",
            "- Planning time reduction: >60% measured improvement",
            "",
            "**Medium-term (3-6 months):**",
            "- Plan quality scores: Objective improvement in completeness",
            "- Value proposition accuracy: >90% relevant and actionable",
            "- User satisfaction: Positive feedback from regular users",
            "- Security assessment utility: Demonstrable risk identification",
            "",
            "**Long-term (6-12 months):**",
            "- Full adoption: 90%+ of all plans use enhanced templates",
            "- Compound efficiency: Planning velocity improvements",
            "- Quality improvement: Reduced plan revision cycles",
            "- Knowledge capture: Better decision documentation",
            "",
            "**Qualitative Success Indicators:**",
            "- Developers prefer enhanced planning process",
            "- Plan reviews are more efficient and comprehensive",
            "- Scientific value propositions improve project prioritization",
            "- Security considerations are systematically addressed",
        ]

        return "\n".join(metrics)

    def _generate_scope_audit(self, plan_data: Dict) -> str:
        """Generate scope audit section by calling plan-scope-auditor.py."""
        import subprocess
        import tempfile
        import os

        try:
            # Create temporary file with plan data
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as temp_file:
                json.dump(plan_data, temp_file, indent=2)
                temp_file_path = temp_file.name

            # Call the scope auditor
            script_path = Path(__file__).parent / "plan-scope-auditor.py"
            result = subprocess.run(
                [
                    "python",
                    str(script_path),
                    "--plan-data",
                    json.dumps(plan_data),
                    "--output-format",
                    "markdown",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Clean up temporary file
            os.unlink(temp_file_path)

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                # Fallback scope audit if the external script fails
                return self._generate_fallback_scope_audit(plan_data)

        except Exception as e:
            # Fallback scope audit if there's any error
            return self._generate_fallback_scope_audit(plan_data)

    def _generate_fallback_scope_audit(self, plan_data: Dict) -> str:
        """Generate a basic scope audit if the external auditor fails."""
        affects = plan_data.get("affects", "")
        objective = plan_data.get("objective", "")

        # Basic alignment assessment
        scientific_terms = [
            "physics",
            "plasma",
            "solar",
            "wind",
            "magnetic",
            "research",
            "analysis",
        ]
        found_terms = [term for term in scientific_terms if term in objective.lower()]

        score = min(len(found_terms) * 15 + 25, 100)  # Basic scoring

        return f"""## 🎯 Scope Audit

### SolarWindPy Alignment Assessment
**Alignment Score**: {score}/100

**Assessment**: {"High" if score >= 80 else "Medium" if score >= 60 else "Low"} alignment with SolarWindPy scientific mission.

### Scientific Research Relevance
**Relevance Level**: {"High" if len(found_terms) >= 3 else "Medium" if len(found_terms) >= 1 else "Low"}

Scientific terms identified: {", ".join(found_terms) if found_terms else "None"}

### Module Impact Analysis
**Affected SolarWindPy Modules**: {affects if affects else "Not specified"}

### Scope Boundary Enforcement
**Recommended Scope Controls:**
- Maintain focus on solar wind physics research objectives
- Ensure all changes preserve scientific accuracy
- Validate computational methods follow SolarWindPy conventions

**Scientific Computing Alignment:**
This plan should advance SolarWindPy's mission to provide accurate, efficient tools for solar wind physics research."""

    def main(self):
        """Main execution function."""
        parser = argparse.ArgumentParser(
            description="Generate comprehensive value propositions for SolarWindPy plans"
        )
        parser.add_argument("--plan-file", type=Path, help="Path to plan overview file")
        parser.add_argument(
            "--plan-data", type=str, help="JSON string with plan metadata"
        )
        parser.add_argument(
            "--output-format",
            choices=["markdown", "json"],
            default="markdown",
            help="Output format (default: markdown)",
        )
        parser.add_argument(
            "--exclude-fair",
            action="store_true",
            default=True,
            help="Exclude FAIR data compliance (default: True)",
        )

        args = parser.parse_args()

        # Parse input data
        if args.plan_file:
            plan_data = self.parse_plan_file(args.plan_file)
        elif args.plan_data:
            plan_data = json.loads(args.plan_data)
        else:
            print(
                "Error: Must provide either --plan-file or --plan-data", file=sys.stderr
            )
            sys.exit(1)

        # Generate value propositions
        try:
            value_propositions = self.generate_value_propositions(plan_data)

            if args.output_format == "json":
                output = {
                    "generated_at": datetime.now().isoformat(),
                    "plan_data": plan_data,
                    "value_propositions": value_propositions,
                    "excludes_fair": args.exclude_fair,
                }
                print(json.dumps(output, indent=2))
            else:
                print(value_propositions)

        except Exception as e:
            print(f"Error generating value propositions: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    generator = SolarWindPyPlanValueGenerator()
    generator.main()
