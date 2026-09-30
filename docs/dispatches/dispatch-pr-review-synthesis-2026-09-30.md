<!--
Spent-When: MARKED(<self>)
Supersedes: none
-->

# Dispatch: synthesize Claude's review feedback on phase-4 PRs #446-#469

author_signoff: none

owner: /Users/balterma/observatories/code/SolarWindPy

**Generated:** 2026-09-30
**Branch:** master
**Work type:** software

## Governing Property

Every claim this repository makes is warranted or bounded. Review feedback is a set of
claims about the code: each point is acted on, rejected with a stated reason, or bounded to
a named later step.

## Purpose

Complete the SolarWindPy work plan the author defined in the phase-4 work plan artifact
(https://claude.ai/code/artifact/1b4223f7-a580-4c84-a438-f3b5e0dc8963). The next step of
that plan is working through the PR review feedback.

## Intent

Every point in the 24 Claude review comments on PRs #446-#469 carries exactly one recorded
disposition: fix before merge (naming the PR branch it goes on), follow-on after merge,
reject with a reason, or author decision. The fixes the author approves are applied as new
commits on the PR branches, and a re-run of the combined check stays green, so the author
can merge all 24.

The observable difference: the author merges the 24 PRs knowing what each review comment
asked for and what happened to it, instead of reading 24 comments one at a time.

Confirm or rewrite this reading with the author before designing against it.

### Surface

The 24 PR branches #446-#469, their Claude review comments, and one synthesis plan file at
`/Users/balterma/observatories/code/SolarWindPy/plans/pr-review-synthesis-2026-09-30.md`.

### Parties

The author decides every disposition, approves the plan, and performs every merge. The
executing session reads the comments, synthesizes them, and proposes dispositions and fixes.
Subagents apply approved per-PR fixes. The `claude-review` GitHub action
(`/Users/balterma/observatories/code/SolarWindPy/.github/workflows/claude-code-review.yml`)
is the source of the feedback.

### Seam

The session proposes and the author approves. Physics values, methodology choices, and plot
label wording go to the author. Nothing merges without the author.

### Layer

Pre-merge fixes are new commits on the PR branches; no force-push. Post-merge follow-ons are
planned in the synthesis file and not executed under this dispatch.

### Blast radius

The 24 PR branches and the synthesis plan file. No merges, no direct commits to `master`
beyond the synthesis plan file, and every change reversible through git.

## Motivation

The phase-4 batch produced 24 PRs, one per unit, each verified alone on base `76877f84`.
The `claude-review` action left one comment on each PR and no inline code comments:

```bash
for n in $(seq 446 469); do
  printf '#%s claude_comments=%s inline=%s\n' "$n" \
    "$(gh pr view $n --json comments --jq '[.comments[]|select(.author.login=="claude")]|length')" \
    "$(gh api repos/blalterman/SolarWindPy/pulls/$n/comments --jq length)"
done
```

Each comment sees only its own PR, so related feedback across PRs is never reconciled, and
a fix applied to one branch can collide with a strict xfail recorded in another branch
(three such collisions surfaced during the batch and were resolved by holding the fix).
No tool in the repository aggregates review feedback across PRs.

A combined check merged all 24 branches on a local scratch branch and found them green
together: no conflicts, no file touched by two PRs, both suites 0 failed, strict docs build
0 warnings, `lint-imports` 2 contracts kept, merge order irrelevant. Any pre-merge fix can
break that result, which is why AC 5 re-runs it.

Each PR records known library defects as `@pytest.mark.xfail(strict=True, ...)` naming the
fix that retires them (about 35 distinct defects). Fixing one of those defects on a
different PR's branch turns the marker into an XPASS(strict) failure at merge. A review
comment that asks to fix a recorded defect is therefore a follow-on, not a pre-merge fix,
unless the fix lands on the same branch that holds the marker and removes it there.

Post-merge work already queued in the plan artifact's Next actions tracker (rows 6-8): drop
`psutil` from `pyproject.toml` and `solarwindpy.yml` (needs #458 merged); fix
`plt.cm.get_cmap` in `solarwindpy/instabilities/verscharen2016.py` and remove #453's
conditional xfail (needs #453 merged); remove the batch worktrees under
`/Users/balterma/observatories/code/SolarWindPy/.claude/worktrees/`; run the follow-on fix
batch grouped by library area. Review feedback that belongs to one of those rows is filed
under that row.

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

1. **Collect.** For each PR 446-469, save the Claude comment body and the PR description
   (`gh pr view <n> --json body,comments --jq '.body, (.comments[]|select(.author.login=="claude")|.body)'`).
   Use subagents to read and summarize in batches so the main context holds summaries, not
   24 raw comments.
2. **Extract points.** Split each comment into discrete points (one requested change or
   concern each), tagged with PR number, severity as the reviewer stated it, and the file
   it concerns.
3. **Synthesize across PRs.** Group points that recur across PRs (for example, the same
   testing pattern or the same library file), and flag points that conflict with each other,
   with `.claude/docs/TEST_PATTERNS.md`, or with a strict xfail recorded in another PR.
4. **Propose dispositions.** Give every point one of: `fix-before-merge (PR #n)`,
   `follow-on (tracker row k or new row)`, `reject (reason)`, `author`. Apply the rule in
   § Motivation: a point that asks to fix a recorded strict-xfail defect is `follow-on`
   unless the fix lands on the branch holding the marker and removes the marker there.
5. **Write the synthesis file** at
   `/Users/balterma/observatories/code/SolarWindPy/plans/pr-review-synthesis-2026-09-30.md`:
   one `### PR #<n>` section per PR listing its points and dispositions, a cross-PR section
   for recurring and conflicting points, and a line `author_approved: no`. Render its
   Spent-When header with
   `python3 /Users/balterma/.claude/plugins/cache/blalterman-tools/session/6.0.3/tools/spent_when.py --emit <path> --member 'MARKED(<self>)' --supersedes none`.
   Commit it to `master`.
6. **Stop for approval.** Present the plan to the author. The author changes the line to
   `author_approved: yes` or edits dispositions.
7. **Apply approved pre-merge fixes** with one subagent per PR branch (at most 3 at a time;
   the session's concurrent-subagent limit is 3), each in a worktree on that PR's head
   branch, adding commits and pushing that branch. Each subagent runs both suites and the
   strict docs build before pushing.
8. **Re-run the combined check** in a subagent: merge all 24 updated branches on a local
   scratch branch from `origin/master`, run both suites, the strict docs build, and
   `lint-imports`, and report `RESULT:`.
9. **Update the plan artifact** Next actions tracker (step 4 to Done, step 5 to Ready) and
   hand the merge to the author.

## Read First

1. `/Users/balterma/observatories/code/SolarWindPy/CLAUDE.md` -- commands, conventions, and
   the rule to run bare `pytest` inside the conda env.
2. `/Users/balterma/observatories/code/SolarWindPy/docs/dispatches/batch-phase4-2026-09-28.md`
   -- the phase-4 instruction every PR was built against: shared brief, W4/W5/W6 seams, and
   each unit's OWNS line.
3. `/Users/balterma/observatories/code/SolarWindPy/.claude/docs/TEST_PATTERNS.md` -- the test
   standard the PRs follow; review points that contradict it are flagged, not applied.
4. https://claude.ai/code/artifact/1b4223f7-a580-4c84-a438-f3b5e0dc8963 -- the work plan
   artifact: Next actions tracker, the 25-unit table with PR links, open decisions. Read it
   with the Claude Docs tools, not a web fetch.

## State Verification

```bash
cd /Users/balterma/observatories/code/SolarWindPy
git fetch -q origin
# master is at or ahead of origin/master and contains the phase-4 hook fix
git merge-base --is-ancestor 76877f84 origin/master && echo "hook fix on origin"
git rev-list --count origin/master..master   # 0 once the author has pushed; report if not 0
# all 24 PRs are open and unmerged
for n in $(seq 446 469); do gh pr view $n --json state -q .state; done | sort | uniq -c   # 24 OPEN
# every PR still branches from 76877f84
for n in $(seq 446 469); do b=$(gh pr view $n --json headRefName -q .headRefName); git fetch -q origin "$b"; git merge-base origin/master "origin/$b"; done | sort | uniq -c
# the review comments exist (24 lines, each claude_comments=1)
for n in $(seq 446 469); do gh pr view $n --json comments --jq '[.comments[]|select(.author.login=="claude")]|length'; done | sort | uniq -c
# tools (the import contract itself lives in #460's pyproject.toml, so run lint-imports on a
# tree that includes #460, such as the combined-check scratch branch)
conda run -n solarwindpy lint-imports --help > /dev/null && echo "lint-imports installed"
```

A PR merged or closed before this session starts is a divergence: drop it from the
synthesis and record why.

## Acceptance Criteria

- [ ] Synthesis file covers every PR: `grep -cE '^### PR #4(4[6-9]|5[0-9]|6[0-9])$' /Users/balterma/observatories/code/SolarWindPy/plans/pr-review-synthesis-2026-09-30.md` → `24`
- [ ] No point lacks a disposition: `grep -ciE 'disposition: *(tbd|none|\?)' /Users/balterma/observatories/code/SolarWindPy/plans/pr-review-synthesis-2026-09-30.md` → `0`
- [ ] Author approved the plan: `grep -q '^author_approved: yes$' /Users/balterma/observatories/code/SolarWindPy/plans/pr-review-synthesis-2026-09-30.md` → exit 0
- [ ] Every PR that received a fix has green CI: `for n in <the fixed PRs>; do gh pr checks $n | grep -cE '\sfail\s'; done` → every line `0`
- [ ] Combined check re-run on the updated branches: the integration subagent's report → last line `RESULT: all green`
- [ ] Plan artifact updated: the Next actions tracker read with the Claude Docs tools → step 4 `Done`, step 5 `Ready`

## Anti-Patterns

- Do NOT merge any PR -- merging is the author's step, and the combined check assumes the
  author merges after it passes.
- Do NOT force-push a PR branch -- the reviewed commits must stay visible; fixes are new
  commits.
- Do NOT fix a recorded strict-xfail defect on a branch that does not hold its marker -- the
  marker turns into an XPASS(strict) failure when both PRs merge; this collision happened
  three times during the batch.
- Do NOT apply a review point that contradicts `.claude/docs/TEST_PATTERNS.md` (for example,
  a request to assert call counts or to add `wraps=` mocks) -- flag it as `author` instead.
- Do NOT decide physics values, methodology, or plot label wording -- those are `author`
  dispositions per the phase-4 seams.
- Do NOT commit with `conda run -n solarwindpy git commit` in a worktree -- the harness
  refuses it; the pre-commit hooks run in the solarwindpy env themselves via
  `/Users/balterma/observatories/code/SolarWindPy/.claude/hooks/project-env.sh`, so use
  plain `git commit`. Never `--no-verify`.
- Do NOT run a `.py` commit on `master` before #460 merges without expecting a stall -- the
  old `tests/test_circular_imports.py` crawls the batch worktrees in the pre-commit hook.
- Do NOT read raw comment bodies for all 24 PRs into the main context -- summarize through
  subagents; the comments total about 70 KB.

## Verification

```bash
cd /Users/balterma/observatories/code/SolarWindPy
P=plans/pr-review-synthesis-2026-09-30.md
grep -cE '^### PR #4(4[6-9]|5[0-9]|6[0-9])$' "$P"        # 24
grep -ciE 'disposition: *(tbd|none|\?)' "$P"              # 0
grep -c '^author_approved: yes$' "$P"                     # 1
for n in $(seq 446 469); do gh pr view $n --json state -q .state; done | sort | uniq -c   # 24 OPEN
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
