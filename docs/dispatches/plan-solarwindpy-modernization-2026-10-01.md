<!--
Spent-When: MARKED(<self>)
Supersedes: none
-->

# SolarWindPy modernization

## Governance-level purpose

**Surface.** In-situ solar wind measurements and the analysis a heliophysicist performs on
them, together with every claim this repository makes about whether that analysis is correct.

**Parties, and the face each is served by.**

- **The researcher.** Served by a library that installs, runs, and either produces a result or
  says precisely why it stopped. They cite what it computes.
- **The author.** Served by gates that can fail. A green check is the only signal that reaches
  them at the moment of a commit, so a gate that cannot fail removes their ability to know.
- **The assistant.** Served by the test suite and the declared conventions. It composes against
  what those assert, so an assertion that cannot fail is an instruction it cannot follow.

**Seam.** The suite and the gates determine whether a claim holds. The author decides whether
the physics is right, which pins move, and what merges. A passing test shows the code does what
the test says; it never shows the science is correct.

**Layer.** Whether the package does what it claims. Separate from whether what it claims is
scientifically preferable, which stays with the author.

**Held stable.** The MultiIndex column contract (`M` measurement, `C` component, `S` species),
views via `.xs()` rather than copies, SI units internally, and `pyproject.toml` as the single
declaration of what the package supports.

### Non-objectives

- **N1.** The program does not judge whether a physics result is correct. It can detect that a
  calculation is unexercised; it cannot detect that an exercised calculation is wrong.
- **N2.** The program does not change the public API. Modules move behind the façade only where
  a name already resolves to nothing.
- **N3.** The program does not redesign the plotting architecture. It raises coverage on what
  exists and records complexity for a later decision.
- **N4.** Retiring an artifact removes it from the working tree. git holds the bytes.

## Governance-level intent

**Every gate in this repository becomes able to fail, and every claim it guards becomes true.**

The two halves are one act. A gate that cannot fail and a claim that is false are the same
defect seen from opposite sides: the artifact reports health it has not measured. Fixing the
claim while the gate stays inert re-rots on the next commit; fixing the gate while the claim
stays false turns every build red and teaches the author to bypass it. They land together, gate
first within each pair, so the repaired claim has something holding it.

## Governing principle

**Every claim this repository makes is warranted or bounded.**

**Warranted** — it points outside itself to something checkable independently: a physical
identity, a published constant, a cited paper, a canonical source file, a measurement anyone can
re-run.

**Bounded** — it names the observable event after which it stops being the best available claim.

A claim that is neither can only be obeyed, and it will be, long after it stops being true.

How it reads across the repository: a file declaration bounds a file, a derived test is
warranted, a recording file is bounded, a lockfile is warranted by `pyproject.toml`, a version
declaration is warranted by measurement.

**When a claim cannot be warranted there are four routes and no fifth.** Cite a source. Assert a
property rather than a value. Record the behavior in a bounded file as part of a named
migration. Declare an honest gap. A unit that can take none of these has found something worth
reporting rather than something worth writing around.

The principle holds only where something consumes it, so each workstream names the check that
refuses a claim which is neither warranted nor bounded, and every unit brief carries this
section.

## Governing property

A check seen only to pass is indistinguishable from one that cannot fail. Every gate this
program touches is demonstrated failing against a known-bad input before it is trusted to pass,
and the demonstration is recorded where the next reader finds it.

## How to read a workstream statement

Each workstream carries **Purpose**, **Intent**, and **Seam**. Purpose names the standing
property of SolarWindPy that workstream holds, so a decision can be measured against something
larger than the task. Intent names what the workstream makes true. Seam names what a unit
settles on its own and what it returns to the author.

Return to these when the brief does not cover the decision in front of you. A choice that
serves no stated purpose is a choice to decline, and a choice past the seam is one to hand back.

## What a test binds to

A test asserts at a layer. Asserting at the contract layer describes what the module owes its
caller, and the implementation stays free to change beneath it. Asserting at the implementation
layer records how today's code happens to work, and every later refactor that preserves
behavior still breaks the test — so the test converts improvement into cost and the module
ossifies around it.

**The governing question, asked of every test this program writes.** Reimplement the module
correctly from scratch. Does the test still pass? A test that survives binds to the contract. A
test that breaks binds to the implementation, and its failures will report refactors rather than
defects.

**The sharpest signal is where the expected value came from,** and it is readable in one line.

Contract-grade — the test derives its expectation independently of the code under test:

- a physical identity computed from its parts, as `w_s² = (2w_⊥² + w_∥²)/3` is
- a published constant read from `scipy.constants` or `physical_constants`
- an analytic limit: continuity at a hinge, a step's magnitude, a plateau's constancy
- a round trip: transform and invert, assert the identity
- a parameter recovery: generate from known truth, fit, assert recovery within a tolerance
- an external value with its citation in the test

Implementation-grade — the expectation was captured from a run of the code:

- a numeric literal with no derivation and no citation
- `assert_called_once_with`, `call_count`, and call-order assertions, which assert how rather
  than what
- exact equality on formatted output, where formatting is not the contract
- assertions on names beginning with an underscore
- a golden file recorded from output

**Properties over cases.** A case pins one point and says nothing about its neighbours, so
pinning enough points to feel safe is what produces a suite that resists change. A property
asserts over a region — monotonic here, bounded there, symmetric under this exchange,
dimensionally consistent throughout — and one property replaces many cases while constraining
the implementation less. Parametrize over a domain chosen for meaning: `[1, 26, 92]` for
hydrogen, iron, uranium says something a hundred random atomic numbers do not.

**When a value cannot be derived.** Some expectations are neither analytic nor derivable —
instability thresholds fitted in a paper, a photospheric abundance table. Cite the source in the
test with its DOI. A citation turns a literal into a contract with an external referent, which
is a claim a reader can check, rather than a self-referential record of what the code did.

### A captured expectation blocks its own correction

A reader treats a test as a statement of what the code owes. So a test recording what the code
once did will be obeyed as a requirement: someone fixes the accident, the test goes red, and
they conclude they broke something.

**Every test states what to do when it fails.** One line. Absent it, a red test means "fix the
code", and that default is what lets a stale test veto a real improvement.

```python
def test_thermal_speed_moment_identity():
    """w_s² = (2w_⊥² + w_∥²)/3, computed from the components.

    ON FAILURE: the code is wrong.
    """
```

### Recording present behavior

Recording what the code currently does is the right move while restructuring code whose contract
is not yet known, because it reports accidental changes. Three properties keep it from becoming
permanent, and all three come from the file boundary rather than from new machinery.

