<!--
Spent-When: MARKED(<self>)
Supersedes: none
-->
# Plan: clean docstrings on Read the Docs, Scatter size/alpha variables, future-work notes to GitHub issues

## Context

Three requests from one session (2026-11-17):

1. **AlfvenicTurbulence docs render badly.** Confirmed from the live page and the local build: the
   causes are in the docstrings.
   - `Alfv\'en` in raw docstrings: reST reads `\'` as an escaped apostrophe, so the page prints
     "Alfv'enic" (5 sites: `alfvenic_turbulence.py:44,55,276,300,313`).
   - The module's References are plain `[1] ...` lines, not numpydoc `.. [1]` entries, so the `[1]`
     and `[3]` in Notes are dead text. The ORCID shows as a raw `<https://...>`. Reference [3] has
     no DOI (Crossref confirms `10.3847/1538-4357/aab03d` is Woodham et al. 2018, ApJ 856, 49).
   - Smaller defects: `eb` has a split summary with no period; `averaging_info` has a sentence
     fragment; typos "calcualte" and "used to calculated".
   - The same References defect is in `Plasma.nuc` (`plasma.py:1748,1775`).
   - The sibling form is `tools/__init__.py:215-230`: `[1]_` in the text, `.. [1]` in References.
2. **Scatter gets per-point `size` and `alpha` variables.** Each is normalized by a matplotlib
   `Normalize` instance, used as is, then mapped onto marker area or alpha. The author approved the
   diagram. A docs example will show it with a size key built from matplotlib's
   `legend_elements` (no new API for the key).
3. **Future-work notes leave the published docs and become GitHub issues.** The case the author
   found is the "Propoded Updates" section of the `plasma` module docstring (`plasma.py:4-26`).
   The only other future-work statement that renders is `scatter.py:34`, "This difference is
   documented for now and needs to be revisited." (`# TODO` comments do not render; out of scope.)

**Reference [2], Telloni & Bruno (2016):** the author has deferred this decision. Git history
shows it was cited in the original module for a `-1` sign flip in `cross_helicity` and `sigma_c`
("so outward propagation is positive"). Commit `fcadc235` (2019-03-25) removed the flip and the
citation and kept the reference. It stays listed; see Stage A for how it renders without failing
the `-W` docs build.

## Stage A: docstrings render cleanly (commit `docs(core): ...`)

Files: `src/solarwindpy/core/alfvenic_turbulence.py`, `src/solarwindpy/core/plasma.py` (`nuc`).

- `Alfv\'en` becomes `Alfvén` (UTF-8 is already used in docstrings, e.g. "Hernández").
- Module References: `.. [1]` and `.. [3]` entries, cited in Notes as `[1]_` and `[3]_`; add the
  DOI to [3]; make the ORCID an RST link (`` `Lloyd Woodham <https://orcid.org/...>`__ ``).
  Telloni & Bruno stays as an unnumbered entry after them. A numbered citation nobody cites
  triggers Sphinx's "Citation [...] is not referenced" warning under `-W`. No claim changes.
- `eb`: one-line summary, matching `ev`. `averaging_info`: one sentence. Fix both typos.
- `Plasma.nuc`: `[1]` becomes `[1]_` and `.. [1]`.

Tests (test-first, in `tests/test_docstrings.py`; land as `xfail(strict=True)`, then fix):
- new `test_no_public_docstring_escapes_an_apostrophe`: no public docstring contains `\'` (it
  renders as a stray apostrophe).
- new `test_numbered_references_are_numpydoc_footnotes`: in a References section, a line that
  opens with `[n]` is written `.. [n]`.
- guards: the existing four tests in `test_docstrings.py`, `tests/core/test_alfvenic_turbulence.py`,
  and the doctests in `alfvenic_turbulence.py`.

## Stage B: future-work notes become GitHub issues (outward: created only after approval)

Searched every module docstring for proposed-updates sections and dated notes (`grep` for
section headings, `(YYYYMMDD)` stamps, "would be", "revisit"). The only hits that render are
`plasma.py:4-26` and `scatter.py:34`. Each item's status, checked in code:

