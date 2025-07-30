"""Update the conda recipe to match the project's version and dependencies."""
from __future__ import annotations

import configparser
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETUP_CFG = ROOT / "setup.cfg"
META_YAML = ROOT / "recipe" / "meta.yaml"


def get_version() -> str:
    """Return package version from ``setup.py`` via ``setuptools_scm``."""
    try:
        out = subprocess.check_output(["python", "setup.py", "--version"], cwd=ROOT)
        return out.decode().strip()
    except Exception:
        return "0.0.0"


def get_requirements() -> list[str]:
    """Parse ``install_requires`` from ``setup.cfg``."""
    parser = configparser.ConfigParser()
    parser.read(SETUP_CFG)
    requires = parser.get("options", "install_requires", fallback="")
    deps = [r.strip() for r in requires.splitlines() if r.strip()]
    return deps


def update_meta_yaml() -> None:
    """Update version and run dependencies in ``meta.yaml``."""
    version = get_version()
    deps = get_requirements()
    text = META_YAML.read_text()

    text = re.sub(
        r"{%\s*set version = \".*?\" %}", f'{{% set version = "{version}" %}}', text
    )

    run_block = (
        "  run:\n"
        + "\n".join(f"    - {dep}" for dep in ["python >=3.7,<4"] + deps)
        + "\n"
    )
    text = re.sub(r"  run:\n(?:\s+-.*\n)+", run_block, text)
    META_YAML.write_text(text)


if __name__ == "__main__":
    update_meta_yaml()