**It lives in its own file**, separate from tests that state requirements, so it is removable as
a unit and unmistakable for a statement of what the code owes.

**That file carries an ordinary file-level declaration** saying it is spent once superseded. The
existing evaluator, sweep and approval gate handle it; there is no second convention and nothing
new to learn. A unit that finishes its migration within its own worktree never commits the file
at all. A unit handing off commits it, so the next session can see it.

**One file, one fate.** Partial retirement is impossible, so a migration either completes or its
leftovers move somewhere that will complete. It cannot dribble.

### Writing the requirement before the code meets it

As understanding arrives mid-migration, write the derived test immediately and mark it
`@pytest.mark.xfail(strict=True)` with a reason naming what it replaces. Strict mode reports an
unexpected pass as a failure, so the day the code catches up the suite says so on its own.

This matters here specifically because sessions do not share memory. An expectation written down
survives; one held by whoever worked it out does not.

**The two signals chain.** A strict xfail flipping says one behavior is now covered properly.
The recording file's declaration says all of them are and the scaffold can come down. Completing
the derived tests is itself what retires the recording file, so no separate list is maintained.

**The trap, and its check.** A strict xfail that never flips sits green forever, asserting
nothing — a new artifact that cannot fail. So a file may declare it supersedes a recording file
only when it carries no remaining xfails. Counting them is one grep.

### Enforcement

Each check refuses something and each is demonstrable against a known-bad input: every test
carries `ON FAILURE`; a recorded-behavior test outside a declared recording file is a defect; a
file with remaining xfails may not declare supersession.

**The test for the test suite.** Perform a behavior-preserving refactor and count the
breakages. Every test that breaks was binding to the implementation. This is runnable rather
than rhetorical, and it is the acceptance criterion W4 carries.

**Measured baseline.** 89 call-assertion sites across 1616 test definitions
(`grep -rnoE "assert_called|call_count|assert_has_calls" tests/`), concentrated in eight files,
all inside the directories marked for rebuild and none in `tests/core/`, `tests/fitfunctions/`,
`tests/plotting/labels/`, or `tests/drift/`.

## Measured state

Re-derive with the command beside each. Run pytest as bare `pytest` inside the environment;
the `python -m` form prepends the repository root to `sys.path`.

| Fact | Reading | Source |
|---|---|---|
| Suite, pandas 2.3.3 | 2168 passed, 20 skipped, 0 failed | `conda run -n solarwindpy pytest -q` |
| Suite, pandas 3.0.5 | 34 failed, 2077 passed, 41 errors | pandas-3 env, two ignores |
| Collection | 2188, and `pytest` agrees with `python -m pytest` | `pytest -q --collect-only` |
| Coverage | 81.79%, 7956 statements, 1449 missing | `coverage.json` |
| Tests | 70 files, 1611 functions | AST count |
| Docstring coverage | 52.4%, 575 items missing | `scripts/docstring_coverage.py` |
| Sphinx warnings | 83, build exits 0 without `-W` | `sphinx -b html docs/source` |
| flake8 | 160 violations, all under `tests/` | `flake8 solarwindpy/ tests/ --count` |
| Doctests, true | 22 pass, 3 fail, 37 skipped | `pytest --doctest-modules solarwindpy` |
| Doctests, reported | 100.0% success, 0 failed | `scripts/simple_doc_validation/` |

### Why each gate reports success

- **Coverage.** `.claude/hooks/pre-commit-tests.sh:33` fails under a threshold above measured
  coverage, so it never passes. `--no-verify` skips every hook, so the only route to committing
  Python also skips black, flake8, doc8 and the commit-message check. 160 flake8 violations
  stand under `tests/`.
- **Doctests.** `doctest_runner.py:40` loads each file standalone, so every module using a
  relative import raises; the exception is recorded as an error contributing zero to
  `tests_attempted` and zero to `failed_tests`, and the verdict at `:138` is
  `failed_tests == 0`. 33 of 44 files fail to import and the runner reports 100%.
- **Sphinx warnings.** `docs.yml` exports `SPHINXOPTS: -W --keep-going -n`; `docs/Makefile:4`
  assigns `SPHINXOPTS =`, and a make assignment beats the environment, so `-W` does not apply.
- **Markers.** `integration` and `slow` are unregistered and read by nothing, so the live
  ICMECAT catalog downloads on every pull request. `--disable-warnings` absorbs the notice.
- **Pre-commit scope.** black and flake8 match `^(solarwindpy|tests|\.claude)/`, excluding
  `scripts/`, where 6 of 11 black failures live.

## Workstreams

### W1 — Gates

**Purpose.** The author's ability to know the state of their own work. A gate is the only
signal that reaches them at the moment of a commit, and every other workstream reports success
through one. This is the workstream the rest of the program is verified by, which is why it
runs first.

**Intent.** Every gate can fail, and the failure reaches the author.

**Seam.** A unit decides how a gate is wired, what it inspects, and how its failure is worded.
The author decides what threshold a gate enforces, because a threshold encodes what this project
considers acceptable work. A unit that believes a threshold is wrong reports the measurement and
the recommendation rather than setting it.

Replace `scripts/simple_doc_validation/` with `pytest --doctest-modules --doctest-glob='*.rst'`.
Move `SPHINXOPTS` to a make-level default the environment can override. Register the markers in
`[tool.pytest.ini_options]` and gate them in `tests/conftest.py`. Extend pre-commit's file
pattern to `scripts/`. Set the coverage gate to the measured floor so it passes on a clean tree.

**Acceptance criteria**

- [ ] Each gate is demonstrated failing: coverage against a stripped test, doctests against a
      deliberately broken example, Sphinx against an injected bad reference, a marker against an
      unregistered name, black against an unformatted file under `scripts/`. Record each
      demonstration in its commit message.
- [ ] `pre-commit run --all-files` runs every hook with no bypass. *Positive control:* it
      reports the 160 known violations before repair and zero after.
- [ ] Collection stays equal between `pytest` and `python -m pytest`. Both report 2188.

### W2 — pandas 3

**Purpose.** The library runs where researchers run it. Half the environments carrying
SolarWindPy on this machine are already on pandas 3, and a fresh `pip install` resolves pandas 3
today, so the gap between what the package supports and what users have is widening on its own.

**Intent.** One source that runs on pandas 2.3.3 and pandas 3.0.5.

**Seam.** A unit decides how to express a fix so it is valid on both versions. The author
decides whether to drop support for a version, because that decision reaches users and cannot be
inferred from a failing test. A unit that believes a version branch is unavoidable stops and
presents the evidence rather than writing one.

