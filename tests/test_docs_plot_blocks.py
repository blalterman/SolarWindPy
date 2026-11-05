# Spent-When: PERMANENT(the documentation stops drawing figures with the plot directive)
# Supersedes: none
"""Every ``.. plot::`` block in the documentation runs on its own.

The guide shows the code that draws each figure, and a reader should be able
to paste one block into a fresh session and get that figure. ``conf.py`` sets
``plot_pre_code = ""``, so the docs build already runs each block without
hidden setup; this module runs each block in a namespace of its own under the
``Agg`` backend, so the default suite catches a block that stops running
without a docs build.
"""

import re
from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402

DOCS = Path(__file__).resolve().parents[1] / "docs" / "source"

if not DOCS.is_dir():
    pytest.skip(
        "docs/source is absent (e.g. testing from the sdist)",
        allow_module_level=True,
    )

_DIRECTIVE = re.compile(r"^(\s*)\.\. plot::(.*)$")


def _plot_blocks(path):
    """Yield ``(line, argument, code)`` for each ``.. plot::`` block in ``path``.

    ``argument`` is the text after ``plot::``, empty for an inline block, and
    ``code`` is the block's body without its options.
    """
    lines = path.read_text().splitlines()
    for i, line in enumerate(lines):
        match = _DIRECTIVE.match(line)
        if match is None:
            continue
        indent = len(match.group(1))
        body = []
        for following in lines[i + 1 :]:
            if following.strip() and len(following) - len(following.lstrip()) <= indent:
                break
            body.append(following)
        # Drop the directive's options, then the blank line after them.
        while body and (not body[0].strip() or body[0].strip().startswith(":")):
            body.pop(0)
        width = min((len(b) - len(b.lstrip()) for b in body if b.strip()), default=0)
        code = "\n".join(b[width:] for b in body).strip()
        yield i + 1, match.group(2).strip(), code + "\n" if code else ""


FOUND = [
    (f"{path.relative_to(DOCS)}:{line}", argument, code)
    for path in sorted(DOCS.rglob("*.rst"))
    for line, argument, code in _plot_blocks(path)
]
BLOCKS = [pytest.param(code, id=where) for where, _, code in FOUND]


def test_the_guide_has_plot_blocks():
    """The collector finds blocks, so an empty parametrization cannot pass."""
    assert BLOCKS


def test_every_plot_block_holds_its_code_inline():
    """No block names a script: the code a reader copies is on the page."""
    named = [f"{where}: plot:: {argument}" for where, argument, _ in FOUND if argument]
    assert not named, named


@pytest.mark.parametrize("code", BLOCKS)
def test_plot_block_runs_alone(code, request):
    """A block runs with nothing defined beforehand and draws a figure."""
    assert code, f"{request.node.callspec.id}: the plot block is empty"
    try:
        exec(compile(code, "<plot block>", "exec"), {"__name__": "__main__"})
        assert plt.get_fignums(), "the block drew no figure"
    finally:
        plt.close("all")
