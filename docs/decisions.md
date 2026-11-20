<!--
Spent-When: PERMANENT(the repository is archived or retired)
Supersedes: docs/dispatches/findings-coherence-and-tooling-review-2026-11-04.md,docs/dispatches/plan-coherence-cleanup-2026-11-04.md
-->

# Decisions, findings and open items

The author's rulings in force (D), the findings later work builds on (C), and the questions
left open. `GOVERNANCE.md` states why SolarWindPy exists; this file states what has been
decided and found. A ruling that was carried out once and constrains nothing further lives in
git history, not here. A retired entry's number is not reused.

Sources cited below:

- **Rulings page**: the author's per-finding notes on the 2026-11-04 coherence review,
  https://claude.ai/artifact/WgvgiS3Ms4S3T3UCpEK5S4.
- **Waves ruling n**: § Scope "Rulings" of the dispatch at
  `8cfc8dbd:docs/dispatches/dispatch-coherence-cleanup-waves-2026-11-18.md`.
- **The author, date**: an answer given in a working session on that date, recorded in the
  commit that carried it out where one exists.

## Decisions in force

### API and names

| # | decision | ruling | source |
|---|---|---|---|
| D1 | Breaking changes before 1.0 | **Made outright, with no alias or deprecation shim**; each is listed in `CHANGELOG.md` | rulings page, 2026-11-04; waves ruling 28 |
| D2 | One name per concept | **One canonical name, no aliases. A short name is canonical when it equals the data label** (attribute = Series `.name` = `M` label). A name uses the field's standard symbol where one exists, otherwise a plain word | rulings page, 2026-11-04 |
| D3 | The position accessor | **`Spacecraft.pos`**, by D2: position is stored under the `M` label `pos`. This supersedes the earlier "the position vector is `r`" | the author, 2026-11-19 (`a429779b`, shipped in 0.6.0) |
| D4 | Names reused across subpackages | **Judged by role, not string**: `Base` and `tools` stay, and `plotting.labels.composition.Ion` keeps its name. One name meaning different things among siblings is the defect. **`rho` stays in both its contexts**: on a vector it is the standard symbol for the xy-plane magnitude, distinct from `mag` (the x, y, z magnitude), and on a species it is mass density | rulings page; waves ruling 8; the author, 2026-11-19 (F74) |
| D5 | Exception kinds | **`TypeError` for a wrong type, `ValueError` for a bad value, `InvalidParameterError` in fitfunctions.** Caller input is never checked with `assert` | waves ruling 16 |
| D6 | Plot constructors | **Data variables positional, every setting keyword-only.** A data variable holds one value per point, so a scalar raises `TypeError`; a constant marker size or opacity goes to `make_plot` as `s` or `alpha` | waves ruling 11; the author, 2026-11-19 (`5a0573b7`) |
| D7 | Plot returns and ownership | **Plot objects own their data and binned results; methods return `(ax, artists..., guides)`** in that order | rulings page, 2026-11-04 |
| D8 | Clip settings | **`True` clips both tails at 0.05% and 99.95%; `False`/`None` none; a `(lower, upper)` pair; `"l"` and `"u"` for one tail; the per-axis mapping composes with each. `"lower"`, `"upper"` and `"both"` are removed.** One code path, the out-of-memory fallback included. The full contract is `solarwindpy.plotting.base.Base.clip_data` | waves ruling 5; the author, 2026-11-19 (O2) |
| D9 | Fit parameters | **Added constants are `y0`, shifts `x0`; the exponent first and the amplitude `A` last.** Every fit exposes one common results form | rulings page, 2026-11-04 |
| D10 | Hinge fits | **One guess interface, `guess_xh` on the base; every hinge class starts from the fit in DOI 10.3847/2041-8213/adb48e** | rulings page, 2026-11-05 |
| D11 | Label names | **Each registry entry has a short title-case display name** (quantity only); `publication_format` is set per label, with a global default the label overrides | rulings page, 2026-11-05 |
| D12 | Logging | **Each class logs under `solarwindpy.<module>.<Class>`; the library adds no handler or level** | waves rulings 12 and 13 |
| D13 | `set_frame_name` | **Accepts only the spacecraft and frames it supports, and raises `NotImplementedError` naming them**, because frame transformations are not general | rulings page, 2026-11-04 |
| D29 | Unused code | **Deleted, not fixed** | rulings page, 2026-11-04 |
| D30 | Design and docstrings Claude wrote | **Treated as suspect and reconciled to the author's forms.** Where the author left parallel structures, Claude proposes a shared one after interviewing the author about intent | rulings page, 2026-11-04 |
| D31 | Plot normalizations | **A count gives the count PDF; a `"sum"` of z gives each cell's share of total z per unit area (z < 0 raises); any other aggregation gives value × count PDF. `w`, `wc`, `wr` are the per-cell forms; `t`, `c`, `r` divide by the peak (max absolute value for signed data).** `allowed_axnorm` is the one list of keys | rulings page, 2026-11-05 |
| D32 | Contours | **`SpiralPlot2D` gets no contour smoothing (its adaptive mesh is its smoothing); `Hist2D` keeps `gaussian_filter_std`.** Every contour method interpolates in plot coordinates, each axis scaled to its span | rulings page, 2026-11-04 |
| D33 | Units and labels | **One quantity registry, `solarwindpy.core.quantities`**: display unit, SI factor and TeX symbol per canonical name, read by `core` to convert and by `plotting` to label | rulings page, 2026-11-04 |
| D34 | Trend fits | **Two levels: a 1-D fit in each column of a 2-D histogram, then a fit to one parameter's trend across columns**, which selects x, y and yerr by name from the per-column results | rulings page, 2026-11-04 |
| D35 | The data model's direction | **Seams first; pint-pandas is rejected** (it drops units on rolling, copies on `.xs` and fails `to_hdf`); xarray waits for O16 | rulings page, 2026-11-04 |
| D37 | Fluctuation vectors | **`AlfvenicTurbulence.v`, `.b`, `.zp` and `.zm` are plain `Vector`s, never `BField`s: fluctuations are not fields, so field quantities such as magnetic pressure do not apply** | the author, 2026-11-20 (F76; `a22102c7`, `386d3817`) |
| D38 | The two `beta` inputs in verscharen2016 | **`StabilityContours` builds the instability threshold curves on a grid of beta values (a numpy array); `StabilityCondition` classifies measured beta and anisotropy per observation (pandas Series). Different jobs, so different input types** | the author, 2026-11-20 (F112, closed) |

