<!--
Spent-When: MARKED(<self>)
Supersedes: none
-->

# Dispatch: SolarWindPy modernization, gates and declarations, then the phase-4 batch

author_signoff: none

owner: /Users/balterma/observatories/code/SolarWindPy

**Generated:** 2026-09-28
**Branch:** master
**Work type:** software

## Governing Property

SolarWindPy installs, runs, and returns correct results on every dependency version it
declares, and every check, version declaration, document, and test that asserts so is able to
fail when the assertion is false.

## Purpose

An artifact that reports health it never measured moves the cost of every later change onto
unverified ground. Six forms of that artifact exist in this repository, and each workstream
answers one:

- **W1, gates.** A check that cannot fail certifies nothing: a doctest runner that counts an
  import failure as a pass, a docs build whose warnings-as-errors flag is overwritten, a
  pre-commit pattern that skips a directory.
- **W2, dependency drift.** Code written against one pandas and matplotlib breaks silently
  on the next. Both environments now pass; the ranges that record this are W3's.
- **W3, declarations.** A version range the package has never run is a promise to every
  installer that nothing checked.
- **W4, tests.** A test bound to the implementation passes on broken code and fails on a
  correct rewrite, so the suite certifies what the code does instead of what it owes.
- **W5, documentation.** A documented call that does not run costs a reader a debugging
  session before they reach the science.
- **W6, retirement.** Every file in the tree is read by every session, so a finished or dead
  artifact competes with live ones and cannot be told apart from them.

Existing capability, and what each leaves open:

- `/Users/balterma/observatories/code/SolarWindPy/.claude/docs/TEST_PATTERNS.md` is the test
  standard. It governs how W4 writes tests; it does not enforce itself.
- `/Users/balterma/observatories/code/SolarWindPy/.pre-commit-config.yaml` runs black, flake8,
  doc8 and the full suite with an 80% coverage floor. It cannot tell a meaningful test from a
  vacuous one and does not cover `scripts/`.
- `/Users/balterma/observatories/code/SolarWindPy/tests/drift/` checks facts about outside
  sources weekly. Nothing checks the package's own declared versions against what it runs on.

## Intent

When this dispatch is done, every remaining W1 gate fails on a known-bad input, every version
the repository declares is one it has run, and a phase-4 batch instruction partitions W4, W5,
and W6 into units with disjoint file sets, ready for the author to launch.

The observable difference: a commit that breaks a doctest, a docs cross-reference, a script's
formatting, or a version pin is refused, and the phase-4 run can start from a trustworthy
gate.

Confirm or rewrite this reading before designing against it. Every step below inherits from
it.

This dispatch executes the program plan at
`/Users/balterma/.claude/plans/note-icmecat-s-hardcoded-v23-typed-bear.md`. That plan settles
the workstream contents, the dependency order, and the test standard's rationale.

### Surface

The six workstreams' files: `tests/`, `docs/`, `solarwindpy/` where a workstream edits source,
and the packaging and CI configuration (`pyproject.toml`, the three lockfiles, `recipe/`,
`conda-recipe/`, `.github/`, `.pre-commit-config.yaml`, `docs/Makefile`, `.readthedocs.yaml`,
`tox.ini`). This session executes W1 and W3; W4, W5 and W6 are prepared as the phase-4 batch.

### Parties

- The researcher who installs SolarWindPy and cites what it computes.
- The author, who decides physics values and label wording and merges every pull request.
- This executing session.
- The phase-4 batch units, which read only their own unit brief.

### Seam

This session and the batch units decide test structure, gate wiring, version ranges from
measurement, and removals the program plan lists. A unit that finds a library defect inside
its own files fixes it, with a test that fails before the fix and passes after; a defect
outside its files becomes a strict xfail naming what retires it. Physics values that cannot be
derived or cited, and the exact wording of plot labels, go back to the author.

### Layer

Whether the package does what it declares. Separate from whether a physical result is
scientifically preferable, which stays with the author.

### Blast radius

This session commits W1 and W3 to `master` and runs the `sync-requirements.yml` workflow on
GitHub. Phase-4 units push their own branches and open pull requests; none merges. Every
removal is recoverable from git history, except `staged-recipes-fork/`, which is untracked.

## Motivation

- The pilot of four units merged as pull requests 435 to 437 and showed that the standard,
  the gates, and the partition rule hold under batch execution.
