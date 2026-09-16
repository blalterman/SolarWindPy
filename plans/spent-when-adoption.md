<!--
Spent-When: MARKED(<self>)
Supersedes: none
-->

# Spent-When adoption for SolarWindPy

## Part 0: what this system is

Declared before the objectives, because an undeclared decision is deferred to whoever
executes.

**Surface.** In-situ solar wind measurements, and the analysis a heliophysicist performs on
them. The library is the object a researcher, the author, and an assistant all work with.

**Parties, and the face each is served by.**

- **The researcher.** Served by the public API and its documentation. They meet the solar
  wind through `Plasma`, `Ion`, the plotting layer, and the solar-activity accessors, and
  they cite the result. They never read this repository's internals.
- **The author.** Served by reports. Rules on physics correctness, on what the library is
  entitled to assert about the solar wind, and on every removal.
- **The assistant.** Served by the declared conventions: the MultiIndex contract, SI units,
  the test suite, and the conditions recorded here. It composes against that grammar.
- **The published record.** The DOI, the JOSS paper, and the released distributions are
  downstream of this repository and cannot be revised in place. What ships is permanent in a
  way the working tree is not.

**Seam.** The assistant composes code, tests, and declarations, and determines whether a
declared condition has been met. The author decides whether the physics is right and whether
a file is removed. A passing test is evidence that the code does what the test says; it is
never evidence that the physics is correct, and no amount of coverage moves that boundary.

**Layer.** Analysis of in-situ solar wind measurements and the context needed to interpret
them. Not instrument calibration, not mission data reduction, and not the scientific
conclusions a user draws.

**Held stable.** The MultiIndex column contract (`M` measurement, `C` component, `S`
species), views via `.xs()` rather than copies, and SI units internally. Every other part of
this system, including every dependency bound, every reference table, and every external
endpoint, is expected to change.

### Non-objectives

Stated as boundaries, because a scope only implied gets crossed.

- **N1.** The system does not judge whether a physics result is correct. It can detect that a
  calculation is untested; it cannot detect that a tested calculation is wrong.
- **N2.** The system does not pin the versions a user runs. It declares the bounds it
  supports and the event that changes them.
- **N3.** The system does not archive its own session history. A record that no longer
  informs execution is removed rather than retained.
- **N4.** Adopting this grammar does not fix a dependency, a test, or a document. It makes the
  facts those repairs depend on auditable.

## The governance objective

**Every fact SolarWindPy records about the world outside itself states the event after which
it stops being true, so a session can determine on its own whether that event has happened.**

The facts in question are concrete: a dependency bound, a published abundance table, a
catalog URL carrying a version, a CI runtime, a supported Python series, a measured test
baseline. Each was true when written. Nothing in the repository says when any of them stops
being true, and nothing distinguishes one that still holds from one that has drifted.

**Why it matters here.** SolarWindPy's next three pieces of work — pandas 3 compatibility, the
test suite, and the documentation — are each work that *reads this repository's recorded facts
to decide what to change*. A dependency upgrade consults the bounds. A test repair consults
the baselines. A documentation rewrite consults the API descriptions. If those inputs are a
mixture of current and stale with nothing marking which is which, the repairs encode the
staleness rather than removing it, and they do so invisibly: the result passes every check it
can run on itself.

That is the whole argument for full coverage rather than a governed subset. A partially
declared repository hands the next session a surface where some claims are checked and some
are not, and offers no way to tell them apart. The declaration is what makes the difference
legible.

**The seam this preserves.** A session determines whether a condition holds. The author
decides whether a file is removed. The tooling proposes; it has no path that removes.

## Starting state

Every number below is re-derivable by the command beside it. Re-derive rather than trust.

