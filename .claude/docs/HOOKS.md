# Hook Scripts

`.claude/settings.json` registers no Claude Code hooks. The scripts in
`.claude/hooks/` run in two ways: the git pre-commit hooks in
`.pre-commit-config.yaml` call some of them, and the rest run by hand.

## Run by the git pre-commit hooks

- `pre-commit-tests.sh`: the `solarwindpy-physics` hook. On any commit that
  touches a `.py` file it runs the full suite with the coverage floor set by its
  `--cov-fail-under` argument. The floor is a regression ratchet below measured
  coverage; raise it as coverage rises.
- `project-env.sh`: runs a command inside the `solarwindpy` conda env. The
  pre-commit hooks that run Python go through it.

## Run by hand

```bash
.claude/hooks/test-runner.sh --changed     # tests for changed files
.claude/hooks/test-runner.sh --physics     # physics validation subset
.claude/hooks/test-runner.sh --coverage    # full coverage report
.claude/hooks/test-runner.sh --fast        # quick run
.claude/hooks/test-runner.sh --all         # complete suite
python .claude/hooks/coverage-monitor.py   # per-module coverage report (advisory)
python .claude/hooks/create-compaction.py  # write a session-state compaction file
.claude/hooks/validate-tags.sh             # check git tags follow the release conventions
```
