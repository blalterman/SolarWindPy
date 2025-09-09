#!/usr/bin/env python3
"""SolarWindPy Plan Scope Auditor.

Validates that plans remain properly scoped to SolarWindPy scientific research software.
Ensures all development efforts align with solar wind physics research goals and
computational science best practices.

Usage:
    python .claude/hooks/plan-scope-auditor.py --plan-file plans/example/0-Overview.md
    python .claude/hooks/plan-scope-auditor.py --plan-data '{"name":"test","objective":"Add plasma calculations"}'
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Tuple
from datetime import datetime


class SolarWindPyPlanScopeAuditor:
    """Audit plan scope alignment with SolarWindPy scientific research mission."""

    def __init__(self):
        self.solarwindpy_modules = {
            "core/": {
                "weight": 1.0,
                "description": "Core physics calculations and data structures",
                "keywords": [
                    "plasma",
                    "ion",
                    "magnetic",
                    "physics",
                    "dataframe",
                    "multiindex",
                ],
            },
            "instabilities/": {
                "weight": 1.0,
                "description": "Plasma instability analysis and calculations",
                "keywords": ["instability", "alfven", "wave", "turbulence", "analysis"],
            },
            "plotting/": {
                "weight": 0.8,
                "description": "Scientific data visualization",
                "keywords": ["plot", "chart", "visualization", "matplotlib", "figure"],
            },
            "fitfunctions/": {
                "weight": 0.9,
                "description": "Curve fitting and statistical analysis",
                "keywords": [
                    "fit",
                    "curve",
                    "statistical",
                    "optimization",
                    "regression",
                ],
            },
            "spacecraft/": {
                "weight": 0.7,
                "description": "Spacecraft data handling and processing",
                "keywords": [
                    "spacecraft",
                    "mission",
                    "data",
                    "processing",
                    "instrument",
                ],
            },
            "tools/": {
                "weight": 0.6,
                "description": "Scientific utility functions and helpers",
                "keywords": ["utility", "helper", "tool", "function", "constant"],
            },
            "tests/": {
                "weight": 0.5,
                "description": "Testing infrastructure and validation",
                "keywords": ["test", "validation", "coverage", "quality", "pytest"],
            },
            "docs/": {
                "weight": 0.4,
                "description": "Documentation and examples",
                "keywords": ["documentation", "example", "tutorial", "guide", "readme"],
            },
        }

        self.scientific_keywords = {
            "high_value": [
                "plasma",
                "solar",
                "wind",
                "magnetic",
                "field",
                "ion",
                "electron",
                "alfven",
                "thermal",
                "velocity",
                "density",
                "temperature",
                "pressure",
                "physics",
                "calculation",
                "scientific",
                "research",
                "analysis",
            ],
            "medium_value": [
                "data",
                "measurement",
                "spacecraft",
                "instrument",
                "processing",
                "algorithm",
                "computation",
                "numerical",
                "statistical",
                "fitting",
            ],
            "low_value": [
                "utility",
                "helper",
                "tool",
                "function",
                "method",
                "class",
                "test",
                "documentation",
                "example",
                "guide",
            ],
        }

        self.out_of_scope_patterns = {
            "web_development": [
                "web",
                "html",
                "css",
                "javascript",
                "frontend",
                "backend",
                "http",
                "rest",
                "api",
                "server",
                "client",
                "browser",
            ],
            "general_software": [
                "gui",
                "interface",
                "ui",
                "desktop",
                "application",
                "app",
                "database",
                "sql",
                "orm",
                "cache",
                "session",
                "auth",
            ],
            "infrastructure": [
                "deployment",
                "container",
                "docker",
                "kubernetes",
                "cloud",
                "aws",
                "azure",
                "gcp",
                "devops",
                "ci/cd",
            ],
            "business_logic": [
                "user",
                "account",
                "billing",
                "payment",
                "subscription",
                "permission",
                "role",
                "workflow",
                "process",
            ],
        }

        self.scientific_frameworks = [
            "numpy",
            "scipy",
            "pandas",
            "matplotlib",
            "astropy",
            "h5py",
            "netcdf4",
            "xarray",
            "scikit-learn",
            "jupyter",
        ]

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
        metadata["affects"] = self._extract_field(content, r"\*\*Affects\*\*:\s*(.+)")
        metadata["total_phases"] = self._extract_field(
            content, r"\*\*Total Phases\*\*:\s*(\d+)"
        )

        # Extract objective and context
        metadata["objective"] = self._extract_section(content, "Objective")
        metadata["context"] = self._extract_section(content, "Context")
        metadata["technical_requirements"] = self._extract_section(
            content, "Technical Requirements"
        )

        # Count phases by looking for phase overview items
        phase_lines = re.findall(r"- \[ \] \*\*Phase \d+:", content)
        metadata["phase_count"] = len(phase_lines) if phase_lines else 1

        return metadata

    def _extract_field(self, content: str, pattern: str) -> str:
        """Extract a single field using regex."""
        match = re.search(pattern, content, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract a full section from the markdown."""
        pattern = rf"## 🎯 {section_name}\s*\n(.*?)(?=\n## |$)"
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if not match:
            # Try alternative patterns
            pattern = rf"## {section_name}\s*\n(.*?)(?=\n## |$)"
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def calculate_alignment_score(self, plan_data: Dict) -> Tuple[int, str]:
        """Calculate SolarWindPy alignment score (0-100)."""

        score_components = {
            "module_relevance": 0,
            "scientific_keywords": 0,
            "research_impact": 0,
            "scope_risk": 0,
        }

        # Analyze full plan text
        plan_text = (
            plan_data.get("objective", "")
            + " "
            + plan_data.get("context", "")
            + " "
            + plan_data.get("technical_requirements", "")
            + " "
            + plan_data.get("affects", "")
        ).lower()

        # 1. Module Relevance Analysis (40 points)
        module_score = self._assess_module_relevance(plan_data.get("affects", ""))
        score_components["module_relevance"] = int(module_score * 40)

        # 2. Scientific Keywords Analysis (30 points)
        keyword_score = self._assess_scientific_keywords(plan_text)
        score_components["scientific_keywords"] = int(keyword_score * 30)

        # 3. Research Impact Analysis (20 points)
        impact_score = self._assess_research_impact(plan_text)
        score_components["research_impact"] = int(impact_score * 20)

        # 4. Scope Risk Analysis (10 points)
        risk_score = self._assess_scope_risk(plan_text)
        score_components["scope_risk"] = int(risk_score * 10)

        total_score = sum(score_components.values())

        # Generate justification
        justification = self._generate_score_justification(score_components, plan_data)

        return total_score, justification

    def _assess_module_relevance(self, affects: str) -> float:
        """Assess relevance based on affected modules."""
        if not affects:
            return 0.3  # Default score for unspecified modules

        affects_lower = affects.lower()
        total_weight = 0
        matched_modules = []

        for module, info in self.solarwindpy_modules.items():
            if module in affects_lower:
                total_weight += info["weight"]
                matched_modules.append(module)

        if not matched_modules:
            # Check for indirect module references
            for module, info in self.solarwindpy_modules.items():
                if any(keyword in affects_lower for keyword in info["keywords"]):
                    total_weight += info["weight"] * 0.5  # Partial credit
                    matched_modules.append(f"{module} (indirect)")

        # Normalize score (max weight is core/ + instabilities/ = 2.0)
        return min(total_weight / 2.0, 1.0)

    def _assess_scientific_keywords(self, plan_text: str) -> float:
        """Assess scientific relevance based on keywords."""
        # High value keywords (physics/research terms)
        high_matches = sum(
            1
            for keyword in self.scientific_keywords["high_value"]
            if keyword in plan_text
        )
        high_score = min(high_matches / 5.0, 1.0)  # Max 5 high-value keywords

        # Medium value keywords (computational/data terms)
        medium_matches = sum(
            1
            for keyword in self.scientific_keywords["medium_value"]
            if keyword in plan_text
        )
        medium_score = min(medium_matches / 8.0, 0.8)  # Max 8 medium-value keywords

        # Scientific framework mentions
        framework_matches = sum(
            1 for framework in self.scientific_frameworks if framework in plan_text
        )
        framework_score = min(framework_matches / 3.0, 0.6)  # Max 3 frameworks

        return high_score * 0.6 + medium_score * 0.3 + framework_score * 0.1

    def _assess_research_impact(self, plan_text: str) -> float:
        """Assess potential research impact."""
        impact_indicators = [
            "physics",
            "calculation",
            "analysis",
            "measurement",
            "data",
            "scientific",
            "research",
            "accuracy",
            "validation",
            "computation",
        ]

        matches = sum(1 for indicator in impact_indicators if indicator in plan_text)

        # Bonus for specific solar wind physics terms
        physics_bonus = (
            0.2
            if any(
                term in plan_text for term in ["solar wind", "plasma", "magnetic field"]
            )
            else 0
        )

        return min(matches / 6.0 + physics_bonus, 1.0)

    def _assess_scope_risk(self, plan_text: str) -> float:
        """Assess scope creep risk (higher score = lower risk)."""
        total_risk = 0

        for category, patterns in self.out_of_scope_patterns.items():
            category_matches = sum(1 for pattern in patterns if pattern in plan_text)
            if category_matches > 0:
                total_risk += category_matches * 0.2

        # Convert risk to score (0 risk = 1.0 score, high risk = 0.0 score)
        return max(1.0 - min(total_risk, 1.0), 0.0)

    def _generate_score_justification(self, components: Dict, plan_data: Dict) -> str:
        """Generate detailed justification for the alignment score."""
        lines = []

        lines.append("**Alignment Score Breakdown:**")
        lines.append(f"- Module Relevance: {components['module_relevance']}/40 points")
        lines.append(
            f"- Scientific Keywords: {components['scientific_keywords']}/30 points"
        )
        lines.append(f"- Research Impact: {components['research_impact']}/20 points")
        lines.append(f"- Scope Risk Control: {components['scope_risk']}/10 points")

        # Add specific insights
        affects = plan_data.get("affects", "")
        if affects:
            lines.append("")
            lines.append("**Module Impact Analysis:**")
            for module, info in self.solarwindpy_modules.items():
                if module in affects.lower():
                    lines.append(f"- **{module}**: {info['description']}")

        # Add recommendations based on score
        total = sum(components.values())
        lines.append("")
        if total >= 80:
            lines.append("**Assessment**: Excellent alignment with SolarWindPy mission")
        elif total >= 60:
            lines.append("**Assessment**: Good alignment, minor scope considerations")
        elif total >= 40:
            lines.append("**Assessment**: Moderate alignment, scope review recommended")
        else:
            lines.append("**Assessment**: Low alignment, significant scope concerns")

        return "\n".join(lines)

    def generate_scope_audit(self, plan_data: Dict) -> str:
        """Generate complete scope audit section."""

        # Calculate alignment score
        score, justification = self.calculate_alignment_score(plan_data)

        # Assess scientific relevance
        relevance = self._assess_scientific_relevance(plan_data)

        # Analyze module impact
        module_analysis = self._analyze_module_impact(plan_data)

        # Identify scope risks
        scope_risks = self._identify_scope_risks(plan_data)

        return f"""## 🎯 Scope Audit

### SolarWindPy Alignment Assessment
**Alignment Score**: {score}/100

{justification}

### Scientific Research Relevance
**Relevance Level**: {relevance['level']}

{relevance['assessment']}

### Module Impact Analysis
{module_analysis}

### Scope Risk Identification
{scope_risks}

### Scope Boundary Enforcement
**Recommended Scope Controls:**
- Limit implementation to affected modules: {plan_data.get('affects', 'Not specified')}
- Maintain focus on solar wind physics research goals
- Validate all changes preserve scientific accuracy
- Ensure computational methods follow SolarWindPy conventions

**Out-of-Scope Elements to Avoid:**
- Web development or user interface features unrelated to scientific analysis
- General-purpose software infrastructure not specific to research computing
- Business logic or user management functionality
- Non-scientific data processing or visualization features

**Scientific Computing Alignment:**
This plan should advance SolarWindPy's mission to provide accurate, efficient tools for solar wind physics research and space weather analysis."""

    def _assess_scientific_relevance(self, plan_data: Dict) -> Dict:
        """Assess the scientific research relevance of the plan."""
        plan_text = (
            plan_data.get("objective", "") + " " + plan_data.get("context", "")
        ).lower()

        # Count scientific indicators
        physics_terms = [
            "physics",
            "plasma",
            "solar",
            "wind",
            "magnetic",
            "ion",
            "electron",
        ]
        research_terms = ["research", "analysis", "calculation", "measurement", "data"]
        computation_terms = ["algorithm", "numerical", "computational", "scientific"]

        physics_count = sum(1 for term in physics_terms if term in plan_text)
        research_count = sum(1 for term in research_terms if term in plan_text)
        computation_count = sum(1 for term in computation_terms if term in plan_text)

        total_relevance = physics_count * 3 + research_count * 2 + computation_count * 1

        if total_relevance >= 15:
            level = "High"
            assessment = "Strong alignment with solar wind physics research objectives"
        elif total_relevance >= 8:
            level = "Medium"
            assessment = (
                "Moderate scientific computing relevance with research applications"
            )
        elif total_relevance >= 3:
            level = "Low"
            assessment = "Limited scientific research relevance, scope review needed"
        else:
            level = "Very Low"
            assessment = "Minimal scientific content, significant scope concerns"

        return {"level": level, "assessment": assessment}

    def _analyze_module_impact(self, plan_data: Dict) -> str:
        """Analyze impact on SolarWindPy modules."""
        affects = plan_data.get("affects", "").lower()

        if not affects:
            return "**No specific module impact identified** - General plan scope"

        analysis = ["**Affected SolarWindPy Modules:**"]

        for module, info in self.solarwindpy_modules.items():
            if module in affects:
                impact_level = (
                    "High"
                    if info["weight"] >= 0.8
                    else "Medium"
                    if info["weight"] >= 0.5
                    else "Low"
                )
                analysis.append(
                    f"- **{module}** ({impact_level} Impact): {info['description']}"
                )

        # Check for keyword matches
        indirect_matches = []
        for module, info in self.solarwindpy_modules.items():
            if module not in affects:
                if any(keyword in affects for keyword in info["keywords"]):
                    indirect_matches.append(
                        f"- **{module}** (Indirect): {info['description']}"
                    )

        if indirect_matches:
            analysis.append("")
            analysis.append("**Potential Secondary Impacts:**")
            analysis.extend(indirect_matches)

        return "\n".join(analysis)

    def _identify_scope_risks(self, plan_data: Dict) -> str:
        """Identify potential scope creep risks."""
        plan_text = (
            plan_data.get("objective", "")
            + " "
            + plan_data.get("context", "")
            + " "
            + plan_data.get("technical_requirements", "")
        ).lower()

        risks = []

        # Check for out-of-scope patterns
        for category, patterns in self.out_of_scope_patterns.items():
            matches = [pattern for pattern in patterns if pattern in plan_text]
            if matches:
                risks.append(
                    f"**{category.replace('_', ' ').title()} Risk**: {', '.join(matches)}"
                )

        if not risks:
            return "**No significant scope risks identified** - Plan appears well-focused on scientific computing objectives"

        risk_section = ["**Potential Scope Risks Detected:**"]
        risk_section.extend(risks)
        risk_section.append("")
        risk_section.append("**Mitigation Recommendations:**")
        risk_section.append("- Review scope boundaries before implementation")
        risk_section.append("- Focus on scientific computing aspects only")
        risk_section.append("- Validate all features serve solar wind physics research")

        return "\n".join(risk_section)

    def main(self):
        """Main execution function."""
        parser = argparse.ArgumentParser(
            description="Audit plan scope alignment with SolarWindPy scientific mission"
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

        # Generate scope audit
        try:
            scope_audit = self.generate_scope_audit(plan_data)

            if args.output_format == "json":
                score, justification = self.calculate_alignment_score(plan_data)
                output = {
                    "generated_at": datetime.now().isoformat(),
                    "plan_data": plan_data,
                    "alignment_score": score,
                    "scope_audit": scope_audit,
                }
                print(json.dumps(output, indent=2))
            else:
                print(scope_audit)

        except Exception as e:
            print(f"Error generating scope audit: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    auditor = SolarWindPyPlanScopeAuditor()
    auditor.main()
