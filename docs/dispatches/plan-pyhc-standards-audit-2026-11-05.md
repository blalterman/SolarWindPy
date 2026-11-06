<!--
Spent-When: MARKED(<self>)
Supersedes: none
-->

# Plan: Independent PyHC standards audit of SolarWindPy (Bronze, PHEP 4)

## Context

The author wants an evidence-only audit of SolarWindPy against the 15 PyHC standards, the six review
categories, PHEP 3, and PHEP 4 Bronze. The audit produces five deliverables for a registry submission.
Done means every claim cites a fetched source, a `file:line`, or a check run with its command, env,
and exit code. Any check that could not run is recorded as a limitation, never as pass or fail.
No production repo file, dependency, config, or git history changes. The audit files are not committed;
the prompt's "do not commit" overrides the CLAUDE.md commit cadence for these files.

## Facts established during planning (read-only, via `gh api`)

Sources read in full: standards.md, PHEP 3, PHEP 4, grading guidelines, both copies of
"adding a project", package_review_template.md, taxonomy.yml, projects*.yml, project_cards.html,
project_title.html, PHEP 3 schedule.md, PHEP 4 announcement post, pyhc-actions README.

- **PHEP 4 is Final but not implemented.** The 2026-06-02 announcement says re-designation has not
  launched, the TSC is not stood up, and "No action is needed from package maintainers right now".
  `projects.html` still renders Core, Other, and Unevaluated. No tier field exists in any `_data/*.yml`.
  The working path today is a legacy `projects.yml` entry plus a self-evaluation. "Requested tier:
  Bronze" can only appear in the PR text.
- **Bronze compliance row is ambiguous.** "Packages must comply with all applicable standards (as
  defined in standards-track PHEPs)." The only Final standards-track PHEP is PHEP 3, which uses
  "should". Two readings follow:
  - Narrow: self-evaluation plus PHEP compliance suffices.
  - Broad: every "must" in standards.md applies.

  Both readings are reported. The audit does not pick one silently.
- **Grading guidelines** say no project is currently rejected for any grade. Grades are assigned from
  each category's own definitions, not from "a must failed, so the grade is red".
- **Registry schema conflicts.** These are flagged in deliverable D, not resolved:
  - All 60 live entries use `python3` for the sixth grade.
  - The live doc (`_pages/docs/adding_to_pyhc_project_list.md`) lists `hssi` and a "Python 3
    standard" grade.
  - The repo copy (`_pyhc_projects/`) lists five grades and no `hssi`.
  - The guidelines name the category PHEP 3.
  - Open PR #398 adds both `python3` and `PHEP3`.
  - `project_cards.html` renders only five grades, and neither key.
  - `hssi` is optional and is left empty when no HSSI record is published.
- **Additional review step.** The Tech Lead compares the self-evaluation against an AI "PyHC
  Standards Evaluator" report. That step is in the live doc and absent from PHEP 4.
- **User's fork** `blalterman/heliophysicsPy.github.io` `master` is level with upstream `main`
  (ahead 0, behind 0) and holds no SolarWindPy entry. SolarWindPy is in no registry file.
- **PHEP 3 schedule (Q4 2026).**
  - Python 3.12 may be dropped this quarter.
  - pandas 3.0, SciPy 1.17, and NumPy 2.4 adoption was due by mid-2026.
  - matplotlib 3.11 and NumPy 2.5 adoption is due by Dec 2026.
- **Repo signals to verify, not conclusions.**
  - `scipy>=1.16` and `pandas>=3,<4` may exclude 1.15.x and 2.3.x, both still inside the 24-month window.
  - Upper bounds `numpy<3` and `pandas<4` are present.
  - `git grep` finds no code of conduct or Contributor Covenant text.
  - No Windows runner appears in any workflow. The OS/Python matrix (ubuntu and macos, 3.12 to 3.14)
    exists only in `publish.yml`.
  - Local tags stop at `v0.4.0` although v0.4.1 release notes are merged.
  - HEAD tracks no notebooks or images. The pack is 56 MiB.

## Execution

All runs happen in a clean clone, so the working tree stays untouched:
`git clone --local . $SCRATCH/swp && git -C $SCRATCH/swp fetch --tags origin`.
`$SCRATCH` is `/private/tmp/claude-501/-Users-blalterman-observatories-code-SolarWindPy/db622101-821c-40e6-8fa1-2493df730407/scratchpad`.
Every command, env, version, exit code, and the key output lines are logged to
`$SCRATCH/evidence.log`. That log feeds the evidence columns.

1. **Env record.** `conda run -n solarwindpy python -c "import sys, numpy, scipy, pandas, matplotlib; ..."`,
   plus `uv --version` and `git rev-parse HEAD`.
