# SolarWindPy v2.0: Core Rewrite via Characterization Testing

## Strategy: Test v1 First, Then Rewrite to Pass Same Tests

```
Phase A-Core:    Write characterization tests against v1 core (A.0-A.6)
                 Tests pass with v1. Tests ARE the spec.

Phase A-NonCore: Write characterization tests against v1 non-core modules (A.7-A.10)
                 Runs IN PARALLEL with Phase B. Pure value for v1. Phase C prerequisites.

Phase B:         Rewrite core/ to xarray, passing Phase A-Core tests.
                 When v2 passes all A-Core tests → behavioral equivalence guaranteed.

Phase C:         (Future) Incrementally migrate fitting/plotting/activity/instabilities.
                 Phase A-NonCore tests already exist → same TDD guarantee as core.
```

```
Timeline:
  Phase A-Core ──────→ Phase B (must pass A-Core)
         │
         └── Phase A-NonCore ──→ (runs in parallel with B, tests v1)
                                  ↓
                            Phase C (future, already has tests)
```

**Why this approach:**
- Tests capture ACTUAL v1 behavior, including innovations we might miss
- v1 gets better tested immediately (pure value, zero risk)
- v2 correctness is guaranteed by passing the same tests
- No guessing about physics formulas — v1 output IS ground truth
- Core rewrite scope: 4,317 lines (21%), non-core tested but untouched: 15,924 lines
- Non-core characterization tests are Phase C prerequisites — future rewrites get TDD "for free"
- A-NonCore runs in parallel with Phase B — no added wall-clock time on the critical path

---

## Decision Record

| Question | Answer |
|----------|--------|
| Package name | Same `solarwindpy`, version 2.0 |
| Rewrite scope | **Core only** (4,317 lines, 21% of codebase) |
| Fitting/plotting/activity/instabilities | **Stay as-is** (15,924 lines untouched) |
| Data backend | xarray (replaces pandas MultiIndex) |
| AI-friendly | First-class design goal |
| Test strategy | **Characterization tests against v1 → rewrite v2 to pass them** |
| Non-core test strategy | **Characterization tests for all modules** (A-NonCore ∥ Phase B) |
| Parallel agents | Yes — phases with independent work parallelized |
| Compatibility bridge | v2 DataArray → `.values`/`.to_series()` for existing modules |
| Species string spec | PRESERVED — tested against v1 behavior |
| `__call__` component access | PRESERVED — `velocity("x")`, `thermal_speed("par")` |
| All 15 core innovations | PRESERVED — characterization tests capture them |
| All 32 non-core innovations | **TESTED + PRESERVED** — characterization tests written, modules untouched |

---

## Innovation Registry

### Scope A: Core Innovations (15 — tested and reimplemented)

| # | Innovation | v1 Location | Phase A Test Strategy |
|---|-----------|-------------|----------------------|
| 1 | Species string spec DSL | `base.py:136-175`, `plasma.py:505-528` | Test all 3 calling patterns with known data |
| 2 | `__getattr__` ion access | `plasma.py:208-212` | Test `plasma.p1` returns correct Ion |
| 3 | `__call__` component access | `vector.py:33-46`, `tensor.py:30-48` | Test `velocity("x")` == `velocity.x` |
| 4 | Calculation chain orchestration | `plasma.py` (full) | Test intermediate + final values match |
| 5 | Adaptive species return types | `plasma.py:798-895` | Test shape/type for single/multi/combined |
| 6 | Scalar w auto-derivation | `plasma.py:744-762` | Test `sqrt((par^2 + 2*per^2)/3)` at init |
| 7 | Tensor par/per/scalar contract | `tensor.py:9-91` | Test rejection of wrong components |
| 8 | Polytropic index context | `units_constants.py:37` | Test cs uses `{par:3, per:2, scalar:5/3}` |
| 9 | lnlambda/nuc/nc validation chain | `plasma.py:1353-1552` | Test rejection of invalid species combos |
| 10 | `estimate_electrons` | `plasma.py:1639-1727` | Test charge neutrality + T_e=T_p |
| 11 | `,` syntax for turbulence | `plasma.py:1776-1822` | Test `"p1,a"` velocity/density separation |
| 12 | `raffaella_version` flag | `alfvenic_turbulence.py:61-62` | Test GSE→RTN + Parker spiral projection |
| 13 | Save/load modifier functions | `plasma.py:296-397` | Test roundtrip with transform |
| 14 | Data quality logging | `plasma.py:678-722` | Test statistics output |
| 15 | BField minimal specialization | `vector.py:294-329` | Test Vector + pressure property |

### Scope B: Non-Core Innovations (32 — characterization tested via A-NonCore, modules untouched)

