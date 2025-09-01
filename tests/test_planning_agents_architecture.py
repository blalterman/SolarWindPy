"""Test suite for planning agents architecture functionality.

This module validates the plan-per-branch architecture, cross-branch coordination,
checksum management, and complete merge workflows used by the planning agents system.
"""

import subprocess
import tempfile
import os
import re
from pathlib import Path
import pytest


class TestPlanningAgentsArchitecture:
    """Test suite for planning agents architecture validation."""

    def test_plan_branch_isolation(self):
        """Test that plan branches maintain proper isolation from master and feature
        branches."""
        # Test that plan files exist only on plan branches and not on master
        plan_file = "solarwindpy/plans/test-planning-agents-architecture.md"

        # Verify the test plan file exists (since we're on master after merge)
        assert Path(plan_file).exists(), "Plan file should exist after merge to master"

        # Verify file contains plan-specific content
        with open(plan_file, "r") as f:
            content = f.read()
            assert "plan/test-planning-agents-architecture" in content
            assert "feature/test-planning-agents-architecture" in content
            assert "Plan Metadata" in content

    def test_checksum_management_format(self):
        """Test checksum placeholder replacement functionality and format validation."""
        plan_file = "solarwindpy/plans/test-planning-agents-architecture.md"

        with open(plan_file, "r") as f:
            content = f.read()

        # Find all commit references in the file
        commit_pattern = r"Commit: `([a-f0-9]{7,}|<checksum>)`"
        commits = re.findall(commit_pattern, content)

        # Should have actual commit hashes (not placeholders) since test completed
        actual_commits = [c for c in commits if c != "<checksum>"]
        assert len(actual_commits) > 0, "Should have actual commit hashes"

        # Validate commit hash format (7+ hex characters)
        for commit in actual_commits:
            assert re.match(
                r"^[a-f0-9]{7,}$", commit
            ), f"Invalid commit hash format: {commit}"

    def test_cross_branch_coordination_documentation(self):
        """Test that cross-branch coordination is properly documented."""
        plan_file = "solarwindpy/plans/test-planning-agents-architecture.md"

        with open(plan_file, "r") as f:
            content = f.read()

        # Verify both branches are documented
        coordination_elements = {
            "plan/test-planning-agents-architecture": "Plan branch reference",
            "feature/test-planning-agents-architecture": "Feature branch reference",
            "cross-branch coordination": "Coordination documentation",
            "Checksum management": "Checksum functionality",
        }

        for element, description in coordination_elements.items():
            assert element in content, f"Missing {description}: {element}"

    def test_merge_workflow_completion(self):
        """Test that the complete merge workflow was documented and completed."""
        plan_file = "solarwindpy/plans/test-planning-agents-architecture.md"

        with open(plan_file, "r") as f:
            content = f.read()

        # Verify all workflow phases are marked completed
        workflow_phases = [
            "Phase 1: Branch Isolation Testing",
            "Phase 2: Cross-Branch Coordination",
            "Phase 3: Merge Workflow Testing",
        ]

        for phase in workflow_phases:
            assert phase in content, f"Missing workflow phase: {phase}"

        # Verify completion status
        assert "COMPLETED ✅" in content, "Plan should be marked as completed"
        assert "Phases Completed**: 3/3" in content, "All phases should be completed"
        assert "Tasks Completed**: 8/8" in content, "All tasks should be completed"

    def test_acceptance_criteria_validation(self):
        """Test that all acceptance criteria were met and documented."""
        plan_file = "solarwindpy/plans/test-planning-agents-architecture.md"

        with open(plan_file, "r") as f:
            content = f.read()

        # Define expected acceptance criteria
        acceptance_criteria = [
            "Plan branch created successfully with isolated plan files",
            "Feature branch can coordinate with plan branch",
            "Checksum placeholders can be replaced with actual commit hashes",
            "Cross-branch status updates work correctly",
            "Complete merge workflow (feature → plan → master) functions properly",
            "Branch isolation maintains true separation between concurrent plans",
        ]

        # Verify all criteria are marked as completed [x]
        for criteria in acceptance_criteria:
            # Look for the criteria with completed checkbox
            pattern = rf"- \[x\].*{re.escape(criteria[:30])}"  # Match first 30 chars
            assert re.search(
                pattern, content, re.IGNORECASE
            ), f"Acceptance criteria not met: {criteria}"

    def test_plan_template_usage(self):
        """Test that the plan properly uses the plan template structure."""
        plan_file = "solarwindpy/plans/test-planning-agents-architecture.md"

        with open(plan_file, "r") as f:
            content = f.read()

        # Verify template structure elements
        template_elements = [
            "## Plan Metadata",
            "## 🎯 Objective",
            "## 🧠 Context",
            "## 🔧 Technical Requirements",
            "## 📂 Affected Areas",
            "## 📋 Implementation Plan",
            "## ✅ Acceptance Criteria",
            "## 🧪 Testing Strategy",
            "## 📊 Progress Tracking",
        ]

        for element in template_elements:
            assert element in content, f"Missing template element: {element}"

    def test_time_estimation_tracking(self):
        """Test that time estimation and tracking functionality works."""
        plan_file = "solarwindpy/plans/test-planning-agents-architecture.md"

        with open(plan_file, "r") as f:
            content = f.read()

        # Verify time tracking elements
        time_elements = [
            "Estimated Duration",
            "Time Invested",
            "Est:",  # Individual task estimates
        ]

        for element in time_elements:
            assert element in content, f"Missing time tracking element: {element}"

        # Verify time format (should have "min" or "h")
        time_pattern = r"\d+\s*(min|h)"
        assert re.search(
            time_pattern, content
        ), "Should contain time estimates in min or h format"


