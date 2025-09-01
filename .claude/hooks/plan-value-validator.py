#!/usr/bin/env python3
"""SolarWindPy Plan Value Proposition Validator.

Validates completeness and accuracy of plan value propositions.
Ensures all required sections are present and contain meaningful content.

Usage:
    python .claude/hooks/plan-value-validator.py --plan-file plans/example/0-Overview.md
    python .claude/hooks/plan-value-validator.py --plan-file plans/example/0-Overview.md --strict
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime


class SolarWindPyPlanValueValidator:
    """Validate value propositions in SolarWindPy development plans."""

    def __init__(self):
        self.required_sections = {
            "value_proposition_analysis": {
                "pattern": r"## 📊 Value Proposition Analysis",
                "required_subsections": [
                    "Scientific Software Development Value",
                    "Developer Productivity Value",
                ],
            },
            "resource_cost_analysis": {
                "pattern": r"## 💰 Resource & Cost Analysis",
                "required_subsections": [
                    "Development Investment",
                    "Token Usage Economics",
                ],
            },
            "risk_assessment": {
                "pattern": r"## ⚠️ Risk Assessment & Mitigation",
                "required_subsections": [
                    "Technical Implementation Risks",
                    "Project Management Risks",
                ],
            },
            "security_proposition": {
                "pattern": r"## 🔒 Security Proposition",
                "required_subsections": ["Code-Level Security Assessment"],
                "forbidden_content": [
                    "fair",
                    "metadata security",
                    "persistent identifier",
                    "ontology",
                    "data format integrity",
                ],
            },
            "scope_audit": {
                "pattern": r"## 🎯 Scope Audit",
                "required_subsections": [
                    "SolarWindPy Alignment Assessment",
                    "Scientific Research Relevance",
                    "Module Impact Analysis",
                ],
                "required_patterns": [
                    r"Alignment Score.*\d+/100",
                    r"Relevance Level.*(?:High|Medium|Low)",
                    r"Scope Boundary Enforcement",
                ],
            },
            "token_optimization": {
                "pattern": r"## 💾 Token Usage Optimization",
                "required_subsections": [
                    "Current Token Usage Patterns",
                    "Optimized Token Usage Strategy",
                ],
            },
            "time_analysis": {
                "pattern": r"## ⏱️ Time Investment Analysis",
                "required_subsections": [
                    "Implementation Time Breakdown",
                    "Time Savings Analysis",
                ],
            },
            "usage_metrics": {
                "pattern": r"## 🎯 Usage & Adoption Metrics",
                "required_subsections": ["Target Use Cases", "Success Metrics"],
            },
        }

        self.token_patterns = {
            "token_numbers": r"(\d{1,5})\s*tokens?",
            "token_savings": r"(\d{1,3})%\s*(?:reduction|savings?)",
            "time_estimates": r"(\d+(?:\.\d+)?)\s*(?:hours?|minutes?)",
        }

    def validate_plan_file(self, plan_file: Path, strict: bool = False) -> Dict:
        """Validate a complete plan file."""
        if not plan_file.exists():
            return {
                "valid": False,
                "error": f"Plan file not found: {plan_file}",
                "sections": {},
            }

        with open(plan_file, "r", encoding="utf-8") as f:
            content = f.read()

        results = {
            "valid": True,
            "plan_file": str(plan_file),
            "validated_at": datetime.now().isoformat(),
            "strict_mode": strict,
            "sections": {},
            "overall_issues": [],
            "summary": {},
        }

        # Validate each required section
        for section_key, section_config in self.required_sections.items():
            section_result = self._validate_section(
                content, section_key, section_config, strict
            )
            results["sections"][section_key] = section_result

            if not section_result["passed"]:
                results["valid"] = False

        # Overall validation checks
        overall_issues = self._validate_overall_consistency(content, strict)
        results["overall_issues"] = overall_issues
        if overall_issues:
            results["valid"] = False

        # Generate summary
        results["summary"] = self._generate_summary(results)

        return results

    def _validate_section(
        self, content: str, section_key: str, section_config: Dict, strict: bool
    ) -> Dict:
        """Validate a specific value proposition section."""
        result = {
            "section_name": section_key.replace("_", " ").title(),
            "passed": True,
            "issues": [],
            "warnings": [],
            "content_quality": "good",
        }

        # Check if section exists
        section_match = re.search(section_config["pattern"], content, re.IGNORECASE)
        if not section_match:
            result["passed"] = False
            result["issues"].append(f"Section '{result['section_name']}' not found")
            return result

        # Extract section content
        section_content = self._extract_section_content(
            content, section_config["pattern"]
        )
        if not section_content:
            result["passed"] = False
            result["issues"].append(f"Section '{result['section_name']}' is empty")
            return result

        # Check required subsections
        if "required_subsections" in section_config:
            for subsection in section_config["required_subsections"]:
                if subsection.lower() not in section_content.lower():
                    if strict:
                        result["passed"] = False
                        result["issues"].append(
                            f"Missing required subsection: {subsection}"
                        )
                    else:
                        result["warnings"].append(
                            f"Recommended subsection missing: {subsection}"
                        )

        # Check forbidden content (especially for security section)
        if "forbidden_content" in section_config:
            for forbidden in section_config["forbidden_content"]:
                if forbidden.lower() in section_content.lower():
                    result["passed"] = False
                    result["issues"].append(
                        f"Forbidden content detected: '{forbidden}' (FAIR compliance not implemented)"
                    )

        # Section-specific validation
        if section_key == "security_proposition":
            security_result = self._validate_security_section(section_content, strict)
            result["issues"].extend(security_result["issues"])
            result["warnings"].extend(security_result["warnings"])
            if security_result["issues"]:
                result["passed"] = False

        elif section_key == "token_optimization":
            token_result = self._validate_token_section(section_content, strict)
            result["issues"].extend(token_result["issues"])
            result["warnings"].extend(token_result["warnings"])
            if token_result["issues"]:
                result["passed"] = False

        elif section_key == "time_analysis":
            time_result = self._validate_time_section(section_content, strict)
            result["issues"].extend(time_result["issues"])
            result["warnings"].extend(time_result["warnings"])
            if time_result["issues"]:
                result["passed"] = False

        elif section_key == "scope_audit":
            scope_result = self._validate_scope_section(section_content, strict)
            result["issues"].extend(scope_result["issues"])
            result["warnings"].extend(scope_result["warnings"])
            if scope_result["issues"]:
                result["passed"] = False

        # Assess content quality
        result["content_quality"] = self._assess_content_quality(section_content)

        return result

    def _extract_section_content(self, content: str, section_pattern: str) -> str:
        """Extract content of a specific section."""
        # Find section start
        section_match = re.search(section_pattern, content, re.IGNORECASE)
        if not section_match:
            return ""

        # Find content between this section and the next section or end
        start_pos = section_match.end()
        next_section_pattern = r"\n## [🎯📊💰⚠️🔒💾⏱️🎯]"
        next_match = re.search(next_section_pattern, content[start_pos:])

        if next_match:
            end_pos = start_pos + next_match.start()
            section_content = content[start_pos:end_pos]
        else:
            section_content = content[start_pos:]

        return section_content.strip()

    def _validate_security_section(self, section_content: str, strict: bool) -> Dict:
        """Validate security proposition section specifically."""
        result = {"issues": [], "warnings": []}

        # Required security components (code-level only)
        required_components = {
            "dependency": ["dependency", "package", "vulnerability", "pip audit"],
            "authentication": ["auth", "access", "control", "permission", "user"],
            "attack_surface": [
                "exposure",
                "interface",
                "attack",
                "surface",
                "validation",
            ],
            "development_security": [
                "workflow",
                "ci/cd",
                "development",
                "git",
                "review",
            ],
        }

        missing_components = []
        for component, keywords in required_components.items():
            if not any(keyword in section_content.lower() for keyword in keywords):
                missing_components.append(component)

        if missing_components:
            if strict:
                result["issues"].extend(
                    [
                        f"Missing {comp} assessment in security section"
                        for comp in missing_components
                    ]
                )
            else:
                result["warnings"].extend(
                    [
                        f"Consider adding {comp} assessment to security section"
                        for comp in missing_components
                    ]
                )

        # Check for proper scope limitations
        scope_indicators = [
            "code-level",
            "explicitly excluded",
            "not implemented",
            "outside scope",
        ]

        if not any(
            indicator in section_content.lower() for indicator in scope_indicators
        ):
            result["warnings"].append(
                "Security section should clarify scope limitations (code-level only)"
            )

        # Verify FAIR exclusion is explicit
        if "fair" in section_content.lower():
            fair_exclusion_phrases = [
                "excluded",
                "not implemented",
                "outside scope",
                "not applicable",
            ]
            if not any(
                phrase in section_content.lower() for phrase in fair_exclusion_phrases
            ):
                result["issues"].append(
                    "FAIR data compliance mentioned but exclusion not clear"
                )

        return result

    def _validate_token_section(self, section_content: str, strict: bool) -> Dict:
        """Validate token usage optimization section."""
        result = {"issues": [], "warnings": []}

        # Extract token numbers
        token_numbers = re.findall(
            self.token_patterns["token_numbers"], section_content
        )

        if not token_numbers:
            result["issues"].append(
                "No token usage numbers found in token optimization section"
            )
            return result

        # Validate token number ranges
        for token_str in token_numbers:
            tokens = int(token_str)
            if tokens < 50:
                result["warnings"].append(
                    f"Token estimate {tokens} seems unusually low"
                )
            elif tokens > 15000:
                result["issues"].append(
                    f"Token estimate {tokens} seems unrealistically high"
                )

        # Check for savings percentage
        savings_matches = re.findall(
            self.token_patterns["token_savings"], section_content
        )

        if not savings_matches:
            result["issues"].append("No token savings percentage found")
        else:
            for savings_str in savings_matches:
                savings_percent = int(savings_str)
                if savings_percent < 30:
                    result["warnings"].append(
                        f"Token savings {savings_percent}% lower than expected (30-80%)"
                    )
                elif savings_percent > 90:
                    result["warnings"].append(
                        f"Token savings {savings_percent}% higher than expected (30-80%)"
                    )

        # Check for current vs optimized comparison
        comparison_indicators = [
            "current",
            "optimized",
            "manual",
            "automated",
            "vs",
            "versus",
        ]
        if not any(
            indicator in section_content.lower() for indicator in comparison_indicators
        ):
            result["warnings"].append(
                "Token section should include current vs optimized comparison"
            )

        return result

    def _validate_time_section(self, section_content: str, strict: bool) -> Dict:
        """Validate time investment analysis section."""
        result = {"issues": [], "warnings": []}

        # Extract time estimates
        time_estimates = re.findall(
            self.token_patterns["time_estimates"], section_content
        )

        if not time_estimates:
            result["warnings"].append(
                "No specific time estimates found in time analysis"
            )

        # Check for required components
        required_time_components = [
            "implementation",
            "breakdown",
            "savings",
            "break-even",
        ]

        missing_components = []
        for component in required_time_components:
            if component not in section_content.lower():
                missing_components.append(component)

        if missing_components:
            if strict:
                result["issues"].extend(
                    [
                        f"Missing {comp} analysis in time section"
                        for comp in missing_components
                    ]
                )
            else:
                result["warnings"].extend(
                    [
                        f"Consider adding {comp} analysis to time section"
                        for comp in missing_components
                    ]
                )

        # Check for realistic time estimates
        for time_str in time_estimates:
            time_value = float(time_str)
            # Assuming hours if no unit specified
            if time_value > 100:  # More than 100 hours seems excessive
                result["warnings"].append(
                    f"Time estimate {time_value} seems high for typical plan"
                )
            elif time_value < 0.5:  # Less than 30 minutes seems too low
                result["warnings"].append(
                    f"Time estimate {time_value} seems low for meaningful work"
                )

        return result

    def _validate_scope_section(self, section_content: str, strict: bool) -> Dict:
        """Validate scope audit section specifically."""
        result = {"issues": [], "warnings": []}

        # Check for alignment score
        alignment_score_pattern = r"Alignment Score[:\s]*(\d+)/100"
        alignment_match = re.search(
            alignment_score_pattern, section_content, re.IGNORECASE
        )

        if not alignment_match:
            result["issues"].append("Missing alignment score (should be X/100 format)")
        else:
            score = int(alignment_match.group(1))
            if score < 40:
                result["warnings"].append(
                    f"Low alignment score ({score}/100) - scope review recommended"
                )
            elif score < 60:
                result["warnings"].append(
                    f"Moderate alignment score ({score}/100) - consider scope refinement"
                )

        # Check for relevance level
        relevance_pattern = r"Relevance Level[:\s]*(High|Medium|Low)"
        if not re.search(relevance_pattern, section_content, re.IGNORECASE):
            result["issues"].append(
                "Missing scientific research relevance level assessment"
            )

        # Check for module impact analysis
        module_indicators = [
            "core/",
            "plotting/",
            "fitfunctions/",
            "instabilities/",
            "spacecraft/",
            "tools/",
            "tests/",
            "docs/",
        ]
        has_module_analysis = any(
            module in section_content.lower() for module in module_indicators
        )

        if not has_module_analysis:
            result["warnings"].append(
                "No specific SolarWindPy module impact identified"
            )

        # Check for scope boundary enforcement section
        boundary_indicators = [
            "scope boundary",
            "out-of-scope",
            "scientific computing",
            "solar wind physics",
        ]
        has_boundary_discussion = any(
            indicator in section_content.lower() for indicator in boundary_indicators
        )

        if not has_boundary_discussion:
            result["issues"].append("Missing scope boundary enforcement discussion")

        # Check for scientific computing focus
        scientific_indicators = [
            "physics",
            "research",
            "scientific",
            "computation",
            "analysis",
        ]
        scientific_count = sum(
            1
            for indicator in scientific_indicators
            if indicator in section_content.lower()
        )

        if scientific_count < 2:
            result["warnings"].append(
                "Limited scientific computing terminology - verify research focus"
            )

        # Check for out-of-scope risk patterns (should be minimal or addressed)
        risky_patterns = ["web", "ui", "frontend", "backend", "database", "api"]
        found_risks = [
            pattern for pattern in risky_patterns if pattern in section_content.lower()
        ]

        if found_risks:
            result["warnings"].append(
                f"Potential out-of-scope elements mentioned: {', '.join(found_risks)}"
            )

        return result

    def _validate_overall_consistency(self, content: str, strict: bool) -> List[str]:
        """Validate overall consistency across sections."""
        issues = []

        # Check for placeholder content that wasn't replaced
        placeholders = [
            "VALUE_PROPOSITION_PLACEHOLDER",
            "AUTO-GENERATED",
            "[Generated content will include",
            "[Auto-generated",
        ]

        for placeholder in placeholders:
            if placeholder in content:
                issues.append(f"Placeholder content not replaced: {placeholder}")

        # Check for consistent token estimates across sections
        all_token_numbers = re.findall(self.token_patterns["token_numbers"], content)
        if len(set(all_token_numbers)) < 2 and len(all_token_numbers) > 3:
            issues.append("Token estimates appear suspiciously uniform across sections")

        # Check for FAIR compliance mentions outside security section
        fair_mentions = re.findall(r"fair\s+data", content, re.IGNORECASE)
        if len(fair_mentions) > 1:  # One mention allowed in security section
            issues.append(
                "Multiple FAIR data mentions found - should be limited to security exclusion"
            )

        return issues

    def _assess_content_quality(self, section_content: str) -> str:
        """Assess the quality of section content."""
        if len(section_content) < 100:
            return "poor"
        elif len(section_content) < 300:
            return "minimal"
        elif len(section_content) > 2000:
            return "verbose"
        else:
            return "good"

    def _generate_summary(self, results: Dict) -> Dict:
        """Generate validation summary."""
        total_sections = len(results["sections"])
        passed_sections = sum(
            1 for section in results["sections"].values() if section["passed"]
        )

        total_issues = sum(
            len(section["issues"]) for section in results["sections"].values()
        )
        total_warnings = sum(
            len(section["warnings"]) for section in results["sections"].values()
        )

        return {
            "overall_status": "PASSED" if results["valid"] else "FAILED",
            "sections_passed": f"{passed_sections}/{total_sections}",
            "total_issues": total_issues,
            "total_warnings": total_warnings,
            "completion_percentage": (passed_sections / total_sections) * 100,
            "recommendation": self._get_recommendation(
                results["valid"], total_issues, total_warnings
            ),
        }

    def _get_recommendation(
        self, valid: bool, total_issues: int, total_warnings: int
    ) -> str:
        """Get recommendation based on validation results."""
        if valid and total_warnings == 0:
            return "Plan ready for implementation"
        elif valid and total_warnings <= 3:
            return "Plan acceptable with minor improvements suggested"
        elif not valid and total_issues <= 2:
            return "Plan needs minor fixes before implementation"
        elif not valid and total_issues <= 5:
            return "Plan needs significant improvements"
        else:
            return "Plan requires major revision before implementation"

    def generate_report(self, validation_results: Dict, format: str = "text") -> str:
        """Generate human-readable validation report."""
        if format == "json":
            return json.dumps(validation_results, indent=2)

        # Text format report
        report_lines = []

        # Header
        report_lines.append("# SolarWindPy Plan Value Proposition Validation Report")
        report_lines.append(f"**Generated**: {validation_results['validated_at']}")
        report_lines.append(f"**Plan File**: {validation_results['plan_file']}")
        report_lines.append(
            f"**Strict Mode**: {'Yes' if validation_results['strict_mode'] else 'No'}"
        )
        report_lines.append("")

        # Overall status
        status_emoji = "✅" if validation_results["valid"] else "❌"
        report_lines.append(
            f"## {status_emoji} Overall Status: {validation_results['summary']['overall_status']}"
        )
        report_lines.append(
            f"- **Sections Passed**: {validation_results['summary']['sections_passed']}"
        )
        report_lines.append(
            f"- **Total Issues**: {validation_results['summary']['total_issues']}"
        )
        report_lines.append(
            f"- **Total Warnings**: {validation_results['summary']['total_warnings']}"
        )
        report_lines.append(
            f"- **Completion**: {validation_results['summary']['completion_percentage']:.0f}%"
        )
        report_lines.append(
            f"- **Recommendation**: {validation_results['summary']['recommendation']}"
        )
        report_lines.append("")

        # Section-by-section results
        report_lines.append("## Section Validation Results")
        report_lines.append("")

        for section_key, section_result in validation_results["sections"].items():
            section_emoji = "✅" if section_result["passed"] else "❌"
            quality_indicator = {
                "good": "👍",
                "minimal": "⚠️",
                "poor": "👎",
                "verbose": "📝",
            }
            quality_emoji = quality_indicator.get(
                section_result["content_quality"], "❓"
            )

            report_lines.append(
                f"### {section_emoji} {section_result['section_name']} {quality_emoji}"
            )

            if section_result["issues"]:
                report_lines.append("**Issues:**")
                for issue in section_result["issues"]:
                    report_lines.append(f"- ❌ {issue}")

            if section_result["warnings"]:
                report_lines.append("**Warnings:**")
                for warning in section_result["warnings"]:
                    report_lines.append(f"- ⚠️ {warning}")

            if not section_result["issues"] and not section_result["warnings"]:
                report_lines.append("No issues found.")

            report_lines.append("")

        # Overall issues
        if validation_results["overall_issues"]:
            report_lines.append("## Overall Consistency Issues")
            for issue in validation_results["overall_issues"]:
                report_lines.append(f"- ❌ {issue}")
            report_lines.append("")

        # Fix suggestions
        if not validation_results["valid"]:
            report_lines.append("## Suggested Fixes")
            report_lines.extend(self._generate_fix_suggestions(validation_results))
            report_lines.append("")

        return "\n".join(report_lines)

    def _generate_fix_suggestions(self, validation_results: Dict) -> List[str]:
        """Generate specific fix suggestions based on validation results."""
        suggestions = []

        for section_key, section_result in validation_results["sections"].items():
            if not section_result["passed"]:
                section_name = section_result["section_name"]

                for issue in section_result["issues"]:
                    if "not found" in issue:
                        suggestions.append(
                            f"- Add the missing '{section_name}' section to your plan"
                        )
                    elif "is empty" in issue:
                        suggestions.append(
                            f"- Add content to the '{section_name}' section"
                        )
                    elif "FAIR compliance" in issue:
                        suggestions.append(
                            "- Remove FAIR data references from security section"
                        )
                    elif "Missing" in issue and "subsection" in issue:
                        missing_subsection = (
                            issue.split(": ")[1] if ": " in issue else "subsection"
                        )
                        suggestions.append(
                            f"- Add '{missing_subsection}' subsection to '{section_name}'"
                        )
                    elif "token" in issue.lower():
                        suggestions.append(
                            "- Add specific token usage numbers and savings percentages"
                        )
                    elif "time" in issue.lower():
                        suggestions.append(
                            "- Include time estimates and implementation breakdown"
                        )

        # Overall suggestions
        for issue in validation_results["overall_issues"]:
            if "placeholder" in issue.lower():
                suggestions.append(
                    "- Replace all placeholder content with actual generated content"
                )
            elif "fair" in issue.lower():
                suggestions.append(
                    "- Limit FAIR data mentions to security section exclusion only"
                )

        if not suggestions:
            suggestions.append("- Review warnings and consider suggested improvements")

        return suggestions

    def can_complete_plan(self, plan_file: Path) -> Tuple[bool, str]:
        """Check if plan can be marked as completed (integration with plan-completion-
        manager)."""
        validation_results = self.validate_plan_file(plan_file, strict=False)

        if validation_results["valid"]:
            return True, "Plan value propositions validated successfully"
        else:
            issues_summary = []
            for section_result in validation_results["sections"].values():
                if not section_result["passed"]:
                    issues_summary.extend(section_result["issues"])

            return (
                False,
                f"Value proposition validation failed: {'; '.join(issues_summary[:3])}",
            )

    def main(self):
        """Main execution function."""
        parser = argparse.ArgumentParser(
            description="Validate SolarWindPy plan value propositions"
        )
        parser.add_argument(
            "--plan-file",
            type=Path,
            required=True,
            help="Path to plan overview file to validate",
        )
        parser.add_argument(
            "--strict", action="store_true", help="Enable strict validation mode"
        )
        parser.add_argument(
            "--report-format",
            choices=["text", "json"],
            default="text",
            help="Report format (default: text)",
        )
        parser.add_argument(
            "--quiet",
            action="store_true",
            help="Only output validation result (pass/fail)",
        )

        args = parser.parse_args()

        try:
            validation_results = self.validate_plan_file(args.plan_file, args.strict)

            if args.quiet:
                print("PASS" if validation_results["valid"] else "FAIL")
                sys.exit(0 if validation_results["valid"] else 1)

            report = self.generate_report(validation_results, args.report_format)
            print(report)

            # Exit with error code if validation failed
            sys.exit(0 if validation_results["valid"] else 1)

        except Exception as e:
            print(f"Error validating plan: {e}", file=sys.stderr)
            sys.exit(2)


if __name__ == "__main__":
    validator = SolarWindPyPlanValueValidator()
    validator.main()