These modules stay as-is but gain comprehensive characterization tests. Phase A-NonCore tests:
- **Fitting (8):** TeXinfo, named tuple tracking, scipy integration, 6 piecewise, composites, joblib, FFPlot, metaclass docstring inheritance
- **Plotting (7):** Species label DSL, aggregation pipeline, Numba spiral, cell filtering, OrbitPlot mixin, 7 normalization modes, bin edge strategies
- **Solar Activity (7):** Dual-layer cache, JSON metadata, extrema calculator, IntervalIndex cycle assignment, Rise/Fall labeling, ICMECAT fallbacks, vectorized containment
- **Instabilities (4):** Verscharen parametric table, sentinel validation, NaN-safe thresholds, table legend
- **Engineering (6):** Import aliases, pandas strict mode, year-selectable abundances, dynamically constructed Ion dict, Ion reconstruction design, view-based memory model

**Current test coverage audit (what A-NonCore addresses):**

| Module | LOC | Methods | Existing Tests | Coverage | Priority |
|--------|-----|---------|---------------|----------|----------|
| instabilities/ | 727 | 22 | 0 | **0%** | CRITICAL |
| solar_activity/ | 2,096 | 92 | 50 | ~30% | CRITICAL |
| plotting/ | 7,362 | ~280 | 207 | ~35-45% | HIGH |
| fitfunctions/ | 5,563 | 188 | 240+ | ~75% | GAP-FILL |

---

## Phase A: Characterization Tests Against v1

**Goal:** Write tests comprehensive enough that if v2 passes them all, we trust it.

**Principle:** Tests assert on INTERFACE and NUMERICAL OUTPUT, not implementation details.
- YES: `assert result.values == expected_array` (numerical equivalence)
- YES: `assert result.name == "p1+a"` (interface contract)
- YES: `assert isinstance(plasma.p1, Ion)` (type contract)
- NO: `assert isinstance(result, pd.Series)` (implementation detail — will change)
- NO: `assert result.index.name == "Epoch"` (pandas-specific)

**Test fixtures:** Create synthetic plasma data with known values so we can predict exact outputs.

```python
# Fixture: known-value plasma for characterization
@pytest.fixture
def known_plasma():
    """Plasma with hand-calculated values for verification.

    Species: p1 (protons), a (alphas)
    Time points: 5
    All values chosen so derived quantities are exact (no floating point ambiguity).
    """
    # ... construct v1 Plasma with known data ...
    return plasma
```

### A.0: Species Spec Tests

**File:** `tests/v2_characterization/test_species_spec.py`

```python
class TestConformSpecies:
    def test_single(self): ...                    # "p1" -> ("p1",)
    def test_plus_splits_and_sorts(self): ...     # "p1+a" -> ("a", "p1")
    def test_multi_args_sorted(self): ...         # "p1", "a" -> ("a", "p1")
    def test_rejects_plus_with_multi(self): ...   # "p1+a", "p2" -> ValueError
    def test_rejects_comma(self): ...             # "a,p1" -> ValueError
    def test_single_species_returns_len1(self): ... # "p1+a" -> len == 1

class TestChkSpecies:
    def test_valid_species(self): ...             # "p1" when plasma has p1
    def test_invalid_species_error(self): ...     # "o6" when not in plasma
    def test_error_message_helpful(self): ...     # lists available species
```

**v1 reference:** `core/base.py:136-175`, `core/plasma.py:505-528`

### A.1: Vector3D + Tensor3D Tests

**File:** `tests/v2_characterization/test_vector_tensor.py`

```python
class TestVector:
    # Core operations — capture v1 numerical output
    def test_magnitude(self, known_vector): ...
    def test_unit_vector(self, known_vector): ...
    def test_dot_product(self, v1, v2): ...
    def test_cross_product(self, v1, v2): ...
    def test_rho_lat_lon(self, known_vector): ...
    def test_cos_theta(self, v1, v2): ...

    # Callable component access — innovation #3
    def test_call_x(self, known_vector): ...           # vector("x")
    def test_call_equivalent_to_attr(self, v): ...     # vector("x") == vector.x

    # Projection — captures exact decomposition
    def test_project_parallel(self, velocity, bfield): ...
    def test_project_perpendicular(self, velocity, bfield): ...
    def test_project_reconstructs_original(self, v, b): ...  # v_par + v_perp == v

class TestTensor:
    def test_par_per_scalar_access(self, known_tensor): ...
    def test_call_par(self, known_tensor): ...         # tensor("par")
    def test_scalar_formula(self, known_tensor): ...   # sqrt((par^2 + 2*per^2)/3)
    def test_magnitude(self, known_tensor): ...
    def test_anisotropy(self, known_tensor): ...       # per/par ratio
    def test_rejects_wrong_components(self): ...       # must be par/per/scalar

class TestBField:
    def test_inherits_vector(self, bfield): ...
    def test_pressure(self, bfield): ...               # B^2/(2*mu_0), exact values
    def test_call_component(self, bfield): ...         # bfield("x")
```

**v1 reference:** `core/vector.py` (328 lines), `core/tensor.py` (90 lines)

### A.2: Ion Tests

**File:** `tests/v2_characterization/test_ion.py`

