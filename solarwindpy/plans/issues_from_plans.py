#!/usr/bin/env python3
"""
Create GitHub issues from Markdown plans with YAML frontmatter.

Usage:
    python create_issues_from_plans.py \
        --owner my-org \
        --repo my-repo \
        --dir SolarWindPy/solarwindpy/plans/combined_test_plan_with_checklist_solar_activity
"""

import os
import glob
import argparse
import logging
import yaml
import requests
from typing import List, Dict

GITHUB_API = "https://api.github.com"

def load_markdown_plan(path: str) -> Dict:
    """
    Read a markdown file, parse YAML frontmatter and return:
      { "name": str, "about": str, "labels": List[str], "body": str }
    """
    text = open(path, 'r', encoding='utf-8').read()
    if not text.startswith('---'):
        raise ValueError(f"No YAML frontmatter found in {path}")
    _, fm, rest = text.split('---', 2)
    meta = yaml.safe_load(fm)
    body = rest.lstrip('\n')
    return {
        "name": meta.get("name", "").strip(),
        "about": meta.get("about", "").strip(),
        "labels": meta.get("labels", []),
        "body": body
    }

def fetch_existing_issue_titles(owner: str, repo: str, token: str) -> List[str]:
    """
    Retrieve the titles of open issues in the repo (up to 100).
    """
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues"
    headers = {"Authorization": f"token {token}"}
    params = {"state": "all", "per_page": 100}
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return [issue["title"] for issue in resp.json()]

def create_issue(owner: str, repo: str, token: str,
                 title: str, body: str, labels: List[str]) -> Dict:
    """
    Create a GitHub issue and return the response JSON.
    """
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    payload = {"title": title, "body": body, "labels": labels}
    resp = requests.post(url, json=payload, headers=headers)
    resp.raise_for_status()
    return resp.json()

def main():
    parser = argparse.ArgumentParser(
        description="Create GitHub issues from Markdown plans."
    )
    parser.add_argument(
        "--owner", required=True,
        help="GitHub organization or username"
    )
    parser.add_argument(
        "--repo", required=True,
        help="GitHub repository name"
    )
    parser.add_argument(
        "--dir", required=True,
        help="Directory containing plan markdown files"
    )
    args = parser.parse_args()

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        logging.error("Environment variable GITHUB_TOKEN not set.")
        exit(1)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    plan_files = glob.glob(os.path.join(args.dir, "*.md"))
    if not plan_files:
        logging.warning("No markdown files found in %s", args.dir)
        return

    logging.info("Found %d plan files", len(plan_files))

    existing_titles = fetch_existing_issue_titles(args.owner, args.repo, token)
    existing_set = set(existing_titles)

    for path in plan_files:
        try:
            plan = load_markdown_plan(path)
            title = plan["name"]
            body = plan["body"]
            labels = plan["labels"]

            if title in existing_set:
                logging.info("Skipping '%s': issue already exists", title)
                continue

            issue = create_issue(args.owner, args.repo, token, title, body, labels)
            logging.info("Created issue #%d '%s'", issue["number"], title)

        except Exception as e:
            logging.error("Failed on %s: %s", path, e)

if __name__ == "__main__":
    main()
