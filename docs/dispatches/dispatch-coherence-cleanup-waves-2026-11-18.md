<!--
Spent-When: MARKED(<self>)
Supersedes: none
-->

# Dispatch: coherence cleanup in three waves (packages A to I, with Q11)

owner: /Users/blalterman/observatories/code/SolarWindPy

**Generated:** 2026-11-18
**Branch:** master
**Work type:** software
**Serves:** `GOVERNANCE.md` § Intent, "Defined once, layered"; § Intent, "Physics carries its reasoning"; § Objectives, "Every implemented physical result cites its source" and "On master, the test suite, the documentation build with warnings as errors, and the import-layering check pass"

## Governing Property

Each physical quantity, unit, convention and name in SolarWindPy has one definition, each name
predicts what it holds, each layer imports only the layers beneath it, and each implemented
physical result names its source. A change anywhere in the package can break this property: a
second copy of a formula, a logger named for the wrong module, an input check that vanishes under
`python -O`, or a constant with no citation each violate it.

Derives from: `GOVERNANCE.md` § Intent, "Defined once, layered."

## Purpose

The mechanism: a fact written in two places drifts, because a change reaches one copy and not the
other. SolarWindPy is executed by AI sessions against declared conventions, so every second copy
(of a formula, a logger helper, a clip percentile, a level-name list, a release procedure, an env
recipe) is a place where execution follows the stale copy. Researchers pay with errors that carry
no message or results whose basis no docstring states; the author pays with attention spent
correcting drift instead of on the physics; sessions pay by following documents that describe
tooling that no longer exists.

The capability boundary, each existing check and what it leaves open:

- `lint-imports` (contracts in `pyproject.toml` `[tool.importlinter]`) enforces the layer order.
  It cannot host a shared helper below `core`, because it declares `core | tools` as independent
  siblings.
- `tests/test_public_imports.py` requires every public name to be documented. It does not detect
  two names for one concept.
- `tests/test_declared_versions.py` ties every restated Python version to `requires-python`. It
  does not read `solarwindpy.yml`.
- `tests/test_changelog_unreleased.py` resolves every `solarwindpy.` path in the Unreleased
  section against the checkout.
- `tests/test_no_line_pointers.py` refuses `file.py` line pointers in live files.
- `.claude/hooks/pre-commit-tests.sh` runs the full suite with a coverage floor on every commit.
  Three of its blocks after the gate cannot fail a commit.
- `.github/workflows/docs.yml` builds the docs with `-W --keep-going -n` on every push.

None of these finds a duplicated formula, a misnamed logger, an `assert` used as an input check,
or a percentile written twice. The items in § Scope close those instances one by one.

Derives from: `GOVERNANCE.md` § Intent, "The author's judgment, AI's execution."

## Intent

Once this lands, every item in § Scope holds on master: each formula, constant, logger helper,
clip rule, level-name list, env recipe and release procedure has one home; caller-input errors
raise a named exception with a message under `python -O` too; the public renames, removals and the
two physical-result changes the author ruled are in the code, the tests and the CHANGELOG; and the
retired development tooling is gone from the tree.

What makes it worth doing: a researcher reading `solarwindpy.core.ions.Ion.cs` or a plot's `clip`
finds one definition with its source, and a session reading the repository finds no document that
describes tooling that no longer runs.

Confirm this reading before designing against it: the work executes rulings and recommendations
already made, and every item below carries its decision. A disagreement with the scope or the
intent goes to the author per § Entry Protocol step 4; it is not resolved by rewriting an item.

This dispatch carries every anchor, decision, file list and test classification the executor needs.
It replaces two earlier plans, which are about to be removed and are cited here as revision records
only: `504a99a9:docs/dispatches/plan-coherence-cleanup-2026-11-04.md` (stages S1 to S40) and
`b01647bf:docs/dispatches/plan-spent-when-adoption-2026-09-16.md` (phases 1 to 6). Their line
numbers are stale and are not used. Stage IDs (S12), finding IDs (F98) and ruling IDs (Q5) below
are labels for grep and commit messages; each item states its content in words.

### Surface

User-facing changes, each one an author ruling (§ Scope, "Rulings"), each recorded in
`CHANGELOG.md` under `## [Unreleased]`:

- Renamed modules, no alias: `solarwindpy.instabilities.beta_ani` → `solarwindpy.instabilities.plots`;
  `solarwindpy.plotting.labels.datetime` → `solarwindpy.plotting.labels.epochs`.
