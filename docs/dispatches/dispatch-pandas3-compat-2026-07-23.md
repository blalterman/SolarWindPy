# Dispatch: pandas 3 compatibility while preserving pandas 2 support

**Generated:** 2026-07-23
**Branch:** master
**Work type:** software

## Scope

Make `/Users/balterma/observatories/code/SolarWindPy` pass its own test suite
under pandas 3.x without regressing pandas 2.3.3, then tag `v0.3.1`.

Measured baselines at authoring (both runs exclude the two files named in
Operational Constraints):

| Environment | pandas | Result |
|---|---|---|
| `solarwindpy` | 2.3.3 | 2181 passed, 5 skipped, 0 failed, 0 errors |
| `imap-loaders-20260225` | 3.0.3 | 2055 passed, 5 skipped, 85 failed, 41 errors |

pandas 2.3.3 is clean, so every one of the 126 failures and errors is a
pandas-3 regression. None are pre-existing.

Three defect classes carry evidence; the remainder are whatever the suite
still reports after these are fixed. Defect 2 is a latent defect that no test
exercises, so it is not counted among the 126.

1. `solarwindpy/plotting/agg_plot.py:125` passes `axis=0` to
   `Series.groupby()`. pandas 3 removed the keyword. Error:
   `TypeError: Series.groupby() got an unexpected keyword argument 'axis'`,
   accounting for 10 of 10 failures in `tests/plotting/test_agg_plot.py`.
   `axis=0` is the pandas-2 default, so deleting the keyword is
   behavior-preserving on both versions. The failure distribution by module
   (21 `test_hist2d_plotting.py`, 15 `fitfunctions/test_plots.py`, 13
   `test_hist2d_pandas_compat.py`, 10 `test_agg_plot.py`, 5
   `test_histograms.py`) is consistent with this single site cascading
   through every `AggPlot` subclass.
2. `solarwindpy/instabilities/verscharen2016.py` lines 350, 360, 508 call
   `.iteritems()`, removed in pandas 2.0 — one major version below the
   `pandas>=2.0` floor at `pyproject.toml:37`. These three sites are NOT
   among the 126 pandas-3 failures: the pandas 2.3.3 run passes 2181 tests
   with zero failures despite `.iteritems()` being absent from pandas 2, which
   proves no test executes these lines. Fixing them is correct and the test
   suite cannot confirm it, which is why AC4 is a grep rather than a test
   result. `.items()` is the replacement and exists in every pandas version
   this project supports.
3. Uppercase offset aliases, removed in pandas 3. Error:
   `ValueError: Invalid frequency: H ... Did you mean h?`. Confirmed sites
   are test-side: `tests/core/test_alfvenic_turbulence.py:534` and `:535`
   (`freq="H"`), and `tests/plotting/labels/test_datetime.py:63` (the
   `test_cases` list contains `"2H"`, `"1M"`, `"1Y"`). The pandas-3 spellings
   are `h`, `ME`, `YE`.

DECIDED (user, 2026-07-23): scope is the full pandas-3 clean plus the version
tag, not only the three classes above.

## Motivation

Every plotting entry point in this library — `Hist1D`, `Hist2D`, every
`AggPlot` subclass, the `fitfunctions` plot layer — raises under pandas 3,
because `agg_plot.py:125` sits in the shared `grouped` property. Four of the
seven conda environments carrying SolarWindPy still run pandas 2.3.3 and three
run pandas 3.x, so the library currently works in some of the user's
environments and is unusable in the others.

A downstream analysis notebook
(`/Users/balterma/observatories/wind/helium-abundance/ahe-ar-indicator-icme/notebooks/ahe-xhel-ar/01_xhel_setup.ipynb`)
carries a kernel-local monkeypatch that strips the `axis` keyword from
`Series.groupby`/`DataFrame.groupby` to work around defect 1. That
monkeypatch, and the ones in the sibling notebooks of that repo, are
removable once this dispatch lands; removing them is separate work in that
repo, not this one.

## Read First

1. `/Users/balterma/observatories/code/SolarWindPy/solarwindpy/plotting/agg_plot.py`
   — lines 110-140: the `grouped` property holding defect 1, and line 131, a
   commented-out second `groupby(..., axis=0)` call.
2. `/Users/balterma/observatories/code/SolarWindPy/solarwindpy/plotting/hist2d.py`
   — lines 230-250: `agg()` and the `alim` masking that the largest failing
   module exercises.
3. `/Users/balterma/observatories/code/SolarWindPy/solarwindpy/instabilities/verscharen2016.py`
   — lines 345-365 and 505-512: defect 2.
4. `/Users/balterma/observatories/code/SolarWindPy/tests/plotting/test_hist2d_pandas_compat.py`
   — the existing pandas-compatibility test module, 13 of whose tests fail;
   read it before adding new compatibility tests so the new ones match its
   conventions.
5. `/Users/balterma/observatories/code/SolarWindPy/pyproject.toml`
   — line 33 `dynamic = ["version"]`, and `setup.py` line 5
   `use_scm_version=True`: the version comes from git tags, so the bump is a
   tag and not a file edit.

## Acceptance Criteria

Run from `/Users/balterma/observatories/code/SolarWindPy`.