The four known API removals are fixed. What remains is the 34 failures and 41 errors the
pandas-3 suite still reports, worked by reading the next cluster and repeating.

The 41 errors are collection failures from packages missing in the pandas-3 environment rather
than pandas defects; confirm that before treating them as in scope.

**Acceptance criteria**

- [ ] Both suites report 0 failed and 0 errors. *Positive control:* the pandas-3 run reports 34
      failed and 41 errors today, so the check is live.
- [ ] `grep -rn "pandas.__version__\|pd\.__version__" solarwindpy/` returns nothing. *Positive
      control:* `grep -c "import pandas" solarwindpy/core/plasma.py` returns at least 1.

### W3 — Declarations

**Purpose.** What the package promises equals what it delivers. A declaration is the contract a
researcher installs against, and it is the one artifact that reaches every new user before any
code runs. It is written after W2 so the numbers in it are measured rather than guessed.

**Intent.** Every version the repository states is one it has run.

**Seam.** A unit regenerates declarations from the canonical source and carries one value to
every site asserting it. The author decides the floors themselves, because raising a floor
excludes users and lowering one accepts a support burden.

Set `requires-python` to `>=3.12,<4`, the pandas range to what W2 measured, and carry both to
the eleven files asserting a Python version, where three distinct values appear today.
Regenerate the three lockfiles from `pyproject.toml` through `sync-requirements.yml`. Point
Dependabot at `pyproject.toml` so bounds arrive where the generator reads them. Keep
`recipe/meta.yaml` as the single conda recipe. Confirm Read the Docs offers 3.12 on its pinned
image before the floor moves.

**Acceptance criteria**

- [ ] A fast test asserts every declared Python version satisfies `requires-python`. *Positive
      control:* it reports drift on first run, before the sweep.
- [ ] Each lockfile satisfies `pyproject.toml` and the three agree on numpy, pandas, astropy,
      scipy. *Positive control:* they disagree on all four today.
- [ ] A fresh install in a clean environment resolves and imports.

### W4 — Tests

**Purpose.** The evidence both the author and the assistant reason from. Every other workstream
cites the suite to justify a change, so a test that cannot fail silently licenses whatever is
built on it. This workstream is what makes the rest of the program's acceptance criteria mean
anything.

**Intent.** A test that passes means the behavior is right.

**Seam.** A unit decides test structure, fixtures, parametrization, and what to assert about
behavior. The author decides whether a physics assertion is correct — a test can encode a
physical identity, and no test can judge whether the identity is the right one. A unit that
cannot determine the expected physical value reports that rather than asserting whatever the
code currently returns, because an expectation captured from the code is a record of present
behavior presented as a requirement.

Every test written here meets the standard in § "What a test binds to". Two discriminators
apply, and they answer different questions.

**Is the file careful?** Re-derivable per file: tolerance assertions and parametrization mark a
sound file; high mock density and introspection-only assertions mark an unsound one. The two
sets barely overlap, and this is what decides rebuild versus repair.

**Is the test at the right layer?** Asked per test, of sound and unsound files alike: could a
correct reimplementation pass it? A careful test can still bind to the implementation, so a file
that survives the first question is still held to the second.

Rebuild `tests/plotting/` outside `labels/`, `tests/solar_activity/sunspot_number/`, and
`tests/solar_activity/` root — roughly 620 tests guarding the worst-covered modules, including
`hist2d.py` at 47.8% across 492 statements and `orbits.py` at 24.3% behind 34 tests of which 16
assert only that attributes exist.

Keep `tests/core/`, `tests/fitfunctions/`, `tests/plotting/labels/`, and `tests/drift/` —
roughly 860 tests holding every physics assertion in the package, including
`w_s² = (2w_⊥² + w_∥²)/3` checked as an identity against independently computed values. Repairs
there are surgical: rename `TestData` so pytest stops warning, run or delete
`TestIonSpecificsOptions` which currently never executes, remove 231 commented lines, resolve
the 7 permanently skipped tests.

Rebuild `tests/core/test_units_constants.py` outright — 22 lines of `hasattr` guarding the
module every temperature depends on, with no constant's value compared to CODATA.

Give `solarwindpy/instabilities/` its first tests; 209 statements of the most physics-dense code
in the package are named in no test file.

`tests/drift/` is the model to generalize: each test restates an external fact as a locally
evaluable assertion carrying fact, location and remedy.

**Acceptance criteria**

- [ ] Coverage rises on the rebuilt directories, measured per module rather than in aggregate.
- [ ] Every rebuilt file asserts values, and no test asserts only that a name exists. *Positive
      control:* count introspection-only assertions before and after; 210 exist today.
- [ ] A constant's value in `units_constants.py` is compared to CODATA. *Positive control:*
      perturb it in a scratch copy and confirm the test fails.
- [ ] Mock targets are external boundaries. *Positive control:* `test_sidc.py` patches three
      classes defined in the module it tests today; that count reaches zero.
- [ ] **The refactor test.** Apply a behavior-preserving refactor to a rebuilt module — rename a
      private helper, extract a method, reorder independent statements — and the suite stays
      green. *Positive control:* apply a behavior-*changing* edit to the same module, such as
      inverting a comparison, and confirm the suite goes red. A suite that survives both is
      measuring nothing.
- [ ] Every numeric expectation is derived, cited, or inside a declared recording file.
      *Positive control:* grep the rebuilt files for bare numeric literals in assertions and
      confirm each surviving one carries a derivation or a DOI.
- [ ] Every test states what to do when it fails. *Positive control:* `grep -c "ON FAILURE"`
      equals the test count in rebuilt files, and a test added without the line is refused.
- [ ] Recorded-behavior tests exist only inside a file carrying a spent declaration. *Positive
      control:* place one in an ordinary test file, confirm the check reports it, then remove it.
- [ ] No file declares supersession while it still carries a strict xfail. *Positive control:*
      add an xfail to a superseding file, confirm the check refuses, then remove it.

### W5 — Documentation

**Purpose.** The face a researcher meets the library through. A wrong example costs them a
debugging session before they ever reach the science, and it is the one defect class that
reaches someone who has not yet decided to trust the package.

**Intent.** Every documented call runs.

**Seam.** A unit fixes what does not run and regenerates what is derived from source. The
author decides what the library should be described as doing, because a description is a claim
about intent rather than about behavior. A unit that finds documentation describing a capability
the code lacks reports the discrepancy rather than choosing which one is right.

