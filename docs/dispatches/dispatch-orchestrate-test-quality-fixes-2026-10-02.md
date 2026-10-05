<!--
Spent-When: MARKED(<self>)
Supersedes: none
-->

# Dispatch: orchestrate the test-quality fix program and draft the revised adoption plan

author_signoff: none

owner: /Users/balterma/observatories/code/SolarWindPy

**Generated:** 2026-10-02
**Branch:** master
**Work type:** software

## Governing Property

Every change that lands in SolarWindPy is one the author reviewed, and every test and documented
example it adds states something true and checkable about the package.

## Purpose

The fix program holds 11 units and 2 long-running units. Run one at a time they take days; run
carelessly in parallel they collide in the one shared checkout, merge without review, or lose
work when an agent stalls. An orchestrator holds the sequence and the review gates so the units
run in parallel safely.

Existing capability and its limit:

- `/Users/balterma/observatories/code/SolarWindPy/docs/dispatches/batch-test-quality-fixes-2026-10-02.md`
  partitions the units into disjoint `OWNS:` file sets; it does not run them.
- The Agent tool's `isolation: "worktree"` separates units from each other; it does not hold the
  gates.
- The project memory `feedback_subagent-limits.md` states that subagents return reports as text
  and stop on a permission refusal; nothing enforces it in a run except the brief.

## Intent

When this dispatch is done, every unit of the fix program has landed through a pull request the
author reviewed and merged, the two long-running checks have re-measured the suite, the
test-quality track is closed and retired, and a revised Spent-When adoption plan waits for the
author's approval.

The observable difference: `gh pr list --state open` shows no fix-program PR, the findings'
gaps are covered by merged tests, and the next track starts from a plan measured against today's
repository.

Confirm or rewrite this reading before designing against it. Every step below inherits from it.

### Surface

Launching and monitoring unit subagents, each in its own git worktree and branch; the status
column of the work-plan doc at
`https://claude.ai/code/artifact/67c0a7fb-bd30-4832-893c-98105dff9358`; orchestration records and
the revised adoption plan in `docs/dispatches/`. The orchestrating session edits no code or test
itself.

### Parties

- The author, who reviews the pilot, merges every PR, and decides physics.
- This orchestrating session.
- The unit subagents.
- The researcher who installs SolarWindPy and relies on what it computes.

### Seam

