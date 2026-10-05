# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed - BREAKING CHANGES

- One import path per public object: every public object is imported from the module that
  defines it, e.g. `from solarwindpy.core.plasma import Plasma` or
  `solarwindpy.plotting.hist2d.Hist2D`. Packages no longer re-export objects; their
  `__all__` lists submodules (and objects the package file itself defines, such as
  `fitfunctions.available`). `solarwindpy.pp` (for `solarwindpy.plotting`) is the one
  temporary nickname. `plotting/histograms.py` is removed. Two misspelled names are
  corrected and sixteen internal helpers are private. No aliases are kept; an old path raises
  `AttributeError` or `ImportError`. Every removed path and its replacement:

  | Old path | New path |
  |---|---|
  | `solarwindpy.units_constants` | `solarwindpy.core.units_constants` |
  | `solarwindpy.base` | `solarwindpy.core.base` |
  | `solarwindpy.vector` | `solarwindpy.core.vector` |
  | `solarwindpy.tensor` | `solarwindpy.core.tensor` |
  | `solarwindpy.ions` | `solarwindpy.core.ions` |
  | `solarwindpy.plasma` | `solarwindpy.core.plasma` |
  | `solarwindpy.spacecraft` | `solarwindpy.core.spacecraft` |
  | `solarwindpy.alfvenic_turbulence` | `solarwindpy.core.alfvenic_turbulence` |
  | `solarwindpy.Plasma` | `solarwindpy.core.plasma.Plasma` |
  | `solarwindpy.ReferenceAbundances` | `solarwindpy.core.abundances.ReferenceAbundances` |
  | `solarwindpy.at` | `solarwindpy.core.alfvenic_turbulence` |
  | `solarwindpy.sc` | `solarwindpy.core.spacecraft` |
  | `solarwindpy.sa` | `solarwindpy.solar_activity` |
  | `solarwindpy.Hist1D` | `solarwindpy.plotting.hist1d.Hist1D` |
  | `solarwindpy.Hist2D` | `solarwindpy.plotting.hist2d.Hist2D` |
  | `solarwindpy.TeXlabel` | `solarwindpy.plotting.labels.base.TeXlabel` |
  | `solarwindpy.core.Base` | `solarwindpy.core.base.Base` |
  | `solarwindpy.core.Core` | `solarwindpy.core.base.Core` |
  | `solarwindpy.core.Vector` | `solarwindpy.core.vector.Vector` |
  | `solarwindpy.core.Tensor` | `solarwindpy.core.tensor.Tensor` |
  | `solarwindpy.core.Ion` | `solarwindpy.core.ions.Ion` |
  | `solarwindpy.core.Plasma` | `solarwindpy.core.plasma.Plasma` |
  | `solarwindpy.core.Spacecraft` | `solarwindpy.core.spacecraft.Spacecraft` |
  | `solarwindpy.core.Units` | `solarwindpy.core.units_constants.Units` |
  | `solarwindpy.core.Constants` | `solarwindpy.core.units_constants.Constants` |
  | `solarwindpy.core.AlfvenicTurbulence` | `solarwindpy.core.alfvenic_turbulence.AlfvenicTurbulence` |
  | `solarwindpy.core.ReferenceAbundances` | `solarwindpy.core.abundances.ReferenceAbundances` |
  | `solarwindpy.core.Abundance` | `solarwindpy.core.abundances.Abundance` |
  | `solarwindpy.fitfunctions.FitFunction` | `solarwindpy.fitfunctions.core.FitFunction` |
  | `solarwindpy.fitfunctions.TrendFit` | `solarwindpy.fitfunctions.trend_fits.TrendFit` |
  | `solarwindpy.fitfunctions.Exponential` | `solarwindpy.fitfunctions.exponentials.Exponential` |
  | `solarwindpy.fitfunctions.ExponentialCDF` | `solarwindpy.fitfunctions.exponentials.ExponentialCDF` |
  | `solarwindpy.fitfunctions.ExponentialPlusC` | `solarwindpy.fitfunctions.exponentials.ExponentialPlusC` |
  | `solarwindpy.fitfunctions.Gaussian` | `solarwindpy.fitfunctions.gaussians.Gaussian` |
  | `solarwindpy.fitfunctions.GaussianLn` | `solarwindpy.fitfunctions.gaussians.GaussianLn` |
  | `solarwindpy.fitfunctions.GaussianNormalized` | `solarwindpy.fitfunctions.gaussians.GaussianNormalized` |
  | `solarwindpy.fitfunctions.GaussianPlusHeavySide` | `solarwindpy.fitfunctions.composite.GaussianPlusHeavySide` |
  | `solarwindpy.fitfunctions.GaussianTimesHeavySide` | `solarwindpy.fitfunctions.composite.GaussianTimesHeavySide` |
  | `solarwindpy.fitfunctions.GaussianTimesHeavySidePlusHeavySide` | `solarwindpy.fitfunctions.composite.GaussianTimesHeavySidePlusHeavySide` |
  | `solarwindpy.fitfunctions.HeavySide` | `solarwindpy.fitfunctions.heaviside.HeavySide` |
  | `solarwindpy.fitfunctions.HingeAtPoint` | `solarwindpy.fitfunctions.hinge.HingeAtPoint` |
  | `solarwindpy.fitfunctions.HingeMax` | `solarwindpy.fitfunctions.hinge.HingeMax` |
  | `solarwindpy.fitfunctions.HingeMin` | `solarwindpy.fitfunctions.hinge.HingeMin` |
  | `solarwindpy.fitfunctions.HingeSaturation` | `solarwindpy.fitfunctions.hinge.HingeSaturation` |
  | `solarwindpy.fitfunctions.Line` | `solarwindpy.fitfunctions.lines.Line` |
  | `solarwindpy.fitfunctions.LineXintercept` | `solarwindpy.fitfunctions.lines.LineXintercept` |
  | `solarwindpy.fitfunctions.PowerLaw` | `solarwindpy.fitfunctions.power_laws.PowerLaw` |
  | `solarwindpy.fitfunctions.PowerLawOffCenter` | `solarwindpy.fitfunctions.power_laws.PowerLawOffCenter` |
  | `solarwindpy.fitfunctions.PowerLawPlusC` | `solarwindpy.fitfunctions.power_laws.PowerLawPlusC` |
  | `solarwindpy.fitfunctions.Saturation` | `solarwindpy.fitfunctions.hinge.Saturation` |
  | `solarwindpy.fitfunctions.TwoLine` | `solarwindpy.fitfunctions.hinge.TwoLine` |
  | `solarwindpy.fitfunctions.FitFunctionError` | `solarwindpy.fitfunctions.core.FitFunctionError` |
  | `solarwindpy.fitfunctions.InsufficientDataError` | `solarwindpy.fitfunctions.core.InsufficientDataError` |
  | `solarwindpy.fitfunctions.FitFailedError` | `solarwindpy.fitfunctions.core.FitFailedError` |
  | `solarwindpy.fitfunctions.InvalidParameterError` | `solarwindpy.fitfunctions.core.InvalidParameterError` |
  | `solarwindpy.plotting.subplots` | `solarwindpy.plotting.tools.subplots` |
  | `solarwindpy.plotting.save` | `solarwindpy.plotting.tools.save` |
  | `solarwindpy.plotting.nan_gaussian_filter` | `solarwindpy.plotting.tools.nan_gaussian_filter` |
  | `solarwindpy.plotting.histograms.agg_plot` | `solarwindpy.plotting.agg_plot` |
  | `solarwindpy.plotting.histograms.hist1d` | `solarwindpy.plotting.hist1d` |
  | `solarwindpy.plotting.histograms.hist2d` | `solarwindpy.plotting.hist2d` |
  | `solarwindpy.plotting.histograms.AggPlot` | `solarwindpy.plotting.agg_plot.AggPlot` |
  | `solarwindpy.plotting.histograms.Hist1D` | `solarwindpy.plotting.hist1d.Hist1D` |
  | `solarwindpy.plotting.histograms.Hist2D` | `solarwindpy.plotting.hist2d.Hist2D` |
  | `solarwindpy.plotting.labels.TeXlabel` | `solarwindpy.plotting.labels.base.TeXlabel` |
  | `solarwindpy.plotting.labels.Vsw` | `solarwindpy.plotting.labels.special.Vsw` |
  | `solarwindpy.plotting.labels.Count` | `solarwindpy.plotting.labels.special.Count` |
  | `solarwindpy.plotting.labels.Ion` | `solarwindpy.plotting.labels.composition.Ion` |
  | `solarwindpy.plotting.labels.ChargeStateRatio` | `solarwindpy.plotting.labels.composition.ChargeStateRatio` |
  | `solarwindpy.plotting.labels.ElementalAbundance` | `solarwindpy.plotting.labels.elemental_abundance.ElementalAbundance` |
  | `solarwindpy.solar_activity.ssn` | `solarwindpy.solar_activity.sunspot_number` |
  | `solarwindpy.solar_activity.icme.ICMECAT` | `solarwindpy.solar_activity.icme.icmecat.ICMECAT` |
  | `solarwindpy.solar_activity.icme.ICMECATDownloadError` | `solarwindpy.solar_activity.icme.icmecat.ICMECATDownloadError` |
  | `solarwindpy.solar_activity.lisird.LISIRD` | none (removed; see Removed) |
  | `solarwindpy.solar_activity.lisird.ExtremaCalculator` | none (removed; see Removed) |
  | `solarwindpy.solar_activity.icme.ICMECAT_URL` | `solarwindpy.solar_activity.icme.icmecat.ICMECAT_URL` |
  | `solarwindpy.solar_activity.icme.SPACECRAFT_NAMES` | `solarwindpy.solar_activity.icme.icmecat.SPACECRAFT_NAMES` |
  | `solarwindpy.solar_activity.icme.RULES_OF_THE_ROAD` | `solarwindpy.solar_activity.icme.icmecat.RULES_OF_THE_ROAD` |
  | `solarwindpy.solar_activity.sunspot_number.sidc.Base` | `solarwindpy.solar_activity.base.Base` |
  | `solarwindpy.core.alfvenic_turbulence.AlvenicTurbAveraging` | `solarwindpy.core.alfvenic_turbulence.AlfvenicTurbAveraging` |
  | `solarwindpy.plotting.labels.special.ComparisonLable` | `solarwindpy.plotting.labels.special.ComparisonLabel` |
  | `solarwindpy.fitfunctions.core.Observations` | `solarwindpy.fitfunctions.core._Observations` (private) |
  | `solarwindpy.fitfunctions.core.UsedRawObs` | `solarwindpy.fitfunctions.core._UsedRawObs` (private) |
  | `solarwindpy.fitfunctions.core.InitialGuessInfo` | `solarwindpy.fitfunctions.core._InitialGuessInfo` (private) |
  | `solarwindpy.fitfunctions.core.ChisqPerDegreeOfFreedom` | `solarwindpy.fitfunctions.core._ChisqPerDegreeOfFreedom` (private) |
  | `solarwindpy.fitfunctions.core.FitBounds` | `solarwindpy.fitfunctions.core._FitBounds` (private) |
  | `solarwindpy.plotting.labels.base.MCS` | `solarwindpy.plotting.labels.base._MCS` (private) |
  | `solarwindpy.plotting.base.CbarMaker` | `solarwindpy.plotting.base._CbarMaker` (private) |
  | `solarwindpy.plotting.base.DataLimFormatter` | none (removed; nothing used it) |
  | `solarwindpy.plotting.tools.calculate_nrows_ncols` | none (removed; it had no callers) |
  | `solarwindpy.plotting.tools.use_style` | `solarwindpy.plotting.tools._use_style` (private; importing solarwindpy.plotting applies the style) |
  | `solarwindpy.fitfunctions.hinge.XIntercepts` | `solarwindpy.fitfunctions.hinge._XIntercepts` (private) |
  | `solarwindpy.plotting.spiral.InitialSpiralEdges` | `solarwindpy.plotting.spiral._InitialSpiralEdges` (private) |
  | `solarwindpy.plotting.spiral.SpiralMeshBinID` | `solarwindpy.plotting.spiral._SpiralMeshBinID` (private) |
  | `solarwindpy.plotting.spiral.SpiralFilterThresholds` | `solarwindpy.plotting.spiral._SpiralFilterThresholds` (private) |
  | `solarwindpy.plotting.spiral.get_counts_per_bin` | `solarwindpy.plotting.spiral._get_counts_per_bin` (private) |
  | `solarwindpy.plotting.spiral.calculate_bin_number_with_numba` | `solarwindpy.plotting.spiral._calculate_bin_number_with_numba` (private) |
  | `solarwindpy.plotting.labels.species_translation` | none (removed; it was `labels.base._run_species_substitution`) |

