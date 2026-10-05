<!--
Spent-When: MARKED(<self>)
Supersedes: none
-->

# Dispatch: finish the test-quality fix program and draft the revised adoption plan

author_signoff: none

owner: /Users/balterma/observatories/code/SolarWindPy

**Generated:** 2026-10-05
**Branch:** master
**Work type:** software

## Governing Property

Every change that lands in SolarWindPy is one the author reviewed, and every test and documented
example it adds states something true and checkable about the package.

## Purpose

Parallel unit subagents share one GitHub remote and one main checkout. Without held gates they
merge unreviewed work, collide on shared files, stall, or ship docstrings that fail the CI docs
build. Three mechanisms produce that cost:

- The author's git sets `push.default=upstream`. A branch created from `origin/master` tracks
  master, so a plain `git push` lands the commit on master with no pull request.
- Two units that both list a file in `OWNS:` (CHANGELOG.md included) produce conflicting pull
  requests.
- CI builds the docs with warnings as errors (`-W`); a unit that runs only the test suites ships a
  docstring that fails that build.

Existing capability and its limit:

- `/Users/balterma/observatories/code/SolarWindPy/docs/dispatches/batch-test-quality-fixes-2026-10-02.md`
  partitions the work into units with disjoint `OWNS:` lines and states every author decision; it
  does not run them.
- The Agent tool's `isolation: "worktree"` separates units' files; it does not hold review gates
  or push targets.
- The project memories
  `/Users/balterma/.claude/projects/-Users-balterma-observatories-code-SolarWindPy/memory/feedback_push-explicit-refspec.md`
  and
  `/Users/balterma/.claude/projects/-Users-balterma-observatories-code-SolarWindPy/memory/feedback_subagent-limits.md`
  state the push rule and the subagent rules; nothing applies them in a run except the brief.

Nothing carries the remaining sequence, the gates, and these rules into a new session; this
dispatch does.

## Intent

When this dispatch is done, every remaining unit of the fix program has landed through a pull
request the author reviewed and merged, the mutation re-measurement is recorded, the test-quality
track is closed and its documents retired, and a revised Spent-When adoption plan waits for the
author's approval.

The observable difference: `gh pr list --state open` shows no `tq-fix/` pull request, the findings
file holds the full re-measurement, and the next track starts from a plan measured against today's
repository.

Confirm or rewrite this reading before designing against it. Every step below inherits from it.

### Surface

Launching and monitoring unit subagents, each in its own git worktree and branch; the status
column of the work-plan doc at
`https://claude.ai/code/artifact/67c0a7fb-bd30-4832-893c-98105dff9358`; orchestration records,
the findings re-measurement, and the revised adoption plan in `docs/dispatches/`. The orchestrating
session edits no package code or test itself.

### Parties

- The author, who reviews and merges every pull request and decides physics.
- This orchestrating session.
- The unit subagents.
- The researcher who installs SolarWindPy and relies on what it computes.

### Seam

This session decides launch order within the gates, how many units run at once (at most
`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`), relaunching a stalled unit, pull-request monitoring, and
triage of the automated Claude PR reviews (verify each claim against the code before acting). The
author decides every merge, every removal, physics, the `HingeMax` fallback start point, and any
new tolerance kind.

### Layer

Coordinating execution. What each test asserts is the unit's layer; physics is the author's.

### Blast radius

Unit branches pushed and pull requests opened, never merged by this session or a unit; worktrees
created and removed; status updates in the work-plan doc; local commits of orchestration records,
pushed with the author's approval each time.

## Motivation

- Merged fix-program pull requests:
  `gh pr list --state merged --limit 300 --json headRefName --jq '[.[]|select(.headRefName|startswith("tq-fix/"))]|length'`
  printed 18 when this dispatch was written.
- The open pull request:
  `gh pr list --state open --json number,headRefName --jq '.[]|"\(.number) \(.headRefName)"'`
  printed `493 tq-fix/tolerance-helpers` when this dispatch was written. It routes every
  hand-written test tolerance through `tests/tolerances.py` and tightens about 15 of them; none
  were loosened.
