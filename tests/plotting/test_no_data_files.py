# Spent-When: PERMANENT(plotting tests are allowed to read data files)
# Supersedes: none
"""Plotting tests build their data in the test and never read a data file.

SolarWindPy is public, so a plotting test that loads a research data file
either fails for everyone without that file or ships the data. Every
``tests/plotting/**/*.py`` file, subfolders included, is parsed and walked for
two things: a string constant ending in a data-file suffix, and a call or
import that reads a data file. Writing is not the concern, so ``to_hdf`` or
``savefig`` alone is not flagged, though a data-file name written as a string
still is.

This file is excluded from the scan because its patterns and planted
snippets necessarily contain the strings it forbids. The scanner itself is
tested on snippets held in memory.
"""

import ast
from pathlib import Path

import pytest

PLOTTING = Path(__file__).resolve().parent
THIS_FILE = Path(__file__).resolve()

SUFFIXES = (
    ".h5",
    ".hdf",
    ".hdf5",
    ".cdf",
    ".pkl",
    ".pickle",
    ".csv",
    ".nc",
    ".fits",
    ".npy",
    ".npz",
)

# A call whose final name is one of these reads a data file, whatever the
# prefix (``pd.read_csv``, ``pandas.read_csv`` or a bare imported ``read_csv``).
READERS = {
    "read_hdf",
    "HDFStore",
    "read_pickle",
    "read_csv",
    "read_parquet",
    "open_dataset",
    "open_mfdataset",
}

# ``<module>.load`` reads a file for these modules.
LOADERS = {"np", "numpy", "pickle"}

# Modules whose only purpose here would be reading a data file.
DATA_MODULES = {"cdflib", "netCDF4", "h5py", "astropy.io.fits"}


def dotted(node):
    """Return ``a.b.c`` for a name or attribute chain, else ``None``."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return ".".join(reversed(parts))


def is_data_module(name):
    """Return whether module ``name`` is, or is inside, a data-reading module."""
    return any(name == m or name.startswith(m + ".") for m in DATA_MODULES)


def data_file_uses(text):
    """Return sorted ``(line number, reason)`` for each data-file use in ``text``."""
    found = []
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value.strip().lower().endswith(SUFFIXES):
                found.append((node.lineno, f"data-file name {node.value!r}"))
        elif isinstance(node, ast.Call):
            name = dotted(node.func)
            if name is None:
                continue
            head, _, last = name.rpartition(".")
            if (
                last in READERS
                or (last == "load" and head in LOADERS)
                or (head.rpartition(".")[2] == "fits" and last in {"open", "getdata"})
                or is_data_module(name)
            ):
                found.append((node.lineno, f"call {name}()"))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if is_data_module(alias.name):
                    found.append((node.lineno, f"import {alias.name}"))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                full = f"{module}.{alias.name}"
                if (
                    is_data_module(module)
                    or is_data_module(full)
                    or alias.name in READERS
                    or (alias.name == "load" and module in LOADERS)
                ):
                    found.append((node.lineno, f"from {module} import {alias.name}"))
    return sorted(found)


def plotting_test_files():
    """Return every ``.py`` file under ``tests/plotting`` except this one."""
    return [p for p in sorted(PLOTTING.rglob("*.py")) if p.resolve() != THIS_FILE]


def test_scan_covers_plotting_subfolders():
    """The scan reaches the nested ``tests/plotting/labels`` folder.

    ON FAILURE: ``plotting_test_files`` no longer recurses, or the subfolders
    moved; fix the file list so every plotting test is scanned.
    """
    folders = {p.parent.name for p in plotting_test_files()}
    assert {"plotting", "labels"} <= folders
    assert THIS_FILE not in [p.resolve() for p in plotting_test_files()]


def test_no_plotting_test_reads_a_data_file():
    """No plotting test names a data file or calls a data-file reader.

    ON FAILURE: replace the data file with seeded synthetic data built in the
    test (``np.random.default_rng(<seed>)`` or hand-placed values), per
    ``.claude/docs/TEST_PATTERNS.md``.
    """
    found = [
        f"{path.relative_to(PLOTTING.parent.parent)}:{n}: {reason}"
        for path in plotting_test_files()
        for n, reason in data_file_uses(path.read_text(encoding="utf-8"))
    ]
    assert not found, "plotting tests that use data files:\n" + "\n".join(found)


@pytest.mark.parametrize("suffix", SUFFIXES + (".H5", ".CSV"))
def test_scanner_flags_a_data_file_name(suffix):
    """A string constant ending in a data-file suffix, any case, is flagged.

    ON FAILURE: the scanner misses a data-file name; fix ``SUFFIXES`` or the
    constant check in ``data_file_uses``.
    """
    plain = f"path = 'wind/ahe{suffix}'"
    fstring = f"path = f'{{root}}/ahe{suffix}'"
    assert [n for n, _ in data_file_uses(plain)] == [1]
    assert [n for n, _ in data_file_uses(fstring)] == [1]


@pytest.mark.parametrize(
    "snippet",
    [
        "df = pd.read_hdf(path)",
        "store = pd.HDFStore(path)",
        "df = pd.read_pickle(path)",
        "df = pandas.read_csv(path)",
        "df = read_csv(path)",
        "df = pd.read_parquet(path)",
        "a = np.load(path)",
        "a = numpy.load(path)",
        "obj = pickle.load(fh)",
        "cdf = cdflib.CDF(path)",
        "ds = netCDF4.Dataset(path)",
        "ds = xr.open_dataset(path)",
        "ds = xarray.open_mfdataset(paths)",
        "hdul = fits.open(path)",
        "f = h5py.File(path)",
        "import cdflib",
        "import netCDF4 as nc",
        "import h5py",
        "from astropy.io import fits",
        "import astropy.io.fits",
        "from pandas import read_hdf",
        "from numpy import load",
        "from pickle import load",
        "from cdflib import CDF",
    ],
)
def test_scanner_flags_a_data_file_reader(snippet):
    """Each reader call or import family is flagged on its line.

    ON FAILURE: the scanner misses a way to read a data file; fix ``READERS``,
    ``LOADERS``, ``DATA_MODULES`` or the call and import checks in
    ``data_file_uses``.
    """
    text = "x = 1\n" + snippet
    assert [n for n, _ in data_file_uses(text)] == [2]


def test_scanner_passes_clean_plotting_code():
    """Synthetic data, writers, and text that only mentions a reader are not flagged.

    ON FAILURE: the scanner flags code that reads no data file; narrow the
    check in ``data_file_uses`` that matched.
    """
    clean = (
        "import numpy as np\n"
        "import pandas as pd\n"
        "rng = np.random.default_rng(4)\n"
        "df = pd.DataFrame({'x': rng.normal(size=100)})\n"
        "df.to_hdf  # attribute access, not a read\n"
        "fig.savefig(tmp_path / 'out.png')\n"
        "label = 'read_csv is not called here'\n"
        "# pd.read_csv('data.csv') in a comment is not code\n"
        "obj = pickle.loads(blob)\n"
        "cfg = json.load(fh)\n"
        "name = 'csv'\n"
    )
    assert data_file_uses(clean) == []
