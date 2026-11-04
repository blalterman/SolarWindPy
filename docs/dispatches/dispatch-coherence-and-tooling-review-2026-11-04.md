<!--
Spent-When: MARKED(<self>)
Supersedes: none
-->

# Dispatch: Review SolarWindPy's agent tooling and code coherence, and plan the cleanup

author_signoff: none

owner: /Users/blalterman/observatories/code/SolarWindPy

**Generated:** 2026-11-04
**Branch:** master
**Work type:** software

## Governing Property

SolarWindPy reads as one design: each physical quantity, unit, and convention is defined once,
names predict what they hold, every layer predicts the one beneath it, and the tests mirror the
code they guard. The agent tooling that works on the package serves that design rather than
adding a parallel one.

## Purpose

Mechanism: code built up by many sessions and contributors accumulates parallel forms and copies,
and each copy drifts; agent tooling written for earlier models accumulates the same way, and its
instructions and hooks shape every later session whether or not they still fit. Local fix
programs improve parts without a frame for the whole.

Existing capability and what each leaves open:
- `lint-imports` with the contracts in `/Users/blalterman/observatories/code/SolarWindPy/pyproject.toml`
  § `[tool.importlinter]` enforces import direction between subpackages and acyclic siblings. It
  does not check naming, duplicated definitions, or whether one layer predicts the next.
- `/Users/blalterman/observatories/code/SolarWindPy/CLAUDE.md` § "Conventions" states "extract at
  the second copy" as a rule, with no detector.
- The test-quality program (`docs/dispatches/findings-test-quality-review-2026-10-02.md`,
  `docs/dispatches/dispatch-continue-test-quality-fixes-2026-10-05.md`) measures tests against the
  contracts they owe. It does not measure coherence between code and tests or across modules.
- Nothing evaluates `.claude/` against current Anthropic guidance or against Opus 5.5.

## Intent

When this lands, the author holds four things: an evaluation of every file of SolarWindPy's agent
tooling with a verdict for rebuilding it for Opus 5.5; a proposed `CLAUDE.md` aligned with
Anthropic's guidance; a layer-by-layer coherence review of the package and its tests; and a staged
cleanup plan, with every public-API change listed for the author's confirmation. No code, test,
or tooling file changes in this dispatch.

What makes it worth doing: the cleanup that follows can proceed stage by stage against named
findings instead of piecemeal, and the record shows how Claude worked under ISE's principles.

This work is also an experiment: it records how Claude responds to interaction surface
engineering (ISE) principles and how that response shapes its work on SolarWindPy. Confirm or
rewrite this reading before designing against it.

### Surface

The SolarWindPy package (`solarwindpy/`), its test suite (`tests/`), and its agent tooling
(`CLAUDE.md`, `.claude/`), as read by the author and by Claude sessions.

### Parties

The author, who holds the physics, the public API, and the why. The executing review session. The
control-arm subagent. Later cleanup sessions that execute the plan.

### Seam

The review reads, measures, and proposes. The author confirms every public-API change, every
change to a scientific result, the `CLAUDE.md` rewrite, the tooling rebuild, and the stage plan.
Judging whether the physics is correct belongs to the author; the review flags suspicions only.

### Layer

Whole-package architecture down to individual functions, the test tree that mirrors it, and the
agent-tooling layer. Not the experiments of any other repository, not the physics itself.

### Blast radius

Held stable: every file under `solarwindpy/`, `tests/`, `.claude/`, plus `CLAUDE.md` and
`pyproject.toml` (this dispatch writes only its two output files); the files of the in-flight
test-quality program; the three untracked items in the working tree.

## Motivation

- The author does not trust the agent tooling. Evidence a reader can re-check:
  `python3 -c 'import json; print(list(json.load(open(".claude/settings.json"))))'` lists
  top-level keys including `systemPrompt`, `tools`, `ai`, and `planningMode`; a `PostToolUse` hook
  runs `.claude/hooks/test-runner.sh --changed` after every Edit, MultiEdit, and Write; runtime
  state is tracked in git (`git ls-files .claude` includes `compacted_state.md`,
  `emergency-rollback.json`, `branch-preservation.log`, `logs/phase0-time-tracking.md`).
