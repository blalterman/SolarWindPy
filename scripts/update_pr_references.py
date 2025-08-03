#!/usr/bin/env python
"""Update PR references in combined_architecture_workflow.md.

This script replaces ``#PR_NUMBER`` placeholders with a specific pull request
number when a PR is opened or reopened and annotates that number as closed when
the pull request closes.

Examples
--------
Update references when a pull request is opened::

    python scripts/update_pr_references.py --pr 123 --action opened

Update references when a pull request is reopened::

    python scripts/update_pr_references.py --pr 123 --action reopened

Mark references as closed when a pull request closes::

    python scripts/update_pr_references.py --pr 123 --action closed
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FILE_PATH = Path("solarwindpy/plans/combined_architecture_workflow.md")


def replace_placeholder(pr_number: int) -> bool:
    """Insert the pull request number in place of ``#PR_NUMBER``.

    Parameters
    ----------
    pr_number : int
        Pull request number to insert.

    Returns
    -------
    bool
        ``True`` if a replacement was made, ``False`` otherwise.
    """
    try:
        content = FILE_PATH.read_text()
    except FileNotFoundError:
        return False

    new_content, count = re.subn("#PR_NUMBER", f"#{pr_number}", content)
    if count == 0:
        return False
    FILE_PATH.write_text(new_content)
    return True


def mark_closed(pr_number: int) -> bool:
    """Append ``(closed)`` after the pull request number.

    Parameters
    ----------
    pr_number : int
        Pull request number to mark as closed.

    Returns
    -------
    bool
        ``True`` if the number was annotated, ``False`` otherwise.
    """
    try:
        content = FILE_PATH.read_text()
    except FileNotFoundError:
        return False

    pattern = rf"#{pr_number}(?! \(closed\))"
    new_content, count = re.subn(pattern, f"#{pr_number} (closed)", content)
    if count == 0:
        return False
    FILE_PATH.write_text(new_content)
    return True


def main() -> None:
    """Parse arguments and update PR references."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr", type=int, required=True, help="Pull request number.")
    parser.add_argument(
        "--action",
        choices=["opened", "reopened", "closed"],
        required=True,
        help="Pull request action triggering the update.",
    )
    args = parser.parse_args()

    if args.action in {"opened", "reopened"}:
        success = replace_placeholder(args.pr)
        if args.action == "opened" and not success:
            sys.exit(1)
    else:
        if not mark_closed(args.pr):
            sys.exit(1)


if __name__ == "__main__":
    main()