```python
class TestIonProperties:
    # Each test captures v1's exact numerical output for known inputs
    def test_n(self, known_ion): ...                   # number density passthrough
    def test_velocity_is_vector(self, known_ion): ...  # returns Vector type
    def test_thermal_speed_is_tensor(self, known_ion): ...
    def test_rho(self, known_ion): ...                 # n * m, exact values
    def test_temperature_par(self, known_ion): ...     # T = m/(2*k_B) * w^2
    def test_temperature_per(self, known_ion): ...
    def test_temperature_scalar(self, known_ion): ...
    def test_pth_par(self, known_ion): ...             # p = 0.5 * rho * w^2
    def test_pth_per(self, known_ion): ...
    def test_pth_scalar(self, known_ion): ...
    def test_sound_speed_par(self, known_ion): ...     # gamma_par = 3.0
    def test_sound_speed_per(self, known_ion): ...     # gamma_per = 2.0
    def test_sound_speed_scalar(self, known_ion): ...  # gamma_scalar = 5/3
    def test_anisotropy(self, known_ion): ...          # w_per^2 / w_par^2
    def test_specific_entropy(self, known_ion): ...
    def test_kinetic_energy_flux(self, known_ion): ...

class TestIonCaching:
    def test_velocity_cached(self, ion): ...           # same object on repeated access
    def test_thermal_speed_cached(self, ion): ...
```

**v1 reference:** `core/ions.py` (311 lines)

### A.3: Plasma Species Spec Tests (THE critical test suite)

**File:** `tests/v2_characterization/test_plasma.py`

```python
class TestPlasmaConstruction:
    def test_species_list(self, plasma): ...           # plasma.species -> ["a", "p1"]
    def test_scalar_w_auto_calculated(self, plasma): ... # captures v1 init behavior

class TestPlasmaIonAccess:
    def test_getattr_returns_ion(self, plasma): ...    # plasma.p1 -> Ion
    def test_getattr_cached(self, plasma): ...         # plasma.p1 is plasma.p1
    def test_getattr_unknown_raises(self, plasma): ... # helpful error

class TestPlasmaNumberDensity:
    # Single species
    def test_n_single_values(self, plasma): ...        # exact numerical output
    def test_n_single_name(self, plasma): ...          # result labeled "p1"

    # Combined (+ combinator)
    def test_n_combined_values(self, plasma): ...      # sum of n_p1 + n_a
    def test_n_combined_name(self, plasma): ...        # labeled "p1+a"

    # Multiple (comparison)
    def test_n_multi_shape(self, plasma): ...          # has species dimension
    def test_n_multi_values(self, plasma): ...         # both species present

class TestPlasmaBeta:
    def test_beta_single_values(self, plasma): ...     # pth / p_B, exact
    def test_beta_combined_values(self, plasma): ...   # summed pth / p_B
    def test_beta_multi_values(self, plasma): ...
    def test_beta_has_thermal_components(self, plasma): ... # par, per, scalar

class TestPlasmaVelocity:
    def test_v_single_values(self, plasma): ...
    def test_v_combined_is_com(self, plasma): ...      # mass-weighted CoM, exact
    def test_v_multi_values(self, plasma): ...

class TestPlasmaAlfvenSpeed:
    def test_ca_single(self, plasma): ...
    def test_ca_combined(self, plasma): ...            # uses total mass density

class TestPlasmaSoundSpeed:
    def test_cs_single(self, plasma): ...
    def test_cs_uses_polytropic_context(self, plasma): ... # par=3, per=2, scalar=5/3

class TestPlasmaThermalPressure:
    def test_pth_single(self, plasma): ...
    def test_pth_combined(self, plasma): ...           # summed across species

class TestPlasmaTwoSpecies:
    def test_dv_values(self, plasma): ...              # v_a - v_p, exact
    def test_dv_with_com(self, plasma): ...            # v_a - v_CoM
    def test_lnlambda_values(self, plasma): ...        # Coulomb log, exact
    def test_lnlambda_rejects_plus(self, plasma): ... # physics-aware validation
    def test_nuc_values(self, plasma): ...             # collision frequency, exact
    def test_nc_requires_spacecraft(self, plasma): ... # physics-aware validation

class TestPlasmaEdgeCases:
    def test_plus_with_multi_raises(self, plasma): ... # "p1+a", "p2" -> error
    def test_thermal_speed_rejects_plus(self, plasma): ...
    def test_nan_handling(self, plasma_with_nans): ... # skipna behavior
    def test_single_species_plasma(self, single_species_plasma): ...

class TestPlasmaEstimateElectrons:
    def test_requires_protons(self, plasma): ...
    def test_electron_density(self, plasma): ...       # n_e = sum(Z_i * n_i), exact
    def test_electron_temperature(self, plasma): ...   # T_e = T_p, exact

class TestPlasmaDataQuality:
    def test_logging_statistics(self, plasma): ...

class TestPlasmaIO:
    def test_save_load_roundtrip(self, plasma, tmp_path): ...
    def test_save_with_modifier(self, plasma, tmp_path): ...
```

**v1 reference:** `core/plasma.py` (1,901 lines)

### A.4: Spacecraft Tests

**File:** `tests/v2_characterization/test_spacecraft.py`

```python
class TestSpacecraft:
    def test_position_is_vector(self, sc): ...
    def test_distance_to_sun(self, sc): ...            # exact values
    def test_carrington_coords(self, sc): ...
```

**v1 reference:** `core/spacecraft.py` (256 lines)