- `.claude/docs/` holds `wc -l .claude/docs/*.md | tail -1` lines of guidance beside `CLAUDE.md`.
- Earlier coherence efforts were piecemeal; the one systematic program covered test quality only.
- The prior review found a mis-pointed name in shipped code: `Vector.latitude` and
  `Vector.colatitude` were swapped (`docs/dispatches/findings-test-quality-review-2026-10-02.md`
  § "Author decisions recorded"). A mis-pointed name fails silently, which is the class of defect
  a coherence review exists to find.
- `git status --porcelain` shows three untracked items the author owns:
  `solarwindpy/fitfunctions/lines_BACKUP_41608.py`, `solarwindpy/plans/`, `solarwindpy/tests/`.

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

Outputs, the only files this dispatch writes:
- `/Users/blalterman/observatories/code/SolarWindPy/docs/dispatches/findings-coherence-and-tooling-review-2026-11-04.md`
- `/Users/blalterman/observatories/code/SolarWindPy/docs/dispatches/plan-coherence-cleanup-2026-11-04.md`

Scratch artifacts go under the git-ignored `tmp/coherence-review/`.

### The principles (judgment), each with the rules that guard it (binary)

Apply these as review lenses. They are untested as a theory of better code; treat them as ways
of looking, and record where one fails to fit.

- **P1. One home per fact.** Each constant, unit, column label, default, and formula is defined
  once. Guarded today by `CLAUDE.md` § "Conventions" ("extract at the second copy"). Rule: a
  proposed definition names the existing owner, or shows the search that found none.
- **P2. A name predicts its content, against its siblings.** Judge a name within its contrast set
  (the other names at the same layer), not alone. A mis-pointed name is worse than an opaque one
  because nothing flags it. Rule: renaming a public name is an API change, proposed only.
- **P3. Each layer predicts the next one down.** Subpackage layout predicts module layout; one
  class's API predicts its siblings'; the code tree predicts the test tree. Rule: at each layer,
  write the prediction before reading below, then record what was found.
- **P4. Each layer exposes only what the layer above needs.** Guarded today by `lint-imports` for
  import direction. Rule: the public API is the seam; changes to it are proposals only.
- **P5. Mirror an existing form before inventing one; repeat forms, never facts.** Rule: every
  proposed change names the `file:symbol` it mirrors, or states that no form fits and why.
- **P6. Density, not line count.** A consolidation counts only if it raises concepts per line.
  Rule: each cleanup stage states its expected density change and how it is measured.
- **P7. Done when it fits.** Rule: each stage states its done condition before it starts.
- **P8. The author holds the physics and the why.** Rule: changes to scientific results or public
  APIs are proposals; a behavior-preserving change needs a test that passes before and after.
- **P9. A claim carries its check.** Rule: every finding gives `path:line` and the command that
  reproduces it; every "found none" carries a positive control.

### Pass 0. Control arm (run first, before reading the principles into any brief)

Spawn one fresh `general-purpose` subagent (not a fork: a fork inherits this dispatch). Its brief,
verbatim: "Review the `solarwindpy/solar_activity/` subpackage of the repository at
/Users/blalterman/observatories/code/SolarWindPy and its tests under `tests/solar_activity/`.
Report code-quality problems with file and line, and propose a cleanup plan. Do not edit any file."
Save its report to `tmp/coherence-review/control-solar_activity.md` unread, before Pass 2 reaches
`solar_activity`.

### Pass 1. Agent tooling and `CLAUDE.md`

Fetch Anthropic's current guidance first (§ Read First items 9 and 10) and cite the URL for every
claim drawn from it. For every file in `git ls-files .claude` and for `CLAUDE.md`, record: what it
claims to do; whether anything registers or calls it (settings, pre-commit, CI); whether its keys
or syntax are valid per the docs; whether it duplicates `CLAUDE.md` or another file; and a verdict
for Opus 5.5 (keep, rebuild, retire) with the reason. Also cover the `.claude`-referencing hooks in
`.pre-commit-config.yaml`. Then write a proposed `CLAUDE.md` inside the findings file (a proposal,
not applied): only what a session cannot infer from the code, each line checked against the docs.

### Pass 2. Coherence review, layer by layer