- Units not yet run, each specified in the batch file: `p0-simplify`, `scalar-w-nan`, and the
  long-running `mutation-recheck`.
  `grep -nE '^### (p0-simplify|scalar-w-nan|mutation-recheck)$' /Users/balterma/observatories/code/SolarWindPy/docs/dispatches/batch-test-quality-fixes-2026-10-02.md`
  prints three headings.
- The suite's warning count rose from 6 to 20 with PR #491 (`p0-contract`):
  `conda run -n solarwindpy pytest -q 2>&1 | grep -oE '[0-9]+ warnings'`. Nobody has read them.
- Agent worktrees from completed units: `git worktree list | grep -c '.claude/worktrees/agent-'`.

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

Execute in this order. A step that waits on a merge waits for the author.

1. **PR #493 (`tolerance-helpers`).** Read its latest Claude review
   (`gh pr view 493 --json comments --jq '[.comments[]|select(.author.login=="claude")]|last|.body'`),
   verify each claim against the code, and send confirmed fixes to a resumed or fresh agent on the
   same branch. Put two questions to the author: whether the agent's `printed(actual/expected,
   decimals=...)` ratio form becomes a fifth named tolerance kind, and whether bare
   `pytest.approx(x)` calls (no tolerance keyword, so pytest's `abs=1e-12` default applies) join
   the enforcing test. Watch CI for intermittent failures in the fit-result checks it tightened to
   `exact`; such a failure means a tolerance too tight for an optimizer result, and goes to the
   author.
2. **After #493 merges, launch `p0-simplify` and `scalar-w-nan` in parallel.** Their `OWNS:` lines
   in the batch file are disjoint; `p0-simplify` also owns CLAUDE.md and CHANGELOG.md, so give
   `scalar-w-nan` its CHANGELOG entry only after `p0-simplify` merges, or drop CHANGELOG from one
   brief. Each brief: point the agent at the batch file's "Governance", "Every unit", and its own
   unit section; include the push-safety block from § Anti-Patterns; require the docs build; cap
   its final report at about 25 lines.
3. **After each merge:** `git fetch origin`, merge `origin/master` into local master (no rebase of
   shared history), run `conda run -n solarwindpy pytest -q` and
   `conda run -n solarwindpy pytest --doctest-modules solarwindpy -q`, and set the unit's Status
   dropdown to Merged in the work-plan doc. A red suite stops further merges and goes to the author
   with the failing test.
4. **Read the 20 warnings** (read-only): `conda run -n solarwindpy pytest -q -rw` and report each
   source in one line. A warning from package code that a decided rule covers (for example an
   empty-sum or divide-by-zero case) becomes a fix in the next unit; any other goes to the author.
5. **`mutation-recheck`**, after `p0-simplify` and `scalar-w-nan` merge. It runs in the main
   checkout with no worktree, writing only under `tmp/test-quality-review/mutmut/`, because its
   inputs live in the git-ignored `tmp/test-quality-review/`. `run_mutmut.sh` mutates an isolated
   copy under `tmp/test-quality-review/mutmut/<slug>/`, never the working tree. Back up
   `tmp/test-quality-review/mutants_recheck.csv` to `mutants_recheck-2026-10-02.csv` before
   rerunning (the script truncates it). Record the results under a `### Mutation` subsection of
   `## Re-measurement (2026-10-05)` in
   `/Users/balterma/observatories/code/SolarWindPy/docs/dispatches/findings-test-quality-review-2026-10-02.md`,
   next to `### Linkcheck`, and commit.
6. **`HingeMax` fallback point.** When the author supplies it, run a small unit that replaces the
   `NotImplementedError` in `HingeMax.p0` (after `p0-simplify`, the branch that raises lives in
   `p0`) with the author's point.
7. **Close the track.** Run `/session:empirical-findings` on
   `/Users/balterma/observatories/code/SolarWindPy/docs/dispatches/dispatch-test-quality-review-2026-10-02.md`
   only if its Governing Property now holds on the evidence; otherwise report what is left. Propose
   `/session:reap` for that review dispatch, the findings file, and the batch file as one batch for
   the author's approval. Remove every agent worktree (`git worktree remove <path>` for each line
   of `git worktree list | grep '.claude/worktrees/agent-'`, then `git worktree prune`), and delete
   local branches named `tq-fix/*` or `worktree-agent-*` whose pull request is merged.