- Python 3.12 or newer is required (was 3.11).
- pandas 3 is required: the supported range is `pandas>=3,<4` (was `>=2.0`). The suite
  also passes on pandas 2.2 and 2.3, but only one major version is tested and declared.
- `pyproject.toml` is the only dependency declaration. `requirements.txt`,
  `requirements-dev.lock`, and `docs/requirements.txt` are removed; install with
  `pip install -e ".[dev]"` (or `".[docs]"` for documentation). `solarwindpy.yml`
  remains the conda development environment.
- The in-repository conda recipe (`recipe/`) is removed. The conda-forge feedstock,
  `conda-forge/solarwindpy-feedstock`, is the only recipe.
- Plot value limits (`alim`) are reworked:
  - `limit_color_norm` is removed from `Hist2D.make_plot`, `plot_hist_with_contours`
    and `plot_contours`, `SpiralPlot2D.make_plot`, and the `OrbitHist2D` plots. To
    limit a plot to the bulk of its values use `set_alim(lower, upper,
    kind="quantile")`, e.g. `set_alim(0.01, 0.99, kind="quantile")`, which masks bins
    outside those quantiles instead of clipping the colour scale. Passing
    `limit_color_norm=` now fails in matplotlib (`AttributeError`) or with
    `ValueError` in `SpiralPlot2D`; `Hist2D.plot_contours` only warns that the keyword
    was unused.
  - Removing `limit_color_norm` moves every later positional parameter of those
    methods one slot left, e.g. `make_plot(ax, cbar, cbar_kwargs, fcn, alpha_fcn)` and
    `plot_contours(ax, label_levels, cbar, cbar_kwargs, fcn, ...)`. Pass them by
    keyword to be safe. `plot_contours` takes `levels` as a named last parameter.
  - `Hist1D` and `OrbitHist1D` no longer have `alim` or `set_alim`; they never applied
    it. `SpiralPlot2D` gains `alim`.
  - `Hist2D.plot_contours` colours densities (`axnorm` of `"d"`, `"cd"`, `"rd"`) with
    a log norm by default, as `make_plot` and `plot_hist_with_contours` already did,
    so density contours default to log colour bands.
  - `OrbitHist2D` applies `alim` to the "Both" leg too, once over all legs (the Both
    leg itself is still disabled).