### Physics and data

| # | decision | ruling | source |
|---|---|---|---|
| D14 | Missing data in fixed-input quantities | **NaN where any input is missing, everywhere, `Spacecraft` included**: `Plasma.nc` is NaN when a position component is missing, and the Raffaella polarity and field are NaN at a missing component. Species totals follow `Plasma._SPECIES_COMBINE` (ruling of 2026-11-10, guarded by `tests/core/test_plasma_species_combine.py`). A change to a `skipna` states the rule it follows first | rulings page, 2026-11-04 |
| D15 | Temperature of several species | **The plain sum `T_a + T_p`**; no density-weighted total temperature | issue #497, 2026-11-05 |
| D16 | Specific entropy | **`s = p rho^(-5/3)` in eV cm² m_p^(-5/3)**, as Xu and Borovsky 2015 (DOI 10.1002/2014ja020412), cited beside Siscoe 1983 | rulings page, 2026-11-04 |
| D17 | Sound speed | **`Ion.cs` uses the CGL indices γ∥ = 3 and γ⊥ = 2, scalar 5/3** (DOI 10.1098/rspa.1956.0116); **`Plasma.cs("p1+a")` is the combined-fluid speed sqrt(γ Σp / Σρ)** | waves rulings 1 and 2 |
| D18 | Solar rotation rate | **2π / 25.38 d, the sidereal Carrington period** (Thompson 2006, DOI 10.1051/0004-6361:20054262, §2.2) | waves ruling 4 |
| D19 | Extremum kind of a sunspot number | **Max where ssn ≥ half the cycle's maximum**, as the code and its test classify | the author, 2026-11-19 (`dff07f07`) |
| D20 | Residuals | **Observed minus fitted, in one home, `FitFunction.residuals`** | rulings page, 2026-11-04 |
| D21 | HDF5 | **PyTables, no h5py; numexpr and bottleneck stay** | rulings page, 2026-11-04 |
| D22 | External facts | **SILSO cycle extrema stay a hand-maintained CSV with an opt-in drift test. ICMECAT expects v23 and probes the next 5 versions only on a 404. Asplund 2021 has no drift test. ICMECAT's rules of the road are linked, never copied** | rulings page, 2026-11-04; waves ruling 15 |
| D23 | Download cache | **`astropy.utils.data.download_file` with `pkgname="solarwindpy"`**, refreshed after each source's freshness window, falling back to the cached copy on a failed download | rulings page, 2026-11-04 |

