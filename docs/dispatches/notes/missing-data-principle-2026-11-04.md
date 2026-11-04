<!--
Spent-When: MARKED(<self>)
Supersedes: none
-->

# Phase A: the missing-data principle (F59, F63, F66)

## Where the rule already lives

The rule is not new to extract from scratch. It is decided and documented for `Plasma` in
`docs/source/missing_data.rst`, from the author decisions recorded in
`docs/dispatches/batch-test-quality-fixes-2026-10-02.md` under `### scalar-w-nan`, and applied by
commits 8321b648 (scalar w NaN where both parts missing), 098f2bd1 (empty species sums NaN in
`heat_flux` and `Wk`), 1b7ce932 ("apply the two-level missing-data rule across Plasma") and
62a5d911 (species masking; pair quantities and density totals). Those state three rules:

1. Within a species, a value needs every component it is built from.
2. Across species, a total uses the species present and is NaN only where none is.
3. A pair quantity (`nuc`'s W_ab and density ratio, `pdynamic`'s reduced mass) needs both species.

`Plasma.set_data` also masks a whole species to NaN at any time one of its n, v or w components
is missing (`plasma.py:988` to `:1010`), so within a species the parts stand or fall together.

The rst is scoped to `Plasma`. Whether it governs `Spacecraft` and `AlfvenicTurbulence`, which
have no species axis, is the real ruling behind F63 and F66 (see Decisions).

## Inventory

Classified by what the reduction runs over. "Kind" separates an additive total over independent
populations or samples from a function of a fixed set of inputs. Lines are as of HEAD 9ef459ed.

