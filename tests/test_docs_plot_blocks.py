# Spent-When: PERMANENT(the documentation stops drawing figures with the plot directive)
# Supersedes: none
"""Every ``.. plot::`` block in the documentation runs on its own.

The guide shows the code that draws each figure, and a reader should be able
to paste one block into a fresh session and get that figure. ``conf.py`` sets
``plot_pre_code = ""``, so the docs build already runs each block without
hidden setup; this module runs each block in a namespace of its own under the
``Agg`` backend, so the default suite catches a block that stops running
without a docs build. A block that loads ``SIDC("m13")`` gets the committed
snapshot from a private download cache, as in the docs build, never the
network.
"""

import importlib.util
import re
from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402

from solarwindpy.solar_activity import cache  # noqa: E402

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


def _found(root):
    """``(where, argument, code)`` of every ``.. plot::`` block under ``root``."""
    return [
        (f"{path.relative_to(root)}:{line}", argument, code)
        for path in sorted(root.rglob("*.rst"))
        for line, argument, code in _plot_blocks(path)
    ]


def _named(found):
    """The blocks that name a script instead of holding their code."""
    return [f"{where}: plot:: {argument}" for where, argument, _ in found if argument]


def _empty(found):
    """The inline blocks with no code."""
    return [where for where, argument, code in found if not argument and not code]


FOUND = _found(DOCS)
BLOCKS = [pytest.param(code, id=where) for where, _, code in FOUND]


def test_the_guide_has_plot_blocks():
    """The collector finds blocks, so an empty parametrization cannot pass."""
    assert BLOCKS


def test_every_plot_block_holds_its_code_inline():
    """No block names a script: the code a reader copies is on the page."""
    named = _named(FOUND)
    assert not named, named


def test_no_plot_block_is_empty():
    """Every inline block holds code, so each figure has code beside it."""
    empty = _empty(FOUND)
    assert not empty, empty


def test_the_guards_catch_an_empty_and_a_named_block(tmp_path):
    """The collector and both guards fire on a page that breaks them.

    A page with an empty inline block (options only), a block naming a
    script, and one good block: the guards name exactly the two bad ones.

    ON FAILURE: the code is wrong -- the collector misreads a block, so the
    guards above can pass on a page that breaks them.
    """
    (tmp_path / "page.rst").write_text(
        "Title\n"
        "=====\n"
        "\n"
        ".. plot::\n"
        "   :include-source: false\n"
        "\n"
        "Some text.\n"
        "\n"
        ".. plot:: figure.py\n"
        "\n"
        ".. plot::\n"
        "\n"
        "   import matplotlib.pyplot as plt\n"
        "   plt.plot([0, 1])\n"
    )
    found = _found(tmp_path)
    assert len(found) == 3
    assert _empty(found) == ["page.rst:4"]
    assert _named(found) == ["page.rst:9: plot:: figure.py"]


def _no_download(url, cache):
    raise AssertionError(f"a plot block tried to download {url}")


@pytest.fixture
def ssn_snapshot(tmp_path, monkeypatch):
    """Serve ``SIDC("m13")`` from the docs' snapshot, as ``conf.py`` does.

    Both seed a private download cache with ``_ssn_snapshot.seed_ssn_snapshot``.
    Any download raises, and a stale-cache fallback is an error, so a block
    never reaches the network.
    """
    spec = importlib.util.spec_from_file_location(
        "_ssn_snapshot", DOCS / "_ssn_snapshot.py"
    )
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    monkeypatch.setattr(cache, "_download_file", _no_download)
    helper.seed_ssn_snapshot(tmp_path / "cache", monkeypatch.setenv)


@pytest.mark.filterwarnings("error::solarwindpy.solar_activity.cache.StaleCacheWarning")
@pytest.mark.parametrize("code", BLOCKS)
def test_plot_block_runs_alone(code, request, ssn_snapshot):
    """A block runs with nothing defined beforehand and draws a figure."""
    assert code, f"{request.node.callspec.id}: the plot block is empty"
    try:
        exec(compile(code, "<plot block>", "exec"), {"__name__": "__main__"})
        assert plt.get_fignums(), "the block drew no figure"
    finally:
        plt.close("all")
