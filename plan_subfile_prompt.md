# Claude Code Prompt: Plan Management Optimization

## Objective
Optimize token and usage for plan management while maintaining functionality. Refactor plan storage, reintroduce a lightweight git-first checklist integration, add end-of-phase compaction, and design an auditor and file manager that validate plan state against the git single source of truth.

## Repo context
- Plans live in `solarwindpy/plans/`.
- Some plans are single files: `solarwindpy/plans/<name>.md`.
- Target structure for `default` and `full` plans:

```
solarwindpy/plans/<name>/
  0-Overview.md
  1-<Phase 1>.md
  2-<Phase 2>.md
  ...
  N-<Phase N>.md
```

- Completed plans move to `solarwindpy/plans/completed/` and must not be searched by default.
- A prior git-first checklist tool likely existed before commit `f87a14e01ffe4c3443e50903e404ce1d6ed65100`.

## Constraints and token rules
- Do not scan the whole repo repeatedly. Prefer `ripgrep` on narrow paths. Cache lightweight results in `.cache/plan-index.json`.
- Summarize long outputs. Keep console prints short and actionable.
- Ignore `solarwindpy/plans/completed/` unless explicitly requested.
- Keep diffs tight. Prefer small, focused commits.

## Tasks
1. **Migrate storage for default and full plans**
   - Create `tools/plan_migrate.py`.
   - Input: `solarwindpy/plans/*.md` that correspond to default or full, not minimal, and not in `completed/`.
   - Split by top-level phase headings (match `^#\s+Phase\s+\d+[:\- ](.*)` or fallback `^##\s+Phase\s+\d+`). If no headings, create `1-Phase-1.md` with entire content.
   - Create `0-Overview.md` with purpose, a high-level checklist per phase, and a table of contents listing the phase files.
   - Replace `<name>.md` with folder `<name>/` and numbered files. Use moves to preserve history.
   - Provide `--dry-run`.

2. **Git-first checklist integration (lightweight)**
   - Create `tools/plan_checklist_git.py`.
   - Accept a plan folder path.
   - Use `ripgrep` to find checklist markers in the repo (for example `[ ]`, `[x]`, `TODO:`) linked to plan items.
   - Write a small cache `.cache/plan-index.json` that maps checklist items to code refs.
   - Update each phase file with a short References section containing stable relative paths and line hints. Keep this under 10 lines per phase.
   - If the prior tool cannot be located via `git log -S` around the given commit, implement this minimal version.

3. **End-of-phase compaction**
   - Create `tools/plan_compact.py`.
   - On phase completion:
     - Append a short summary to `claude_session_state.md` (date, plan name, phase id, key decisions, follow-ups).
     - Update `0-Overview.md` checklist state and link to the completed phase file.
     - Truncate verbose logs into a 5 to 10 bullet summary stored next to the phase file as `phase-summary.json`.

4. **Auditor and file manager design and scaffold**
   - Produce a short recommendation with value proposition and tradeoffs for:
     - Option A: Integrate auditor and file manager inside existing plan manager and implementer agents.
     - Option B: Standalone agents. Either a single combined maintainer or two small agents.
   - Implement the recommended option minimally:
     - Create `agents/plan_maintainer.py` (combined) or `agents/plan_auditor.py` and `agents/plan_file_manager.py` (separate).
     - Auditor duties: validate folder shape, numbering, presence of `0-Overview.md`, checklist integrity, cross-check against git single source of truth, and report drift.
     - File manager duties: safe moves between active and `completed/`, renumber phases, rebuild `0-Overview.md` index, refresh caches.
     - Provide a CLI with subcommands: `audit`, `fix`, `migrate`, `compact`, `reindex`.

5. **Documentation and CI**
   - Update `README.md` with usage snippets.
   - Add `docs/plans.md` describing folder spec, naming rules, and examples.
   - Add a CI job that runs the auditor in check mode on PRs, ignoring `completed/`.

## Acceptance criteria
- New default and full plans use the numbered folder format.
- `0-Overview.md` exists and lists phases with checkboxes that mirror per-phase tasks.
- `tools/plan_checklist_git.py` runs quickly and writes a small cache. No full-repo scans per run.
- `tools/plan_compact.py` updates `claude_session_state.md` and `0-Overview.md` with concise summaries.
- `agents/*` implement the chosen design and pass `--help` plus a smoke test.
- `completed/` is ignored by default by all tools.
- CI fails if auditor detects structural drift.

## Deliverables
- `tools/`: `plan_migrate.py`, `plan_checklist_git.py`, `plan_compact.py`.
- `agents/`: either `plan_maintainer.py` or `plan_auditor.py` and `plan_file_manager.py`.
- Updated docs: `README.md`, `docs/plans.md`.
- CI workflow update.

## Commands to use
- Search narrowly:
  - `rg -n "Phase\\s+\\d" solarwindpy/plans`
  - `git log -S "checklist" -n 20`
- Run tools:
  - `python tools/plan_migrate.py --dry-run`
  - `python tools/plan_checklist_git.py solarwindpy/plans/<name>`
  - `python tools/plan_compact.py --plan solarwindpy/plans/<name> --phase 2`
  - `python -m agents.plan_maintainer audit --path solarwindpy/plans/<name>`

## Architecture decision request
Produce a short written recommendation with tradeoffs, then scaffold accordingly. If separate agents are chosen, explain why separate auditor and file manager are better than a combined maintainer for this repo.

## Assumptions
- Migrate all existing default and full single-file plans under `solarwindpy/plans/*.md` that are not in `completed/`. If any should be excluded, note them in the PR.

## Output
- A single PR with small, focused commits and a brief summary at top.
- Final console output: a short checklist of what changed and how to run each tool.