### A.5: Alfvenic Turbulence Tests

**File:** `tests/v2_characterization/test_turbulence.py`

```python
class TestAlfvenicTurbulence:
    def test_elsasser_zplus(self, turb): ...            # z+ = dv + db_A, exact
    def test_elsasser_zminus(self, turb): ...           # z- = dv - db_A, exact
    def test_cross_helicity(self, turb): ...            # sigma_c
    def test_residual_energy(self, turb): ...           # sigma_r
    def test_alfven_ratio(self, turb): ...

class TestCommaSyntax:
    def test_vel_from_p1_density_from_a(self, plasma): ...  # "p1,a"
    def test_comma_with_plus(self, plasma): ...              # "p1+p2,p1+p2+a"

class TestRaffaellaVersion:
    def test_gse_to_rtn(self, turb_raff): ...
    def test_parker_spiral_projection(self, turb_raff): ...

class TestAlfvenUnitsConversion:
    def test_b_converted_before_averaging(self, turb): ... # order matters
```

**v1 reference:** `core/alfvenic_turbulence.py` (804 lines)

### A.6: Units & Constants Tests

**File:** `tests/v2_characterization/test_units.py`

```python
class TestPolytropic:
    def test_par_is_3(self): ...
    def test_per_is_2(self): ...
    def test_scalar_is_5_over_3(self): ...

class TestConversionFactors:
    # Capture v1's exact conversion factors
    def test_bfield_to_si(self): ...                   # 1e-9
    def test_velocity_to_si(self): ...                 # 1e3
    def test_density_to_si(self): ...                  # 1e6
    # ... all conversion factors from units_constants.py
```

**v1 reference:** `core/units_constants.py` (199 lines)

### Phase A Execution Strategy

**Parallel agents within Phase A:**
- Agent 1: A.0 (species spec) + A.6 (units) — foundational, small
- Agent 2: A.1 (vector/tensor) + A.2 (ion) — data containers
- Agent 3: A.3 (plasma) — the big one, can start once fixtures exist

**Known-value fixtures:** Construct ONE set of synthetic plasma data with hand-calculable values. All characterization tests use this fixture. Example:
```python
# Known values chosen for exact arithmetic:
# n_p1 = 5.0 cm^-3, n_a = 0.2 cm^-3
# v_p1 = [400, 0, 0] km/s, v_a = [420, 10, 0] km/s
# w_p1 = {par: 30, per: 20} km/s, w_a = {par: 40, per: 25} km/s
# B = [3, -2, 1] nT
# → beta_p1_par = (0.5 * rho_p1 * w_p1_par^2) / (B^2 / 2*mu_0) = [exact value]
```

**Verification:** Run `pytest tests/v2_characterization/ -v` against v1. All tests must pass.

---

## Phase A-NonCore: Characterization Tests for Non-Core Modules

**Goal:** Bring all non-core modules to characterization-test standard. Runs IN PARALLEL with Phase B.

**Principle:** Same as Phase A-Core — tests assert on INTERFACE and OUTPUT, not implementation.
These tests run against v1 as-is. They provide:
1. Immediate regression safety for v1
2. Documentation of behavior for 87% undocumented functions
3. Ready-made test suites if Phase C ever rewrites these modules

**Key difference from A-Core tests:** These tests CAN assert on pandas types (`pd.Series`, `pd.DataFrame`) since we are NOT rewriting these modules. If/when Phase C rewrites a module, the tests would be adapted then, just as A-Core tests were designed implementation-agnostic for Phase B.

### A.7: Instabilities Tests (CRITICAL — 0% coverage)

**File:** `tests/v2_characterization/test_instabilities.py`

**Current state:** ZERO tests. 727 LOC. Contains deprecated `iteritems()` call that crashes.

```python
class TestVerscharen2016:
    # Parametric table — the core data structure
    def test_table_shape(self, verscharen): ...           # correct dimensions
    def test_table_columns(self, verscharen): ...         # AIC, FMW, MM, OFI present
    def test_growth_rates_available(self, verscharen): ... # -4, -3, -2

    # Threshold calculations — numerical output for known inputs
    def test_aic_threshold(self, verscharen): ...          # exact values for known beta
    def test_fmw_threshold(self, verscharen): ...
    def test_mm_threshold(self, verscharen): ...
    def test_ofi_threshold(self, verscharen): ...

    # Interpolation
    def test_interpolation_within_range(self, verscharen): ...
    def test_interpolation_extrapolation(self, verscharen): ...

    # Validation
    def test_nan_safe_thresholds(self, verscharen): ...   # NaN input handling
    def test_sentinel_fill_values(self, verscharen): ...  # invalid data detection
    def test_rejects_invalid_instability(self, verscharen): ...

class TestBetaRPlot:
    def test_initialization(self, beta_r_plot): ...
    def test_labels(self, beta_r_plot): ...
    def test_inherits_hist2d(self, beta_r_plot): ...

class TestIteritemsFix:
    def test_no_iteritems_usage(self): ...                # verify deprecated API removed
```

**v1 reference:** `instabilities/verscharen2016.py` (630 lines), `instabilities/beta_ani.py` (81 lines)

