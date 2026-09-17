<!--
Spent-When: MARKED(<self>)
Supersedes: none
-->

# Remove dead `Write(path)` deny rules from project settings

## Context

Every Claude Code session in this repo starts with four warnings:

```
Permission deny rule (.claude/settings.json): Write(./.env*) is not matched by
file permission checks — only Edit(path) rules are.
```

...one each for `Write(./.env*)`, `Write(./secrets/**)`, `Write(./.token*)`,
`Write(~/.ssh/**)`.

Root cause: Claude Code's file-permission layer resolves all file-editing tools
(`Write`, `Edit`, `MultiEdit`, `NotebookEdit`) against the single `Edit(path)`
rule namespace. A `Write(path)` entry in a permission list is therefore never
consulted. `Read(path)` is a distinct, live namespace, which is why the five
`Read(...)` deny rules in the same block draw no warning.

Security impact: none. `.claude/settings.json` already denies `Edit(./.env*)`,
`Edit(./secrets/**)`, `Edit(./.token*)`, and `Edit(~/.ssh/**)` — the same four
paths. Those rules are live and already block write attempts. The `Write(...)`
entries are pure duplicates.

Intended outcome: sessions start clean, with protection unchanged.

## Change

Single file: `.claude/settings.json`, `permissions.deny` array.

Delete these four lines (they sit immediately after the four `Edit(...)` lines):

```json
"Write(./.env*)",
"Write(./secrets/**)",
"Write(./.token*)",
"Write(~/.ssh/**)",
```

Do **not** follow the warning text literally. It suggests replacing each
`Write(X)` with `Edit(X)`; since the matching `Edit(X)` already exists, that
would produce four duplicate entries. Deletion is the correct fix.

Leave untouched: the four `Edit(...)` rules, all `Read(...)` rules, and the
`Bash(git add ...)` deny rules that guard the same paths via a different
mechanism.

## Scope check already done

`grep -n 'Write(' ~/.claude/settings.json .claude/settings.local.json
~/dotfiles/claude/.claude/settings.base.json` returns nothing. The project
`.claude/settings.json` is the only affected file.

## Verification

1. `python -c "import json; json.load(open('.claude/settings.json'))"` — confirm
   the file still parses after the edit (watch the trailing comma on the line
   above the deletion).
2. Confirm the four `Edit(...)` deny rules survive:
   `grep -n 'Edit(' .claude/settings.json` should show exactly four entries.
3. Start a fresh Claude Code session in this directory. The four permission
   warnings should be gone and no new ones should appear.
4. Spot-check the protection is live: ask a session to write to `./.env.test`.
   It should be denied by the `Edit(./.env*)` rule.

## Commit

Per the project's conventional-commit convention:

```
chore(settings): drop dead Write() deny rules, superseded by Edit() rules
```

## Out of scope (noted, not changed)

`ai.preferredModel` is pinned to `claude-sonnet-4-20250514`. Raise separately.

---

## Empirical Findings (2026-09-17 trial run)

### End-state metrics

- Deny-rule lines removed: 4 of 4 named in the startup warnings.
- `permissions.deny` entries: 29 before, 25 after.
- Commits predicted by the plan: 1. Landed: 1. Match.
- Files changed: 1 (`.claude/settings.json`), 4 deletions, 0 insertions.

### Acceptance Criteria

| AC | Status | Evidence |
|---|---|---|
| `.claude/settings.json` still parses after the edit | PASS | `python -c "import json; json.load(...)"` printed `parses OK, deny entries: 25` |
| The four `Edit(...)` deny rules survive | PASS | Filtering `permissions.deny` printed `['Edit(./.env*)', 'Edit(./secrets/**)', 'Edit(./.token*)', 'Edit(~/.ssh/**)']`. Positive control for the same filter on the removed class: `Write rules: []`, against 4 present before the edit. |
| Fresh session start emits no permission warnings | DEFERRED | Requires a new session; this one was already running when the edit landed. Next session start is the observation. |
| Writing to `./.env.test` is denied by `Edit(./.env*)` | DEFERRED | Not exercised. Triggering a deny mid-session surfaces a permission prompt to the author for no new information beyond AC2, which already shows the live rule present. |

### Deviations from plan

- None. The plan's stated non-obvious call (delete the four `Write(...)` lines rather than
  rewrite them to `Edit(...)` as the warning text literally instructs, because that would
  duplicate the existing `Edit(...)` entries) is what execution did.

### Commits

- `726bf441` chore(settings): drop dead Write() deny rules, superseded by Edit() rules

## Spent-Mark: executed, findings recorded