8. **Draft the revised adoption plan.** Re-measure every count in
   `/Users/balterma/observatories/code/SolarWindPy/docs/dispatches/plan-spent-when-adoption-2026-09-16.md`
   (tracked files, inline and sidecar carriers, register rows), each with its command, after step 7
   so the counts reflect the removals. Write
   `docs/dispatches/plan-spent-when-adoption-<YYYY-MM-DD>.md`, rendering its declaration with
   `spent_when.py --emit` and naming the old plan in `--supersedes`. Commit locally and stop for the
   author's approval.

Status updates use the Claude Docs tools: read
`read( ref = {"object":"project","id":"67c0a7fb-bd30-4832-893c-98105dff9358"} )`, then the "Fix
program units" table, then change a unit's Status dropdown (enum `6c21622c-9236`: Not started, In
progress, PR open, Merged, Blocked) in its row.

## Read First

1. `/Users/balterma/observatories/code/SolarWindPy/docs/dispatches/batch-test-quality-fixes-2026-10-02.md`:
   every unit's `OWNS:` line and author decisions; the sections each unit brief points to.
2. `/Users/balterma/observatories/code/SolarWindPy/docs/dispatches/findings-test-quality-review-2026-10-02.md`:
   the baseline numbers and the `## Re-measurement (2026-10-05)` section step 5 extends.
3. `/Users/balterma/observatories/code/SolarWindPy/.claude/docs/TEST_PATTERNS.md`: the test standard
   every unit writes to; after #493 merges it points to `tests/tolerances.py`.
4. `/Users/balterma/.claude/projects/-Users-balterma-observatories-code-SolarWindPy/memory/feedback_push-explicit-refspec.md`
   and
   `/Users/balterma/.claude/projects/-Users-balterma-observatories-code-SolarWindPy/memory/feedback_subagent-limits.md`:
   the two rules every brief carries.
5. `/Users/balterma/observatories/code/SolarWindPy/docs/dispatches/plan-spent-when-adoption-2026-09-16.md`:
   the plan step 8 revises.

## State Verification

```bash
cd /Users/balterma/observatories/code/SolarWindPy
git fetch -q origin
git rev-list --count origin/master..master        # expect 0
git rev-list --count master..origin/master        # expect 0
git status --porcelain | grep -v '^??'            # expect no output
gh pr list --state open --json number,headRefName --jq '.[]|"\(.number) \(.headRefName)"'   # expect 493 tq-fix/tolerance-helpers, or nothing once it merged
grep -cE '^### (p0-simplify|scalar-w-nan|mutation-recheck)$' docs/dispatches/batch-test-quality-fixes-2026-10-02.md   # expect 3
echo "$CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS"      # the concurrency cap
git config --get push.default                     # expect upstream: every push uses an explicit refspec
conda run -n solarwindpy pytest -q 2>&1 | grep -E '[0-9]+ (passed|failed)' | tail -1   # expect 0 failed
```

## Acceptance Criteria

Run from `/Users/balterma/observatories/code/SolarWindPy`. Each criterion carries a positive
control showing the check can fire.