### A.8: Solar Activity Tests (CRITICAL — ~30% coverage)

**File:** `tests/v2_characterization/test_solar_activity.py`

**Current state:** 50 tests for 92 methods. Critical gaps in LISIRD (2/14), extrema_calculator (2/18), SIDC (2/16).

```python
class TestBase:
    # Dual-layer cache — innovation
    def test_cache_stores_data(self, loader): ...
    def test_cache_staleness_detection(self, loader): ...
    def test_cache_refresh(self, loader): ...

    # ID system
    def test_id_construction(self): ...
    def test_id_url_generation(self): ...

    # DataLoader
    def test_data_loading(self, loader): ...
    def test_data_filtering(self, loader): ...
    def test_json_metadata(self, loader): ...

class TestLISIRD:
    # Currently only 2 tests for 14 methods
    def test_data_retrieval(self, lisird): ...
    def test_time_series_format(self, lisird): ...
    def test_interpolation(self, lisird): ...
    def test_missing_data_handling(self, lisird): ...
    def test_multiple_datasets(self, lisird): ...

class TestExtremaCalculator:
    # Currently only 2 tests for 18 methods
    def test_find_maxima(self, calc): ...
    def test_find_minima(self, calc): ...
    def test_cycle_boundaries(self, calc): ...
    def test_interval_index_assignment(self, calc): ...   # innovation
    def test_rise_fall_labeling(self, calc): ...           # innovation
    def test_edge_cases_near_boundaries(self, calc): ...

class TestSIDC:
    # Currently only 2 tests for 16 methods
    def test_sunspot_number_loading(self, sidc): ...
    def test_data_format(self, sidc): ...
    def test_monthly_vs_daily(self, sidc): ...
    def test_smoothing(self, sidc): ...
    def test_cycle_number_assignment(self, sidc): ...

class TestICMECAT:
    # Already decent (10 tests), fill gaps
    def test_fallback_data_sources(self, icmecat): ...    # innovation
    def test_vectorized_containment(self, icmecat): ...   # innovation
    def test_interval_overlap(self, icmecat): ...
```

**v1 reference:** `solar_activity/base.py` (604 lines), `solar_activity/lisird/` (711 lines), `solar_activity/sunspot_number/` (558 lines), `solar_activity/icme/` (452 lines)

### A.9: Plotting Tests (HIGH — ~35-45% coverage)

**File:** `tests/v2_characterization/test_plotting.py` (split into sub-files as needed)

**Current state:** 207 tests for ~280 methods. Major gaps in special labels (14/89), hist2d (4/13), spiral (10/30).

```python
# --- test_plotting_labels.py ---
class TestSpeciesLabelDSL:
    # Currently 14 tests for 89 methods — the biggest gap
    def test_proton_label(self): ...
    def test_alpha_label(self): ...
    def test_combined_species_label(self): ...
    def test_measurement_label(self): ...
    def test_component_label(self): ...
    def test_latex_rendering(self): ...
    def test_units_formatting(self): ...
    # Test each of the 14 specialized label classes
    def test_beta_label(self): ...
    def test_temperature_label(self): ...
    def test_density_label(self): ...
    def test_velocity_label(self): ...
    def test_thermal_speed_label(self): ...
    def test_pressure_label(self): ...
    def test_alfven_speed_label(self): ...

class TestDatetimeLabels:
    def test_year_format(self): ...
    def test_month_format(self): ...
    def test_epoch_format(self): ...
    def test_custom_format(self): ...

# --- test_plotting_hist2d.py ---
class TestHist2D:
    # Currently 4 tests for 1,200 LOC — weakest ratio
    def test_basic_histogram(self, hist2d): ...
    def test_normalization_modes(self, hist2d): ...       # 7 modes — innovation
    def test_bin_edge_strategies(self, hist2d): ...       # innovation
    def test_colorbar(self, hist2d): ...
    def test_log_scale(self, hist2d): ...
    def test_aggregation_pipeline(self, hist2d): ...      # innovation
    def test_cell_filtering(self, hist2d): ...            # innovation
    def test_empty_bins(self, hist2d): ...

# --- test_plotting_spiral.py ---
class TestSpiral:
    # Currently 10 tests for 1,074 LOC
    def test_numba_binning(self, spiral): ...             # innovation
    def test_parker_spiral_overlay(self, spiral): ...
    def test_carrington_projection(self, spiral): ...
    def test_radial_extent(self, spiral): ...
    def test_cell_filter_integration(self, spiral): ...

# --- test_plotting_agg.py ---
class TestAggPlot:
    def test_aggregation_pipeline(self, agg): ...         # innovation
    def test_multiple_aggregations(self, agg): ...
    def test_orbit_mixin(self, orbit_plot): ...           # innovation
```

**v1 reference:** `plotting/labels/` (2,458 lines), `plotting/hist2d.py` (1,200 lines), `plotting/spiral.py` (1,074 lines), `plotting/base.py` (311 lines), `plotting/agg_plot.py` (488 lines)

### A.10: Fitting Tests (GAP-FILL — ~75% coverage)

