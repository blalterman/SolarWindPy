#!/usr/bin/env python3
"""Create GitHub issues from plan files.

The script parses markdown files under ``solarwindpy/plans`` that contain
YAML frontmatter and converts them into GitHub issues. Frontmatter fields
``name``, ``about`` and ``labels`` are used for the issue metadata while the
markdown content beginning with ``## 🧠 Context`` becomes the issue body.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
import yaml

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


def load_repo_config() -> Tuple[Optional[str], Optional[str]]:
    """Load default repository information from package config.

    Returns
    -------
    tuple of (str or None, str or None)
        Repository owner and name if available.
    """

    config_path = Path(__file__).resolve().parent.parent / "github_config.json"
    if not config_path.exists():
        return None, None

    with config_path.open("r", encoding="utf-8") as cfg:
        data = json.load(cfg)

    return data.get("owner"), data.get("repo")


def find_plan_files() -> List[Path]:
    """Recursively locate plan markdown files."""

    root = Path(__file__).resolve().parent
    return [p for p in root.rglob("*.md") if "pre_combination_files" not in p.parts]


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
    args = parser.parse_args()

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise SystemExit("Environment variable GITHUB_TOKEN not set.")

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
        cfg_owner, cfg_repo = load_repo_config()
        owner = owner or cfg_owner
        repo = repo or cfg_repo
    if not owner or not repo:
        logging.error("Repository owner and name must be provided")
        raise SystemExit(1)

    plan_files = find_plan_files()
    if not plan_files:
        logging.warning("No markdown files found in plans directory")
        return

    logging.info("Found %d plan files", len(plan_files))

    existing_titles = set(fetch_existing_issue_titles(owner, repo, token))

    for path in plan_files:
        try:
            plan = load_markdown_plan(path)
            title = plan["name"]
            body = plan["body"]
            labels = plan["labels"]

            if title in existing_titles:
                logging.info("Skipping '%s': issue already exists", title)
                continue

            issue = create_issue(owner, repo, token, title, body, labels)
            logging.info("Created issue #%d '%s'", issue["number"], title)

        except Exception as err:  # noqa: BLE001 - logging the error
            logging.error("Failed on %s: %s", path, err)


if __name__ == "__main__":
    main()
