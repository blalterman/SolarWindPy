import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from plans.issues_from_plans import infer_issue_title


def test_infer_issue_title_preserves_numbers(tmp_path):
    path = (
        tmp_path
        / "combined_plan_with_checklist_documentation"
        / "1-Overview-and-Goals.md"
    )
    path.parent.mkdir()
    path.touch()
    title = infer_issue_title(path, "")
    assert title == "Combined Plan With Checklist Documentation – 1 Overview and Goals"


def test_infer_issue_title_uses_frontmatter_name(tmp_path):
    path = tmp_path / "combined_plan_with_checklist_documentation" / "2-Another.md"
    path.parent.mkdir(exist_ok=True)
    path.touch()
    title = infer_issue_title(path, "Custom Name")
    assert title == "Combined Plan With Checklist Documentation – 2 Custom Name"
