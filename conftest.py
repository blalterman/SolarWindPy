# Spent-When: PERMANENT(SolarWindPy stops collecting doctests with pytest)
# Supersedes: none
"""Repository-root pytest configuration for documentation examples.

``pytest --doctest-modules solarwindpy`` collects docstring examples as
``DoctestItem`` objects, which accept no decorators. Examples that document
correct behavior the library does not yet deliver are marked strict xfail
here, so the suite reports the day the library catches up.

The examples in the rst files listed in ``SYBIL_DOCUMENTS`` run under Sybil:
``>>>`` examples as doctests, so each shown output is asserted, and any
``code-block:: python`` as plain code that must run. Run them with::

    pytest -p no:doctest README.rst \\
        docs/source/tutorial/quickstart.rst docs/source/installation.rst

``-p no:doctest`` stops pytest's own doctest plugin from collecting the same
rst files a second time when they are named on the command line. Sybil is
declared in the ``dev`` extra; without it no Sybil example is collected.

A document's examples share one namespace and read as a sequence: README's
later examples use the ``plasma`` its earlier ones build. pytest-randomly
shuffles items before this file's ``pytest_collection_modifyitems`` runs, so
that hook puts each document's examples back in line order.
"""

import pytest

# Doctest node id -> reason. Each entry names the defect that retires it.
DOCTEST_XFAIL = {}

# rst documents whose examples run under Sybil, relative to this directory.
SYBIL_DOCUMENTS = [
    "README.rst",
    "docs/source/tutorial/quickstart.rst",
    "docs/source/installation.rst",
]

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
        parsers=[DocTestParser(), PythonCodeBlockParser(), SkipParser()],
        patterns=SYBIL_DOCUMENTS,
    ).pytest()


def _restore_document_order(items):
    """Put Sybil examples back in document line order, in their own slots."""
    slots = [i for i, item in enumerate(items) if isinstance(item, SybilItem)]
    ordered = sorted(
        (items[i] for i in slots),
        key=lambda item: (str(item.example.path), item.example.line),
    )
    for i, item in zip(slots, ordered):
        items[i] = item


def pytest_collection_modifyitems(config, items):
    for item in items:
        reason = DOCTEST_XFAIL.get(item.nodeid)
        if reason is not None:
            item.add_marker(pytest.mark.xfail(strict=True, reason=reason))
    if SybilItem is not None:
        _restore_document_order(items)