- [ ] Three remaining units merged: `gh pr list --state merged --limit 300 --json headRefName --jq '[.[]|.headRefName|select(.=="tq-fix/tolerance-helpers" or .=="tq-fix/p0-simplify" or .=="tq-fix/scalar-w-nan")]|length'` → 3. Control: the same command with only `"tq-fix/no-such-unit"` → 0.
- [ ] No fix-program pull request open: `gh pr list --state open --limit 200 --json headRefName --jq '[.[]|select(.headRefName|startswith("tq-fix/"))]|length'` → 0. Control: the same command with `--state all` → 21 or more once both remaining units opened their pull requests.
- [ ] Suite green: `conda run -n solarwindpy pytest -q 2>&1 | grep -E '[0-9]+ (passed|failed)' | tail -1` → contains `passed`, no `failed`. Control: the same grep on `tmp/test-quality-review/baseline_run.txt` prints the pre-fix summary line.
- [ ] Docs build green: `make -C docs html SPHINXOPTS="-W --keep-going -n" BUILDDIR=$(mktemp -d) 2>&1 | tail -1` → contains `build succeeded`. Control: the CI log of PR #491's first push failed this build.
- [ ] `fallback_p0` private: `grep -rc 'def fallback_p0' solarwindpy/fitfunctions/ | awk -F: '{s+=$2} END {print s}'` → 0, and `grep -c 'def _fallback_p0' solarwindpy/fitfunctions/core.py` → 1. Control: before `p0-simplify`, the first command → 7.
- [ ] Stale CLAUDE.md pointer gone: `grep -c 'plasma.py:102' CLAUDE.md` → 0. Control: before `p0-simplify` → 1.
- [ ] Mutation re-measurement recorded: `grep -c '^### Mutation' docs/dispatches/findings-test-quality-review-2026-10-02.md` → 1. Control: `grep -c '^### Linkcheck' docs/dispatches/findings-test-quality-review-2026-10-02.md` → 1.
- [ ] Agent worktrees removed: `git worktree list | grep -c '.claude/worktrees/agent-'` → 0. Control: before step 7 → 1 or more.
- [ ] Revised adoption plan drafted: `grep -l 'Supersedes: .*plan-spent-when-adoption-2026-09-16' docs/dispatches/plan-spent-when-adoption-*.md` → one path other than the 2026-09-16 plan. Control: `head -4 docs/dispatches/plan-spent-when-adoption-2026-09-16.md | grep -c 'Supersedes: none'` → 1.

## Anti-Patterns

- Do NOT run a plain `git push`, and do NOT create a branch with `git checkout -b <b> origin/master` without `--no-track`. With `push.default=upstream` the branch tracks master and the push lands on master unreviewed; this happened once in this program and needed a revert pull request. Every brief carries: `git checkout --no-track -b tq-fix/<unit> origin/master`, push only with `git push -u origin HEAD:refs/heads/tq-fix/<unit>`, and confirm `git rev-parse --abbrev-ref --symbolic-full-name @{u}` names the unit's own branch.
- Do NOT give two concurrent units the same file in `OWNS:`, CHANGELOG.md included. Two units once both owned it and risked a conflict on whichever merged second.
- Do NOT let a unit skip the docs build when it edits a docstring. PR #491 failed CI on 11 unqualified Sphinx references that the test suites passed. The build command that avoids the guard's false positive: `make -C docs html SPHINXOPTS="-W --keep-going -n" BUILDDIR=<mktemp -d dir>`, with no `make clean`.
- Do NOT name the path `docs/source` on a unit's shell command line. The worktree guard misreads it as the shell builtin `source` and refuses the command. Units read files there with file tools.
- Do NOT treat a guard refusal of a command's shape (compound commands, heredocs, `sed` with a runtime value) as a permission denial. The guard names a plain alternative; the author accepts following it. A refusal of a permission itself stops the unit, which reports the exact message.
- Do NOT act on an automated Claude review claim without checking it against the code. In this program several claims described stale heads or misread the code.
- Do NOT merge a pull request, and do NOT edit package code or tests in this session. Merging is the author's; code and tests are the units'.
- Do NOT let a unit's final report run long. Cap it at about 25 lines in the brief; the orchestrating context is spent on reports.
- Do NOT run `rm -rf` or inline `python -c` in a unit. Scratch files go in a `mktemp -d` directory outside the repo.

## Verification

```bash
cd /Users/balterma/observatories/code/SolarWindPy
gh pr list --state all --limit 300 --json number,state,headRefName --jq '.[]|select(.headRefName|startswith("tq-fix/"))|"\(.number) \(.state) \(.headRefName)"'
conda run -n solarwindpy pytest -q 2>&1 | grep -E '[0-9]+ (passed|failed)' | tail -1
conda run -n solarwindpy pytest --doctest-modules solarwindpy -q 2>&1 | grep -E '[0-9]+ (passed|failed)' | tail -1
git worktree list
ls docs/dispatches/
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
