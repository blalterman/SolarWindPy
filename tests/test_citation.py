# Spent-When: PERMANENT(SolarWindPy stops publishing citation metadata)
# Supersedes: none
"""The citation shown in the README matches the citation files.

GitHub cannot render an RST ``include``, so ``README.rst`` carries its own copy
of the BibTeX entry in ``CITATION.rst``. ``CITATION.cff`` feeds GitHub's "Cite
this repository" button. These tests keep the three in step.
"""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def bibtex_blocks(path):
    """BibTeX entries in ``path``'s ``.. code-block:: bibtex`` directives."""
    text = path.read_text(encoding="utf-8")
    blocks = re.findall(
        r"^\.\. code-block:: bibtex\n\n((?:(?:   .*)?\n)+)", text, flags=re.MULTILINE
    )
    return [
        "\n".join(line[3:] for line in block.rstrip("\n").splitlines())
        for block in blocks
    ]


def test_readme_bibtex_is_the_citation_file_bibtex():
    """The README's BibTeX entry is identical to the one in ``CITATION.rst``.

    Identity: both files show one BibTeX block, and the README's is a copy.

    ON FAILURE: the README and CITATION.rst citations diverged; make them match.
    """
    readme = bibtex_blocks(ROOT / "README.rst")
    citation = bibtex_blocks(ROOT / "CITATION.rst")
    assert len(citation) == 1, citation
    assert readme == citation


def test_bibtex_doi_is_the_citation_cff_doi():
    """The BibTeX ``doi`` field is the DOI declared in ``CITATION.cff``.

    Identity: both describe the same Zenodo concept DOI.

    ON FAILURE: CITATION.rst and CITATION.cff name different DOIs; make them match.
    """
    cff = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))
    (entry,) = bibtex_blocks(ROOT / "CITATION.rst")
    match = re.search(r"doi\s*=\s*\{([^}]+)\}", entry)
    assert match is not None, entry
    assert match.group(1) == cff["doi"]