- Three W1 gates still report success without measuring:
  `ls /Users/balterma/observatories/code/SolarWindPy/scripts/simple_doc_validation` lists the
  standalone doctest runner, `grep -n '^SPHINXOPTS' /Users/balterma/observatories/code/SolarWindPy/docs/Makefile`
  shows a plain assignment, and `grep -n 'files:' /Users/balterma/observatories/code/SolarWindPy/.pre-commit-config.yaml`
  shows patterns without `scripts`.
- `grep -n requires-python /Users/balterma/observatories/code/SolarWindPy/pyproject.toml`
  shows the declared floor; both conda environments named in § State Verification pass the
  suite, so W3's ranges can be measured rather than guessed.
- Numbers in the program plan's measured-state table are re-derived by § State Verification.
  Where the two differ, the command governs.

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
   unresolved, the shape-matched tool, distilled back to plain English -> the
   user last. Never guess past it, never mask a failure; irreversible actions
   and scope or intent changes go straight to the user.
5. Report completion against the Acceptance Criteria.

---
```

## Scope

Execute in this order. Each stage lands as its own commits before the next starts.

**Stage 1, W1 gates.** Three changes, each demonstrated failing on a known-bad input with the
demonstration recorded in its commit message:

1. Replace `scripts/simple_doc_validation/` with pytest's doctest collection
   (`--doctest-modules` for `solarwindpy/`, `--doctest-glob='*.rst'` for `docs/source/`).
   Point `.github/workflows/doctest_validation.yml` at the pytest invocation and delete the
   runner directory. Doctests that fail under pytest are fixed when the fix is inside the
   docstring and the expected output is derivable; otherwise they are marked strict xfail with
   a reason.
2. In `docs/Makefile`, change `SPHINXOPTS    =` to `SPHINXOPTS    ?=` so the `-W --keep-going -n`
   that `.github/workflows/docs.yml` exports reaches `sphinx-build`.
3. In `.pre-commit-config.yaml`, extend the black and flake8 `files:` patterns to include
   `scripts/`, then format and lint `scripts/` so the hook passes.

**Stage 2, W3 declarations.**

1. Set `requires-python` to `">=3.12,<4"` in `pyproject.toml` and update its version
   classifiers. Carry 3.12 as the floor to every file that asserts a Python version: `tox.ini`,
   `.readthedocs.yaml`, `recipe/meta.yaml`, and every `.github/workflows/*.yml` returned by
   `grep -l python-version .github/workflows/*.yml`.
2. Set the pandas range to the lowest version the suite passes on through the next untested
   major. Establish the floor by running the suite, not by reading release notes.
3. Add a fast test that asserts every declared Python version satisfies `requires-python`,
   and demonstrate it failing on one deliberately wrong site before correcting it.
4. Regenerate the three lockfiles through the `sync-requirements.yml` workflow and merge the
   pull request it opens only after both environments pass. Change `.github/dependabot.yml`
   so pip updates target `pyproject.toml`.
5. Keep `recipe/meta.yaml` as the single conda recipe. Delete `conda-recipe/`. Before
   removing the untracked `staged-recipes-fork/`, run
   `git -C staged-recipes-fork log --branches --not --remotes --oneline`; any output is
   unpushed work and goes to the author before deletion.
6. Confirm Read the Docs offers Python 3.12 on the image `.readthedocs.yaml` pins, and change
   the image in the same commit when it does not.

**Stage 3, the phase-4 batch instruction.** Write
`/Users/balterma/observatories/code/SolarWindPy/docs/dispatches/batch-phase4-2026-09-28.md`
carrying the instruction the author pastes after `/batch`. It holds:

- The governance triple for each of W4, W5, W6 from the program plan, and the test standard
  by path.
- One unit per directory or document set, each with its exact owned paths on a single line
  of the form `OWNS: <path>, <path>`, directories ending in `/`. W4 follows the
  plan's rebuild and repair verdicts, the CODATA value tests, the first tests for
  `solarwindpy/instabilities/`, replacing `tests/test_circular_imports.py` with an
  `import-linter` contract, shrinking `tests/drift/`, and the D205 docstring warning at
  `tests/core/test_ions.py:223`. W5 and W6 follow their plan sections, less the items
  § Anti-Patterns reserves. W5 also repoints three files that cite sections the current
  `.claude/docs/TEST_PATTERNS.md` no longer has: `.claude/commands/swp/test/audit.md`,
  `tools/dev/ast_grep/test-patterns.yml`, and `.claude/docs/DEVELOPMENT.md`.
- Units expected to run long, listed separately, so they are identified before launch. The
  pilot's hardest unit ran about ten times the median.
- Each unit's baselines with the command that produced each number.
- The commit route `conda run -n solarwindpy git commit`, explicit-path staging, and push
  branch plus open pull request with no merge.

Stop after Stage 3. The author launches phase 4.

## Read First

1. `/Users/balterma/.claude/plans/note-icmecat-s-hardcoded-v23-typed-bear.md` -- the program
   plan: governance-level purpose and intent, governing principle, § "What a test binds to",
   each workstream's Purpose, Intent, and Seam, § "Batch topology", and § "Parked".
2. `/Users/balterma/observatories/code/SolarWindPy/.claude/docs/TEST_PATTERNS.md` -- the test
   standard every phase-4 test unit follows.
3. `/Users/balterma/observatories/code/SolarWindPy/CLAUDE.md` -- commands and conventions, in
   particular the bare-`pytest` rule and the pre-commit hook's coverage floor.
4. `/Users/balterma/observatories/code/SolarWindPy/.pre-commit-config.yaml`,
   `/Users/balterma/observatories/code/SolarWindPy/docs/Makefile`,
   `/Users/balterma/observatories/code/SolarWindPy/.github/workflows/doctest_validation.yml`
   -- the three W1 gate sites.
5. `/Users/balterma/observatories/code/SolarWindPy/pyproject.toml` and
   `/Users/balterma/observatories/code/SolarWindPy/.github/workflows/sync-requirements.yml`
   -- the W3 declaration source and its lockfile generator.

## State Verification

```bash
cd /Users/balterma/observatories/code/SolarWindPy
git fetch origin --quiet
git rev-list --count master..origin/master     # expect 0
git rev-list --count origin/master..master     # expect 0; a batch worktree branches from origin
git status --porcelain | grep -v -e '^?? .claude/worktrees/' -e '^?? my_plot'   # expect no output
conda run -n solarwindpy pytest -q 2>&1 | grep -E '[0-9]+ (passed|failed)' | tail -1
conda run -n imap-loaders-20260225 pytest -q --no-header \
  --ignore=tests/plotting/test_performance.py --ignore=tests/test_issue_titles.py 2>&1 \
  | grep -E '[0-9]+ (passed|failed)' | tail -1
# both: 0 failed. The two environments carry pandas 2.3.x and 3.0.x respectively:
conda run -n solarwindpy python -c 'import pandas,sys;print(pandas.__version__, sys.version.split()[0])'
conda run -n imap-loaders-20260225 python -c 'import pandas,sys;print(pandas.__version__, sys.version.split()[0])'
grep -c 'Spent-When' .claude/docs/TEST_PATTERNS.md   # expect 1: the standard is on disk
```

## Acceptance Criteria

- [ ] Standalone doctest runner removed: `test -d /Users/balterma/observatories/code/SolarWindPy/scripts/simple_doc_validation; echo $?` → `1`
- [ ] Doctests run under pytest and pass: `cd /Users/balterma/observatories/code/SolarWindPy && conda run -n solarwindpy pytest --doctest-modules solarwindpy -q 2>&1 | tail -1` → a summary with `0 failed`, or no `failed` count
- [ ] Doctest workflow calls pytest: `grep -c 'doctest-modules' /Users/balterma/observatories/code/SolarWindPy/.github/workflows/doctest_validation.yml` → `1` or more
- [ ] Sphinx options overridable: `grep -nE '^SPHINXOPTS[[:space:]]+\?=' /Users/balterma/observatories/code/SolarWindPy/docs/Makefile` → one line
- [ ] Sphinx `-W` fails on a bad reference: the commit message of the Makefile change shows `sphinx-build` exiting non-zero on an injected broken cross-reference: `git -C /Users/balterma/observatories/code/SolarWindPy log -1 --format=%B -- docs/Makefile | grep -ci 'exit\|error'` → `1` or more
- [ ] Pre-commit covers scripts: `grep -cE 'files:.*scripts' /Users/balterma/observatories/code/SolarWindPy/.pre-commit-config.yaml` → `2` or more, and `cd /Users/balterma/observatories/code/SolarWindPy && conda run -n solarwindpy pre-commit run black --all-files` → `Passed`
- [ ] Python floor declared: `grep -n 'requires-python' /Users/balterma/observatories/code/SolarWindPy/pyproject.toml` → `requires-python = ">=3.12,<4"`
- [ ] No declared Python version below 3.12: `grep -rnE "3\.1[01]['\"]" /Users/balterma/observatories/code/SolarWindPy/pyproject.toml /Users/balterma/observatories/code/SolarWindPy/tox.ini /Users/balterma/observatories/code/SolarWindPy/.readthedocs.yaml /Users/balterma/observatories/code/SolarWindPy/.github/workflows /Users/balterma/observatories/code/SolarWindPy/recipe/meta.yaml` → no output
- [ ] Declared-version consistency test exists and passes: `cd /Users/balterma/observatories/code/SolarWindPy && conda run -n solarwindpy pytest -q -k requires_python 2>&1 | tail -1` → `passed`, no `failed`
- [ ] Single conda recipe: `test -e /Users/balterma/observatories/code/SolarWindPy/conda-recipe; echo $?` → `1`
- [ ] Dependabot targets pyproject: `grep -n 'directory' /Users/balterma/observatories/code/SolarWindPy/.github/dependabot.yml` → the pip entry points at the directory holding `pyproject.toml`
- [ ] Suite green in both environments after stages 1 and 2: the two suite commands in § State Verification → `0 failed` each
- [ ] Phase-4 instruction written: `test -f /Users/balterma/observatories/code/SolarWindPy/docs/dispatches/batch-phase4-2026-09-28.md; echo $?` → `0`
- [ ] Phase-4 units own disjoint paths: `grep -oE '^OWNS: .*' /Users/balterma/observatories/code/SolarWindPy/docs/dispatches/batch-phase4-2026-09-28.md | tr ' ,' '\n\n' | grep -v '^OWNS:' | grep . | sort | uniq -d` → no output
- [ ] Nothing ahead of origin before the batch launches: `git -C /Users/balterma/observatories/code/SolarWindPy rev-list --count origin/master..master` → `0`

## Anti-Patterns

- Do NOT commit with a bare `git commit`. A bare shell resolves `/opt/anaconda3/bin/pytest`
  7.4.4, which produces about 25 order-dependent failures and blocks the hook on correct work.
  Use `conda run -n solarwindpy git commit`.
- Do NOT pass `--no-verify`. Skipping the hook skips black, flake8, doc8 and the suite
  together, which is how 160 flake8 violations accumulated in `tests/`.
- Do NOT stage with `git add -A`, `git add .`, or `git commit -a`. Another session works this
  checkout and holds the index intermittently; stage explicit paths and retry on an
  `index.lock` rather than removing it.
- Do NOT launch the phase-4 batch before local `master` is pushed. Batch worktrees branch from
  `origin/master`, and a stale origin sent three pilot units to a base 25 commits old.
- Do NOT change the `29.9` constant in `Plasma.lnlambda`. It is parked until the author
  supplies its citation.
- Do NOT delete `.claude/scripts/gh-plan-create.sh` or the `.claude/hooks/plan-*.py` scripts it
  calls. `/Users/balterma/observatories/code/SolarWindPy/CLAUDE.md` § "Planning workflow"
  documents them as the planning workflow; retiring them is the author's decision and is held
  out of the phase-4 instruction until made.
- Do NOT delete `staged-recipes-fork/` while `git -C staged-recipes-fork log --branches --not --remotes`
  prints anything. It is untracked, so git holds no copy.

## Verification

```bash
cd /Users/balterma/observatories/code/SolarWindPy
conda run -n solarwindpy pytest -q 2>&1 | tail -1
conda run -n imap-loaders-20260225 pytest -q --no-header \
  --ignore=tests/plotting/test_performance.py --ignore=tests/test_issue_titles.py 2>&1 | tail -1
conda run -n solarwindpy pytest --doctest-modules solarwindpy -q 2>&1 | tail -1
conda run -n solarwindpy pre-commit run --all-files
grep -n 'requires-python' pyproject.toml
grep -nE '^SPHINXOPTS' docs/Makefile
git rev-list --count origin/master..master
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