- `solarwindpy.plotting.orbits` removed (unused); last available at commit e790d95f.
- `Probability`, `CountOther`, `MathFcn` and `AbsoluteValue` in
  `solarwindpy.plotting.labels.special` raise `TypeError` at construction when
  `other_label` is a plain `str`. A string was never usable (it failed later with
  `AttributeError`); wrap raw TeX in `ManualLabel`.
- `Hist1D` no longer accepts `axnorm` words beyond `"d"`/`"t"` (e.g. `"density"`, which
  was truncated to `"d"`). An invalid `axnorm` on `Hist1D` or `Hist2D` raises `TypeError`
  (not a string or None) or `ValueError` (unknown key) instead of `AssertionError`.
- Fit-function help text inheritance now uses `docstring-inheritance` 3.x
  (`>=3.0,<4`). Importing `solarwindpy` sets `DOCSTRING_INHERITANCE_ENABLE=1` unless
  the variable is already set, and warns if `docstring_inheritance` was imported
  earlier with inheritance off.

### Changed

- `ICMECAT(cache_dir=...)` caches the catalog as `icmecat.csv`, the format it downloads
  in, instead of `icmecat.parquet`, so caching needs no parquet engine (it raised
  `ImportError` without one). An existing `icmecat.parquet` cache is ignored, so the
  catalog downloads once more.