| Note (plasma.py) | Status | Action |
|---|---|---|
| `plasma % a` / subtract an ion | covered by `Plasma.drop_species` (`plasma.py:626`) | no issue |
| `__getitem__` / `__iter__` over ions (2018-03-16) | absent | issue 1 |
| `Plasma.__len__` = number of ions (2018-03-16) | absent | issue 1 |
| `__format__` for `str.format` (2018-03-16) | absent | issue 2 |
| split each class into its own file (2018-02-17) | done (`core/` has one file per class) | no issue |
| `Plasma.dropna` that rebuilds ions (2018-04-04) | absent | issue 3 |
| moved `_conform_species` to `base.Base` (2018-11-21) | history note, done (`base.py:282`) | no issue |

No existing issue duplicates these (`gh issue list --state all`, 100 issues read).

Draft issues (label `type:feature`; issue 4 also gets `domain:plotting`):
1. **Plasma: container protocol over its ions (`__len__`, `__iter__`, `__getitem__`)**. Body: the
   two 2018 notes verbatim with their dates, including the caution that this "could have
   complicated results as to how we actually access the underlying data and objects stored in the
   DataFrame"; current state: `Plasma` defines none of the three.
2. **Core objects: define `__format__` for use with `str.format`**. Body: the 2018-03-16 note.
3. **Plasma.dropna that drops rows and rebuilds the ions**. Body: the 2018-04-04 note, plus a
   pointer to the missing-data page (`docs/source/missing_data.rst`) as the current behaviour.
4. **Scatter: should a log axis hold log10(abs()) like Hist2D and SpiralPlot2D?** Body: the Notes
   paragraph from `scatter.py:26-34`.

Then (commit `docs(core): ...`, `docs(plotting): ...`): delete the "Propoded Updates" section,
keeping the module summary line; replace scatter.py's "needs to be revisited" sentence with a
link to issue 4. Tests: no behaviour change; the doctest and docs build are the guards.

## Stage C: Scatter `size` and `alpha` variables

API:
```python
sc = Scatter(x, y, z=None, size=None, alpha=None, logx=None, logy=None, clip=None, mask=None)
sc.make_plot(..., size_norm=None, size_range=(9, 144), alpha_norm=None, alpha_range=(0.15, 1.0))
```
- The default alpha range starts at 0.15, the faintest alpha at which a marker is still visible.
  A caller who passes a lower end gets it as given; the floor applies only to the default.
- The norm's `vmin`/`vmax` are in data units: which values land at 0 and 1. `*_range` is in marker
  units: the area (pt²) or alpha at 0 and 1. The default area range is ½× to 2× matplotlib's
  default marker diameter (6 pt, so 36 pt² area). Author's decision (2026-11-17): defaults that
  callers can override.
- `size` and `alpha` are per-point Series, aligned by label like `z`, held in `sc.data` as the
  columns `"size"` and `"alpha"`. A NaN or infinite value drops the point, as for `z`.
- `*_norm` takes any `matplotlib.colors.Normalize` (`Normalize`, `LogNorm`, `PowerNorm`, ...),
  used as is. None means `Normalize()`, scaled to the drawn points. The package adds one step:
  normalized value `f`, clipped to [0, 1], becomes `lo + f * (hi - lo)`. A value outside the
  norm's `vmin`/`vmax` therefore saturates at an end. A value the norm masks (≤ 0 under `LogNorm`)
  is not drawn, like a value ≤ 0 on a log axis.
- A reversed range inverts the mapping: `alpha_range=(1, 0.15)` makes high values faint.
- `TypeError` if `size` is set and `make_plot` gets `s=`, or `alpha` is set and `make_plot` gets
  `alpha=`, or a `size_*`/`alpha_*` keyword arrives without its variable.
- The normalization sees only drawn points (after mask, NaN, `alim`, clip).
- With `connect=True` and no z, the segment colour is the points' colour at full opacity, not
  point 0's alpha. The colorbar stays opaque (matplotlib drops an array alpha on colorbars).

Code: extend `ColorPlot._set_data` (`plotting/base.py:659`) to take the extra per-point columns
into `_PlotSource`'s coords (`plotting/binned.py:287`), so alignment and NaN-dropping reuse
`_combine`/`_usable`. Mapping and checks live in `Scatter.make_plot` (`plotting/scatter.py:93`).
`Hist2D` and `SpiralPlot2D` are unchanged.

Tests (`tests/plotting/test_scatter.py`; land as `xfail(strict=True)`, then implement):
- size maps linearly: `size=[1, 2, 3]` with ends `(10, 30)` gives `get_sizes() == [10, 20, 30]`
  (hand computed).
