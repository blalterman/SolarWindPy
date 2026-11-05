# Spent-When: PERMANENT(the package stops writing TeX in its docstrings)
# Supersedes: none
r"""Docstring math is TeX that MathJax accepts.

The API pages render each ``:math:`` role and ``.. math::`` block with
MathJax, which rejects a double subscript or superscript (``a_b_c``,
``x^2^3``, ``\ln_\lambda_{0,1}``: "Double subscripts: use braces to
clarify") and unbalanced braces, and shows the error in place of the
equation. Sphinx builds such a page without a warning, so the strict docs
build cannot catch it. This test reads every docstring under
``src/solarwindpy`` with :mod:`ast`, without importing the package.
"""

import ast
import re
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src" / "solarwindpy"

_ROLE = re.compile(r":math:`([^`]*)`")
_DIRECTIVE = re.compile(r"^(\s*)\.\. math::(.*)$")


def _docstrings(path):
    """Yield ``(qualified name, docstring)`` for a module and its classes and functions."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    nodes = [(path.stem, tree)]
    while nodes:
        name, node = nodes.pop()
        doc = ast.get_docstring(node, clean=False)
        if doc:
            yield name, doc
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                nodes.append((f"{name}.{child.name}", child))


def _math(doc):
    """Every TeX expression in ``doc``: role contents and directive bodies."""
    yield from _ROLE.findall(doc)
    lines = doc.splitlines()
    for i, line in enumerate(lines):
        match = _DIRECTIVE.match(line)
        if not match:
            continue
        indent = len(match.group(1))
        body = [match.group(2)]
        for nxt in lines[i + 1 :]:
            if nxt.strip() and len(nxt) - len(nxt.lstrip()) <= indent:
                break
            if not nxt.strip().startswith(":"):  # directive options
                body.append(nxt)
        yield "\n".join(body)


def _argument_end(tex, i):
    """Index after the sub- or superscript argument starting at ``tex[i]``."""
    while i < len(tex) and tex[i].isspace():
        i += 1
    if i >= len(tex):
        return i
    if tex[i] == "{":
        depth = 0
        for j in range(i, len(tex)):
            depth += {"{": 1, "}": -1}.get(tex[j], 0)
            if depth == 0:
                return j + 1
        return len(tex)
    if tex[i] == "\\":
        match = re.match(r"\\([A-Za-z]+|.)", tex[i:])
        return i + match.end()
    return i + 1


def problems(tex):
    """What MathJax rejects in ``tex``: double sub/superscripts, unbalanced braces."""
    found = []
    # Escaped braces \{ \} are literal and do not group.
    plain = re.sub(r"\\[{}]", "", tex)
    if plain.count("{") != plain.count("}"):
        found.append("unbalanced braces")
    seen = set()  # which of _ and ^ the current atom already has
    i = 0
    while i < len(tex):
        c = tex[i]
        if c in "_^":
            if c in seen:
                kind = "subscript" if c == "_" else "superscript"
                found.append(f"double {kind} at {tex[max(0, i - 12) : i + 6]!r}")
            seen.add(c)
            i = _argument_end(tex, i + 1)
            continue
        if c == "\\" and tex[i : i + 2] in ("\\{", "\\}"):
            i += 2
        elif c == "\\":
            i = _argument_end(tex, i)
        elif c == "{":
            i = _argument_end(tex, i)
        else:
            i += 1
        if not c.isspace():
            seen = set()
    return found


@pytest.mark.parametrize(
    "tex, expected",
    [
        (r"a_b_c", ["double subscript"]),
        (r"x^2^3", ["double superscript"]),
        (r"\ln_\lambda_{i,i}", ["double subscript"]),
        (r"x_{a}^{b}", []),
        (r"x_a^b_c", ["double subscript"]),
        (r"{x_a}_b", []),
        (r"w_\parallel w_\perp^2", []),
        (r"\frac{a}{b", ["unbalanced braces"]),
        (r"\{a\}", []),
    ],
)
def test_the_checker_finds_what_mathjax_rejects(tex, expected):
    """Hand-written cases: each MathJax error is found, and valid TeX passes.

    ON FAILURE: the checker is wrong.
    """
    found = problems(tex)
    assert len(found) == len(expected)
    for f, e in zip(found, expected):
        assert f.startswith(e)


def test_docstring_math_has_no_tex_mathjax_rejects():
    """No docstring under src/solarwindpy holds math MathJax would reject.

    ON FAILURE: the code is wrong; brace the sub- or superscript, e.g.
    ``a_{b_c}`` or ``{a_b}_c``.
    """
    bad = []
    for path in sorted(SRC.rglob("*.py")):
        for name, doc in _docstrings(path):
            for tex in _math(doc):
                for p in problems(tex):
                    bad.append(f"{path.relative_to(SRC)}::{name}: {p}")
    assert bad == []
