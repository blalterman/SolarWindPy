# Spent-When: PERMANENT(SolarWindPy stops collecting doctests with pytest)
# Supersedes: none
r"""Repository-root pytest configuration for documentation examples.

``pytest --doctest-modules src/solarwindpy`` collects docstring examples as
``DoctestItem`` objects, which accept no decorators. Examples that document
correct behavior the library does not yet deliver are marked strict xfail
here, so the suite reports the day the library catches up.

The examples in the rst files listed in ``SYBIL_DOCUMENTS`` run under Sybil:
``>>>`` examples as doctests, so each shown output is asserted, and any
``code-block:: python`` as plain code that must run. Run them with::

    pytest -p no:doctest README.rst \
        docs/source/tutorial/quickstart.rst docs/source/installation.rst

``-p no:doctest`` stops pytest's own doctest plugin from collecting the same
rst files a second time when they are named on the command line. Under
``--doctest-glob='*.rst'`` the plugin collects them too; while Sybil is active
those doctest items are deselected here, so each example runs once. Sybil is
declared in the ``dev`` extra; without it no Sybil example is collected.

A document's examples share one namespace and read as a sequence: README's
later examples use the ``plasma`` its earlier ones build. pytest-randomly
shuffles items before this file's ``pytest_collection_modifyitems`` runs, so
that hook puts each document's examples back in line order.

Docstring examples that need a ``Plasma`` build one with
``solarwindpy.examples.load_plasma()``; no fixture injects one.

Every example, doctest or Sybil, runs under pandas' display defaults for a
session without a terminal (``PANDAS_DISPLAY``), so a printed Series or
DataFrame does not depend on the width of the terminal running pytest, and a
reader who copies an example sees the output it shows. Whitespace in an
expected output of an rst example is normalized, under Sybil and under the
doctest plugin alike; docstring examples keep exact whitespace.
"""

import doctest
from pathlib import Path

import pandas as pd
import pytest

# Doctest node id -> reason. Each entry names the defect that retires it.
DOCTEST_XFAIL = {}

# rst documents whose examples run under Sybil, relative to this directory.
SYBIL_DOCUMENTS = [
    "README.rst",
    "docs/source/tutorial/quickstart.rst",
    "docs/source/installation.rst",
]

# pandas' own defaults when output is not a terminal, set explicitly so an
# example's printed table never follows the terminal pytest runs in.
PANDAS_DISPLAY = {
    "display.width": 80,
    "display.max_columns": 20,
    "display.max_rows": 60,
    "display.precision": 6,
}
_pandas_display_contexts = []


def _enter_pandas_display():
    """Apply ``PANDAS_DISPLAY`` until the matching ``_exit_pandas_display``."""
    context = pd.option_context(*(x for item in PANDAS_DISPLAY.items() for x in item))
    context.__enter__()
    _pandas_display_contexts.append(context)


def _exit_pandas_display():
    """Restore the pandas options ``_enter_pandas_display`` replaced."""
    _pandas_display_contexts.pop().__exit__(None, None, None)


_SYBIL_PATHS = {
    Path(__file__).resolve().parent / document for document in SYBIL_DOCUMENTS
}

try:
    from sybil import Sybil
except ModuleNotFoundError as error:  # sybil is a dev extra; tests/ needs only test
    if error.name != "sybil":
        raise
    SybilItem = None
else:
    from sybil.integration.pytest import SybilItem
    from sybil.parsers.rest import DocTestParser, PythonCodeBlockParser, SkipParser

    pytest_collect_file = Sybil(
        parsers=[
            DocTestParser(optionflags=doctest.NORMALIZE_WHITESPACE),
            PythonCodeBlockParser(),
            SkipParser(),
        ],
        patterns=SYBIL_DOCUMENTS,
        setup=lambda namespace: _enter_pandas_display(),
        teardown=lambda namespace: _exit_pandas_display(),
    ).pytest()


@pytest.fixture(autouse=True)
def _pandas_display_defaults(request):
    """Run each doctest under ``PANDAS_DISPLAY``; Sybil sets it per document."""
    if not isinstance(request.node, pytest.DoctestItem):
        yield
        return
    _enter_pandas_display()
    try:
        yield
    finally:
        _exit_pandas_display()


def _restore_document_order(items):
    """Put Sybil examples back in document line order, in their own slots."""
    # Sorts the Sybil items by (path, line), so within each document the
    # examples run in line order, and writes them back into the positions Sybil
    # items already held; every other item stays where it is. Assumes a single
    # process: under pytest-xdist a document's examples could be split across
    # workers, and no reordering here would keep their shared namespace intact.
    slots = [i for i, item in enumerate(items) if isinstance(item, SybilItem)]
    ordered = sorted(
        (items[i] for i in slots),
        key=lambda item: (str(item.example.path), item.example.line),
    )
    for i, item in zip(slots, ordered):
        items[i] = item


def _deselect_doctest_duplicates(config, items):
    """Deselect pytest's own doctest items for the documents Sybil runs."""
    duplicates = [
        item
        for item in items
        if isinstance(item, pytest.DoctestItem) and item.path.resolve() in _SYBIL_PATHS
    ]
    if duplicates:
        dropped = {id(item) for item in duplicates}
        config.hook.pytest_deselected(items=duplicates)
        items[:] = [item for item in items if id(item) not in dropped]


def pytest_collection_modifyitems(config, items):
    for item in items:
        if isinstance(item, pytest.DoctestItem) and item.path.suffix == ".rst":
            # One runner serves a file's examples, so this sets the file's flag.
            item.runner.optionflags |= doctest.NORMALIZE_WHITESPACE
        reason = DOCTEST_XFAIL.get(item.nodeid)
        if reason is not None:
            item.add_marker(pytest.mark.xfail(strict=True, reason=reason))
    if SybilItem is not None:
        _deselect_doctest_duplicates(config, items)
        _restore_document_order(items)
