<!--
Spent-When: PERMANENT(the repository stops maintaining a test suite)
Supersedes: none
-->
# SolarWindPy Test Standard

## Purpose and intent

**Purpose.** The test suite is the evidence the author and every agent reason from. A change
is justified by pointing at tests, so a test that cannot fail licenses whatever is built on it.

**Intent.** A passing test means the behavior is right. A failing test either means the
behavior is wrong or says, in its own docstring, what else it means.

Every test does two things:

1. **Passes on a correct rewrite.** It asserts what SolarWindPy promises its users (public
   functions, classes and properties, the `M`/`C`/`S` column layout, physics, raised errors,
   module layering), never how today's code happens to get there.
2. **Fails on a broken one.** Show it: break the code by hand (invert a comparison, change a
   coefficient, swap two behaviors) and watch the test go red, then restore the code.

**Seam.** An agent decides test structure, inputs, and what behavior to assert. The author
decides physics and wording. An agent that cannot derive or cite an expected physical value,
or that needs the exact wording of a plot label, stops and asks the author.

When a case is not covered here, choose what makes both properties above demonstrable.

## What a test asserts

Assert through the public API: names without a leading underscore, and `solarwindpy.__all__`.
The expected value comes from outside the code under test, and its source sits next to it:

| Source | Example in this repo |
|---|---|
| Input chosen so the answer is known | hist2d `KNOWN_COUNTS`, a non-square grid so a transpose fails |
| Published value, cited | a constant compared to CODATA or IAU, with DOI |
| Hand-computed case | 5 cm⁻³ protons at 400 km/s carry ½ρv³ = 267.6 µW m⁻² |
| Identity that must hold | w² = (2w⊥² + w∥²)/3; histogram counts sum to N |
| Round trip or recovery | fit data generated from known parameters, recover them |

When a test re-derives a formula, add one hand-computed case as well, so that a formula wrong
in both places still fails. A value copied from a previous run of our own code is not a source.

Errors are part of the contract: `pytest.raises(ExpectedError, match="...")`.

Plots: use the Agg backend and assert the data handed to matplotlib (mesh values, cell
coordinates, line vertices). Close figures with `plt.close("all")`.

**Show it:** for each expected value, a reader can name its source from the line it is on.

## Inputs and fixtures

- Build real SolarWindPy objects from inputs you chose: round numbers, hand-built grids,
  distinctive non-default parameter values.
- Randomness comes from `np.random.default_rng(<seed>)`, and only when a hand-built input
  cannot exercise the behavior.
- A fixture that exists to tell two behaviors apart ships a test proving it does, whose
  docstring says ON FAILURE: fix the fixture. Example: `test_clim_and_alim_are_different_filters`.
- A fixture that mutates state is function-scoped. Tests leave global state as they found it:
  `sys.modules` and `sys.path` unchanged.

## Fakes

Fake only a genuine external boundary: the network, the clock, the filesystem or home
directory. Prefer a real local file (`tmp_path`, or `monkeypatch.setattr` on a URL constant)
to replacing a library function. Run matplotlib, pandas, numpy, scipy and SolarWindPy's own
classes for real.

Show that a parameter takes effect by showing that changing it changes the output in the way
the test predicts, computed independently (for example, smoothing checked against
`scipy.signal.savgol_filter` with the caller's window).

**Show it:** every `patch` or `monkeypatch` target in the file is on the boundary list above.

## Tolerances

Every tolerance carries a one-line reason next to it.

| Case | Tolerance |
|---|---|
| Exact SI constants and exact identities | `pytest.approx(x, rel=1e-12, abs=0)` |
| A published value the package stores as printed | exact comparison |
| A value the package computes and a source prints to d decimal places | half the last printed digit: `abs = 0.5 × 10^-d`, `rel=0` |
| Noise-free fits | `rel=1e-6`: far above optimizer convergence, far below any real bug |
| Noisy fits | fixed seed, and each parameter within 4 error bars |

The half-digit rule holds on linear and logarithmic scales alike: a source that prints
log10 values to d decimal places is compared in log10 with `abs = 0.5 × 10^-d`.

Set `abs=0` whenever values are small. `pytest.approx` otherwise allows an absolute margin of
1e-12, which accepts any wrong value of order 1e-34.

The fit functions wrap scipy; scipy owns fit accuracy. Low-noise recovery tests check that the
wrappers pass data, weights and parameters through correctly. Noisy tests use a fixed seed so
they never flicker, and 4 error bars so they pass for almost any seed (a joint false-alarm rate
near 1 in 4000 for four parameters), not only a lucky one.

**Show it:** against the correct code the test passes; against a value shifted by a physically
meaningful amount, it fails.

## Defects found while testing

- **Inside the files you own:** fix the library, with a test that fails before the fix and
  passes after. Record both runs in the commit message.
- **Outside the files you own:** write the correct-behavior test and mark it

  ```python
  @pytest.mark.xfail(strict=True, raises=SomeError,
                     reason="<defect and location>; <expected message>; "
                            "remove this marker when <retiring fix> lands")
  ```

  `strict=True` turns an unexpected pass into a failure, so the day the fix lands the suite says
  so. `raises=` narrows the marker by exception type. `pytest.mark.xfail` ignores `match=`, so
  record the expected message in `reason`. When the test raises the failure itself, raise a
  dedicated `AssertionError` subclass so `raises=` is exact.

**Show it, in three runs:** it xfails as committed; with the fix applied transiently, it fails
as XPASS(strict); with an unrelated `assert False` injected, it is reported FAILED rather than
xfailed. Revert both edits.

A test never weakens an assertion to match a defect, and never asserts a private attribute, a
call count, or `hasattr` in place of the public value.

## Docstrings and names

A test name completes "it is true that ...": `test_hbar_is_h_over_two_pi`.

Every new or rebuilt test's docstring says what it asserts and ends with one `ON FAILURE:` line:

- `the code is wrong.`
- `the code is wrong, unless the author rejects <identity or source>.`
- `the fixture no longer separates <A> from <B>; fix the fixture.`
- `nothing is wrong with the package; <environment condition>.`
- `(unexpected pass) <fix> has landed; drop the xfail marker.`
- `external fact drifted; update <location>.`

**Show it:** `grep -c "ON FAILURE"` over a rebuilt file equals its `def test_` count.

## Structure and layering

Layering is a contract checked by import-linter (`lint-imports`), declared in
`pyproject.toml`:

- `core/` and `tools/` import nothing above them.
- `fitfunctions/`, `instabilities/` and `solar_activity/` may import `plotting/`.

The public import paths are one plain parametrized test that imports each promised name.

**Show it:** add a forbidden import (for example, `plotting` from `core`), watch
`lint-imports` fail, then revert.

## Running and committing

Run the suite in the project environment: `conda run -n solarwindpy pytest -q`. Commit with
plain `git commit`: the pre-commit hooks run the suite in the solarwindpy environment
themselves, through `.claude/hooks/project-env.sh`, whatever shell the commit starts from.
Stage explicit paths.

## Checklist for writing or reviewing a test

1. It uses only public names.
2. Every fake is on the network, clock, or file boundary.
3. Each expected value's source is on its line: chosen input, citation, hand calculation,
   identity, or recovery.
4. Each tolerance has a reason, and small values use `abs=0`.
5. The name states the claim; the docstring ends with `ON FAILURE:`.
6. You watched it fail against deliberately broken code.
7. Physics you could not derive or cite, and label wording, went to the author.