| Quantity | Value | Command |
|---|---|---|
| Tracked files | 400 | `git ls-files \| wc -l` |
| Files carrying a declaration | 0 | `grep -rl 'Spent-When:' . --exclude-dir=.git \| wc -l` |
| Coverage | 0% | the two above |
| Inline `#` carrier | 218 | carrier census, Phase 0 |
| Inline `<!--` carrier | 131 | carrier census, Phase 0 |
| Inline `%` carrier | 2 | carrier census, Phase 0 |
| Sidecar required | 49 | carrier census, Phase 0 |

The repository is in corpus: `in_corpus()` returns `True` for a path under this root, and the
root appears on no exclusion list. The `Write` and `git commit` gates therefore already fire
here, and every one of the 400 undeclared files is a defect under R5.1b rather than a neutral
absence. This plan works a backlog that already exists; it does not opt in to one.

## The tooling, and where authority over it lives

`ai-session-mgmt` owns the grammar and ships it as the `session` plugin. This repository is a
consumer and holds no opinion about the form.

- **Grammar:** two fields, `Spent-When:` and `Supersedes:`, within the first twelve lines,
  after an optional comment opener. Both always present; `Supersedes: none` is a recorded
  decision.
- **Members:** `PERMANENT(reversal)`, `DELETED(paths)`, `PRODUCED(paths)`, `MARKED(paths)`,
  `SUPERSEDED`, `DEREGISTERED(registry)`. Every fact is read from git history, never from the
  working tree.
- **Carriers:** inline, `<file>.spent-when` sidecar, or enumerated membership in a
  `<name>.spent-group` manifest. Exactly one declaration resolves per file; resolving by two
  is out of spec rather than a precedence contest.
- **Issuer:** render every declaration with
  `python3 <plugin>/tools/spent_when.py --emit <path> --member '<member>' --supersedes '<v>'`
  and paste the output verbatim. One authority on the form means no producer holds an opinion
  about it.

SolarWindPy adds a **resolver**, not a copy. Vendoring the issuer would make this repository a
second authority on a grammar that already has one, and the copy would drift silently the
moment the spec moved.

## Phases

### Phase 1 — Reap the residue

About 100 tracked files record a session that has ended and inform no execution: the
`.claude/compaction-*.md` set, the six committed `docs/*build*.log` files, the two coverage
snapshots totalling 922 KB, `pre-commit-config.yaml.old`, and a tracked `.DS_Store`. The
spec's test applies directly: if you cannot name what ends it, it does not belong in the
repository. Writing 100 declarations for these would record a hundred decisions nobody made.

Removal is a transfer between two stores rather than a destruction; git holds the bytes.
The author approves the removal list as one batch.

**Acceptance criteria**

- [ ] The removal list is presented as paths with per-class reasoning, and the author approves
      it before any `git rm` runs.
- [ ] `git ls-files | wc -l` returns a count below 320, and `git log --diff-filter=D` records
      the removals. *Positive control:* `git show HEAD~1:<a removed path> | head -1` returns
      content, proving the bytes are recoverable.
- [ ] Every file surviving Phase 1 has a stated reason to exist, captured as the draft member
      it will carry in Phase 3 or 4.

### Phase 2 — The governance statement enters the repository

Part 0 and the governance objective above become `docs/objectives-and-requirements.md`, the
root of this repository's specification chain. It names no file, no script, and no threshold
value: an objective that names a mechanism cannot survive the mechanism changing.

This resolves a live gap. Three documents require every plan to score at least 80 on
"SolarWindPy alignment" and "mission consistency", and `.claude/hooks/plan-scope-auditor.py`
enforces that score, while no document states the mission being scored against. The objective
exists today only as literals inside the auditor.

The statement does not go in `CLAUDE.md`. That file is guidance for a session, and a second
home for a fact makes two authorities on it.

**Acceptance criteria**

- [ ] `docs/objectives-and-requirements.md` exists, carries a rendered declaration, and states
      Surface, Parties, Seam, Layer, Held stable, and Non-objectives.
