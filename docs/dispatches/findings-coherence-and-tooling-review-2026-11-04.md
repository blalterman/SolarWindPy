<!--
Spent-When: MARKED(<self>)
Supersedes: none
-->

# Findings: coherence and agent-tooling review of SolarWindPy

author_signoff: none

owner: /Users/blalterman/observatories/code/SolarWindPy

Produced by `docs/dispatches/dispatch-coherence-and-tooling-review-2026-11-04.md`. The staged
cleanup is `docs/dispatches/plan-coherence-cleanup-2026-11-04.md`. Scratch artifacts, including
each pass's own report, live under the git-ignored `tmp/coherence-review/`. Run every command
from the repository root; run Python tools inside the `solarwindpy` conda env
(`conda run -n solarwindpy ...`), and search with `command grep` or `git grep`.

## Method

- Pass 0 ran the control arm on `solar_activity` from the dispatch's verbatim brief
  (`tmp/coherence-review/control-solar_activity.md`). Pass 1 reviewed every tracked `.claude`
  file, `CLAUDE.md`, and the two `.claude`-calling pre-commit hooks. Pass 2 ran as four slices,
  each a separate subagent: package, core, examples, and the env spec; fitfunctions and
  instabilities; plotting and tools; solar_activity and the whole test tree. This file merges
  their reports.
- Duplicates across slices are merged into one finding that keeps every site. The merged pairs
  are listed in the Experiment record. Every finding is renumbered globally, F1 to Fn, in order
  of appearance, and every cross-reference points at the new number.
- `[AUTHOR]` inside a finding marks a public-API, data-column, or scientific-result change, or a
  physics suspicion. Each is a proposal; the plan lists them under "Changes for author
  confirmation".
- Pass 2's Predicted lines are kept as each reviewer wrote them, with that reviewer's own note on
  when they were written. The Experiment record reports the timing.
- Where a finding overlaps a unit of the test-quality program, it cites the unit. The open-unit
  list in `docs/dispatches/dispatch-continue-test-quality-fixes-2026-10-05.md` § Scope is stale;
  see the Experiment record.
- The assembler reran the Repro of 34 findings drawn from all five reports; every one
  reproduced (Experiment record, "Repro spot-check").

### Principles as applied

Pass 1 and Pass 2 ran under the dispatch's original P1 to P9. The author revised the principles
during the review, and the revision is applied here, at assembly. P1 to P9 keep their numbers
and names, so every tag below stands as its reviewer judged it.

The aim is harmony: the felt quality of a surface whose parts fit so well that it leaves the
worker's attention. Harmony is the author's judgment, and this review does not assess it.
Coherence is the property harmony rests on: copies agree, each layer predicts the next one down,
names fit their siblings, and each layer exposes only what the layer above needs.

The principles are lenses that flex with the task and the reasoning. They are not procedures.
Guards sit only at seams: the asks the author requires, and explicit acceptance criteria.

- **P1. One home per idea.** Every concept, claim, and convention lives in one place, and
  everything else points to it. The revision reaches past constants to duplicated guidance and
  claims, such as `.claude/docs/` restating `CLAUDE.md`.
- **P2. A name predicts its content, against its siblings.** Public renames go to the author.
- **P3. Each layer predicts the next one down.** Write the prediction before looking, then record
  what was found.
- **P4. Each layer exposes only what the layer above needs.** Point to the layer below rather
  than restate it. The public interface is the seam.
- **P5. Mirror an existing form before inventing one; repeat forms, never facts.** Name the form
  mirrored, or say why none fits.
- **P6. Density, not line count.** A judgment, with no defined measure yet.
- **P7. Done when it fits.** A judgment, except where explicit acceptance criteria exist; each
  plan stage's done condition is such a criterion.
- **P8. The author holds the why:** meaning, claim status, public interfaces, scientific results.
  Each one is a required ask.
- **P9. A claim carries its check:** a command that re-derives it, and a positive control for
  every "found none".

Principles govern the open space of composition, and rules hold its binary seams. Precise rules
in an open space can lower consistency. Rules still matter where a decision belongs to the
author. A model that crosses such a seam produces correct content that was not its to decide,
and that content looks like competence. Explicit rules and required asks hold those seams.

## Session context

The session departed from the dispatch in these places. Each change was made with the author's
approval where noted.

- **Observe First failed on the environment.** In a plain shell, bare `pytest` and `lint-imports`
  were not on PATH. The `solarwindpy` conda env held pandas 2.3.3 (`pyproject.toml` requires
  pandas 3 or later), numpy 1.26.4, and Python 3.13.9, and it had no import-linter. Its editable
  install pointed at `/Users/blalterman/code/SolarWindPy`, which does not exist. In that env the
  suite gave 155 failed, 3282 passed, 12 skipped, 245 errors with four package-walking modules
  ignored (`tmp/coherence-review/env-before/summary.txt`).
- **The env was rebuilt, with the author's approval.** It was removed and recreated from
  `solarwindpy.yml` plus `python=3.12` and `pandas>=3`
  (`tmp/coherence-review/solarwindpy-py312.yml`), then `pip install -e ".[dev]"`. The unpinned
  solve paired astropy 6.1.7 with numpy 2.5.4, and astropy failed to import because numpy 2.5
  removed `np.in1d` (F202). `conda install "astropy>=7"` fixed it with astropy 8.0.2 from
  `pkgs/main`, so the env now mixes channels.
- **One untracked file was deleted, with the author's explicit approval.** The approval
  overrode the dispatch's anti-pattern for that file only. The conflict-marker file
  `solarwindpy/fitfunctions/lines_BACKUP_41608.py` caused 4 collection errors in the full suite.
  `solarwindpy/plans/` and `solarwindpy/tests/` were not touched.
- **Baseline after the rebuild.** `conda run -n solarwindpy pytest -q` gives 1 failed, 6254
  passed, 12 skipped (`tmp/coherence-review/baseline-pytest-full.txt`). `lint-imports` reports
  2 contracts kept. The one failure is `tests/test_import_aliases.py`, which flags aliases in the
  author's untracked `solarwindpy/tests/`, because its scan uses `rglob` and so reads untracked
  files (F194, F195).
- **The dispatch's last acceptance criterion cannot hold as written.** "Suite unchanged and
  green: a passed count, 0 failed" fails while the author's untracked `solarwindpy/tests/` sits
  in the working tree. This review changes no file under `tests/`, so the suite stays at 1 failed
  until F194 is fixed or the untracked directory moves.
- **The brief to Pass 1 said 24 `.claude` files.** `git ls-files .claude | wc -l` gives 25, and
  Pass 1 reviewed all 25.

## Agent tooling