- Moved: `SIDC.plot_on_colorbar` → `solarwindpy.solar_activity.plots` (call form: open item O1).
- Removed: `SIDC.cut_spec_by_ssn_band`, `SIDC.spec_by_ssn_band`, `SIDC.ssn_band_intervals`;
  `solarwindpy.solar_activity.icme.icmecat.RULES_OF_THE_ROAD` (replaced by a link to
  https://helioforecast.space/icmecat in the docstrings).
- Signatures: `Hist1D`, `Hist2D`, `Scatter` and `SpiralPlot2D` take their data variables
  positionally and every other parameter keyword-only; `beta_ani_inst(beta, a, b, c)` has no
  `None` defaults; `FFPlot.set_log(x=None, y=None)` matches `plotting.base.Base.set_log`.
- `clip`: the default cut moves from 0.01%/99.99% to 0.05%/99.95%, and `clip` accepts a pair
  `(lower, upper)`.
- Physical results: `Ion.cs` par and per use the CGL indices γ∥ = 3 and γ⊥ = 2 (first row of the
  example plasma: par 9.13 → 12.25 km/s, per 6.39 → 7.0 km/s, scalar unchanged at 7.42 km/s); the
  solar rotation rate in `AlfvenicTurbulence` becomes 2π/(25.38 d), moving the hand-computed
  rotation speed from 257.126 to 257.155 km/s.
- Errors: caller-input checks raise `TypeError`, `ValueError` or `InvalidParameterError` with a
  message instead of a bare `AssertionError`; `FFPlot.set_observations` raises `ValueError`.
- Logging: each class logs under `<its own module>.<class>` (for example
  `solarwindpy.core.plasma.Plasma`, today `solarwindpy.core.base.Plasma`); `swap_protons` logs on
  `solarwindpy.tools` with no handler, so its statistics no longer print by default.
- Python 3.15 joins the supported versions (classifiers, tox, the publish matrix).

Developer-facing: `solarwindpy.yml` pins `python>=3.12,<3.16` and adds `nodefaults`; CLAUDE.md §
"Environment" drops its `python=3.12` pin; the import-linter layers put `tools` below `core`.
Evidence: the rulings in § Scope; `git grep` counts in § State Verification.

### Parties

- The author holds the physics and the public API (`GOVERNANCE.md` § Intent, "The author's
  judgment, AI's execution"; `CLAUDE.md` § "Conventions"). The author answers open items O1 and O2
  and gives each OK named in § Blast radius.
- The executing session is the orchestrator: it launches one fresh subagent per package, merges,
  runs the post-merge checks and writes `CHANGELOG.md`.
- Each package subagent edits only its package's owned files, in its own git worktree.
- Researchers who use SolarWindPy meet the API breaks in the next release's CHANGELOG.
- GitHub Actions runs the dry-run publish.

### Seam

The work meets the existing system at: the import-linter contract in `pyproject.toml` (C changes
the layers); the pre-commit hook, which runs the full suite on every commit in every worktree; the
commit-msg hook (Conventional Commits); `tests/test_changelog_unreleased.py` (Unreleased entries
resolve against the checkout, so the orchestrator writes each entry after its code merges);
`tests/test_declared_versions.py` (H's version sites); `tests/test_public_imports.py` (renamed and
removed public names); `tests/test_hooks.py` (`.claude/settings.json` keys, no hooks registered,
pushes ask); `MANIFEST.in` and `[tool.setuptools.package-data]` (H's CSV move); and
`.github/workflows/publish.yml` (H's matrix and schedule). Between packages the seam is the merge:
rebase onto master, then `merge --ff-only`, with `CHANGELOG.md` written by the orchestrator alone.

### Layer

Edited layers: package code under `src/solarwindpy/` (core, tools, fitfunctions, instabilities,
plotting, solar_activity, examples); tests; `docs/source/`; development tooling (`.claude/`,
`.github/workflows/`, `solarwindpy.yml`, `tox.ini`, `pyproject.toml`). Governance text: only the
"Rebuild the env" bullet of `CLAUDE.md` § "Environment" changes (ruling Q18); `GOVERNANCE.md` is
not edited. The layer rule after package C: `tools` imports nothing from the package, `core`
imports only `tools`, `plotting` imports `core` and `tools`, and `fitfunctions`, `instabilities`
and `solar_activity` sit on top. Evidence: `GOVERNANCE.md` § Intent, "Defined once, layered"; the
T1 decision under package C.

### Blast radius

- Reversible through git: every code, test and doc edit, and every deleted file (25 retired files
  in package H). A deleted file is restored with `git checkout <commit>^ -- <path>`.
- Changes users see at the next release: the physical results and API breaks in § Surface. The
  author ruled each one; none needs a further OK.
- Outward, needing the author's explicit OK each time: any `git push` (the repo's settings make
  pushes ask, `tests/test_hooks.py::test_git_push_asks_and_is_not_allowed`); the dry-run publish
  (`gh workflow run publish.yml ...`), which runs on GitHub against the pushed master. This dispatch
  creates no tag, uploads nothing and makes no release.
- Shared repository state: a commit in a linked worktree runs the hook with an inherited `GIT_DIR`;
  a test that runs `git init` under it once wrote `core.bare = true` into the shared
  `.git/config`. § Operational Constraints checks it after every commit.

## Motivation

Every count below is re-derived by a command in § State Verification; each was measured on master
at `d0b51fa4` on 2026-11-18.

- Seven `_init_logger` copies name 57 of 74 class loggers after the base's module, not the class's
  (`git grep -c "def _init_logger" -- src`), and `swap_protons` installs its own stderr handler on
  a logger outside the `solarwindpy` tree.
- Fourteen `assert` statements in `src/solarwindpy/core`, ten of them caller-input checks that
  `python -O` removes; `set_sc("not a spacecraft")` under `-O` fails with
  `AttributeError: 'str' object has no attribute 'data'`.
- The sound-speed formula line is written twice, the Alfvén-unit coefficient twice, the Gaussian
  kernel three times, the log-normal moments twice, `set_new_line_for_units` four times.
- `Ion.cs` applies γ = 5/3 to its par and per columns while `polytropic_index` holds 3 and 2, and
  no docstring or test cites a source for either.
- The plot clip default 0.01%/99.99% is written in 18 files under `src/solarwindpy/plotting`,
  `tests/plotting` and `docs/source`, while the out-of-memory bin fallback uses 0.05%/99.95%.
- `Core._select` has 31 call sites that re-implement pandas selection.
- `.claude/` tracks 20 files; 14 of them describe tooling nothing runs, and `test-runner.sh` exits
  127 on macOS (`timeout: command not found`).
- The top supported Python is 3.14 in `publish.yml`, `tox.ini` and the classifiers;
  `solarwindpy.yml` resolves Python 3.15 and mixes channels on a fresh solve.
- No workflow runs `lint-imports` on a master push: `continuous-integration.yml` runs on pull
  requests and `feature/**` pushes, and `ci-master.yml` runs tests and ruff only.
- `GOVERNANCE.md` landed on 2026-11-18 (`7c91cb54`), so this dispatch can derive from it.

## Entry Protocol

```
This dispatch is the authorized work order. Execute it faithfully -- do NOT
re-derive, re-plan, or "improve" the scope and intent it settles.

1. Read this dispatch in full, then the files in "Read First".
2. Run the commands in "State Verification" and confirm reality matches what
   this dispatch assumes. Treat any mismatch as a divergence (step 4).
3. Execute the work; re-anchor on Intent after each verification gate.
4. On ambiguity or a reality-vs-dispatch divergence, follow the Divergence
   Resolution Ladder: articulate in plain English (often self-resolves) -> if
   unresolved, the shape-matched tool, distilled back to plain English -> who
   decides, per the session plugin's reference/decision-method.md step 7.
   Principle 8's kinds, scope and intent changes and any action that cannot
   be undone among them, go to the user with alternatives and a
   recommendation; settle every other choice through the method and record
   its trace in the commit message. Never guess past it, never mask a failure.
5. Report completion against the Acceptance Criteria.

---
```

## Scope

### How the work runs

The executing session is the orchestrator. It does not edit package files itself. For each wave it
launches one fresh subagent per package with `isolation: "worktree"`, all packages of the wave at
once, waits for every handback, then merges in the order below per § Closing Protocol, "Merge
protocol".

| Wave | Packages, in merge order | Starts when |
|---|---|---|
| 1 | I, C, F, H (H includes the Q24 removals) | § State Verification passes |
| 2 | A, B, D, E-plot (E-plot includes Q11) | wave 1 is merged and open items O1 and O2 are answered |
| 3 | E-core, then G (G includes S32) | wave 2 is merged; G's subagent launches after E-core merges |

After wave 1 merges, ask the author for an OK to push master and run the dry-run publish
(§ Verification, "Dry-run publish"). Waves 2 and 3 do not wait for the dry run's result unless it
fails; a failure is a divergence (§ Entry Protocol step 4).

The order encodes these dependencies: I deletes `Core._select` before A, B and E write code that
would call it, and I's renames land before C's logger names, B's edit of `epochs.py` and D's edit
of the colorbar plot block; C's layer change (T1) lands before its logger mixin (T3) and before D
edits `ICMECAT`; B owns the `growth_rate` check in `StabilityContours.plot_contours`, not A; H's
example-data move lands before A and E-core edit `examples/__init__.py`; F lands before G moves the
`tests/core` files; A and B land before E-core (`Plasma.load_from_file`,
`AlfvenicTurbulence.set_data`); E-plot rewrites the clip pins before G splits and renames those
test files.

**Subagent prompt.** Launch each package with this prompt, filling `<P>`:

```
You are package <P> of the dispatch
/Users/blalterman/observatories/code/SolarWindPy/docs/dispatches/dispatch-coherence-cleanup-waves-2026-11-18.md.
Read, in that file: § Intent, § Scope "Rulings" and "Open author items", § Scope "Package <P>",
§ Operational Constraints, § Anti-Patterns (including the must-not-modify row for <P>), and the
Acceptance Criteria whose IDs start with <P>-. Then read GOVERNANCE.md, CLAUDE.md and
.claude/docs/TEST_PATTERNS.md.
Work test-first: land each target test as pytest.mark.xfail(strict=True), then the code change
that removes the marker. One logical change per commit, Conventional Commits subjects, the hook
passing. Edit only the files package <P> owns. Do not edit CHANGELOG.md. Do not push.
Hand back, in this order: the output of `git rev-parse --abbrev-ref HEAD` and
`git rev-parse --show-toplevel`; `git log --oneline master..HEAD`; each <P>- acceptance command
with its output; a drafted CHANGELOG entry (Keep a Changelog sections: Changed, Removed, Fixed,
Added) for every user-facing change; and every divergence from the dispatch with its evidence.
```

### Rulings

The author's rulings, settled. The executor implements them and does not reopen them (§
Anti-Patterns). Each is stated in words; the Q-number is an index only.

1. `Plasma.cs("p1+a")` returns the combined-fluid sound speed sqrt(γ Σp / Σρ) from the summed
   pressure and summed mass density. Keep it. (Q1)
2. `Ion.cs` computes par with γ∥ = 3 and per with γ⊥ = 2, the CGL double-adiabatic indices (Chew,
   Goldberger & Low 1956, Proc. R. Soc. Lond. A 236, 112, DOI 10.1098/rspa.1956.0116; verify the
   citation against the publisher record before writing it). Scalar keeps γ = 5/3. Rewrite
   `tests/core/test_ions.py::IonTestBase::test_cs` from CGL and add a CHANGELOG entry. (Q2, QN1, T5)
3. Delete the stale `# should be 5/3` comment in `Plasma.cs`. (Q3)
4. The solar rotation rate is 2π/(25.38 d), the sidereal Carrington period, cited as Thompson
   (2006), A&A 449, 791, DOI 10.1051/0004-6361:20054262, §2.2. The pinned hand value in
   `test_raffaella_version_converts_gse_to_rtn_with_hand_computed_values` moves from
   257.12585161166068 to about 257.15539 km/s; recompute it by hand from the formula. (Q4)
5. Clip settings (Q5, eighth pass):
   - `True`: both tails at the default cuts 0.0005 and 0.9995 (0.05% and 99.95%);
   - `False` or `None`: no clipping;
   - `(lower, upper)`: each item is `True` (the default cut), `False` (no clip on that tail) or a
     number read as pandas `quantile` reads it, a fraction in [0, 1]; validate lower < 0.5 < upper
     and raise `ValueError` otherwise;
   - `"l"` and `"u"` stay as documented shorthands for `(True, False)` and `(False, True)`;
   - the per-axis mapping (`{"z": ...}`) composes with every form above;
   - one shared clip code path, which the binning out-of-memory fallback uses too.
   The default change needs a CHANGELOG entry and docstring updates.
6. Remove `SIDC.cut_spec_by_ssn_band` together with the properties `SIDC.spec_by_ssn_band` and
   `SIDC.ssn_band_intervals`, and their 7 tests. CHANGELOG entry. (Q6)
7. Rename `instabilities.beta_ani` to `instabilities.plots`. (Q7)
8. `plotting.labels.composition.Ion` keeps its name; the names `Base` and `tools` reused across
   subpackages stay (F116, F138). (Q8)
9. Rename `plotting.labels.datetime` to `plotting.labels.epochs`. (Q9)
10. Keep `examples._read_example` private and as it is; tests keep using it (F173). (Q10)
11. Plot constructors: the data variables come first and positional (`Hist1D`: x, y; `Hist2D` and
    `SpiralPlot2D`: x, y, z; `Scatter`: x, y, z, size, alpha), then `*`, and every setting after
    it is keyword-only. Shared settings keep one name across the classes. (Q11)
12. Each logger is named for its class's own module: `solarwindpy.core.plasma.Plasma`. (Q12)
13. `swap_protons` logs under `solarwindpy.tools`. (Q13)
14. Move `SIDC.plot_on_colorbar` to `solar_activity.plots`: a public API move with a CHANGELOG
    entry and a `docs/source/usage.rst` update. (Q14, T2)
15. `RULES_OF_THE_ROAD` becomes a link, never a copy. The docstrings state: follow the ICMECAT
    rules of the road at the HELIO4CAST site (https://helioforecast.space/icmecat). (Q15)
16. Exception classes: `TypeError` for a wrong type, `ValueError` for a bad value, and
    fitfunctions' own `InvalidParameterError`. `beta_ani_inst` loses its `None` defaults. (Q16)
17. `FFPlot.set_observations` raises `ValueError` with a message instead of its two asserts. (Q17)
18. `solarwindpy.yml` is the one home for creating the conda env: it holds the Python bound
    `python>=3.12,<3.16` and the channels, with `nodefaults`. CLAUDE.md drops its `python=3.12`
    pin, and README, CONTRIBUTING and `docs/source/installation.rst` point to the yml. (Q18, QN6)
19. Python 3.15 joins the publish matrix, the tox envlist and the classifiers, kept consistent by
    `tests/test_declared_versions.py`; a dry-run publish on all three operating systems verifies
    it, with the author's OK. (QN6)
20. CI runs the full matrix (Linux, macOS, Windows × Python 3.12 to 3.15) weekly on master and
    before every release; the strict docs build and `lint-imports` may stay on one Linux job.
    (governance follow-up, `d0b51fa4`)
21. Retire the 11 remaining unused `.claude` tooling files and their permission rules. (Q20)
22. Retire `.claude/hooks/test-runner.sh` and its 7 allow rules. (Q21)
23. Retire `.claude/docs/DEVELOPMENT.md` and `.claude/docs/MAINTENANCE.md` after moving their
    release-script usage into `.claude/docs/RELEASING.md`, which stays a document. (Q22)
24. Delete `Core._select`. Its 31 call sites use native pandas: `.xs` for one label,
    `.loc[:, pd.IndexSlice[...]]` for several. (Q23)
25. Remove the 12 development files no tracked file references. (Q24)
26. Values are stored in display units; `GOVERNANCE.md` replaces the planned objectives document
    and exists. (Q25)
27. The package tree is not exempt from Spent-When declarations. Until the deferred header work
    lands, every file created during this work gets a declaration at write time: inline for tests
    and docs, a sidecar for a new package module. Shipped modules carry no inline header;
    `src/solarwindpy/plotting/scales.py.spent-when` stays. (Q26, QN2, sixth pass)
28. Pre-1.0 API breaks are made outright, with no alias or deprecation shim (coherence rulings,
    2026-11-04).

Out of scope by ruling: the build-strip of headers and sidecars, inline module headers, and the
declaration backlog (package J, deferred: QN5, SW1, SW2); `GOVERNANCE.md` itself (package K,
done); the public/private repository split and its two version schemes; alpha options for `Hist2D`
and `SpiralPlot2D`.

### Open author items

Measured against the rulings above, two items set a user-facing name or format that no ruling
fixes. The orchestrator puts both to the author before launching wave 2, each with its
recommendation; the recommendation stands only on the author's answer.

- **O1, the call form of the moved `plot_on_colorbar`.** Ruling 14 fixes the module, not the form.
  Recommendation: a module function `solarwindpy.solar_activity.plots.plot_on_colorbar(indicator,
  cax, t0, t1, vertical_cbar=True)` taking the `SIDC` instance first, returning what the method
  returns today. Grounds: `SSNPlot.__init__` requires a `plasma_index` window while this draws
  `t0:t1`, so a method on `SSNPlot` would need an instance whose window it ignores; the function
  keeps the name and every other parameter. Alternative: a method on `SSNPlot`.
- **O2, the long clip strings.** Ruling 5 names `"l"` and `"u"`; the code and five docstrings also
  accept `"lower"`, `"upper"` and `"both"` (`_CLIP_STRINGS` in `solarwindpy.plotting.binned`).
  Recommendation: keep all five strings unchanged in this dispatch, because removing an accepted
  value is a public removal no ruling names. Alternative: remove the three long forms (one name
  per concept).

Recorded as out of scope, not blocking: the `SIDC.calculate_extrema_kind` docstring says
"ssn < cycle mean" while the code and `test_extremum_kind_follows_the_half_max_rule` use half the
cycle maximum (F157, a physics question for the author); leave that docstring line unchanged.
Findings F60, F64 and F67 (stage S14) and the F112 `set_beta` Series option (stage S13) are not
part of this dispatch.

### Package I: public renames and native column selection (wave 1)

Owns: `src/solarwindpy/instabilities/beta_ani.py` (becomes `plots.py`),
`src/solarwindpy/instabilities/__init__.py`, `src/solarwindpy/plotting/labels/datetime.py`
(becomes `epochs.py`), `src/solarwindpy/plotting/labels/__init__.py`,
`src/solarwindpy/solar_activity/plots.py` (`IndicatorPlot.__init__` only), `docs/source/usage.rst`
(the `labels.datetime` import line in the colorbar plot block only); in
`src/solarwindpy/core/{base,alfvenic_turbulence,ions,plasma,spacecraft,vector}.py` only
`Core._select`, `_ComponentFrame.__call__`, the column-access comment block above `_level_labels`,
and the 31 `_select` call sites; tests `tests/instabilities/test_beta_ani.py` (becomes
`test_plots.py`), `tests/plotting/test_{binned_data,derived_path,plain_string_label_warning,plot_invariants,return_order,integration}.py`,
`tests/test_docstrings.py`, `tests/plotting/labels/test_datetime.py` (becomes `test_epochs.py`),
`tests/plotting/labels/test_special.py`, `tests/plotting/labels/test_with_units_formatter.py`,
`tests/solar_activity/test_plots.py` (imports only), `tests/core/test_seams.py`.

1. **Q7 / F114. Rename `solarwindpy.instabilities.beta_ani` to `solarwindpy.instabilities.plots`.**
   - Anchor: module `solarwindpy.instabilities.beta_ani`, class `BetaRPlot`. Check:
     `git grep -n -w beta_ani -- src tests docs/source` (12 lines at `d0b51fa4`; none after).
   - Do: `git mv` the module and `tests/instabilities/test_beta_ani.py` to `test_plots.py`; update
     the import, `__all__` and the module list in `instabilities/__init__.py`; re-render the moved
     test's Spent-When line with `--emit` so its reversal names `instabilities.plots`.
   - Tests: update (import path) `tests/instabilities/test_beta_ani.py`,
     `tests/plotting/test_{binned_data,derived_path,plain_string_label_warning,plot_invariants,return_order}.py`,
     `tests/test_docstrings.py`; guard `tests/test_public_imports.py`.
2. **Q9 / F117. Rename `solarwindpy.plotting.labels.datetime` to `solarwindpy.plotting.labels.epochs`.**
   - Anchor: module `solarwindpy.plotting.labels.datetime` (`Timedelta`, `DateTime`, `Epoch`,
     `Frequency`, `January1st`). Check:
     `git grep -n -E "labels\.datetime|labels import .*datetime|^from \. import datetime" -- src tests docs/source`
     (10 lines at `d0b51fa4`; none after).
   - Do: `git mv` the module and `tests/plotting/labels/test_datetime.py` to `test_epochs.py`;
     update `plotting/labels/__init__.py` (`__all__`, the import, the `available()` loop),
     `IndicatorPlot.__init__`, and the plot-block import in `docs/source/usage.rst`. Drop the
     `as dt_labels` and `as datetime_labels` aliases in tests where the new name no longer
     shadows the standard library.
   - Tests: update (import path) `tests/plotting/labels/test_datetime.py`, `test_special.py`,
     `test_with_units_formatter.py`, `tests/plotting/test_integration.py`,
     `tests/plotting/test_plain_string_label_warning.py`, `tests/solar_activity/test_plots.py`;
     guard `tests/test_public_imports.py`, `tests/test_docs_plot_blocks.py`.
3. **Q23. Delete `Core._select`; call sites use native pandas.**
   - Anchor: `solarwindpy.core.base.Core._select`, `_ComponentFrame.__call__`. Check:
     `git grep -c "_select(" -- src tests` (7 files at `d0b51fa4`; none after).
   - Do: replace each call with `frame.xs(key, axis=1, level=level)` for one label (plain
     `frame.xs(key, axis=1)` on a flat Index) and `frame.loc[:, pd.IndexSlice[...]]` for several,
     which keeps the order given and raises `KeyError` on an absent label; never
     `.reindex(level=)`, which drops an absent label silently. Keep `_level_labels` and
     `_LEVEL_WORDS` (`Core._reduce_level` uses them). Reword the comment block above
     `_level_labels` so it no longer claims every selection goes through these methods. Rewrite
     the 6 direct calls in `tests/core/test_seams.py` through public callers and keep
     `test_component_selection_shares_the_parent_data`, the view-sharing check.
   - Tests: update `tests/core/test_seams.py`; guard every other test in `tests/core` (the full
     suite). A test that matched the old `"Unknown species ... Available:"` message is a
     divergence to report, not to rewrite silently.

CHANGELOG drafts due: Q7 and Q9 (Changed, breaking).

### Package C: one logger helper, tools below core (wave 1)

Owns: `src/solarwindpy/tools/__init__.py`; in `src/solarwindpy/core/base.py` the `Core` class
statement, `Core.logger`, `Core._init_logger`, the `_init_logger()` call in `Core.__init__` and
the import block; in `src/solarwindpy/core/plasma.py` the `_init_logger()` call in
`Plasma.__init__` only; in `src/solarwindpy/fitfunctions/core.py`,
`src/solarwindpy/plotting/base.py`, `src/solarwindpy/plotting/labels/base.py`,
`src/solarwindpy/solar_activity/base.py` and `src/solarwindpy/solar_activity/icme/icmecat.py`
each base's class statement, `logger`, `_init_logger`, the `_init_logger()` calls and the import
block; `src/solarwindpy/instabilities/verscharen2016.py` (`StabilityCondition._init_logger`, its
call, `import logging`); `src/solarwindpy/plotting/labels/elemental_abundance.py`
(`ElementalAbundance.set_species`); `src/solarwindpy/plotting/spiral.py` (the `SpiralPlot2D`
method with a local `getLogger`); `src/solarwindpy/solar_activity/sunspot_number/sidc.py` (the
`_init_logger()` call in `SIDC.__init__` only); `pyproject.toml` (`[[tool.importlinter.contracts]]`
only); `.claude/docs/TEST_PATTERNS.md` (§ "Structure and layering" only); `docs/source/usage.rst`
(a new "Logging" section, outside every plot block); tests `tests/tools/test_tools.py`,
`tests/solar_activity/test_base.py`, `tests/plotting/test_base.py`.

1. **T1. `tools` is the layer below `core`.**
   - Anchor: the layers contract "Subpackage layers: core and tools import nothing above them" in
     `pyproject.toml`; `solarwindpy.tools._warn`. Check: `grep -c '"core | tools"' pyproject.toml`
     (1 at `d0b51fa4`; 0 after).
   - Decision (method, Claude's): `tools` imports nothing from the package and every importer takes
     only `_warn`, so it already behaves as the bottom layer; the `|` independence was a
     translation choice in `ce6f4709`. Change the layers to `"core"` then `"tools"`, rename the
     contract so its name states the order, correct the `_warn` docstring sentence calling `core`
     an "independent sibling", and state the order in TEST_PATTERNS § "Structure and layering".
   - Tests: guard `lint-imports`, `tests/test_warning_attribution.py`, `tests/tools/test_tools.py`.
     Show the contract biting: in a scratch copy, plant `from ..core import base` in `tools`, watch
     `lint-imports` fail, discard the copy.
2. **S17 + T3 / F101, F133, F137 + Q12, Q13. One stateless logger mixin.**
   - Anchor: the seven `_init_logger` methods and six `logger` properties (symbols in the Owns
     list), `solarwindpy.tools.swap_protons` (its `logger is None` branch),
     `ElementalAbundance.set_species` (two root-logger warnings). Checks:
     `git grep -c "def _init_logger" -- src` (7 files at `d0b51fa4`; none after);
     `git grep -l "def logger" -- src` (6 files; after, only `src/solarwindpy/tools/__init__.py`);
     `git grep -n -E "addHandler|StreamHandler|setLevel|main\.solarwindpy|getLogger\(\)" -- src`
     (6 lines; none after).
   - Do: add one private mixin in `tools/__init__.py` beside `_warn` with a stateless property
     `logger` returning `logging.getLogger(f"{type(self).__module__}.{type(self).__name__}")`.
     Each of the seven bases inherits it. Delete the seven `_init_logger` methods, the six
     `logger` properties, every `_init_logger()` call (twelve sites, including `new._init_logger()`
     in `ICMECAT.filter`) and `StabilityCondition`'s unused logger. `swap_protons` with no
     `logger` uses `logging.getLogger(__name__)` with no handler and no `setLevel`; keep its
     public `logger=` parameter. `ElementalAbundance.set_species` logs through `self.logger`.
     `SpiralPlot2D` uses `self.logger` instead of its local `getLogger(__name__)`. Add no
     `NullHandler` anywhere: warnings keep reaching stderr through `logging.lastResort`. `ICMECAT`
     inherits the mixin only (this closes the logger half of S26 / F139). `Binning` keeps the
     logger its plot passes it.
   - Add a "Logging" section to `docs/source/usage.rst`: loggers are `solarwindpy.<module>.<Class>`
     and `solarwindpy.<module>`; `logging.basicConfig(level=logging.INFO)` or a handler on
     `logging.getLogger("solarwindpy")` shows them.
   - Tests, new first as `xfail(strict=True)`:
     `tests/tools/test_tools.py::test_every_package_class_logs_under_its_own_module` (parametrized
     over the package classes that inherit the mixin);
     `tests/tools/test_tools.py::test_swap_protons_logs_on_solarwindpy_tools_with_no_handler`;
     one test that `ElementalAbundance("Xx", "Fe")` logs on
     `solarwindpy.plotting.labels.elemental_abundance.ElementalAbundance`, not the root logger.
     Update `tests/solar_activity/test_base.py::test_loggers_sit_under_the_solarwindpy_logger`,
     `::test_loader_logger_sits_under_the_solarwindpy_logger` and
     `tests/plotting/test_base.py::test_str_and_logger_name_the_concrete_class`: they pin names
     for classes defined in the test module, which now log under the test module; assert the
     own-module rule instead. Guard `tests/plotting/labels/test_labels_base.py::test_logger_is_named_for_module_and_class`,
     the `ICMECAT().logger.name` test in `tests/solar_activity/icme/test_icmecat.py`,
     `tests/test_contracts_class.py::test_ion_has_logger`,
     `tests/tools/test_tools.py::TestSwapProtons::test_default_logger_does_not_accumulate_handlers`,
     and every `caplog` test (they capture on `solarwindpy` or the root logger).
3. **F138. The `tools` docstring states what holds.** Delete the module docstring's claim that its
   functions are "not yet organized into their own submodules". Check:
   `git grep -c "not yet organized" -- src/solarwindpy/tools/__init__.py` (1; none after). Tests:
   guard `tests/test_docstrings.py`.

CHANGELOG drafts due: logger names (Changed), `swap_protons` output (Changed).

### Package F: test hygiene (wave 1)

Owns: new `tests/_tracked.py`; `tests/test_tolerance_rule.py`, `tests/plotting/test_no_data_files.py`,
`tests/test_docs_plot_blocks.py`, `tests/test_docstring_math.py`, `tests/test_warning_attribution.py`,
`tests/test_no_line_pointers.py`, `tests/test_package_module_headers.py`; in
`tests/core/test_{alfvenic_turbulence,base,ions,plasma,quantities,spacecraft}.py` the module-level
`pd.set_option("mode.chained_assignment", "raise")` line only.

1. **S2 / F195. Scans read git-tracked files only.**
   - Anchor: the `rglob` scans in `test_tolerance_rule` (two), `test_no_data_files`,
     `test_docs_plot_blocks._found`, `test_docstring_math`, `test_warning_attribution`; the two
     existing helpers `tests.test_no_line_pointers._tracked_files` and
     `tests.test_package_module_headers._tracked_package_modules`. Check:
     `git grep -n rglob -- tests ':!tests/solar_activity/test_cache.py'` (6 lines; none after).
   - Do: extract one helper module `tests/_tracked.py` (form: `tests/plotting/_cases.py`) from the
     two existing copies and use it at all 8 sites, the two former copies included. Outside a git
     checkout, skip with `pytest.skip("not a git checkout")` as `test_package_module_headers`
     does. The two `test_cache.py` `rglob` calls walk a `tmp_path` fixture and stay.
   - Tests: update (file source only) the 8 files above; guard each vacuity and scanner self-test
     (`test_scan_covers_plotting_subfolders`, `test_the_guide_has_plot_blocks`, the
     `test_scanner_*` tests, `test_the_checker_finds_what_mathjax_rejects`,
     `test_the_guard_finds_a_direct_call`).
2. **S3 / F172. Delete the six `mode.chained_assignment` lines.** Pandas 3 ignores the option and
   warns `Pandas4Warning`; pandas 4 removes it. Check: `git grep -n chained_assignment -- tests`
   (6 lines; none after). Delete only: no new `filterwarnings` key in `pyproject.toml`, which
   three other packages edit. Tests: guard all 1050 tests in `tests/core`.

No CHANGELOG entry (tests only).

### Package H: tooling, environment, CI and retired files (wave 1)

Owns: `MANIFEST.in`; `pyproject.toml` (`[tool.setuptools.package-data]`, `[tool.pip-tools]`, the
classifiers); `solarwindpy.yml`; `CLAUDE.md` (the "Rebuild the env" bullet only); `tox.ini`;
`.github/workflows/publish.yml`; `.github/workflows/ci-master.yml`; `tests/test_declared_versions.py`;
`src/solarwindpy/examples/__init__.py` (`_DATA`, the CSV path in `_read_example`, the column
mapping in `load_plasma`); `src/solarwindpy/core/data/example_{epoch,plasma,spacecraft}.csv`
(moved to `src/solarwindpy/examples/data/`); `tests/test_examples.py` (docstrings only);
`.claude/docs/TEST_PATTERNS.md` (the sentence naming `src/solarwindpy/core/data/` only);
`.claude/settings.json`; `.pre-commit-config.yaml`; `setup.cfg`; `.claude/hooks/pre-commit-tests.sh`;
`.claude/docs/RELEASING.md`; and the 25 files it deletes, listed in items 4 to 7.

1. **S1 / F169, F201, F205. One package-data home; no dead pip-tools block.** Move
   `ssn_extrema.csv` into `[tool.setuptools.package-data]` and drop its `MANIFEST.in` line; delete
   `[tool.pip-tools]`. Checks: `grep -c csv MANIFEST.in` (1; 0 after), `grep -c pip-tools pyproject.toml`
   (1; 0 after). Tests: guard `tests/test_release_artifacts.py::test_wheel_installs_every_package_file`
   (it asserts `ssn_extrema.csv` is in the wheel, the positive control for the move) and
   `::test_sdist_keeps_tests_and_docs_source`.
2. **Q18 + QN6. The env spec, Python 3.15, and the weekly matrix.**
   - `solarwindpy.yml`: add `- nodefaults` under `channels:` and `- python>=3.12,<3.16` under
     `dependencies:`; rewrite the header sentence "No Python version is listed, so conda picks
     one". `CLAUDE.md` § "Environment", "Rebuild the env": drop the copy-and-pin step, so it reads
     `conda env create -f solarwindpy.yml`, then `conda run -n solarwindpy pip install -e ".[dev]"`.
     README.rst, CONTRIBUTING.md and `docs/source/installation.rst` already run
     `conda env create -f solarwindpy.yml` and restate neither version nor channels: leave them.
   - Python 3.15: add `'3.15'` to the `platform-matrix` in `publish.yml`, `py315` to the tox
     envlist and the 3.15 classifier. Extend `tests/test_declared_versions.py` to read the yml's
     `python` bound as one more site, so the yml's upper bound and the classifiers cannot
     disagree. Test-first: land the new site check as `xfail(strict=True)` before the yml gains
     its bound, then remove the marker in the commit that adds the bound.
   - Weekly matrix (ruling 20): add `schedule: - cron: '0 6 * * 1'` to `publish.yml`'s `on:`. On a
     schedule event `platform-matrix` runs the full suite on 3 OS × 4 Pythons, and every upload,
     release and feedstock step stays skipped, because each is gated on `workflow_dispatch` or a
     tag push. This keeps one home for the matrix.
   - Add a `lint-imports` step to `ci-master.yml`, so the import-layering check runs on Linux for
     every master commit as `GOVERNANCE.md` § Objectives states; today no workflow runs it on a
     master push.
   - Tests: update `tests/test_declared_versions.py`; guard the rest of it.
3. **S30 / F49, F85. The examples package owns its data and teaches the real labels.** Relabel the
   spacecraft CSV header from `pos_HCI`, `v_HCI`, `Carr` to `pos`, `v`, `carr` and delete the
   mapping in `load_plasma`; `git mv` the three example CSVs to `src/solarwindpy/examples/data/`;
   point `_DATA` at `solarwindpy.examples` and add `examples/data/*.csv` to package-data; update
   the CSV path sentence in TEST_PATTERNS and the `tests/test_examples.py` docstrings. Checks:
   `git ls-files src/solarwindpy/examples/data` (0 files; 3 after);
   `git grep -n 'resources.files("solarwindpy.core")' -- src/solarwindpy/examples` (1 line; none
   after). Tests: guard `tests/test_examples.py::test_load_plasma_finds_its_data_through_the_package`
   (the positive control for the move), `::test_load_plasma_holds_the_example_species_rows_and_spacecraft`,
   the `load_plasma` doctest, `tests/test_release_artifacts.py::test_wheel_installs_every_package_file`.
4. **S36 + Q20. Retire 11 unused `.claude` files.** `git rm` `.claude/README.md`,
   `.claude/WORKFLOW_TEMPLATE.md`, `.claude/branch-preservation.log`, `.claude/docs/HOOKS.md`,
   `.claude/hooks/coverage-monitor.py`, `.claude/hooks/create-compaction.py`,
   `.claude/hooks/validate-tags.sh`, `.claude/logs/phase0-time-tracking.md`,
   `.claude/scripts/cleanup-compaction-tags.py`, `.claude/scripts/generate-test.py`,
   `.claude/templates/test-patterns.py`. Remove their 4 allow rules from `.claude/settings.json`
   (coverage-monitor, create-compaction, and two generate-test rules; the ruling's "3" counted
   generate-test once) and the `.claude/templates` excludes in `.pre-commit-config.yaml` and the
   `[doc8] ignore-path` of `setup.cfg`. Tests: guard `tests/test_hooks.py`.
5. **S38 + Q21. The commit hook's blocks gate, and `test-runner.sh` retires.** Delete the three
   blocks after the `--cov-fail-under` gate in `.claude/hooks/pre-commit-tests.sh` (per-module,
   physics, performance: none can fail a commit). Measure coverage on H's branch with
   `conda run -n solarwindpy pytest --cov=solarwindpy -q -p no:randomly` and set the floor two
   points under the TOTAL in the comment, the echo and the flag (98% measured on 2026-11-18 gives
   96). Replace RELEASING.md's two "Coverage ≥95%" lines with a pointer to the hook's floor.
   `git rm .claude/hooks/test-runner.sh` and remove its 7 allow rules. Tests: guard
   `tests/test_hooks.py`; the suite under the new floor.
6. **S39 + Q22. Retire DEVELOPMENT.md and MAINTENANCE.md.** Move MAINTENANCE.md's "Conda Feedstock
   Automation" and "Release Monitoring" usage into RELEASING.md, repoint RELEASING.md's links to
   the two files, then `git rm` both. Keep RELEASING.md § "5. Dry-Run the Publish Workflow"
   unchanged: § Verification runs it. Tests: guard `tests/plotting/test_no_data_files.py`,
   `tests/test_no_line_pointers.py`.
7. **Q24. Remove the other 6 unreferenced development files.** `git rm`
   `scripts/analyze_imports_fixed.py`, `scripts/test_dynamic_imports.py`,
   `scripts/docstring_coverage.py`, `docs/conda-feedstock-automation.md`, `docs/RELEASE_PROCESS.md`,
   `setup.py`, and remove the `Bash(git add setup.py)` allow rule. The other 6 of Q24's 12 are in
   item 4. `setup.py` holds only `setup(use_scm_version=True)`, and `pyproject.toml` already
   configures `[tool.setuptools_scm]` with `dynamic = ["version"]`, so the version still
   resolves without it (AC H-1). Tests: guard `tests/test_release_artifacts.py`.

CHANGELOG draft due: Python 3.15 support (Added).

### Package A: named errors (wave 2)

Owns: in `src/solarwindpy/core/base.py` a level-name constant beside `_LEVEL_WORDS`,
`Base.mi_tuples`, and `Core._require_level_names` placed beside `Core._require_dataframe`; in
`src/solarwindpy/core/plasma.py` `Plasma._require_level_names` (removed), `Plasma.set_sc`,
`Plasma._set_aux`, `Plasma.set_data`, `Plasma.load_from_file`, `Plasma.estimate_electrons`,
`Plasma._set_ions`; in `src/solarwindpy/core/ions.py` `Ion.set_data`, `Ion._set_species`;
`src/solarwindpy/core/spacecraft.py` (`Spacecraft.set_data` and its Raises docstring);
`src/solarwindpy/examples/__init__.py` (`_read_example`'s level names only);
`src/solarwindpy/tools/__init__.py` (`swap_protons`' `reorder_levels` only); in
`src/solarwindpy/fitfunctions/core.py` `FitFunction.__init__` and `FitFunction._build_outside_mask`;
`src/solarwindpy/fitfunctions/plots.py` (`FFPlot.set_observations` only); in
`src/solarwindpy/instabilities/verscharen2016.py` `beta_ani_inst`, `StabilityCondition.set_beta_ani`,
`StabilityContours.set_beta` and the `ax` check in `StabilityContours.plot_contours`; tests
`tests/core/test_plasma.py`, `tests/core/test_spacecraft.py`, `tests/core/test_ions.py` (new tests
only), `tests/fitfunctions/test_core.py`, `tests/fitfunctions/test_plots.py`,
`tests/instabilities/test_verscharen2016.py` (new tests placed directly after the
`test_tk_kind_rejects_*` tests).

1. **S12 / F50, F55, F56, F57, F58. Core input checks raise named errors; level names have one home.**
   - Anchors: `solarwindpy.core.base.Base.mi_tuples`, `_LEVEL_WORDS`, `Core._require_dataframe`,
     `Plasma._require_level_names` and the methods in the Owns list. Checks:
     `git grep -n -E '^[[:space:]]*assert ' -- 'src/solarwindpy/core/*.py'` (14 lines at
     `d0b51fa4`); `git grep -n -E "def _require_level_names|columns.names ==|columns.names !=" -- src/solarwindpy/core`
     (3 lines); the level-name literal grep in AC A-2 (10 lines).
   - Do: derive one level-name constant from `_LEVEL_WORDS` (its keys, in order) and have
     `Base.mi_tuples` read it; move `_require_level_names` to `Core` beside `_require_dataframe`
     and call it from `Ion.set_data` (three levels when the frame has three, else M and C);
     `estimate_electrons` and `_read_example` build their columns through `Base.mi_tuples` or the
     constant; `swap_protons` reorders with `data.columns.names`, since `tools` cannot import
     `core`. Turn the 10 caller-input asserts (`Plasma.set_sc` ×2, `Plasma._set_aux` ×2,
     `Spacecraft.set_data` ×6) into `TypeError` (wrong type, or an index that is not a
     DatetimeIndex) or `ValueError` (wrong column count), each with a message. In its own commit,
     delete the unreachable `"+" not in s` assert in `Plasma._set_ions`
     (`Base._clean_species_for_setting` refuses `+` first) and route `Ion._set_species` through
     `_clean_species_for_setting`. Keep the three internal asserts in
     `ReferenceAbundances.get_element`, `Plasma.cs` and `Plasma.vdf_ratio`.
   - Tests, new first as `xfail(strict=True)`, one per contract: `set_sc` with a non-Spacecraft
     raises `TypeError`; `Spacecraft` with a non-DatetimeIndex raises `TypeError`; `Ion` with
     misnamed levels raises `ValueError` matching `"levels named"`. Guard the three
     `test_*_with_wrong_level_names_raises_value_error` tests and the reordered-levels aux test in
     `tests/core/test_plasma.py`, `tests/core/test_base_mi_tuples.py`, `tests/core/test_spacecraft.py`,
     `tests/core/test_ions.py`, `tests/core/test_core_verify_datetimeindex.py`,
     `tests/tools/test_tools.py`, `tests/test_examples.py`, the doctests. No test pins
     `AssertionError` at these sites.
2. **S13 / F98, F104, F112 + Q16, Q17. Fitfunctions and instabilities raise named errors.**
   - Anchors: `FitFunction.__init__` (`yerr_min`/`yerr_max` without `yerr`),
     `FitFunction._build_outside_mask` (`lower < upper`), `beta_ani_inst`,
     `StabilityCondition.set_beta_ani` (shape), `StabilityContours.set_beta` (type),
     `StabilityContours.plot_contours` (`ax` type), `FFPlot.set_observations` (two shape checks).
     Check: `git grep -n -E '^[[:space:]]*assert ' -- 'src/solarwindpy/fitfunctions/*.py' src/solarwindpy/instabilities`
     (12 lines at `d0b51fa4`).
   - Do: `InvalidParameterError` with a message for inverted `xoutside`/`youtside` and for
     `yerr_min`/`yerr_max` without `yerr`; `ValueError` for the `set_beta_ani` shape mismatch and
     for both `set_observations` checks; `TypeError` for `set_beta` and for a non-Axes `ax`;
     signature `beta_ani_inst(beta, a, b, c)`. Update every `Raises` docstring that names
     `AssertionError`. Leave the `growth_rate` check to package B. Keep the internal asserts in
     `TeXinfo._check_and_add_math_escapes`, `StabilityContours._calc_instability_contours` and
     `StabilityContours._add_table_legend`.
   - Tests, new first as `xfail(strict=True)`: inverted `xoutside`; `yerr_min` without `yerr`;
     the `set_beta_ani` shape check; the `set_beta` type check; a non-Axes `ax`; the
     `beta_ani_inst` signature. Update
     `tests/fitfunctions/test_plots.py::test_set_observations_refuses_a_y_fit_of_another_length`
     (`AssertionError` → `ValueError`). Guard `tests/fitfunctions/test_core.py` (including
     `test_xoutside_excludes_the_open_interval`), `tests/instabilities/test_verscharen2016.py`
     (including `test_beta_ani_inst_is_equation_5`, all keyword calls).

CHANGELOG drafts due: the exception changes, the `beta_ani_inst` signature, `set_observations`
(Changed).

### Package B: one source per formula and constant (wave 2)

Owns: `src/solarwindpy/core/quantities.py` (`_ELEMENTS`, `_species_tex`); in
`src/solarwindpy/core/base.py` a `Core._sound_speed` helper and an Alfvén-coefficient helper placed
beside `Core._species_total`; `src/solarwindpy/core/ions.py` (`Ion.cs`); in
`src/solarwindpy/core/plasma.py` `Plasma.cs` and `Plasma.ca`; in
`src/solarwindpy/core/alfvenic_turbulence.py` the `omega` and coefficient lines of
`AlfvenicTurbulence.set_data`; `src/solarwindpy/core/units_constants.py` (a private rotation-rate
constant and the citations); `src/solarwindpy/fitfunctions/gaussians.py`; in
`src/solarwindpy/instabilities/verscharen2016.py` `_plot_contour_kwargs`, `_instability_tests`,
`StabilityCondition.stability_map`, `StabilityCondition._calc_stability_bin`, the `growth_rate`
check in `StabilityContours.plot_contours`, `StabilityContours._add_table_legend`;
`src/solarwindpy/plotting/labels/{base,special,composition,epochs}.py`; tests
`tests/core/test_ions.py` (`IonTestBase::test_cs`), `tests/core/test_alfvenic_turbulence.py`,
`tests/plotting/labels/test_composition.py`, `tests/instabilities/test_verscharen2016.py` (one new
test placed directly after `test_growth_rate_draws_only_its_curves`).

1. **S14 / F61, F62, F65 + Q1, Q3, Q4, QN1. Each core formula has one home.**
   - Anchors: `Ion.cs`, `Plasma.cs`, `Plasma.ca`, `AlfvenicTurbulence.set_data`,
     `units_constants._misc_constants`, `Constants.polytropic_index`. Checks:
     `git grep -n -E "divide\(rho, axis=0\)" -- src/solarwindpy/core` (2 lines, `ions.py` and
     `plasma.py`; after, 1 line in `base.py`); `git grep -n -E "units\.b / \(" -- src/solarwindpy/core`
     (2; after 1); `git grep -n "2.865e-6" -- src` (1; none after); `git grep -n "should be 5/3" -- src`
     (1; none after).
   - One quantity or two: `Ion.cs` is one species' sound speed per pressure component;
     `Plasma.cs("p1", "a")` is the same quantity, scalar only, per species; `Plasma.cs("p1+a")` is
     the combined-fluid speed no `Ion` can compute. Share the formula line only; keep both methods.
   - Do: `Core._sound_speed(pth, rho, gamma)` returns sqrt(γ p / ρ) / `units.cs` for SI inputs,
     with γ a scalar or one value per column; `Ion.cs` passes γ per column from
     `polytropic_index` (par 3, per 2, scalar 5/3) and `Plasma.cs` passes the scalar γ. Cite CGL
     1956 in the `Ion.cs` docstring and on `_polytropic_index`. Delete the no-op `cs.name = "cs"`
     on the DataFrame and the `# should be 5/3` comment. One private `Core` helper for the
     Alfvén-unit coefficient, used by `Plasma.ca` and `AlfvenicTurbulence.set_data`. Replace
     `omega = 2.865e-6` with a private constant in `units_constants.py` equal to
     `2 * np.pi / (25.38 * 86400)` rad/s, citing Thompson (2006) §2.2; no public key in
     `Constants.misc`.
   - Tests: rewrite (update) `tests/core/test_ions.py::IonTestBase::test_cs` (it runs through
     `TestIonA`, `TestIonP1` and `TestIonP2`) from CGL: par = sqrt(3 p∥/ρ),
     per = sqrt(2 p⊥/ρ), scalar = sqrt(5/3 p/ρ), with the citation and an ON FAILURE line; rewrite
     (update) the `ROTATION_SPEED_KM_S` pin in
     `tests/core/test_alfvenic_turbulence.py::test_raffaella_version_converts_gse_to_rtn_with_hand_computed_values`
     from 2π/(25.38 d), hand-computed in its comment. Guard
     `tests/core/test_plasma.py::test_sound_speed_of_one_species_is_sqrt_gamma_p_over_rho` (its
     27.38612788 is derived as 30·√(5/6), not fragile),
     `::test_sound_speed_per_species_and_species_sum`, `TestPlasma::test_ca`,
     `tests/core/test_quantity_registry.py` (the `cs` and `ca` rows),
     `tests/core/test_missing_data.py::test_raffaella_polarity_and_field_are_nan_where_a_component_is_missing`.
2. **S24 / F134. Log-normal moments have one home.** `GaussianLn.normal_parameters` returns
   `dict(mean=mu, std=sigma)` from `tools.normal_parameters(self.popt["mu"], self.popt["sigma"])`;
   its docstring points there for the formula and the Fenton (1960) citation. The plan's old check
   `git grep -c 'np.exp(s\*\*2.0) - 1.0'` passes while the defect stands, because `GaussianLn`
   spells the variable `sigma`; use this check:
   `git grep -n -E "np.exp\((s|sigma)\*\*2.0\) - 1.0" -- src/solarwindpy` (2 lines; after, only
   `tools/__init__.py`). Tests: guard
   `tests/fitfunctions/test_gaussians.py::TestGaussianLn::test_normal_parameters_calculation`
   (exact equality holds) and `tests/tools/test_tools.py`.
3. **S10 / F87. One Gaussian kernel.** A private module function `_gaussian(u, mu, sigma, A)` in
   `gaussians.py`; `Gaussian`'s closure returns `_gaussian(x, mu, sigma, A)`,
   `GaussianNormalized`'s returns `_gaussian(x, mu, sigma, n / (np.sqrt(2 * np.pi) * sigma))`,
   `GaussianLn`'s returns `_gaussian(np.log(x), mu, sigma, A)`. The closures keep their own
   signatures, because `FitFunction._set_argnames` reads parameter names from them. Check:
   `git grep -n "arg = -0.5" -- src/solarwindpy/fitfunctions` (3; after 1). Tests: guard
   `tests/fitfunctions/test_gaussians.py`, `test_every_fit_function.py`,
   `test_docstring_inheritance.py`, `test_p0_contract.py`, `tests/test_available.py`.
4. **S22 / F132. One `new_line_for_units` option.** Move the property and setter to
   `solarwindpy.plotting.labels.base.Base` with the class default `_new_line_for_units = False`
   (the form of `_name` and `_publication_format`), delete the four copies (`TeXlabel`,
   `CountOther`, `MathFcn`, `AbsoluteValue`), and pass `new_line=self.new_line_for_units` to
   `format_with_units` in every label `__str__`, `epochs.py` included. In a separate commit, give
   `Probability` and `CountOther` one private parent holding the comparison scaffolding
   (`other_label`, `comparison`, `set_other_label`, `set_comparison`, `_build_tex`,
   `_build_path`, `build_label`) with the TeX prefix, path prefix and units as class attributes;
   do not name it `ComparisonLabel`, an existing class. Never merge the two classes: a percentage
   and a count are two quantities. Checks: `git grep -n "def set_new_line_for_units" -- src/solarwindpy/plotting/labels`
   (4; after 1); `git grep -n "def set_comparison" -- src/solarwindpy/plotting/labels` (2; after
   1). Tests: guard `tests/plotting/labels/test_labels_base.py`, `test_special.py`,
   `tests/plotting/test_integration.py`.
5. **S8 / F129. Composition species come from one table.** Name the element tuple in
   `core/quantities.py` as a private `_ELEMENTS` that `_species_tex` loops over;
   `composition.known_species = tuple(s for s in _ELEMENTS if s != "H")`, keeping today's order and
   the exclusion of H. Check: `git grep -n -E 'known_species = \("' -- src/solarwindpy/plotting/labels`
   (1; none after). Tests: fragile, rewrite as a relation
   `tests/plotting/labels/test_composition.py::test_known_species_list` (known species equal the
   core elements minus H); fragile, delete `::test_module_attributes` (a `hasattr` check, which
   TEST_PATTERNS forbids; the relation test asserts the public value). Guard
   `test_set_species_charge_known_species`, `test_set_species_charge_unknown_species`,
   `test_all_known_species_no_warning`, `test_known_species_completeness`,
   `tests/core/test_quantity_registry.py`.
6. **S20 / F106, F107, F108. The verscharen2016 tables are keyed once.** Derive the growth-rate set
   from `insta_params.index.unique("growth_rate")` (display order `sorted(..., reverse=True)`);
   build `_plot_contour_kwargs` from a per-instability (colour, marker) table and a per-rate
   linestyle table with the same 12 values; take `_add_table_legend`'s `types` from
   `_inst_type_idx`; key the stability bins by short private names mapped to the same integers,
   so `_calc_stability_bin` stops looking up display strings; order `_instability_tests` as
   `AIC, FMW, MM, OFI`. The `growth_rate` check in `plot_contours` raises `ValueError` naming the
   allowed set (this replaces its assert; package A leaves it). No threshold, colour, label string
   or bin integer changes. Checks: `git grep -n -F "[-2, -3, -4]" -- src/solarwindpy/instabilities`
   (2; none after); `git grep -n 'map_inverse\["Between' -- src/solarwindpy/instabilities` (2;
   none after). Tests: new first as `xfail(strict=True)`, an unknown `growth_rate` raises
   `ValueError`; guard every test in `tests/instabilities/test_verscharen2016.py`, including
   `test_fit_parameters_are_verscharen2016_table_1`,
   `test_stability_condition_classifies_by_published_thresholds`,
   `test_plot_contours_default_styles`, `test_stability_contours_figure_renders_to_png`.

CHANGELOG drafts due: `Ion.cs` par and per (Changed, physical result), the rotation rate (Changed,
physical result).

### Package D: solar_activity (wave 2)

Owns: `src/solarwindpy/solar_activity/base.py` (`IndicatorExtrema.calculate_extrema_bands`,
`IndicatorExtrema.cut_spec_by_interval`, the `from abc import` line, `ID._url_base`,
`ID._trans_url`, `DataLoader.convert_nans`, `ActivityIndicator.normalized`,
`ActivityIndicator.run_normalization`); `src/solarwindpy/solar_activity/icme/icmecat.py` (all but
the logger members C changed); `src/solarwindpy/solar_activity/icme/__init__.py`;
`src/solarwindpy/solar_activity/sunspot_number/sidc.py` (all but `SIDC.__init__`'s logger line);
`src/solarwindpy/solar_activity/plots.py` (new `plot_on_colorbar`, `__all__`, the
`SSNPlot._format_axis` docstring); `docs/source/usage.rst` (the "solar cycle on the colorbar"
prose and plot block only); tests `tests/solar_activity/sunspot_number/test_sidc.py`,
`tests/solar_activity/test_plots.py`, `tests/solar_activity/test_base.py` (the `CacheLoader` and
`Indicator` test subclasses only), `tests/solar_activity/icme/test_icmecat.py` (only if F162
changes `filter`'s warning).

1. **S18 / F146, F149, F152, F153, F166. Dead copies and stale text.** Delete the second
   `dt = pd.to_timedelta(dt)` in `IndicatorExtrema.calculate_extrema_bands`; give the bare
   `raise ValueError` in `IndicatorExtrema.cut_spec_by_interval` a message naming the cause
   (cycle intervals overlap or are out of order); reword the `# Vectorized containment check`
   comment in `ICMECAT.contains` to state what the loop does; delete the unreachable
   `NotImplementedError("Please specify how to build ...")` branch in `SIDCLoader.read_data`;
   bind `_Dtypes_Columns` once, as one class and one instance, without `defaults=`. Checks: AC D-1.
   Tests: guard the `test_cut_*` and band tests in `tests/solar_activity/test_base.py`, the
   `test_contains_*` tests, and `tests/solar_activity/sunspot_number/test_sidc_loader.py::test_read_data_refuses_a_series_with_no_column_layout`.
2. **S19 / F151, F152, F155, F156, F160. One home per fact in `sidc.py`.** Use
   `_m_dtypes_columns` and `_hm_dtypes_columns` for the m13 and hm13 layouts (the same files);
   one key table holding URL fragment, layout and date kind per key, read by `SIDC_ID._trans_url`
   and `SIDCLoader.read_data`; `SIDC.set_extrema` reads the extrema the loader built; one private
   per-cycle helper yielding `(k, series, before_max, after_max)`, called by
   `calculate_extrema_kind` and `calculate_edge`, which stay two methods (two outputs) and keep
   the half-max line unchanged; one code path in the moved `plot_on_colorbar` that picks the value
   and time axes from `vertical_cbar`. The `SSNExtrema()` count excludes doctest lines (a
   `>>> extrema = SSNExtrema()` line is a doctest, not a copy). Checks: AC D-2. Tests: guard
   `tests/solar_activity/sunspot_number/test_sidc_loader.py` (`test_read_data_*`,
   `test_load_data_assigns_each_measurement_to_its_containing_cycle`) and `test_sidc.py`
   (`test_edge_rises_to_the_cycle_maximum_and_falls_after`,
   `test_extremum_kind_follows_the_half_max_rule`, `test_extrema_is_the_real_shipped_table`,
   `test_every_measurement_lands_in_a_cycle`).
3. **T2 + Q14 / F159. Move `plot_on_colorbar` to `solar_activity.plots`.** In the form the author
   confirms for O1. Remove it and the matplotlib and `Guides` imports from `sidc.py`; update the
   `SSNPlot._format_axis` docstring and the usage.rst prose and plot block. Tests: update and move
   the four `test_plot_on_colorbar_*` tests from `tests/solar_activity/sunspot_number/test_sidc.py`
   to `tests/solar_activity/test_plots.py`; update the shared-scale test in `test_plots.py`; guard
   `tests/test_docs_ssn_snapshot.py` and `tests/test_docs_plot_blocks.py`.
4. **Q6 / F158. Remove `cut_spec_by_ssn_band`, `spec_by_ssn_band`, `ssn_band_intervals`.** Tests:
   delete the 7 `test_ssn_bands_*` tests in `tests/solar_activity/sunspot_number/test_sidc.py`
   (the methods they test are removed by ruling).
5. **S25 / F142, F144, F150. Base contracts predict their subclasses.** Replace the deprecated
   `abstractproperty` and `abstractstaticmethod` with `@property` over `@abstractmethod` (the
   form of `DataLoader.max_age`); make `DataLoader.convert_nans` an abstract instance method
   documenting in-place replacement, matching `SIDCLoader.convert_nans`; add `norm_by="max"` to
   `ActivityIndicator.run_normalization`'s signature and delete the
   `run_normalization.__doc__ = ...` statement in `sidc.py` (`inspect.getdoc` inherits). Checks:
   AC D-3. Tests: guard `tests/solar_activity/test_base.py::test_abstract_bases_cannot_be_instantiated_directly`,
   the four `test_convert_nans_*` tests,
   `test_sidc.py::test_sidc_run_normalization_documents_itself_with_the_base_docstring`; update
   the `CacheLoader` and `Indicator` test subclasses to the new contract.
6. **S26 / F162, F164, F167 + Q15. ICMECAT has one lookup and links its terms.** `filter` builds its
   result through `_filter_by_spacecraft`'s lookup (one private method that returns the catalog's
   spelling and warns on a miss) and a private constructor path instead of `object.__new__`;
   rename `_intervals` to `_estimated_intervals`; shorten the package docstring in
   `icme/__init__.py` to point at the `ICMECAT` class example; delete `RULES_OF_THE_ROAD` and
   state in the class and package docstrings: follow the ICMECAT rules of the road at the
   HELIO4CAST site (https://helioforecast.space/icmecat). Checks: AC D-4. Tests: guard the
   `test_filter_*` tests, `test_init_with_spacecraft_filters`, the `test_contains_*` tests, the
   repr tests, `tests/solar_activity/icme/test_icmecat_versions.py`, `tests/test_public_imports.py`,
   `conda run -n solarwindpy pytest --doctest-modules src/solarwindpy/solar_activity -q`.

CHANGELOG drafts due: the `plot_on_colorbar` move (Changed), the Q6 and Q15 removals (Removed),
the `run_normalization` and `convert_nans` signatures (Changed).

### Package E-plot: plotting leftovers, clip, keyword-only constructors (wave 2)

Owns: in `src/solarwindpy/fitfunctions/core.py` the `FitFunction.residuals` docstring only; in
`src/solarwindpy/fitfunctions/plots.py` `FFPlot.set_log`, `FFPlot._set_labels` and the import from
`..plotting.base`; `src/solarwindpy/plotting/base.py` (`Base._set_labels`, a new private helper
placed after the `ScatterLabels` definition, the clip members and docstrings);
`src/solarwindpy/plotting/binned.py`; `src/solarwindpy/plotting/binning.py` (the `MemoryError`
fallback in `FixedGrid`); `src/solarwindpy/plotting/tools.py` (`_STYLE_PATH`, `_use_style`);
`src/solarwindpy/plotting/{hist1d,hist2d,scatter,spiral}.py` (constructor signatures and clip
docstrings); `src/solarwindpy/instabilities/plots.py` (only if `BetaRPlot.__init__` needs a
change to forward keyword-only settings); `docs/source/usage.rst` (the clip-percentile sentence
only); tests `tests/plotting/test_{agg_plot,base,binned_data,data_path_defects,hist1d,hist2d_defects,hist2d_plotting,review_findings,scatter,spiral,architecture}.py`,
`tests/test_source_plotting_defects.py`.

1. **S9 / F95.** Delete the "Addresses TODO" Notes section of the `FitFunction.residuals`
   docstring; the `use_all` parameter entry holds the fact. Check:
   `git grep -n "set_extrema" -- src/solarwindpy/fitfunctions` (1; none after). Tests: guard the
   `residuals` doctest and `tests/test_docstrings.py`.
2. **S21 / F115.** Delete the unused `_STYLE_PATH` and `_use_style` in `plotting/tools.py`;
   `plotting/__init__.py` owns the style path. Check:
   `git grep -n -E '_STYLE_PATH =|_use_style' -- src` (3 lines; after, 1 in `plotting/__init__.py`).
   Tests: guard `tests/plotting/test_integration.py`, `tests/plotting/test_tools.py`.
3. **S21 / F118 + Q5. One clip code path with user-settable cuts.** Implement ruling 5 in
   `plotting/binned.py`: one function computes the lower and upper quantile for a clip setting,
   used by `_clip_to_quantiles` (and so `Base.clip_data`) and by `FixedGrid`'s `MemoryError`
   fallback with the default cuts. `_store_clip` validates pairs at construction. Rewrite every
   docstring, the usage.rst sentence and the `FixedGrid` warning text to state the 0.05%/99.95%
   default once each. Keep `"lower"`, `"upper"` and `"both"` per O2's answer. Checks: AC E-3.
   Tests: new first as `xfail(strict=True)`: a pair `(0.01, True)` clips the lower tail at 1% and
   the upper at the default; `(0.6, 0.9)` raises `ValueError`; `(False, True)` equals `"u"`.
   Update every clip test that pins or derives the 0.01%/99.99% default, recomputing each hand
   value at 0.05%/99.95% in its comment: `tests/plotting/test_agg_plot.py`, `test_base.py`,
   `test_binned_data.py`, `test_data_path_defects.py`, `test_hist1d.py`,
   `test_hist2d_defects.py`, `test_hist2d_plotting.py`, `test_review_findings.py`,
   `test_scatter.py`, `test_spiral.py`, `tests/test_source_plotting_defects.py`. Guard
   `test_agg_plot.py`'s two out-of-memory fallback tests (their 0.05th percentile is unchanged)
   and `tests/plotting/test_review_findings.py::TestClipSetting::test_constructors_reject_an_unknown_clip_string`.
4. **S28 / F100. The fit plotter shares plotting's vocabulary.** `FFPlot.set_log(self, x=None, y=None)`
   with None keeping the current value and `bool` coercion, as `plotting.base.Base.set_log`; one
   private module helper in `plotting/base.py` (for example `_updated_labels(labels, **kwargs)`)
   called by `Base._set_labels` and `FFPlot._set_labels`. Leave `SpiralMesh`'s keyword check.
   Checks: AC E-4. Tests: guard `tests/fitfunctions/test_plots.py::test_set_log_changes_only_the_axes_it_is_given`,
   `::test_set_labels_keeps_the_labels_it_is_not_given`,
   `::test_set_labels_refuses_an_unknown_label_naming_it`, the `tests/plotting/test_base.py`
   label tests, `tests/instabilities/test_plots.py`.
5. **Q11 / F125. Keyword-only settings after the data variables.** Put `*` after the data variables
   in `Hist1D.__init__` (x, y), `Hist2D.__init__` and `SpiralPlot2D.__init__` (x, y, z) and
   `Scatter.__init__` (x, y, z, size, alpha); keep every setting's name. Check that
   `BetaRPlot.__init__(beta, R, species, **kwargs)` still forwards its settings. Today
   `Scatter(x, y, None, True)` silently stores `True` as every point's size while
   `Hist2D(x, y, None, True)` sets a log x axis. Checks: AC E-5. Tests: update
   `tests/plotting/test_architecture.py::test_constructors_take_variables_then_log_axes_then_axnorm`
   to assert that every parameter after the variables is `KEYWORD_ONLY`; update
   `tests/plotting/test_hist2d_plotting.py::TestPlotSignatures::test_positional_parameters_are_in_the_documented_order`;
   guard `test_scatter.py`, `test_spiral.py`, `test_hist1d.py`.

CHANGELOG drafts due: the clip default and pair form (Changed), keyword-only constructors (Changed,
breaking), `FFPlot.set_log` (Changed).

### Package E-core: Plasma helpers and docstrings (wave 3)

Owns: in `src/solarwindpy/core/plasma.py` `Plasma._SPECIES_COMBINE`, `Plasma._gather`, `Plasma.Wk`,
`Plasma.nuc`, `Plasma.beta`, `Plasma.R`, `Plasma.save`, `Plasma.load_from_file`, new private
class attributes for the HDF keys, a private species-label helper, and the module-top comment;
`src/solarwindpy/examples/__init__.py` (`load_plasma`); `src/solarwindpy/core/abundances.py`;
`src/solarwindpy/core/alfvenic_turbulence.py` (module-top comment, the `cos_colat` local);
`src/solarwindpy/core/spacecraft.py` (module-top comment); `src/solarwindpy/core/units_constants.py`
(module docstring and module-top comment); in `src/solarwindpy/instabilities/verscharen2016.py`
the TODO above `StabilityCondition.norm`; `tests/core/test_plasma_io.py` (one optional new test).

1. **S15 / F68, F69, F70, F71, F72. One gather helper; no dead code in Plasma.** `Wk` gathers
   through `_gather` with `"Wk": "sum"` in `_SPECIES_COMBINE` (its missing-data rule unchanged);
   `nuc` gathers through `_gather("w", sa, sb)` and keeps its strict `sqrt(w_a² + w_b²)`
   (`skipna=False`) locally, because W_ab is part of the collision formula, not a species total;
   delete the two dead `include_dynamic` blocks in `beta` and `R`; `save` validates all three
   modifier functions before writing anything, with one message (no "You passes"); the HDF key
   defaults (`"FC"`, `"SC"`, `"FC_AUX"`) live once as private class attributes read by `save` and
   `load_from_file`; one private helper in `plasma.py` returns the non-empty S labels, and
   `load_plasma` sorts its result while `load_from_file` keeps file order; one private key-to-level
   method serves `ReferenceAbundances.get_element` and `get_comment`. Checks: AC E-6. Tests: guard
   the `Wk`, `nuc`, `beta` and anisotropy tests in `tests/core/test_plasma.py`, all of
   `tests/core/test_plasma_io.py` (notably `test_save_rejects_a_modifier_that_is_not_a_function`),
   the two `Unrecognized key type` tests in `tests/core/test_abundances.py`,
   `tests/test_examples.py`. Optional new test, `xfail(strict=True)` first: a rejected modifier
   writes no file.
2. **S16 / F53, F77, F84, F111. Comments and docstrings predict their content.** Delete the four
   module-top "We rely on views via DataFrame.xs" comments: CLAUDE.md § "Data model" holds the
   rule and `tests/core/test_seams.py::test_component_selection_shares_the_parent_data` guards
   it. Rename the local `cos_colat` to `cos_lat` (it is √(x²+y²)/√(x²+y²+z²), the cosine of
   latitude). Rewrite the `units_constants` module docstring to state what holds: `Constants`
   holds physical constants and per-species values, `Units` holds per-quantity display-to-SI
   factors read from `quantities`. Delete the `color_norm` TODO above `StabilityCondition.norm`.
   Checks: AC E-7. Tests: guard the doctests, the docs build,
   `test_raffaella_version_converts_gse_to_rtn_with_hand_computed_values`, `tests/test_docstrings.py`.

CHANGELOG draft due: `Plasma.save` refuses an invalid modifier before writing (Fixed).

### Package G: test layout (wave 3, after E-core merges)

Owns: everything under `tests/` that the items below move, split, merge or rename, plus
`tests/conftest.py`, `tests/solar_activity/icme/conftest.py`, `tests/drift/test_drift_icmecat.py`
and the `markers` key of `pyproject.toml`. New files: `tests/core/_fixtures.py`,
`tests/core/test_vector.py`, `tests/core/test_tensor.py`, `tests/examples/__init__.py`,
`tests/fitfunctions/_scan.py`, `tests/plotting/test_data_path.py`. Every move is a `git mv` so
history and Spent-When lines travel; every new file gets its declaration at write time.

Before starting, record `conda run -n solarwindpy pytest --collect-only -q | grep collected`
(`N tests collected in ...`); after G,
the collected count equals that number minus the tests G deletes (item 2's duplicate and item 4's
nine sunspot init tests) plus the parametrized cases item 4 adds.

1. **S32 / F170, F174, F187, F189, F191 + Q10. tests/core and examples mirror their modules.**
   Split `tests/core/test_quantities.py` (it tests `vector.py` and `tensor.py`, while
   `core/quantities.py` is now the quantity registry) into `test_vector.py` and `test_tensor.py`;
   move the fixture classes (`SyntheticData`, `SWEData`, `AlphaTest`, `P1Test`, `P2Test`,
   `AlphaP1Test`, `AlphaP2Test`, `P1P2Test`, `AlphaP1P2Test`) and `_species_masked_plasma` into
   `tests/core/_fixtures.py` and repoint the importers (`test_alfvenic_turbulence`, `test_ions`,
   `test_plasma`, `test_plasma_io`, `test_spacecraft`, `test_plasma_species_combine`,
   `test_quantity_registry`); `_read_example` stays as the fixtures' loader (ruling 10); rename
   `test_core_verify_datetimeindex.py` to `test_base_verify_datetimeindex.py`; move
   `tests/test_examples.py` to `tests/examples/test_examples.py` and its two Plasma-logging tests
   into `tests/core/test_plasma.py`; move `tests/test_contracts_class.py` to `tests/core/`.
   Checks: AC G-1. Tests: all guards, moved with ids unchanged except the path.
2. **S33 / F177, F179, F190. fitfunctions tests live under tests/fitfunctions.** Move
   `tests/test_available.py` to `tests/fitfunctions/test_init.py`; move
   `test_scan_finds_fit_functions` and `test_every_fit_function_is_declared_public_in_its_module`
   from `tests/test_fitfunctions_public_names.py` into `tests/fitfunctions/test_every_fit_function.py`;
   delete `test_no_fit_function_is_reexported_by_the_package` (duplicate:
   `tests/test_public_imports.py::test_no_package_binds_a_solarwindpy_object_it_does_not_define[solarwindpy.fitfunctions]`
   covers it); extract the three identical scan helpers into `tests/fitfunctions/_scan.py`; fold
   `test_trend_fit_properties.py` into `test_trend_fits.py`. Leave `test_trend_fits_advanced.py`
   and `test_trend_results.py`. Keep the package's `_fit_function_classes` walk separate from the
   test scan: `test_available` checks one against the other. Checks: AC G-2. Tests: delete the
   duplicate; all others guard (moved).
3. **S34 / F180, F181, F182, F188. Plotting test files are named for what they test.** Move the
   root `tests/test_source_plotting_defects.py` tests into `tests/plotting/test_scatter.py`,
   `tests/plotting/labels/test_labels_base.py` and `tests/plotting/labels/test_composition.py`;
   split `test_histograms.py` into `test_hist1d.py` and the Hist2D file; rename
   `test_hist2d_plotting.py` → `test_hist2d.py`, `test_agg_plot.py` → `test_base_binned_plot.py`,
   `test_agg_full_grid.py` → `test_hist2d_agg_grid.py`, `test_hist2d_pandas_compat.py` →
   `test_hist2d_pandas.py`, `test_hist2d_defects.py` → `test_hist2d_projection.py`; fold
   `test_hist1d_defects.py` into `test_hist1d.py`; merge `test_review_findings.py` and
   `test_data_path_defects.py` into `test_data_path.py`; rename `labels/test_labels_base.py` →
   `labels/test_base.py`. Checks: AC G-3. Tests: all guards, moved.
4. **S35 / F183, F184, F193. One placement rule for solar_activity and root tests.** Replace the
   nine tests in `tests/solar_activity/sunspot_number/test_init.py` with the parametrized form of
   `tests/solar_activity/test_init.py::test_every_exported_name_resolves`; move
   `TestModuleConstants` from `tests/solar_activity/icme/test_icmecat_smoke.py` into
   `test_icmecat.py`; correct the `tests/conftest.py` docstring and the "No special module path
   configuration needed" comment (`pyproject.toml` sets `pythonpath = ["src"]`); delete the unused
   `debug_print` fixture and the `--debug-prints` option. A root test file is one that imports
   more than one subpackage, imports no package code, or tests `docs/`. Checks: AC G-4. Tests:
   delete the nine sunspot init tests (the parent form and `tests/test_public_imports.py` cover
   their contract); guard `TestModuleConstants` (moved) and the drift gate.
5. **T4 / F185. Live ICMECAT checks live in tests/drift.** Move the 8 live tests
   (`TestLiveDownload`, `TestMultipleSpacecraft`) from
   `tests/solar_activity/icme/test_icmecat_integration.py` into `tests/drift/test_drift_icmecat.py`
   under its `pytestmark = pytest.mark.drift`, keeping `slow` where set; delete the emptied file;
   remove the `integration` marker from `pyproject.toml`, from the gate set and skip reason in
   `tests/conftest.py::pytest_collection_modifyitems` and the `--run-drift` help text, and from
   the exemption in `tests/solar_activity/icme/conftest.py::_no_network`. The weekly
   `drift-detection` job in `doctest_validation.yml` then runs them; today no CI job does. Keep
   `test_icmecat_smoke.py`'s content (offline) and `test_icmecat_versions.py` in the code mirror.
   Checks: AC G-5. Tests: update (moved and re-marked, assertions unchanged) the 8 live tests;
   guard the 17 offline ICMECAT tests, `tests/drift/test_drift_controls.py`, and the default
   suite's skipped count.

No CHANGELOG entry (tests only).

## Read First

1. `/Users/blalterman/observatories/code/SolarWindPy/GOVERNANCE.md`: the purpose, intent and
   objectives § Governing Property and § Purpose derive from; § Intent "Defined once, layered" is
   the property every item serves.
2. `/Users/blalterman/observatories/code/SolarWindPy/CLAUDE.md`: § "Environment" (the conda env,
   `PYTHONPATH=$PWD/src` in another worktree), § "Checks", § "Data model" (`.xs` shares data),
   § "Conventions" (test-first classification, Conventional Commits), § "Gotchas".
3. `/Users/blalterman/observatories/code/SolarWindPy/.claude/docs/TEST_PATTERNS.md`: what a test
   asserts, fragile pins, the `hasattr` prohibition, § "Structure and layering".
4. `/Users/blalterman/observatories/code/SolarWindPy/.claude/docs/RELEASING.md`: § "5. Dry-Run the
   Publish Workflow", which § Verification runs after wave 1.
5. The decision traces, if they still exist: `/tmp/swp-traces/RULINGS.md`, `AB.md`, `CDE.md`,
   `FGH.md`, `AUTH.md`, `GOV.md`, `EXPLAIN.md`, `OVERLAP.md`, `BRIEF.md`. They hold the
   measurements behind each item; everything the executor needs from them is in § Scope. `/tmp`
   is not durable, so their absence is not a divergence.

## State Verification

Run from `/Users/blalterman/observatories/code/SolarWindPy`. Each line re-derives a precondition;
a mismatch is a divergence (§ Entry Protocol step 4).

```bash
git rev-parse --abbrev-ref HEAD                      # master
git status --porcelain                               # empty
git merge-base --is-ancestor d0b51fa4 HEAD; echo $?  # 0: this dispatch was written against d0b51fa4
git config core.bare                                 # false
conda run -n solarwindpy python -c "import solarwindpy, pandas; print(solarwindpy.__file__, pandas.__version__)"
                                                     # .../SolarWindPy/src/solarwindpy/__init__.py 3.x
conda run -n solarwindpy lint-imports | tail -1      # Contracts: 2 kept, 0 broken.
test -f GOVERNANCE.md && grep -c '^@GOVERNANCE.md' CLAUDE.md   # 1
gh auth status >/dev/null 2>&1; echo $?              # 0 (needed only for the dry run)
```

The defects are still present on HEAD (each count is the positive control for an absence check in
§ Acceptance Criteria; a smaller count means another change touched the item, which is a
divergence to report before starting):

```bash
git grep -c "_select(" -- src tests | wc -l                     # 7   (package I)
git grep -c "def _init_logger" -- src | wc -l                   # 7   (C)
git grep -n rglob -- tests ':!tests/solar_activity/test_cache.py' | wc -l   # 6 (F)
git ls-files .claude | wc -l                                    # 20  (H)
git grep -n -E '^[[:space:]]*assert ' -- 'src/solarwindpy/core/*.py' | wc -l   # 14 (A)
git grep -n -E "divide\(rho, axis=0\)" -- src/solarwindpy/core | wc -l          # 2  (B)
git grep -n -E "cut_spec_by_ssn_band|spec_by_ssn_band|ssn_band_intervals" -- src tests docs/source | wc -l   # 25 (D)
git grep -l -E "0\.0001|0\.9999[^0-9]|0\.01st|99\.99(th|%)" -- src/solarwindpy/plotting tests/plotting tests/test_source_plotting_defects.py docs/source | wc -l   # 18 (E-plot)
git grep -n include_dynamic -- src/solarwindpy/core/plasma.py | wc -l           # 4  (E-core)
git grep -n -E "from \. import test_base|from tests\.core\.test_" -- tests | wc -l   # 8 (G)
```

## Operational Constraints

- **Worktrees.** Each package runs in a fresh subagent launched with `isolation: "worktree"`; its
  handback names its branch and worktree path. Where that option is unavailable, the orchestrator
  creates the worktree by hand from master:
  `git worktree add ../SolarWindPy-wt-<p> -b cleanup/<p> master` (`<p>` is the package letter in
  lower case, `e-plot` and `e-core` for E). After a package merges, the orchestrator removes it:
  `git worktree remove ../SolarWindPy-wt-<p>` and `git branch -d cleanup/<p>`.
- **The env in a worktree.** `pytest` puts the worktree's `src/` first through `pyproject.toml`;
  `python -c` and `lint-imports` do not, so prefix them with `PYTHONPATH=$PWD/src` in a worktree.
  Run every Python tool through `conda run -n solarwindpy`.
- **Commits.** Every commit runs the full suite through the pre-commit hook (about two minutes)
  and the commit-msg hook (Conventional Commits). Stage explicit paths, never `git add -A`. After
  every commit made in a worktree, run `git -C /Users/blalterman/observatories/code/SolarWindPy config core.bare`
  and expect `false`; on `true`, stop and report (the restore is the author's to run).
- **Tests that run git.** A test that writes with git (`git init`, commit, tag) deletes every
  `GIT_*` variable first and sets `GIT_CONFIG_GLOBAL=/dev/null` and `GIT_CONFIG_NOSYSTEM=1`.
  Read-only `git ls-files` (package F's helper) may inherit the hook's environment.
- **Declarations.** Every new file gets its Spent-When declaration when it is written, rendered by
  the issuer, never typed:
  ```bash
  SESSION=$(ls -d ~/.claude/plugins/cache/blalterman-tools/session/*/ | sort -V | tail -1)
  python3 "$SESSION/tools/spent_when.py" --emit <path> --member '<member>' --supersedes none
  ```
  Tests and docs take the inline form it prints. A new module under `src/solarwindpy/` takes a
  sidecar: add `--sidecar` to the command, which prints `# write this to <path>.spent-when` and
  the two lines to write there (the form of `src/solarwindpy/plotting/scales.py.spent-when`);
  without the flag it prints an inline header, which a shipped module does not carry. New test files use
  `PERMANENT(the repository stops maintaining a test suite)`. A `git mv` keeps the moved file's
  declaration; re-render it only where its reversal names the old path.
- **CHANGELOG.md** is written by the orchestrator only, after each merge, from the package's
  drafted entry, as its own commit `docs(changelog): <package> <summary>`.
- **No push** without the author's explicit OK, including after the dry-run question.

## Acceptance Criteria

Each absence check carries its positive control: the same command against `d0b51fa4`, the commit
this dispatch was written against, which shows the defect. These are more than a handful of
items: seed a `/session:track` ledger from the IDs below and check them off there; this section
stays the authority on done.

**Package I**
- [ ] I-1 `Core._select` is gone: `git grep -c "_select(" -- src tests` → no output, exit 1;
      control `git grep -c "_select(" d0b51fa4 -- src tests | wc -l` → 7
- [ ] I-2 no `beta_ani` module name remains: `git grep -n -w beta_ani -- src tests docs/source` →
      no output, exit 1; control `git grep -n -w beta_ani d0b51fa4 -- src tests docs/source | wc -l` → 12
- [ ] I-3 no `labels.datetime` import remains:
      `git grep -n -E "labels\.datetime|labels import .*datetime|^from \. import datetime" -- src tests docs/source`
      → no output, exit 1; control (same pattern with `d0b51fa4` before `--`) `| wc -l` → 10
- [ ] I-4 the renamed modules import:
      `conda run -n solarwindpy python -c "import solarwindpy.instabilities.plots, solarwindpy.plotting.labels.epochs; print('ok')"`
      → `ok`

**Package C**
- [ ] C-1 one logger helper: `git grep -l "def logger" -- src` → `src/solarwindpy/tools/__init__.py`
      only (control at `d0b51fa4` `| wc -l` → 6);
      `git grep -c "def _init_logger" -- src` → no output, exit 1; control
      `git grep -c "def _init_logger" d0b51fa4 -- src | wc -l` → 7
- [ ] C-2 no handler, level or root logger in the library:
      `git grep -n -E "addHandler|StreamHandler|setLevel|main\.solarwindpy|getLogger\(\)" -- src`
      → no output, exit 1; control (same pattern at `d0b51fa4`) `| wc -l` → 6
- [ ] C-3 `tools` is below `core`: `grep -c '"core | tools"' pyproject.toml` → `0`; control
      `git show d0b51fa4:pyproject.toml | grep -c '"core | tools"'` → `1`;
      `conda run -n solarwindpy lint-imports | tail -1` → `Contracts: 2 kept, 0 broken.`
- [ ] C-4 every class logs under its own module:
      `conda run -n solarwindpy pytest -q tests/tools/test_tools.py -k "own_module or no_handler"`
      → passed, 0 failed, at least 2 selected
- [ ] C-5 `swap_protons` prints nothing by default:
      `conda run -n solarwindpy python -c "import pandas as pd; from solarwindpy.tools import swap_protons; c=pd.MultiIndex.from_tuples([('n','','p1'),('n','','p2')],names=list('MCS')); swap_protons(pd.DataFrame([[1.,2.]],columns=c))" 2>&1 | grep -c .`
      → `0`; control: the same command at `d0b51fa4` printed 4 lines (the statistics block)
- [ ] C-6 stale docstring claims gone: `git grep -n -E "independent sibling|not yet organized" -- src`
      → no output, exit 1; control (same pattern at `d0b51fa4`) `| wc -l` → 2

**Package F**
- [ ] F-1 scans read tracked files: `git grep -n rglob -- tests ':!tests/solar_activity/test_cache.py'`
      → no output, exit 1; control (same at `d0b51fa4`) `| wc -l` → 6; `git grep -l "_tracked" -- tests | wc -l` → 9
      (the helper and its 8 users; control at `d0b51fa4` → 2, the two former copies)
- [ ] F-2 no inert pandas option: `git grep -n chained_assignment -- tests` → no output, exit 1;
      control (same at `d0b51fa4`) `| wc -l` → 6;
      `conda run -n solarwindpy pytest -q tests/core tests/test_examples.py -W error::pandas.errors.Pandas4Warning`
      → passed, 0 errors

**Package H**
- [ ] H-1 retired files gone: `git ls-files .claude | wc -l` → `6`; control
      `git ls-tree -r --name-only d0b51fa4 -- .claude | wc -l` → `20`;
      `git ls-files scripts/analyze_imports_fixed.py scripts/test_dynamic_imports.py scripts/docstring_coverage.py docs/conda-feedstock-automation.md docs/RELEASE_PROCESS.md setup.py | wc -l`
      → `0`; control (`git ls-tree -r --name-only d0b51fa4 --` with the same paths) → `6`;
      `conda run -n solarwindpy python -c "from setuptools_scm import get_version; print(get_version())"`
      → a version string such as `0.6.1.devN+g<sha>`, with no error
- [ ] H-2 no rule or doc names retired tooling:
      `grep -c -E "setup\.py|test-runner|coverage-monitor|create-compaction|generate-test" .claude/settings.json`
      → `0` (control at `d0b51fa4` via `git show d0b51fa4:.claude/settings.json | grep -c ...` → `12`);
      `git grep -n -E "DEVELOPMENT\.md|MAINTENANCE\.md|test-runner" -- .claude CLAUDE.md` → no
      output, exit 1 (control at `d0b51fa4` `| wc -l` → 29);
      `git grep -c "claude/templates" -- .pre-commit-config.yaml setup.cfg` → no output, exit 1
- [ ] H-3 the hook gates and has one floor:
      `grep -c -E "physics_files|core_files|module_path" .claude/hooks/pre-commit-tests.sh` → `0`
      (control at `d0b51fa4` → `10`); `grep -o -E "(≥|=)9[0-9]" .claude/hooks/pre-commit-tests.sh | tr -d '≥=' | sort -u`
      → one number, two under the measured TOTAL; `git grep -n -E "≥ ?9[0-9]%" -- .claude/docs`
      → no output, exit 1
- [ ] H-4 one package-data home: `grep -c csv MANIFEST.in` → `0`; `grep -c pip-tools pyproject.toml`
      → `0`; `git ls-files src/solarwindpy/examples/data | wc -l` → `3`;
      `head -1 src/solarwindpy/examples/data/example_spacecraft.csv | grep -c pos_HCI` → `0`;
      `conda run -n solarwindpy pytest -q tests/test_release_artifacts.py tests/test_examples.py`
      → passed, 0 failed
- [ ] H-5 the env spec and versions: `grep -n -E "^- (python[<>=]|nodefaults)" solarwindpy.yml` →
      two lines, `- nodefaults` and `- python>=3.12,<3.16` (control at `d0b51fa4` → no output);
      `grep -c "python=3.12" CLAUDE.md` → `0`; `grep -c "3.15" tox.ini .github/workflows/publish.yml pyproject.toml`
      → each ≥ 1; `conda run -n solarwindpy pytest -q tests/test_declared_versions.py` → passed
- [ ] H-6 weekly matrix and per-commit layering check:
      `grep -n -A1 "schedule:" .github/workflows/publish.yml` → a `cron:` line;
      `grep -c "lint-imports" .github/workflows/ci-master.yml` → `1`

**Package A**
- [ ] A-1 core asserts are internal only:
      `git grep -n -E '^[[:space:]]*assert ' -- 'src/solarwindpy/core/*.py'` → 3 lines, inside
      `ReferenceAbundances.get_element`, `Plasma.cs` and `Plasma.vdf_ratio` (control at `d0b51fa4`
      `| wc -l` → 14). Write `[[:space:]]`, not `\s`: `git grep -E` matches nothing with `\s`.
- [ ] A-2 level names have one home:
      `git grep -n -E '"M", ?"C", ?"S"' -- 'src/solarwindpy/*.py' | grep -v -E '>>>|``|labeled by|labelled|Build a Plasma|levels must|level=|column levels' | wc -l`
      → `1` or `0` (control at `d0b51fa4` → 10);
      `git grep -n -E "def _require_level_names|columns.names ==|columns.names !=" -- src/solarwindpy/core`
      → 1 line, in `base.py`
- [ ] A-3 named errors under `-O`:
      `conda run -n solarwindpy python -O -c 'import solarwindpy as swp; swp.examples.load_plasma().set_sc("not a spacecraft")' 2>&1 | grep Error`
      → a `TypeError: ...` line (at `d0b51fa4`: `AttributeError: 'str' object has no attribute 'data'`);
      `conda run -n solarwindpy python -O -c "import numpy as np; from solarwindpy.fitfunctions.lines import Line; Line(np.arange(5.),np.arange(5.),xoutside=(3,1))" 2>&1 | grep Error | tail -1`
      → an `InvalidParameterError: ...` line with a message
- [ ] A-4 fitfunctions and instabilities asserts:
      `git grep -n -E '^[[:space:]]*assert ' -- 'src/solarwindpy/fitfunctions/*.py' src/solarwindpy/instabilities | wc -l`
      → `3` (`tex_info.py` once, `_calc_instability_contours` and `_add_table_legend`; control at
      `d0b51fa4` → 12);
      `conda run -n solarwindpy python -c "import inspect; from solarwindpy.instabilities.verscharen2016 import beta_ani_inst as f; print(inspect.signature(f))"`
      → `(beta, a, b, c)`

**Package B**
- [ ] B-1 one sound-speed formula and the CGL values:
      `git grep -n -E "divide\(rho, axis=0\)" -- src/solarwindpy/core` → 1 line, in `base.py`
      (control at `d0b51fa4` → 2 lines);
      `conda run -n solarwindpy python -c "import solarwindpy as swp; print(swp.examples.load_plasma().p1.cs.iloc[0].round(2).to_dict())"`
      → `{'par': 12.25, 'per': 7.0, 'scalar': 7.42}` (at `d0b51fa4`: par 9.13, per 6.39);
      `git grep -n "10.1098/rspa.1956.0116" -- src/solarwindpy/core` → ≥ 1 line (if the publisher
      record gives another DOI, that is a divergence to report before writing it)
- [ ] B-2 the combined-fluid speed is unchanged:
      `conda run -n solarwindpy python -c "import numpy as np, solarwindpy as swp; p=swp.examples.load_plasma(); u=p.units; e=np.sqrt(5/3*p.pth('p1+a').xs('scalar',axis=1)*u.pth/(p.rho('p1+a')*u.rho))/u.cs; print(np.allclose(p.cs('p1+a'), e, equal_nan=True))"`
      → `True`
- [ ] B-3 constants and coefficient: `git grep -n "2.865e-6" -- src` → no output, exit 1 (control at
      `d0b51fa4` → 1 line); `git grep -n "10.1051/0004-6361:20054262" -- src/solarwindpy/core` → ≥ 1;
      `git grep -n -E "units\.b / \(" -- src/solarwindpy/core | wc -l` → `1`;
      `git grep -n "should be 5/3" -- src` → no output, exit 1
- [ ] B-4 fitfunction formulas: `git grep -n -E "np.exp\((s|sigma)\*\*2.0\) - 1.0" -- src/solarwindpy`
      → 1 line, in `tools/__init__.py` (control at `d0b51fa4` → 2);
      `git grep -n "arg = -0.5" -- src/solarwindpy/fitfunctions | wc -l` → `1` (control → 3)
- [ ] B-5 labels: `git grep -n "def set_new_line_for_units" -- src/solarwindpy/plotting/labels | wc -l`
      → `1` (control → 4); `git grep -n "def set_comparison" -- src/solarwindpy/plotting/labels | wc -l`
      → `1`; `git grep -n -E 'known_species = \("' -- src/solarwindpy/plotting/labels` → no
      output, exit 1;
      `conda run -n solarwindpy python -c 'from solarwindpy.plotting.labels import composition as c; print(c.known_species)'`
      → `('C', 'Fe', 'He', 'Mg', 'Ne', 'N', 'O', 'Si', 'S')`
- [ ] B-6 verscharen2016 tables: `git grep -n -F "[-2, -3, -4]" -- src/solarwindpy/instabilities`
      → no output, exit 1 (control → 2); `git grep -n 'map_inverse\["Between' -- src/solarwindpy/instabilities`
      → no output, exit 1;
      `conda run -n solarwindpy python -c "from solarwindpy.instabilities.verscharen2016 import _instability_tests as t, _inst_type_idx as i; print(t._fields, list(i))"`
      → `('AIC', 'FMW', 'MM', 'OFI') ['AIC', 'FMW', 'MM', 'OFI']`

**Package D**
- [ ] D-1 dead copies gone (with `b=src/solarwindpy/solar_activity/base.py`,
      `s=src/solarwindpy/solar_activity/sunspot_number/sidc.py`):
      `grep -c 'dt = pd.to_timedelta(dt)' $b` → `1` (control → 2);
      `grep -c 'raise ValueError$' $b` → `0`;
      `grep -c 'Vectorized containment' src/solarwindpy/solar_activity/icme/icmecat.py` → `0`;
      `grep -c -E 'Please specify how to build|defaults=\(None,\)' $s` → `0` (control → 2)
- [ ] D-2 one home per fact in `sidc.py` (same `s`): `grep -c '_dtypes_columns = ' $s` → `5` (control 7);
      `grep -v '>>>' $s | grep -c 'SSNExtrema()'` → `1` (control 2); `grep -c 'groupby("cycle")' $s`
      → `1`; `grep -c '(7, 3, 2, 3, 2, 3, 2, 3)' $s` → `1`; `grep -c 'def plot_on_colorbar' $s` → `0`;
      `git grep -l -E "^import matplotlib|^from matplotlib" -- src/solarwindpy/solar_activity` →
      only `src/solarwindpy/solar_activity/plots.py`
- [ ] D-3 removals and contracts:
      `git grep -n -E "cut_spec_by_ssn_band|spec_by_ssn_band|ssn_band_intervals" -- src tests docs/source`
      → no output, exit 1 (control at `d0b51fa4` `| wc -l` → 25);
      `git grep -n -E 'abstractproperty|abstractstaticmethod' -- src/solarwindpy/solar_activity`
      → no output, exit 1; `grep -c '__doc__ =' $s` → `0`;
      `conda run -n solarwindpy python -c "import inspect; from solarwindpy.solar_activity.base import DataLoader as D, ActivityIndicator as A; from solarwindpy.solar_activity.sunspot_number.sidc import SIDCLoader as L, SIDC as S; print(inspect.signature(D.convert_nans)==inspect.signature(L.convert_nans), list(inspect.signature(A.run_normalization).parameters)==list(inspect.signature(S.run_normalization).parameters))"`
      → `True True` (at `d0b51fa4`: `False False`)
- [ ] D-4 ICMECAT (with `g=src/solarwindpy/solar_activity/icme/icmecat.py`):
      `git grep -n "RULES_OF_THE_ROAD" -- src tests docs/source` → no output, exit 1 (control → 3);
      `git grep -n -i "rules of the road at the HELIO4CAST site" -- src/solarwindpy/solar_activity/icme | wc -l`
      → ≥ 2, the class and package docstrings (control at `d0b51fa4` → 0);
      `grep -c 'name_map = ' $g` → `1`; `grep -c 'object.__new__' $g` → `0`;
      `grep -c -E 'self\._intervals\b' $g` → `0` (control 7);
      `grep -c 'icmecat.ICMECAT_URL = str(local)' src/solarwindpy/solar_activity/icme/__init__.py` → `0`

**Package E-plot**
- [ ] E-1 `git grep -n "set_extrema" -- src/solarwindpy/fitfunctions` → no output, exit 1 (control → 1)
- [ ] E-2 `git grep -n -E '_STYLE_PATH =|_use_style' -- src` → 1 line, in `plotting/__init__.py` (control → 3)
- [ ] E-3 one clip rule:
      `git grep -n -E "0\.0001|0\.9999[^0-9]|0\.01st|99\.99(th|%)" -- src/solarwindpy/plotting tests/plotting tests/test_source_plotting_defects.py docs/source`
      → no output, exit 1 (control at `d0b51fa4` `| wc -l` → 40);
      `git grep -n -E "quantile\(\[" -- src/solarwindpy/plotting | wc -l` → `1` (control → 2);
      `conda run -n solarwindpy python -c "import numpy as np, pandas as pd; from solarwindpy.plotting.hist1d import Hist1D; Hist1D(pd.Series(np.arange(100.)), clip=(0.6, 0.9))" 2>&1 | grep -c ValueError`
      → `1` (at `d0b51fa4` the pair was accepted)
- [ ] E-4 `conda run -n solarwindpy python -c "import inspect; from solarwindpy.fitfunctions.plots import FFPlot; from solarwindpy.plotting.base import Base; print(inspect.signature(FFPlot.set_log)==inspect.signature(Base.set_log))"`
      → `True` (at `d0b51fa4`: `False`); `git grep -n "Unexpected kwarg" -- src/solarwindpy/fitfunctions src/solarwindpy/plotting/base.py | wc -l` → `1` (control → 2)
- [ ] E-5 keyword-only settings:
      `conda run -n solarwindpy python -c "import inspect; from solarwindpy.plotting import hist1d, hist2d, scatter, spiral; print([[p.name for p in inspect.signature(c.__init__).parameters.values() if p.kind not in (p.KEYWORD_ONLY, p.VAR_KEYWORD)] for c in (hist1d.Hist1D, hist2d.Hist2D, scatter.Scatter, spiral.SpiralPlot2D)])"`
      → `[['self', 'x', 'y'], ['self', 'x', 'y', 'z'], ['self', 'x', 'y', 'z', 'size', 'alpha'], ['self', 'x', 'y', 'z']]`

**Package E-core**
- [ ] E-6 (with `p=src/solarwindpy/core/plasma.py`):
      `git grep -n -E "\{s: self\.ions\.loc\[s\]\." -- $p` → no output, exit 1 (control → 2);
      `git grep -n include_dynamic -- $p` → no output, exit 1 (control → 4);
      `git grep -n "You passes" -- src` → no output, exit 1 (control → 2);
      `git grep -n '"FC_AUX"' -- $p | wc -l` → `1` (control → 4);
      `git grep -n 'get_level_values("S").unique() if s' -- src | wc -l` → `1` (control → 2);
      `git grep -n 'level = "Symbol"' -- src/solarwindpy/core/abundances.py | wc -l` → `1` (control → 2)
- [ ] E-7 `git grep -n -E "We rely on views via DataFrame.xs|cos_colat|color_norm" -- src` → no
      output, exit 1 (control at `d0b51fa4` `| wc -l` → 7);
      `git grep -n "corresponding entry" -- src/solarwindpy/core/units_constants.py` → no output, exit 1

**Package G**
- [ ] G-1 `git grep -n -E "from \. import test_base|from tests\.core\.test_" -- tests` → no output,
      exit 1 (control → 8); `ls tests/core/test_vector.py tests/core/test_tensor.py tests/core/_fixtures.py tests/examples/test_examples.py tests/core/test_contracts_class.py`
      → five paths, exit 0; `git ls-files tests/core/test_quantities.py` → no output
- [ ] G-2 `ls tests/test_available.py tests/test_fitfunctions_public_names.py tests/fitfunctions/test_trend_fit_properties.py 2>&1 | grep -c "No such file"`
      → `3` (control: all three exist at `d0b51fa4`);
      `git grep -c "for info in pkgutil.walk_packages(ff.__path__" -- tests` → 1 line, in `tests/fitfunctions/_scan.py`
- [ ] G-3 `ls tests/test_source_plotting_defects.py 2>&1 | grep -c "No such file"` → `1`;
      `git ls-files 'tests/plotting/*' | grep -c -E 'defects|review_findings|histograms|pandas_compat|agg_plot|agg_full|labels_base'`
      → `0` (control at `d0b51fa4` → 9)
- [ ] G-4 `wc -l < tests/solar_activity/sunspot_number/test_init.py` → under 20 (control 155);
      `ls tests/solar_activity/icme/test_icmecat_smoke.py 2>&1 | grep -c "No such file"` → `1`;
      `git grep -n -E "debug_print|debug-prints|external package imports|No special module path" -- tests`
      → no output, exit 1 (control → 11)
- [ ] G-5 `git grep -n "pytest.mark.integration" -- tests` → no output, exit 1 (control → 2);
      `grep -c '"integration' pyproject.toml` → `0` (control → 1);
      `SWP_RUN_DRIFT=1 conda run -n solarwindpy pytest tests/drift -q --collect-only | grep collected`
      → 8 more than the same command printed before G (17 on 2026-11-18, so 25)
- [ ] G-6 the collected count matches the relation stated at the top of package G:
      `conda run -n solarwindpy pytest --collect-only -q | grep collected` → the recorded count
      minus 10 deleted tests plus the parametrized cases item 4 adds

**Whole tree, after the last merge**
- [ ] W-1 full suite: `conda run -n solarwindpy pytest -q` → `passed`, 0 failed
- [ ] W-2 layers: `conda run -n solarwindpy lint-imports | tail -1` → `Contracts: 2 kept, 0 broken.`
- [ ] W-3 strict docs: `conda run -n solarwindpy sphinx-build -W --keep-going -n -b html docs/source docs/build/html`
      → `build succeeded`, exit 0
- [ ] W-4 doctests: `conda run -n solarwindpy pytest --doctest-modules src/solarwindpy -q` → passed, 0 failed
- [ ] W-5 CHANGELOG: `conda run -n solarwindpy pytest -q tests/test_changelog_unreleased.py` → passed;
      `sed -n '/^## \[Unreleased\]/,/^## \[0/p' CHANGELOG.md | grep -c -E "instabilities.plots|labels.epochs|plot_on_colorbar|cut_spec_by_ssn_band|RULES_OF_THE_ROAD|clip|Ion.cs|rotation|logger|3.15|keyword-only"`
      → ≥ 11
- [ ] W-6 shared config intact: `git config core.bare` → `false`
- [ ] W-7 dry-run publish (after the author's OK, § Verification): every `platform-matrix` job and
      `build-and-publish` → `success`; `update-conda-feedstock` → `skipped`

## Anti-Patterns

- Do NOT use a line number from the earlier plans or from any trace. Both plans' line numbers went
  stale with the `src/` move and every merge since; anchor on the qualified symbol and the `git grep`
  check each item names.
- Do NOT accept a check that passes while the defect stands. The plan's S24 check
  `git grep -c 'np.exp(s\*\*2.0) - 1.0'` passed because `GaussianLn` spells the variable `sigma`;
  the S19 `SSNExtrema()` count could not reach its target because a doctest line matched; a
  `git grep -E` pattern with `\s` matched nothing at all. Every absence check here carries its
  positive control at `d0b51fa4`; run the control, not only the check.
- Do NOT read or write text with the platform's default encoding. The v0.6.0 Windows publish jobs
  failed at collection when `test_docs_plot_blocks` read `usage.rst` as cp1252 (`a0d7b39d`,
  `fd0539e7`). Pass `encoding="utf-8"` to every `read_text`, `write_text`, text-mode `open` and
  `text=True` subprocess call.
- Do NOT read `gh run watch`'s result through a wrapper's exit code. A pipe (`| tail`) or a
  `conda run` wrapper returns its own status, so a failed run reads as success. Use
  `gh run watch "$RUN_ID" --exit-status` directly, then list each job's conclusion with
  `gh run view "$RUN_ID" --json jobs` (`c09e2462`).
- Do NOT `pip install` into the base Python or build an env any other way than from
  `solarwindpy.yml` plus `pip install -e ".[dev]"` inside the `solarwindpy` env. Plain
  `pip install -e .` leaves out import-linter and pre-commit, and a stale env produces failures
  that look like code bugs (CLAUDE.md § "Environment").
- Do NOT reopen a ruling in § Scope, "Rulings". A disagreement with one goes to the author with
  evidence per § Entry Protocol step 4; the item is not reworded, skipped or re-decided.
- Do NOT merge two quantities that are physically different. `Ion.cs` (one species, per
  component) and `Plasma.cs("p1+a")` (the combined fluid) share only the formula line; `nuc`'s
  W_ab is not a species total; `calculate_extrema_kind` and `calculate_edge` are two outputs;
  `Probability` and `CountOther` are a percentage and a count. Share the formula or the
  scaffolding, keep the methods.
- Do NOT create a file without its Spent-When declaration: inline for tests and docs, a sidecar
  for a new module under `src/solarwindpy/`, because shipped modules carry no inline header until
  the deferred header work lands (ruling 27).
- Do NOT edit `CHANGELOG.md` in a package worktree: `## [Unreleased]` is one block every package
  would append to, and `tests/test_changelog_unreleased.py` resolves its paths only once the code
  is merged.
- Do NOT add a `NullHandler` or any handler to a package logger: it would silence the 32
  warning-level messages core sends through `logging.lastResort`.
- Do NOT add `.copy(deep=True)` while replacing `_select` (CLAUDE.md § "Data model").
- Do NOT name either earlier plan by its plain path in a live file; a live reference blocks their
  removal. Cite them as the `<sha>:<path>` records in § Intent.
- **Must-not-modify, per package.** Each package leaves alone the files and members its wave
  siblings own, because two writers on one region turn the ff-only merge into a conflict the
  orchestrator must resolve by hand:

| Package | Must not modify (owned by a wave sibling) |
|---|---|
| I | C's members: every `logger`, `_init_logger` and class statement in the seven bases, `tools/__init__.py`, `pyproject.toml`, the usage.rst Logging section; F's test files; H's files (`examples/__init__.py`, `CLAUDE.md`, `.claude/`, workflows, `solarwindpy.yml`, `tox.ini`, `MANIFEST.in`) |
| C | I's members: `Core._select`, `_ComponentFrame.__call__`, every `_select` call site, the renamed modules and their tests, `solar_activity/plots.py`, the usage.rst colorbar block; F's and H's files |
| F | every `src/` file; `tests/core/test_seams.py` (I); `tests/tools/test_tools.py`, `tests/solar_activity/test_base.py`, `tests/plotting/test_base.py` (C); `tests/test_examples.py`, `tests/test_declared_versions.py` (H) |
| H | `pyproject.toml`'s `[tool.importlinter]` and `.claude/docs/TEST_PATTERNS.md` § "Structure and layering" (C); every `src/` file except `examples/__init__.py` and the example CSVs; F's and I's test files |
| A | B's members (`Ion.cs`, `Plasma.cs`, `Plasma.ca`, `AlfvenicTurbulence.set_data`, `Core` helpers beside `_species_total`, the `growth_rate` check and the verscharen2016 tables, `gaussians.py`, `plotting/labels/`); E-plot's members (`FFPlot.set_log`, `FFPlot._set_labels`, `FitFunction.residuals` docstring, `plotting/`); every D file |
| B | A's members (the validators, asserts and signatures listed under A, `Core._require_level_names`, the A tests in `tests/core/test_ions.py` and `tests/instabilities/test_verscharen2016.py`); every D and E-plot file |
| D | every file outside `src/solarwindpy/solar_activity/`, its tests and the usage.rst colorbar section; the usage.rst clip sentence (E-plot) |
| E-plot | A's members in `fitfunctions/core.py` and `fitfunctions/plots.py` (`FitFunction.__init__`, `_build_outside_mask`, `FFPlot.set_observations`); every B and D file; the usage.rst colorbar section |
| E-core | runs alone before G; G's files only after E-core merges |
| G | runs after E-core merges; every `src/` file |

## Verification

Run after every merge (§ Closing Protocol, "Merge protocol") and once more after the last:

```bash
cd /Users/blalterman/observatories/code/SolarWindPy
conda run -n solarwindpy pytest -q                                   # passed, 0 failed
conda run -n solarwindpy lint-imports | tail -1                      # Contracts: 2 kept, 0 broken.
conda run -n solarwindpy sphinx-build -W --keep-going -n -b html docs/source docs/build/html   # exit 0
conda run -n solarwindpy pytest --doctest-modules src/solarwindpy -q # passed, 0 failed
# right after the ff merge, while ORIG_HEAD is the pre-merge master; xargs splits in bash and zsh
git diff -z --name-only --diff-filter=d ORIG_HEAD HEAD -- '*.py' | xargs -0 conda run -n solarwindpy pre-commit run ruff-check --files
git diff -z --name-only --diff-filter=d ORIG_HEAD HEAD -- '*.py' | xargs -0 conda run -n solarwindpy pre-commit run ruff-format --files
git config core.bare                                                 # false
```

Then run the package's acceptance commands (IDs starting with its letter) on master.

### Dry-run publish

After wave 1 merges, ask the author for an OK to push master and to run the dry run, naming both
actions. On the OK:

```bash
git push origin master
gh workflow run publish.yml --ref master -f target=testpypi -f dry_run=true
RUN_ID=$(gh run list --workflow publish.yml --limit 1 --json databaseId -q '.[0].databaseId')
gh run watch "$RUN_ID" --exit-status
gh run view "$RUN_ID" --json jobs -q '.jobs[] | "\(.name): \(.conclusion)"'
```

Expect every `platform-matrix` job (3 operating systems × Python 3.12, 3.13, 3.14, 3.15) and
`build-and-publish` to report `success` and `update-conda-feedstock` to report `skipped`, per
`.claude/docs/RELEASING.md` § "5. Dry-Run the Publish Workflow". A failed job is a divergence:
report its log (`gh run view "$RUN_ID" --log-failed`) and do not work around it.

## Closing Protocol

### Merge protocol (this dispatch is the orchestrator)

For each package, in the wave order of § Scope (wave 1: I, C, F, H; wave 2: A, B, D, E-plot;
wave 3: E-core, then G):

```bash
cd <package worktree>
git rebase master                       # replay the package's commits onto current master
cd /Users/blalterman/observatories/code/SolarWindPy
git merge --ff-only <package branch>    # refuses unless master can fast-forward
```

Then run § Verification's per-merge block and the package's acceptance commands; write the
package's CHANGELOG entry from its draft as one commit; remove the worktree. A rebase conflict in a
shared file is resolved by the orchestrator keeping both packages' changes, after which it reruns
the package's acceptance commands before merging. Packages never merge into each other.

### After the Acceptance Criteria pass

After a dispatch's Acceptance Criteria pass:

1. **Append empirical findings.** Run `/session:empirical-findings <absolute-path-to-dispatch>`
   to append a `## Empirical Findings (YYYY-MM-DD trial run)` section recording end-state
   metrics, AC outcomes, deviations, and commits. In tracked contexts the skill commits
   the findings — this commit is load-bearing: step 2 deletes the dispatch, so uncommitted
   findings are lost permanently.

1a. **Write up the plan too, when the executed work has one.** `/session:empirical-findings`
   takes one path and writes the completion marker into that path alone, so a run against the
   dispatch records nothing about the `plan-<slug>-<date>.md` the work was planned from. A plan
   declares `MARKED(<self>)` like any other artifact and is spent by the same event, so run the
   skill on the plan as well. Without this the plan reads `NOT-YET` permanently: never proposed
   for removal, still resolving for every reader, and unable to announce that it is spent — the
   failure the declaration exists to prevent, at the one artifact the protocol never named.

   Two properties, neither derivable from the step itself:

   - **Each artifact reaps on its own declaration.** `/session:reap` does not pair a plan with
     its dispatch; it targets one path, checks that path's own `SPENT` verdict and its own
     committed Empirical Findings, and tears down only that file. So a plan that finished its
     work is reaped by invoking the skill on the plan directly, a separate call from the one
     that reaps the dispatch.
   - **A plan is written up only when EVERY unit it governs is done.** A multi-unit plan
     governs one dispatch per unit, so one dispatch's findings do not finish it. Marking it at
     the first unit would spend a plan whose remaining units are in flight.

   A plan with no dispatch is its own unit: run the skill on it directly, which is the same
   command with nothing else to pair.

2. **Tear down the dispatch.** `/session:reap <path>` — after its gates pass,
   delete the dispatch in git-tracked contexts. git history is the durable archive. In
   untracked locations the dispatch is preserved, because the working tree is its only
   record.
   - **Before deleting, update live cross-references.** Another *open* dispatch may name
     this one in a live instruction. Grep the open dispatches for its basename and update
     each hit, so a future zero-context executor is not sent after a deleted file.
     Historical mentions in already-completed dispatches need no change — provenance lives
     in git history.
3. **Author a successor dispatch** if work continues across sessions.
4. **Lint** the dispatch: `bash ~/.claude/tools/lint-ai-clean.sh <path>` when present.

If the dispatch was abandoned without execution: skip steps 1, 1a and 2, and optionally append
`## Abandoned (YYYY-MM-DD)` with a one-line reason. An abandoned unit's plan keeps its
`NOT-YET`, which is the correct reading — the work stopped rather than finished, and no marker
claims otherwise.