### Repository and release

| # | decision | ruling | source |
|---|---|---|---|
| D24 | Pointers in live files | **Name code and tests by symbol (`module.symbol`, `file.py::test_name`), never by line number**; `tests/test_no_line_pointers.py` guards it | rulings page, 2026-11-04 |
| D25 | Spent-When in the package tree | **Shipped modules carry no inline header; a new module gets a sidecar**; tests and docs carry the inline form | waves ruling 27 |
| D26 | Creating the conda env | **`pyproject.toml` is the one dependency list; `solarwindpy.yml` is generated from it by `pyproject2conda` (settings in `[tool.pyproject2conda]`) and held by `tests/test_conda_env.py`. Every dependency comes from conda-forge; pip only registers the checkout (`pip install -e . --no-deps --no-build-isolation`)** | waves ruling 18; the author, 2026-11-20 (F196) |
| D27 | The citation file | **`CITATION.cff` names the current release (`version`, `date-released`), set by the release procedure** | the author, 2026-11-19 |
| D28 | The next release | **0.7.0 follows the review's remaining items, done on 2026-11-20** (`50b6eed1` to `59b6f7a0`); the multi-species design (O3, O13), package J (O15) and the xarray spike (O16) go to later releases | the author, 2026-11-19 |
| D36 | `master` protection | **Minimal: a GitHub ruleset blocks force-push and deletion; no pull-request requirement** | rulings page, 2026-11-04 |

## Findings

**C1: the 2026-11-04 review's 206 findings, checked against master at `ed19fe64`.** On
2026-11-19, 162 are fixed, 5 closed by a ruling, 29 superseded (their code was deleted) and
14 open, of which 4 are partly fixed. Each fixed row was checked on master and, as its positive
control, at the review's commit `7b6d99fe`. Most fixing commits cite no finding ID, so a search
of commit messages undercounts: search the code (`git log -S`). Two commits cite each other's
finding (`069d7a7c` and `123abf2b`). The open ones are below.

**C2: a loader's `url` and an indicator ID's `url` are two quantities.** A `DataLoader`'s url
can be a local path (its doctest passes one), so the review's F147 is not a defect.

**C3: `ICMECAT` joined the subpackage's shared parts.** It inherits the logger mixin
(`solarwindpy.tools._WithLogger`) and uses `solarwindpy.solar_activity.cache`, which closes
F139; whether it should subclass a `DataLoader` is a structure question nobody has asked for.

**C4: `tables` installs from a wheel that bundles HDF5.** At the lowest declared version on
Python 3.12 pip resolves `tables-3.10.1-cp312-cp312-manylinux...whl`, and at 3.11.1 an abi3
wheel for every Python from 3.11; so no workflow installs HDF5 with apt (`e6a7bad8`,
`ed19fe64`). If a `tables` release drops the wheel, the Linux jobs fail at install.

**C5: specific entropy before `baae8ffc` (2026-09-27) is 9.2 times too small.** The units
factor was wrong until then; analyses made earlier need checking.

## Open items

| # | item | who decides | recommendation |
|---|---|---|---|
| O3 | F75: `Ion.w` returns a `Tensor`, `Plasma.w` a `DataFrame` | the author | settle with O13 |
| O13 | The multi-species `Vector`/`Tensor` design: one species' thermal speed comes back as a `Tensor`, two species' as a DataFrame | the author, by interview; not yet ready to decide (2026-11-19) | |
| O15 | Package J, deferred: strip headers and sidecars at build, inline module headers, the declaration backlog, and a Spent-When member tied to a release tag (session plugin work) | the author (scheduling) | |
| O16 | The xarray-native spike (`spike/xarray-2026-11`) | the author | parked until the rest of this list is settled (rulings page, 2026-11-04) |