- `FitFunction.rsq` returns NaN when the fitted `y` have no spread (a single point, or
  constant data), where R^2 is undefined. It previously divided by zero, warning and
  returning -inf or NaN.
- `Line.p0` and `LineXintercept.p0` return `None` (no initial estimate) for repeated `x`
  without a divide-by-zero warning. `LineXintercept.p0` also returns `None` when the
  estimated slope is zero, since a flat line has no x-intercept; it previously returned
  an x-intercept of -inf or NaN, and a NaN initial guess made `make_fit` fail.
- `Hist2D.plot_edges` documents its `xlim` and `ylim` keywords as inclusive: a vertex
  exactly on a limit is kept. Behaviour is unchanged.

### Added

- `solarwindpy.tools.normal_parameters(m, s, base=np.e)`: `base` gives the log base of
  `m` and `s`, e.g. `base=10` for a base-10 log-normal. The default is unchanged.
- `Hist1D.set_axnorm("t")` (and `Hist1D(axnorm="t")`) divides the histogram by its
  maximum, so the peak equals 1, as `Hist2D` does. It previously raised `AssertionError`.
- `CITATION.cff` gives the Zenodo concept DOI and the author's ORCID in Citation File
  Format, so GitHub and Zenodo can read the citation.
- Python 3.14 is supported and declared; the full suite passes on it.
- `solarwindpy.examples.load_plasma()` returns a small example `Plasma`: three rows with
  species `a`, `e`, `p1` and `p2`, and a Parker Solar Probe trajectory in HCI. The data
  ships in `core/data/example_*.csv`; docstring examples start from it.

