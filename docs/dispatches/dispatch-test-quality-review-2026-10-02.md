<!--
Spent-When: MARKED(<self>)
Supersedes: none
-->

# Dispatch: holistic test-quality review of SolarWindPy

author_signoff: none

owner: /Users/balterma/observatories/code/SolarWindPy

**Generated:** 2026-10-02
**Branch:** master
**Work type:** software

## Governing Property

Every passing test in SolarWindPy means a behavior the package owes its users holds; every
behavior the package owes has a test that would fail if it broke; and no test fails when the
package changes correctly.

## Purpose

A suite fixed directory by directory is never measured as a whole against what the package
owes, so gaps, checks of the wrong thing, and fragile tests (hard-coded numbers, repo-state
checks, assertions on private internals) persist wherever no one looks. Line coverage shows
which lines ran, not which promises are checked or which tests block correct changes. The
review builds its inventory with tools that produce re-runnable artifacts, chosen by a short
trial.

Existing capability and its limit:

- `/Users/balterma/observatories/code/SolarWindPy/.claude/docs/TEST_PATTERNS.md` states how
  to write one test, not what the suite must cover.
- `/Users/balterma/observatories/code/SolarWindPy/tests/test_public_imports.py` checks that
  public names import and are documented, not that they behave.

## Intent

When this review is done, the author holds a findings report that relates every collected
test and every documented example to what the package owes, and a partitioned fix program
ready to launch. Every number in both documents is reproducible from a recorded command or
artifact.

The observable difference: each test in the suite can be answered for, by type, by what it
asserts, by where its expected value comes from, and by the harm it does if it binds to the
wrong thing, and each owed behavior without a test that would fail is named.

Confirm or rewrite this reading before designing against it. Every step below inherits from it.

### Surface

`tests/`, `README.rst`, `docs/source/` including `docs/source/tutorial/quickstart.rst` and
`docs/source/tutorial.rst`, and the docstring examples in `solarwindpy/`, measured against
`.claude/docs/TEST_PATTERNS.md`. The review writes two documents and changes no code or test.

### Parties

- The researcher who installs SolarWindPy and cites what it computes.
- The author, who decides physics correctness, every removal, and what merges.
- This review session.
- The fix units that execute the fix program later.

### Seam

This session decides tool selection, measurement method, test classification, and the
proposed disposition of each finding. The author decides whether a physics expectation is
correct, every removal, which tests of the repository's own tooling stay, and which tools
join the dev dependencies in `pyproject.toml`.

### Layer

Whether tests and documented examples check what the package owes, and only that. Whether the
physics itself is right is the author's layer.

### Blast radius

Two new documents in `docs/dispatches/`, re-runnable artifacts under the git-ignored
`tmp/test-quality-review/`, and a throwaway conda environment for the tools. One local commit;
push on the author's approval.

## Motivation

Each command below re-derives a fact this review rests on. Run them in the `solarwindpy` env
from the repository root.

- Line coverage total: `pytest --cov=solarwindpy -q 2>&1 | grep TOTAL`
- Tests stating what to do when they fail, against tests collected:
  `grep -rho "ON FAILURE" tests/ | wc -l` and `pytest --collect-only -q 2>&1 | tail -1`
- Docstring examples that never run: `grep -rn "+SKIP" solarwindpy --include='*.py' | wc -l`
- Quick Start examples outside any runner:
  `grep -c 'code-block' docs/source/tutorial/quickstart.rst` and
  `grep -c '>>>' docs/source/tutorial/quickstart.rst`
- A test reading documentation text: `grep -n "CLAUDE" tests/test_hook_integration.py`

Known defects, used below as the review's positive control: the `CLAUDE.md`-coupled assertion
and the text-matching hook tests in `tests/test_hook_integration.py`; the docstring at
`tests/solar_activity/sunspot_number/test_sidc.py:12`, which says nothing patches a name from
`sidc.py` while a test in the same file does; the `+SKIP` docstring examples; and the
`code-block` examples in `docs/source/tutorial/quickstart.rst`. A method that does not surface
each of them on its own is too weak, and the findings say so.

## Entry Protocol