Scope: every file in `git ls-files .claude` (25 files; `git ls-files .claude | wc -l`, so the
brief's count of 24 was one short), `CLAUDE.md`, and the two
`.pre-commit-config.yaml` hooks that call into `.claude/` (`solarwindpy-physics`, `import-test`).
Nothing under `solarwindpy/`, `tests/`, `.claude/`, or `CLAUDE.md` was edited.

### Sources

Each claim below drawn from Anthropic's documentation carries one of these URLs, fetched
2026-11-04:

- https://code.claude.com/docs/en/memory.md
- https://code.claude.com/docs/en/best-practices.md
- https://code.claude.com/docs/en/claude-directory.md
- https://code.claude.com/docs/en/hooks-guide.md
- https://code.claude.com/docs/en/skills.md
- https://code.claude.com/docs/en/sub-agents.md
- https://code.claude.com/docs/en/settings.md (found through https://code.claude.com/docs/en/claude_code_docs_map.md)
- https://code.claude.com/docs/en/settings-reference.md (settings reference, found through the docs map)
- https://code.claude.com/docs/en/hooks.md (hooks reference, found through the docs map)
- https://code.claude.com/docs/en/permissions.md (found through the docs map)

Doc statements this review leans on, paraphrased with their source:

- CLAUDE.md is context, not enforced configuration; to block an action regardless of what Claude
  decides, use a hook (https://code.claude.com/docs/en/memory.md).
- Target under 200 lines per CLAUDE.md; longer files reduce adherence
  (https://code.claude.com/docs/en/memory.md).
- Before writing a line, ask: could Claude find this by reading the code, and would it go and
  look? If both are yes, leave it out (https://code.claude.com/docs/en/best-practices.md). The
  file should hold the exact check commands, places where the code misleads, decisions not in the
  repo, and anything corrected twice (same URL).
- Adding IMPORTANT to an ignored line probably will not fix it; a rule that cannot have exceptions
  belongs in a hook (https://code.claude.com/docs/en/best-practices.md). The reverse also holds:
  hooks for things that are only preferences should be deleted (same URL).
- memory.md lists "project architecture" as a use for project CLAUDE.md
  (https://code.claude.com/docs/en/memory.md). best-practices.md says current models find file
  layout and conventions themselves (https://code.claude.com/docs/en/best-practices.md). I resolve
  the tension with the two-question test: architecture that `ls` and the code reveal stays out;
  architecture that misleads stays in.
- A skill body loads only when used, so a procedure that has grown inside CLAUDE.md belongs in a
  skill (https://code.claude.com/docs/en/skills.md). Project skills live at
  `.claude/skills/<name>/SKILL.md` and can carry supporting files and scripts (same URL).
- Project subagents live in `.claude/agents/*.md` with required `name` and `description`
  (https://code.claude.com/docs/en/sub-agents.md).
- The project `.claude/` holds `CLAUDE.md` (or root), `rules/*.md`, `settings.json`,
  `settings.local.json`, `skills/`, `commands/`, `agents/`, `output-styles/`, `workflows/`,
  `agent-memory/` (https://code.claude.com/docs/en/claude-directory.md). The page lists no role
  for docs, logs, JSON state, or templates inside `.claude/`; Claude Code reads none of them.
- Claude Code's system prompt is not published; standing instructions go in CLAUDE.md or
  `--append-system-prompt` (https://code.claude.com/docs/en/settings.md).
- Settings with invalid values raise a Settings Error or Warning at session start
  (https://code.claude.com/docs/en/settings.md). I did not check the published JSON schema, so I
  claim only that the four keys below are absent from the settings index, not that they error.
- Permission rules are evaluated deny, then ask, then allow; an allow rule cannot carve an
  exception out of a deny rule (https://code.claude.com/docs/en/permissions.md).
- A `/path` rule anchors at the settings source (the project root for project settings), not the
  filesystem root; `//path` is absolute (https://code.claude.com/docs/en/permissions.md).
- `!` is documented only as a gitignore negation inside Read and Edit path rules
  (https://code.claude.com/docs/en/permissions.md).
- MultiEdit is called "legacy MultiEdit" (https://code.claude.com/docs/en/permissions.md).
- `Stop` has no matcher support; a matcher on it is silently ignored
  (https://code.claude.com/docs/en/hooks.md).
- For most events, including PostToolUse and Stop, hook stdout goes to the debug log, not to
  Claude. Exit 2 on PostToolUse shows stderr to Claude; on Stop it keeps Claude working. Other
  nonzero codes are non-blocking errors (https://code.claude.com/docs/en/hooks.md).
- Hook handlers run in the current directory; reference scripts with `${CLAUDE_PROJECT_DIR}` or
  absolute paths (https://code.claude.com/docs/en/hooks.md,
  https://code.claude.com/docs/en/hooks-guide.md).
- PreCompact can block compaction; Claude Code discards its `systemMessage` and `continue`
  (https://code.claude.com/docs/en/hooks.md).
- A Stop hook should check `stop_hook_active` and exit early when it is true; Claude Code
  overrides a Stop hook after eight consecutive blocks
  (https://code.claude.com/docs/en/hooks-guide.md).
- Long-running hooks such as test suites can run with `"async": true`; async hooks cannot block
  (https://code.claude.com/docs/en/hooks.md).

### Environment facts used throughout

I verified each of these this session.

- In a plain shell, `command -v pytest lint-imports` prints nothing and `python` is
  `/opt/miniconda3/bin/python` (base). Inside the rebuilt env, `pytest` is
  `/opt/miniconda3/envs/solarwindpy/bin/pytest`.
- `import solarwindpy` in the env resolves to this checkout's `solarwindpy/__init__.py`, whether
  run from the repo root or from `/private/tmp`. `pip show solarwindpy` reports
  "Editable project location: /Users/blalterman/observatories/code/SolarWindPy".
- There is no `timeout` binary on PATH, in the shell or in the env: `bash -c 'timeout 5s true'`
  exits 127.
- pytest-xdist is not installed and not declared in `pyproject.toml`: `pytest -n 4` fails with
  "unrecognized arguments: -n".
- Full suite with coverage: 1 failed, 6254 passed, 12 skipped in 115.86 s. Total coverage is 98%
  (`coverage report --format=total`), the same with the author's untracked files omitted. The one
  failure is the known alias test on `solarwindpy/tests/`.
- `.git/hooks/` holds only `*.sample` files and `core.hooksPath` is unset, so pre-commit is not
  installed in this clone.
- `.claude/settings.local.json` holds only `enabledPlugins` and no hooks. The user-level
  `~/.claude/settings.json` registers its own hooks but names no SolarWindPy script.
- `tests/test_hooks.py` passes 6 of 6 against the current tooling. It tests `.claude/`, so
  retiring a hook means changing a file under `tests/`.

### Reference sweep (applies to every "registered or called" line)

The command, run over all 25 files, lists every tracked file outside the file itself that names
its basename:

`for f in $(git ls-files .claude); do b=$(basename $f); echo "$f <= $(git grep -l -F "$b" -- . ":!$f" | tr '\n' ' ')"; done`

Positive control: the same loop reports `.claude/hooks/test-runner.sh` named in
`.claude/settings.json`, `.github/PULL_REQUEST_TEMPLATE.md`, `CLAUDE.md`, and `tests/test_hooks.py`,
so a real reference is found. Zero-hit results: `.claude/hooks/input-validation.sh`,
`.claude/hooks/validate-tags.sh`, `.claude/scripts/cleanup-compaction-tags.py`,
`.claude/templates/test-patterns.py`. `git grep -n -F '.claude' -- .github` matches only
`.github/PULL_REQUEST_TEMPLATE.md:18`, so no workflow under `.github/workflows` calls a `.claude/`
file. Indirectly, `.github/workflows/claude.yml:35` and `.github/workflows/claude-code-review.yml:45`
run `anthropics/claude-code-action@v1` on a checkout. I infer, without checking the action's
source, that those CI sessions also load `CLAUDE.md` and `.claude/settings.json`, hooks included.

### .claude/README.md

- Claims: describes `settings.json`, `.claude/CLAUDE.md`, `agents.md`, specialized agents, a
  project system prompt, and a "branch-first" workflow in which Claude never works on master.
- Registered or called: Claude Code does not load it. The sweep hit in `tests/test_hooks.py` is a
  false positive: line 55 writes a `README.md` into a temporary repository. Other references are
  dispatches.
- Validity: `.claude/agents.md` and `.claude/CLAUDE.md` do not exist; `.claude/agents/` does not
  exist. Practice is mixed: code reaches master through PR merges from `perf/`, `feature/`, and
  `tq-fix/` branches (`b58e27df`, `da07993d`, `4bc1c08e`), while the two dispatch commits
  (`9b9cb747`, `48c61017`) went directly on master, which breaks the "never on master" rule. The
  README's `claude/YYYY-MM-DD-...` naming matches none of the merged branches.
- Duplication: restates settings.json and WORKFLOW_TEMPLATE.md.
- Verdict: **retire**. Every factual line is false or derivable. The branch policy is a decision
  the author has to state; the proposal leaves it as an open line for the author.

### .claude/WORKFLOW_TEMPLATE.md

- Claims: a six-step branch-first feature workflow, including Claude running
  `git branch -r --no-merged master` and asking which branch to use.
- Registered or called: named only by `.claude/README.md` and a dispatch. Not loaded by Claude Code.
- Validity: its premise that "all work [is] isolated to feature branches" (line 133) is broken by
  the direct dispatch commits on master (see README.md above).
- Duplication: overlaps README.md and DEVELOPMENT.md § Git Workflow (`feature/<name>`), which in
  turn disagrees with README.md's `claude/YYYY-MM-DD-...` naming.
- Verdict: **retire**. If the author wants a branch policy, it is one line in CLAUDE.md.

### .claude/branch-preservation.log

- Claims: JSON lines marking `plan/compaction-hook-enhancement` and `plan/hook-system-enhancement`
  as "DO NOT DELETE".
- Registered or called: nothing reads it (sweep: only this dispatch).
- Validity: neither branch exists locally or on origin
  (`git branch -a --list '*compaction-hook-enhancement*' '*hook-system-enhancement*'` prints
  nothing). Eleven other `remotes/origin/plan/*` branches exist; the log does not govern them.
- Duplication: none.
- Verdict: **retire**. Removing the log deletes no branch.

### .claude/compacted_state.md

- Claims: compaction snapshot from 2026-02-10 (branch master, plan `tests-audit`).
- Registered or called: written by `.claude/hooks/create-compaction.py:613`; read by nothing.
  `tests/test_hooks.py:142` reads a copy written into a temporary repository, not this file.
- Validity: tracked although `.gitignore:121` ignores `**/compacted_state.md`, so every
  compaction dirties a tracked file.
- Duplication: same content as the untracked `.claude/compaction-*.md` copies.
- Verdict: **retire** (untrack it; the ignore rule already covers it).

### .claude/docs/DEVELOPMENT.md

- Claims: physics rules "(Automated via Hooks)", data patterns, an 80% coverage floor,
  generate-test.py scaffolding, `feature/<name>` branches, environment setup, dependency
  workflow, attribution and license-compatibility rules, doc8 limits.
- Registered or called: named by `CLAUDE.md:76` and `.claude/docs/RELEASING.md`. Loaded only if a
  session follows the pointer.
- Validity: no hook automates any physics rule. The coverage floor (80) disagrees with
  `.claude/hooks/pre-commit-tests.sh:36` (92). The conda route at line 40 installs
  `pip install -e .` without `[dev]`, which omits `import-linter` (`pyproject.toml:132`).
  The physics conventions it lists are already stated in code: `solarwindpy/core/plasma.py:82`
  and `solarwindpy/core/ions.py:64` give `mw^2 = 2kT`.
- Duplication: `.xs()` and attribution lines repeat CLAUDE.md; the physics list repeats the
  docstrings. Its "Common Aliases" section teaches names that do not resolve (F47, added at assembly).
- The `pip install -e .` route is one of five copies of that instruction (F200).
- Verdict: **rebuild**. Keep the license-compatibility list and the dependency workflow (not
  derivable), move them into CLAUDE.md or the release skill, and drop the rest.

### .claude/docs/HOOKS.md

- Claims: four hook types, including a SessionStart hook `validate-session-state.sh`; a 95%
  coverage requirement; "60-80% token savings".
- Registered or called: named by `CLAUDE.md:77`.
- Validity: `.claude/hooks/validate-session-state.sh` does not exist and settings.json registers
  no SessionStart hook. The 95% floor matches no enforcing site.
- Duplication: restates settings.json, which is the source of truth for hooks.
- Verdict: **retire**. settings.json and the hooks reference are the documentation.

### .claude/docs/MAINTENANCE.md

- Claims: GitHub Actions run cleanup, CI conda setup, conda-feedstock automation, release
  monitoring, hook maintenance, directory upkeep.
- Registered or called: named by `CLAUDE.md:77` and `.claude/docs/RELEASING.md`.
- Validity: the feedstock and release commands point at scripts that exist
  (`scripts/update_conda_feedstock.py`, `scripts/wait_for_pypi.py`,
  `.claude/scripts/monitor-conda-release.sh`). The hook section cites the nonexistent
  `.claude/hooks/validate-session-state.sh` and `.claude/hooks/physics-validation.py` (lines
  127-132). The directory section creates `.claude/backups` and `.claude/logs/security-audit.log`,
  which no tool uses.
- Duplication: release monitoring repeats RELEASING.md.
- Verdict: **rebuild**. Move the feedstock and CI-cleanup procedures into the release skill and
  drop the hook and directory sections.

### .claude/docs/RELEASING.md

- Claims: the full release procedure (checklist, CHANGELOG, `scripts/bump_version.py`,
  `scripts/check_release_ready.py`, tagging, PyPI, conda-forge).
- Registered or called: named by `CLAUDE.md:77`, DEVELOPMENT.md, MAINTENANCE.md, and
  monitor-conda-release.sh.
- Validity: every root `scripts/` command it names exists (`ls scripts`). It is 591 lines and
  loads only when a session follows a pointer.
- Duplication: overlaps MAINTENANCE.md.
- Verdict: **rebuild** as `.claude/skills/release/SKILL.md`, with this file as a supporting
  reference. A procedure belongs in a skill whose body loads on use, and SKILL.md should stay
  under 500 lines with details in supporting files (https://code.claude.com/docs/en/skills.md).

### .claude/docs/TEST_PATTERNS.md

- Claims: the test standard (what a test asserts, fakes, tolerances, ON FAILURE docstrings,
  layering, how to run and commit).
- Registered or called: cited by `pyproject.toml:24`, `tests/plotting/test_no_data_files.py:134`,
  `CLAUDE.md:77`, and the test-quality dispatches. Not auto-loaded.
- Validity: line 154 gives the correct run form, `conda run -n solarwindpy pytest -q`. Line 155
  says the pre-commit hooks run the suite at commit time, which does not hold in this clone
  (pre-commit not installed).
- Duplication: line 154 contradicts `CLAUDE.md:46` (bare `pytest`).
- Verdict: **keep**. It is the live, cited standard. Optional: load it as
  `.claude/rules/tests.md` with `paths: ["tests/**"]` so it arrives when a session touches tests
  (https://code.claude.com/docs/en/memory.md). That move would break the three citations above
  unless they are updated with it.

### .claude/ecosystem-documentation.md

- Claims: a "Claude Settings Ecosystem" with a 6-layer security model, 7 hooks, 5 named agents
  (UnifiedPlanCoordinator, DataFrameArchitect, and others), `agent-routing.json`,
  `workflow-automation.json`, `code-style.md`.
- Registered or called: named only by `.claude/emergency-rollback.json`.
- Validity: none of the named agents, JSON files, `code-style.md`, `.claude/backups/LATEST_BACKUP`,
  or `validate-session-state.sh` exists. It locates hooks in `settings.local.json`, which holds
  only `enabledPlugins`.
- Duplication: restates HOOKS.md and settings.json, wrongly.
- Verdict: **retire**.

### .claude/emergency-rollback.json

- Claims: rollback procedures, such as writing `{"disableAllHooks": true}` to
  `.claude/emergency-disable.json` and copying `.claude/backups/minimal-settings.json`.
- Registered or called: named only by ecosystem-documentation.md.
- Validity: `disableAllHooks` is a real settings key
  (https://code.claude.com/docs/en/settings-reference.md), but Claude Code reads it only from a
  settings file; `.claude/emergency-disable.json` is not one
  (https://code.claude.com/docs/en/claude-directory.md). `.claude/backups/` does not exist.
- Duplication: none useful.
- Verdict: **retire**. The working rollback is `"disableAllHooks": true` in
  `.claude/settings.local.json`, or `git revert`.

### .claude/hooks/coverage-monitor.py

- Claims: per-module coverage analysis with module thresholds, run at Stop.
- Registered or called: `.claude/settings.json:181` (Stop); also allowed at
  `.claude/settings.json:20`; described by CLAUDE.md, HOOKS.md, MAINTENANCE.md.
- Validity: from a plain shell, `python` is base conda, `pytest` is absent, and the hook exits in
  0.02 s after printing "pytest not found". Inside the env it runs the full suite (116 s with
  coverage) under a 60 s subprocess timeout and always times out (measured: 61 s, "Coverage
  analysis timed out"). It never reaches the per-module report. Its output is stdout on a Stop
  hook with exit 0, which goes to the debug log, not to Claude
  (https://code.claude.com/docs/en/hooks.md). The matcher `"*"` at settings.json:177 is ignored on
  Stop (same URL).
- Duplication: a third set of coverage numbers (module thresholds of 85 to 95 at lines 75-91).
- Verdict: **retire**, with its Stop registration. Coverage already has a gate (pre-commit) and CI.
  An advisory hook that nobody sees is the kind best-practices says to delete
  (https://code.claude.com/docs/en/best-practices.md).

### .claude/hooks/create-compaction.py

- Claims: "structured compaction preserving plan state at token boundaries".
- Registered or called: `.claude/settings.json:169` (PreCompact); `tests/test_hooks.py:122` and
  `tests/test_hooks.py:184` test it.
- Validity: it writes `.claude/compacted_state.md` (tracked), a timestamped
  `.claude/compaction-*.md`, and a `compacted_state.md` into the first directory under `plans/`
  that `iterdir()` returns (lines 254-258, 622-626). Nothing reads these files back; no
  SessionStart hook exists. PreCompact cannot add to the compacted context, since Claude Code
  discards its `systemMessage` (https://code.claude.com/docs/en/hooks.md). Its token estimate
  reads `claude_session_state.md` and `.claude/agents/*.md` (line 167), neither of which exists,
  so the "context reduction" figure is unrelated to the session.
- Duplication: none.
- Verdict: **retire**, with its PreCompact registration and the two tests in
  `tests/test_hooks.py`. Claude Code compacts on its own
  (https://code.claude.com/docs/en/best-practices.md).

### .claude/hooks/input-validation.sh

- Claims: input sanitizers "for use in other hooks".
- Registered or called: nothing sources it (zero hits in the sweep; positive control above).
- Validity: exports functions nobody imports.
- Duplication: none.
- Verdict: **retire**.

### .claude/hooks/pre-commit-tests.sh

- Claims: runs the tests and enforces coverage before commits.
- Registered or called: `.pre-commit-config.yaml` hook `solarwindpy-physics`
  (`entry: .claude/hooks/pre-commit-tests.sh`); also allowed at `.claude/settings.json:21`.
- Validity: line 36 is the only gate that does anything: the full suite with
  `--cov-fail-under=92`, run in the env through project-env.sh. The rest adds runtime without
  gating:
  - Lines 47-63: the test path is computed as `tests/tests/...`, so the block never runs.
  - Line 73: reruns a name-substring selection (215 of 1729 tests in
    `tests/core tests/instabilities tests/fitfunctions`) with stderr discarded, and failures only
    warn.
  - Line 83: calls the absent `timeout` binary, so it always prints "Performance tests completed
    with timeout (expected for large datasets)" without running anything.
  - Line 14 advises `pip install`, which `.claude/settings.json:100` denies.
  - The ratchet comment says the baseline is 94%; measured coverage is 98%.
- Duplication: the floor comment duplicates CLAUDE.md:56-58.
- Verdict: **rebuild**: keep the staged-file guard and the line 36 gate; delete lines 44-86;
  raise the floor per the ratchet rule (author's call).

### .claude/hooks/project-env.sh

- Claims: runs its arguments inside the `solarwindpy` env when that env exists and is not active.
- Registered or called: `.pre-commit-config.yaml` hook `import-test`
  (`entry: .claude/hooks/project-env.sh python -c`); `.claude/hooks/pre-commit-tests.sh:10`;
  `.claude/docs/TEST_PATTERNS.md:155`.
- Validity: verified. From a plain shell,
  `.claude/hooks/project-env.sh python -c "import pandas, solarwindpy; print(...)"` printed pandas
  3.1.0 and this checkout's package.
- Duplication: none.
- Verdict: **keep**. It solves the problem behind this session's stale-env failures. It is a
  git-hook helper, not Claude Code tooling, so `scripts/` would be a truer home (author's call).

### .claude/hooks/test-runner.sh

- Claims: "smart" test selection with `--changed`, `--physics`, `--fast`, `--coverage`, `--all`.
- Registered or called: `.claude/settings.json:137`, `:147`, `:157` (PostToolUse on Edit,
  MultiEdit, Write); allowed at settings.json:12-18; cited by `CLAUDE.md:38`, `CLAUDE.md:39`, and
  `.github/PULL_REQUEST_TEMPLATE.md:18`; tested by `tests/test_hooks.py:164`.
- Validity:
  - `--changed` diffs `HEAD^ HEAD` (line 140): it tests the last commit's files, never the file
    just edited, and ignores the hook's stdin.
  - Every mode that runs tests builds `timeout ... pytest -n 4` (line 198). Both pieces are
    absent here, so `--physics` exits 127.
  - Failures exit with pytest's code, not 2, and print to stdout, so Claude would not see them
    even if tests ran (https://code.claude.com/docs/en/hooks.md).
  - The registered command `bash .claude/hooks/test-runner.sh` is cwd-relative: from `tests/` it
    exits 127.
  - It runs under `set -e` in whatever Python is on PATH, not through project-env.sh.
  - It fires after every edit, including edits to Markdown files.
- Duplication: re-implements test-file mapping that pre-commit-tests.sh also gets wrong.
- Verdict: **rebuild**. Drop the PostToolUse registration. For a check Claude can see, the
  documented shape is a Stop hook that exits 2 with failures on stderr and checks
  `stop_hook_active` (https://code.claude.com/docs/en/best-practices.md,
  https://code.claude.com/docs/en/hooks-guide.md). It would run the tests that mirror files
  changed since HEAD (`git diff --name-only HEAD` plus untracked files), through
  `${CLAUDE_PROJECT_DIR}/.claude/hooks/project-env.sh`. Whether a per-turn test gate is wanted at
  all is the author's call; if it is not, retire the script and fix the PR template line.

### .claude/hooks/validate-tags.sh

- Claims: validates that git tags follow `vX.Y.Z[-pre]`.
- Registered or called: nothing (zero hits; positive control above).
- Validity: rejects the 17 existing PEP 440 tags (`v0.1.0rc5` through `v0.1.3rc1`), so it exits 1
  on this repository. I first suspected `set -e` with `((VALID_VERSION_TAGS++))` aborted it; the
  run shows it completes, so that suspicion was wrong.
- Duplication: release readiness belongs to `scripts/check_release_ready.py`.
- Verdict: **retire**. If tag-format checking is wanted, fold a PEP 440 check into the release
  skill.

### .claude/logs/phase0-time-tracking.md

- Claims: a December 2025 time log for a "memory hierarchy" project on
  `feature/phase0-memory-commands`.
- Registered or called: nothing (only this dispatch).
- Validity: cites `.claude/memory/`, which does not exist. Runtime logs do not belong in the
  committed `.claude/` (https://code.claude.com/docs/en/claude-directory.md lists no such role).
- Duplication: none.
- Verdict: **retire**.

### .claude/scripts/cleanup-compaction-tags.py

- Claims: deletes `claude/compaction/*` tags locally and on the remote.
- Registered or called: nothing (zero hits).
- Validity: `git tag -l 'claude/compaction/*' | wc -l` is 0; the migration it served is done. It
  would push tag deletions, an action that leaves the machine.
- Duplication: none.
- Verdict: **retire**.

### .claude/scripts/generate-test.py

- Claims: interactive test scaffolding.
- Registered or called: allowed at `.claude/settings.json:22-23`; the settings `systemPrompt` tells
  Claude to "Execute the .claude/scripts/ CLI scripts directly"; cited by DEVELOPMENT.md:22,
  HOOKS.md:64, MAINTENANCE.md:106-107.
- Validity: it reads `input()`, so under the Bash tool it fails with "EOF when reading a line".
  Generated tests import `solarwindpy.tools.units_constants` (line 110), which does not exist. The
  module is `solarwindpy/core/units_constants.py`, and it has no `proton_mass` or `k_B`.
- Duplication: its templates contradict TEST_PATTERNS.md checklist items 3-4 (sourced expected
  values, tolerance helpers).
- Verdict: **retire**.

### .claude/scripts/monitor-conda-release.sh

- Claims: tracks a conda-forge release by issue number through `gh`.
- Registered or called: cited by RELEASING.md and MAINTENANCE.md as a manual step.
- Validity: checks for `gh` and its auth before use; exit codes are documented in the header. I did
  not run it, since it needs a live release issue.
- Duplication: none.
- Verdict: **keep**, relocated to `.claude/skills/release/` as a supporting script
  (https://code.claude.com/docs/en/skills.md).

### .claude/settings.json

- Claims: permissions, a system prompt, a tool list, a preferred model, planning mode, hooks.
- Registered or called: loaded by Claude Code as shared project settings
  (https://code.claude.com/docs/en/settings.md); tested by `tests/test_hooks.py:146-192`.
- Validity:
  - `systemPrompt`, `tools`, `ai`, and `planningMode` are absent from the settings index
    (https://code.claude.com/docs/en/settings-reference.md). The documented equivalents are
    `model` and `permissions.defaultMode` (https://code.claude.com/docs/en/permissions.md).
  - `Read(/etc/**)` guards a path under the repository, not `/etc`. `Bash(git add /etc/**)` is a
    command-text match and is unaffected.
  - `WebFetch(domain:!docs.anthropic.com)` uses an undocumented negation.
  - `Bash(pip install -e .)` is shadowed by the `pip install` deny.
  - Pushes run without a prompt.
  - 12 pytest allow rules are subsumed by `Bash(pytest:*)`.
  - Rules exist for nonexistent `.claude/backups` and `security-audit.log`.
  - The Stop matcher is ignored, MultiEdit is legacy, and hook paths are cwd-relative.
  - The deny list is the one part that does real work (`.env`, `secrets/`, `~/.ssh`).
- Duplication: `systemPrompt` restates CLAUDE.md's role.
- Verdict: **rebuild**: drop the four undocumented keys and the dead allow rules; move push to
  `ask`; change `Read(/etc/**)` to `Read(//etc/**)`; delete the WebFetch negation; remove PreCompact and Stop; keep the
  deny list; add `"$schema"` for editor validation (https://code.claude.com/docs/en/settings.md).

### .claude/templates/test-patterns.py

- Claims: string templates for physics tests.
- Registered or called: no importer (zero hits). Its directory is named only by the `exclude`
  regex `\.claude/templates/.*\.py$` in `.pre-commit-config.yaml`, which keeps black and flake8 off
  it.
- Validity: it hardcodes the proton mass as `1.67e-27` and `mu_0` as `4 * np.pi * 1e-7`, and line
  69 imports the nonexistent `solarwindpy.tools.units_constants`.
- Duplication: restates constants that `solarwindpy/core/units_constants.py` takes from
  `scipy.constants`.
- Verdict: **retire**, and drop the pre-commit exclude with it.

### .claude/validation-monitoring.json

- Claims: a "validation and monitoring system": component tests, metrics, a troubleshooting guide.
- Registered or called: named only by ecosystem-documentation.md and emergency-rollback.json.
- Validity: tests `.claude/hooks/physics-validation.py` (absent) and expects
  `git add ~/.ssh/id_rsa` to be "blocked". Nothing executes the file.
- Duplication: restates settings.json rules.
- Verdict: **retire**.

### CLAUDE.md

- Claims: package summary, data model, commands, the bare-`pytest` rule, CI contents,
  pre-commit floor, conventions, pointers to `.claude/docs/`.
- Registered or called: loaded every session (https://code.claude.com/docs/en/memory.md); 77
  lines, under the 200-line target.
- Validity:
  - Line 25 cites `units_constants.py:16`; the statement is at line 21.
  - Lines 38-39 list test-runner modes that cannot run tests.
  - Line 46 prescribes bare `pytest`, which is not on PATH outside the env. TEST_PATTERNS.md:154
    gives the working `conda run` form.
  - Line 41's `black` is env black 26.10.1, while CI runs pre-commit black 26.5.1 on
    `solarwindpy/*.py` only (`.github/workflows/ci-master.yml:47`).
  - Line 54 describes a pre-commit hook that is not installed in this clone.
  - Line 56 says coverage is about 95%; measured 98%.
  - Line 58 says coverage-monitor reports per-module coverage; it never does.
  - Lines 5-9 and 28-31 describe layout that `ls solarwindpy` and the code show.
  - Lines 16-18 and 59 use em-dashes.
- Duplication: `.xs()` and attribution also in DEVELOPMENT.md; floor also in pre-commit-tests.sh.
- Verdict: **rebuild** (proposal below).

### .pre-commit-config.yaml (solarwindpy-physics and import-test)

- Claims: `solarwindpy-physics` runs `.claude/hooks/pre-commit-tests.sh` on any staged `.py`
  file; `import-test` imports the package through `.claude/hooks/project-env.sh` on changes under
  `solarwindpy/`.
- Registered or called: by pre-commit, once `pre-commit install` has run. In this clone it has not
  (`.git/hooks` holds only samples). CI calls only the `black` and `flake8` hooks by id
  (`.github/workflows/ci-master.yml:47-48`).
- Validity: both entries are well formed. `solarwindpy-physics` carries the defects of its script.
- Duplication: the full-suite run duplicates CI's pytest step, which is the point of a local gate.
- Verdict: `solarwindpy-physics` **rebuild** (with its script); `import-test` **keep**.

### Verdict counts

Over the 25 tracked `.claude` files: keep 3 (`.claude/docs/TEST_PATTERNS.md`,
`.claude/hooks/project-env.sh`, `.claude/scripts/monitor-conda-release.sh`); rebuild 6
(`.claude/docs/DEVELOPMENT.md`, `.claude/docs/MAINTENANCE.md`, `.claude/docs/RELEASING.md`,
`.claude/hooks/pre-commit-tests.sh`, `.claude/hooks/test-runner.sh`, `.claude/settings.json`);
retire 16. Beyond the 25: `CLAUDE.md` rebuild, `solarwindpy-physics` rebuild, `import-test` keep.

Cross-dependency for the cleanup plan: every hook retirement or rebuild changes `tests/test_hooks.py`.
Its lines 164-181 require MultiEdit and PostToolUse, and lines 122-143 and 184-192 require
PreCompact. Those tests check registration strings only, so they pass while the registered hook
cannot run tests (F33).

### Findings

- **F1** [P9] `.claude/settings.json:113`: `systemPrompt` is absent from the settings index (https://code.claude.com/docs/en/settings-reference.md), and settings.md says standing instructions go in CLAUDE.md or `--append-system-prompt` (https://code.claude.com/docs/en/settings.md); its text also orders sessions to run `.claude/scripts/` directly. Repro: `python3 -c 'import json; print(list(json.load(open(".claude/settings.json"))))'`
- **F2** [P9] `.claude/settings.json:114`: `tools.enabled` is absent from the settings index; tool access is set through `permissions` allow, ask, and deny (https://code.claude.com/docs/en/settings-reference.md). Repro: `command grep -n '"tools"' .claude/settings.json`
- **F3** [P2] `.claude/settings.json:126`: `ai.preferredModel` names `claude-sonnet-4-20250514` under a key absent from the index; the documented key is `model` (https://code.claude.com/docs/en/settings-reference.md), so the name promises a model choice that I infer nothing applies. Repro: `command grep -n -A1 '"ai"' .claude/settings.json`
- **F4** [P9] `.claude/settings.json:129`: `planningMode` is absent from the index; plan mode is set with `permissions.defaultMode` (https://code.claude.com/docs/en/permissions.md). Repro: `command grep -n planningMode .claude/settings.json`
- **F5** [P2] `.claude/settings.json:90`: `Read(/etc/**)` anchors at the project root, so it guards `<repo>/etc/**`, not `/etc`; the absolute form is `Read(//etc/**)` (https://code.claude.com/docs/en/permissions.md). Bash rules match command text instead, so `Bash(git add /etc/**)` at line 108 is not affected. Repro: `command grep -n '/etc/' .claude/settings.json`
- **F6** [P9] `.claude/settings.json:102`: `WebFetch(domain:!docs.anthropic.com)` uses `!`, which is documented only as path negation for Read and Edit rules (https://code.claude.com/docs/en/permissions.md); this session fetched code.claude.com with the rule loaded, so I infer it matches nothing. Repro: `command grep -n 'domain:' .claude/settings.json`
- **F7** [P2] `.claude/settings.json:8`: the only WebFetch allow names `docs.anthropic.com`, while the Claude Code docs this review used are served from code.claude.com. Repro: `command grep -n 'WebFetch' .claude/settings.json`
- **F8** [P8] `.claude/settings.json:58`: `Bash(git push)` and `Bash(git push origin :*)` let pushes run with no prompt, removing the checkpoint the author's push rule depends on; propose moving them to `ask`. Repro: `command grep -n 'git push' .claude/settings.json`
- **F9** [P9] `.claude/settings.json:78`: allow `Bash(pip install -e .)` is dead because deny `Bash(pip install :*)` at line 100 wins; an allow rule cannot carve an exception out of a deny (https://code.claude.com/docs/en/permissions.md). Repro: `command grep -n 'pip install' .claude/settings.json`
- **F10** [P1] `.claude/settings.json:36`: `Bash(pytest:*)` subsumes the 12 other pytest allow rules in the same list. Repro: `command grep -c '"Bash(pytest' .claude/settings.json`
- **F11** [P1] `.claude/settings.json:4`: `Bash(grep:*)` restates the built-in read-only set, which already runs `grep` without a prompt (https://code.claude.com/docs/en/permissions.md). Repro: `command grep -n 'grep:' .claude/settings.json`
- **F12** [P9] `.claude/settings.json:82`: allow rules create `.claude/backups` and `.claude/logs/security-audit.log`, which nothing writes or reads. Repro: `ls .claude/backups .claude/logs/security-audit.log`
- **F13** [P9] `.claude/settings.json:22`: allows `generate-test.py`, which reads `input()` and fails with EOF under the non-interactive Bash tool. Repro: `python .claude/scripts/generate-test.py </dev/null`
- **F14** [P9] `.claude/settings.json:143`: a PostToolUse matcher for `MultiEdit`, which the permissions page calls legacy (https://code.claude.com/docs/en/permissions.md); `tests/test_hooks.py:172` requires it. Repro: `command grep -n MultiEdit .claude/settings.json tests/test_hooks.py`
- **F15** [P9] `.claude/settings.json:177`: matcher `"*"` on Stop, an event with no matcher support where a matcher is silently ignored (https://code.claude.com/docs/en/hooks.md). Repro: `command grep -n -B1 -A6 '"Stop"' .claude/settings.json`
- **F16** [P9] `.claude/settings.json:137`: hook commands use cwd-relative paths (`bash .claude/hooks/...`); handlers run in the current directory (https://code.claude.com/docs/en/hooks.md), so after a `cd` the script is not found. Repro: `cd tests && bash .claude/hooks/test-runner.sh --help; echo $?`
- **F17** [P2] `.claude/hooks/test-runner.sh:140`: `--changed` diffs `HEAD^ HEAD`, the last commit, and ignores the edited path on stdin; for an edit to `plasma.py` it reports "No Python files changed". Repro: `echo '{"tool_input":{"file_path":"solarwindpy/core/plasma.py"}}' | bash .claude/hooks/test-runner.sh --changed`
- **F18** [P9] `.claude/hooks/test-runner.sh:198`: every test-running mode builds `timeout ... pytest -n 4`; there is no `timeout` binary and pytest-xdist is undeclared, so `--physics` exits 127. Repro: `bash .claude/hooks/test-runner.sh --physics; echo $?`
- **F19** [P9] `.claude/hooks/test-runner.sh:233`: failures exit with pytest's code and print to stdout; for PostToolUse only exit 2 with stderr reaches Claude (https://code.claude.com/docs/en/hooks.md), so even a working run would be invisible. Repro: `command grep -n -E 'exit|echo' .claude/hooks/test-runner.sh`
- **F20** [P9] `CLAUDE.md:38`: lists `test-runner.sh --changed` and `--physics` as commands, and `.github/PULL_REQUEST_TEMPLATE.md:18` asks contributors to pass `--physics`; neither mode can run a test (F17, F18). Repro: `bash .claude/hooks/test-runner.sh --physics; echo $?`
- **F21** [P9] `.claude/hooks/coverage-monitor.py:38`: a 60 s subprocess timeout on a suite that takes 116 s with coverage, so inside the env it always times out, and from a plain shell it finds no pytest; `CLAUDE.md:58` says it reports per-module coverage, which it never does. Repro: `conda run -n solarwindpy python .claude/hooks/coverage-monitor.py`
- **F22** [P1] `.claude/docs/DEVELOPMENT.md:18`: the coverage floor is stated five ways: 80 here, 92 at `.claude/hooks/pre-commit-tests.sh:36`, 95 at `.claude/docs/HOOKS.md:61`, 85 to 95 per module at `.claude/hooks/coverage-monitor.py:77`, and "about 95%" at `CLAUDE.md:56`; measured coverage is 98%. Repro: `command grep -n -E 'cov-fail-under|95%|80%|"required"' .claude/docs/DEVELOPMENT.md .claude/docs/HOOKS.md .claude/hooks/pre-commit-tests.sh .claude/hooks/coverage-monitor.py CLAUDE.md`
- **F23** [P9] `.claude/hooks/pre-commit-tests.sh:53`: the test path is built as `tests/tests/...`, so the module-specific block at lines 47-63 never runs. Repro: `f=solarwindpy/core/plasma.py; t="tests/${f#solarwindpy/}"; echo "tests/${t%.py}"`
- **F24** [P2] `.claude/hooks/pre-commit-tests.sh:83`: calls the absent `timeout`, so the step always prints "Performance tests completed with timeout (expected for large datasets)" without running a test; the message names an outcome that never happened. Repro: `bash -c 'timeout 5s true'; echo $?`
- **F25** [P6] `.claude/hooks/pre-commit-tests.sh:73`: reruns 215 tests already run by the full suite at line 36, selected by name substring, with stderr discarded and failure only warning; it adds commit time and no gate. Repro: `conda run -n solarwindpy pytest --co -q -p no:randomly tests/core tests/instabilities tests/fitfunctions -k "physics or thermal or alfven or conservation"`
- **F26** [P9] `CLAUDE.md:54`: says the `solarwindpy-physics` hook runs on every commit touching a `.py` file, and `.claude/docs/TEST_PATTERNS.md:155` says the same; pre-commit is not installed in this clone, so neither it nor the commit-msg hook runs. Under the revised P1 this is also one false claim with two homes. Repro: `ls .git/hooks`
- **F27** [P9] `CLAUDE.md:46`: prescribes bare `pytest`, which is not on PATH outside the env, and attributes about 25 failures to `python3 -m pytest` shadowing. The installed package now resolves to this checkout, so I infer the shadowing cannot differ and the failures came from the stale install; `.claude/docs/TEST_PATTERNS.md:154` gives the working form, so the run command has two homes that disagree (the revised P1 reading). Repro: `command -v pytest; conda run -n solarwindpy python -c "import solarwindpy; print(solarwindpy.__file__)"`
- **F28** [P9] `CLAUDE.md:25`: cites `solarwindpy/core/units_constants.py:16` for the `.xs()` view rule; the statement is at line 21. The Pass 2 core reviewer found the same pointer independently. Read under the revised P1, a line number copied into prose is a second home for the location of the rule, the same defect as F163. Repro: `sed -n 24,25p CLAUDE.md; sed -n 16p solarwindpy/core/units_constants.py; sed -n 21p solarwindpy/core/units_constants.py`
- **F29** [P1] `CLAUDE.md:41`: `black solarwindpy/ tests/` runs env black 26.10.1 over two trees, while CI runs pre-commit black 26.5.1 on `solarwindpy/*.py` only, so the formatter is defined twice. Repro: `conda run -n solarwindpy black --version; command grep -n -A1 'psf/black' .pre-commit-config.yaml`
- **F30** [P6] `CLAUDE.md:7`: lines 7-9 and 28-31 describe the subpackage layout and key class files, which `ls solarwindpy` and the code show; by the two-question test they cost attention every session (https://code.claude.com/docs/en/best-practices.md). Repro: `ls solarwindpy`
- **F31** [P9] `.claude/hooks/create-compaction.py:613`: writes the tracked `.claude/compacted_state.md` (also ignored by `.gitignore:121`), a timestamped copy, and a file in the first `plans/*` directory; nothing reads any of them, and PreCompact output cannot enter the compacted context (https://code.claude.com/docs/en/hooks.md). Repro: `git grep -n compacted_state -- ':!.claude' ':!docs'`
- **F32** [P9] `.claude/hooks/create-compaction.py:167`: the token estimate reads `claude_session_state.md` and `.claude/agents/*.md`, neither of which exists, so the reported reduction is unrelated to the session. Repro: `ls claude_session_state.md .claude/agents`
- **F33** [P9] `tests/test_hooks.py:164`: the hook tests assert registration strings only and pass (6 of 6) while the registered PostToolUse script cannot run a test; a check that cannot see the failure it guards. Repro: `conda run -n solarwindpy pytest -q -p no:randomly tests/test_hooks.py`
- **F34** [P9] `.claude/docs/HOOKS.md:9`: documents a SessionStart hook `validate-session-state.sh`, and `.claude/docs/MAINTENANCE.md:130` documents `physics-validation.py`; neither file exists. Repro: `ls .claude/hooks/validate-session-state.sh .claude/hooks/physics-validation.py`
- **F35** [P9] `.claude/README.md:9`: lists `agents.md` and `.claude/CLAUDE.md` and promises specialized agents; neither file nor `.claude/agents/` exists. Repro: `ls .claude/agents.md .claude/CLAUDE.md .claude/agents`
- **F36** [P1] `.claude/README.md:38`: three branch-naming schemes coexist: `claude/YYYY-MM-DD-...` here, `feature/<name>` at `.claude/docs/DEVELOPMENT.md:25`, and the `perf/`, `feature/`, `tq-fix/` names actually merged; the "never on master" rule at line 37 is also broken by direct dispatch commits. Repro: `git log --first-parent --format=%h_%s -6 master`
- **F37** [P9] `.claude/ecosystem-documentation.md:21`: describes `agent-routing.json`, `workflow-automation.json`, `code-style.md`, five named agents, and seven hooks; none exists. Repro: `ls .claude/agent-routing.json .claude/workflow-automation.json .claude/docs/code-style.md .claude/agents`
- **F38** [P9] `.claude/emergency-rollback.json:7`: the "immediate" rollback writes `disableAllHooks` into `.claude/emergency-disable.json`, a file Claude Code never reads; the key works only inside a settings file (https://code.claude.com/docs/en/settings-reference.md). Repro: `command grep -n 'emergency-disable\|backups' .claude/emergency-rollback.json`
- **F39** [P9] `.claude/validation-monitoring.json:16`: its component tests run the nonexistent `.claude/hooks/physics-validation.py` and expect `git add ~/.ssh/id_rsa` to be blocked; nothing executes the file. Repro: `command grep -n 'physics-validation\|id_rsa' .claude/validation-monitoring.json`
- **F40** [P9] `.claude/branch-preservation.log:1`: marks two branches "DO NOT DELETE" that no longer exist locally or on origin. Repro: `git branch -a --list '*compaction-hook-enhancement*' '*hook-system-enhancement*' | wc -l`
- **F41** [P9] `.claude/hooks/validate-tags.sh:32`: the semver-only pattern rejects 17 existing PEP 440 tags, so the unregistered validator always exits 1 here. Repro: `git tag --list | command grep -c -v -E '^v[0-9]+\.[0-9]+\.[0-9]+(-.+)?$'`
- **F42** [P9] `.claude/scripts/cleanup-compaction-tags.py:1`: targets `claude/compaction/*` tags, of which none exist, and would push tag deletions. Repro: `git tag -l 'claude/compaction/*' | wc -l`
- **F43** [P2] `.claude/scripts/generate-test.py:110`: generated tests import `solarwindpy.tools.units_constants`, which does not exist; the module lives at `solarwindpy/core/units_constants.py` and has no `proton_mass` or `k_B`. Repro: `conda run -n solarwindpy python -c "from solarwindpy.tools import units_constants"`
- **F44** [P1] `.claude/templates/test-patterns.py:15`: hardcodes the proton mass (`1.67e-27`) and `mu_0` (`4 * np.pi * 1e-7`), restating constants owned by `solarwindpy/core/units_constants.py` through `scipy.constants`. Repro: `command grep -n -E '1\.67e-27|1e-7' .claude/templates/test-patterns.py`
- **F45** [P9] `.claude/hooks/input-validation.sh:83`: exports five helper functions that no script sources. Repro: `git grep -n 'input-validation' -- . ':!docs'`
- **F46** [P9] `.claude/logs/phase0-time-tracking.md:14`: a tracked 2025 work log that cites `.claude/memory/`, which does not exist; runtime logs have no role in a committed `.claude/` (https://code.claude.com/docs/en/claude-directory.md). Repro: `ls .claude/memory`
- **F47** [P2] `.claude/docs/DEVELOPMENT.md:175`: the "Common Aliases" section teaches `swp.Plasma`, `swp.pp`, `swp.sa`, and `swp.sc` (the last mapped to `solarwindpy.spacecraft`); only `swp.pp` resolves, and `solarwindpy.spacecraft` raises `ModuleNotFoundError`. Three of four names point at nothing. Read under P1, it is also a second home for import paths that contradicts the package's one-import-path rule (`solarwindpy/__init__.py`). Guidance a session reads is a likelier source of alias habits than any test. Repro: `sed -n 175,179p .claude/docs/DEVELOPMENT.md; conda run -n solarwindpy python -c 'import solarwindpy as swp; print(hasattr(swp,"Plasma"), hasattr(swp,"pp"), hasattr(swp,"sa"), hasattr(swp,"sc"))'`

Tag fit: most tooling defects are P9 (a claim without a working check). Three tags were forced,
because the principles are written for package code: F8 as P8 (the author's push checkpoint, not
physics or API), F25 as P6 (runtime density, not concepts per line), and F43 as P2 (an import path
that points at nothing, not a misleading name among siblings). The Experiment record counts these as forced
template fits.

Found none, with positive controls:

- **No CI workflow calls a `.claude/` file.** `git grep -n -F '.claude' -- .github/workflows` is
  empty. Positive control: the same pattern over `.github` finds
  `.github/PULL_REQUEST_TEMPLATE.md:18`.
- **No local or user settings register the unreferenced scripts.**
  `command grep -n -E 'input-validation|validate-tags|cleanup-compaction' .claude/settings.local.json ~/.claude/settings.json`
  is empty. Positive control: `command grep -n test-runner .claude/settings.json` finds lines 137,
  147, and 157.
- **No `claude/compaction/*` tags remain.** `git tag -l 'claude/compaction/*'` is empty. Positive
  control: `git tag -l 'v0.1.0*'` lists tags.

## CLAUDE.md proposal

A proposal only; nothing is applied. Proposal lines not executed this session:

- The env rebuild pair. This session's rebuild used a copy of `solarwindpy.yml` with `python=3.12`
  and `pandas>=3` added (`tmp/coherence-review/solarwindpy-py312.yml`); the committed file leaves
  the Python version to CI (`solarwindpy.yml:8`).
- `pre-commit install`. Standard pre-commit usage; `.pre-commit-config.yaml` declares a
  `commit-msg` stage, which the default install omits.
- The two `pre-commit run` lines. Not run, since they rewrite files and download hook envs; CI
  uses the same hook ids (`.github/workflows/ci-master.yml:47-48`).
- The doctest line. Taken from `.github/workflows/doctest_validation.yml:34`.

The `.xs()` line was probed in the env (pandas 3.1.0). An `.xs()` result shares memory with the
parent (`np.shares_memory` is True), but a write to it does not reach the parent (copy-on-write).
The comment at `solarwindpy/core/units_constants.py:21` dates from 2019 (`git log -L` shows
`c8596a4a`) and says "views"; Pass 2 should check it against pandas 3 semantics.

```markdown
# SolarWindPy

In-situ solar wind plasma analysis. The author owns the physics and the public API.

## Environment

- Run every Python tool inside the `solarwindpy` conda env: `conda run -n solarwindpy <command>`,
  or activate the env first. Outside it, `python` is the base install and `pytest` and
  `lint-imports` are not on PATH.
- A stale env produces failures that look like code bugs. Before debugging a surprising failure,
  check that the env imports this checkout and a pandas inside the `pyproject.toml` range:
  `conda run -n solarwindpy python -c "import solarwindpy, pandas; print(solarwindpy.__file__, pandas.__version__)"`
- Rebuild the env: `solarwindpy.yml` leaves the Python version to CI, so pin it in a copy
  (`python=3.12`) and run `conda env create -f <copy>`, then
  `conda run -n solarwindpy pip install -e ".[dev]"`. Plain `pip install -e .` leaves out
  import-linter and pre-commit.
- Install the git hooks once per clone:
  `conda run -n solarwindpy pre-commit install --hook-type pre-commit --hook-type commit-msg`.

## Checks

- Full suite: `conda run -n solarwindpy pytest -q` (about two minutes).
- One file: `conda run -n solarwindpy pytest -q tests/core/test_plasma.py`
- Network and slow tests are skipped unless you pass `--run-drift` or set `SWP_RUN_DRIFT=1`.
- Import layering: `conda run -n solarwindpy lint-imports`
- Format and lint at the versions CI pins:
  `conda run -n solarwindpy pre-commit run black --files <paths>` and
  `conda run -n solarwindpy pre-commit run flake8 --files <paths>`.
- Doctests: `conda run -n solarwindpy pytest --doctest-modules solarwindpy -q`
- The pre-commit hook runs the full suite with a coverage floor in
  `.claude/hooks/pre-commit-tests.sh`. The floor is a ratchet below measured coverage, not a
  target; raise it as coverage rises.

## Data model

- Columns are a three-level MultiIndex named `M` (measurement), `C` (component), `S` (species).
  An empty string means no component or no species.
- Select columns with `.xs()`, which shares the parent's data instead of copying it; the package
  relies on this to keep memory down. Do not add `.copy(deep=True)` in load or compute paths.
  Under pandas 3 copy-on-write, writing to an `.xs()` result does not change the parent.

## Conventions

- Extract shared logic at the second copy. In this repository that overrides the general
  three-examples rule.
- Cite scientific sources in docstrings: DOI or arXiv, plus the equation number when you implement
  a specific published result.
- External code: record its URL, license, and modifications in a comment. Copy only MIT, BSD,
  Apache 2.0, or public-domain code. When provenance or license is unclear, reimplement.
- Commit subjects follow Conventional Commits (`fix(core):`, `feat(plotting):`, `chore:`); the
  commit-msg hook rejects others.
- Renaming a public name, changing a column label, or changing a physical result is the author's
  decision: propose it, do not make it.
- Tests follow `.claude/docs/TEST_PATTERNS.md`. Read it before writing or reviewing a test.
- Release work follows the `/release` skill.
- Branches: placeholder for the author to fill in. State which work goes through a branch and PR,
  which may commit to master, and the branch naming scheme.

## Gotchas

- `tests/test_hooks.py` tests the Claude Code hooks in `.claude/settings.json`. Change both
  together.
- Untracked directories inside `solarwindpy/` belong to the author. Do not edit, move, or commit
  them.
```

### Rationale, line by line

Kept, because a session cannot infer it from the code:

- **The `conda run` form and the PATH fact.** These are the exact check commands
  (https://code.claude.com/docs/en/best-practices.md). They replace CLAUDE.md:46, which was wrong
  on this machine (F27), and match TEST_PATTERNS.md:154.
- **The stale-env probe and rebuild steps.** An environment fact not in the code, which cost this
  session a rebuild. `[dev]` is spelled out because of F200.
- **`pre-commit install` with both hook types.** Hooks are not installed in this clone (F26), and
  the commit-msg stage needs the explicit type.
- **Single-file run, opt-in flag, and doctest command.** The opt-in flag is in `tests/conftest.py`,
  but a session would not look for it before running the suite.
- **Black and flake8 through pre-commit.** This replaces CLAUDE.md:41 so that local and CI
  formatting use one pinned version (F29).
- **The floor-as-ratchet line, without a number.** It records the author's decision (the why). The
  number stays in one home, the script (P1, F22).
- **M/C/S and `.xs()`.** The level names are visible in the code. The data-sharing rule and the
  ban on deep copies are a decision that the code does not enforce. The wording follows the pandas
  3.1 probe above, not the 2019 comment, and the line citation is dropped rather than corrected
  (F28), so it cannot drift again.
- **The opening line.** One sentence of purpose and the ownership seam. A session cannot read who
  decides physics and API from the code.
- **The `/release` pointer.** Valid only if the RELEASING.md rebuild into
  `.claude/skills/release/` is accepted. Otherwise point at `.claude/docs/RELEASING.md` instead.
- **The branch placeholder.** The current files state three inconsistent schemes (F36). Branch
  policy is a decision not in the code, so the author has to state it; I do not infer it from
  history.
- **Extract at the second copy, the citation rule, and the attribution and license rule.** These
  are decisions not in the repo. The license list is moved up from DEVELOPMENT.md.
- **Conventional Commits.** One line, noting that the hook enforces it once installed.
- **Author's-call line.** This states the Seam that the dispatch and TEST_PATTERNS.md already
  assume.
- **TEST_PATTERNS pointer.** Kept as a pointer, not inlined, so the 168 lines do not load every
  session.
- **`tests/test_hooks.py` gotcha.** A test of tooling under `tests/` is the kind of misleading
  placement best-practices names (https://code.claude.com/docs/en/best-practices.md).
- **Untracked-dirs gotcha.** It protects the author's work. If it must never bend, it belongs in a
  deny rule instead (`Edit(/solarwindpy/plans/**)`, `Edit(/solarwindpy/tests/**)`). A line here
  works most of the time, and a deny rule holds every time
  (https://code.claude.com/docs/en/best-practices.md).

Cut:

- **The package summary and subpackage list (lines 7-9) and the key-class paragraph (28-31).**
  `ls` and the code show both (F30, https://code.claude.com/docs/en/best-practices.md).
- **The `examples.load_plasma()` pointer.** Discoverable from `solarwindpy/examples/__init__.py:50`.
- **The test-runner commands.** They cannot run (F18, F20).
- **The `python3 -m pytest` warning.** Its mechanism is gone with the rebuilt editable install
  (F27, an inference). If the author wants a guard anyway, the place is a PreToolUse hook or an
  `ask` rule on `Bash(python3 -m pytest *)`, not prose.
- **"CI runs ..." (line 51).** Discoverable in `.github/workflows/`.
- **The coverage-monitor sentence.** The hook is proposed for retirement (F21).
- **The `.claude/docs/` index.** HOOKS.md is retired, RELEASING.md and MAINTENANCE.md become a
  skill, and DEVELOPMENT.md is folded in. Only the TEST_PATTERNS pointer remains.
- **"NumPy-style docstrings".** `flake8-docstrings` runs in pre-commit (`.pre-commit-config.yaml`),
  and every module shows the style.
- **Emphasis (the bold "Access columns..." and "Invoke the bare pytest...").** Emphasis does not
  raise adherence (https://code.claude.com/docs/en/best-practices.md).

Moved to configuration, not prose:

- **The push checkpoint.** Moved to `permissions.ask` for `Bash(git push *)` (F8).
- **Protecting `.env`, `secrets/`, and `~/.ssh`.** Already deny rules; kept there.
- **The author's untracked directories.** A candidate deny rule (above).
- **"Run the tests before you finish".** If wanted as a rule without exceptions, it becomes the
  rebuilt Stop hook with exit 2 and a `stop_hook_active` guard
  (https://code.claude.com/docs/en/hooks-guide.md). Otherwise it stays out entirely.

Moved to CLAUDE.local.md (personal, gitignored; https://code.claude.com/docs/en/memory.md):

- **The shell-shim rule "use `command grep` or `git grep`, never plain `grep -r`".** It is a
  property of this machine's shell, not of the repository.

## Coherence review

Pass 2 ran as four slices. Each slice's own notes on prediction timing and test-quality overlap
are kept below, attributed to the slice.

- **Package, core, examples, env spec.** The `**Predicted:**` lines below were written after the evidence pass. Each was reconstructed from the layer above it (its docstring, the `Core`/`Base` contract, the sibling classes), not from what was later read beneath it, but none was committed to text before reading. Treat them as reconstructions, not as prior predictions.
- **fitfunctions and instabilities.** The two subpackage predictions were formed after reading only each subpackage's `__init__.py` (docstring and `__all__`). The module-level and test-tree predictions were formed after one introspection pass over the subclass constructor signatures, before reading the module bodies; they were written into this file after the reading, so treat them as recorded from memory, not pre-registered.
- **plotting and tools.** The slice states no timing for its Predicted lines.
- **solar_activity and the test tree.** The P3 rule says to write each prediction before reading below it. I read all of `solar_activity` before writing any line of this file, so the `**Predicted:**` lines below are reconstructed from the layer-above text only (the subpackage docstring and `__all__`, each module's `__all__` and class list, `base.py`'s class names), not from memory of what lay beneath. I cannot fully separate the two. This is a place where the principle (predict, then look) and the rule as executed pulled apart.

Baselines quoted by the slices: `conda run -n solarwindpy pytest tests/core tests/test_examples.py -q` gives 894 passed, 6 warnings, 18 subtests passed (run this session). All six warnings are the `mode.chained_assignment` Pandas4Warning of F172. Baseline: `conda run -n solarwindpy lint-imports` reports "Contracts: 2 kept, 0 broken."

Test-quality overlap, as the core slice found it: Every unit of `docs/dispatches/dispatch-continue-test-quality-fixes-2026-10-05.md` § Scope that touches this scope shows a merged pull request (`git log --oneline --merges | command grep -E "tq-fix/(scalar-w-nan|p0-simplify|rm-core-solar|plasma-survivor-tests|plasma-io-electrons)"`). Still open, judged from that § Scope and the absence of a closing commit: step 1 (two questions to the author), step 4 (read the warnings), step 6 (`HingeMax` point, outside this scope), steps 7 and 8 (close the track). Two findings overlap: F172 is warnings that step 4 reads, and F59 is a gap in the missing-data rule of the merged `scalar-w-nan` unit (batch file § scalar-w-nan). No in-flight unit owns a file named below.

Author's untracked work, reported only: `solarwindpy/plans/` (three scripts: `check_sweep.sh`, `find_recent_automation_commits.zsh`, `make_branch_from_plan.py`) and `solarwindpy/tests/` (`test_base_master.py`, `test_base_old.py`; this directory is what `tests/test_import_aliases.py` flags in the suite baseline). `solarwindpy/fitfunctions/lines_BACKUP_41608.py`, listed as untracked in the dispatch Motivation, is no longer present (`git status --porcelain`). `solarwindpy/scripts/` holds only `logs/` and `__pycache__/` and is neither tracked nor listed by `git status`.

### Package layer

**Predicted:** `solarwindpy/__init__.py` imports seven subpackages and states that every public object has one import path, the module that defines it. So I expect: every subpackage placed in the `[tool.importlinter]` layers; `core` as the single owner of constants, units, and the `(M, C, S)` column convention, with higher layers importing them; each subpackage owning its own data files; no session or tooling markers in shipped modules.
**Found:** Constants are owned once: no subpackage outside `core/units_constants.py` defines a physical constant (positive control below finds the owner). The one-import-path rule holds (`core/__init__.py` re-exports modules only). The rest does not fit: `examples` sits outside the layer contract and keeps its data inside `core`; the `(M, C, S)` level names are a literal in ten code lines with a half-used owner (`Base.mi_tuples`); unit factors and unit TeX strings live in two subpackages under different keys; one comment that CLAUDE.md treats as a rule is copied into four modules and its CLAUDE.md pointer is stale.

Positive control for "constants have one home": `git grep -n -E "from scipy import constants|physical_constants\[" -- 'solarwindpy/*.py'` finds only `solarwindpy/core/units_constants.py`. One exception was found below the package layer (F65, a rotation rate in `alfvenic_turbulence.py`).

- **F48** [P4] `pyproject.toml:32`: the `layers` contract lists `fitfunctions | instabilities | solar_activity`, `plotting`, `core | tools` and omits `examples`, which imports `core` (`examples/__init__.py:81`); nothing stops `core` from importing `examples`, and `lint-imports` reports KEPT only because no such import exists yet. Repro: `sed -n 28,36p pyproject.toml; git grep -n -E "from \.\.?examples|solarwindpy\.examples" -- solarwindpy/core solarwindpy/tools; git grep -n "from \.\.core" -- solarwindpy/examples`
- **F49** [P3] `solarwindpy/examples/__init__.py:18`: the example CSVs are read from `resources.files("solarwindpy.core")/data`, so data owned by `examples` live in `core/data/` beside `asplund2021.csv`, which `core.abundances` owns; the layout does not predict the owner. Repro: `sed -n 18p solarwindpy/examples/__init__.py; ls solarwindpy/core/data; sed -n 153,154p pyproject.toml`
- **F50** [P1] `solarwindpy/core/base.py:398`: the level names `["M", "C", "S"]` are a local literal inside `Base.mi_tuples`; the same literal, as list or tuple, is rewritten in nine more code lines (`ions.py:143`, `plasma.py:444`, `:495`, `:725`, `:907`, `:909`, `:2018`, `examples/__init__.py:43`, `tools/__init__.py:92`), beside docstring and doctest copies, and `plasma.py:2018` and `examples/__init__.py:43` rebuild the MultiIndex by hand instead of calling `Base.mi_tuples`. Repro: `git grep -n -E '"M", ?"C", ?"S"' -- 'solarwindpy/*.py' | command grep -v -E '>>>|``|labeled by|labelled|Build a Plasma|levels must|level=|column levels'`
- **F51** [P1] `solarwindpy/core/units_constants.py:180`: the units of each stored quantity are declared twice, as factors in `Units` and as TeX strings in `plotting/labels/base.py:120` `_trans_units`, under different keys for the same quantity (`temperature`/`T`, `qpar`/`q`, `specific_entropy`/`S`, `kinetic_energy_flux`/`Wk`), and nothing checks the two agree; `plotting/labels/base.py:169` carries "TODO: verify that these units are Hertz" for `nuc`, although `core/units_constants.py:166` documents and `:194` sets `nuc = 1e-7` (10^-7 Hz), so only one home knows `nuc` is settled (found independently by the plotting slice). [AUTHOR] Repro: `sed -n 180,198p solarwindpy/core/units_constants.py; sed -n 139,170p solarwindpy/plotting/labels/base.py; git grep -n -E 'nuc' -- solarwindpy/plotting/labels/base.py solarwindpy/core/units_constants.py`
- **F52** [P2] `solarwindpy/core/plasma.py:2033`: one quantity, three names: method `heat_flux`, alias `qpar` (`plasma.py:2096`) and `Units.qpar` (`units_constants.py:196`), label key `q`; its siblings `kinetic_energy_flux`/`Wk` and `specific_entropy`/`S` put the long name in `Units` (`units_constants.py:197`, `:199`) and the alias in the labels, while `heat_flux` puts its alias in `Units` and a third name in the labels. [AUTHOR] Repro: `git grep -n -E "def heat_flux|def qpar|qpar: float|\"q\": " -- solarwindpy/core solarwindpy/plotting/labels/base.py`
- **F53** [P1] `solarwindpy/core/units_constants.py:21`: the comment "We rely on views via DataFrame.xs ... do not .copy(deep=True)" is copied into four modules (`alfvenic_turbulence.py:34`, `plasma.py:36`, `spacecraft.py:14`, `units_constants.py:21`), and `units_constants.py` never calls `.xs` (positive control: the count search finds the calls in `plasma.py`). Repro: `git grep -n "We rely on views via DataFrame.xs" -- solarwindpy; git grep -c "\.xs(" -- solarwindpy/core/units_constants.py solarwindpy/core/plasma.py`
- **F54** [P5] `solarwindpy/examples/__init__.py:1`: two of 51 tracked package modules carry a `Spent-When:` purge-system header in shipped code (`examples/__init__.py:1`, `plotting/binned.py:1`), so shipped modules follow two header forms; whether the purge system belongs in shipped code is the author's call. [AUTHOR] Repro: `git grep -l "Spent-When" -- 'solarwindpy/*.py'; git ls-files 'solarwindpy/*.py' | wc -l`

### core

**Predicted:** the `core/__init__.py` docstring ("each class is imported from the module that defines it") and the `Core`/`Base` contract (logger, units, constants, `set_data` validates, `mi_tuples` names the levels) predict: one class family per module; every data-backed class validates through shared `Core`/`Base` helpers rather than its own checks; every formula has one home (an `Ion` computes a per-species quantity, a `Plasma` gathers it over species, a `Vector` or `Tensor` computes magnitudes); every sibling pairs a long name with one short alias, and a name means the same thing on every class that has it.
**Found:** The time-order machinery fits the prediction well (`_time_disorder`, `_put_in_time_order`, `_time_checked`, all in `base.py`), and the `Ion`/`Plasma` split holds for `n`, `rho`, `w`, `pth`, `temperature`, `Wk`. It breaks in four places: validators for level names and `+` species live in leaves (`Plasma`, `Ion`) instead of `Core`/`Base`, and several checks are `assert`s; four formulas have a second home (scalar thermal speed, sound speed, anisotropy, the Alfvén-unit coefficient) and two code paths reimplement `Vector.mag` with a different missing-data rule; `Plasma` repeats one gather block six times; and several names mean different things on different siblings (`r`, `rho`, `thermal_speed`, `velocity`). Two of these drifts change results (F59, F63), and both contradict the author's recorded missing-data rule.

Descended into: `base.py` (whole), `ions.py` (whole), `vector.py`, `tensor.py`, `spacecraft.py` (whole), `plasma.py` (module docstring, `save`, `load_from_file`, species and container methods, `set_data`, every quantity through `lnlambda`, `specific_entropy`, `kinetic_energy_flux`), `alfvenic_turbulence.py` (`set_data` and the energy properties), `abundances.py` (whole), `units_constants.py` (whole).

#### Shared validation (Core, Base, and the leaves)

- **F55** [P1] `solarwindpy/core/plasma.py:740`: `_require_level_names` is a static method on `Plasma`, so `Ion.set_data` cannot use it and re-checks level names by hand (`ions.py:143`, `data.columns.names == ["M", "C", "S"]`); mirror `base.py:Core._require_dataframe` by moving it to `Core`. Repro: `git grep -n -E "_require_level_names|columns.names ==|columns.names !=" -- solarwindpy/core`
- **F56** [P1] `solarwindpy/core/base.py:453`: the rule "a species string may not contain `+`" has three homes: `Base._clean_species_for_setting` (`base.py:453`), `Ion.set_species` (`ions.py:125`), and an `assert` in `Plasma._set_ions` (`plasma.py:562`) that `Base._clean_species_for_setting` has already made unreachable. Repro: `git grep -n -E "\"\+\" in s|\"\+\" not in s|'\+' in species|\"\+\" in species" -- solarwindpy/core`
- **F57** [P5] `solarwindpy/core/plasma.py:657`: `set_spacecraft` and `_set_auxiliary_data` (`plasma.py:720`) check input type with `assert`, where `base.py:Core._require_dataframe` raises `TypeError` with a message; under `python -O` a wrong type surfaces as an unrelated `AttributeError`. Repro: `conda run -n solarwindpy python -O -c 'import solarwindpy as swp; swp.examples.load_plasma().set_spacecraft("not a spacecraft")' 2>&1 | command grep Error`
- **F58** [P5] `solarwindpy/core/spacecraft.py:244`: `Spacecraft.set_data` validates column shape and index type with six `assert`s (`spacecraft.py:244` to `spacecraft.py:268`); `core/` holds 14 `assert`s, 10 of them input checks (the other four, `abundances.py:145` and `plasma.py:561`, `:1510`, `:1926`, are internal invariants), while the merged `rm-core-solar` unit turned the column-name asserts of `set_auxiliary_data` into `ValueError`. Mirror `plasma.py:Plasma._require_level_names`. Repro: `git grep -n "assert " -- 'solarwindpy/core/*.py'`

#### Formulas with a second home

- **F59** [P1] `solarwindpy/core/plasma.py:1271`: `Plasma.anisotropy` recomputes `ions.py:Ion.anisotropy` without its `skipna=False`, so at a time where the species is masked, `Plasma.anisotropy("p1")` is 1.0 (the product of nothing) where `plasma.p1.anisotropy` is NaN; the multi-species branch (`plasma.py:1269`) does the same. This contradicts the missing-data rule of the merged `scalar-w-nan` unit (batch file § scalar-w-nan). Changes a result. [AUTHOR] Repro: `conda run -n solarwindpy python -c 'import numpy as np, solarwindpy as swp; from solarwindpy.core.plasma import Plasma; d=swp.examples.load_plasma().data.copy(); d.iloc[0, d.columns.get_loc(("w","par","p1"))]=np.nan; q=Plasma(d,"a","e","p1","p2"); print(q.anisotropy("p1").iloc[0], q.p1.anisotropy.iloc[0])' 2>/dev/null`
- **F60** [P1] `solarwindpy/core/plasma.py:928`: the scalar thermal speed `w = sqrt((w_par^2 + 2 w_per^2)/3)` is computed in `Plasma.set_data` and again in `tensor.py:116` `Tensor.magnitude`, whose docstring says "This is the combination Plasma uses"; mirror `Tensor.magnitude` as the one home. Repro: `sed -n 928p solarwindpy/core/plasma.py; sed -n 111,116p solarwindpy/core/tensor.py`
- **F61** [P1] `solarwindpy/core/plasma.py:1505`: `Plasma.sound_speed` repeats the formula line of `ions.py:275` `Ion.cs` verbatim instead of gathering `Ion.cs` over species as `Plasma.pth` gathers `Ion.pth`. Repro: `git grep -n "cs = pth.divide(rho, axis=0).multiply(gamma)" -- solarwindpy/core`
- **F62** [P1] `solarwindpy/core/alfvenic_turbulence.py:362`: the Alfvén-unit coefficient `units.b / (sqrt(units.rho * mu0) * units.v)` is written again in `plasma.py:1538` `Plasma.ca` (with `units.ca`, equal to `units.v`). Repro: `git grep -n -E "units\.b / \(" -- solarwindpy/core; sed -n 363p solarwindpy/core/alfvenic_turbulence.py`
- **F63** [P1] `solarwindpy/core/spacecraft.py:182`: `Spacecraft.distance2sun` sums squared components with pandas' default `skipna=True`, so a missing `x` gives a finite distance where `vector.py:Vector.mag` (`skipna=False`) gives NaN; mirror `Vector.mag`. Changes a result. [AUTHOR] Repro: `conda run -n solarwindpy python -c 'import numpy as np, solarwindpy as swp; from solarwindpy.core.spacecraft import Spacecraft; d=swp.examples.load_plasma().spacecraft.data.copy(); d.iloc[0, d.columns.get_loc(("pos","x"))]=np.nan; s=Spacecraft(d,"PSP","HCI"); print(s.distance2sun.iloc[0], s.position.mag.iloc[0])' 2>/dev/null`
- **F64** [P1] `solarwindpy/core/alfvenic_turbulence.py:389`: the `raffaella_version` branch rebuilds `Vector.mag` and `Vector.rho` from the position columns (`r_rtn`, `rho_rtn`) instead of building a `Vector`, and converts m to km with a literal `1e-3` (`alfvenic_turbulence.py:400`) beside `Units.v = 1e3`. Behaviour is fixed by the merged Raffaella decision, so this is a form change only; mirror `vector.py:Vector.rho`. Repro: `sed -n 389,400p solarwindpy/core/alfvenic_turbulence.py`
- **F65** [P1] `solarwindpy/core/alfvenic_turbulence.py:387`: the solar sidereal rotation rate `omega = 2.865e-6` rad/s is a local literal, the one physical constant in the package outside `units_constants.py` (positive control in the package layer). Mirror `units_constants.py:_misc_constants`. Repro: `git grep -n "2.865e-6" -- solarwindpy`
- **F66** [P1] `solarwindpy/core/alfvenic_turbulence.py:200`: `e_plus`, `e_minus`, `kinetic_energy`, `magnetic_energy` (`:200`, `:211`, `:222`, `:235`) sum components with the default `skipna=True`, so a missing component gives a partial energy, unlike `Vector.mag`'s `skipna=False`; suspicion only, the author holds whether the fluctuation energies follow the within-species rule. [AUTHOR] Repro: `git grep -n -E "0\.5 \* self\.(zp|zm|v|b)\.pow\(2\)\.sum\(axis=1\)" -- solarwindpy/core/alfvenic_turbulence.py`
- **F67** [P1] `solarwindpy/core/units_constants.py:58`: the species roster (`e`, `p`, `p1`, `p2`, `pm`, `p_bimax`, `a`, `a1`, `a2`, `a_bimax`) is written out in five tables, and `_charges` equals `_charge_states * e` entry for entry, so it is derivable rather than a second fact. Repro: `conda run -n solarwindpy python -c 'import solarwindpy as swp; from scipy.constants import e; c=swp.core.units_constants.Constants(); print((c.charges == c.charge_states*e).all())'; command grep -c '"p_bimax"' solarwindpy/core/units_constants.py`

#### Copied blocks inside `Plasma`

- **F68** [P1] `solarwindpy/core/plasma.py:1044`: the gather block `{s: self.ions.loc[s].<q> for s in slist}` then `pd.concat(..., names=["S"])` then a species sum is written six times (`:1044`, `:1076`, `:1109`, `:1150`, `:1181`, `:2217`), plus a two-species variant without the sum in `nuc` (`:1761`), several restating the `min_count=1` rule in a comment. No existing form fits exactly; the nearest is the shared static helper `plasma.py:Plasma._species_weighted_mean`. Repro: `git grep -n -E "\{s: self\.ions\.loc\[s\]\." -- solarwindpy/core/plasma.py`
- **F69** [P1] `solarwindpy/core/plasma.py:1146`: `include_dynamic = False; if include_dynamic: raise NotImplementedError` is dead code copied into `pth`, `beta` and `anisotropy` (`:1146`, `:1228`, `:1260`), the last with unreachable lines after the `raise`. Repro: `git grep -n -A4 "include_dynamic = False" -- solarwindpy/core/plasma.py`
- **F70** [P1] `solarwindpy/core/plasma.py:370`: `Plasma.save` defines its "modifier_fcn must be a FunctionType. You passes" message twice (`:354`, `:370`) and writes the type check three times; the HDF key defaults `"FC"`, `"SC"`, `"FC_AUX"` are repeated in `save` (`:308`) and `load_from_file` (`:413`). Repro: `git grep -n -E "You passes|dkey=\"FC\"|sckey=\"SC\"|akey=\"FC_AUX\"" -- solarwindpy/core/plasma.py`
- **F71** [P1] `solarwindpy/core/plasma.py:450`: "species are the non-empty `S` labels" is written in `load_from_file` and again in `examples/__init__.py:87` (sorted there, unsorted here). Repro: `git grep -n -E "get_level_values\(\"S\"\)\.unique\(\) if s" -- solarwindpy`
- **F72** [P1] `solarwindpy/core/abundances.py:138`: the key-type dispatch (str to `Symbol`, int to `Z`, else `ValueError`) is written in both `get_element` and `get_comment` (`abundances.py:180`). Repro: `git grep -n -B1 -A4 'level = "Symbol"' -- solarwindpy/core/abundances.py`

#### Names and documentation against their siblings

- **F73** [P2] `solarwindpy/core/spacecraft.py:116`: `Spacecraft.r` returns the position `Vector`, while `vector.py:203` `Vector.r` returns the magnitude `Series`; `plasma.sc.r` and `plasma.sc.r.r` mean different things under one name. [AUTHOR] Repro: `conda run -n solarwindpy python -c 'import solarwindpy as swp; p=swp.examples.load_plasma(); print(type(p.sc.r).__name__, type(p.b.r).__name__)' 2>/dev/null`
- **F74** [P2] `solarwindpy/core/vector.py:109`: `Vector.rho` is the xy-plane magnitude while `Ion.rho` (`ions.py:213`) and `Plasma.rho` are mass density, so `plasma.p1.rho` and `plasma.p1.v.rho` share a name across unrelated quantities. [AUTHOR] Repro: `git grep -n -A3 "def rho" -- solarwindpy/core`
- **F75** [P2] `solarwindpy/core/ions.py:182`: `Ion.thermal_speed` returns a `Tensor` while `Plasma.thermal_speed` returns a `DataFrame`; `Ion.velocity` and `Plasma.velocity` both return a `Vector`, so the pair predicts a `Tensor`. [AUTHOR] Repro: `conda run -n solarwindpy python -c 'import solarwindpy as swp; p=swp.examples.load_plasma(); print(type(p.p1.thermal_speed).__name__, type(p.thermal_speed("p1")).__name__, type(p.p1.velocity).__name__, type(p.velocity("p1")).__name__)' 2>/dev/null`
- **F76** [P2] `solarwindpy/core/alfvenic_turbulence.py:138`: `AlfvenicTurbulence.velocity` and `.bfield` (`:148`) return DataFrames, while every sibling `velocity`/`bfield` in `core` returns a `Vector`/`BField`. [AUTHOR] Repro: `git grep -n -A3 -E "def (velocity|bfield)\(self\)" -- solarwindpy/core`
- **F77** [P2] `solarwindpy/core/alfvenic_turbulence.py:398`: the local `cos_colat = rho_rtn / r_rtn` holds the cosine of latitude (the sine of colatitude), which is what the class Notes call `cos(lambda)`; the value is right and the name is mis-pointed, the class of defect behind the earlier `Vector.latitude`/`colatitude` swap. Private local, no API change. Repro: `sed -n 398p solarwindpy/core/alfvenic_turbulence.py; command grep -n "cos.lambda" solarwindpy/core/alfvenic_turbulence.py`
- **F78** [P2] `solarwindpy/core/vector.py:53`: `Vector.__call__` and `Tensor.__call__` (`tensor.py:52`) return `self.__getattr__(component)`, which no class defines (the delegating `Base.__getattr__` was removed long ago), so `plasma.b("x")` always raises `AttributeError`; documented public API, untested. Fix or remove. [AUTHOR] Repro: `conda run -n solarwindpy python -c 'import solarwindpy as swp; swp.examples.load_plasma().b("x")' 2>&1 | command grep AttributeError; git log --oneline -S "def __getattr__" -- solarwindpy/core/base.py`
- **F79** [P2] `solarwindpy/core/ions.py:111`: `Ion.set_species` is public while its sibling `Plasma._set_species` (`plasma.py:507`) is private; `Ion` lacks the long name `sound_speed` (`ions.py:264`, `cs` only) that `Plasma` pairs with `cs`, and `Tensor` lacks the short `mag` that `Vector` pairs with `magnitude` (`tensor.py:95`). [AUTHOR] Repro: `git grep -n -E "def (_?set_species|sound_speed|cs|mag|magnitude)\(" -- solarwindpy/core`
- **F80** [P2] `solarwindpy/core/spacecraft.py:211`: `set_frame_name` refuses every spacecraft but `WIND` and `PSP` and every frame but `GSE` and `HCI` with `NotImplementedError`; the class docstring does not say a name list exists. [AUTHOR] Repro: `sed -n 209,212p solarwindpy/core/spacecraft.py`
- **F81** [P2] `solarwindpy/core/alfvenic_turbulence.py:333`: the `set_data` docstring documents an `auto_reindex` keyword that the signature does not have. Repro: `git grep -n "auto_reindex" -- solarwindpy`
- **F82** [P2] `solarwindpy/core/plasma.py:4`: the module docstring is a 2018 "Propoded Updates" list whose last item says `_conform_species` moved to `base.Base` (it is on `Core`, `base.py:133`); it records history, not the module. Repro: `sed -n 4,25p solarwindpy/core/plasma.py; git grep -n "def _conform_species" -- solarwindpy/core`
- **F83** [P2] `solarwindpy/core/plasma.py:337`: the `save` docstring documents `spacecraft_modifier_fcn` for the parameter `sc_modifier_fcn`, and gives `dkey`, `sckey`, `akey` as `None` (`:323`) while their defaults are `"FC"`, `"SC"`, `"FC_AUX"`. Repro: `sed -n 306,312p solarwindpy/core/plasma.py; sed -n 323,337p solarwindpy/core/plasma.py`
- **F84** [P2] `solarwindpy/core/units_constants.py:4`: the module docstring says every quantity `Plasma` stores has an entry in `Constants`; the per-quantity entries are in `Units`, and `anisotropy`, `afsq`, `vdf_ratio` have none. Repro: `sed -n 4,6p solarwindpy/core/units_constants.py; command grep -n -E "^    [a-z_]+: float" solarwindpy/core/units_constants.py`

### examples

**Predicted:** `examples` is the layer above `core`, so I expect it to be a thin client: it reads its own data files, uses `core`'s column conventions and helpers (`Base.mi_tuples`, the species rule of `Plasma`), and writes example columns under the labels `Spacecraft` expects.
**Found:** It is thin and correct (its doctest and `tests/test_examples.py` pass), but it rebuilds the `(M, C, S)` index by hand (F50), repeats the species rule (F71), keeps its CSVs in `core/data/` (F49), sits outside the layer contract (F48), and its spacecraft CSV uses labels that differ from `Spacecraft`'s, so the loader carries a translation table.

- **F85** [P2] `solarwindpy/examples/__init__.py:92`: the spacecraft CSV names its measurements `pos_HCI`, `v_HCI`, `Carr`, and the loader renames them to the `pos`, `v`, `carr` that `Spacecraft` reads, so the example data and the class disagree on the labels the example exists to teach. Repro: `head -1 solarwindpy/core/data/example_spacecraft.csv; sed -n 90,95p solarwindpy/examples/__init__.py`

### fitfunctions

**Predicted:** From `fitfunctions/__init__.py`: one abstract `FitFunction` in `core.py`; one module per model family, each sibling class writing only `function`, `p0`, `TeX_function`; shared helpers rather than per-class copies of a formula; `plots.py` and `tex_info.py` as collaborators built by `make_fit`; `TrendFit` composing fit functions over bins; no physical constants (pure math); configuration through `__init__` keywords such as `guess_x0`.
**Found:** The layout holds. The sibling contract breaks in four places: the same Gaussian and Heaviside kernels are rewritten per class (and the step kernels disagree at the step), the six hinge classes name and default one concept three ways, `FitFunction.residuals` and `FFPlot.residuals` share a name with opposite signs, and configuration arrives three ways (constructor keyword, post-construction setter, required keyword with a `None` default). No physical constant appears.

- **F86** [P2] `solarwindpy/fitfunctions/core.py:713`: [AUTHOR] `FitFunction.residuals` returns observed minus fitted (with `use_all=`), while `FFPlot.residuals` at `solarwindpy/fitfunctions/plots.py:595` returns model minus observation (with `robust=`); one name, opposite signs, disjoint keywords, and the percent formula written twice. `rm-fit-plots` (commit 6e2db117) set FFPlot's contract deliberately, so the author picks which sign governs. Repro: `conda run -n solarwindpy python -c "import numpy as np; from solarwindpy.fitfunctions.lines import Line; x=np.arange(10.); y=2*x+1; y[3]+=1; f=Line(x,y); f.make_fit(loss='linear'); print(f.residuals()[3], f.plotter.residuals()[3])"`
- **F87** [P1] `solarwindpy/fitfunctions/composite.py:209`: the Gaussian kernel `A * exp(-0.5 * ((x - mu) / sigma) ** 2)` is written five times (`gaussians.py:93` in `Gaussian`, `gaussians.py:157` in `GaussianNormalized`, `composite.py:209`, `composite.py:388`, `composite.py:563`) although `gaussians.py:_weighted_moments` already shows the shared module-helper form the composites import. Repro: `git grep -n "arg = -0.5 \* (((x - mu)" solarwindpy/fitfunctions`
- **F88** [P8] `solarwindpy/fitfunctions/heaviside.py:123`: [AUTHOR] suspicion. The step value at `x == x0` is `0.5*(y0+y1)` in `HeavySide` (so f(x0) = y1*(y0+y1)/2 + y0, which mixes y squared into a y-valued model and gives 7 for levels 4 and 1), 0.5 in `GaussianPlusHeavySide` (`composite.py:212`, the midpoint 2.5), and 1.0 in `GaussianTimesHeavySidePlusHeavySide` (`composite.py:566`, both pieces on at x0). The value is documented and locked by `tests/fitfunctions/test_heaviside.py:170`. Repro: `conda run -n solarwindpy python -c "import numpy as np; from solarwindpy.fitfunctions.heaviside import HeavySide as H; from solarwindpy.fitfunctions.composite import GaussianPlusHeavySide as G; x=np.linspace(0,10,50); X=np.array([4.,5.,6.]); print(H(x,x).function(X,x0=5.,y0=1.,y1=3.), G(x,x).function(X,x0=5.,y0=1.,y1=3.,mu=0.,sigma=1.,A=0.))"`
- **F89** [P1] `solarwindpy/fitfunctions/composite.py:285`: the Gaussian's LaTeX is written four times and has drifted: `Gaussian.TeX_function` uses `\left(\frac{x-\mu}{\sigma}\right)`, the three composites use bare parentheses. Repro: `conda run -n solarwindpy python -c "import solarwindpy.fitfunctions as ff; ff.available()" | command grep -i gauss`
- **F90** [P2] `solarwindpy/fitfunctions/composite.py:182`: all three composite classes name their model closure `gaussian_heavy_side`, so `function.__name__` does not tell `GaussianPlusHeavySide`, `GaussianTimesHeavySide` and `GaussianTimesHeavySidePlusHeavySide` apart (siblings in `gaussians.py` and `heaviside.py` name the closure after the class's model). Repro: `git grep -n "def gaussian_heavy_side" solarwindpy/fitfunctions`
- **F91** [P2] `solarwindpy/fitfunctions/hinge.py:256`: [AUTHOR] the six `Hinge` children name the data split point three ways (`guess_xh` in `HingeSaturation` and `HingeAtPoint`, `guess_xs` in `TwoLine` and `Saturation`, `guess_h` in `HingeMin` and `HingeMax`) with three defaults (326, 425, 400) beside the single reference hinge `Hinge._XH = 433` (`hinge.py:120`); `guess_xh` itself means 326 in one class and 400 in another. `rm-fit-models` already pruned `guess_yh` from `HingeAtPoint` and `guess_s` from `Saturation`, the same cleanup half done. Repro: `conda run -n solarwindpy python -c "import inspect; from solarwindpy.fitfunctions import hinge as h; [print(c, {k:v.default for k,v in inspect.signature(getattr(h,c).__init__).parameters.items() if k.startswith('guess')}) for c in ('HingeSaturation','TwoLine','Saturation','HingeMin','HingeMax','HingeAtPoint')]"`
- **F92** [P3] `solarwindpy/fitfunctions/hinge.py:264`: [AUTHOR] `HingeSaturation` exposes its guess as a tuple property `saturation_guess`, while its five siblings expose a scalar property named after the keyword (`guess_xs`, `guess_h`, `guess_xh`); four children also repeat the same store-and-property block (`hinge.py:446`, `660`, `897`, `1165`) that `Hinge` could hold once. Repro: `command grep -n "self._guess_\|self._saturation_guess" solarwindpy/fitfunctions/hinge.py`
- **F93** [P5] `solarwindpy/fitfunctions/CONTRIBUTING.md:135`: the contributor guide lists `x0 = 425  # Solar wind speed` as a prohibited hardcoded value, while `TwoLine` and `Saturation` ship `guess_xs=425.0` and their docstrings call it appropriate for solar wind speed analysis (`hinge.py:424`, `hinge.py:637`); the rule and the code it governs disagree. Repro: `git grep -n "425" solarwindpy/fitfunctions`
- **F94** [P2] `solarwindpy/fitfunctions/composite.py:248`: five `# TODO: Convert to data-driven p0 estimation (see GH issue #XX)` placeholders name no issue, and three of them sit inside rendered docstring Notes sections, so they print in `help()` and the API docs. Repro: `git grep -n "#XX" solarwindpy/fitfunctions`
- **F95** [P2] `solarwindpy/fitfunctions/core.py:757`: the `FitFunction.residuals` Notes section is provenance about a removed TODO and a nonexistent `set_extrema`, not a statement of behavior. Repro: `sed -n 755,759p solarwindpy/fitfunctions/core.py`
- **F96** [P3] `solarwindpy/fitfunctions/exponentials.py:118`: [AUTHOR] `ExponentialCDF` takes its fixed amplitude through a setter `set_y0` that must be called after construction (otherwise `make_fit` raises `AttributeError`), while siblings take configuration as constructor keywords (`GaussianTimesHeavySide(guess_x0=...)`, `HeavySide(guess_y0=...)`); the attribute is `y0` but `TeX_function` and the annotation call it `A` (`exponentials.py:148`). Repro: `conda run -n solarwindpy python -c "import numpy as np; from solarwindpy.fitfunctions.exponentials import ExponentialCDF as E; x=np.arange(1.,10); E(x,1-np.exp(-x)).make_fit()" 2>&1 | command grep Error`
- **F97** [P2] `solarwindpy/fitfunctions/composite.py:340`: [AUTHOR] `GaussianTimesHeavySide.__init__(guess_x0=None)` and its sibling `GaussianTimesHeavySidePlusHeavySide` advertise an optional argument and raise `ValueError` when it is omitted; `HeavySide(guess_x0=None)` really is optional. The same optional-looking-required form recurs at `instabilities/verscharen2016.py:115` (F104). Repro: `conda run -n solarwindpy python -c "import numpy as np; from solarwindpy.fitfunctions.composite import GaussianTimesHeavySide as G; G(np.arange(5.), np.arange(5.))" 2>&1 | command grep ValueError`
- **F98** [P3] `solarwindpy/fitfunctions/core.py:646`: caller input is validated with bare `assert` at five sites in fitfunctions (`core.py:262`, `263`, `646`, `exponentials.py:128`, `trend_fits.py:433`), while `core.py` defines `InvalidParameterError` for exactly this and raises it in three places (three further asserts, `plots.py:175`, `176` and `tex_info.py:199`, are internal invariants, a separate question for the author); an inverted `xoutside` gives a message-less `AssertionError`, and nothing at all under `python -O`. Repro: `conda run -n solarwindpy python -c "import numpy as np; from solarwindpy.fitfunctions.lines import Line; Line(np.arange(5.),np.arange(5.),xoutside=(3,1))" 2>&1 | command grep Error`
- **F99** [P1] `solarwindpy/fitfunctions/plots.py:23`: [AUTHOR] `AxesLabels` and `LogAxes` are defined identically in `fitfunctions/plots.py` (lines 23 and 24) and `plotting/base.py` (lines 30 and 35); the layer contract lets fitfunctions import plotting (as `trend_fits.py:19` does), but both names are in `plots.__all__`, so retiring the copy changes a public name's defining module. Repro: `git grep -n "AxesLabels = namedtuple\|LogAxes = namedtuple" solarwindpy`
- **F100** [P3] `solarwindpy/fitfunctions/plots.py:652`: `FFPlot.set_log(**kwargs)` accepts any key and builds `LogAxes(**log)`, while the sibling plotter API `plotting/base.py:161` is `set_log(x=None, y=None)`; `FFPlot.set_labels` (`plots.py:636`) re-implements the pop-and-reject logic of `plotting/base.py:239`. Repro: `command grep -n "def set_log\|def set_labels" solarwindpy/fitfunctions/plots.py solarwindpy/plotting/base.py`
- **F101** [P1] `solarwindpy/fitfunctions/core.py:308`: `_init_logger` is written seven times across the package with the same one-line body (`core/base.py:123`, `fitfunctions/core.py:308`, `instabilities/verscharen2016.py:201`, `plotting/base.py:71`, `plotting/labels/base.py:344`, `solar_activity/base.py:36`, `solar_activity/icme/icmecat.py:164`); the two in this scope copy `core/base.py:Base._init_logger`. Merged here: the solar_activity slice found that `solar_activity/icme/icmecat.py:164` re-implements `solar_activity/base.py:Base` (lines 31-41) line for line where subclassing `Base` would serve (F139), and the plotting slice found the same copy behind F133. Repro: `git grep -n "def _init_logger" solarwindpy`
- **F102** [P2] `solarwindpy/fitfunctions/trend_fits.py:98`: [AUTHOR] `TrendFit` spells the per-bin concept several ways in one class (`popt_1d`, `psigma_1d`, `popt1d_keys`, `make_1dfits`, `make_ffunc1ds`, `plot_all_popt_1d`, `plot_1d_popt_and_trend`), so no one name predicts its sibling. Repro: `command grep -n "def \w*1d\w*" solarwindpy/fitfunctions/trend_fits.py`
- **F103** [P2] `solarwindpy/fitfunctions/trend_fits.py:13`: `import logging  # noqa: F401` imports a module the file never uses and suppresses the lint that would say so (in `core.py` and `plots.py` the same line is used). Repro: `command grep -c "logging\." solarwindpy/fitfunctions/trend_fits.py`

Found none, with controls:
- No physical constant or unit is defined in either subpackage, so P1 against `core/units_constants.py` has nothing to merge. Search: `git grep -n -E "scipy.constants|physical_constants|units_constants|k_B|m_p\b" solarwindpy/fitfunctions solarwindpy/instabilities | wc -l` gives 0; the same search on `solarwindpy/core` gives 33.
- No import reaches outside the allowed layers: `git grep -n "from \.\.\(core\|tools\|plotting\)" solarwindpy/fitfunctions solarwindpy/instabilities` lists four imports, all from `plotting`, which the `layers` contract in `pyproject.toml` places below both subpackages.
- `GaussianLn.normal_parameters` (`gaussians.py:297`) matches the standard log-normal mean and standard deviation, checked against `tests/fitfunctions/test_gaussians.py:236`. Not a finding.

#### hinge module

**Predicted:** From the `Hinge` class docstring (`hinge.py:79`): "A subclass writes its model (`function` and `TeX_function`), its estimate (`_estimate`) and the translation of the reference hinge to its parameters (`_reference_start`)". So each child defines those four members and nothing else, and the reference hinge lives only in `Hinge`.
**Found:** The reference hinge has one home (`Hinge._XH` and siblings). Five children also carry their own guess keyword, store and property, under three names and three defaults (F91, F92, F93), which the parent's description does not predict.

#### composite and heaviside modules

**Predicted:** From the composite class names, `GaussianPlusHeavySide` is `Gaussian` plus `HeavySide`, so each composite builds on the `Gaussian` and `HeavySide` models rather than restating them.
**Found:** Each composite restates the Gaussian kernel and its own step kernel (F87, F89, F90), and the restated steps disagree with `HeavySide` at `x == x0` (F88).

#### plots module

**Predicted:** From `trend_fits.py:19`, which already imports `plotting.tools.subplots`, fitfunctions' plotter reuses the plotting layer's axis vocabulary.
**Found:** `FFPlot` redefines `AxesLabels` and `LogAxes` and re-implements `set_labels` with a different `set_log` signature (F99, F100); its `residuals` diverges from `FitFunction.residuals` (F86).

### instabilities

**Predicted:** From `instabilities/__init__.py`: `verscharen2016` holds the Table 1 coefficients once and the Eq. (5) threshold once, with a classifier and a contour plotter that both read those; `beta_ani` holds plotting wrappers. The growth rates and instability names live in one index each. The two classes in `verscharen2016` share one vocabulary for growth rate.
**Found:** The threshold formula (`beta_ani_inst`) and the coefficient table (`insta_params`) each have one home, and both classes call them. The growth-rate set and the instability names are re-typed in several structures, the two classes name growth rate differently, and the module-name contrast set mixes a citation (`verscharen2016`) with a quantity (`beta_ani`) whose module holds only a `Hist2D` subclass.

- **F104** [P2] `solarwindpy/instabilities/verscharen2016.py:115`: `beta_ani_inst(beta, a=None, b=None, c=None)` defaults every coefficient to None and then raises `TypeError` from `float(None)`; the signature says optional, the body says required (the F97 form). Repro: `conda run -n solarwindpy python -c "from solarwindpy.instabilities.verscharen2016 import beta_ani_inst; beta_ani_inst(1.0)" 2>&1 | command grep TypeError`
- **F105** [P8] `solarwindpy/instabilities/verscharen2016.py:141`: [AUTHOR] suspicion. The doctest calls `beta_ani_inst` with `a=0.367, b=-0.408, c=0.011`; the table's AIC row at growth rate -4 is `a=0.367, b=0.364, c=0.011`, and -0.408 is the FMW `a`. The printed thresholds are therefore for no published instability. Repro: `sed -n 141p solarwindpy/instabilities/verscharen2016.py; conda run -n solarwindpy python -c "from solarwindpy.instabilities.verscharen2016 import insta_params as p; print(p.loc[('AIC',-4)].to_dict())"`
- **F106** [P1] `solarwindpy/instabilities/verscharen2016.py:91`: the growth-rate set {-4, -3, -2} is typed out in the `insta_params` keys (line 40), the `_plot_contour_kwargs` index (lines 91 to 103), the `plot_gamma` assert (line 513), the legend handles (lines 573 to 586) and the legend labels (lines 597 to 599); the contour style table repeats each instability's colour and marker three times, where colour and marker vary by instability and line style by growth rate. `_inst_type_idx` (line 32) is the one-index form to mirror. Repro: `command grep -n -- "-4\|\[-2, -3, -4\]" solarwindpy/instabilities/verscharen2016.py`
- **F107** [P1] `solarwindpy/instabilities/verscharen2016.py:392`: the display labels of `stability_map` (`"Between\nAIC &\nMM"`, `"Between\nFMW &\nOFI"`, line 242) are re-typed as lookup keys in `_calc_stability_bin`, so editing a colourbar label breaks the classifier. Repro: `command grep -n "Between" solarwindpy/instabilities/verscharen2016.py`
- **F108** [P2] `solarwindpy/instabilities/verscharen2016.py:110`: `_instability_tests` orders its fields `AIC, MM, FMW, OFI`, while `_inst_type_idx` and every table use `AIC, FMW, MM, OFI`; lookups are by name so results agree, but the two orders invite positional misuse. Repro: `conda run -n solarwindpy python -c "from solarwindpy.instabilities.verscharen2016 import _instability_tests as t, _inst_type_idx as i; print(t._fields, list(i))"`
- **F109** [P2] `solarwindpy/instabilities/verscharen2016.py:170`: [AUTHOR] `stability_bin` is documented as an "Integer label" but is float64, because the `fill` placeholder (line 210) is `-9999.0`. Repro: `conda run -n solarwindpy python -c "import pandas as pd; from solarwindpy.instabilities.verscharen2016 import StabilityCondition as S; print(S(-3, pd.Series([1.,2.]), pd.Series([1.,1.])).stability_bin.dtype)"`
- **F110** [P2] `solarwindpy/instabilities/verscharen2016.py:457`: [AUTHOR] one concept, three names: `StabilityCondition(growth_rate=...)`, `StabilityContours.plot_contours(plot_gamma=...)` and the loop variable `gamma` at line 509; the condition fixes it at construction while the contours choose it at plot time. Repro: `command grep -n "growth_rate\|plot_gamma" solarwindpy/instabilities/verscharen2016.py`
- **F111** [P2] `solarwindpy/instabilities/verscharen2016.py:290`: the `norm` TODO asks for a rename to `color_norm` "for consistancy w/ plotting code", but no `color_norm` exists anywhere in the package, so the TODO points at a convention that is not there. Repro: `git grep -n "color_norm" solarwindpy`
- **F112** [P3] `solarwindpy/instabilities/verscharen2016.py:435`: four bare `assert` checks validate caller input in this module (lines 340, 435, 479, 513; lines 449 and 550 are internal invariants), the F98 form; `StabilityContours.set_beta` rejects a `pandas.Series`, the type `StabilityCondition.set_beta_ani` is documented to take, so the sibling classes accept different input types for the same beta. Repro: `command grep -n "assert " solarwindpy/instabilities/verscharen2016.py`
- **F113** [P1] `solarwindpy/instabilities/beta_ani.py:71`: `species.replace("_bimax", "")` restates the `p_bimax` to `p` mapping already held at `plotting/labels/base.py:26`; the TeX output is identical either way, and the strip only changes the save path (`R_T_p` against `R_T_p_bimax`). Repro: `conda run -n solarwindpy python -c "from solarwindpy.plotting.labels.base import TeXlabel as T; print(T(('R','T','p_bimax')).tex == T(('R','T','p')).tex, T(('R','T','p_bimax')).path)"`
- **F114** [P2] `solarwindpy/instabilities/beta_ani.py:1`: [AUTHOR] within the module contrast set, `verscharen2016` names a source and `beta_ani` names a quantity, yet `beta_ani` holds no instability physics, only `BetaRPlot(Hist2D)`, which sets labels, log axes, a count floor and a colormap. A reader predicts thresholds in `beta_ani` and finds a plot. Repro: `command grep -n "^class\|^def\|^from" solarwindpy/instabilities/beta_ani.py`

### plotting

**Predicted:** `plotting/__init__.py` re-exports nothing (one import path per object) and lists
one module per plot type (`hist1d`, `hist2d`, `scatter`, `spiral`) plus a shared `base`, an
aggregation layer `agg_plot`, figure helpers `tools`, and a `labels` subpackage that is the only
home for axis strings and units. `binned` reads like a second aggregation module and may
duplicate `agg_plot`. Each plot class has one abstract parent, so the classes share a
constructor shape (`x, y, z, logx, logy, clip, mask`) and a `make_plot` shape. The test tree
holds one `test_<module>.py` per module.

**Found:** The module list matches. `binned` is not a duplicate: it is the data layer
(`_PlotSource`, `BinnedData`, the clip helpers) that `base` and `agg_plot` both import, so the
layout holds. Two plot classes share no aggregating parent: `Hist1D` and `Hist2D` derive from
`AggPlot`, `SpiralPlot2D` derives only from `PlotWithZdata` and re-implements the `AggPlot`
pieces it needs. The style path is defined twice. The contrast set of class names collides
across layers (four `Base`, two `Ion`). Descending into classes, labels and the test tree.

- **F115** [P1] `solarwindpy/plotting/tools.py:25`: `_STYLE_PATH` is defined a second time (first at `solarwindpy/plotting/__init__.py:14`), and `_use_style` (`tools.py:28`), its only reader, has no caller. Repro: `git grep -n -E '_STYLE_PATH|_use_style' -- solarwindpy tests`
- **F116** [P2] `solarwindpy/plotting/base.py:39`: four public classes are named `Base` (`core/base.py:344`, `plotting/base.py:39`, `plotting/labels/base.py:312`, `solar_activity/base.py:28`) and two `Ion` (`core/ions.py:20`, `plotting/labels/composition.py:11`); within the contrast set the name does not say which layer it belongs to, and `labels.composition.Ion` is a label, not an ion. The solar_activity slice adds that `solar_activity/base.py:28` `Base` is only a logger mixin, and that inside `solar_activity/plots.py:16` `base.Base` names plotting's `Base`. [AUTHOR] Repro: `git grep -n -E '^class (Base|Ion)[(:]' -- solarwindpy; git grep -n '^from ..plotting import base' -- solarwindpy/solar_activity`
- **F117** [P2] `solarwindpy/plotting/labels/datetime.py:1`: a public module named `datetime` reuses the stdlib name its siblings import (`from datetime import datetime` at `plotting/spiral.py:16`, `plotting/tools.py:20`); absolute imports keep them apart, but a caller who wants both must rename one, as `tests/plotting/test_integration.py` does (`import datetime as dt_labels`). [AUTHOR] Repro: `git grep -n -E '^from datetime import|labels import datetime' -- solarwindpy tests`

#### plot classes (base, agg_plot, hist1d, hist2d, scatter, spiral)

**Predicted:** `Base` owns labels, log flags, the save path and clipping; `PlotWithZdata` adds z;
`AggPlot` owns binning, `clim`, and `agg`. Siblings override only what differs, call
`set_log`/`set_labels`/`set_path("auto")` the same way in their constructors, and use the same
parameter order and defaults for parameters with the same name.

**Found:** The clip path is shared well (`Base.clip_data` delegates to
`binned._clip_to_quantiles`, and every class routes through `_store_clip`), which is the positive
control for this layer: every class routes `clip` through `_store_clip` and `Base.clip_data`.
Searching for a copy of the clipping body rather than its name
(`git grep -n -E 'quantile\(\[' -- solarwindpy/plotting`) finds the shared rule at `binned.py:89`
and one more rule, F118. Everything else in the prediction breaks somewhere too.

- **F118** [P1] `solarwindpy/plotting/agg_plot.py:359`: the `MemoryError` fallback in `calc_bins_intervals` clips at its own quantiles `[0.0005, 0.9995]` with its own `d.clip`, beside the shared rule `binned.py:_clip_to_quantiles` (`0.0001`, `0.9999`, `binned.py:87-89`). The fallback is deliberate and documented (`agg_plot.py:301-304`, a memory bound, not user clipping), so this is two percentile facts and two clipping implementations; whether one helper with a percentile argument serves both is the author's call. [AUTHOR] (bin edges change if the percentile moves) Repro: `git grep -n -E 'quantile\(\[|q[01] = 0\.' -- solarwindpy/plotting`

- **F119** [P1] `solarwindpy/plotting/spiral.py:932`: `SpiralPlot2D.set_clim` re-implements `AggPlot.set_clim` (`agg_plot.py:156`) and the two store different types, so `Hist2D(...).clim` is a `tuple` and `SpiralPlot2D(...).clim` a `RangeLimits`. [AUTHOR] (public type) Repro: `conda run -n solarwindpy python -c 'import numpy as np,pandas as pd;from solarwindpy.plotting.hist2d import Hist2D;from solarwindpy.plotting.spiral import SpiralPlot2D;x=pd.Series(np.random.default_rng(0).random(600));print(type(Hist2D(x,x,nbins=5).clim).__name__,type(SpiralPlot2D(x,x).clim).__name__)'`
- **F120** [P1] `solarwindpy/plotting/spiral.py:798`: the `clim` count filter in `SpiralPlot2D.agg` is a line-for-line copy of `AggPlot.agg` (`agg_plot.py:618`). Repro: `diff <(sed -n 618,627p solarwindpy/plotting/agg_plot.py | sed 's/  #.*//') <(sed -n 798,808p solarwindpy/plotting/spiral.py)`
- **F121** [P1] `solarwindpy/plotting/base.py:286`: the "label to path part" rule (`.path`, else the string with spaces as `-`, else the axis letter) is written three times in one function, once each for x, y, z. Repro: `sed -n 286,313p solarwindpy/plotting/base.py`
- **F122** [P1] `solarwindpy/plotting/hist1d.py:118`: `Hist1D.set_path` copies `PlotWithZdata.set_path` (`base.py:631`) minus z and the y scale, so a `Hist1D` with `set_log(y=True)` saves under `.../linX` with no y scale even after `set_path("auto")` refreshes it. Repro: `conda run -n solarwindpy python -c 'import numpy as np,pandas as pd;from solarwindpy.plotting.hist1d import Hist1D;x=pd.Series(np.random.default_rng(0).random(60)+1);h=Hist1D(x,nbins=5);h.set_log(y=True);h.set_path("auto");print(h.log,h.path)'`
- **F123** [P1] `solarwindpy/plotting/base.py:632`: the save path is stored, not derived, so it holds a second copy of the log flags that `set_log` does not refresh; the comment "Bug: path doesn't auto-set log information" is still true: a `Scatter` after `set_log(x=True, y=True)` keeps path `linX-linY`. [AUTHOR] (saved-figure paths change) Repro: `conda run -n solarwindpy python -c 'import numpy as np,pandas as pd;from solarwindpy.plotting.scatter import Scatter;x=pd.Series(np.random.default_rng(0).random(60)+1);s=Scatter(x,x);s.set_log(x=True,y=True);print(s.log,s.path)'`
- **F124** [P3] `solarwindpy/plotting/scatter.py:40`: `Scatter.__init__` assigns `_labels` and `_log` directly and calls `set_path(None)`, where every sibling calls `set_log`, `set_labels` and the inherited `set_path("auto")`; so `Scatter(...).path` is `linX-linY` and `Hist2D(...).path` is `Hist2D/x/y/count/linX-linY`. [AUTHOR] (saved-figure paths change) Repro: `conda run -n solarwindpy python -c 'import numpy as np,pandas as pd;from solarwindpy.plotting.scatter import Scatter;from solarwindpy.plotting.hist2d import Hist2D;x=pd.Series(np.random.default_rng(0).random(60));print(Scatter(x,x).path,Hist2D(x,x,nbins=5).path)'`
- **F125** [P3] `solarwindpy/plotting/hist1d.py:33`: sibling constructors order shared parameters differently: `Hist1D(x, y, logx, axnorm, ...)` against `Hist2D(x, y, z, axnorm, logx, logy, ...)`, and `Scatter` takes no `logx`/`logy` at all, so the same positional call binds `axnorm` in one class and `logx` in the other. [AUTHOR] Repro: `conda run -n solarwindpy python -c 'import inspect;from solarwindpy.plotting import hist1d,hist2d,scatter,spiral;[print(c.__name__,inspect.signature(c.__init__)) for c in (hist1d.Hist1D,hist2d.Hist2D,scatter.Scatter,spiral.SpiralPlot2D)]'`
- **F126** [P3] `solarwindpy/plotting/spiral.py:1161`: `plot_contours` takes the same-named smoothing parameters with different defaults in the two classes that have it: `Hist2D` `gaussian_filter_std=0, nan_aware_filter=False`, `SpiralPlot2D` `gaussian_filter_std=1.5, nan_aware_filter=True`, and only `Hist2D` takes `levels` and `gaussian_filter_kwargs`. Changing a default changes figures. [AUTHOR] Repro: `conda run -n solarwindpy python -c 'import inspect;from solarwindpy.plotting import hist2d,spiral;[print(c.__name__,inspect.signature(c.plot_contours)) for c in (hist2d.Hist2D,spiral.SpiralPlot2D)]'`
- **F127** [P3] `solarwindpy/plotting/hist2d.py:313`: `Hist2D._nan_gaussian_filter` is a one-line pass-through to `tools.nan_gaussian_filter`, which `SpiralPlot2D` calls directly (`spiral.py:1271`); two call forms for one function. Repro: `git grep -n 'nan_gaussian_filter' -- solarwindpy/plotting`

#### labels

**Predicted:** `labels/base.py` holds the only translation tables (species, components,
measurements, units); every label class composes `tex` and `units` into `with_units` through one
shared method; the species table matches the species core defines
(`core/units_constants.py:_m_in_mp`), since the same `S` column level feeds both.

**Found:** The tables live in `labels/base.py` as predicted, and `elemental_abundance.py:9`
derives its species from them (the form to mirror). The species set is not core's, and the
`tex [units]` format is restated in 14 places in two bracket forms.

- **F128** [P1] `solarwindpy/plotting/labels/base.py:20`: `_trans_species` is a second species list beside `core/units_constants.py:45` (`_m_in_mp`); core's `a_bimax` and `pm` are absent, and the species regex then substitutes inside the name, so `TeXlabel(("n","","a_bimax")).tex` is `n_{\alpha_bim\alphax}`. [AUTHOR] (TeX for the new species) Repro: `conda run -n solarwindpy python -c 'from solarwindpy.plotting.labels.base import TeXlabel;from solarwindpy.core import units_constants as uc;from solarwindpy.plotting.labels import base as lb;print(sorted(set(uc._m_in_mp)-set(lb._trans_species)),TeXlabel(("n","","a_bimax")).tex)'`
- **F129** [P1] `solarwindpy/plotting/labels/composition.py:8`: `known_species` is a hand-typed copy of the element loop at `labels/base.py:33` (minus `H`), where `elemental_abundance.py:9` derives the same tuple from `base._trans_species`. Repro: `git grep -n -E 'known_species =|for s in \("C"' -- solarwindpy/plotting/labels`
- **F130** [P1] `solarwindpy/plotting/labels/special.py:390`: the label-with-units format `$tex <sep> [units]$` is written 14 times across `labels/` (13 `result = ...` lines plus `ManualLabel` at `special.py:162`); three (`labels/base.py:386`, `special.py:563,683`) use `\left[ \right]` and eleven plain `[ ]`, so labels from sibling classes set side by side bracket differently. [AUTHOR] (one bracket form changes rendered labels) Repro: `git grep -n -E 'result = .*\[' -- solarwindpy/plotting/labels; sed -n 162p solarwindpy/plotting/labels/special.py`
- **F131** [P1] `solarwindpy/plotting/labels/special.py:238`: the dimensionless count unit is hard-coded as `\#` five times (`special.py:238,290,482,804,1033`) while `labels/base.py:113` owns it as `_inU["dimless"] = \mathrm{\#}`, which `special.py:370,575,841` use. Matplotlib mathtext draws both as the same glyph (checked with `matplotlib.mathtext.MathTextParser("path")`), so this is two spellings of one fact, not a visible defect. Repro: `git grep -n -F -e '\#' -e '_inU["dimless"]' -- solarwindpy/plotting/labels/special.py`
- **F132** [P1] `solarwindpy/plotting/labels/special.py:451`: `CountOther` is a copy of `Probability` (`special.py:378`) that differs only in the prefix (`Count.`/`cnt` against `Prob.`/`prob`), the unit, and a `new_line_for_units` option that `Probability` lacks; `set_new_line_for_units` is itself defined four times (`labels/base.py:496`, `special.py:504,604,711`). Repro: `diff <(sed -n 378,450p solarwindpy/plotting/labels/special.py) <(sed -n 451,540p solarwindpy/plotting/labels/special.py)`
- **F133** [P2] `solarwindpy/plotting/labels/base.py:345`: `_init_logger(self, handlers=None)` says "Create a logger at the INFO level" but sets no level and never reads `handlers`; the copies of this logger setup across subpackages are F101. Repro: `sed -n 344,348p solarwindpy/plotting/labels/base.py; git grep -n 'def _init_logger' -- solarwindpy`

#### plotting public surface (P4)

**Predicted:** Some names in each plotting module's `__all__` are used nowhere outside it, so
the modules expose more than the layer above needs.

**Found:** None of consequence. For each name in the `__all__` of the 8 plotting modules, a
`git grep -l -w` over `solarwindpy` and `tests` (excluding the defining file) finds outside uses
for all 18; the fewest are `spiral.SpiralMesh` (2 files, tests only, and reachable through
`SpiralPlot2D.mesh`), `tools.joint_legend` and `tools.build_ax_array_with_common_colorbar`
(1 test file each, figure helpers meant for users). Positive control: the same scan does report
these low counts, so a name with no outside use would show `files=0`. Script:
`for m in agg_plot base binned hist1d hist2d scatter spiral tools; do for n in $(conda run -n solarwindpy python -c "import solarwindpy.plotting.$m as x;print(*x.__all__)"); do echo "$m.$n $(git grep -l -w $n -- solarwindpy tests | command grep -v plotting/$m.py | wc -l)"; done; done`

### tools

**Predicted:** `solarwindpy/tools/` is the bottom layer (`pyproject.toml` § `[tool.importlinter]`
puts it beside `core`), so it holds generic helpers with no knowledge of the `M, C, S` data model,
each formula defined here once, and upper layers import it rather than re-deriving.

**Found:** `lint-imports` holds (2 kept). No package module imports `tools`
(`git grep -n -E 'from (\.\.|solarwindpy\.)tools' -- solarwindpy` prints nothing; positive control:
`git grep -n -E 'from \.binned' -- solarwindpy` prints the plotting imports, so the pattern form
matches). `swap_protons` knows the `("n", "", "p1")` column convention, so the "generic"
prediction fails, and the log-normal moment formula exists twice.

- **F134** [P1] `solarwindpy/fitfunctions/gaussians.py:308`: `GaussianLn.normal_parameters` (`gaussians.py:297`, formula at `:308`) re-derives the moments `solarwindpy/tools/__init__.py:198` owns (with its Fenton 1960 citation and `base` handling); fitfunctions sits above tools and may import it. `p0-simplify` (#496), which owned `fitfunctions/`, is merged. Repro: `diff <(sed -n 198,201p solarwindpy/tools/__init__.py) <(sed -n 308,311p solarwindpy/fitfunctions/gaussians.py | sed 's/^    //')`
- **F135** [P2] `solarwindpy/tools/__init__.py:127`: `normal_parameters` (and the `GaussianLn` property of the same name) returns the mean and standard deviation of a log-normal variable, not normal-distribution parameters; the name points away from its content. [AUTHOR] Repro: `sed -n 127,131p solarwindpy/tools/__init__.py`
- **F136** [P9] `solarwindpy/tools/__init__.py:103`: the post-swap check divides `n p2` by `n p2`, so it is always 1 and the `<= 1.0` assertion can never fire; the intended check is `n p2 / n p1`. Changing it can raise where it never did. [AUTHOR] Repro: `sed -n 103,106p solarwindpy/tools/__init__.py`
- **F137** [P5] `solarwindpy/tools/__init__.py:109`: the fallback logger is named `main.<module>` and attaches its own `StreamHandler`, unlike every class logger in the package (`<module>.<class>`, no handler; `plotting/base.py:71`). Repro: `sed -n 108,115p solarwindpy/tools/__init__.py; sed -n 71,73p solarwindpy/plotting/base.py`
- **F138** [P2] `solarwindpy/tools/__init__.py:1`: two modules are named `tools` at different layers (`solarwindpy.tools` for plasma data, `solarwindpy.plotting.tools` for figures, the latter also holding the numeric `nan_gaussian_filter`); the docstring calls the subpackage's functions "not yet organized into their own submodules". [AUTHOR] Repro: `sed -n 4,6p solarwindpy/tools/__init__.py; git grep -n '^def ' -- solarwindpy/plotting/tools.py`

### solar_activity

**Predicted:** From `solar_activity/__init__.py` ("indicators and event catalogs") and `base.py`'s `__all__` (`Base`, `ID`, `DataLoader`, `ActivityIndicator`, `IndicatorExtrema`), every data source is an `ID` + `DataLoader` + `ActivityIndicator` triple: `sunspot_number/sidc.py` and `icme/icmecat.py` both build on `base.py`; `plots.py` plots any `ActivityIndicator`.
**Found:** `sidc.py` follows the triple (`SIDC_ID`, `SIDCLoader`, `SIDC`, `SSNExtrema`). `icmecat.py` imports nothing from `base.py`: `ICMECAT` is a free-standing class that copies the logger and runs its own cache policy. `plots.py` holds only the generic line plot; the SSN colour-bar plot lives in `sidc.py`. The prediction holds for one of two sources. Descended into every module.

- **F139** [P3] `solarwindpy/solar_activity/icme/icmecat.py:71`: `ICMECAT` subclasses none of `base.py`'s classes, so the subpackage's base layer predicts one of its two data sources; a reader of `base.py` cannot find the catalog's loader, cache, or interval logic there. Repro: `command grep -nE '^from|^import|^class' solarwindpy/solar_activity/icme/icmecat.py`
- **F140** [P1] `solarwindpy/solar_activity/icme/icmecat.py:220`: [AUTHOR] two cache policies in one subpackage: `DataLoader` caches under `~/solarwindpy/data/<source>/<key>/YYYYMMDD.csv` and refreshes daily by file name (`base.py:235`), `ICMECAT` caches opt-in under `cache_dir/icmecat.csv` and refreshes after 30 days by mtime (`icmecat.py:24`). Unifying them changes user-visible cache behavior. Repro: `command grep -nE '_CACHE_MAX_AGE_DAYS|st_mtime|def data_path|strftime' solarwindpy/solar_activity/base.py solarwindpy/solar_activity/icme/icmecat.py`

#### Module: solar_activity/base.py

**Predicted:** From its `__all__`, five abstract classes whose abstract signatures are the contracts `sidc.py` implements; subclass signatures match the abstract ones.
**Found:** Three abstract signatures do not match their implementation or their caller; the module uses the deprecated `abstractproperty`/`abstractstaticmethod`; one documented bug is guarded by a bare `assert`.

- **F141** [P3] `solarwindpy/solar_activity/base.py:144`: abstract `download_data(self)` takes no arguments, but `maybe_update_stale_data` calls it with two (`base.py:247`) and `SIDCLoader.download_data(self, new_data_path, old_data_path)` implements two; the base does not predict its subclass. Repro: `command grep -n 'def download_data\|self.download_data(' solarwindpy/solar_activity/base.py solarwindpy/solar_activity/sunspot_number/sidc.py`
- **F142** [P3] `solarwindpy/solar_activity/base.py:138`: `convert_nans` is declared `abstractstaticmethod` but `SIDCLoader.convert_nans(self, data)` (`sidc.py:214`) is an instance method. Repro: `command grep -n -A1 'abstractstaticmethod$' solarwindpy/solar_activity/base.py; command grep -n 'def convert_nans' solarwindpy/solar_activity/sunspot_number/sidc.py`
- **F143** [P3] `solarwindpy/solar_activity/sunspot_number/sidc.py:350`: [AUTHOR] `SIDC.interpolate_data(target_index, key="ssn")` reorders and replaces the parameters of `ActivityIndicator.interpolate_data(source_data, target_index)` (`base.py:299`); a caller written against the base passes data where the subclass expects an index. Public signature change. Repro: `command grep -n 'def interpolate_data' solarwindpy/solar_activity/base.py solarwindpy/solar_activity/sunspot_number/sidc.py`
- **F144** [P5] `solarwindpy/solar_activity/base.py:19`: five uses of `abc.abstractproperty`/`abstractstaticmethod`, deprecated since Python 3.3; the form to mirror is `@property` over `@abstractmethod`. `solarwindpy/plotting/agg_plot.py:716` has the same deprecated form (outside this scope). Repro: `git grep -nE '@abstract(property|staticmethod)' solarwindpy`
- **F145** [P9] `solarwindpy/solar_activity/base.py:222`: a `# BUG:` comment ("fails if there are more than two dated data directories") over `assert dates.size == 1`, which in fact fails at two; the defect is guarded by an assert that `python -O` strips. Repro: `sed -n '221,222p' solarwindpy/solar_activity/base.py`
- **F146** [P1] `solarwindpy/solar_activity/base.py:578`: `dt = pd.to_timedelta(dt)` is executed twice (lines 575 and 578). Repro: `command grep -n 'dt = pd.to_timedelta(dt)' solarwindpy/solar_activity/base.py`
- **F147** [P1] `solarwindpy/solar_activity/base.py:113`: `DataLoader(key, url)` re-stores the key and URL that its `ID` already holds (`sidc.py:342` passes `self.id.key, self.id.url`), with its own `key`/`url` properties duplicating `ID.key`/`ID.url` (`base.py:73`, `base.py:78`). Repro: `command grep -n 'def key\|def url\|SIDCLoader(' solarwindpy/solar_activity/base.py solarwindpy/solar_activity/sunspot_number/sidc.py`
- **F148** [P2] `solarwindpy/solar_activity/base.py:96`: [AUTHOR] an unknown key raises `NotImplementedError`, while the same module raises `ValueError` for an unknown interval kind (`base.py:537`); the exception class mis-states bad input as missing code. Pinned by `tests/solar_activity/test_base.py:193`, so the change is an API change. Repro: `command grep -n 'raise NotImplementedError\|raise ValueError' solarwindpy/solar_activity/base.py`
- **F149** [P9] `solarwindpy/solar_activity/base.py:552`: `raise ValueError` with no message when the cycle intervals overlap or are unsorted; every other raise in the module names its cause. Repro: `command grep -n 'raise ValueError$' solarwindpy/solar_activity/base.py`
- **F150** [P5] `solarwindpy/solar_activity/sunspot_number/sidc.py:466`: `run_normalization.__doc__ = ActivityIndicator.run_normalization.__doc__` hand-copies a docstring; the package already has an inheritance form, `solarwindpy/fitfunctions/core.py:FitFunctionMeta` (docstring_inheritance). The copied docstring also documents a `norm_by` parameter the abstract signature lacks (`base.py:370`). Repro: `command grep -n '__doc__ =\|def run_normalization' solarwindpy/solar_activity/base.py solarwindpy/solar_activity/sunspot_number/sidc.py`

#### Module: solar_activity/sunspot_number/sidc.py

**Predicted:** From `__all__` (`SIDC_ID`, `SIDCLoader`, `SIDC`, `SSNExtrema`) and the `SIDC_ID` key table, one definition of the seven series keys, one dtype table per distinct file layout, and data logic only (plots in `plots.py`).
**Found:** The key set is spelled in five places; two pairs of dtype tables are identical; the extrema table is loaded twice per `SIDC`; a plotting method and its duplicated branches live here.

- **F151** [P1] `solarwindpy/solar_activity/sunspot_number/sidc.py:36`: `_m13_dtypes_columns` equals `_m_dtypes_columns` and `_hm13_dtypes_columns` (line 48) equals `_hm_dtypes_columns` (line 81); seven tables hold five facts. Repro: `conda run -n solarwindpy python -I -c "from solarwindpy.solar_activity.sunspot_number import sidc as s; print(s._m_dtypes_columns.dtypes==s._m13_dtypes_columns.dtypes, s._hm_dtypes_columns==s._hm13_dtypes_columns)"`
- **F152** [P1] `solarwindpy/solar_activity/sunspot_number/sidc.py:237`: the seven series keys are spelled in the docstring table (169), `_trans_url` (194), the `_Dtypes_Columns` fields (150), the date-building branches (237, 242, 246), and `key.startswith("h")` (257); the `else` at 252 is unreachable because line 229 already rejected unknown keys. Repro: `command grep -nE '"(m13|hm13)"|startswith\("h"\)|d,m,m13' solarwindpy/solar_activity/sunspot_number/sidc.py`
- **F153** [P2] `solarwindpy/solar_activity/sunspot_number/sidc.py:150`: `_Dtypes_Columns` is first a namedtuple class and then rebound to its own instance, and `defaults=(None,)` gives a default only to the last field `hm13`, which is always passed. Repro: `sed -n '150,160p' solarwindpy/solar_activity/sunspot_number/sidc.py`
- **F154** [P2] `solarwindpy/solar_activity/sunspot_number/sidc.py:267`: [AUTHOR] hemispheric series get columns `totalstd_error`, `northstd_error`, `southstd_error`, without the underscore of their siblings `total_std`, `n_total`, and of the scalar `std_error` (line 275); `tests/solar_activity/sunspot_number/test_sidc_loader.py:402` matches by `startswith`/`endswith` and so pins no name. Renaming is a data-column change. Repro: `conda run -n solarwindpy python -I -c "import pandas as pd; c=pd.Index(['total_std','north_std']).to_series().str.split('_').apply(lambda x:x[0]); print(list(c+'std_error'))"`
- **F155** [P1] `solarwindpy/solar_activity/sunspot_number/sidc.py:298`: `SIDCLoader.load_data` builds an `SSNExtrema()` (reading `ssn_extrema.csv`), and `SIDC.set_extrema` (line 348) builds a second one for the same object. Repro: `command grep -n 'SSNExtrema()' solarwindpy/solar_activity/sunspot_number/sidc.py`
- **F156** [P1] `solarwindpy/solar_activity/sunspot_number/sidc.py:404`: `calculate_edge` repeats the per-cycle loop of `calculate_extrema_kind` (lines 381-397): same `groupby("cycle")`, same `max_date`, `before_max`, `after_max`, same `kind.update`. Extract one per-cycle helper. Repro: `command grep -n 'groupby("cycle")\|before_max =\|after_max =' solarwindpy/solar_activity/sunspot_number/sidc.py`
- **F157** [P2] `solarwindpy/solar_activity/sunspot_number/sidc.py:374`: [AUTHOR] the docstring defines Min/Max by "ssn < cycle mean", but the code uses half the cycle maximum (`mid = 0.5 * g.max()`, line 385), and `tests/solar_activity/sunspot_number/test_sidc.py:385` asserts the half-max rule. Which rule is intended is physics; the author decides. Repro: `sed -n '374,375p;385p' solarwindpy/solar_activity/sunspot_number/sidc.py`
- **F158** [P3] `solarwindpy/solar_activity/sunspot_number/sidc.py:490`: `cut_spec_by_ssn_band` takes its band range from `self.data` (line 481) but cuts `self.interpolated` (line 490, `# TODO: generalize this hack`), so the bands need not cover the values cut. Repro: `sed -n '481,482p;490p' solarwindpy/solar_activity/sunspot_number/sidc.py`
- **F159** [P3] `solarwindpy/solar_activity/sunspot_number/sidc.py:514`: `plot_on_colorbar` is a plotting method in the data module while the subpackage has `plots.py`; its own TODO (line 523) concedes the misplacement. Repro: `command grep -n 'def plot_on_colorbar\|TODO: Refactor' solarwindpy/solar_activity/sunspot_number/sidc.py`
- **F160** [P1] `solarwindpy/solar_activity/sunspot_number/sidc.py:555`: the horizontal branch (555-568) repeats the vertical branch (541-552) with the axes swapped, including the dash pattern `(0, (7, 3, 2, 3, 2, 3, 2, 3))` and the duplicated comment. Repro: `command grep -n '(7, 3, 2, 3, 2, 3, 2, 3)\|We force the maximum' solarwindpy/solar_activity/sunspot_number/sidc.py`
- **F161** [P1] `solarwindpy/solar_activity/plots.py:148`: [AUTHOR] two SSN axis conventions: `SSNPlot` fixes the range at 0 to 200, while `SIDC.plot_on_colorbar` rounds the peak up to the next 100 (`sidc.py:537`). Suspicion only: a fixed 200 would clip cycle 19's smoothed maximum, which I believe SILSO V2 tabulates above 200 (not checked against the table). Pinned by `tests/solar_activity/test_plots.py:206`. Repro: `command grep -n 'set_ylim(0, 200)\|np.ceil(ssn.max()' solarwindpy/solar_activity/plots.py solarwindpy/solar_activity/sunspot_number/sidc.py`

#### Module: solar_activity/icme/icmecat.py and icme/__init__.py

**Predicted:** From the module's `__all__` and the `ICMECAT` class docstring, one loader, one spacecraft-name rule, the `strict`/`estimated` interval pair, and code comments that name the constants they refer to correctly.
**Found:** The spacecraft lookup is written twice and the copies differ; the error message and the drift suite carry five line pointers into this file, all stale; the package `__init__` repeats the class doctest.

- **F162** [P1] `solarwindpy/solar_activity/icme/icmecat.py:337`: `filter` rebuilds the case-insensitive `name_map` of `_filter_by_spacecraft` (lines 304-310), and the copies have already drifted: only `_filter_by_spacecraft` warns on an unknown name. `filter` also hand-assembles an instance via `object.__new__` (line 345). Repro: `command grep -n 'name_map = \|logger.warning(' solarwindpy/solar_activity/icme/icmecat.py`
- **F163** [P1] `solarwindpy/solar_activity/icme/icmecat.py:282`: the download error tells the user to "Edit ... icmecat.py:11 (ICMECAT_URL)", but `ICMECAT_URL` is at line 19; a line number copied into a message is a second home for the constant's location. `tests/drift/test_drift_icmecat.py` carries four more stale pointers: `:11` for `ICMECAT_URL` (lines 5 and 37; actual 19), `:32` for `_DATETIME_COLUMNS` (line 68; actual 51), `:14` for `SPACECRAFT_NAMES` (line 91; actual 35). Mirror the test-quality `p0-simplify` acceptance check that removed the stale `plasma.py:102` pointer: name the symbol, not the line. Repro: `git grep -nE 'icmecat\.py:[0-9]+'; command grep -nE '^(ICMECAT_URL|SPACECRAFT_NAMES|_DATETIME_COLUMNS) =' solarwindpy/solar_activity/icme/icmecat.py`
- **F164** [P1] `solarwindpy/solar_activity/icme/__init__.py:19`: the package docstring's offline doctest (lines 19-46) repeats the `ICMECAT` class doctest (`icmecat.py:103-143`) with one row fewer. Repro: `command grep -c 'icmecat.ICMECAT_URL = str(local)' solarwindpy/solar_activity/icme/__init__.py solarwindpy/solar_activity/icme/icmecat.py`
- **F165** [P4] `solarwindpy/solar_activity/icme/icmecat.py:3`: `__all__` omits `RULES_OF_THE_ROAD`, which the package docstring interpolates (`icme/__init__.py:15`) and the class docstring tells users to read (line 74). Repro: `sed -n '3,8p;54p' solarwindpy/solar_activity/icme/icmecat.py`
- **F166** [P2] `solarwindpy/solar_activity/icme/icmecat.py:471`: the comment "Vectorized containment check" sits over a per-observation Python loop (line 473). Repro: `sed -n '471,474p' solarwindpy/solar_activity/icme/icmecat.py`
- **F167** [P2] `solarwindpy/solar_activity/icme/icmecat.py:155`: the private `_intervals` holds what the public API calls `estimated_intervals` (line 199), beside a public `strict_intervals`; `summary` (line 499) and `contains` (line 454) read `_intervals`, so a reader must trace which pair member each uses. Private rename only. Repro: `command grep -n 'self._intervals' solarwindpy/solar_activity/icme/icmecat.py`

#### Data files: solar_activity

**Predicted:** From `SSNExtrema.load_or_set_data` (one `read_csv` of `ssn_extrema.csv`), one extrema table, declared as package data in the one place the package declares data.
**Found:** A second, tracked extrema table that nothing reads, and package data declared in two files.

- **F168** [P1] `solarwindpy/solar_activity/sunspot_number/ssn_extrema.csv.silso:72`: [AUTHOR] a tracked near-copy of `ssn_extrema.csv` that no code reads; it disagrees on cycle 25's maximum (`2030-12-01` placeholder against `2024-10-01`). Its commit ("Added SILSO ssn extrema to repo") suggests a provenance copy of the SILSO table, so this proposes keeping or retiring it, never deleting unasked. Repro: `diff solarwindpy/solar_activity/sunspot_number/ssn_extrema.csv solarwindpy/solar_activity/sunspot_number/ssn_extrema.csv.silso; git grep -n 'ssn_extrema.csv.silso' -- solarwindpy`
- **F169** [P1] `MANIFEST.in:5`: `ssn_extrema.csv` ships through `MANIFEST.in` plus `include_package_data`, while `core/data/*.csv` ships through `pyproject.toml` `[tool.setuptools.package-data]` (line 154); package data has two homes. Repro: `command grep -n 'csv' MANIFEST.in pyproject.toml`

### Test tree

#### tests/core and tests/test_examples.py

**Predicted:** the code tree has one module per class family, so I expect one `tests/core/test_<module>.py` per module, a shared fixture module named as a helper (as `tests/plotting/_cases.py` is), tests importing only public names, and `tests/test_examples.py` testing the loader alone.
**Found:** The mirror holds for `abundances`, `alfvenic_turbulence`, `ions`, `plasma` (plus `test_plasma_io.py`), `spacecraft`, `units_constants`. It breaks for `base` and for `vector`/`tensor`, the fixture module is named as a test of `base.py`, and six files still set an option pandas 3 ignores.

- **F170** [P3] `tests/core/test_base.py:17`: `test_base.py` is the shared fixture module (`SyntheticData`, `SWEData`, the species mixins) that six test files import as `from . import test_base as base`, while the tests of `core/base.py` are spread over `test_base_head_tail.py`, `test_base_mi_tuples.py` (11 lines), `test_core_verify_datetimeindex.py` and the bottom of `test_base.py`; mirror `tests/plotting/_cases.py` for the fixture module. Repro: `git grep -n "import test_base" -- tests; ls tests/core`
- **F171** [P3] `tests/core/test_quantities.py:87`: `Vector`, `BField` and `Tensor` are tested in one `test_quantities.py`, so the test tree has no file named for `vector.py` or `tensor.py`, and nothing tests `Vector.__call__`/`Tensor.__call__` (F78); the solar_activity slice found the same gap from the module layer. Positive control: the second search finds the `mag` tests. Repro: `git grep -n -E "\.b\(\"|\(\"x\"\)|\(\"par\"\)" -- tests/core; git grep -c "\.mag" -- tests/core/test_quantities.py`
- **F172** [P1] `tests/core/test_base.py:14`: six `tests/core` files set `pd.set_option("mode.chained_assignment", "raise")`, which pandas 3 ignores and warns about; the author removed the identical package-side settings ("chore: remove the inert pandas chained_assignment settings"), and these are all six warnings of the `tests/core` run, which step 4 of the test-quality § Scope reads. Repro: `git grep -n "chained_assignment" -- tests; git log --oneline --grep "inert pandas chained_assignment"`
- **F173** [P4] `tests/core/test_base.py:12`: the shared fixtures import the private `solarwindpy.examples._read_example` to get the raw example frames, so a private loader is part of the test contract; a public raw-frame loader or a test-side reader is the author's choice. [AUTHOR] Repro: `git grep -n "_read_example" -- tests`
- **F174** [P3] `tests/test_examples.py:117`: `test_plasma_logs_each_optional_input_not_passed` and `test_plasma_no_longer_accepts_log_plasma_stats` (`:106`) test `Plasma`, not the example loader, so `Plasma` behaviour is guarded outside `tests/core/test_plasma.py`. Repro: `command grep -n "^def test" tests/test_examples.py`

#### tests/fitfunctions

**Predicted:** One test file per module (`test_<module>.py` for each of the eleven modules), cross-class contract files for the shared `FitFunction` contract, every fitfunctions test under `tests/fitfunctions/`, and the same package marker (`__init__.py`) as the sibling test directories.
**Found:** All eleven modules have a mirror file. Around them: `trend_fits.py` has three test files, fitfunctions tests also live in two top-level files, one of which holds tests its header does not name, and `tests/fitfunctions/` is the only subpackage test directory without `__init__.py`.

- **F175** [P2] `tests/test_source_fitfunctions_defects.py:1`: the header (`Spent-When: ... drops GaussianPlusHeavySide`, and a docstring about `GaussianPlusHeavySide` only) mis-predicts the file, which also holds `Line`, `LineXintercept` and `TrendFit` tests (lines 193, 204, 216, 236); dropping `GaussianPlusHeavySide` would spend a file still guarding three other modules. Repro: `command grep -n "^def test" tests/test_source_fitfunctions_defects.py`
- **F176** [P3] `tests/test_source_fitfunctions_defects.py:45`: the code tree predicts these tests in `tests/fitfunctions/test_composite.py`, `test_lines.py` and `test_trend_fits.py`; the top-level `test_source_<pkg>_defects.py` form repeats for plotting (`tests/test_source_plotting_defects.py`, added in 6bdcbdba), so whether a fixed-defect file mirrors the code tree or the fix history is a question for the author, not a defect. The solar_activity slice found the plotting file independently: it tests only `solarwindpy/plotting/` while files of its kind (`test_hist1d_defects.py`, `test_hist2d_defects.py`, `test_data_path_defects.py`) live in `tests/plotting/`. Repro: `ls tests/test_source_*_defects.py tests/fitfunctions/test_composite.py tests/fitfunctions/test_lines.py`
- **F177** [P3] `tests/fitfunctions/test_trend_fit_properties.py:1`: `trend_fits.py` is tested by three files (`test_trend_fits.py`, `test_trend_fits_advanced.py`, and this 31-line, 2-test file with no module docstring). Repro: `ls tests/fitfunctions/test_trend_fit*.py; head -3 tests/fitfunctions/test_trend_fit_properties.py`
- **F178** [P3] `tests/fitfunctions/conftest.py:1`: `tests/fitfunctions/` has no `__init__.py`, so its modules import as top-level names (`test_plots`, `test_core`) beside packaged siblings such as `tests.solar_activity.test_plots` (found by two slices), while `tests/core`, `tests/instabilities`, `tests/plotting`, `tests/solar_activity`, `tests/tools` and `tests/drift` each have one. Repro: `ls tests/*/__init__.py`
- **F179** [P1] `tests/test_fitfunctions_public_names.py:59`: `test_no_fit_function_is_reexported_by_the_package` is a strict subset of `tests/test_public_imports.py:201` with the `solarwindpy.fitfunctions` parameter, which rejects any solarwindpy object the package file does not define, fit functions included. Repro: `conda run -n solarwindpy pytest --collect-only -q tests/test_public_imports.py 2>/dev/null | command grep "binds.*fitfunctions\]"`

#### tests/instabilities

**Predicted:** `tests/instabilities/test_beta_ani.py` and `tests/instabilities/test_verscharen2016.py`, one per module, with the Table 1 coefficients restated in the test as an independent oracle.
**Found:** As predicted. The mirror is one to one, and the coefficient restatement is an intended oracle, not a P1 copy.

Found none, with control: `ls solarwindpy/instabilities/*.py tests/instabilities/test_*.py` pairs `beta_ani` and `verscharen2016` with one test file each; the same listing for fitfunctions (F177) shows how a broken mirror appears.

#### tests/plotting

**Predicted:** One `test_<module>.py` per module under `tests/plotting/` and one per label module
under `tests/plotting/labels/`, each named for its module.

**Found:** Label tests mirror their modules one-to-one, apart from the names `test_labels_base.py`
and `test_init.py`. The plot tests are organized by the review episode that produced them, and the
file named for `histograms` mirrors a module that no longer exists. Positive control for the
mirroring check: it passes for tools (`ls tests/tools` lists `test_tools.py` for
`solarwindpy/tools/__init__.py`) and for `binned`, `scatter`, `spiral`, `agg_plot`.

- **F180** [P3] `tests/plotting/test_histograms.py:1`: named for `solarwindpy/plotting/histograms.py`, deleted in c7c5d160, it now tests `Hist1D` and `Hist2D` beside `test_hist1d.py` and four `Hist2D` files. Repro: `git log --oneline --diff-filter=D -- solarwindpy/plotting/histograms.py; ls tests/plotting/ | command grep -E 'hist|agg_full'`
- **F181** [P2] `tests/plotting/test_review_findings.py:3`: two files are named for the review that produced them, not the code they test, and open with the same sentence ("Contract tests for four rulings on the plot(ting) data path", `test_data_path_defects.py:3`); a third sits outside the tree at `tests/test_source_plotting_defects.py`. Clip behaviour alone is tested in 12 files. Repro: `sed -n 3p tests/plotting/test_review_findings.py tests/plotting/test_data_path_defects.py; git grep -c -E 'def test_[a-z0-9_]*clip' -- tests/plotting tests/test_source_plotting_defects.py`
- **F182** [P2] `tests/plotting/test_agg_full_grid.py:1`: named for `agg`, it tests `Hist2D`'s grid and contour selection ("Hist2D's full ``agg`` grid"); `test_hist2d_defects.py` likewise tests `Hist2D` projections under a provenance name. Repro: `sed -n 1p tests/plotting/test_agg_full_grid.py tests/plotting/test_hist2d_defects.py`

#### tests/solar_activity

**Predicted:** From the code tree (`base.py`, `plots.py`, `icme/icmecat.py`, `sunspot_number/sidc.py`, three `__init__.py`), test files `test_base.py`, `test_plots.py`, `test_init.py`, `icme/test_icmecat.py`, `icme/test_init.py`, `sunspot_number/test_sidc.py`, `sunspot_number/test_init.py`.
**Found:** The directory mirror holds. Within it, `sidc.py` is split by class into four files (`test_sidc_id`, `test_sidc_loader`, `test_ssn_extrema`, `test_sidc`) while `icmecat.py` is split by test kind into three (`test_icmecat`, `_smoke`, `_integration`); `icme/__init__.py` has no `test_init.py` (its doctest stands in); the two `test_init.py` files use different forms for the same contract. The icme test files belong to a completed test-quality unit (batch line 100), not an in-flight one.

- **F183** [P3] `tests/solar_activity/icme/test_icmecat_smoke.py:1`: one subpackage uses two split rules: `sidc.py` tests split by class, `icmecat.py` tests split by kind, the "smoke" file holding two constant checks that a `TestModuleConstants` class in `test_icmecat.py` would hold under the class rule. Repro: `ls tests/solar_activity/icme tests/solar_activity/sunspot_number`
- **F184** [P5] `tests/solar_activity/sunspot_number/test_init.py:34`: nine tests and 155 lines check a five-line `__init__.py`, while the parent's `tests/solar_activity/test_init.py:test_every_exported_name_resolves` checks the same contract (every `__all__` name resolves) in 14 lines; mirror the parent form. Repro: `wc -l tests/solar_activity/test_init.py tests/solar_activity/sunspot_number/test_init.py solarwindpy/solar_activity/sunspot_number/__init__.py`
- **F185** [P3] `tests/solar_activity/icme/test_icmecat_integration.py:14`: [AUTHOR] live-network checks of the same catalog have two homes and two markers: `integration` tests in the code mirror, `drift` tests in `tests/drift/test_drift_icmecat.py`; both are skipped by the same gate (`tests/conftest.py:50`). Which home is canonical is the author's call. Repro: `git grep -nE 'pytest.mark.(integration|drift)' -- tests/solar_activity tests/drift`
- **F186** [P9] `solarwindpy/solar_activity/sunspot_number/sidc.py:189`: the SIDC download base (`http://www.sidc.be/silso/INFO/`) has no drift check, while the ICMECAT URL has one; positive control: `tests/drift/test_drift_icmecat.py` exists and references `ICMECAT_URL`. Repro: `git grep -il 'sidc' -- tests/drift | wc -l`

#### The test tree against the subpackage layer

**Predicted:** From `solarwindpy/__init__.py` `__all__` (`core`, `examples`, `fitfunctions`, `instabilities`, `plotting`, `solar_activity`, `tools`), one `tests/<subpackage>/` package per subpackage, each with `__init__.py`; root holds only cross-package checks and shared helpers.
**Found:** Six of seven subpackages have a test directory; `examples` has none (its test sits at root). `tests/fitfunctions/` alone lacks `__init__.py`. One extra directory, `tests/drift/`, has no code counterpart by design, and its placement is predictable from its documented rule (`tests/drift/__init__.py`).

- **F187** [P3] `tests/test_examples.py:1`: `solarwindpy/examples/` has no `tests/examples/`; its test sits at root, while the template for a one-module subpackage is `tests/tools/test_tools.py` for `solarwindpy/tools/__init__.py`. Repro: `ls -d tests/examples tests/tools 2>&1`

#### The test tree against the module layer

**Predicted:** One `test_<module>.py` per code module, `test_init.py` per `__init__.py`; extra files named for the code behavior they guard.
**Found:** Three code modules have no same-named test file, and 20 test files are named for no code module. Positive control for the check: `solarwindpy/core/ions.py` maps to `tests/core/test_ions.py` and the check passes it. Most extras are readable (`test_every_fit_function`, `test_p0_contract`); the findings are the ones whose names point elsewhere or at provenance.

- **F188** [P2] `tests/plotting/labels/test_labels_base.py:4`: tests `plotting/labels/base.py` under a name that breaks the `test_base.py` form its siblings use (`tests/core/test_base.py`, `tests/plotting/test_base.py`, `tests/solar_activity/test_base.py`); packaged directories make a `test_base.py` here collision-free. Repro: `git ls-files 'tests/*base.py'`
- **F189** [P2] `tests/core/test_core_verify_datetimeindex.py:1`: the `test_core_` prefix repeats its directory; its siblings testing `core/base.py` are `test_base_head_tail.py` and `test_base_mi_tuples.py`, so the form would be `test_base_verify_datetimeindex.py`. Repro: `ls tests/core | command grep -E 'base|core_'`

#### Root-level tests and helpers

**Predicted:** Root holds what spans packages or is not package code: public-import and alias scans, version declarations, hook tests, the tolerance rule and helper, the shared `conftest.py`.
**Found:** Those are present and their placement is predictable. Five root files test exactly one subpackage that has its own test directory; one root "contract" file tests no package code; the root `conftest.py` docstring describes a migration that ended. Helper naming is consistent within its contrast set (found none): `_cases.py` and `_drift.py` are imported only within their own directory and `tolerances.py` is imported from six directories, so the underscore marks a directory-local helper. Positive control: `git grep -l 'tests.tolerances' -- tests | awk -F/ '{print $2}' | sort -u` lists six directories plus two root files, and `git grep -l '_cases' -- tests` lists only `tests/plotting/` files.

- **F190** [P3] `tests/test_available.py:3`: two root files test only `fitfunctions` (`test_available.py`, `test_fitfunctions_public_names.py`; the third, `test_source_fitfunctions_defects.py`, is F176) while `tests/fitfunctions/` exists; a reader of the code tree cannot predict them. `p0-simplify` (#496), which owned `tests/fitfunctions/`, is merged. Repro: `command grep -l 'solarwindpy.fitfunctions' tests/test_*.py`
- **F191** [P3] `tests/test_contracts_class.py:15`: tests only `solarwindpy.core` (its docstring says so) and sits at root beside `tests/core/`. Repro: `command grep -n '^from solarwindpy' tests/test_contracts_class.py`
- **F192** [P2] `tests/test_contracts_dataframe.py:1`: [AUTHOR] named a package contract test but references `solarwindpy` zero times: it builds its own DataFrames and checks pandas behavior, so it guards no package code. Keep it as documentation, point it at `swp.examples.load_plasma()`, or retire it. Repro: `command grep -c solarwindpy tests/test_contracts_dataframe.py`
- **F193** [P2] `tests/conftest.py:3`: the docstring says the file "enables external package imports for migrated tests from solarwindpy/tests/", and lines 12-14 comment on configuration that does not exist; the file holds the drift gate and `debug_print`. Repro: `sed -n '1,14p' tests/conftest.py`

#### Untracked author items and scan scope

**Predicted:** Untracked files in the working tree are invisible to the suite, as they are to CI.
**Found:** `solarwindpy/tests/` (`test_base_master.py`, `test_base_old.py`, `test_plasma_old.py`, no `__init__.py`) and `solarwindpy/plans/` (`make_branch_from_plan.py`, `check_sweep.sh`, `find_recent_automation_commits.zsh`, no `__init__.py`) are untracked; I listed them and read only the alias scan's output about them. `solarwindpy/fitfunctions/lines_BACKUP_41608.py`, which the dispatch's Motivation (line 98) lists, no longer exists. One filesystem scan reads the untracked files and fails on them.

Verdict on the scan scope: it is a coherence problem. "The package" already has one definition in
the suite, `pkgutil.walk_packages` at `tests/test_public_imports.py:40`, which yields 50 modules
and none under `tests/` or `plans/` (both lack `__init__.py`); `git ls-files 'solarwindpy/*.py'`
gives 51, the 50 plus the top-level `__init__.py`, so the two definitions agree on tracked code.
`tests/test_import_aliases.py:47` uses a third definition, `rglob("*.py")`, under which the same
commit is red on the author's machine and green in a clean checkout. Mirror the `walk_packages`
form (or `git ls-files`) so the verdict depends on the commit, not the working tree. The prior
review also noted that ruff's `ICN` rules cover this test's convention
(`docs/dispatches/findings-test-quality-review-2026-10-02.md:147`); replacing the test with `ICN`
would retire the scan altogether. Assembler's note: that suggestion does not hold. PR #480 probed ruff `ICN` and found it cannot ban every alias outside a whitelist (`gh pr view 480 --json body`), so the test is custom code with no ruff replacement. Positive control: `conda run -n solarwindpy pytest -q
tests/test_import_aliases.py` fails naming `solarwindpy/tests/test_base_master.py:184` and
`solarwindpy/tests/test_plasma_old.py:9,17`.

- **F194** [P9] `tests/test_import_aliases.py:47`: `PACKAGE.rglob("*.py")` scans untracked files, so the test's verdict depends on working-tree state that neither git nor the wheel contains; it fails today on the author's untracked `solarwindpy/tests/`. The plan recommends deleting the test (plan stage S2); scoping it to tracked files by mirroring `tests/test_public_imports.py:40` is the fallback if the author keeps it. Repro: `conda run -n solarwindpy pytest -q tests/test_import_aliases.py 2>&1 | command grep -E '^E .*solarwindpy/tests'`
- **F195** [P9] `tests/plotting/test_no_data_files.py:115`: the same `rglob` scope as F194, over `solarwindpy/plotting/`, and `tests/test_tolerance_rule.py:54` (again at line 110) over `tests/`; both pass today only because nothing untracked sits under their roots. Repro: `git grep -n 'rglob' -- tests`

### Environment spec and packaging

**Predicted:** CONTRIBUTING.md states "`pyproject.toml` is the only dependency declaration", so I expect `solarwindpy.yml` to be a thin conda shell that names the conda-only builds of what `pyproject.toml` declares, pins Python to `requires-python`, and ends in the same install command CI runs (`pip install -e ".[dev]"`); and every runtime dependency in `[project.dependencies]` to be imported by the package.
**Found:** `solarwindpy.yml` is a second hand-maintained list of 91 names, many transitive (`six`, `urllib3`, `idna`), with no Python, missing seven `[dev]` tools, and a header that makes three false claims. `pyproject.toml` declares runtime dependencies nothing imports and leaves out the one HDF I/O needs. The items the caller verified before this pass (no import-linter, phantom `pip:` subsection, `pip install -e .`, no Python pin, the astropy floor) are located below; I re-verified each.

- **F196** [P1] `solarwindpy.yml:3`: the file is a second dependency declaration (91 hand-listed packages, including transitive ones such as `six` and `urllib3`) while `CONTRIBUTING.md:121` says "`pyproject.toml` is the only dependency declaration"; no script generates it. Repro: `sed -n 121p CONTRIBUTING.md; command grep -c '^- ' solarwindpy.yml; command grep -l "solarwindpy.yml" scripts/*.py`
- **F197** [P9] `solarwindpy.yml:11`: the header promises a `pip:` subsection holding pip-only packages (`ast-grep-py`); none exists. Repro: `command grep -n -E "pip:|ast-grep" solarwindpy.yml`
- **F198** [P9] `solarwindpy.yml:8`: the header says GitHub Actions injects the Python version into this file for matrix testing; no workflow reads the file. Positive control: the second command finds the workflows' own `python-version` keys. Repro: `git grep -n "solarwindpy.yml" -- .github; git grep -c "python-version" -- .github`
- **F199** [P1] `solarwindpy.yml:22`: no `python` entry, while `pyproject.toml:57` requires `>=3.12,<4` and CI runs 3.12, so `conda env create` takes whatever Python conda-forge resolves. Positive control: the second count finds `pytest`. Repro: `command grep -c -E "^- python( |=|$)" solarwindpy.yml; command grep -c "^- pytest$" solarwindpy.yml; sed -n 57p pyproject.toml`
- **F200** [P1] `solarwindpy.yml:17`: the conda route ends in `pip install -e .` while CI runs `pip install -e ".[dev]"` (`.github/workflows/ci-master.yml:36`); the same instruction is repeated at `README.rst:96`, `CONTRIBUTING.md:20`, `docs/source/installation.rst:68`, `.claude/docs/DEVELOPMENT.md:40`, so a conda user lacks the tools CLAUDE.md § Commands tells them to run. Pass 1 found the `.claude/docs/DEVELOPMENT.md` copy independently and inferred that this is how the stale env came to lack `lint-imports`. Repro: `git grep -n -E "pip install -e \.( |$)" -- solarwindpy.yml README.rst CONTRIBUTING.md docs/source/installation.rst .claude/docs/DEVELOPMENT.md; sed -n 36p .github/workflows/ci-master.yml`
- **F201** [P1] `solarwindpy.yml:22`: seven `[dev]` tools are absent from the yml (`import-linter`, `griffe`, `mutmut`, `sybil`, `pytest-randomly`, `vulture`, `ruff`), so `lint-imports` from CLAUDE.md § Commands is missing in a yml-built env. Positive control: `pytest` is found. Repro: `for p in import-linter griffe mutmut sybil pytest-randomly vulture ruff pytest; do command grep -q -- "^- $p$" solarwindpy.yml || echo "missing $p"; done`
- **F202** [P8] `pyproject.toml:72`: `astropy>=5.0` admits astropy 6.1.x, which calls `numpy.in1d`, removed in the numpy 2.5 that `numpy>=1.26,<3.0` admits; conda resolved exactly that pair and the import failed (verified by the caller this session; the env now has astropy 8.0.2). Raising the floor is a declared-compatibility change. [AUTHOR] Repro: `sed -n 64p pyproject.toml; sed -n 72p pyproject.toml; conda run -n solarwindpy python -c 'import numpy; print(numpy.__version__, hasattr(numpy, "in1d"))'`
- **F203** [P1] `pyproject.toml:69`: `h5py` is a runtime dependency nothing imports, while `Plasma.save`/`load_from_file` (`plasma.py:360`, `plasma.py:443`) go through pandas HDF, which needs PyTables, declared only in `[dev]` (`pyproject.toml:131`): a plain `pip install solarwindpy` cannot save or load a Plasma. Positive control: the last search finds `tabulate`. [AUTHOR] Repro: `conda run -n solarwindpy python -c 'import importlib.metadata as m; print([r for r in m.requires("solarwindpy") if r.startswith(("tables","h5py"))])'; git grep -n -w -E "h5py|tables" -- 'solarwindpy/*.py'; git grep -n -w tabulate -- 'solarwindpy/*.py'`
- **F204** [P1] `pyproject.toml:70`: `pyyaml` is a runtime dependency imported only by `tests/test_declared_versions.py`; `numexpr` and `bottleneck` (`pyproject.toml:67`) are imported by nothing in the package (they may be deliberate pandas accelerators). Positive control: the last search finds `tabulate`. [AUTHOR] Repro: `git grep -n -w -E "yaml|numexpr|bottleneck" -- 'solarwindpy/*.py' 'tests/*.py'; git grep -n -w tabulate -- 'solarwindpy/*.py'`
- **F205** [P9] `pyproject.toml:156`: a `[tool.pip-tools]` block configures lockfile generation while `CONTRIBUTING.md:121` and `.claude/docs/DEVELOPMENT.md` say there are no lockfiles. Repro: `sed -n 156,159p pyproject.toml; sed -n 121p CONTRIBUTING.md; git ls-files | command grep -c -E "requirements.*\.txt$"`
- **F206** [P9] `MANIFEST.in:3`: `include LICESNSE.rst` names a misspelled file, so the line includes nothing; the repository's license file is `LICENSE`. Reported by the solar_activity slice as outside its scope. Repro: `command grep -n LICESNSE MANIFEST.in; ls LICENSE*`

## Control comparison

The control arm received the dispatch's two-sentence brief and nothing else: no principles, no
finding format, no test-quality context. Its report is saved verbatim at
`tmp/coherence-review/control-solar_activity.md`. Below it is compared with the principled arm's
`solar_activity` findings: the solar_activity layer of the Coherence review and its
`tests/solar_activity` subsection. The other test-tree findings cover the whole `tests/` tree,
which lies outside the control's scope, and are left out of the comparison.

Headline: each arm caught what the other missed. The control arm found correctness bugs the principled arm missed, two of them verified
by the assembler (a documented default that raises, and loggers named after the wrong module).
The principled arm found structural problems the control missed (two cache policies, a base layer
that predicts one of its two data sources, two homes for package data and for live-network
tests). The two arms agree on 26 items. Neither result can be attributed to the principles
(Experiment record).

### Overlap: matched pairs

Control item (by its report's wording and line) against the principled finding:

| Control item | Principled finding |
|---|---|
| bug 4, `sidc.py:372-375` docstring says cycle mean, code uses half max | F157 |
| bug 5, `icmecat.py:282` and `tests/drift/test_drift_icmecat.py:5,37` point at `icmecat.py:11` | F163 (the principled arm also found the stale `:32` and `:14` pointers) |
| bug 3 in part, `base.py:222` assert under a "more than two" comment | F145 |
| `convert_nans` declared `abstractstaticmethod`, implemented as an instance method | F142 |
| `download_data(self)` abstract with no parameters, called with two | F141 |
| `interpolate_data` base and `SIDC` signatures disagree | F143 |
| `abstractproperty` and `abstractstaticmethod` deprecated | F144 |
| unknown key raises `NotImplementedError` | F148 |
| bare `raise ValueError` at `base.py:552` | F149 |
| `pd.to_timedelta` twice at `base.py:575,578` | F146 |
| `run_normalization` docstring documents `norm_by`; `__doc__` assigned by hand | F150 |
| `m` equals `m13`, `hm` equals `hm13` dtype tables | F151 |
| `sidc.py:253` unreachable | F152 (the unreachable-branch part) |
| `_Dtypes_Columns` rebound over its own class, meaningless `defaults` | F153 |
| `totalstd_error` and siblings lack an underscore | F154 |
| `SSNExtrema` built twice | F155 |
| `calculate_extrema_kind` and `calculate_edge` share one loop | F156 |
| `cut_spec_by_ssn_band` builds bands from `self.data`, cuts `self.interpolated` | F158 |
| `plot_on_colorbar` branches are copies | F160 |
| `SSNPlot` fixes `ylim(0, 200)` against the round-up rule | F161 |
| `ICMECAT` re-implements `Base._init_logger` | F101, the package-wide logger finding, which absorbed the solar_activity copy |
| `filter` copies the name-mapping block and drops the warning | F162 |
| "Vectorized containment check" over a Python loop | F166 |
| `RULES_OF_THE_ROAD` missing from `__all__` | F165 |
| `ssn_extrema.csv.silso` tracked, unreferenced, placeholder cycle 25 | F168 |
| `sunspot_number/test_init.py` tests import machinery | F184 (the principled arm states it as a form mismatch with the parent `test_init.py`) |

### Findings only the control made

The control-arm labels C1 to C17 are the assembler's, for reference from the plan. They are not
numbered findings and are not counted in the Experiment record's tag counts.

- C1. `base.py:530-531,554`: `cut_spec_by_interval(kind=None)`, the documented default, raises
  `ValueError: Overlapping IntervalIndex is not accepted`. Verified by the assembler:
  `conda run -n solarwindpy python -c 'import pandas as pd; from solarwindpy.solar_activity.sunspot_number.sidc import SSNExtrema; SSNExtrema().cut_spec_by_interval(pd.date_range("2000","2010",freq="MS"))'`
  prints that error.
- C2. `sidc.py:271-279`: `std_error` is computed before `convert_nans` replaces SILSO's `-1`
  sentinel, so a sentinel row caches `-inf` or `-0.5`. The assembler read the order (std_error at
  lines 271-275, `self.convert_nans(csv)` at line 279) and did not run the case.
- C3. `base.py:207-222`: `get_data_ctime` runs the 8-digit date regex over the full path, not the
  file name, and three test fixtures work around it (`test_sidc.py:57-72`,
  `test_sidc_loader.py:33-78`, `test_plots.py:41-59`). The assembler read that `files` holds full
  path strings from `rglob`; the digit-path failure itself was not reproduced by either arm.
- C4. `sidc.py:13,526,551,565`: `mpl.dates` and `mpl.ticker` are used after a bare
  `import matplotlib as mpl`, and work only because `plots.py` imports `matplotlib.dates` first.
  Not checked by the assembler.
- C5. `base.py:38-40`: every logger is named `solarwindpy.solar_activity.base.<Class>`. Verified:
  `SIDC_ID("m").logger.name` prints `solarwindpy.solar_activity.base.SIDC_ID`.
- C6. `base.py:440`: abstract `load_or_set_data(self)` is called with `*args, **kwargs`.
- C7. `base.py:237-247`: `maybe_update_stale_data` logs "Updating stale data" on every call and
  never refreshes `ctime` and `age` after downloading.
- C8. `inplace=True` at `base.py:162` and `sidc.py:276,278,454`, and `.values` on an IntervalDtype
  Series at `base.py:632`, emit Pandas4Warnings, about 130 of 135 in the subpackage run.
- C9. "Today" is computed separately in three methods, which is why the tests carry
  midnight-straddle guards.
- C10. `base.py:24`: namedtuple assigned to `_Loader_Dtypes_Columns` but named
  `"LoaderNamedTuple"`.
- C11. `sidc.py:381-416`: neither extrema loop handles a cycle whose `Max` is `NaT`, which the base
  `calculate_intervals` handles.
- C12. Further asserts and control flow: `sidc.py:431` validates `norm_by` with `assert`,
  `sidc.py:456-462` uses `AttributeError` for control flow, `plots.py:91-95` validates with
  asserts, `plots.py:35` marks `_format_axis` abstract with a real body, `plots.py:119-126` builds
  an unused figure.
- C13. `sidc.py:588`: `skiprows=48` couples the reader to the header length; `comment="#"` would
  not.
- C14. `icmecat.py`: empty input loses the caller's index type (line 452), a redundant guard
  (line 454), `_PINNED_VERSION` repeats the version already in the URL (line 23).
- C15. Shebangs in `solar_activity/__init__.py:1` and `sidc.py:1`.
- C16. Tests: three different network guards, `matplotlib.use("Agg")` repeated, overlapping base
  and SIDC tests (empty-cache epoch, age, `set_id` refusal), `check_freq` warnings, no test of
  `kind=None` or of the `base.py:552` raise, two tests that expect `AssertionError`.
- C17. Tooling failure: `pytest tests/solar_activity --cov=solarwindpy.solar_activity` fails at
  collection with `ImportError: cannot load module more than once per process`. Verified by the
  assembler on one file:
  `conda run -n solarwindpy pytest -q -p no:randomly tests/solar_activity/test_base.py --cov=solarwindpy.solar_activity`
  fails with that error, and the same command with `--cov=solarwindpy` gives 44 passed. **Pass 1
  did not cover this.** Pass 1 reviewed the hooks' coverage invocations, which use the whole
  package form `--cov=solarwindpy` (`.claude/hooks/pre-commit-tests.sh:36`), and never tried a
  dotted subpackage target. I infer the pre-commit gate is unaffected, from that one passing run.
  The control's two theories (pytest-cov imports the subpackage and numpy before collection, or a
  version clash in this env) both fit; neither arm tested which holds.

### Findings only the principled arm made

- F139: `ICMECAT` subclasses nothing in `base.py`, so the base layer predicts one of two sources.
- F140: two cache policies (daily by file name against 30 days by mtime) in one subpackage.
- F147: `DataLoader` re-stores the key and URL its `ID` already holds.
- F116, its solar_activity half: four public classes named `Base`, and `solar_activity/plots.py:16`
  reads `base.Base` as plotting's.
- F152 in full: the seven series keys are spelled in five places (the control found only the
  unreachable branch).
- F159: `plot_on_colorbar` is a plotting method in the data module (the control noted its TODO,
  not the placement).
- F163, its drift-test half: the stale `:32` and `:14` pointers in the drift test.
- F164: the `icme/__init__.py` doctest repeats the class doctest.
- F167: private `_intervals` holds what the public API calls `estimated_intervals`.
- F169: package data ships through `MANIFEST.in` for one subpackage and `pyproject.toml` for
  another.
- F183: `sidc.py` tests split by class, `icmecat.py` tests split by kind.
- F185: live-network checks of one catalog have two homes and two markers.
- F186: the SIDC download base has no drift check while the ICMECAT URL has one.

### API changes proposed by each arm

The principled arm tags nine `solar_activity` findings `[AUTHOR]` (F140, F143, F148, F116 for its solar_activity `Base`,
F154, F157, F161, F168, F185) and keeps each out of every stage until the
author rules. Its slice stages did schedule three caller-visible changes untagged: the abstract
signatures of the public base classes (F141, F142), the `assert` under `get_data_ctime` made a
`ValueError` (F145), and, from the plotting slice, a renamed `tools` logger (F137). The
assembled plan now lists all three for the author. Both arms, then, scheduled some
caller-visible changes without asking; the control did so more often.

The control arm asks approval for three items only: deleting `ssn_extrema.csv.silso`, renaming
the hemispheric `*std_error` columns, and changing `ylim(0, 200)`. Its nine-commit plan makes
other caller-visible changes without asking: exception types (`NotImplementedError` to
`ValueError` in `ID.set_key`, asserts to `ValueError` or `TypeError`, with two tests rewritten to
match), the behavior of the `kind=None` default (raise a clear error or default to `"Cycle"`),
logger names (from `type(self).__module__`), the abstract signatures, and `RULES_OF_THE_ROAD` in
`__all__`. The principled arm marks the exception-type change (F148) and the signature change
(F143) for the author; the control plans both as refactors.

### Scope of each proposed plan

The control's plan is nine conventional commits, all inside `solarwindpy/solar_activity/`,
`tests/solar_activity/`, and `tests/drift/test_drift_icmecat.py`, ordered bugs first. The
principled arm's plan for this slice is four `solar_activity` stages (pointers and dead copies,
one home per fact in `sidc.py`, base contracts, `ICMECAT` on the base layer), two test-tree stages
that reach across the whole `tests/` tree, and one author-decision stage. It schedules no bug
fix, because it found none of C1, C2, C3, C5, C11.

## Experiment record

One run, with one control subpackage, cannot establish that the principles caused any
difference between the arms. The arms differed in more than the principles. The principled arm
had the dispatch's context, the finding format, the test-quality program's files, and a
whole-package view. The control had a two-sentence brief and one subpackage. Each arm is one
sample of one model's output. What follows describes what happened. It does not measure an
effect.

### Counts

206 findings after merging (214 in the five reports, 10 merged away, 2 added by the assembler:
an item the solar_activity slice left unnumbered, and F47, added on the main thread's request). By principle tag:

| Tag | Tooling (Pass 1) | Package, core, examples, env | fitfunctions, instabilities | plotting, tools | solar_activity, test tree | Total |
|---|---|---|---|---|---|---|
| P1 | 6 | 26 | 8 | 13 | 14 | 67 |
| P2 | 7 | 14 | 15 | 7 | 10 | 53 |
| P3 | 0 | 4 | 8 | 5 | 11 | 28 |
| P4 | 0 | 2 | 0 | 0 | 1 | 3 |
| P5 | 0 | 3 | 1 | 1 | 3 | 8 |
| P6 | 2 | 0 | 0 | 0 | 0 | 2 |
| P7 | 0 | 0 | 0 | 0 | 0 | 0 |
| P8 | 1 | 1 | 2 | 0 | 0 | 4 |
| P9 | 31 | 3 | 0 | 1 | 6 | 41 |
| All | 47 | 53 | 34 | 27 | 45 | 206 |

The solar_activity column counts F206, the `MANIFEST.in` finding the assembler numbered.
Count with `command grep -o -E '^- \*\*F[0-9]+\*\* \[P[0-9]\]' docs/dispatches/findings-coherence-and-tooling-review-2026-11-04.md | awk '{print $3}' | sort | uniq -c`.

Proposals against escalations: 51 findings carry `[AUTHOR]` (17 package and core, 12
fitfunctions and instabilities, 13 plotting and tools, 9 solar_activity and test tree, 0 tooling).
The other 155 are proposals a cleanup session can carry out under a test that passes before and
after. Pass 1 tagged no finding `[AUTHOR]`. Its 25 verdicts (keep 3, rebuild 6, retire 16) and
the `CLAUDE.md` rewrite are author decisions as a whole, and the plan lists them that way.

Merged duplicates, each kept under the id of the member that comes first in reading order. Local
numbers are given as slice and number (tooling #28 is Pass 1's F28 before renumbering):

- core #7 into tooling #28, now F28: the `CLAUDE.md` line pointer.
- tooling #45 into core #13, now F200: `pip install -e .` without `[dev]`.
- solar #2 and the copy half of plotting #18 into fitfunctions #16, now F101: the copied `_init_logger`.
- solar #13 into plotting #2, now F116: four classes named `Base`.
- plotting #19 into core #4, now F51: units declared in two homes, the `nuc` TODO.
- solar #41 into core #51, now F171: no test file for `vector` or `tensor`.
- solar #40 into fitfunctions #22, now F178: `tests/fitfunctions/` without `__init__.py`.
- solar #44 into plotting #21, now F181: review-named test files.
- solar #46 into fitfunctions #20, now F176: root `test_source_*_defects.py` files.
- solar #28 into solar #27, now F163: stale `icmecat.py:<n>` pointers.

Where either member carried `[AUTHOR]`, the merged finding keeps it.

### How the principles flexed

**P1 bent well across layers.** The core and solar_activity slices used it on code; Pass 1 used
it on tooling (five statements of the coverage floor, F22; three branch-naming schemes,
F36); the env-spec layer used it on dependency declarations (F196 to F201). The revised
reading, one home per idea, fits several Pass 1 findings that their reviewer tagged P9 because
the claim was false: F26 (one false claim about the pre-commit hook in `CLAUDE.md` and
`TEST_PATTERNS.md`), F27 (two homes for the run command that disagree), and F28 (a line
number copied into prose, the same defect the solar_activity slice tagged P1 at F163). The
assembler kept the reviewer's tags and added a sentence to each of those three findings. The
merges above are P1 applied to the review itself: ten findings had a second home.

**P2 needed the contrast set to work.** Judged alone, `Spacecraft.r`, `Vector.rho`, and
`residuals` are reasonable names. Judged against their siblings they collide (F73, F74,
F86). The contrast-set framing is what found them. It also found the defect class the dispatch
named, a mis-pointed name with a correct value (F77, `cos_colat`).

**P3 under delegation.** Predict-before-reading did not survive delegation as written. Two slices
state that their Predicted lines were written after reading the lower layers: the core slice
("written after the evidence pass ... reconstructions, not prior predictions") and the
solar_activity slice ("I read all of `solar_activity` before writing any line of this file").
The fitfunctions slice says its subpackage predictions were formed from `__init__.py` alone, and
its module and test-tree predictions after one introspection pass, but all were written into the
file after the reading, "from memory". The plotting slice states no timing, and its file offers
no evidence either way. One weak sign of genuine prediction is a guess that turned out wrong:
"`binned` reads like a second aggregation module and may duplicate `agg_plot`" was refuted below.
Each slice wrote one file at the end of its run, so nothing in the delegation shape gave a
prediction a place to land before the reading. Three of the four slices reported this
themselves. The reconstructed predictions still did work. They stated each layer's contract in a
sentence a reader can check (the `Hinge` docstring's four-member contract; the `ID`, `DataLoader`,
`ActivityIndicator` triple), and the Found lines are organized as departures from those
contracts, which is where most P3 and P5 findings come from. What they cannot do is show that
the layer above predicted the surprise, since the writer already knew it. The control arm made
no predictions and found the same base-contract mismatches (F141, F142, F143) by reading.

**P4 found little.** Three findings in the whole review. The plotting slice's `__all__` scan found
every public name used outside its module (positive control included). Either the package's
seams are in good shape, or the lens was rarely aimed; the review cannot tell which.

**P5 often fused with P1.** Most proposed changes name the form they mirror, and the plan states
one per stage. In several places the lens was stretched to cover a missing form rather than a
copied one (F57 and F58, asserts where `Core._require_dataframe` raises). In those places
P5 reads as "the sibling's form is the one to mirror", which works.

**P6 is judgment with no defined measure.** Each plan stage's Density line is written as a
judgment fitted to that stage. Two Pass 1 tags were stretched to P6 for runtime cost (F25) and
attention cost (F30); both are reasonable readings of density.

**P7 had a seam only at the stages.** Each plan stage's "done when" is an explicit acceptance
criterion and is binary. Elsewhere "done when it fits" was not invoked by any reviewer.

**P8 placed most findings.** It worked mainly as a router: 51 findings were sent to the author
rather than given a stage. It also shaped the review's wording on physics. The heaviside value
at the step (F88), the Verscharen doctest coefficients (F105), the extrema rule (F157), and
the anisotropy masking (F59) are all stated as suspicions or proposals, not corrections.

**P9 fit tooling best, and code less well.** It is a rule for review claims. Pass 1 used it as the
default tag for a tooling claim with no working check (31 of 46). The plotting slice stretched it
to a code assertion that can never fire (F136), and said so; no principle names "a check in
code must be able to fail". The positive-control half held throughout. Every "found none" in the
five reports carries one.

### Forced or stretched template fits, as the reviewers recorded them

- F8 tagged P8: the author's push checkpoint, not physics or API.
- F25 tagged P6: runtime density, not concepts per line.
- F43 tagged P2: an import path that points at nothing, not a misleading name among siblings.
- F136 tagged P9: a code assertion that cannot fire, by nearest fit.
- F127 first tagged P4, moved to P3: the wrapper is private and exposes nothing.
- F133 mixes P2 (wrong docstring) and P1 (copied logger, now merged into F101).

### Where reasoning overrode a principle or a premise

- **Stale test-quality premise.** The dispatch said to take the 2026-10-05 dispatch's open units
  as given. Three slices checked instead and found them merged. `gh pr list --state merged --limit 60`
  confirms it: `tq-fix/p0-simplify` (#496) and `tq-fix/scalar-w-nan` (#494) merged on
  2026-10-07, and every unit through `tq-fix/rm-hist-agg` (#521) merged by 2026-11-02. `git log`
  shows `mutation-recheck` recorded (82240ad3). `gh pr list --state open` is empty. The solar
  activity slice took the stale list at face value and wrote that `p0-simplify` is in flight
  (its preamble, its findings on `tests/fitfunctions/__init__.py` and the root fitfunctions files, and its test-tree stage). The assembler corrected those lines.
  One unit is still open: step 6, the parked `hingemax-point` (`hinge.py:1070` still raises
  `NotImplementedError`). The plan's hinge stage depends on it. Step 4 ("read the warnings") has
  no closing commit the assembler could identify. `tq-fix/warning-fixes` (#499) suggests it ran.
  The plan names it as unverified-open where the core slice's warning finding depends on it.
  Overriding the premise was the right call: following it would have made several plan stages
  wait on finished work.
- **Untracked files and the alias test.** The solar_activity slice judged the `rglob` scan a
  coherence defect rather than an author's-file problem (F194). The suite's own
  `walk_packages` definition supports that reading. Which fix to take stays with the author.
- **The alias test moved from a seam to open space.** The solar_activity slice treated the
  `rglob` scope as the defect and offered scoping as the fix. With the author, the main thread
  judged alias choice to be open-space composition, not an author seam: the
  package already imports under real names, and sessions mirror the code around them. The plan
  now recommends deleting the test, with scoping as the fallback. Deleting a test is still a
  deletion, so it stays in the author's list.
- **Pass 1 resolved a doc tension.** `memory.md` lists project architecture for `CLAUDE.md`, while
  `best-practices.md` says models find layout themselves. Pass 1 applied the two-question test and
  cut the layout lines. That is a reasoned override of one source by another, stated in the
  proposal's rationale.

### The seams: required asks and acceptance criteria

These held:

- Rebuilding the conda env and deleting `solarwindpy/fitfunctions/lines_BACKUP_41608.py` were each
  asked of the author before acting. The deletion overrode the dispatch's anti-pattern for that
  one file, with the author's explicit approval.
- Every public-API, data-column, scientific-result, and physics item is a proposal (`[AUTHOR]`
  above), and the plan holds each one out of its stages until the author rules.
- No tracked file under `solarwindpy/`, `tests/`, `.claude/`, or `CLAUDE.md` changed in this review
  (`git status --porcelain` lists only the two output files and the author's untracked
  directories).
- The acceptance checks for this file and the plan are binary, and their outputs are recorded in
  the hand-back.

The control arm's "unread until Pass 2 reaches solar_activity" seam held only in part. A
subagent's result returns to the parent, so the main thread saw the control report when it
arrived; the report's header says so. The rule held for the Pass 2 solar_activity reviewer, which
reports that one stray `head ... >/dev/null` command touched `control-solar_activity.md` with its
output discarded.

The main thread's brief to Pass 1 said 24 `.claude` files. There are 25, and Pass 1 counted them
itself.

### Correct content that was not its to decide

The clearest instance is in the control arm. Its plan schedules caller-visible changes as
refactors: new exception types, a new behavior for the `kind=None` default, new logger names,
and new abstract signatures, with two tests rewritten to match. Each is probably right. None was
its to decide, and the plan reads as competent work. It asked approval only for a deletion, a
column rename, and a plot range.

In the principled arm, every sign convention and physics reading the assembler looked for stayed
a proposal: which residual sign governs (F86), the step value at `x0` (F88), the extrema rule
(F157), the missing-data rule for anisotropy and distance (F59, F63). Two places come
close to deciding without saying so. The core slice applies the merged `scalar-w-nan` rule to
`Plasma.anisotropy` and `distance2sun` as if it obviously governs them. The finding is tagged
`[AUTHOR]`, but its framing ("contradicts the missing-data rule") presumes the reading. The
plotting slice suggests `RangeLimits` for `clim` because it "matches the docstring", which picks
a public type while deferring the choice. Pass 1's proposal drops the `python3 -m pytest` warning
on an inference (F27), labelled as one. The principled slices also scheduled three caller-visible changes without the
tag (Control comparison, "API changes proposed by each arm"). The assembler did the same in its
first plan draft: three stages' done conditions wrote one outcome of a pending ruling (`nan nan`,
a divisor of `n p1`, a path of `logX-logY`). Review caught them, and they now read as "the value
the author's ruling names", with the proposal in parentheses. Merging and renumbering change no
claim.

### Self-assessed claims contradicted by verification

- The solar_activity slice's "`p0-simplify` is in flight" (above): contradicted by `gh`.
- F134 said "waits on `p0-simplify`", which the slice's own stage 8 contradicted. It also named
  the class `LogNormal`. `git grep -n "^class " solarwindpy/fitfunctions/gaussians.py` shows
  `GaussianLn` (line 201), whose `normal_parameters` is at line 297. Corrected.
- F28 located the `CLAUDE.md` pointer at line 24; `command grep -n 'units_constants.py:16' CLAUDE.md`
  prints line 25, as the core slice had it. Corrected.
- `CLAUDE.md` states coverage of about 95%; Pass 1 measured 98% (F22).
- Pass 1 first suspected `validate-tags.sh` of aborting under `set -e`, ran it, and withdrew the
  suspicion itself.
- The prior review and the solar_activity slice proposed ruff `ICN` as a replacement for
  `tests/test_import_aliases.py`. PR #480 had already probed it: `ICN` cannot ban every alias
  outside a whitelist. The finding text now says so.
- The dispatch's Motivation lists `lines_BACKUP_41608.py` as untracked author work. It was
  deleted during this session with the author's approval, so the claim was true when written.

No finding was dropped. Every spot-checked repro reproduced.

### Repro spot-check

The assembler reran 34 Repro commands, spread over all five reports and weighted toward
`[AUTHOR]` and bug-class findings. All 34 reproduced.

| Finding | Report | Observed |
|---|---|---|
| F10 | tooling | 13 pytest allow rules |
| F17 | tooling | "No Python files changed" for an edit to `plasma.py` |
| F18 | tooling | `--physics` exits 127 |
| F23 | tooling | path built as `tests/tests/core/plasma` |
| F24 | tooling | `timeout` exits 127 |
| F28 | tooling | line 16 is `import pandas as pd`; the comment is at line 21 |
| F40 | tooling | 0 matching branches |
| F41 | tooling | 17 non-semver tags |
| F50 | core | 10 code lines carry the level-name literal |
| F202 | env | numpy 2.5.4, `in1d` absent |
| F57 | core | under `python -O`, `AttributeError: 'str' object has no attribute 'data'` |
| F59 | core | `Plasma.anisotropy` 1.0 against `Ion.anisotropy` NaN |
| F63 | core | `distance2sun` 2.9e10 against `position.mag` NaN |
| F73 | core | `Vector` against `Series` |
| F75 | core | `Tensor`, `DataFrame`, `Vector`, `Vector` |
| F78 | core | `AttributeError: 'BField' object has no attribute '__getattr__'` |
| F86 | fitfunctions | residuals 0.873 against -0.873 |
| F87 | fitfunctions | 5 kernel copies |
| F88 | fitfunctions | `HeavySide` gives 7 at `x0`, `GaussianPlusHeavySide` 2.5 |
| F98 | fitfunctions | message-less `AssertionError` |
| F101 | fitfunctions | 7 `_init_logger` definitions |
| F105 | instabilities | AIC row `b=0.364`; FMW `a=-0.408` |
| F109 | instabilities | `float64` |
| F119 | plotting | `tuple` against `RangeLimits` |
| F123 | plotting | `LogAxes(x=True, y=True)` with path `linX-linY` |
| F128 | plotting | `['a_bimax', 'pm']` missing; `n_{\alpha_bim\alphax}` |
| F136 | tools | `n p2` divided by `n p2` |
| F141 | solar_activity | abstract takes none, call and subclass take two |
| F146 | solar_activity | lines 575 and 578 |
| F151 | solar_activity | `True True` |
| F163 | solar_activity | five stale `icmecat.py:<n>` pointers; actual lines 19, 35, 51 |
| F168 | solar_activity | files differ, including the cycle 25 maximum |
| F194 | test tree | fails naming `solarwindpy/tests/test_base_master.py:184` and `test_plasma_old.py:9,17` |
| F206 | packaging | `include LICESNSE.rst`; only `LICENSE` exists |

### Not assessed

Harmony is the author's judgment. This review does not assess it.