- alpha maps linearly: `alpha=[0, 5, 10]` with ends `(0.2, 1)` gives `[0.2, 0.6, 1.0]`.
- a passed `LogNorm` is used: `[1, 10, 100]` gives low, middle, high.
- a reversed end pair inverts; values outside `vmin`/`vmax` saturate.
- NaN in `size` drops that point from `get_offsets()`.
- the three `TypeError` cases (`pytest.raises(..., match=...)`).
- guards: every existing test in `test_scatter.py`, and the `Scatter` doctest.

Commits: `test(plotting): ...` (xfail), `feat(plotting): ...` (removes markers), plus a
CHANGELOG `### Added` entry under `[Unreleased]`.

## Stage D: docs example (commit `docs(usage): ...`)

In `docs/source/usage.rst` under "Individual points", after the no-z example, add a paragraph
and a `.. plot::` block in the guide's form (seeded synthetic data, self-contained). Proposed
content: x = `v`, y = thermal speed `w`, `size=n`, and `alpha` = a per-point fit uncertainty,
with reversed alpha ends so uncertain points fade. Add a size key from
`points.legend_elements("sizes", num=[...], func=<inverse of the mapping>)`, titled with the
density label's string. Labels use `TeXlabel`.

## Verification

- `conda run -n solarwindpy pytest -q` (the full suite, also run by the commit hook).
- `conda run -n solarwindpy pytest --doctest-modules src/solarwindpy -q`.
- Strict docs build, as CI runs it: `cd docs && SPHINXOPTS="-W --keep-going -n" make html`.
  Then read the built text of the `alfvenic_turbulence`, `AlfvenicTurbulence`, `plasma` and
  usage pages: no "Alfv'en", citations are links, ORCID is a link, no "Propoded Updates",
  and the new figure renders.
- `pre-commit run ruff-check` / `ruff-format` on touched files.
- Watch each new test fail against deliberately broken code (TEST_PATTERNS.md).
- After the GitHub issues are created, check each with `gh issue view <n>`.

## Order

A, then B (create the issues, verify them, then edit the docstrings), then C, then D. Each stage
is its own commit or commits, with the suite passing. Nothing is pushed.

---

# Round 2 (2026-11-17): scales and guides — author-settled design

Stages A–D are committed (unpushed): 43283a33..57f5a5b7. Round 2 replaces the loose
`size_norm`/`size_range`/`alpha_norm`/`alpha_range` keywords from f71e56eb (unpushed, under
Unreleased only, so no downstream user).

## Settled by the author (do not revisit)
- One home per encoding channel, as a small public class holding the scale and its guide,
  validated at construction, with a readable `__str__`/`__repr__`, shareable across panels the way
  `BinnedData` is shared across plots (author compared it to BinnedData).
  - `ColorScale(norm=None, cmap=None, cbar=True, cbar_kwargs=None)`
  - `SizeScale(norm=None, range=(9, 144), key=True, key_kwargs=None)` — range in pt² of area; `key`:
    False/None = no key, True = ~4 values chosen automatically, a sequence = those data values.
    `key_kwargs` passed to `ax.legend`. The key is opaque (alpha=1).
  - `AlphaScale(norm=None, range=(0.15, 1.0), cbar=True, cbar_kwargs=None)` — the alpha bar is a
    colorbar whose colormap is one colour ramping in alpha over `range`, ticks in data units via
    the norm. 0.15 is the default "minimum viable alpha"; a caller's lower end is used as given.
  - Norms are matplotlib `Normalize` instances used as is (matplotlib autoscales unset vmin/vmax in
    place, so a shared scale with unset limits takes the first panel's limits; document this, and
    `print(scale)` then shows the limits used). Norm maps data -> [0, 1]; range maps [0, 1] -> marker
    value; a reversed range inverts; f is clipped to [0, 1] so values outside vmin/vmax saturate;
    a value the norm masks is not drawn.
- Colour: the plain keywords (`norm`, `cmap` in kwargs, `cbar`, `cbar_kwargs`) stay as the common
  path. Plotters build a `ColorScale` internally from them, so all channels share one machinery.
  `make_plot(color_scale=ColorScale(...))` is also accepted; passing it together with any plain
  colour keyword raises TypeError.
- Scatter: `make_plot(..., color_scale=None, size_scale=None, alpha_scale=None, draw_order=None,
  draw_ascending=True)`. A size/alpha variable without a scale gets the default scale. A scale
  without its variable raises TypeError. `s=` with a size variable, `alpha=` with an alpha variable
  raise TypeError. `connect=True` with an alpha variable raises TypeError (for now).