```
This is diagnostic work -- the goal is to learn the system's actual behavior, not
to execute a pre-specified change. Follow this protocol:

1. Read this dispatch in full.
2. Run the commands in "Observe First" and read their real output before
   committing to any hypothesis. Reality is the source of truth; this
   dispatch's framing is not.
3. State your initial hypothesis, grounded in what step 2 showed.
4. Probe to confirm or refute (run, read, measure). Iterate steps 3-4 until the
   evidence converges. On an ambiguity probing cannot settle, follow the
   Divergence Resolution Ladder.
5. Report findings with evidence and propose next actions. Make no irreversible
   change until the user confirms the diagnosis.

---
```

## Scope

Run in this order. Artifacts go to `tmp/test-quality-review/`; each artifact's generating
command is recorded in the findings.

1. **Tool trial.** In a throwaway conda env (Python 3.12, `pip install -e ".[dev]"`), try:
   griffe, coverage.py dynamic contexts (`--cov-context=test`), mutmut, ast-grep, Sybil,
   pytest-randomly, grimp, pydeps, pyreverse, radon, wily, vulture, deptry,
   pytest-deadfixtures, ruff with the `PT` and `B` rule sets, `pytest --durations`,
   interrogate, numpydoc validation, Sphinx linkcheck. A tool is kept when it runs on this
   package and writes a re-runnable artifact. Record each tool as kept or dropped, with the
   reason. Remove the env at the end.
2. **Contract inventory.** Every public object (griffe over `solarwindpy/`, cross-checked
   against `solarwindpy.fitfunctions.available()` and
   `solarwindpy.plotting.labels.available()`), the
   physics identities the package computes, and the behaviors promised in docstrings and in
   documented examples.
3. **Test inventory.** Every collected test classified by type (architecture or structure,
   unit, functional, integration, end-to-end), by what it asserts, and by the source of its
   expected value (derived, cited, captured from a run). One row per test in
   `tmp/test-quality-review/tests.csv`, with a header row.
4. **Cross-map.** Gaps: owed behavior no test catches, from coverage contexts and from
   mutation survivors. Excess: tests checking nothing the package owes. Run mutmut module by
   module on a sample that includes `solarwindpy/plotting/hist2d.py`, and record the sample.
5. **Fragility and harm.** Every test a correct change breaks: captured literals, repo-state or
   file-text checks, private-name access, call-count mocks. Class each by harm (blocks a
   correct change, misstates the contract, invites edit-until-green) and propose a
   disposition (derive, cite, move, delete).
6. **Tooling tests.** Each test of the repository's own tooling (hooks, conventions, declared
   versions, import aliases) names the user-facing harm it prevents, or is proposed for
   removal or for a move outside the package suite.
7. **Documented code.** Quick Start, tutorial, README, and docstring examples: which run,
   which are skipped, which are wrong.
8. **Suite properties.** Random-order determinism, seeding, run time, network use, marker
   hygiene.
9. **Outputs.**
   - `docs/dispatches/findings-test-quality-review-2026-10-02.md`: every number with its
     command or artifact path; a tool-trial table; the positive-control results.
   - `docs/dispatches/batch-test-quality-fixes-2026-10-02.md`: the fix program as a batch
     instruction, one unit per disjoint file set on a single line of the form
     `OWNS: <path>, <path>`, long-running units listed separately, each unit's baselines with
     the command that produced them, and the commit route
     `conda run -n solarwindpy git commit -F <file> -- <paths>` with explicit-path staging.

## Observe First

```bash
cd /Users/balterma/observatories/code/SolarWindPy
conda run -n solarwindpy pytest --collect-only -q 2>&1 | tail -1
conda run -n solarwindpy pytest --cov=solarwindpy -q 2>&1 | grep TOTAL
conda run -n solarwindpy python -c "import pkgutil, solarwindpy; print(len(list(pkgutil.walk_packages(solarwindpy.__path__, 'solarwindpy.'))))"
grep -rn "+SKIP" solarwindpy --include='*.py' | wc -l
grep -n "CLAUDE" tests/test_hook_integration.py
grep -c 'code-block' docs/source/tutorial/quickstart.rst
sed -n 1,20p tests/solar_activity/sunspot_number/test_sidc.py
```

## State Verification

