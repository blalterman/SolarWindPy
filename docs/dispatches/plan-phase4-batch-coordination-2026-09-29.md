<!--
Spent-When: MARKED(<self>)
Supersedes: none
-->

# /batch: phase-4, the 24 remaining units

## Context

The author launched `/batch` with the phase-4 instruction (`docs/dispatches/batch-phase4-2026-09-28.md`
at `238af274`): shared brief plus 24 units across W4 tests, W5 docs, W6 retirement. The units are
already partitioned by the author, so the decomposition is the instruction's own: one worker per
unit. Research confirmed the 24 OWNS sets are disjoint (script over the file: 24 units, 0 overlaps)
and the launch gate is clear (`origin/master` = `master` = `238af274`).

## Blocker found in research: workers cannot commit

The `docs-build` pilot could not commit. Root cause, verified:
- `.pre-commit-config.yaml` runs two hooks with `language: system` that take the interpreter from
  `PATH`: `solarwindpy-physics` (`.claude/hooks/pre-commit-tests.sh`, calls bare `pytest`) and
  `import-test` (`python -c "import solarwindpy"`).
- In a plain shell, `PATH` resolves `/opt/anaconda3/bin/pytest` (7.4.4) and `/opt/anaconda3/bin/python`
  with pandas 2.2.2; the package requires pandas >= 3. So `git commit` fails the hooks on correct work.
- The brief's workaround, `conda run -n solarwindpy git commit`, was refused inside a worker's
  worktree by the Claude Code harness (not a repo or user hook: `~/.claude/settings.json` has none).

## Step 0 (before launch): make the hooks find the project env

One commit on `master`, then the author pushes:
- New `.claude/hooks/project-env.sh`: runs its arguments inside the `solarwindpy` conda env
  (`conda run -n solarwindpy "$@"`) when the current shell has not activated it and the env exists;
  otherwise runs them as given (CI, other machines).
- `pre-commit-tests.sh`: every `pytest` call goes through `project-env.sh`.
- `.pre-commit-config.yaml` `import-test`: entry `.claude/hooks/project-env.sh python -c`.
- Positive control: in a scratch worktree from a plain shell, a trivial staged `.py` change commits
  with plain `git commit` after the fix, and the same commit failed the hooks before it (reverted,
  worktree removed). Full suite in both envs stays `0 failed`.
- Worker commit route then becomes plain `git commit` (hooks run, never `--no-verify`).

## Units (24, verbatim from the instruction)

W4 tests: `core-repair`, `core-units-constants`, `fitfunctions-repair`, `plotting-orbits` (long),
`plotting-spiral` (long), `plotting-base-scatter`, `plotting-agg-tools`, `plotting-hist1d`,
`plotting-misc`, `solar-activity-root`, `instabilities` (long), `import-contract`, `drift-shrink`,
`tooling-lint`.
W5 docs: `usage`, `install-citation`, `test-patterns-refs`, `source-core` (long),
`source-fitfunctions`, `source-plotting`, `source-misc`.
W6 retirement: `retire-paper`, `retire-scripts`, `retire-reports`.

Each unit's files and change are its OWNS line and block in the instruction; the worker prompt
carries that block verbatim.

## E2E recipe (from the brief; no user question needed)

1. Re-measure the unit's baselines before and after, with the commands in its block.
2. Both suites: `conda run -n solarwindpy pytest -q` and
   `conda run -n imap-loaders-20260225 pytest -q --no-header --ignore=tests/plotting/test_performance.py --ignore=tests/test_issue_titles.py`, both `0 failed`.
3. The unit's positive control, shown failing on a known-bad input, then reverted.
4. `source-*` units: the clean-export strict docs build and per-subpackage count from the brief.

## Worker prompt (Agent, general-purpose, isolation worktree, background; all 24 in one message)

Each prompt: the full shared brief verbatim; the "Units expected to run long" note when it applies;
the unit's block verbatim; the "Not partitioned" list (do not touch); these coordinator notes:
- Branch base is `origin/master` (`238af274` or later with Step 0); confirm with `git log -1`.
- Commit with plain `git commit`: the hooks find the `solarwindpy` env themselves. This replaces
  the brief's `conda run ... git commit`, which the harness refuses in worktrees. Never `--no-verify`.
- Run pytest as `conda run -n <env> pytest` (bare binary inside the env), never `python -m pytest`.
- `black` in the `solarwindpy` env is 26.5.1, matching pre-commit.
- New files in the repo need a `Spent-When` header; render it with
  `python3 /Users/balterma/.claude/plugins/cache/blalterman-tools/session/6.0.2/tools/spent_when.py --emit <path> --member '<event>' --supersedes none`.
- Commit message body ends with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; PR
  body ends with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`. Do not merge.
- The skill's worker instructions, verbatim (code-review, tests, e2e, commit/push/PR, `PR: <url>`).

## Tracking

Status table of 24 rows, updated as each `PR:` line arrives; the plan doc's units table
(`SolarWindPy phase-4 work plan`) updated to match.

---

## Empirical Findings (2026-10-01 trial run)

### End-state metrics

- Units: 24 planned, 24 pull requests opened (#446-#469), 24 merged; the last merge is `c3f2ce92`.
- Full unit-level results, acceptance criteria and deviations are recorded in the batch dispatch's findings at `e97111e0` (`git show e97111e0`).

### Open Item dispositions

| Open Item | Disposition |
|---|---|
| Step 0: hooks find the project env so workers commit with plain `git commit` | RESOLVED -- `76877f84` |
| api_reference.rst section prose (unassigned in the batch) | RESOLVED -- `07cc1efb`, `eeffae43` |

### Commits

- `76877f84` fix(hooks): run the Python pre-commit hooks in the solarwindpy env
- `c3f2ce92` Merge pull request #469 (last of the 24 unit merges)
- `e97111e0` docs(tdd): append empirical findings to dispatch-batch-phase4-2026-09-28 dispatch

## Spent-Mark: executed, findings recorded