- [ ] pandas-3 suite clean: `conda run -n imap-loaders-20260225 python -m pytest -q --no-header --ignore=tests/plotting/test_performance.py --ignore=tests/test_issue_titles.py 2>&1 | tail -1` → a summary line containing `0 failed` and no `error` count, exit 0 (authoring baseline: `85 failed, 41 errors`)
- [ ] pandas-2 no regression: `conda run -n solarwindpy python -m pytest -q --no-header --ignore=tests/plotting/test_performance.py --ignore=tests/test_issue_titles.py 2>&1 | tail -1` → `2181 passed, 5 skipped` or a higher passed count, zero failed, exit 0
- [ ] defect 1 removed: `grep -n "groupby(.*axis=" solarwindpy/plotting/agg_plot.py` → no output, exit 1 (positive control that the grep is live: `grep -c "groupby(" solarwindpy/plotting/agg_plot.py` → ≥ 1)
- [ ] defect 2 removed: `grep -rn "iteritems" solarwindpy/` → no output, exit 1 (positive control: `grep -rc "\.items()" solarwindpy/instabilities/verscharen2016.py` → ≥ 3)
- [ ] defect 3 removed: `conda run -n imap-loaders-20260225 python -m pytest tests/core/test_alfvenic_turbulence.py tests/plotting/labels/test_datetime.py -q --no-header 2>&1 | tail -1` → `0 failed` in the summary, exit 0
- [ ] latent dead path recorded: `gh issue list --repo blalterman/SolarWindPy --search "verscharen2016 test coverage" --state open` → one issue listed, exit 0. The issue body states that `solarwindpy/instabilities/verscharen2016.py` had three `.iteritems()` calls that survived a `pandas>=2.0` floor, that the pandas 2.3.3 suite passes 2181 tests with zero failures, and that those two facts together prove the module has no test coverage. File it before the tag; the fix in AC4 changes the syntax and cannot demonstrate the module runs.
- [ ] `v0.3.1` tag exists on the fix commit: `git describe --tags --exact-match HEAD` → `v0.3.1`, exit 0
- [ ] version resolves from the tag: `conda run -n imap-loaders-20260225 python -c "import solarwindpy; print(solarwindpy.__version__)"` → a string beginning `0.3.1`, exit 0

## Anti-Patterns

- Do NOT add a pandas-version conditional, a compatibility shim, or a
  `try/except TypeError` around the `groupby` call. Both known library fixes
  (dropping `axis=0`, `.iteritems()` → `.items()`) are valid on pandas 2.3.3
  and 3.x simultaneously, so a version branch adds a second code path with no
  behavioral justification.
- Do NOT drop pandas 2 support or raise the `pyproject.toml` pandas floor to
  `>=3`. Four of the seven environments carrying this library run pandas
  2.3.3 (`solarwindpy`, `solarwindpy-2`, `megha-20251210`,
  `nh-ahe-20251205`); raising the floor breaks all four.
- Do NOT install `psutil` or `requests` into `imap-loaders-20260225` and
  count that as progress. Those two missing packages are why
  `tests/plotting/test_performance.py` and `tests/test_issue_titles.py` fail
  to collect in that environment; the failures are environment provisioning,
  not pandas 3, and both files are excluded from every command in this
  dispatch.
- Do NOT tag `v0.3.1` before both suites pass. The tag is what
  `setuptools_scm` reads, so a tag on a failing commit publishes a version
  that names a broken state.
- Do NOT rewrite or force-push `master`. The tag and fixes go on top of
  `2769a19a`.
- Do NOT treat the AC4 grep passing as evidence that
  `solarwindpy/instabilities/verscharen2016.py` works. The grep proves the
  removed API is gone, nothing more. A syntax fix on a module no test
  executes converts a visible defect into an invisible one, which is what
  AC8 exists to prevent.
- Do NOT edit
  `/Users/balterma/observatories/wind/helium-abundance/ahe-ar-indicator-icme`.
  Removing that repo's monkeypatches is separate work in a separate repo.

## Verification

```bash
cd /Users/balterma/observatories/code/SolarWindPy

# both suites, both pandas majors
conda run -n imap-loaders-20260225 python -m pytest -q --no-header \
  --ignore=tests/plotting/test_performance.py --ignore=tests/test_issue_titles.py 2>&1 | tail -1
conda run -n solarwindpy python -m pytest -q --no-header \
  --ignore=tests/plotting/test_performance.py --ignore=tests/test_issue_titles.py 2>&1 | tail -1

# defect sites gone (each paired with a positive control above)
grep -n "groupby(.*axis=" solarwindpy/plotting/agg_plot.py ; echo "exit=$?"
grep -rn "iteritems" solarwindpy/ ; echo "exit=$?"

# version
git describe --tags --exact-match HEAD
conda run -n imap-loaders-20260225 python -c "import solarwindpy; print(solarwindpy.__version__)"
```

## Closing Protocol

After Verification passes, follow the closing protocol in
`~/.claude/rules/handoff-protocol.md` § "Closing Protocol":

1. `/session:empirical-findings /Users/balterma/observatories/code/SolarWindPy/docs/dispatches/dispatch-pandas3-compat-2026-07-23.md`
2. `/session:tombstone-launch /Users/balterma/observatories/code/SolarWindPy/docs/dispatches/launch-pandas3-compat-2026-07-23.md`
   then `/session:purge-tombstoned` on the same path
3. `bash ~/.claude/tools/lint-ai-clean.sh /Users/balterma/observatories/code/SolarWindPy/docs/dispatches/dispatch-pandas3-compat-2026-07-23.md`