76% of rendered output regenerates from docstrings and is already correct, so the rebuild is
small. Delete the second API tree (`docs/source/api/`, sphinx-apidoc, `add_no_index.py`,
`TEMPLATE_SYSTEM.md`), which produces ~40 of the 83 warnings and 52 unreachable pages, and keep
autosummary as the sole mechanism. Rewrite `usage.rst`, which carries seven verified defects
including three import errors, modeled on `README.rst:19-49` — the one correct example in the
repository. Rewrite `installation.rst`, whose dependency floors sit below the real ones and
whose outage note concerns a version three releases back. Fill `CITATION.rst`, currently the
word `TODO` rendered onto the published landing page beneath a live DOI. Raise docstring
coverage from 52.4%, working the modules under 50%.

Put every documented snippet under doctest, which W1 makes capable of failing.

**Acceptance criteria**

- [ ] Sphinx builds clean under `-W`. *Positive control:* inject a bad cross-reference and
      confirm the build fails.
- [ ] Every snippet in `usage.rst` executes under `--doctest-glob='*.rst'`. *Positive control:*
      three of its imports raise today.
- [ ] Docstring coverage rises, measured by the existing script.

### W6 — Retire

**Purpose.** The working tree is the surface the assistant reads. Whatever is present is read
on every session, so an artifact describing a finished event competes for attention with one
describing live work, and the reader cannot tell them apart from the artifact alone.

**Intent.** What remains in the tree has a stated reason to exist.

**Seam.** A unit proposes a removal, shows the path is recoverable from history, and shows the
suite passes without it. The author approves every removal. A unit that cannot name what ends an
artifact reports it as undecided rather than removing it.

Remove `paper/` and `draft-joss-paper.yml` from the live surface. Remove the nine orphan scripts
including three near-duplicate `analyze_imports*.py` and the archived tarball. Remove the
~112 KB plan-hook subtree whose only root is `gh-plan-create.sh`. Remove five completed one-time
reports totalling 628 lines with no inbound links. Delete the commented-out
`AlfvenicTurbulenceDAmicis` class at `alfvenic_turbulence.py:450-804` and the ~549 lines of
commented code across 30 files. Fix `labels/__init__.py:9`, which exports a name defined
nowhere so `from solarwindpy.plotting.labels import *` raises. Untrack `baseline-coverage.json`,
`.DS_Store`, `pre-commit-config.yaml.old`, and the root migration notes.

**Acceptance criteria**

- [ ] `from solarwindpy.plotting.labels import *` succeeds. *Positive control:* it raises
      `AttributeError` today.
- [ ] Every removed path is recoverable from history, and every surviving file has a stated
      reason to exist.
- [ ] The suite passes unchanged after removal, confirming nothing live was removed.

## Dependency order

```
W1 Gates ─────────────────────────────────────────── must complete first
   │        (a gate that cannot fail verifies nothing downstream)
   ▼
W2 pandas 3 ──────────────────────────────────────── blocks W3
   │        (the measured range is W3's input)
   ▼
W3 Declarations ──────────────────────────────────── blocks nothing
   │
   ├── W4 Tests ──────┐
   ├── W5 Docs ───────┼── independent of one another; disjoint file sets
   └── W6 Retire ─────┘
```

W6 may begin alongside W2 for paths no other workstream touches — `paper/`, the orphan scripts,
the plan-hook subtree. The commented-code deletions wait for W4, since removing lines from a
module being retested invites conflicts.

## Pilot

**What it measures.** Whether this plan's statements change agent behavior. The subject is the
plan, not the four directories. A pilot that produces good tests and teaches nothing about the
plan has failed at its actual job.

**Why four, and why these four.** They span the decisions W4 asks a unit to make, and two of
them are controls.

| Case | Verdict | The question it answers |
|---|---|---|
| `tests/core/test_plasma.py` | keep, repair surgically | Does a unit preserve the best tests in the package rather than improving them away? |
| `tests/solar_activity/sunspot_number/` | rebuild | Does it rebuild without carrying the mocked pattern forward? |
| `tests/plotting/` for `hist2d.py` | rebuild, hardest | Does it reach contract-grade assertions where derivation is hard, or golden-master the output? |
| `tests/plotting/labels/` | keep, untouched | Does it leave a healthy directory alone? |

`labels` is the negative control: 245 tests, zero mocks, coverage earned rather than mocked, and
the correct output is an empty diff. `sunspot_number` is the positive control: 65 mock sites, an
`assert True`, and a mocked read of the file under test, so change is certainly warranted. A
quiet run with only one of them is ambiguous — restraint and paralysis look identical.

`hist2d` is the case that stresses the standard hardest. 492 statements at 47.8% coverage, four
of the package's twelve complexity hot spots, and output that is a rendered figure. Plotting is
where a golden master is easiest to reach for and hardest to justify, so this is where
§ "What a test binds to" either holds or is revealed as unusable.

**Predictions, registered before the run.** Recorded so the result can disconfirm something.

1. `labels` receives an empty diff.
2. `sunspot_number` loses its `pandas.read_csv` patches and its `assert True`.
3. `test_plasma.py` keeps its independently derived coefficients; the diff touches only the
   commented lines, the `pass`-only test, and the skipped block.
4. `hist2d` is where a unit asks rather than decides, because the expected value of a binned
   statistic is derivable and the expected appearance of a figure is not.
5. At least one unit crosses a seam without noticing — most likely by choosing a physical
   expectation itself rather than reporting that it could not derive one.

Prediction 5 is the one worth being wrong about. If no unit crosses a seam, the seam statements
are doing more work than the evidence so far supports.

**Per-case criteria.**

- [ ] `labels`: no files changed. *Read the diff, not the summary.*
- [ ] `sunspot_number`: `grep -c "read_csv" tests/solar_activity/sunspot_number/` falls, and the
      rebuilt tests read the shipped file. No test asserts only `True`.
- [ ] `test_plasma.py`: every `constants.`-derived coefficient survives. *Positive control:*
      `grep -c "constants\." tests/core/test_plasma.py` before and after.
- [ ] `hist2d`: every numeric expectation is derived, cited, or declared characterization. No
      golden file appears.
- [ ] Every unit ran its positive control and reported the result, including units that found
      nothing to change.

**What each failure locates in the plan.**

- An edited `labels` means the keep verdict is not reaching the unit. The fix is in how a unit
  brief carries the per-directory verdict, not in the unit.
- A rebuilt `sunspot_number` that still mocks the file read means § "What a test binds to" is
  stated but not operative at the moment of writing a test.
- A rewritten `test_plasma.py` means the repair-versus-rebuild discriminator is legible to a
  reader and invisible to an executor.