### Fixed

These change computed values; rerun any analysis that used them.

- `Plasma.heat_flux` / `qpar` is now reported in uW m^-2, matching its docstring and
  plot label. The previous factor produced values in units of 1e-7 W m^-2 while the
  label said mW cm^-2, a factor of 1e8 apart; values are now 10 times smaller than
  before.
- `Ion.specific_entropy` / `Plasma.specific_entropy` is now in eV cm^2 m_p^-5/3 as
  labelled. Values were 9.2 times too small; ratios and trends are unchanged.
- `Ion.kinetic_energy_flux` / `Plasma.kinetic_energy_flux` raised `AttributeError` on
  every call; it now returns uW m^-2.
- `hbar` is scipy's exact h/2pi (was the CODATA 2014 value), and the solar radius is
  the IAU 2015 nominal 695.7e6 m (was 695.508e6 m), shifting distances in solar radii
  by 0.028%.
- Kinetic energy flux has a plot label, `"Wk"`, rendered W_K in uW m^-2.
- `Vector.latitude` / `lat` and `Vector.colatitude` / `colat` were swapped. Latitude is
  now the angle above the xy-plane, `arctan2(z, rho)` in [-90, 90]; colatitude is the
  angle from +z, `arctan2(rho, z)` in [0, 180]. A vector along +z has latitude 90 and
  colatitude 0 (previously the reverse); each old value converts as `new = 90 - old`.
- `Tensor.magnitude` raised `ValueError` on every Tensor the package builds. It now
  returns the scalar thermal speed sqrt((w_par^2 + 2 w_per^2) / 3), which combines the
  components through the temperatures and matches the stored `scalar` column.
- `Vector.project` and `Vector.cos_theta` returned 0 (a perpendicular answer) on rows
  present in only one of the two vectors, or with a NaN component. They now return NaN
  there. The `Plasma` methods built on `project` change the same way on such rows.
