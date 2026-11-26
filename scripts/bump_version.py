#!/usr/bin/env python3
"""Create SolarWindPy's next release tag, named by the release date.

A release tag is the release date, ``YEAR.MONTH.DAY`` without leading zeros
(``2026.12.3``), so the tag, the PyPI version, ``CITATION.cff`` and the
Zenodo record read the same. A second release on one day adds a serial
(``2026.12.3.1``); a release candidate adds ``rcN`` (``2026.12.3rc1``), which
the publish workflow sends to TestPyPI. ``pyproject.toml``'s setuptools_scm
settings read these tags, so the tag sets the version every build reports.

Usage
-----
    python scripts/bump_version.py               # tag HEAD with today's release tag
    python scripts/bump_version.py --rc          # tag a release candidate
    python scripts/bump_version.py --dry-run     # print the tag without creating it
    python scripts/bump_version.py --check TAG   # exit 0 if TAG is a release tag

Today is the date in UTC, the clock GitHub's runners and PyPI keep.
"""

import argparse
import datetime
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: A release tag: the date without leading zeros, an optional serial, an optional rc.
RELEASE_TAG = re.compile(
    r"^(?P<year>20\d{2})\.(?P<month>[1-9]|1[0-2])\.(?P<day>[1-9]|[12]\d|3[01])"
    r"(?:\.(?P<serial>[1-9]\d*))?(?:rc(?P<rc>[1-9]\d*))?$"
)


def is_release_tag(tag):
    """Return True when ``tag`` is a release tag naming a real date."""
    match = RELEASE_TAG.match(tag)
    if match is None:
        return False
    try:
        datetime.date(int(match["year"]), int(match["month"]), int(match["day"]))
    except ValueError:
        return False
    return True


def next_tag(day, existing, rc=False):
    """Return the next release tag on ``day``, given the tags that already exist.

    The first release of the day is the date; each further release adds the
    next serial. A release candidate names the release it precedes and adds
    the next ``rcN`` for that release.
    """
    base = f"{day.year}.{day.month}.{day.day}"
    serials = []
    for tag in existing:
        match = RELEASE_TAG.match(tag)
        if match is None or match["rc"] is not None:
            continue
        if f"{match['year']}.{match['month']}.{match['day']}" == base:
            serials.append(int(match["serial"] or 0))
    release = base if not serials else f"{base}.{max(serials) + 1}"
    if not rc:
        return release
    candidate = re.compile(re.escape(release) + r"rc([1-9]\d*)")
    numbers = [int(m[1]) for m in map(candidate.fullmatch, existing) if m is not None]
    return f"{release}rc{max(numbers, default=0) + 1}"


def _git(*args):
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout


def main(argv=None):
    """Create, print, or check a release tag."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rc", action="store_true", help="tag a release candidate")
    parser.add_argument("--dry-run", action="store_true", help="print the tag only")
    parser.add_argument("--check", metavar="TAG", help="exit 0 if TAG is a release tag")
    args = parser.parse_args(argv)

    if args.check is not None:
        if is_release_tag(args.check):
            return 0
        print(
            f"{args.check} is not a release tag: use the release date without "
            "leading zeros, YEAR.MONTH.DAY (2026.12.3), with .N for a further "
            "release that day and rcN for a release candidate",
            file=sys.stderr,
        )
        return 1

    today = datetime.datetime.now(datetime.timezone.utc).date()
    tag = next_tag(today, _git("tag", "--list").split(), rc=args.rc)
    if args.dry_run:
        print(tag)
        return 0
    if _git("status", "--porcelain").strip():
        print("Commit or stash changes before tagging a release.", file=sys.stderr)
        return 1
    _git("tag", "-a", tag, "-m", f"Release {tag}")
    print(f"Created tag {tag}. Push it to the public repository to release it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