```bash
cd /Users/balterma/observatories/code/SolarWindPy
git status --porcelain -- solarwindpy tests      # expect no output
git branch --show-current                         # expect master
git rev-list --count master..origin/master        # expect 0
conda run -n solarwindpy pytest -q 2>&1 | tail -1 # expect 0 failed
```

## Acceptance Criteria

Each criterion carries a positive control showing the check can fire. Run from
`/Users/balterma/observatories/code/SolarWindPy`.

- [ ] Tool trial complete: `for t in griffe coverage mutmut ast-grep Sybil pytest-randomly grimp pydeps pyreverse radon wily vulture deptry pytest-deadfixtures ruff durations interrogate numpydoc linkcheck; do grep -qi -- "$t" docs/dispatches/findings-test-quality-review-2026-10-02.md || echo "MISSING $t"; done` → no output. Control: the same loop with `notatool` appended prints `MISSING notatool`.
- [ ] Contract inventory reproducible: the inventory command recorded in `docs/dispatches/findings-test-quality-review-2026-10-02.md` re-run → the count recorded there. Control: the inventory artifact contains `Plasma` (`grep -c Plasma <artifact>` → 1 or more).
- [ ] Every test classified: `tail -n +2 tmp/test-quality-review/tests.csv | wc -l` → the count from `conda run -n solarwindpy pytest --collect-only -q 2>&1 | tail -1`. Control: the same count on a copy with one row deleted differs by 1.
- [ ] Known defects surfaced: `for k in "test_hook_integration.py" "CLAUDE.md" "test_sidc.py:12" "+SKIP" "quickstart.rst"; do grep -qF -- "$k" docs/dispatches/findings-test-quality-review-2026-10-02.md || echo "MISSED $k"; done` → no output. Control: the same loop with `test_nonexistent_widget.py` appended prints `MISSED test_nonexistent_widget.py`.
- [ ] Mutation sampling live: `docs/dispatches/findings-test-quality-review-2026-10-02.md` reports surviving mutants per sampled module, or a stated reason for none. Control: mutmut's results for `solarwindpy/plotting/hist2d.py` show the mutant that flips the `x0 <= x` comparison as killed.
- [ ] Fix program partitioned: `grep -c '^OWNS:' docs/dispatches/batch-test-quality-fixes-2026-10-02.md` → 1 or more, and `grep -oE '^OWNS: .*' docs/dispatches/batch-test-quality-fixes-2026-10-02.md | tr ' ,' '\n\n' | grep -v '^OWNS:' | grep . | sort | uniq -d` → no output. Control: the same pipeline on a copy with one `OWNS:` path duplicated prints that path.
- [ ] Read-only held: `git status --porcelain -- solarwindpy tests` → no output, and `git show --name-only --format= HEAD` → the two output documents only. Control: a scratch edit to one test file is listed by the same `git status` command, then reverted with `git checkout -- <file>`.

## Verification

```bash
cd /Users/balterma/observatories/code/SolarWindPy
test -f docs/dispatches/findings-test-quality-review-2026-10-02.md && echo findings
test -f docs/dispatches/batch-test-quality-fixes-2026-10-02.md && echo fix-program
git status --porcelain -- solarwindpy tests
conda run -n solarwindpy pytest -q 2>&1 | tail -1
git log --oneline -1
```

## Closing Protocol

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
   - **A plan is written up only when EVERY unit it governs is done.** `/session:plan-draft`
     emits one dispatch per unit from a single plan, so one dispatch's findings do not finish a
     multi-unit plan. Marking it at the first unit would spend a plan whose remaining units are
     in flight.

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

### Orchestrator handoff lifecycle

A parent handoff's closeout is asymmetric with a dispatch's. A dispatch is purged right
after its own Acceptance Criteria pass; a parent handoff waits until every child dispatch
is DONE.

- **Populate the findings index incrementally.** Each time a child dispatch commits its
  `## Empirical Findings`, append that child's row to the parent's findings index
  (`child-slug -> findings-commit SHA -> elapsed-vs-estimate`). The index points at the
  committed findings in git history; it never restates them.
- **Purge only when all children are DONE.** A parent purged while a child is still open
  would strand that child's context.

---