- `draw_order`: None (row order), "size" or "alpha", sorted by the marker value (area or opacity),
  `draw_ascending=True` draws low to high, so the highest is on top; faint-on-top is
  `draw_order="alpha", draw_ascending=False`. Segments are unaffected.
- Labels: Scatter's `set_labels` gains `size=` and `alpha=`; the size key and the alpha bar take
  their titles from them; the plot's `path` gains their parts when set.
- Return: a namedtuple `Guides(color, size, alpha)` of drawn artists (Colorbar, Legend, Colorbar),
  each None when not drawn. Name `guides` chosen by the author. Aligned across siblings now:
  `Scatter.make_plot -> (ax, points, segments, guides)`,
  `Hist2D.make_plot -> (ax, pc, guides)`, `SpiralPlot2D.make_plot -> (ax, collection, guides)`
  (and any other make_plot-like method in those classes that returns a bare cbar today).
  Hist2D/Spiral fill only `guides.color`. API break, accepted.

## Implementer's choices (reversible before push; report them)
- The three scale classes live in a new module `src/solarwindpy/plotting/scales.py` (one concept,
  one home; base.py is already ~1400 lines). `Guides` sits with the other plot namedtuples in
  `plotting/base.py`.

## Stages
- E: `Guides` return + `ColorScale` across Hist2D, SpiralPlot2D, Scatter (colour channel only).
- F: `SizeScale`, `AlphaScale`, the alpha bar, the size key, labels/path, draw_order; replace the
  f71e56eb keywords; docs: rewrite the usage-11 example (size + alpha, with alpha bar and package
  size key) and add a complete five-variable example (x, y, z colour, size, alpha).

---

## Empirical Findings (2026-11-18 trial run)

### End-state metrics

- Commits on master from `43283a33` to `7c781a59`: 33 (`git log --oneline 4f8a14f2..7c781a59 | wc -l`); 77 files changed, +2812/−813 (`git diff --shortstat 4f8a14f2 7c781a59`).
- Full suite in the rebuilt env before the release: 6847 passed, 16 skipped (`pytest -q`); strict docs build (`sphinx-build -W --keep-going -n`) exit 0, 0 warnings, at `40330110`.
- Released as v0.6.0: publish run 44195376310, all 9 platform-matrix jobs, `build-and-publish` and `update-conda-feedstock` success; PyPI lists `solarwindpy-0.6.0-py3-none-any.whl` and `solarwindpy-0.6.0.tar.gz`.

### Acceptance Criteria

The plan carries a Verification section rather than numbered ACs; each item is a row.

| AC | Status | Evidence |
|---|---|---|
| Stage A: AlfvenicTurbulence and `Plasma.nuc` docstrings render (no "Alfv'en", linked citations, ORCID link) | PASS | `75c07f7d`; tests `test_no_public_docstring_escapes_an_apostrophe` and `test_numbered_references_are_numpydoc_footnotes` (`43283a33`) each failed against a reintroduced `\'` and plain `[1]` line, naming `AlfvenicTurbulence.rA` and `Plasma.nuc` |
| Stage B: future-work notes moved to GitHub issues and out of the docstrings | PASS | issues #538, #539, #540, #541 open (`gh issue view`); `310300c1`, `f0142923` |
| Stage C, round 2: Scatter `size` and `alpha` through `SizeScale` and `AlphaScale`, `ColorScale`, a `Guides` return on every plotter | PASS | `8dec4ee1`, `f36ed956`, `00950396`, `ad67ce6e`; `tests/plotting/test_marker_scales.py`, `tests/plotting/test_color_scale.py` |
| Stage D: usage example for size and alpha, plus a five-variable example | PASS | `usage.rst` "Size and opacity" and "Five variables"; rendered PNGs inspected at `/tmp/swp-docs-H-203742/_images/usage-11.png` and `usage-12.png` |
| Strict docs build exits 0 | PASS | `/tmp/swp-docs-review-5.log`: exit 0, `grep -c WARNING` = 0; docs CI for `40330110` success |
| Each new test fails against deliberately broken code | PASS | broken-code tables in the messages of `f36ed956`, `00950396`, `ad67ce6e` (27, 7 and 4 plants respectively) |
| Windows suite passes | PASS | dry-run publish 44193760147 and release run 44195376310: `platform-matrix (windows-latest, 3.12/3.13/3.14)` success |