**File:** `tests/v2_characterization/test_fitting.py` (extends existing tests)

**Current state:** 240+ tests for 188 methods. Best covered, but specific gaps remain.

```python
# --- test_fitting_composite.py (currently 3 tests for 11 methods) ---
class TestComposite:
    def test_gaussian_times_heaviside(self, composite): ...
    def test_gaussian_times_heaviside_plus_heaviside(self, composite): ...
    def test_parameter_count(self, composite): ...
    def test_component_access(self, composite): ...
    def test_tex_info_combined(self, composite): ...     # innovation: TeXinfo on composites
    def test_jacobian(self, composite): ...
    def test_bounds(self, composite): ...

# --- test_fitting_gaussians.py (currently 7 tests for 15 methods) ---
class TestGaussians:
    def test_gaussian_fit(self, gauss): ...
    def test_skew_gaussian(self, skew_gauss): ...
    def test_parameter_names(self, gauss): ...
    def test_tex_info_gaussian(self, gauss): ...         # innovation: TeXinfo
    def test_bounded_fit(self, gauss): ...

# --- test_fitting_texinfo.py (ensure comprehensive coverage) ---
class TestTeXInfoEngine:
    # TeXinfo is a CORE innovation per user
    def test_parameter_annotation(self, tex_info): ...
    def test_fit_result_annotation(self, tex_info): ...
    def test_latex_rendering(self, tex_info): ...
    def test_multi_component_annotation(self, tex_info): ...
    def test_custom_format(self, tex_info): ...

# --- test_fitting_metaclass.py ---
class TestFitFunctionMetaclass:
    def test_docstring_inheritance(self): ...             # innovation
    def test_subclass_gets_parent_docs(self): ...
    def test_method_docs_inherited(self): ...

# --- test_fitting_observation_tracking.py ---
class TestObservationTracking:
    def test_named_tuple_format(self, fit): ...           # innovation
    def test_observation_count(self, fit): ...
    def test_observation_persistence(self, fit): ...
```

**v1 reference:** `fitfunctions/composite.py` (559 lines), `fitfunctions/gaussians.py` (244 lines), `fitfunctions/tex_info.py` (567 lines), `fitfunctions/core.py` (825 lines)

### Phase A-NonCore Execution Strategy

**Parallel agents within A-NonCore:**
- Agent 1: A.7 (instabilities) — smallest, highest priority (0% → target 95%)
- Agent 2: A.8 (solar_activity) — critical gaps to fill (~30% → target 95%)
- Agent 3: A.9 (plotting) + A.10 (fitting) — larger but partially covered

**A-NonCore runs IN PARALLEL with Phase B.** Since A-NonCore tests v1, it has no dependency on the v2 core rewrite. This means:
- No added wall-clock time on the critical path
- v1 gets comprehensive test coverage immediately
- Phase C gets ready-made test suites whenever we decide to rewrite those modules

**Test approach differences from A-Core:**
- A-NonCore tests CAN use pandas assertions (these modules stay pandas-based)
- A-NonCore tests CAN mock network calls (solar_activity has external data sources)
- A-NonCore tests SHOULD use `@pytest.mark.mpl_image_compare` for plotting (visual regression)
- A-NonCore tests inherit existing conftest.py fixtures where available

**Verification:** `pytest tests/v2_characterization/noncore/ -v` passes against v1. All green.

---

## Phase B: Core Rewrite with xarray

**Goal:** Reimplement core/ using xarray, passing ALL Phase A tests.

**Principle:** Change the import in test fixtures from v1 to v2. Run tests. Fix failures.

### B.0: Scaffold + Species System

**Implement:**
- `pyproject.toml` (xarray, pint, pint-xarray, scipy, numpy, matplotlib, numba, joblib)
- `core/base.py` — `_conform_species()`, `_chk_species()` (port from v1)
- `core/species.py` — `SpeciesInfo` (frozen dataclass), `SpeciesRegistry`
- `core/units.py` — pint registry + polytropic index context dict
- mypy strict config

**Pass:** All A.0 + A.6 tests

### B.1: Vector3D + Tensor3D

**Implement:**
- `core/vector.py` — `Vector3D` wrapping `xr.DataArray(dims=[..., "component"])`
  - `__call__("x")` for callable component access
  - `project(other)` for par/per decomposition
  - `rho`, `lat`, `lon` for spherical coordinates
- `core/tensor.py` — `Tensor3D` wrapping `xr.DataArray(dims=[..., "thermal_component"])`
  - `__call__("par")` for callable component access
  - Hard validation: exactly par/per/scalar
- `core/bfield.py` — `MagneticField(Vector3D)` + pressure property

**Pass:** All A.1 tests

**Parallel opportunity:** Vector3D and Tensor3D can be implemented by separate agents.

### B.2: Ion

**Implement:**
- `core/ion.py` — Ion backed by `xr.Dataset`, `cached_property` for Vector3D/Tensor3D
  - All derived quantities as properties (T, pth, cs, rho, anisotropy, entropy, KE flux)
  - Sound speed uses polytropic index context dict

**Pass:** All A.2 tests