| Site | Quantity | Reduces over | Kind | Missing-data choice | Follows rule? |
|---|---|---|---|---|---|
| `vector.py:93` | `Vector.mag` | components | fixed inputs | `skipna=False` | yes |
| `vector.py:118` | `Vector.rho` | components x, y | fixed inputs | `skipna=False` | yes |
| `vector.py:278`, `:282` | `Vector.project` par, per | components | fixed inputs | `skipna=False` | yes |
| `vector.py:313` | `Vector.cos_theta` | components | fixed inputs | `skipna=False` | yes |
| `ions.py:228` | `Ion.anisotropy` | par, per | fixed inputs | `skipna=False` | yes |
| `plasma.py:938` | scalar w in `set_data` | par, per of one species | fixed inputs | `skipna=False` | yes |
| `plasma.py:1458` | `pdynamic` dv^2 per species | components | fixed inputs | `skipna=False` | yes |
| `plasma.py:1467` | `pdynamic` dv^2, two species | components | fixed inputs | `skipna=False` | yes |
| `plasma.py:1471`, `:1472` | `pdynamic` reduced mass | pair of species | fixed inputs (pair) | `skipna=False` | yes |
| `plasma.py:1583` | `afsq` B^2 | field components | fixed inputs | `skipna=False` | yes |
| `plasma.py:1764` | `nuc` W_ab | pair of species | fixed inputs (pair) | `skipna=False` | yes |
| `plasma.py:1785` | `nuc` mass-density ratio | pair of species | fixed inputs (pair) | `skipna=False` | yes |
| `plasma.py:1919` | `vdf_ratio` drift term | components | fixed inputs | `skipna=False` | yes |
| `alfvenic_turbulence.py:392`, `:396` | raffaella `r_rtn`, `rho_rtn` | position components | fixed inputs | `skipna=False` | yes |
| `plasma.py:1049` | `number_density` total | species | additive total | `skipna=skipna` (default True), `min_count=1` | yes; only reduction whose choice is a caller argument |
| `plasma.py:1081` | `mass_density` total | species | additive total | `min_count=1` | yes |
| `plasma.py:1115` | `thermal_speed` (raises for `+` totals) | species | additive total | `min_count=1` | yes |
| `plasma.py:1155` | `pth` total | species | additive total | `min_count=1` | yes |
| `plasma.py:1186` | `temperature` total | species | additive total | `min_count=1` | yes |
| `plasma.py:1368` to `:1372` | `_species_weighted_mean` (velocity, electrons) | species | weighted mean | species dropped from numerator and denominator where any component or weight is missing; `min_count=1` | yes |
| `plasma.py:1460` | `pdynamic` species sum | species | additive total | `min_count=1` | yes |
| `plasma.py:1996` | `estimate_electrons` n_e | species | additive total | `min_count=1` | yes |
| `plasma.py:2089` | `heat_flux` total | species | additive total | `min_count=1` | yes |
| `plasma.py:2222` | `kinetic_energy_flux` total | species | additive total | `min_count=1` | yes |
| `plasma.py:1271` | `Plasma.anisotropy` one string | par, per (of a species or of a species total) | fixed inputs | default `skipna=True`, no `min_count` | **no (F59)** |
| `plasma.py:1269` | `Plasma.anisotropy` several species | par, per per species (groupby S) | fixed inputs | default `skipna=True` | **no (F59)** |
| `spacecraft.py:182` | `Spacecraft.distance2sun` | position components | fixed inputs | default `skipna=True` | **no (F63)** |
| `alfvenic_turbulence.py:200`, `:211`, `:222`, `:235` | `e_plus`, `e_minus`, `kinetic_energy`, `magnetic_energy` | components | fixed inputs | default `skipna=True` | **no (F66)** |
| `alfvenic_turbulence.py:283` | `cross_helicity` | components (dot product) | fixed inputs | default `skipna=True` | **no (new, not in F66)** |
| `alfvenic_turbulence.py:412` | raffaella `polarity` | components x, y of v.b | fixed inputs | default `skipna=True` | **no (new; raffaella branch, see F64)** |
| `alfvenic_turbulence.py:401` | raffaella `r` | position components | fixed inputs | inherits `distance2sun` | inherits F63; disagrees with `:392` in the same formula |
| `alfvenic_turbulence.py` rolling `agg("mean")` | background v, b | rows over time | additive over samples | `min_periods=5` default | yes (time level) |
| `plotting/agg_plot.py:406`, `:674`; `binned.py:228`, `:283`; `hist1d.py:210`; `scatter.py:88`; `spiral.py:874` | bin statistics, plot inputs | rows / bins | samples | `dropna` / `notna` filter | yes (time or bin level) |
| `fitfunctions/hinge.py:774` | combined slope | two slope estimates | estimates | `nanmedian`, NaN if both NaN | yes (empty gives NaN) |
| `fitfunctions/trend_fits.py:168` | failed-fit index | rows | bookkeeping | `dropna` | not a measurement reduction |
| `tools/__init__.py:83`, `:84`, `:106` | p1/p2 swap | rows | bookkeeping | `dropna(how="all")` | not a measurement reduction |
| `solar_activity/*` (`sidc.py:366`, `icmecat.py`, `base.py:320`, `:550`) | catalog and index series | rows over time | samples / bookkeeping | `dropna`, `isna` guards | time level |
| `plasma.py:1751`, `:1754` | `nuc` charge and mass products | constants table | none | n/a | excluded: no measured data |
| `abundances.py:191`, `base.py:200`, `instabilities/verscharen2016.py:560`, `fitfunctions/tex_info.py:430`, `plotting/binned.py:591` | input validation, comments | n/a | n/a | `isna` checks | excluded: not a reduction |

## The principle

Stated in positive form, each with the check that would show it failing.

**P1. A function of a fixed set of inputs needs every input.** A magnitude, a dot product, a
scalar built from par and per, a ratio, or a pair quantity is NaN at any time one of its inputs is
missing (`skipna=False`). Check: mask one component (or one species of a pair) at one row; the
result at that row must be NaN, and equal to what `Vector.mag` or `Ion.anisotropy` gives there.

**P2. Only an additive total over independent populations may be partial.** A species total, or a
weighted mean over species, uses the species present and renormalizes weights over them
(`min_count=1`); a statistic over time or bins uses the samples present, gated by
`min_periods` or a count. Check: mask one species at a row; the total must equal the other
species' value there, and the weighted mean must equal the present species' own vector.

