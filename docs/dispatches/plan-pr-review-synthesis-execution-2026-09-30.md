<!--
Spent-When: MARKED(<self>)
Supersedes: none
-->

# Plan: synthesize Claude review feedback on phase-4 PRs #446-#469

## Context

The dispatch `docs/dispatches/pr-review-synthesis` work order (commit 4bef3572) asks for
one disposition per point across the 24 `claude-review` comments, approved pre-merge fixes
applied as new commits on the PR branches, a green re-run of the combined check, and the
plan artifact's tracker advanced (step 4 Done, step 5 Ready). Steps 1-4 of the dispatch's
Scope (collect, extract, synthesize, propose) are done in this planning session through
three Explore agents; this plan carries their result and the remaining execution.

State verification: 24 OPEN, all branch from `76877f84` with `behind=0`, 24 Claude
comments and 0 inline comments, `lint-imports` installed, local `master` 3 ahead of origin
(tracker step 3, the author's push). No file is touched by two PRs; only #460 edits
`pyproject.toml`.

**Divergence (AC 4).** `Documentation / build` (strict nitpicky Sphinx) fails on all 24 PRs
and on every `master` push since `0742fd6a` (2026-09-28). Each PR clears only its own
area's warnings; only the combined tree is warning-free. `gh pr checks <n>` therefore shows
2 `fail` lines on every PR today, independent of any fix. Proposed bound: AC 4 counts
failures other than `Documentation / build`, whose green state is proven by the combined
check (AC 5). **Author ruled: exclude the docs build from AC 4.** The synthesis file records
this bound. The author also confirmed the dispatch's Intent as written.

## Synthesis result (the content of the synthesis file)

About 110 points. No reviewer marked anything blocking. Roughly 20 points are wrong on
checking (E501 is ignored in `setup.cfg`, black passes, the thing asked for is already
done, pandas is already pinned `>=3,<4`). Three push against `TEST_PATTERNS.md` (#456
drop ON FAILURE lines, #456 weaken exact limits, #457 speculative tolerance loosening)
and are rejected under it.

### Proposed fix-before-merge (12 edits on 11 branches)

| PR | Point | Edit |
|---|---|---|
| #446 | P446.2 | xfail reasons cite function names, not `orbits.py` line numbers (#450's docstrings shift every cited line) |
| #448 | P448.1 | `set_threshold` docstring describes actual behaviour (only a plain function is called; other callables are stored uncalled, per this PR's own xfail). The `callable()` fix stays follow-on: it needs `tests/solar_activity/.../test_extrema_calculator.py`, which #448 does not own |
| #450 | P450.5 | `tests/test_source_plotting_defects.py` Spent-When header names an event that fits all the file tests |
| #452 | P452.1 | `test_gse` asserts inequality against a perturbed Vector so it can fail |
| #453 | P453.4 | test pre-sets a log scale and asserts it survives; if it does not survive, narrow the docstring instead and report (no new xfail without the author) |
| #455 | P455.1 | `composite.py:149` guards a `None` fine-scan result by keeping the coarse-scan best gap (defensive guard; the x0-scan method itself stays the author's) |
| #456 | P456.2 | parametrize the `set_log` test over x and y |
| #460 | P460.5 | `CLAUDE.md` "CI runs" line adds `lint-imports` |
| #460 | P460.1 | `pyproject.toml` comment on why `reproducibility` and `scripts` sit outside `layers` |
| #466 | P466.3 | reword the "which governs" sentence in `.claude/commands/swp/test/audit.md:12` |
| #468 | P468.1, P468.2 | drop the `$(SOURCEDIR)/api` removal in `docs/Makefile` and `docs/make.bat`; trailing newline on `docs/README.md` |
| #469 | P469.1 | `README.rst:55` links `pyproject.toml` on GitHub master (the README also renders on PyPI) |

None of these touches a strict-xfail defect held on another branch.

### Author decisions

Physics and method: P447.1 Moyal functional form; P454.4 267.63 unrounded vs TEST_PATTERNS'
267.6; P455.3 `scan_x0` opt-out; P459.2 base-10 lognormal in `normal_parameters`; P463.2
which thermal speed beta uses and the `mw²=2kT` convention sentence; P450.4 scatter clips at
0.0001/0.9999 vs removes; P450.3 `set_axnorm("t")`.
Labels and API: P450.6 `TypeError` for a str `other_label`; P458.7 duplicate `ab`, `carr`,
`cos_theta` entries in `labels.available()`.
Rules and docs: P460.2 confirm lateral imports between `fitfunctions`/`instabilities`/
`solar_activity` and `core`/`tools` are forbidden; P466.1 and P466.2 retire or invert the
ast-grep rules swp-test-001/002/005/006/007 (one decision); P466.6 TEST_PATTERNS'
`conda run ... git commit` advice, which the harness refuses; P454.5 scipy floor 1.15;
P469.2 stated Python floor; P469.4 citation form (tracker row 13); P451.3 spiral hang and
top-edge formula (tracker row 14, #470); P456.7 second review pass on `test_base.py`;
P457.6 tracking issues for the xfails.

### Follow-on, filed by tracker row

- **Row 6** (post-merge dependency fixes): P458.8 drop `psutil`; #453's `get_cmap` xfail
  reason also cites `matplotlib>=3.5`, stale once step 3 pushes `b570a1c5`.
- **Row 8** (follow-on fix batch, each unit removes its own markers), with the collisions
  that decide the grouping:
  - Hist1D unnamed index: strict in #457 and #459. One fix, both marker sets in one commit.
  - `calc_bins_intervals` rounding/closure: #457 and existing `test_hist2d_plotting.py`
    markers, worded differently; a rounding-only fix XPASSes one hist2d marker only.
  - Integer smoothing truncation: `Hist1D.make_plot` (#457) and `nan_gaussian_filter`
    (#459); one float-cast policy.
  - `SpiralMesh.build_cat`: #451's marker; P450.2 lands here, not on #450.
  - `clip_lower`/`clip_upper` (#459 markers; P450.1).
  - orbits (#446, 5), solar_activity (#462, 3; P462.1, P462.6), fitfunctions (#447, 4;
    P447.5), extrema `callable()` plus `test_extrema_calculator.py` (#448, 3; P448.1 rest),
    verscharen2016 (#453, 3), scatter `cbar_kwargs` (#456, 1), `swap_protons` (#459).
- **Row 7** gains: retire `scripts/archived/` once #467 and #468 merge (P467.2).
- **New row, test-quality nits** (no library change): P446.3, P447.4, P448.3, P449.1-3,
  P450 `__geq__`/`__leq__`, P452.2-3, P453.1, P453.5, P454.1, P455.4-5, P456.3, P457.2,
  P458.1-3, P458.5-6, P459.5, P460.3, P461.1, P463.3-4, P464.2, P468.3.

### Rejected

Every remaining point, each with its reason in the file: already done (P462.2, P462.4,
P462.5, P459.3), false on checking (E501/black: P448.2, P451.2, P453.6; P451.1, P454.2,
P455.2, P460.4, P461.2, P463.1, P453.2, P446.4, P446.5), contradicts TEST_PATTERNS (P447.3,
P456.1, P456.4, P457.4), no ask (P446.1, P451.4, P452.4-5, P457.3, P456.6, P461.3, P458.4),
moot once step 3 is pushed (P453.3).

## Execution after plan approval

1. **Write** `plans/pr-review-synthesis-2026-09-30.md`: header rendered with
   `python3 .../session/6.0.3/tools/spent_when.py --emit <path> --member 'MARKED(<self>)' --supersedes none`,
   then `author_approved: no`, then one `### PR #<n>` section per PR (24), each point as
   `- P<n>.<k> [severity] <file>: <ask>. disposition: <value>. <reason>`, then
   `## Cross-PR` with the collisions above. Commit to `master` staging that path only
   (parallel chats share this tree). The pre-commit hook skips it (no `.py`).
2. **Stop.** The author flips `author_approved: yes` or edits dispositions.
3. **Apply fixes**: one general-purpose subagent per branch in the table, at most 3 at a
   time, each with `isolation: worktree` checked out on the PR head branch. Each runs
   `pytest -q` in the solarwindpy env, the docs build with `-W -n`, and pushes with plain
   `git commit` (never `conda run ... git commit`, never `--no-verify`, never force-push).
   Only the fixes the author approved.
4. **Combined check** subagent: scratch branch from `origin/master`, merge all 24 updated
   heads, both suites, strict docs build, `lint-imports`; last line `RESULT:`.
5. **CI**: `gh pr checks` on the 11 fixed PRs, read under the AC 4 bound.
6. **Tracker**: Claude Docs `update` on the Next actions table: step 4 Done, step 5 Ready,
   add the test-quality row and the Row 7 note. Hand the merge to the author.

## Verification

```bash
P=plans/pr-review-synthesis-2026-09-30.md
grep -cE '^### PR #4(4[6-9]|5[0-9]|6[0-9])$' "$P"   # 24
grep -ciE 'disposition: *(tbd|none|\?)' "$P"         # 0
grep -c '^author_approved: yes$' "$P"                # 1 after the author flips it
for n in $(seq 446 469); do gh pr view $n --json state -q .state; done | sort | uniq -c   # 24 OPEN
```

---

## Empirical Findings (2026-10-01 trial run)

### End-state metrics

- Review points: about 110 estimated, 116 extracted; fix-before-merge edits: 12 planned on 11 branches, 21 fix commits landed on 10 PR branches after author rulings added scope.
- Combined check green twice (base 76877f84, then 91574dbc); 24 PRs merged ending at `c3f2ce92`, merged tree `faaccce1` identical to the combined-check tree.

### Acceptance Criteria

| AC | Status | Evidence |
|---|---|---|
| Synthesis covers every PR (24 headings) | PASS | `git show 91574dbc:plans/pr-review-synthesis-2026-09-30.md \| grep -cE '^### PR #4'` returned 24 at approval |
| No point lacks a disposition | PASS | same file at 91574dbc: 0 `disposition: tbd\|none\|?` matches against 116 `disposition:` lines |
| `author_approved: yes` | PASS | commit `91574dbc` |
| 24 PRs merged | PASS | `gh pr view 446..469 --json state`: 24 MERGED; last merge `c3f2ce92` |

### Deviations from plan

- Review ran through a Claude Doc with one card per decision rather than edits to the synthesis file; rulings were transcribed into the file.
- AC 4 was bounded by the author to exclude the `Documentation / build` check, which failed on master and every PR until the combined merge.
- Claude merged the PRs on the author's instruction; the plan reserved merging for the author.
- `master` was pushed before merge, so the combined check was re-run on the new base.

### Commits

- `1dcf1e63`, `df5cb91b`, `66c9d21a`, `d180fc4e`, `91574dbc`: the synthesis file and author rulings.
- `c3f2ce92`: last of the 24 PR merges.

## Spent-Mark: executed, findings recorded