- [ ] `.claude/hooks/plan-scope-auditor.py` cites the document as the source of the mission it
      scores. *Positive control:* run the auditor against a plan that plainly serves the
      objective and against one that plainly does not, and confirm the scores differ. A scorer
      that returns the same number for both is measuring nothing.
- [ ] `CLAUDE.md` points at the document by name and restates none of it.

### Phase 3 — Declare the 49 sidecar files and the 2 percent-carriers

These are the judged cases, and each earns its sidecar for one of three mechanical reasons:
the bytes cannot hold a declaration, a consumer is changed by one, or the syntax has nowhere
to put it that is not content.

- **8 JSON files** take sidecars unconditionally. A top-level key leaves the file parseable
  and changes the object.
- **13 `.rst` files**, including `README.rst` and every `docs/source/` page, take sidecars:
  reStructuredText's `..` is not in the grammar's comment alternation.
- **7 `.csv` files** take sidecars because a header line is data. Three of these are the
  highest-value declarations in the repository and are handled in Phase 5.
- **Binary and opaque carriers** — `paper.pdf`, `favicon.ico`, the archived `.tar.gz` —
  cannot hold the bytes.
- **Dotfiles and extensionless files** — `.gitignore`, `.gitmessage`, `.pydocstyle`, `LICENSE`,
  `MANIFEST.in`, `docs/Makefile` — have no extension the issuer can read.

Group manifests are appropriate where a set is genuinely one artifact, and the author confirms
each membership list before it is written. Candidates: `tests/data/*.csv` as one fixture set;
`docs/source/_templates/autosummary/*.rst` as one template set;
`plans/tests-audit/artifacts/*` as one audit output.

**Acceptance criteria**

- [ ] Every sidecar's content came from `--emit` rather than being typed. *Positive control:*
      re-run `--emit` with the same arguments for three sidecars chosen at random and confirm
      byte-identical output.
- [ ] `spent_when.py` reports zero `INVALID` and zero `OUT-OF-SPEC` across the repository.
      *Positive control:* introduce a deliberately malformed declaration in a scratch file,
      confirm the validator reports it, then remove it. A validator that has only ever
      returned clean has not been shown to fire.
- [ ] No file resolves a declaration by more than one carrier.
- [ ] Every `.spent-group` membership list was read and approved by the author before writing.

### Phase 4 — Declare the 349 inline carriers

218 hash carriers (`.py`, `.sh`, `.yml`, `.yaml`, `.toml`, `.cfg`, `.ini`) and 131 html
carriers (`.md`, `.html`).

Most source modules will declare `PERMANENT`, and each still owes a real reversal: R3.2
requires a permanent file to state what would end its permanence, so permanence stays
falsifiable rather than becoming a default. `PERMANENT(the Plasma class is removed from the
public API)` records a decision; `PERMANENT(this file is permanent)` records none.

Work the tree in dependency order — `core`, then `plotting`, `fitfunctions`,
`solar_activity`, `instabilities`, `tools` — so the reversal condition for a module is written
after the modules it depends on are understood.

The `.claude/` and `plans/` markdown carries the largest share of the html set and the
weakest claim to permanence. Files describing a workflow that no longer runs are Phase 1
candidates a second pass will surface.

**Acceptance criteria**

- [ ] Declaration coverage reaches 100%: the count of files carrying a declaration equals
      `git ls-files | wc -l`. *Positive control:* the coverage report names its denominator,
      so a truncated scan reads `COVERAGE N of M` rather than appearing clean.
- [ ] No declaration reads `PERMANENT` with a reversal that restates permanence, and none
      hedges between two futures. A declaration hedging between futures is a declaration not
      yet made.
- [ ] `solarwindpy/_version.py` and any other generated file is declared through its producer.
      *Positive control:* run the generator, then confirm the declaration survives. A
      declaration its own generator deletes is worse than none, because it reads as a decision
      right up until it silently disappears.

### Phase 5 — The external-fact register

The declarations that unlock the three downstream tasks. Each pins a fact about the world and
currently states no condition for revisiting it.