Layers: the package; each subpackage (`core`, `fitfunctions`, `instabilities`, `plotting`,
`solar_activity`, `tools`, `examples`, `plans`); then modules, classes, and functions where the
layer above flags a problem; and the test tree against the code tree. At each layer write
`**Predicted:**` before reading below and `**Found:**` after. Apply P1 to P9. Take the
test-quality program's open units (`docs/dispatches/dispatch-continue-test-quality-fixes-2026-10-05.md`
§ Scope) as given: cite them where they overlap a finding instead of re-reviewing them.

### Pass 3. Staged cleanup plan

Write the plan file: stages ordered by dependency, each with its target files, the principle it
serves, the template it mirrors, its done condition, its expected density change, and the tests
that guard behavior before and after. List every public-API or scientific-result change in a
separate section for the author. Name which stages depend on the test-quality program's open units.

### Pass 4. Control comparison and experiment record

Compare Pass 2's `solar_activity` findings with the control report: overlap, findings only one arm
made, API changes proposed, scope of the proposed plans. Record in the findings file, for the whole
review: each finding's principle tag; counts of proposals versus escalations to the author; any
place a principle and a rule pulled apart; any template fit that was forced; and any self-assessed
claim later contradicted by verification. State that one run with one control subpackage cannot
establish that the principles caused any difference.

### Finding format

Every finding is one line:
`- **F<n>** [P<k>] \`path:line\`: what is wrong. Repro: \`command\``

## Observe First

```bash
cd /Users/blalterman/observatories/code/SolarWindPy
git branch --show-current
git status --porcelain
git ls-files .claude
python3 -c 'import json; d=json.load(open(".claude/settings.json")); print(list(d)); print(json.dumps(d.get("hooks"), indent=1))'
command grep -n "claude" .pre-commit-config.yaml
find solarwindpy -name '*.py' -not -path '*/__pycache__/*' | awk -F/ '{print $2}' | sort | uniq -c
find tests -name '*.py' | awk -F/ '{print $2}' | sort | uniq -c
pytest -q 2>&1 | tail -3
lint-imports 2>&1 | tail -5
```

## Read First

1. `/Users/blalterman/observatories/code/SolarWindPy/CLAUDE.md`: the current instructions every
   session loads; Pass 1 evaluates every line.
2. `/Users/blalterman/observatories/code/SolarWindPy/.claude/settings.json`: hooks and keys.
3. `/Users/blalterman/observatories/code/SolarWindPy/.claude/README.md`: what the tooling claims
   to provide.
4. `/Users/blalterman/observatories/code/SolarWindPy/.claude/docs/`: the guidance beyond
   `CLAUDE.md`, checked for duplication and staleness.
5. `/Users/blalterman/observatories/code/SolarWindPy/pyproject.toml` § `[tool.importlinter]`: the
   layer rule already enforced.
6. `/Users/blalterman/observatories/code/SolarWindPy/docs/dispatches/findings-test-quality-review-2026-10-02.md`:
   the prior review's method and findings, the pattern this review's findings file follows.
7. `/Users/blalterman/observatories/code/SolarWindPy/docs/dispatches/dispatch-continue-test-quality-fixes-2026-10-05.md`:
   the in-flight units this review must not duplicate.
8. `/Users/blalterman/observatories/code/SolarWindPy/solarwindpy/__init__.py`: the public surface.
9. `https://code.claude.com/docs/en/memory.md` and `https://code.claude.com/docs/en/best-practices.md`:
   what belongs in `CLAUDE.md` (what Claude cannot work out from the code; concrete, checkable
   lines; under 200 lines per file), what does not (architecture and file layout descriptions,
   emphasis such as IMPORTANT), and that a line which must never bend belongs in a hook or deny rule.
10. `https://code.claude.com/docs/en/claude-directory.md`, `https://code.claude.com/docs/en/hooks-guide.md`,
    `https://code.claude.com/docs/en/skills.md`, `https://code.claude.com/docs/en/sub-agents.md`:
    what belongs in `.claude/`, what is committed versus personal, and how hooks, skills, and
    agents are defined. The settings and hooks references were not checked when this dispatch was
    written: find them through `https://code.claude.com/docs/en/claude_code_docs_map.md` and fetch
    them before judging any `settings.json` key or hook event.

## Acceptance Criteria