- A golden master in `hist2d` means the standard has no answer for output that is genuinely hard
  to derive, and owes one.
- A unit reporting success without a positive control means the governing property is decoration.

**Mechanics.** One `/batch` run, four units. The file sets are disjoint — 17 tracked paths,
zero shared:

| Unit | Paths |
|---|---|
| plasma | `tests/core/test_plasma.py` |
| sunspot_number | `tests/solar_activity/sunspot_number/` (6 files) |
| hist2d | `tests/plotting/test_hist2d_plotting.py`, `test_hist2d_pandas_compat.py`, `test_histograms.py` |
| labels | `tests/plotting/labels/` (8 files) |

`tests/plotting/test_orbits.py` also touches `Hist2D` and stays outside the pilot, so the
hist2d unit owns exactly three files.

The gates W1 repairs are still inert during the pilot, so measure with bare `pytest` inside the
named environment and read coverage per module rather than trusting a gate.

**Baselines, re-derivable.**

| Measure | Now | Command |
|---|---|---|
| labels tracked files | 8 | `git ls-files tests/plotting/labels \| wc -l` |
| labels mock sites | 0 | `grep -rcE "@patch\|MagicMock\|Mock\(" tests/plotting/labels/` |
| sunspot `read_csv` | 70 | `grep -rc read_csv tests/solar_activity/sunspot_number/` |
| sunspot `assert True` | 1 | `grep -rc "assert True" tests/solar_activity/sunspot_number/` |
| sunspot mock sites | 56 | `grep -rcE "@patch\|MagicMock\|Mock\(\|monkeypatch" tests/solar_activity/sunspot_number/` |
| plasma `constants.`-derived | 19 | `grep -c "constants\." tests/core/test_plasma.py` |
| plasma test definitions | 41 | `grep -c "def test_" tests/core/test_plasma.py` |

The plasma row is the preservation check. Those 19 sites are where the test derives its
expectation from `scipy.constants` rather than from the code, so they are precisely what a
rewrite would destroy. A diff that lowers this number has failed regardless of what else it
improved.

**Two corrections to the unit briefs, found by re-deriving before the run.**

`test_plasma.py:195 test_chk_species_fail` is an `@abstractmethod` whose docstring documents
the template subclasses implement, and seven subclasses implement it at `:2401` through
`:2559`. Its empty body is the design. Unit 1 leaves it alone.

The commented-line count is ambiguous rather than wrong: 538 lines begin with `#`, of which
184 look like commented-out code. Unit 1 gets the criterion — remove commented-out code, keep
prose comments — and measures for itself rather than working to a number.

## Pilot execution

**Units: exactly four, on exactly the paths above.** This overrides the 5-to-30 default, and
the count is not a decomposition target to be widened.

**End-to-end verification.** The suite is the end-to-end check for a test-suite change, run in
both environments. A unit is done when both stay green:

```
conda run -n solarwindpy pytest -q
  -> 2168 passed, 20 skipped, 0 failed          (pandas 2.3.3, mpl 3.10.8)

conda run -n imap-loaders-20260225 pytest -q --no-header \
  --ignore=tests/plotting/test_performance.py --ignore=tests/test_issue_titles.py
  -> 2152 passed, 18 skipped, 0 failed, 0 errors  (pandas 3.0.5, mpl 3.11.1)
```

The 16-test difference is the two files excluded for missing packages in the pandas-3
environment. No browser, server, or CLI path applies; this is a library with no runtime
surface to exercise beyond its own suite.

**Each unit additionally runs its own positive control** and reports the command and output,
including a unit that changed nothing.

**Concurrency observation.** `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` is 3. Four units make the
binding testable: if all four run at once the cap does not reach this execution path, which
decides whether phase 4 runs as one invocation or three.

**Worker brief composition.** Each unit receives, in this order: the governance triple
(Purpose, Intent, Seam), the governing principle with its four routes, the `ON FAILURE`
requirement, the recording-file and strict-xfail sections, its own unit spec verbatim, the
end-to-end recipe above, and the four reporting requirements. Then the closing sequence: run
`code-review` and fix what it surfaces, run both suites, commit, push, open a pull request,
and end with `PR: <url>`.

Every unit stages explicit paths only. A concurrent session works this checkout, and worktree
isolation protects units from each other but not from that session.

**Preconditions, verified.** Tree clean at `706fd8c6`; 18 unit paths with zero overlap; `gh`
authenticated. Pushing and opening pull requests is the execution model this run was invoked
under, so it needs no separate approval; merging still does.

**Disposition.** The pull requests are evidence. Merging any of them is a separate decision, and
a pilot that ends with four discarded branches and a revised plan has succeeded. Revise the plan
from what the run shows, then run phase 1 for real.

### Run record

Launched from `706fd8c6`. Elapsed is wall-clock from worktree creation; the completion
notification carries the authoritative figure.

| # | Unit | Launched | Elapsed | Status | PR |
|---|---|---|---|---|---|
| 1 | plasma — preserve | 01:51:52 | 23m 14s | done | #435 |
| 2 | sunspot_number — rebuild | 01:52:13 | 38m 42s | done | #436 |
| 3 | hist2d — rebuild | 01:52:43 | 8h 32m wall | done | #437 |
| 4 | labels — assess only | 02:00:52 | 5m 10s | done | none — empty diff, as designed |

**Base defect.** `worktree.baseRef` is unset, so worktrees branch from `origin/<default-branch>`.
`origin/master` is 25 commits behind local `master`, none of which were pushed, so units 1, 3
and 4 built on `01e21b34` while unit 2 built on `706fd8c6`. Every discrepancy unit 1 reported
against the brief traces here: the old hook does carry `--cov-fail-under=95`, and `tests/drift/`
does not exist at that commit, which is the whole 2199/5 versus 2168/20 gap.

Unit 4's result survives it: only `test_datetime.py` differs across the range within its scope,
and `solarwindpy/plotting/labels/` is identical at both commits.

**The fix before any further run:** either push local master, or set `worktree.baseRef = head`.

### What the pilot found about the standard

Unit 4 located a hole that the standard cannot close on its own, and it is the run's most
valuable output so far.

**The governing question is necessary but not sufficient.** "Survives a correct reimplementation"
admits an assertion that is too weak to fail at all. `assert "M" in r"\mathrm{M}"` and
`assert "not recognized" in caplog.text or len(caplog.records) > 0` both survive any
reimplementation, correct or broken. The standard grades them as passing and has no category for
them.

