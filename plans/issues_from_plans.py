#!/usr/bin/env python3
"""Create GitHub issues from plan files.

The script parses markdown files under ``solarwindpy/plans`` that contain
YAML frontmatter and converts them into GitHub issues. Frontmatter fields
``name``, ``about`` and ``labels`` are used for the issue metadata while the
markdown content beginning with ``## 🧠 Context`` becomes the issue body. The
final issue title combines the containing directory name with any numeric
prefix in the filename to preserve ordering. Optionally a specific
subdirectory can be scanned via the ``-d/--directory`` CLI argument.
Authentication uses a token supplied via ``--token`` or the ``GITHUB_TOKEN_SOLARWINDPY``.
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
import yaml
from tabulate import tabulate

GITHUB_API = "https://api.github.com"


def load_markdown_plan(path: Path) -> Dict[str, object]:
    """Parse a markdown plan file.

    Parameters
    ----------
    path : Path
        Location of the markdown file.

    Returns
    -------
    dict
        Dictionary with ``name``, ``about``, ``labels`` and ``body`` keys.
    """

    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"No YAML frontmatter found in {path}")

    _, fm, rest = text.split("---", 2)
    meta = yaml.safe_load(fm)

    context_index = rest.find("## 🧠 Context")
    body = rest[context_index:].lstrip() if context_index != -1 else rest.lstrip("\n")

    return {
        "name": meta.get("name", "").strip(),
        "about": meta.get("about", "").strip(),
        "labels": meta.get("labels", []),
        "body": body,
    }


def fetch_existing_issue_titles(owner: str, repo: str, token: str) -> List[str]:
    """Retrieve titles of all issues in a repository.

    Parameters
    ----------
    owner : str
        GitHub organization or username.
    repo : str
        GitHub repository name.
    token : str
        Personal access token.

    Returns
    -------
    list of str
        Titles of existing issues (open and closed).
    """

    titles: List[str] = []
    headers = {"Authorization": f"token {token}"}
    page = 1
    while True:
        params = {"state": "all", "per_page": 100, "page": page}
        url = f"{GITHUB_API}/repos/{owner}/{repo}/issues"
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            break
        titles.extend(issue["title"] for issue in data)
        page += 1
    return titles


def create_issue(
    owner: str, repo: str, token: str, title: str, body: str, labels: List[str]
) -> Dict[str, object]:
    """Create a GitHub issue.

    Parameters
    ----------
    owner, repo, token, title, body, labels : str or list of str
        Standard GitHub issue parameters.

    Returns
    -------
    dict
        Response JSON from GitHub API.
    """

    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    payload = {"title": title, "body": body, "labels": labels}
    resp = requests.post(url, json=payload, headers=headers)
    resp.raise_for_status()
    return resp.json()


def infer_owner_repo() -> Tuple[Optional[str], Optional[str]]:
    """Infer repository information from the local Git remote.

    Returns
    -------
    tuple of (str or None, str or None)
        Repository owner and name if available.
    """

    try:
        url = subprocess.check_output(
            ["git", "remote", "get-url", "origin"],
            text=True,
        ).strip()
    except Exception:  # pragma: no cover - best effort
        return None, None

    if url.startswith("git@"):
        _, path = url.split(":", 1)
    elif "github.com/" in url:
        path = url.split("github.com/", 1)[1]
    else:
        return None, None

    if path.endswith(".git"):
        path = path[:-4]

    parts = path.strip("/").split("/")
    if len(parts) != 2:
        return None, None
    return parts[0], parts[1]


def find_plan_files(subdir: Optional[str] = None) -> List[Path]:
    """Recursively locate plan markdown files.

    Parameters
    ----------
    subdir : str, optional
        Specific directory under the plans folder to search.

    Returns
    -------
    list of Path
        Markdown files excluding ``pre_combination_files``.
    """

    root = Path(__file__).resolve().parent
    search_root = root / subdir if subdir else root
    if not search_root.exists():
        raise FileNotFoundError(f"Directory {search_root} does not exist")
    files = [
        p for p in search_root.rglob("*.md") if "pre_combination_files" not in p.parts
    ]
    return sorted(files, key=lambda p: p.name)


def infer_issue_title(path: Path, name: str) -> str:
    """Construct an issue title from directory and file names.

    Parameters
    ----------
    path : Path
        Location of the markdown file.
    name : str
        Title from the YAML frontmatter. When provided, it is combined with
        the numeric prefix from ``path``.

    Returns
    -------
    str
        Issue title in the form ``"<Directory> – <number> <name>"``. If
        ``name`` is empty the filename (with hyphens/underscores replaced by
        spaces) is used.
    """

    dir_name = path.parent.name
    dir_title = " ".join(
        part.capitalize() for part in re.split(r"[-_]", dir_name) if part
    )

    stem_parts = re.split(r"[-_]", path.stem)
    number = stem_parts[0] if stem_parts and stem_parts[0].isdigit() else ""

    if name:
        n = name.strip()
        # Remove any leading directory/plan name and keep only the final part after the last dash or en dash
        if "–" in n:
            n = n.split("–")[-1].strip()
        elif "-" in n:
            n = n.split("-")[-1].strip()
        # Remove any repeated directory/plan name at the start of n
        if n.lower().startswith(dir_title.lower()):
            n = n[len(dir_title):].lstrip(" -–")
        title_part = f"{number} {n}".strip() if number else n
    else:
        title_part = " ".join(stem_parts)

    return f"{dir_title} – {title_part}".strip()


def format_summary_table(rows: List[Tuple[str, str]]) -> str:
    """Build a tabulated summary of issue creation outcomes.

    Parameters
    ----------
    rows : list of tuple of str
        Each tuple is a ``(status, detail)`` pair.

    Returns
    -------
    str
        Formatted table using :mod:`tabulate`. Returns a message when ``rows`` is
        empty.
    """

    if not rows:
        return "No actions performed."

    return tabulate(rows, headers=["Status", "Detail"], tablefmt="github")


def main() -> None:
    """CLI entry point for converting plans into GitHub issues."""

    parser = argparse.ArgumentParser(
        description="Create GitHub issues from Markdown plans.",
    )
    parser.add_argument(
        "--owner",
        help="GitHub organization or username",
    )
    parser.add_argument(
        "--repo",
        help="GitHub repository name",
    )
    parser.add_argument(
        "-d",
        "--directory",
        help="Subdirectory under plans to search for markdown files",
    )
    parser.add_argument(
        "--token",
        help="GitHub personal access token; falls back to env vars",
    )
    args = parser.parse_args()

    token = (
        args.token
        or os.getenv("GITHUB_TOKEN_SOLARWINDPY")
    )
    if not token:
        raise SystemExit(
            "GitHub access token not provided. Use --token or set GITHUB_TOKEN_SOLARWINDPY"
            "/GH_TOKEN/GITHUB_ACCESS_TOKEN."
        )

    log_dir = Path(__file__).resolve().parent.parent / "scripts" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "issues_from_plans.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )

    owner = args.owner
    repo = args.repo
    if not owner or not repo:
        git_owner, git_repo = infer_owner_repo()
        owner = owner or git_owner
        repo = repo or git_repo
    if not owner or not repo:
        logging.error("Repository owner and name must be provided")
        raise SystemExit(1)

    summary_rows: List[Tuple[str, str]] = []

    try:
        plan_files = find_plan_files(args.directory)
    except FileNotFoundError as err:
        logging.error(err)
        raise SystemExit(1)
    if not plan_files:
        msg = "No markdown files found in plans directory"
        logging.warning(msg)
        summary_rows.append(("Warning", msg))
    else:
        logging.info("Found %d plan files", len(plan_files))
        existing_titles = set(fetch_existing_issue_titles(owner, repo, token))
        for path in plan_files:
            try:
                plan = load_markdown_plan(path)
                title = infer_issue_title(path, plan["name"])
                body = plan["body"]
                labels = plan["labels"]

                if title in existing_titles:
                    logging.info("Skipping '%s': issue already exists", title)
                    summary_rows.append(("Exists", title))
                    continue

                issue = create_issue(owner, repo, token, title, body, labels)
                logging.info("Created issue #%d '%s'", issue["number"], title)
                summary_rows.append(("Created", f"{title} (#{issue['number']})"))

            except Exception as err:  # noqa: BLE001 - logging the error
                logging.error("Failed on %s: %s", path, err)
                summary_rows.append(("Error", f"{path.name}: {err}"))

    table = format_summary_table(summary_rows)

    logging.info("\n%s", table)
    with log_file.open("a", encoding="utf-8") as fh:
        fh.write(table + "\n")


if __name__ == "__main__":
    main()