- Plot labels for a latitude component (`"lat"`) now render as lambda and a colatitude
  component (`"colat"`) as theta; the two symbols were swapped.
- `ReferenceAbundances` CI chondrite abundances for Ne, Ar, Kr and Xe were NaN. They are
  now the Asplund et al. (2021) Table 2 values -1.12, -0.50, -2.27 and -1.95 dex (each
  ± 0.18), doi:10.1051/0004-6361/202140445.
- `ReferenceAbundances.get_element` named its Series by the index level it did not
  search: `get_element("Fe")` was named 26 and `get_element(26)` was named `"Fe"`. Both
  are now named by the atomic number, 26.

### Removed

- `solarwindpy.plotting.select_data_from_figure` and its `SelectFromPlot2D` class. It
  passed the `rectprops` keyword, which current matplotlib's `RectangleSelector` no
  longer accepts, so construction raised `TypeError` (verified on matplotlib 3.10.8).
  Interactive selection of data from a plot is available in [glue](https://glueviz.org).
- The `"Q"` plot label key. It was commented as a heating rate, carried a heat flux
  unit, and nothing in the package computes a heating rate. Heat flux is labelled
  `"q"`.
- `Hist2D`: removed the undocumented, unreachable tuple `axnorm` branch; `set_axnorm`
  already rejected tuples and still does.
- `solarwindpy.solar_activity.lisird` (`LISIRD`, `ExtremaCalculator`) and
  `solarwindpy.solar_activity.get_all_indices` removed (unused); last available at
  commit beb10945.
- The `"Lalpha"`, `"f10.7"`, `"CaK"`, and `"MgII"` plot label keys, which existed only
  for the removed LISIRD indices.
- Asplund et al. (2009) abundances: `ReferenceAbundances` loses its `year` parameter and
  `.year` property, and `core/data/asplund2009.csv` is removed. `ReferenceAbundances()`
  always loads Asplund et al. (2021), Table 2 (doi:10.1051/0004-6361/202140445);
  passing `year=` raises `TypeError`.
- `Plasma` plasma-statistics logging: the `log_plasma_stats` argument (of `Plasma` and
  `Plasma.load_from_file`), the `log_plasma_at_init` property and `set_log_plasma_stats`.
  Nothing used them, and turning them on raised `AttributeError` on pandas 3
  (`DataFrame.applymap` is gone). Passing `log_plasma_stats=` raises `TypeError`. `Plasma`
  still logs "No spacecraft data passed to Plasma" (and likewise for `auxiliary_data`) at
  INFO when that input is `None`.

## [0.3.0] - 2025-12-24

### Changed - BREAKING CHANGES

**Dependency Management Overhaul**: Consolidated 11 dependency files into single-source-of-truth system using `pyproject.toml` with `pip-tools` lockfiles.

- **REMOVED**: `requirements-dev.txt` (replaced by `requirements-dev.lock`)
- **REMOVED**: `scripts/freeze_requirements.py` (replaced by `pip-compile`)
- **REMOVED**: `scripts/generate_docs_requirements.py` (replaced by `pip-compile --extra=docs`)
- **Migration required**: See [the v0.3.0 migration guide](https://github.com/blalterman/SolarWindPy/blob/v0.3.0/docs/MIGRATION-DEPENDENCY-OVERHAUL.md)

**Developer Workflow Changes**:
```bash
# OLD (v0.2.x):
pip install -r requirements-dev.txt

# NEW (v0.3.0+):
pip install -r requirements-dev.lock
```

**Dependency Updates**: Minimum versions updated for NumPy 2.0 ecosystem compatibility
  - `numpy`: `>=1.22,<2.0` → `>=1.26,<3.0` (adds NumPy 2.0 support)
  - `scipy`: `>=1.10` → `>=1.13`
  - `pandas`: `>=1.5` → `>=2.0`
  - `numba`: `>=0.57` → `>=0.59`
  - `docstring-inheritance`: `>=2.0` → `>=2.2.0,<3.0` (MRO fix, exclude breaking v3.0)
  - `pytest`: `>=7.4.4` → `>=8.0`
  - `pytest-cov`: `>=4.1.0` → `>=6.0`

### Added

- **Lockfiles** for reproducible builds:
  - `requirements.txt` - Production dependencies (from `[project.dependencies]`)
  - `requirements-dev.lock` - Development dependencies (from `[project.optional-dependencies.dev]`)
  - `docs/requirements.txt` - Documentation dependencies (from `[project.optional-dependencies.docs]`)

- **Tests**: `tests/fitfunctions/test_metaclass_compatibility.py`
  - Validates `FitFunctionMeta` MRO compatibility with `NumpyDocstringInheritanceMeta` and `ABCMeta`
  - Prevents metaclass regression bugs
  - Tests abstract method enforcement, docstring inheritance, all fitfunction instantiation
  - Includes version constraint validation (docstring-inheritance >=2.2.0,<3.0)

- **Documentation**: Comprehensive [migration guide](https://github.com/blalterman/SolarWindPy/blob/v0.3.0/docs/MIGRATION-DEPENDENCY-OVERHAUL.md) (retired from the tree; kept at the v0.3.0 tag)
  - Breaking changes overview
  - Old vs new developer workflows
  - NumPy 2.0 compatibility matrix
  - CI/CD changes
  - Rollback procedures
  - FAQ with common migration questions

- **Dependency Groups** in `pyproject.toml`:
  - `[project.optional-dependencies.test]` - Testing tools only
  - `[project.optional-dependencies.docs]` - Documentation tools only
  - `[project.optional-dependencies.dev]` - All development tools (test + docs + dev)

### Fixed

- **Critical**: `numpy==2.2.6` in `requirements.txt` violated `pyproject.toml` constraint `<2.0`
  - Root cause: `freeze_requirements.py` used `pip freeze` without validating `pyproject.toml`
  - Fix: Replaced custom scripts with `pip-compile` which enforces constraints
- **Dependency fragmentation**: Eliminated sync issues between 11 dependency files
- **Version drift**: Lockfiles prevent undocumented version changes

### Infrastructure

**GitHub Actions**: All CI/CD workflows updated for lockfile-based dependency management

- `.github/workflows/sync-requirements.yml`:
  - Triggers on `pyproject.toml` changes (single source of truth)
  - Uses `pip-compile` to generate lockfiles instead of Python scripts
  - Validates lockfiles with `pip install --dry-run`

- `.github/workflows/continuous-integration.yml`:
  - Uses `requirements-dev.lock` instead of `requirements-dev.txt`
  - Faster caching via lockfile hash
  - Cross-platform testing: ubuntu/macos × Python 3.11/3.13

- `.github/workflows/ci-master.yml`:
  - Updated to use `requirements-dev.lock`
  - Consistent with other workflows

- `.github/workflows/security.yml`:
  - Audits `requirements-dev.lock` with `safety` and `pip-audit`
  - Security scans on frozen versions instead of loose constraints

- `.github/workflows/publish.yml`:
  - **Pre-release validation**: Blocks PyPI deployment if lockfiles are out of sync with `pyproject.toml`
  - Prevents releasing with inconsistent dependencies

**Scripts**: Updated `scripts/requirements_to_conda_env.py`
- Now reads lockfiles (default: `requirements.txt`) instead of `requirements-dev.txt`
- Documentation clarifies `pip-compile` is a prerequisite
- Supports generating conda environments from any lockfile

### Testing

- **NumPy Compatibility**: Validated with NumPy 1.26.4 and 2.2.6 (247 tests passed each)
- **Coverage**: Maintained 78% (improved from 77.86% baseline)
- **Test Suite**: 1576 tests passed, 19 skipped
- **Metaclass Tests**: 9 new regression tests for `FitFunctionMeta` MRO compatibility

### Migration

**For Developers**:
1. Update checkout: `git pull`
2. Install from lockfile: `pip install -r requirements-dev.lock`
3. Verify: `pytest -q`

**For CI/CD Pipelines**:
- Replace `pip install -r requirements-dev.txt` with `pip install -r requirements-dev.lock`

**Rollback**: Use `pip install solarwindpy==0.2.0` if issues arise

See [the v0.3.0 migration guide](https://github.com/blalterman/SolarWindPy/blob/v0.3.0/docs/MIGRATION-DEPENDENCY-OVERHAUL.md) for complete migration instructions

## [0.2.0] - 2025-11-12

### Changed
- **BREAKING**: Minimum Python version raised from 3.10 to 3.11
  - Aligns with scientific Python ecosystem (NumPy 2.x, Astropy 7.x require Python 3.11+)
  - Python 3.10 reaches end-of-life in October 2026
  - Enables Python 3.11+ performance improvements (10-60% faster in many workloads)
  - Added Python 3.13 to CI testing matrix for forward compatibility

### Fixed
- Resolved conda-forge feedstock Issue #8 (Python version compatibility)
- Removed all Python 3.10 references from CI and packaging configuration
- Updated ReadTheDocs configuration to use Python 3.11

### Added
- Python 3.13 CI testing for forward compatibility validation
- Runnable Quick Start example in README with realistic solar wind data
  - Demonstrates complete Plasma object creation workflow
  - Includes physically accurate parameter values
  - Users can copy-paste and execute immediately

### Documentation
- Updated installation requirements in README.rst and docs/source/installation.rst
- Fixed LICENSE file detection for GitHub (converted from .rst to plain text)
- Archived completed documentation to reduce AI context overhead

## [0.1.5] - 2025-11-10

### Fixed
- **Documentation validation** - Resolved doctest failures for JOSS submission
  - Added continuation markers (`...`) to multi-line doctest examples
  - Completed Ion class example with all required columns (v.x, v.y, v.z, w.par, w.per)
  - Added `# doctest: +SKIP` directives to non-deterministic fitfunction examples
  - Added `# doctest: +NORMALIZE_WHITESPACE` for pandas DataFrame output
  - All 33 doctests now passing (11 executed, 22 appropriately skipped)
  - Aligns with paper statement: "fitfunctions tests remain in active development"
  - Unit tests (1,557 test cases) provide comprehensive functionality validation

### Changed
- **Documentation examples** - Maintain instructional value while ensuring reliable validation
- **JOSS paper** - Updated acknowledgements to reflect AI-assisted development workflow
- **Conda channels** - Switched to conda-forge only (removed Anaconda `defaults` channel)
  - Eliminates commercial channel licensing warnings in CI
  - All dependencies available on open-source conda-forge channel
  - Users with existing environments should recreate: `conda env remove -n solarwindpy && conda env create -f solarwindpy.yml`
  - Aligns with JOSS open-source infrastructure requirements

## [0.1.0] - 2025-08-23

### Added
- **Initial stable release on PyPI** - First public release of SolarWindPy
- **Semantic versioning with setuptools_scm** - Automatic version detection from git tags
- **Automated deployment pipeline via GitHub Actions** - Complete CI/CD for PyPI publishing
- **Core plasma physics calculations and data structures** - Multi-species plasma analysis
- **Plotting and visualization capabilities** - Publication-quality scientific plots
- **Instability analysis tools** - Solar wind plasma instability calculations
- **Comprehensive test coverage** - ≥95% code coverage with scientific validation
- **Release automation scripts** - check_release_ready.py and bump_version.py tools
- **Comprehensive documentation** - Release process and deployment guides

### Changed
- **Migrated from development to stable release** - Production-ready package
- **Enhanced package metadata for PyPI distribution** - Complete project configuration
- **Improved version detection with setuptools_scm** - Tag-based versioning
- **Enhanced GitHub Actions workflows** - Production deployment automation

### Fixed
- **Graceful handling of missing PyPI tokens** - Continues deployment without tokens
- **Code formatting standardization** - Black formatting across entire codebase
- **Test fixture scope issues** - Module-level fixtures for cross-class access
- **Documentation validation** - Comprehensive doctest and example validation

### Security
- **Added validation gates for release deployment** - Multi-stage verification process
- **PyPI token security** - Secure repository secrets management