Let `START` be `$(git log --format=%H --diff-filter=A -1 -- docs/dispatches/dispatch-coherence-and-tooling-review-2026-11-04.md)`, run in `/Users/blalterman/observatories/code/SolarWindPy`. Let `FIND` be `docs/dispatches/findings-coherence-and-tooling-review-2026-11-04.md` and `PLAN` be `docs/dispatches/plan-coherence-cleanup-2026-11-04.md`.

- [ ] No package, test, or tooling file changed: `git diff --stat $START..HEAD -- solarwindpy tests .claude CLAUDE.md pyproject.toml .pre-commit-config.yaml` → empty output
- [ ] Findings file has every section: `command grep -c -E '^## (Agent tooling|CLAUDE.md proposal|Coherence review|Control comparison|Experiment record)$' $FIND` → 5
- [ ] Every tooling file has a verdict: `for f in $(git ls-files .claude); do command grep -q "$f" $FIND || echo "no verdict: $f"; done` → no output
- [ ] Every finding is located and reproducible: `echo $(command grep -c '^- \*\*F[0-9]' $FIND) $(command grep -c -E '^- \*\*F[0-9]+\*\* \[P[0-9]\] `[^`]+:[0-9]+`: .* Repro: `' $FIND)` → two equal numbers above 0
- [ ] Every subpackage layer carries a prediction: `command grep -c '^\*\*Predicted:\*\*' $FIND` → 9 or more
- [ ] Control arm ran first and is saved: `test -s tmp/coherence-review/control-solar_activity.md && echo ok` → ok
- [ ] Plan stages are complete: `awk '/^### Stage/{s++} /^\*\*Done when:\*\*/{d++} /^\*\*Guarding tests:\*\*/{g++} /^\*\*Density:\*\*/{n++} END{print (s>0 && s==d && s==g && s==n) ? "ok " s : "FAIL " s" "d" "g" "n}' $PLAN` → `ok N`
- [ ] API and result changes listed for the author: `command grep -c '^## Changes for author confirmation$' $PLAN` → 1
- [ ] Both outputs lint clean: `bash ~/.claude/tools/lint-ai-clean.sh $FIND $PLAN` → "All files clean."
- [ ] Suite unchanged and green: `pytest -q 2>&1 | tail -1` → a passed count, 0 failed

## Anti-Patterns

- Do NOT edit any file under `solarwindpy/`, `tests/`, `.claude/`, or `CLAUDE.md`. This dispatch
  proposes; the author confirms before any change.
- Do NOT treat output from this repository's hooks as authoritative. The `PostToolUse` test runner
  and the `Stop` coverage monitor will fire during this session; they are among the tools under
  evaluation.
- Do NOT write the control arm's brief from the principles, and do NOT read its report before
  Pass 2 reaches `solar_activity`. Either one contaminates the comparison.
- Do NOT re-review units the test-quality program owns; cite them.
- Do NOT touch `solarwindpy/fitfunctions/lines_BACKUP_41608.py`, `solarwindpy/plans/`, or
  `solarwindpy/tests/`. They are the author's untracked work; report them, nothing more.
- Do NOT state a claim about Anthropic's guidance without the URL it came from.
- Do NOT run `python3 -m pytest`; `CLAUDE.md` § "Commands" explains the 25 spurious failures.
- Do NOT use plain `grep -r`; the shell shim skips ignored paths. Use `command grep` or `git grep`.

## Verification

```bash
cd /Users/blalterman/observatories/code/SolarWindPy
START=$(git log --format=%H --diff-filter=A -1 -- docs/dispatches/dispatch-coherence-and-tooling-review-2026-11-04.md)
FIND=docs/dispatches/findings-coherence-and-tooling-review-2026-11-04.md
PLAN=docs/dispatches/plan-coherence-cleanup-2026-11-04.md
git diff --stat $START..HEAD -- solarwindpy tests .claude CLAUDE.md pyproject.toml .pre-commit-config.yaml
command grep -c -E '^## (Agent tooling|CLAUDE.md proposal|Coherence review|Control comparison|Experiment record)$' $FIND
command grep -c '^\*\*Predicted:\*\*' $FIND
awk '/^### Stage/{s++} /^\*\*Done when:\*\*/{d++} END{print s, d}' $PLAN
bash ~/.claude/tools/lint-ai-clean.sh $FIND $PLAN
pytest -q 2>&1 | tail -1
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
