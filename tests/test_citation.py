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


# The newest release section of CHANGELOG.md: "## [X.Y.Z] - YYYY-MM-DD".
RELEASE_HEADING = re.compile(
    r"^## \[(\d+\.\d+\.\d+[^\]]*)\] - (\d{4}-\d{2}-\d{2})$", flags=re.MULTILINE
)


def test_citation_cff_names_the_newest_changelog_release():
    """``CITATION.cff``'s version and date are the newest release in ``CHANGELOG.md``.

    The release commit writes the version section of ``CHANGELOG.md``; this test
    makes the same commit set ``version`` and ``date-released`` in
    ``CITATION.cff``, so the citation names the current release. The publish
    workflow refuses a tag that differs from it.

    ON FAILURE: the code is wrong; set CITATION.cff's version and date-released
    to the newest ``## [X.Y.Z] - YYYY-MM-DD`` heading in CHANGELOG.md.
    """
    cff = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    newest = RELEASE_HEADING.search(changelog)
    assert newest is not None, "CHANGELOG.md has no release heading"
    version, date = newest.groups()
    assert (cff["version"], str(cff["date-released"])) == (version, date)