### B.3: Spacecraft

**Implement:**
- `core/spacecraft.py` — position, velocity, Carrington coords

**Pass:** All A.4 tests

**Parallel opportunity:** B.2 (Ion) and B.3 (Spacecraft) are independent.

### B.4: Plasma (THE centerpiece)

**Implement:**
- `core/plasma.py` — Full species string spec, `__getattr__`, all physics methods
  - Ions stored in `dict[str, Ion]`
  - All physics methods with calculation chains
  - Scalar w auto-derivation at init
  - `estimate_electrons()`
  - lnlambda/nuc/nc validation chain
  - Data quality logging
  - Save/load with modifier functions

**Pass:** All A.3 tests — this is the critical milestone

**Parallel opportunity within B.4:**
- Agent A: Construction, `__getattr__`, ion access
- Agent B: Single-species methods (n, rho, beta, ca, cs, pth, T)
- Agent C: Multi-species methods (dv, lnlambda, nuc, nc) + estimate_electrons

### B.5: I/O

**Implement:**
- `io/` — Protocol-based, NetCDF default
- `compat/convert.py` — `from_mcs_dataframe()`
- `Plasma.load()` and `Plasma.save()` with modifier support

**Pass:** A.3 I/O tests

### B.6: Alfvenic Turbulence

**Implement:**
- `core/turbulence.py` — Elsasser, sigma_c, sigma_r
  - `,` species syntax preserved
  - `raffaella_version` flag preserved
  - Alfven units conversion pipeline

**Pass:** All A.5 tests

**Parallel opportunity:** B.5 (I/O) and B.6 (Turbulence) are independent.

### Phase B Compatibility Bridge

Existing fitting/plotting/activity/instabilities modules consume v2 output via:

```python
# v2 Plasma returns xr.DataArray
result = plasma.beta("p1")

# Existing modules can use:
result.values          # → numpy array (zero-cost)
result.to_series()     # → pandas Series
result.to_dataframe()  # → pandas DataFrame
```

No changes needed to existing modules. They continue to work.

---

## Full Parallel Execution Plan

```
Phase A-Core (A.0-A.6)  ─────────────────→  Phase B (core rewrite)
  Agent 1: A.0 + A.6                         B.0: Scaffold + Species + Units
  Agent 2: A.1 + A.2                              |
  Agent 3: A.3 + A.4 + A.5                   ├── B.1a: Vector3D  ──┐
         │                                    |                      ├── (PARALLEL)
         │                                    └── B.1b: Tensor3D  ──┘
         │                                             |
         │                                             └── B.1c: BField
         │                                                   |
         │                                        ├── B.2: Ion          ─┐
         │                                        |                      ├── (PARALLEL)
         │                                        └── B.3: Spacecraft   ─┘
         │                                                  |
         │                                             B.4: Plasma
         │                                                  |
         │                                        ├── B.5: I/O          ─┐
         │                                        |                      ├── (PARALLEL)
         │                                        └── B.6: Turbulence  ─┘
         │
         └── Phase A-NonCore (A.7-A.10)  ← RUNS IN PARALLEL with Phase B
               Agent 1: A.7 (instabilities, 0%→95%)
               Agent 2: A.8 (solar_activity, 30%→95%)
               Agent 3: A.9 (plotting) + A.10 (fitting)
```

**Critical path:** A-Core → B.0 → B.1 → B.2 → B.4 → B.6
**A-NonCore is OFF critical path** — runs alongside Phase B at zero added cost
**Wall-clock phases:** 6 (A-Core, then 5 Phase B stages with A-NonCore in parallel)

---

## Phase C: Future Incremental Migration (Out of Scope — But Test-Ready)

These modules work as-is with v2 core. **Phase A-NonCore provides characterization tests** so any future rewrite gets the same TDD guarantee as core.

| Module | Lines | Priority | A-NonCore Tests | Reason to Migrate |
|--------|-------|----------|-----------------|-------------------|
| instabilities/ | 727 | HIGH | A.7 (0%→95%) | Fix `iteritems()` crash, modernize |
| solar_activity/ | 2,496 | MEDIUM | A.8 (30%→95%) | Could benefit from xarray |
| fitting/ | 5,563 | LOW | A.10 (75%→95%) | Accepts arrays, minimal ceremony |
| plotting/ | 7,138 | LOW | A.9 (40%→95%) | Accepts arrays, Numba stays as-is |

Phase C can also include:
- Type annotations for non-core modules
- Docstring backfill for non-core modules
- `__init_subclass__` replacing metaclass in FitFunction
- Adapt A-NonCore tests from pandas assertions to implementation-agnostic (same as A-Core)

---

## Internal Architecture: xarray Replaces M/C/S MultiIndex

### v1 Internal Structure
```
Plasma._data: pd.DataFrame
  columns: MultiIndex(M, C, S)
    ("v", "x", "p1"), ("v", "y", "p1"), ("n", "", "p1"), ("b", "x", ""), ...
  index: DatetimeIndex("Epoch")
```