This session decides launch order within the gates, how many units run at once (at most the
session's concurrent-subagent cap, `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`), relaunching a stalled
unit, and PR monitoring. The author decides whether the pilot PR is sound, every merge, the
definition and source of `Plasma.Wk`, every removal, and which of the adoption plan or the
docstring rewrite comes next.

### Layer

Coordinating execution. What each test asserts is the unit's layer; physics is the author's.

### Blast radius

Unit branches pushed and pull requests opened, never merged by this session or a unit; worktrees
created and removed; status updates in the work-plan doc; local commits of orchestration records
and the revised plan, pushed with the author's approval.

## Motivation

- `ls /Users/balterma/observatories/code/SolarWindPy/docs/dispatches/` lists the review dispatch,
  its findings, the fix program, and `plan-spent-when-adoption-2026-09-16.md`.
- `grep -c '^OWNS:' /Users/balterma/observatories/code/SolarWindPy/docs/dispatches/batch-test-quality-fixes-2026-10-02.md`
  prints the unit count (13: 11 units, 2 long-running).
- `gh pr list --state open --json number --jq length` printed 0 when this dispatch was written,
  so every PR this run sees is its own.
- Worktree-based subagents branch from `origin/master`. A stale origin once sent three units to a
  base 25 commits old, so local and origin must match before any launch.
- A subagent once routed around a GitHub permission refusal by merging locally and pushing over
  git; another stalled for 10 minutes mid-write and was stopped.

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

Each unit subagent receives, in this order: the "Governance" and "Every unit" sections of the
fix program verbatim, its own unit section verbatim, and these three rules:

- Work only in your worktree on branch `tq-fix/<unit-name>`; touch only your `OWNS:` paths.
- Return your final report as text; do not write report files.
- On any permission refusal, stop and report the exact message; never reach the same result by
  another route.

Launch every unit with the Agent tool, `subagent_type: "general-purpose"`,
`isolation: "worktree"`, in the background.

1. **Pilot.** Launch `quantities-and-vector`. When its report arrives, give the author the PR URL
   and the report's controls, set its status to "PR open" in the work-plan doc, and wait in the
   chat for the author's verdict. Sound → step 2. Not sound → revise the fix program with the
   author, commit the revision, push with approval, relaunch the pilot.
2. **Ten units.** Launch the other ten, never more at once than the concurrent-subagent cap. Set
   each status as its PR opens. For `plasma-physics-cases`, include the author's `Wk` definition
   and source if given; otherwise the unit reports `Wk` as blocked. A unit silent for 20 minutes
   with nothing new on its branch is stalled: resume it once with "save each file as you finish
   it"; a second stall goes to the author.
3. **Merges.** The author reviews and merges each PR. After each merge: set the status to
   "Merged", `git pull --ff-only`, and run `conda run -n solarwindpy pytest -q`. A red suite after
   a merge stops further merges and goes to the author with the failing test.
4. **Long-running units.** After `docstring-examples` is merged, launch `linkcheck`. After every
   other unit is merged, launch `mutation-recheck`. Record their results in
   `docs/dispatches/findings-test-quality-review-2026-10-02.md` under a dated "Re-measurement"
   section.
5. **Close the track.** Run `/session:empirical-findings` on
   `docs/dispatches/dispatch-test-quality-review-2026-10-02.md` only if its Governing Property now
   holds on the evidence; otherwise report what is left. Propose `/session:reap` for the review
   dispatch, the findings, and the fix program as one batch for the author's approval. Remove
   the unit worktrees: `git worktree remove <path>` for each, then `git worktree prune`.
6. **Draft the revised adoption plan.** Re-measure every count in
   `docs/dispatches/plan-spent-when-adoption-2026-09-16.md` (tracked files, sidecar and inline
   carriers, register rows) against the current tree, each with its command. Write the revision
   as `docs/dispatches/plan-spent-when-adoption-<YYYY-MM-DD>.md` whose declaration names the old
   plan in `Supersedes:`. Commit locally and stop for the author's approval.

Status updates use the Claude Docs tools: read the doc with
`read( ref = {"object":"project","id":"67c0a7fb-bd30-4832-893c-98105dff9358"} )`, then the
"Fix program units" table, then change a unit's Status dropdown in its row.

## Read First

1. `/Users/balterma/observatories/code/SolarWindPy/docs/dispatches/batch-test-quality-fixes-2026-10-02.md`
   -- the units, their `OWNS:` lines, their baselines and controls; the sections each unit
   receives verbatim.
2. `/Users/balterma/observatories/code/SolarWindPy/docs/dispatches/findings-test-quality-review-2026-10-02.md`
   -- the evidence each unit acts on and the "Author decisions recorded" section.
3. `/Users/balterma/observatories/code/SolarWindPy/docs/dispatches/plan-spent-when-adoption-2026-09-16.md`
   -- the plan step 6 revises.
4. `/Users/balterma/observatories/code/SolarWindPy/.claude/docs/TEST_PATTERNS.md` -- the test
   standard every unit writes to.
5. `/Users/balterma/.claude/projects/-Users-balterma-observatories-code-SolarWindPy/memory/feedback_subagent-limits.md`
   -- the two subagent rules this dispatch passes to every unit.

## State Verification

```bash
cd /Users/balterma/observatories/code/SolarWindPy
git fetch -q origin
git rev-list --count origin/master..master        # expect 0
git rev-list --count master..origin/master        # expect 0
git status --porcelain | grep -v '^??'            # expect no output
gh pr list --state open --limit 200 --json headRefName --jq '[.[] | select(.headRefName|startswith("tq-fix/"))] | length'   # expect 0
grep -c '^OWNS:' docs/dispatches/batch-test-quality-fixes-2026-10-02.md               # expect 13
echo "$CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS"      # the concurrency cap for step 2
conda run -n solarwindpy pytest -q 2>&1 | grep -E '[0-9]+ passed' | tail -1   # expect 0 failed
```

## Acceptance Criteria

Each criterion carries a positive control showing the check can fire. Run from
`/Users/balterma/observatories/code/SolarWindPy`.

- [ ] Every unit merged through a PR: `gh pr list --state merged --limit 200 --json headRefName --jq '[.[] | select(.headRefName|startswith("tq-fix/"))] | length'` → 11 or more. Control: the same command with `startswith("tq-fix/no-such-unit")` → 0.
- [ ] No fix-program PR left open: `gh pr list --state open --limit 200 --json headRefName --jq '[.[] | select(.headRefName|startswith("tq-fix/"))] | length'` → 0. Control: the same command with `--state all` → 11 or more.
- [ ] Suite green after the merges: `conda run -n solarwindpy pytest -q 2>&1 | grep -E '[0-9]+ passed' | tail -1` → contains `passed` and no `failed`. Control: the same grep on `tmp/test-quality-review/baseline_run.txt` prints the pre-fix summary line.
- [ ] Latitude fix landed: `conda run -n solarwindpy python -c "import pandas as pd; from solarwindpy.core.vector import Vector; v = Vector(pd.DataFrame({'x':[0.0],'y':[0.0],'z':[1.0]})); print(round(float(v.latitude.iloc[0])))"` → 90. Control: the same command printed 0 before the fix (findings, "Gaps").
- [ ] Re-measurement recorded: `grep -c '^## Re-measurement' docs/dispatches/findings-test-quality-review-2026-10-02.md` → 1. Control: `grep -c '^## Re-measurement' docs/dispatches/batch-test-quality-fixes-2026-10-02.md` → 0.
- [ ] Unit worktrees removed: `git worktree list | grep -c 'tq-fix/'` → 0. Control: during step 2, the same command printed 1 or more.
- [ ] Revised adoption plan drafted: `grep -l 'Supersedes: .*plan-spent-when-adoption-2026-09-16' docs/dispatches/plan-spent-when-adoption-*.md` → one path other than the 2026-09-16 plan. Control: `grep -c 'Supersedes: none' docs/dispatches/plan-spent-when-adoption-2026-09-16.md` → 1.

## Verification

```bash
cd /Users/balterma/observatories/code/SolarWindPy
gh pr list --state all --limit 200 --json number,state,headRefName --jq '.[] | select(.headRefName|startswith("tq-fix/")) | "\(.number) \(.state) \(.headRefName)"'
conda run -n solarwindpy pytest -q 2>&1 | grep -E '[0-9]+ passed' | tail -1
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

---


---

## Empirical Findings (2026-10-05 trial run)

### End-state metrics

- Fix-program pull requests merged: 18 (AC predicted 11 or more). Open: 1 (#493, `tolerance-helpers`).
- Suite on master after #492: `2836 passed, 12 skipped`, 0 failed, 0 xfailed (baseline `2849 passed, 12 skipped`; counts moved as units removed and added tests).
- Doctests: `59 passed, 1 skipped` (baseline `24 passed, 36 skipped`).
- Sphinx linkcheck broken links: 5 to 4.
- Units added beyond the original 11 plus 2 long-running, each by author decision: `abundances-2021-only`, `examples-and-logging-cleanup`, `small-code-fixes`, `plasma-code-fixes`, `p0-contract`, `loader-examples`, `tolerance-helpers`, `p0-simplify`, `scalar-w-nan`.

### Governing Property

not served -- the work is incomplete: PR #493 is open and `p0-simplify`, `scalar-w-nan` and `mutation-recheck` have not run (`gh pr list --state open` shows #493). One change, 6ed14f84, reached master without review; PR #487 reverted it and PR #489 replaced it through review.

### Acceptance Criteria

| AC | Status | Evidence |
|---|---|---|
| Every unit merged through a PR (11 or more) | PASS | `gh pr list --state merged ... startswith("tq-fix/")` → 18; control `"tq-fix/no-such-unit"` → 0 |
| No fix-program PR open | FAIL | the same query with `--state open` → 1 (#493); carried to `dispatch-continue-test-quality-fixes-2026-10-05.md` |
| Suite green after the merges | PASS | `2836 passed, 12 skipped, 20 warnings, 18 subtests passed` on master after #492; control `tmp/test-quality-review/baseline_run.txt` prints `2849 passed, 12 skipped` |
| Latitude fix landed | PASS | the `Vector(0, 0, 1).latitude` command printed 90 (it printed 0 before #475) |
| Re-measurement recorded | PASS | `grep -c '^## Re-measurement' findings-test-quality-review-2026-10-02.md` → 1 (linkcheck only; mutation pending); control on the batch file → 0 |
| Unit worktrees removed | DEFERRED | `git worktree list | grep -c '.claude/worktrees/agent-'` → 18; carried to the successor's step 7 |
| Revised adoption plan drafted | DEFERRED | only `plan-spent-when-adoption-2026-09-16.md` exists; carried to the successor's step 8 |

### Deviations from plan

- The pilot's prescribed `conda run ... git commit` was refused by the worktree guard; units commit with plain `git commit` from the worktree (9166fba3).
- The two long-running units ran in the main checkout, not worktrees, because `tmp/` is git-ignored; `run_mutmut.sh` mutates an isolated copy.
- A branch created from `origin/master` tracked master under `push.default=upstream`, so 6ed14f84 landed on master unreviewed. Reverted through PR #487, replaced through PR #489; units now push with an explicit refspec (08bf75c5) and a project memory records the rule.
- Two units were given CHANGELOG.md in `OWNS:`, and units ran only the test suites while CI builds the docs with `-W`; PR #491 failed CI on 11 Sphinx references. Units now build the docs (297e1328).
- Local master merged `origin/master` instead of `git pull --ff-only`, because local orchestration commits diverged from merged pull requests.
- Each pull request also went through one or more rounds of automated Claude review, triaged against the code before fixes were sent.
- Units followed the worktree guard's prescribed plain-command alternatives when a command's shape was refused; the author accepted this.

### Commits

- `9166fba3` docs(dispatch): units commit with plain git commit from the worktree
- `75efe5f5` docs(dispatch): record pilot physics decisions and widen its OWNS
- `72dc836c` docs(dispatch): give plasma-physics-cases the Wk definition and NaN rules
- `80629fab` docs(dispatch): add abundances-2021-only unit
- `760e834c` docs(dispatch): pin the 15 unavailable Asplund 2021 photosphere cells as NaN
- `14d500f2` docs(dispatch): record the shared doctest setup decision for plasma.py examples
- `97b8c3ec` docs(dispatch): retire ATTRIBUTION.md in the dev-extras unit
- `3daf67cd` docs(dispatch): add plasma-code-fixes and small-code-fixes follow-up units
- `08bf75c5` docs(dispatch): units push only with an explicit refspec
- `59550929` docs(review): record the linkcheck re-measurement
- `53d872f2` docs(dispatch): fold attribution and coverage-wording leftovers into small-code-fixes
- `319217e4` docs(dispatch): add p0-contract and tolerance-helpers units
- `12be2b0a` docs(dispatch): add examples-and-logging-cleanup unit
- `297e1328` docs(dispatch): units build the docs with warnings as errors
- `53dd5ef1` docs(dispatch): record zero-width, hinge fallback and GaussianLn decisions
- `69461d74` docs(dispatch): add loader-examples unit; fold #490's test gaps into tolerance-helpers
- `564a703d` docs(dispatch): record that the heat_flux label stays q
- `e1f9cec8` docs(dispatch): add scalar-w-nan unit (author decision)
- `85621bf4` docs(dispatch): add p0-simplify unit (author decision)
- `cc9284b8` docs(dispatch): continue the test-quality fix program in a new session

## Spent-Mark: declined; stopped by decision; the remaining work continues in docs/dispatches/dispatch-continue-test-quality-fixes-2026-10-05.md