**P3. An empty reduction is NaN, never the reduction's identity.** Check: with every input missing
at a row, the result is NaN, not 0 (sum) or 1 (product). pandas gives 0 and 1 by default:
`DataFrame.sum(axis=1)` of an all-NaN row is 0.0 and `.prod(axis=1)` is 1.0 (verified).

The levels compose in order: P1 within each species first, then P2 across species on those
results. That is the two-level diagram in `missing_data.rst`. The axis alone does not decide the
choice, because the pair rule reduces over species with `skipna=False`; what decides it is whether
the reduction is an additive total over independent populations (P2) or a function of a fixed set
of inputs (P1).

Epistemic status. I verified that every `core/` reduction except the six flagged sites follows
P1 to P3. I infer the extension to `Spacecraft` and `AlfvenicTurbulence` from these premises:
`Vector.mag`, `Vector.rho`, `Vector.project` and `Vector.cos_theta` all use `skipna=False`; and
`alfvenic_turbulence.py:392` and `:396`, in F66's own file, use `skipna=False` over position
components. The rst itself says nothing about objects without a species axis.

## Counterexamples to the candidate "components skipna=False, species skipna=True"

- The pair rule. `nuc` (`plasma.py:1764`, `:1785`) and `pdynamic`'s reduced mass
  (`plasma.py:1471`) reduce over species with `skipna=False`. A pair quantity is a function of two
  fixed inputs, not a total. Hence P1 and P2 are keyed on kind, not axis.
- `number_density(skipna=...)` (`plasma.py:1022`). The across-species choice is a caller argument
  here and nowhere else; `skipna=False` there means "require every named species". It is the one
  place the package lets a caller turn a P2 total into a P1 quantity.
- `thermal_speed("a+p1")` raises. Thermal speeds do not add across species, so not every species
  reduction is allowed to be partial; some are refused outright.
- Species totals are not plain `skipna=True`: every one carries `min_count=1` (P3). A bare
  `skipna=True` total is the pattern 098f2bd1 and 8321b648 fixed.

I found no `core/` counterexample to P1 to P3 other than the six flagged sites.

## Demonstrations

Script: `/private/tmp/claude-501/-Users-blalterman-observatories-code-SolarWindPy/a04e7fdc-c916-4938-acad-74b79ff7234b/scratchpad/md_demo.py`,
run with `conda run -n solarwindpy python`. The example plasma has three rows and species
`a, e, p1, p2`. I masked p1's `w_par` at row 0 (p1 masked), a's `w_per` at row 1 (a masked), and
both at row 2 (neither present). All values below are verified output.

| Call | row 0 (a only) | row 1 (p1 only) | row 2 (none) |
|---|---|---|---|
| `Plasma.anisotropy("p1")` | 1.0 | 1.69 | 1.0 |
| `plasma.p1.anisotropy` | NaN | 1.69 | NaN |
| `Plasma.anisotropy("a+p1")` | 5.4444 | 1.69 | 1.0 |
| same, component product with `skipna=False` | 5.4444 | 1.69 | NaN |
| `Plasma.anisotropy("a","p1")`, column a | 5.4444 | 1.0 | 1.0 |
| `Plasma.anisotropy("a","p1")`, column p1 | 1.0 | 1.69 | 1.0 |
| `plasma.a.anisotropy` | 5.4444 | NaN | NaN |

Across all rows of `pth("a+p1")`, no row has `par` missing with `per` present or the reverse
(0 and 0): species masking guarantees a total's par and per come from the same species set.

F63: with PSP HCI position x masked at row 0, `distance2sun` is 2.9136e10 m while
`position.mag` is NaN. Row 1, unmasked, is finite in both.

F66: with dv_x masked at row 0 and db_z at row 1, `e_plus`, `e_minus`, `kinetic_energy`,
`magnetic_energy`, `cross_helicity` and `total_energy` are all 0.0 at every row. The
`skipna=False` form of the kinetic energy gives NaN at row 0. The other values are 0 because the
three rows are years apart, so each sits alone in its 15 min rolling window and every fluctuation
is zero; the contrast that matters is 0.0 against NaN at the masked row.

