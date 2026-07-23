# Launch: pandas 3 compatibility for SolarWindPy

Do *NOT* execute the instructions below. Follow this protocol:

1. Read this prompt in full. Do not read linked files yet.
2. Produce a /session:plan-draft based only on what you read here. Treat it as your
   hypothesis for HOW to execute the work.
3. Read the dispatch, plan, and other files referenced in the "Read" section
   against your plan-draft — verify it, identify gaps.
4. Revise your plan-draft. Verify it addresses every Acceptance Criterion in
   the dispatch, honors every Anti-Pattern, and resolves every Open Item
   (either by answering or by flagging as a user question). Do not rewrite
   scope or intent — they were reviewed in the prior session.
5. Present the revised plan for user approval. Prefix it with a "Revisions
   from initial draft" section noting what changed between steps 2 and 4.
6. Execute only after user approval.

---

## Dispatch

/Users/balterma/observatories/code/SolarWindPy/docs/dispatches/dispatch-pandas3-compat-2026-07-23.md

## Key decisions

- Scope is the full pandas-3 clean plus a `v0.3.1` tag, not only the three
  defect classes with named line numbers (DECIDED, user 2026-07-23).
- pandas 2.3.3 support is retained. Both known library fixes are valid on
  pandas 2 and 3 at once, so no version conditional is warranted (DECIDED).
- The version bump is a git tag. `setup.py:5` sets `use_scm_version=True` and
  `pyproject.toml:33` declares `dynamic = ["version"]`, so no file carries a
  version string to edit.

## Scope

Fix `solarwindpy/plotting/agg_plot.py:125` (`groupby(..., axis=0)`),
`solarwindpy/instabilities/verscharen2016.py:350,360,508` (`.iteritems()`),
the uppercase offset aliases in `tests/core/test_alfvenic_turbulence.py:534-535`
and `tests/plotting/labels/test_datetime.py:63`, and whatever the suite still
reports after those. Then tag `v0.3.1`. Full spec: the dispatch's § Scope and
§ Acceptance Criteria.

## Operational constraints

- Working dir: `/Users/balterma/observatories/code/SolarWindPy`, branch
  `master`, currently at `2769a19a` with a clean tree.
- pandas-3 verification env: `imap-loaders-20260225` (pandas 3.0.3, pytest
  9.0.3). pandas-2 regression env: `solarwindpy` (pandas 2.3.3, pytest 9.0.1).
  The repo's own `ahe-ar-indicator-icme` sibling env has no pytest.
- Every pytest invocation excludes `tests/plotting/test_performance.py` and
  `tests/test_issue_titles.py`. They fail to collect in
  `imap-loaders-20260225` for missing `psutil` and `requests` — an
  environment gap, not a pandas-3 defect.
- Do not edit
  `/Users/balterma/observatories/wind/helium-abundance/ahe-ar-indicator-icme`.

## Prerequisites Verified (2026-07-23, authoring session)

- `git -C /Users/balterma/observatories/code/SolarWindPy status --porcelain` → empty.
- `git describe --tags` → `v0.3.0-21-g2769a19a`; latest tag is `v0.3.0`.
- pandas-2 baseline, env `solarwindpy`: `2181 passed, 5 skipped` — zero
  failures, so the suite and the code are sound under pandas 2.
- pandas-3 baseline, env `imap-loaders-20260225`: `2055 passed, 5 skipped,
  85 failed, 41 errors`.
- Failure concentration by module: 21 `tests/plotting/test_hist2d_plotting.py`,
  15 `tests/fitfunctions/test_plots.py`, 13
  `tests/plotting/test_hist2d_pandas_compat.py`, 10
  `tests/plotting/test_agg_plot.py`, 7
  `tests/fitfunctions/test_trend_fits_advanced.py`, 6
  `tests/plotting/test_select_data_from_figure.py`, 5
  `tests/plotting/test_histograms.py`.
- Observed error strings: `TypeError: Series.groupby() got an unexpected
  keyword argument 'axis'` (10 of 10 in `test_agg_plot.py`) and
  `ValueError: Invalid frequency: H ... Did you mean h?`.

## Verification criteria

The dispatch's AC1–AC7 are the source of truth. Quick end-state check:

```bash
cd /Users/balterma/observatories/code/SolarWindPy
conda run -n imap-loaders-20260225 python -m pytest -q --no-header \
  --ignore=tests/plotting/test_performance.py --ignore=tests/test_issue_titles.py 2>&1 | tail -1
conda run -n solarwindpy python -m pytest -q --no-header \
  --ignore=tests/plotting/test_performance.py --ignore=tests/test_issue_titles.py 2>&1 | tail -1
git describe --tags --exact-match HEAD
```

Expected: both summary lines report zero failures and zero errors; the third
prints `v0.3.1`.