### Deviations from plan

- The Scatter API was redesigned in a second round with the author (2026-11-17): the interim `size_norm`/`size_range`/`alpha_norm`/`alpha_range` keywords (`f71e56eb`) were replaced by `SizeScale`, `AlphaScale` and `ColorScale` in `solarwindpy.plotting.scales`, and every plotter returns `Guides(color, size, alpha)`. The plan's Round 2 section records the settled design.
- Added at the author's request after the plan: an alpha bar and a package-drawn size key, `draw_order`, faint and smallest markers on top by default, the alpha bar's placement rule, default figure size in the examples, the property layout CSS fix and the property `Returns` cleanup (49 properties), and the usage-guide heading changes.
- Not in the plan: a strict-docs-build failure already on master from `152348bd` was fixed (`e1c9d5da`); the release surfaced a Windows `UnicodeDecodeError` from default-encoding text reads, fixed at 70 sites (`fd0539e7`, `a0d7b39d`); the first `v0.6.0` tag (on `8d2203de`) published nothing, was deleted, and was re-tagged on `7c781a59` after a dry-run publish passed on Windows.
- Environment: the `solarwindpy` conda env was rebuilt from `solarwindpy.yml`, which gained `python-build`, `setuptools-scm` and `astropy-base` (`8d2203de`, `b7c17a78`).

### Commits

- `43283a33` test(docs): pin escaped apostrophes and plain numbered references in docstrings
- `75c07f7d` docs(core): render AlfvenicTurbulence and Plasma.nuc docstrings cleanly
- `310300c1` docs(core): move the plasma module's proposed updates to GitHub issues
- `f0142923` docs(plotting): point Scatter's log-axis note to its GitHub issue
- `e1c9d5da` docs(plotting): name the label base class in set_labels' kwargs type
- `9f8b3c97` test(plotting): pin Scatter size and alpha variables as strict xfails
- `f71e56eb` feat(plotting): add per-point size and alpha variables to Scatter
- `57f5a5b7` docs(usage): show Scatter's size and alpha variables
- `be0d9323` test(plotting): pin ColorScale and make_plot(color_scale=) as strict xfails
- `8dec4ee1` feat(plotting)!: return a Guides record and accept a ColorScale in every draw method
- `c95bb9fe` test(plotting): pin norm given as a matplotlib scale name as strict xfails
- `eb67cc77` fix(plotting): accept a matplotlib scale name as a colour norm again
- `c34deb30` test(plotting): pin SizeScale, AlphaScale and Scatter's guides as strict xfails
- `f36ed956` feat(plotting)!: draw Scatter's size and alpha through SizeScale and AlphaScale
- `5130be0a` docs(plotting): name the scales' private bases as unlinkable in nitpick_ignore
- `060eda0d` test(plotting): pin faint-on-top, a top alpha bar and a size key beside the legend as strict xfails
- `00950396` feat(plotting)!: draw faint points on top, the alpha bar above the axes, the size key beside the legend
- `00340a75` test(plotting): pin the alpha bar on the right without a z colorbar and the smallest markers on top as strict xfails
- `ad67ce6e` feat(plotting)!: stand the alpha bar on the right without a z colorbar, draw the smallest markers on top
- `eaa02a20` fix(docs): stack property entries instead of flowing them side by side
- `be1d5289` test(docs): pin no Returns section on a public property as a strict xfail
- `b5352d5f` docs: fold property Returns sections into the summary or body
- `e0f46f9e` docs(usage): head each example in the plot sections
- `fb19539d` docs(usage): rename the plot sections and nest shared bins under Bins
- `b9e88391` docs(usage): make the save path its own section
- `40330110` docs(usage): place the save path after Labels
- `c691c397` chore: ignore Claude Code agent worktrees
- `a17f82ff` docs(changelog): prepare v0.6.0 release notes
- `8d2203de` build(env): list the release build tools in the env spec and dev extras
- `fd0539e7` fix: read the package data files as UTF-8
- `a0d7b39d` fix: name UTF-8 at every text read and write in tests and scripts
- `b7c17a78` build(env): take astropy-base in the dev env spec
- `7c781a59` docs(changelog): note the UTF-8 data-file reads in v0.6.0

## Spent-Mark: executed, findings recorded