2. **Packaging (#1, #3).**
   - `python -m build --outdir $SCRATCH/dist`, run in the clone.
   - `twine check`, and listing of the sdist and wheel contents.
   - `pip index versions solarwindpy` for PyPI, and a web-fetch of the conda-forge feedstock page.
   - Compare against git tags and CHANGELOG. Release cadence comes from tag dates.
3. **Clean install (#1, #11).** Fresh `uv venv` for each of Python 3.12, 3.13, and 3.14. Install the
   built wheel, `import solarwindpy`, and print the resolved versions.
4. **Tests and coverage (#9).**
   - `pytest -q --cov=solarwindpy --cov-report=term` in the clone, under the solarwindpy env.
   - Read the coverage floor from `.claude/hooks/pre-commit-tests.sh`.
   - Classify the unit and integration tests by markers and directories.
5. **Lint and static analysis (#7).** `pre-commit run ruff-check --all-files` and
   `pre-commit run ruff-format --all-files`, both in the clone, plus `PYTHONPATH=src lint-imports`.
   Read the ignore list in `pyproject.toml` as evidence of which PEP 8 and docstring rules are waived.
6. **Docs (#8).**
   - `sphinx-build -b html` and `-b coverage` in the clone.
   - Docstring sampling with a stdlib `ast` script over `src/solarwindpy`. It counts public objects
     with docstrings and with Parameters, Returns, and Examples sections.
   - Check that Read the Docs is live with a web-fetch of solarwindpy.readthedocs.io.
   - Inventory the guides, tutorials, and developer docs under `docs/source`.
7. **PHEP 3 (#11).**
   - `pip install git+https://github.com/heliophysicsPy/pyhc-actions.git@v1.2.0` into a scratch venv.
   - `phep3-check pyproject.toml` and `pyhc-env-compat-check pyproject.toml`.
   - Cross-check the floors against the site's `schedule.md`.
   - Actual-compatibility probes with uv:
     - Resolve the minimum in-window set (`scipy==1.15.*`, `pandas==2.3.*`) and report whether it is
       excluded by metadata.
     - Resolve the newest set (NumPy 2.4 and 2.5, matplotlib 3.11) with numba and `astropy>=8`.
       Report any resolver conflict.
     - Run the suite at the newest resolvable set if time allows.
   - Excluded combinations and untested platforms are recorded as unverified, not incompatible.
8. **OS support (#4).** Read the workflow matrices and `gh run list` results for publish, CI, and
   docs. No Windows CI means Windows is unverified.
9. **Community (#2, #12, #13, #15).**
   - `gh api repos/blalterman/SolarWindPy/community/profile` and a check for a `blalterman/.github`
     default CoC.
   - Read `CONTRIBUTING.md` in full for #13's "clearly explain when a contribution is not accepted".
   - Branch protection via `gh api`, to test whether tests run before merge.
   - #12 duplication: compare scope with listed PyHC packages (PlasmaPy, pyspedas, etc.) from
     `projects.yml` descriptions and the README. The audit reports overlap honestly.
10. **Binaries (#14).** `git ls-files` checks for tracked artifacts (`.coverage`, egg-info,
    `__pycache__`, notebooks). List the largest historical blobs with
    `git rev-list --objects --all | git cat-file --batch-check`.
11. **License (#5).** Read LICENSE, the classifiers, and the attribution comments for copied external
    code. The CLAUDE.md convention requires those comments.
12. **HSSI and registry metadata.** Web-fetch `hssi.hsdcloud.org/software/solarwindpy/`. Pick keywords
    only from `taxonomy.yml`, and add mission keywords only where loader code supports them.
    `contact` comes from `pyproject.toml` authors and is flagged for author confirmation. The session
    email is never used.

**Independence.** Do not run the PyHC Standards Evaluator or read its `reports/`. Skip any prior PyHC
write-ups found under `.claude/` or `docs/dispatches/`. Grades are assigned only after steps 1 to 12.

## Deliverables (in `$SCRATCH/pyhc_audit/`, the author's choice; temporary, so the final reply gives the absolute paths and a reminder to copy them out)

- `pyhc_standards_audit.md`: a 15-row matrix (requirement verbatim, must or should, status, evidence
  with `file:line` and links, deficiency, recommendation). A six-category table follows (grade,
  evidence, remaining issues, confidence). Last comes a source-discrepancies section covering PHEP 4
  versus the live procedure, the schema keys, and the five versus six grades.
- `pyhc_bronze_readiness.md`: executive summary and eligibility under both readings of the compliance
  row, the six grades, mandatory gaps, unverified items, blockers, and next steps. Facts, judgments,
  and uncertainties are labeled.
- `pyhc_remediation_plan.md`: P0, P1, and P2 items, each with requirement, evidence, change, scope,
  and verification. Candidates include a CoC file, the PHEP 3 floors, a documented dependency policy,
  Windows CI, and test-before-merge. Final placement depends on the evidence.
- `solarwindpy_pyhc_entry.yml`: follows the live `projects.yml` keys (`python3` for the PHEP 3
  grade). Unresolved fields are marked with YAML comments, including the `PHEP3` key ambiguity, the
  absent tier field, `hssi`, `contact`, and `logo`.
- `pyhc_submission_pr.md`: verified scope, requested tier (Bronze, in text only, with the reason),
  six grades, evidence links, below-Good justifications, and plans.

## Verification

- Every Status and Grade cell traces to an `evidence.log` entry or a quoted source.
- Grep the deliverables for "passed" and "pass"; each hit must map to an executed command with exit 0.
- Validate the YAML with `python -c "import yaml; yaml.safe_load(open(...))"`. Diff its keys against
  the live `projects.yml` key set.
- Confirm `git status` in the production repo is unchanged.
- Advisor review before declaring done.

## Pending housekeeping

Plan mode blocks the two `prompt-outcome.sh --log` calls the prompt hooks requested. Both run first
after approval.

---

## Empirical Findings (2026-11-05 trial run)

### End-state metrics

- Deliverables: 5 of 5 written, plus `evidence_log.md`, in the session scratchpad `pyhc_audit/` and synced to `~/Documents/Obsidian-Vault/solarwindpy/pyhc-submission/`.
- Bronze determination: eligible under both readings of PHEP 4 at `a0fbb5b8` (planning expected the broad reading to fail on #12 and #13 before remediation).
- Grades submitted: Community, Documentation, Testing, Software Maturity, License Good; PHEP 3 Partially met (three documented floor deviations).

### Acceptance Criteria

| AC | Status | Evidence |
|---|---|---|
| Every Status and Grade cell traces to evidence | PASS | `evidence_log.md` entries E1 to E83 cited from each table row in `pyhc_standards_audit.md` and `pyhc_bronze_readiness.md` |
| "pass" claims map to executed checks | PASS | CI run on `a0fbb5b8`: ci-summary, test-windows, phep3, minimum-versions, build, docs all `pass` (`gh pr checks` / `gh run list` output in session) |
| YAML entry validates and matches live keys | PASS | `yaml.safe_load` returns a list; PyHC PR #399 `check_projects` pass |
| Production repo unchanged by the audit itself | PASS | Audit files lived only in the scratchpad; repo changes came later as separately authorized remediation commits |
| Advisor review before done | PASS | advisor calls before deliverables and before submission |

### Deviations from plan

- The plan scoped a read-only audit. The author then authorized remediation in the same session: code of conduct, contribution rejection criteria, citation page, branding, Windows CI, PHEP 3 policy and CI checks, dependency floors, clean-room rewrites of the legend and SciPy-derived fitting code, `conda_config.py` deletion, and release 0.5.1. Each landed as its own commit.
- The registry entry was submitted (PyHC PR #399 from `blalterman/heliophysicsPy.github.io` branch `add-solarwindpy`), beyond the plan's draft-only deliverable, on the author's go.
- Remediation items P1-4 (matplotlib floor) declined until 2026-12-14, P2-1 (branch protection) deferred to the author, P2-6 (upper bounds) accepted as-is.

### Commits

- `c2754236` docs: adopt the Contributor Covenant 2.1 code of conduct
- `93fa3b35` docs(contributing): state when a contribution is not accepted
- `a6506fff` docs: add a How to cite section and docs page
- `ddb29caa` docs: adopt the approved SolarWindPy branding
- `6db44c73` build: declare the license as SPDX and clear the packaging warnings
- `aa8a6864` docs(fitfunctions): record the source, license, and changes of adapted SciPy and matplotlib code
- `bca44268` docs: add a Related packages page
- `74123b14` refactor(instabilities): reimplement the table legend from a spec
- `30595619` build(deps): raise dependency floors to versions that install together and pass the suite
- `1e6cfd0d` ci: check the PHEP 3 window and test the minimum dependency versions
- `1f79b503` docs(contributing): state the PHEP 3 dependency policy and its deviations
- `071f6fe3` chore(scripts): delete the unused conda_config.py
- `b0a286b4` test(fitfunctions): guard that fitting modules import only public SciPy names
- `66f42262` refactor(fitfunctions): fit with public SciPy API only
- `ffce0fe4` Merge pull request #536 from blalterman/ci/windows-on-code-prs
- `c848ba90` build(deps): raise numexpr and bottleneck to pandas 3's minimums
- `a0fbb5b8` test(fitfunctions): stop pinning where the HingeMax caller-start fit ends

## Spent-Mark: executed, findings recorded
