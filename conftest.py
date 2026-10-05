# Spent-When: PERMANENT(SolarWindPy stops collecting doctests with pytest)
# Supersedes: none
r"""Repository-root pytest configuration for documentation examples.

``pytest --doctest-modules solarwindpy`` collects docstring examples as
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

Docstring examples in ``.py`` modules find a fresh ``plasma`` in their
namespace, provided by the ``_doctest_plasma`` fixture; rst doctests do not.
"""

from pathlib import Path

import pytest

# Doctest node id -> reason. Each entry names the defect that retires it.
DOCTEST_XFAIL = {}

# rst documents whose examples run under Sybil, relative to this directory.
SYBIL_DOCUMENTS = [
    "README.rst",
    "docs/source/tutorial/quickstart.rst",
    "docs/source/installation.rst",
]
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
        parsers=[DocTestParser(), PythonCodeBlockParser(), SkipParser()],
        patterns=SYBIL_DOCUMENTS,
    ).pytest()


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
        reason = DOCTEST_XFAIL.get(item.nodeid)
        if reason is not None:
            item.add_marker(pytest.mark.xfail(strict=True, reason=reason))
    if SybilItem is not None:
        _deselect_doctest_duplicates(config, items)
        _restore_document_order(items)


def _small_plasma():
    """Build the two-row proton ``Plasma`` that docstring examples share.

    The same setup the ``Plasma.epoch``, ``set_log_plasma_stats``,
    ``set_spacecraft`` and ``set_auxiliary_data`` docstring examples build for
    themselves: every value 1.0, two epochs one minute apart.
    """
    import pandas as pd

    from solarwindpy.core.plasma import Plasma

    epoch = pd.DatetimeIndex(["2023-01-01 00:00", "2023-01-01 00:01"], name="Epoch")
    columns = pd.MultiIndex.from_tuples(
        [
            ("b", "x", ""),
            ("b", "y", ""),
            ("b", "z", ""),
            ("n", "", "p1"),
            ("v", "x", "p1"),
            ("v", "y", "p1"),
            ("v", "z", "p1"),
            ("w", "par", "p1"),
            ("w", "per", "p1"),
        ],
        names=["M", "C", "S"],
    )
    return Plasma(pd.DataFrame(1.0, index=epoch, columns=columns), "p1")


@pytest.fixture(autouse=True)
def _doctest_plasma(request):
    """Give each ``.py`` docstring example a fresh ``plasma``.

    rst doctests and all other tests get nothing, so a document example that
    uses ``plasma`` without building it still fails. ``doctest_namespace`` is
    session-scoped, so the name is removed again after each docstring runs;
    otherwise an rst doctest running later would inherit it.
    """
    node = request.node
    if not (isinstance(node, pytest.DoctestItem) and node.path.suffix == ".py"):
        yield
        return
    namespace = request.getfixturevalue("doctest_namespace")
    namespace["plasma"] = _small_plasma()
    yield
    namespace.pop("plasma", None)