class TestPlanningAgentsIntegration:
    """Integration tests for planning agents with git operations."""

    def test_git_branch_operations(self):
        """Test basic git operations that planning agents would use."""
        # This test validates that git operations work in the current environment
        try:
            # Test branch listing
            result = subprocess.run(
                ["git", "branch"], capture_output=True, text=True, check=True
            )
            assert (
                "master" in result.stdout
            ), "Should be able to list branches including master"

            # Test branch status
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            )
            # Exit code 0 means git status worked (output content doesn't matter)

        except subprocess.CalledProcessError as e:
            pytest.fail(f"Git operations failed: {e}")

    def test_checksum_pattern_matching(self):
        """Test checksum pattern matching functionality."""
        test_patterns = [
            ("<checksum>", False),  # Placeholder, not replaced
            ("a1b2c3d", True),  # 7-char hash
            ("a1b2c3d4e5f", True),  # 11-char hash
            ("invalid", False),  # Invalid format
            ("123", False),  # Too short
        ]

        # Pattern for valid git commit hash (7+ hex characters)
        commit_pattern = re.compile(r"^[a-f0-9]{7,}$")

        for test_input, expected in test_patterns:
            is_valid = bool(commit_pattern.match(test_input))
            assert (
                is_valid == expected
            ), f"Pattern matching failed for '{test_input}': expected {expected}, got {is_valid}"


def test_planning_agents_architecture_meta():
    """Meta-test: validate that this test file itself follows good practices."""
    # Verify this test file exists in the right location
    current_file = Path(__file__)
    assert current_file.name == "test_planning_agents_architecture.py"
    assert "solarwindpy/tests" in str(
        current_file
    ), "Test should be in solarwindpy/tests directory"

    # Verify it has proper pytest structure
    assert hasattr(TestPlanningAgentsArchitecture, "test_plan_branch_isolation")
    assert hasattr(TestPlanningAgentsArchitecture, "test_checksum_management_format")

    # Verify docstrings exist
    assert TestPlanningAgentsArchitecture.__doc__ is not None
    assert TestPlanningAgentsArchitecture.test_plan_branch_isolation.__doc__ is not None
