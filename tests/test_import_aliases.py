# Spent-When: PERMANENT(solarwindpy stops restricting import aliases)
# Supersedes: none
"""Every import in ``solarwindpy/`` binds its real name, with five exceptions.

The allowed aliases are the community conventions ``np`` (numpy), ``pd``
(pandas), ``plt`` (matplotlib.pyplot), ``mpl`` (matplotlib) and ``mdates``
(matplotlib.dates), each only for its own module. Files come from scanning
the package directory, never from a typed list.
"""

import ast
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "solarwindpy"

ALLOWED = {
    "np": "numpy",
    "pd": "pandas",
    "plt": "matplotlib.pyplot",
    "mpl": "matplotlib",
    "mdates": "matplotlib.dates",
}


def _aliases(path):
    """``(line, module, alias)`` for every aliased import in ``path``.

    ``module`` is the dotted name the alias binds: ``a.b`` for
    ``import a.b as x`` and for ``from a import b as x``. A relative import
    keeps its leading dots, so it never matches an allowed module.
    """
    found = []
    for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
        if isinstance(node, ast.Import):
            prefix = ""
        elif isinstance(node, ast.ImportFrom):
            prefix = "." * node.level + (node.module or "")
            prefix = prefix if prefix.endswith(".") else prefix + "."
        else:
            continue
        for alias in node.names:
            if alias.asname is not None:
                found.append((node.lineno, prefix + alias.name, alias.asname))
    return found


FILES = sorted(PACKAGE.rglob("*.py"))
ALIASES = [
    (path.relative_to(PACKAGE.parent), line, module, alias)
    for path in FILES
    for line, module, alias in _aliases(path)
]


def test_the_scan_reads_the_package_and_finds_allowed_aliases():
    """The walk reaches the package's files and sees at least one allowed alias.

    Guards the next test against passing vacuously.

    ON FAILURE: the scan no longer reaches ``solarwindpy/``; fix the test.
    """
    assert len(FILES) > 40
    assert any(ALLOWED.get(alias) == module for _, _, module, alias in ALIASES)


def test_only_np_pd_plt_mpl_mdates_aliases_are_used():
    """Every aliased import is one of the five allowed, for its own module.

    ON FAILURE: the code is wrong; import the flagged module under its real
    name, unless the author adds the alias to ``ALLOWED``.
    """
    offenders = [
        f"{path}:{line}: {module} as {alias}"
        for path, line, module, alias in ALIASES
        if ALLOWED.get(alias) != module
    ]
    assert not offenders, "\n".join(offenders)