## Verdicts

**F59, `Plasma.anisotropy`: breaks P1 and P3; the author's purpose is kept by the fix.** The
product at `plasma.py:1271` reduces over par and per, not over species. The species partiality the
author wants for `"a+p1"` already happens upstream, in `pth`'s `min_count=1` (`plasma.py:1155`).
With `skipna=False` on the component product, `"a+p1"` still gives 5.4444 where only alphas are
present and 1.69 where only protons are; only the row with no species changes, from 1.0 to NaN.
So the correction and the finding agree: `skipna=False` on the par/per product, and the total
stays partial over species. The single-species call and the `("a","p1")` branch (`:1269`) return
1.0 for a masked species, the empty product, which nothing in the author's note defends. The
finding's framing ("contradicts the scalar-w-nan rule") is fair for the component product, but
not if read as a ban on partial species totals.

**F63, `Spacecraft.distance2sun`: breaks P1 and P3, if P1 governs objects without species.**
It is the magnitude of one position vector, a function of three fixed inputs. A missing x gives a
finite, wrong distance (2.9e10 m against NaN). It also disagrees with
`alfvenic_turbulence.py:392`, which computes the same r with `skipna=False` and then uses
`distance2sun` at `:401` in the same formula. Mirror `Vector.mag`.

**F66, `AlfvenicTurbulence` energies: breaks P1 and P3, under the same condition.** Each energy is
half the squared magnitude of one fluctuation vector, a fixed-input function; a missing component
gives a partial energy (0.0 against NaN in the demo). The author's earlier note ("skipna=False
should hold") matches P1. `cross_helicity` (`:283`) is a dot product with the same default and
belongs with F66. `total_energy`, `residual_energy` and the normalized forms add or divide
Series, so they propagate NaN once the four energies are fixed.

**New, `polarity` (`alfvenic_turbulence.py:412`): breaks P1; not ruled.** It sums v_x b_x +
v_y b_y with the default, so a missing component gives the sign of one term. It sits in the
raffaella branch, whose behaviour F64 says a merged decision fixes, so this is flagged for the
author only.

## Decisions for the author

Decided already (cite, do not reopen):

- **All-NaN species total.** NaN, not 0 (`min_count=1`): 098f2bd1, 8321b648, 62a5d911, and
  `missing_data.rst` "NaN only when no species is present".
- **Weighting when one species is missing.** The species leaves both numerator and denominator
  (`_species_weighted_mean`, `plasma.py:1368`): 1b7ce932.

Open:

- **D1, empty product.** Should an anisotropy with no species present be NaN, as P3 says, or 1.0
  (isotropic) as today? Options: (a) NaN via `skipna=False` on the par/per product, at both
  branches; (b) `min_count=2` on the product, same result here; (c) keep 1.0 and document it.
  Recommendation: (a), which mirrors `Ion.anisotropy`.
- **D2, scope.** Does the Plasma rule govern objects with no species axis (`Spacecraft`,
  `AlfvenicTurbulence`, `Vector`)? Options: (a) yes, P1 applies to every vector or tensor in
  `core/`, and the rst gains a sentence saying so; (b) no, those classes keep pandas defaults and
  `Vector.mag` is the exception; (c) yes, and `Spacecraft.set_data` also masks the whole position
  where any component is missing, the analog of species masking. Recommendation: (a). F63 and F66
  follow from it.
- **D3, partial totals carry no record of who contributed.** `"a+p1"` anisotropy where alphas are
  missing is simply p1's anisotropy; a protons-only `heat_flux("a+p1")` is 0 (098f2bd1). A time
  series of totals mixes rows built from different species sets with no flag. Options: (a) accept,
  as `missing_data.rst` does; (b) document per method that a partial total equals the present
  species' value; (c) offer a species-count or coverage series beside totals; (d) extend
  `number_density`'s `skipna` argument to the other totals so a caller can require every species.
  Recommendation: (a) now, (d) if a caller asks.