| Artifact | The pinned fact | The event that ends it |
|---|---|---|
| `solar_activity/icme/icmecat.py` | `HELIO4CAST_ICMECAT_v23.csv`, plus a transcribed co-authorship policy | HELIO4CAST publishes a successor catalog version |
| `sunspot_number/ssn_extrema.csv` | SILSO solar cycle minima and maxima | SILSO revises the cycle table |
| `core/data/asplund2021.csv` | Asplund et al. 2021 photospheric abundances | a successor compilation is published |
| `pyproject.toml` bounds | `numpy<3.0`, `docstring-inheritance<3.0`, `pandas>=2.0` | the named incompatibility is resolved upstream |
| `requirements.txt`, `requirements-dev.lock`, `docs/requirements.txt` | three mutually inconsistent locks | a regeneration run |
| four `conda-recipe`/`recipe` `meta.yaml` | versions 0.1.2 / 0.1.4 / 0.1.dev1034 against a released 0.3.0 | the generating script runs |
| `.readthedocs.yaml` | `ubuntu-22.04`, Python 3.11 | RTD retires the image |
| `.pre-commit-config.yaml` | black 23.1.0, flake8 6.0.0 | the pins reach the floors `pyproject.toml` declares |

Two of these resolve defects on contact. The conda recipes and the lockfiles disagree with
`pyproject.toml` and with each other, and writing the condition forces the question of which
one is canonical. `tox.ini` names `requirements-dev.txt`, a file that does not exist, so tox
cannot run at all.

`units_constants.py` derives from `scipy.constants` and rides CODATA updates automatically.
Two literals, `Re` and `Rs`, do not, and carry no cited source. Citing them is the
declaration.

**Acceptance criteria**

- [ ] Every row above carries a declaration whose member names an observable event.
- [ ] Where a condition cannot be evaluated mechanically, it says so and describes the manual
      check, rather than shipping a command that can only ever report "not yet". A condition
      stated as an absence usually cannot be checked, because `Purge-Check`-style evaluation
      runs without a shell.
- [ ] `CITATION.rst`, currently the single word `TODO` behind a README pointer and a live DOI,
      is either filled or declared with the event that fills it.
- [ ] One lockfile is named canonical in `docs/objectives-and-requirements.md`, and the others
      declare their relationship to it.

### Phase 6 — Wire the sweep and hand off

**Acceptance criteria**

- [ ] `/session:close` step 5 runs clean against this repository with `--corpus` setting the
      denominator, reporting four populations: conditions met, invalid declarations, files
      carrying none, and declarations revised in the window.
- [ ] `docs/PROGRESS.md` exists and records the state and the next action.
- [ ] The project memory directory holds a `MEMORY.md` index and the decisions this work
      settled. It is currently empty, so `/session:recall` against this project returns
      nothing.
- [ ] The pandas-3 dispatch's measured baselines are re-derived and the dispatch either
      carries current numbers or is declared spent. The three downstream tasks may begin.

## Positive controls for this plan

Each control is a check run against a case where the condition is known to hold, so an empty
result is distinguishable from a check that never ran. An empty result is a question and never
a verdict.

1. **Coverage is reported against a stated denominator.** A scan that silently read zero files
   reports the same clean as a scan that read everything.
2. **The validator is shown to fail before it is trusted to pass.** A deliberately malformed
   declaration must be reported, then removed.
3. **Generated files are re-generated after declaring.** The producer, not the working tree,
   is the test of whether a declaration survives.
4. **Every count in this document carries its re-derivation command.** A reader refreshes
   rather than trusts.
5. **The carrier census comes from `carrier()`, not from reading extensions.** The `.rst`
   result contradicted the extension-based guess, and the tool was right.

## What this plan does not do

It does not repair a dependency, a test, or a document. Those are the three tasks this unlocks,
and each gets its own dispatch once the facts they consume are declared and auditable.