**The warranted test does not reach a rendering module.** For a label string such as
`{v}_{{X};{p}}` there is no independent source — no spec, no published convention, no second
implementation. By the letter of the standard every label assertion is an underived literal; by
its spirit each is exactly the contract. The one assertion that escapes is a units check that
agrees independently with `units_constants.py:179`, and that shape is unavailable to the rest.

Unit 1 found a narrower conflict in its own brief: two lines are simultaneously commented-out
code and one of the 19 `constants.` sites, so the cleanup rule and the preservation gate point
opposite ways. Its diagnosis is right — the gate should count live derivation sites, 18, rather
than raw matches, 19.

**There is a fifth route.** Unit 2: "Its four routes cover claims you *cannot* warrant; these
are claims I *can* warrant against code I am not allowed to touch." A defect found in source
outside a unit's scope is warranted and unfixable at once. Strict xfail is the answer, and the
routes list does not name it even though the brief describes the mechanism elsewhere.

**A number without its command is not checkable.** Unit 2 could not reproduce the brief's
counts under any rule it tried, getting 34 and 151 where the brief said 70 and 56, while
matching the 97-test total exactly — so the same tree, a different counting rule. Its objection
is the standard turned back on the plan: every baseline a brief quotes carries the command that
produced it, or it cannot be verified.

**Assertions must fail on a broken implementation, not merely survive a correct one.** Unit 2
wrote a test that grepped the `skiprows` literal out of `sidc.py`, found it was the only thing
catching a 45→46 mutation, and deleted it: 45 and 46 parse identically because a blank line
absorbs the difference, so the test caught a non-defect and would have reported a correct
reimplementation as broken. That is the governing question applied against the plan's own
earlier suggestion.

### Production defects found while rebuilding, both verified

- `solar_activity/base.py:210` sets `self._data_age`; the `age` property at `:154` returns
  `self._age`. Every caller raises `AttributeError`.
- `plot_on_colorbar` scales by `np.round(ssn.max(), -2)`, which is 0 for any window peaking at
  or below SSN 50 and 100 at 51, so a solar-minimum window divides by zero.

### Predictions, scored

1. `labels` empty diff — **held**.
2. `sunspot_number` loses its `read_csv` patches and `assert True` — **held**, 30→0 and 1→0.
3. `test_plasma.py` keeps its derived coefficients — **held**, 19→19.
4. `hist2d` asks rather than decides — pending.
4. `hist2d` asks rather than decides — **held.** Density normalisation on a log axis integrates
   to 38.2 in linear measure and 0.0159 in log measure, 1 under neither. Unit 3 asserted nothing
   and recorded the reasoning, because which measure a density plot should use is a physics call.
5. At least one unit crosses a seam without noticing — **not held, zero of four.** Every unit
   that hit a seam reported it: unit 1 on `lnlambda`'s uncited 29.9, unit 2 on cycle 25's
   placeholder maximum, unit 3 on the density measure, unit 4 on the rendering-module gap. Unit
   3 modified source outside its scope mid-run and reverted it before finishing. This was the
   prediction worth being wrong about; being wrong is evidence the seam statements carry weight.

### Seven defects in the standard, found by execution

1. **The governing question is necessary, not sufficient** (unit 4). An assertion too weak to
   fail survives any reimplementation, correct or broken, and the standard grades it as passing.
2. **The warranted test does not reach a rendering module** (unit 4). A label string has no
   independent source, so by the letter every such assertion is an underived literal.
3. **A fifth route is missing** (units 2 and 3, independently). The four cover claims that
   cannot be warranted; a defect found in code outside a unit's scope is warranted and
   unfixable at once. Strict xfail is the construction, and both units reached it unprompted.
4. **A metric quoted without its command is not checkable** (unit 2). Briefs must carry the
   command that produced every baseline, which is the standard applied to the plan itself.
5. **Properties over cases cannot detect a vacuous fixture** (unit 3). A `set_clim` test was
   contract-grade by every listed criterion and constrained nothing, because count-only data
   makes `clim` and `alim` indistinguishable.
6. **Strict xfail cannot say "broken on this dependency version"** (unit 3).
7. **The preservation gate counted the wrong thing** (unit 1). Raw `constants.` matches, 19,
   rather than live derivation sites, 18, so the cleanup rule and the gate pointed opposite ways.

### Defects found in the package

Verified independently: `solar_activity/base.py:210` sets `_data_age` while the property at
`:154` reads `_age`, so every caller raises; `plot_on_colorbar` divides by
`np.round(ssn.max(), -2)`, which is 0 for any window peaking at or below SSN 50.

Unit 3 reports five more in `hist2d.py`, each recorded as strict xfail: auto-computed bins
silently drop extreme observations (300 in, 298 counted); `limit_color_norm=True` raises when
`axnorm is None`; `plot_edges` shares one kwargs dict so the bottom edge ignores caller
smoothing; `id_data_above_contour` raises on an empty column and is broken under pandas 3.

### Coverage delta

`hist2d.py` 47.8% → 94%, 257 missing → 28. Suite 2199 → 2287 passed at unit 3's base.

### Parked

- **Coulomb logarithm constant.** `Plasma.lnlambda` uses `29.9 - ln(...)`; 31 is the
  alternative. The author holds 29.9 as justified and is locating the citation. No change until
  the source is in hand; the test keeps its current expectation and names the missing citation.
- **`tests/core/test_ions.py:223` docstring format (D205).** Handled by the phase-4 batch
  alongside the other `tests/` lint work.
- **Lowercase `"q"` label.** Also commented as heat flux, alongside `"Q"`. Whether it stays as a
  second key or retires is the author's call.

### Outstanding

All three PRs are based on `origin/master`, 25 commits behind local `master`. Rebasing onto
local master before merge clears both the stale base and the 95%-versus-80% coverage gate that
made unit 3 commit with `--no-verify`.

**The concurrency cap binds.** Launching the fourth unit was refused: "Concurrent subagent
limit reached. You can run 3 subagents at once." `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS=3`
therefore reaches this execution path, which the documentation left ambiguous by scoping the
variable to the Agent tool and excluding workflows.

**Consequence for phase 4.** It stays one invocation of 15–25 units; the cap serializes them
into groups of three on its own. The three-invocation fallback and its two extra approval
rounds are unnecessary.

**Where to resume.** Worktrees live under `.claude/worktrees/agent-<id>/` and persist while
they carry changes. A unit's work is inspectable there whether or not it opened a pull request.

## Batch topology

Two properties of the execution mechanism constrain the design: each unit runs in an isolated
git worktree and lands as a pull request, and a run has no mid-run sequencing. Confirm both
against the current mechanism before a run; the design below holds only while they do.

**One run per phase, author approval between phases**, because the dependency order above
cannot live inside a single run.