### v2 Internal Structure
```
Plasma._ds: xr.Dataset
  coords: time, component (x,y,z), species (p1,a), thermal_component (par,per,scalar)
  data_vars:
    velocity:       (time, component, species)
    number_density: (time, species)
    thermal_speed:  (time, thermal_component, species)
    magnetic_field: (time, component)
```

### What Changes (pandas ceremony eliminated)

| v1 Pattern | Count | v2 Equivalent |
|------------|-------|---------------|
| `{s: self.ions.loc[s].X for s in slist}` + `pd.concat()` | 6 | `.sel(species=list)` |
| `.T.groupby(level="S").sum().T` | 9 | `.sum(dim="species")` |
| `.multiply(coeff, axis=1, level="C")` | 6+ | `* coeff` (auto-broadcast) |
| `axis=0` / `axis=1` | 253 | Named dimensions |
| `level=` parameters | 65 | Dimension names |
| Empty string `""` hacks | multiple | Dimensions are optional |

**plasma.py code composition changes:**
- v1: 34% pandas ceremony, 42% physics, 24% method structure
- v2: ~5% xarray ops, 60% physics, 35% method structure + docstrings

---

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Test strategy** | **Characterization tests** | v1 output IS ground truth |
| **Rewrite scope** | **Core only (4,317 lines)** | Where ceremony is worst, rest works as-is |
| **Species string spec** | Preserved exactly | Tested against v1 behavior |
| **`plasma.p1` access** | Preserved (`__getattr__`) | Tested against v1 behavior |
| **`velocity("x")` callable** | Preserved (`__call__`) | Tested against v1 behavior |
| **All physics formulas** | v1-equivalent | Characterization tests guarantee it |
| Data backend | xarray Dataset | Named dims, no ceremony |
| Type annotations | mypy strict | From day 1 in v2 |
| Docstrings | NumPy + examples + LaTeX | In v2 code |
| Return types | Always `xr.DataArray` | Consistent (bridge to pandas available) |
| Ion storage | `dict[str, Ion]` | No pandas dependency |
| Object caching | `cached_property` | Fix v1's per-access creation |
| Units | pint-xarray (opt-in) | Replaces manual conversion factors |
| I/O | NetCDF default + plugins | xarray native |
| Error messages | Include available options | AI self-correction |
| Docstring inheritance | `__init_subclass__` | Modern replacement for metaclass |

## Verification Strategy

### Phase A-Core Verification
- **A-Core completion:** `pytest tests/v2_characterization/core/ -v` passes against v1. ALL GREEN.
- Gate: ALL A-Core tests green before Phase B starts.

### Phase A-NonCore Verification
- **A.7 (instabilities):** `pytest tests/v2_characterization/noncore/test_instabilities.py -v` — ALL GREEN against v1.
- **A.8 (solar_activity):** `pytest tests/v2_characterization/noncore/test_solar_activity.py -v` — ALL GREEN.
- **A.9 (plotting):** `pytest tests/v2_characterization/noncore/test_plotting*.py -v` — ALL GREEN.
- **A.10 (fitting):** `pytest tests/v2_characterization/noncore/test_fitting*.py -v` — ALL GREEN.
- A-NonCore can complete while Phase B is in progress (no blocking dependency).

### Phase B Verification
- **Phase B.0:** Species spec tests pass with v2 implementation
- **Phase B.1:** Vector/Tensor tests pass with v2
- **Phase B.2-B.3:** Ion/Spacecraft tests pass with v2
- **Phase B.4:** ALL plasma characterization tests pass — **critical milestone**
- **Phase B.5-B.6:** I/O + Turbulence tests pass
- **Final:** `pytest tests/v2_characterization/core/ -v` passes against v2. ALL GREEN.
- **Every sub-phase:** `mypy --strict`, `--cov-fail-under=95`
- **Numerical equivalence:** `np.testing.assert_allclose(v2_result.values, v1_expected, rtol=1e-10)`

### Full Project Verification
- `pytest tests/v2_characterization/ -v` — ALL tests (core + noncore) pass. Full codebase characterized.

## Critical v1 Files to Reference

| v1 File | Lines | What to Port |
|---------|-------|-------------|
| `core/base.py:136-175` | — | `_conform_species`, `_chk_species` |
| `core/plasma.py` (full) | 1,901 | Species spec, `__getattr__`, all physics methods |
| `core/plasma.py:744-762` | — | Scalar w auto-calculation |
| `core/plasma.py:1353-1552` | — | lnlambda/nuc/nc validation chain |
| `core/plasma.py:1639-1727` | — | `estimate_electrons` |
| `core/plasma.py:1776-1822` | — | `build_alfvenic_turbulence` with `,` syntax |
| `core/plasma.py:296-397` | — | Save/load modifier functions |
| `core/ions.py` | 311 | Single-species physics, lazy properties |
| `core/vector.py` | 328 | Vector ops, `__call__`, BField |
| `core/tensor.py` | 90 | par/per/scalar contract, `__call__` |
| `core/units_constants.py` | 199 | Conversion factors, polytropic index |
| `core/spacecraft.py` | 256 | Position, Carrington coords |
| `core/alfvenic_turbulence.py` | 804 | Elsasser, `,` syntax, `raffaella_version` |