| Phase | Run | Units | Concurrency |
|---|---|---|---|
| 1 | W1 gates | 5–6, one per gate | low; units share config files |
| 2 | W2 pandas 3 | 1–3, partitioned by module | low; the fixes interact |
| 3 | W3 declarations | 1 | serial by nature |
| 4 | W4 + W5 + W6 | 15–25, partitioned by directory | high; file sets are disjoint |

Phase 4 is where `/batch` earns its cost. The rebuilt test directories, the documentation
rewrites, and the retirements touch disjoint paths, so they parallelize cleanly.

**Every unit brief carries its workstream's Purpose, Intent, and Seam.** That is what the unit
returns to when it meets a decision the brief does not cover, and what tells it whether to settle
the question or hand it back.

**Partition rule.** Units within a run own disjoint file sets. Two units editing
`pyproject.toml` produce a merge conflict at integration rather than an error at runtime, so
shared-file edits are assigned to exactly one unit or deferred to a serial phase.

**Failure and rollback.**

- A unit's work lives in its worktree and reaches the repository only as a pull request.
  Declining the pull request discards the unit at zero cost to its siblings.
- Worktrees carrying changes persist on disk; empty ones are removed automatically. A failed
  unit is inspectable after the run.
- Rollback for a merged unit is the pull request's revert. Rollback for an unmerged unit is
  closing it.
- A phase that produces more failures than merges stops the program until its cause is named.
- A unit that cannot demonstrate its positive control firing reports that rather than reporting
  success.

**The merge gate is CI and human review.** A pull request earns merge by passing checks that
can fail, which is what W1 supplies and why it runs first.

**Concurrency.** `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` in the `env` block of user settings
caps subagents spawned through the Agent tool; it is documented as not applying to workflows.
Whether it binds to a batch run is unresolved, so the pilot measures it: with the cap at 3 and
four units, count how many run in flight.

If it binds, phase 4 runs as one invocation of 15–25 units. If it does not, phase 4 runs as
three invocations of five to eight units, which caps concurrency by construction and keeps
worktree isolation, at the cost of two extra approval rounds.

**Cost.** Run one unit of phase 4 first and read its pull request before approving the
remainder.

## Verification

- `conda run -n solarwindpy pytest -q` and the pandas-3 environment both report 0 failed,
  0 errors.
- `pytest -q` and `python -m pytest -q` agree.
- `pre-commit run --all-files` passes with no bypass.
- `sphinx -b html docs/source /tmp/out -W --keep-going` exits 0.
- `pytest --doctest-modules --doctest-glob='*.rst'` passes, and a deliberately broken example
  makes it fail.
- A clean environment resolves `pip install -e .` and imports the public API.
- Each gate has a recorded demonstration of failing.

---

## Empirical Findings (2026-10-01 trial run)

Program closeout, run on master at `dfbd9fb2` (all phase-4 PRs merged; #442, a Dependabot
bound, open and out of scope). The plan's `## Governing property` (lower-case) is not the
`## Governing Property` heading the findings convention keys on, so its outcome is stated in
End-state metrics rather than its own subsection.

### End-state metrics

- Suite, `solarwindpy` env (pandas 3.0.x, py3.13): `conda run -n solarwindpy pytest -q` →
  2848 passed, 12 skipped, 0 failed. Plan baseline: 2168 passed.
- Suite, `imap-loaders-20260225` env (pandas 3.0.5, py3.12), `--ignore=tests/plotting/test_performance.py`
  → 1 failed, 2847 passed. The failure is
  `tests/test_public_imports.py::test_every_public_object_is_documented_on_the_api_reference`,
  `ModuleNotFoundError: No module named 'sphinx'`: the env lacks the `docs` extra. Same class
  as the existing `test_performance.py` ignore (package absent from that env), not a pandas
  defect. Plan baseline: 34 failed, 41 errors.
- Python 3.14: 2900 passed, 0 failed in a throwaway py3.14.7 / pandas 3.0.6 / numpy 2.5.3 /
  numba 0.68 env (`17c73c2c`).
- Collection: `pytest -q --collect-only` and `python -m pytest -q --collect-only` both →
  2860 tests collected.
- Coverage: `pytest --cov=solarwindpy` → 94% (7108 statements, 417 missing). Plan baseline
  81.79%. Hook ratchet raised 80 → 92 (`7b7c5116`).
- Docstring coverage: `python scripts/docstring_coverage.py` → 86.5% (1091 items, 147
  missing). Plan baseline 52.4%.
- Sphinx: `SPHINXOPTS='-W --keep-going -n' make html` on a full `git archive HEAD` export →
  `build succeeded`, exit 0. Plan baseline: 83 warnings without `-W`; 2309 once `-n` applied.
- Doctests: `pytest --doctest-modules solarwindpy -q` → 24 passed, 36 skipped, 0 failed
  (plan baseline 22 passed, 3 failed, 37 skipped); `pytest --doctest-glob='*.rst' docs/source -q`
  → 1 passed (`usage.rst` runs; its strict xfail and `docs/source/conftest.py` retired in #463).
- `ON FAILURE` lines: `grep -rho 'ON FAILURE' tests --include='*.py' | wc -l` → 633, against
  1511 `def test_` definitions. 22 test files carry none, concentrated in the kept
  directories (`tests/fitfunctions/`, `tests/plotting/labels/`, `tests/core/`) and
  `tests/solar_activity/icme/`.
- Introspection-only assertions: `grep -rhE '^\s*assert (not )?(hasattr|isinstance|callable)\(' tests --include='*.py' | wc -l`
  → 268 (58 of them `hasattr`). The plan's 210 carries no command, so the two numbers are
  not comparable; the largest counts sit in `tests/test_contracts_class.py` (28),
  `tests/core/test_abundances.py` (23), and `tests/fitfunctions/` (kept directories).
- Governing property ("every gate this program touches is demonstrated failing against a
  known-bad input"): held for the doctest, Sphinx, black-on-`scripts/`, declared-version,
  CODATA, and refactor-test gates, each with a recorded failing run. Not held for the
  coverage gate and the marker gate: no commit records either failing on a known-bad input.

### Acceptance Criteria

| AC | Status | Evidence |
|---|---|---|
| W1: each gate demonstrated failing | PASS (partial) | doctests `93337e07`, Sphinx `ca29eda5`, black on `scripts/` `2ddc52c6`, declared versions `c4c849b1`; coverage and marker gates: DEFERRED, no recorded failing run |
| W1: `pre-commit run --all-files` runs every hook with no bypass | FAIL (scoped) | every hook passes except doc8: 73 findings, all in `plans/tests-audit/artifacts/NUMERICAL_STABILITY_GUIDE_TEMPLATE.rst` (50) and `PHYSICS_GUIDE_TEMPLATE.rst` (23), inside the `plans/` records held for a separate author decision; one is a malformed table, not mechanical |
| W1: collection equal under `pytest` and `python -m pytest` | PASS | 2860 = 2860 |
| W2: both suites 0 failed, 0 errors | PASS (with env note) | 2848/0 failed; pandas-3 env 1 failed from a missing `sphinx` package, see metrics |
| W2: no pandas version branches | PASS | `grep -rn "pandas.__version__\|pd\.__version__" solarwindpy/ \| wc -l` → 0; positive control `grep -c "import pandas" solarwindpy/core/plasma.py` ≥ 1 |
| W3: fast test asserts declared Python versions | PASS | `tests/test_declared_versions.py`, demonstrated failing in `c4c849b1` and `a66de393` |
| W3: lockfiles agree on numpy, pandas, astropy, scipy | SUPERSEDED | lockfiles retired; `pyproject.toml` is the only declaration (`5447dc8e`) |
| W3: fresh install resolves and imports | PASS | wheel `solarwindpy-0.3.1.dev346+gdfbd9fb2` into a fresh py3.12.13 venv resolved pandas 3.0.6, numpy 2.5.3; `import solarwindpy`, `solarwindpy.core.plasma.Plasma`, `from solarwindpy.plotting.labels import *`, fitfunctions, instabilities, solar_activity import from site-packages |
| W4: coverage rises on rebuilt directories | PASS | total 81.79% → 94%; `hist2d.py` 47.8% → 94% (pilot) |
| W4: no test asserts only that a name exists | DEFERRED | 268 introspection-only asserts by the command above, mostly in kept directories; to the test-quality program |
| W4: a units constant compared to CODATA | PASS | positive control: alpha/proton mass ratio in `units_constants.py:51` × 1.001 → `tests/core/test_units_constants.py` 1 failed, 98 passed; restored → 99 passed |
| W4: mock targets are external boundaries | PASS (partial) | `test_sidc.py` patches of module-defined classes 3 → 1; the remaining `monkeypatch.setattr(SIDCLoader, "download_data", refuse)` at `:90` blocks the network. The file's docstring at `:12` ("Nothing here patches a name defined in `sidc.py`") is inaccurate |
| W4: refactor test | PASS | rename `_prep_agg_for_plot` → `_prepare_agg_for_plot` (3 sites) in `hist2d.py`: `pytest tests/plotting` 892 passed; invert `x0 <= x` at `hist2d.py:619`: 1 failed (`TestPlotEdges::test_limits_drop_vertices_outside_them`), 891 passed; file restored, empty diff after each |
| W4: every numeric expectation derived, cited, or recorded | DEFERRED | not audited suite-wide; to the test-quality program |
| W4: every test states ON FAILURE | DEFERRED | 633 of 1511; to the test-quality program |
| W4: recorded-behavior and xfail-supersession checks | DEFERRED | no automated check exists |
| W5: Sphinx clean under `-W` | PASS | exit 0 with `-W --keep-going -n` |
| W5: `usage.rst` snippets execute | PASS | `--doctest-glob='*.rst' docs/source` → 1 passed |
| W5: docstring coverage rises | PASS | 52.4% → 86.5% |
| W6: `from solarwindpy.plotting.labels import *` | PASS | succeeds in the clean venv |
| W6: removed paths recoverable, suite passes | PASS | removals are git commits; suite 2848 passed |
| Release gate (added after the plan) | see Release-gate dry run | `publish.yml` `platform-matrix` |

### Deviations from plan

- Dependency model changed by author decision: `pyproject.toml` is the single declaration,
  pandas `>=3,<4`, Python `>=3.12,<4` with 3.14 measured and declared, lockfiles and the
  in-repo conda recipe retired, formatter versions only in `.pre-commit-config.yaml`.
- The multi-platform test matrix (Linux and macOS × 3.12/3.13/3.14) runs as a release gate
  in `publish.yml`, not on pushes (`72fc8339`).
- Retired beyond the plan's W6 list by author decision: the `swp` and `propositions` slash
  commands and their ast-grep rules, the GitHub Issues planning workflow,
  `git-workflow-validator.sh` and its hooks, the `plan-*.yml` issue templates and `plan/**`
  CI triggers (`0186a03c`, `523f66b0`, `93f53f7f`, `f8dc544c`).
- The `lnlambda` 29.9 citation and the lowercase `"q"` label stay parked.
- Phase 4 ran as 25 PRs (#445 to #469) plus follow-on rows merged directly on master.

### Commits

The program spans `706fd8c6..7b7c5116` (`git log --oneline 706fd8c6..7b7c5116`, 300
commits). Phase markers:

- `93337e07`, `ca29eda5`, `2ddc52c6` W1 gates
- `c4c849b1`, `6dddeb70`, `5447dc8e`, `a66de393`, `17c73c2c` W3 declarations
- `3d0f83fd`, `ec080c75` single formatter version
- PRs #445 to #469 phase 4 (merge commits `9f9dd89a` to `c3f2ce92`)
- `0186a03c`, `523f66b0`, `93f53f7f`, `f8dc544c` retirements
- `72fc8339` release gate
- `7b7c5116` coverage ratchet 92%

### Release-gate dry run

`gh workflow run publish.yml --ref master -f target=testpypi -f dry_run=true` → run
36821465780, conclusion success. `platform-matrix` passed in all six cells (ubuntu-latest
and macos-latest × Python 3.12, 3.13, 3.14). `build-and-publish` ran the full suite, built
the package and passed `twine check`; Publish to TestPyPI, Publish to PyPI, and Create GitHub
Release were skipped, and `update-conda-feedstock` was skipped, as `dry_run=true` and a
manual trigger require.

### Open items for the author

The plan stays live, without a completion marker, until these close: its governing
property did not hold for every gate it touched, so the program is not recorded as served.


- doc8 findings in `plans/tests-audit/artifacts/` keep `pre-commit run --all-files` from
  passing; they resolve with the separate `plans/` records decision.
- Coverage-gate and marker-gate failing demonstrations are not recorded.
- `tests/solar_activity/sunspot_number/test_sidc.py:12` claims no patch of a name from
  `sidc.py`; `:90` patches `SIDCLoader.download_data`.
- W4 suite-wide checks (introspection-only assertions, numeric expectations, `ON FAILURE`
  coverage) go to the next program, test and documentation quality.
