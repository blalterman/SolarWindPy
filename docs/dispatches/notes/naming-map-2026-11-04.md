<!--
Spent-When: MARKED(<self>)
Supersedes: none
-->

# Phase A: naming rule test (F52, F73, F74, F79, F110)

Read-only. Everything below was measured on `swp.examples.load_plasma()` at the current
`master`, with the label tables in `solarwindpy/plotting/labels/base.py` and the `Units`
dataclass in `solarwindpy/core/units_constants.py`.

## Outcome

The rule holds only after two repairs, and even then two concepts break it.

As stated ("the attribute name, the returned Series' `.name`, and the M-level column label
are one string"), the rule fails at the `Plasma` layer for every quantity: `Plasma` methods
name their Series after the species (`'p1'`, `'p1+a'`), because the result is concatenated
over the `S` level. Read literally, every `Plasma` method is an alias. The author's own
example matches the `Ion` layer instead: `plasma.p1.mass_density.name == 'rho'`.

The repaired rule: **a name is canonical when it equals the `.name` of the single-species,
single-quantity Series (the `Ion`, `Vector`, `BField` or `Spacecraft` layer), the `Units` key,
and the TeX key, at the level (M or C) the quantity lives on. `Plasma` inherits the name from
`Ion`.** Under that rule 36 public members are deleted, 4 public members and 1 public
keyword are renamed, 18 public members need an author decision, and 17 label, `Units` or
`.name` strings change.

It still fails to give one name per concept in two places: `Vector.mag` and `Vector.r` are
the same quantity and each passes its own layers; and `S` (specific entropy) passes every
layer while colliding with the `S` level name, the sulfur species code, and species access.

## What the data model actually stores

The example plasma stores four M labels: `b`, `n`, `v`, `w` (columns
`('n','','p1')`, `('w','par','p1')`, and so on). The spacecraft frame stores `pos`, `v`,
`carr`. Nothing else has a stored M label. For every derived quantity (`rho`, `pth`, `cs`,
`T`, `q`, `Wk`, `S`, ...) the "M-level label" is inferred from three other homes: the
`Ion`-layer Series `.name`, the `Units` key, and the TeX key in `_templates` /
`_trans_units`, which is the M key a user passes to `TeXlabel((M, C, S))`. These three are
the layers the rule can actually test.

Two layers are weaker than they look:

- `.name` on a DataFrame return (`Ion.temperature` "T", `Ion.pth` "pth", `Ion.cs` "cs") is
  an ad hoc attribute. I verified `(plasma.p1.temperature * 1).name` raises `AttributeError`: it does not
  survive arithmetic, so it is not a real layer. On a Series it survives
  (`(plasma.p1.rho * 1).name == 'rho'`, verified).
- Every `AlfvenicTurbulence` Series and `Tensor.magnitude` return `.name = None`
  (verified), so the `.name` leg cannot decide them; only the TeX key can.

## Classification key

(a) equals the data label at every layer that exists for it: canonical. (b) a long
descriptive name with a separate short data label: two homes. (c) a pure alias, a one-line
property or method whose docstring says "Shortcut" or "Alias for" (taken from
`git grep -n -B3 -E 'Shortcut|Alias for' -- solarwindpy/core`). (d) one name meaning
different things in sibling classes. "Rule silent" marks container accessors and verbs,
which carry no data label.

Note that many current (c) aliases are the names the rule keeps: `n`, `rho`, `v`, `w`, `cs`,
`Wk`, `pb`, `zp`, `sigma_c`. Under the rule the alias becomes the definition and the long
name is deleted.

## Full map

| Class | Name | Class. | Returns | Observed `.name` | `Units` key | TeX key (level) | Stored M | Under the rule | Note |
|---|---|---|---|---|---|---|---|---|---|
| Plasma | `n` | c | Series/DataFrame by S | species | n | n (M) | n | keep | becomes the definition |
| Plasma | `number_density` | b | same as n | species | n | n (M) | n | delete |  |
| Plasma | `rho` | c | Series/DataFrame by S | species | rho | rho (M) | none | keep | conflicts with F74 note |
| Plasma | `mass_density` | b | same as rho | species | rho | rho (M) | none | delete |  |
| Plasma | `v` | c | Vector | n/a | v | v (M) | v | keep |  |
| Plasma | `velocity` | b | Vector | n/a | v | v (M) | v | delete |  |
| Plasma | `w` | c | DataFrame (C) or (C,S) | n/a | w | w (M) | w | keep |  |
| Plasma | `thermal_speed` | b | DataFrame | n/a | w | w (M) | w | delete | Ion returns Tensor (F75) |
| Plasma | `b` | c | BField | n/a | b and bfield | b (M) | b | keep |  |
| Plasma | `bfield` | b | BField | n/a | bfield | b (M) | b | delete | Units.bfield merges into Units.b |
| Plasma | `pth` | a | DataFrame | n/a | pth | pth (M) | none | keep |  |
| Plasma | `beta` | a | DataFrame | n/a | beta | beta (M) | none | keep |  |
| Plasma | `ca` | a | Series by S | species | ca | ca (M) | none | keep |  |
| Plasma | `caani` | a | Series | a+p1 | none (v units) | caani (M) | none | keep |  |
| Plasma | `afsq` | a | Series by S | species | none | afsq (M) | none | keep |  |
| Plasma | `lnlambda` | a | Series | p1,a | lnlambda | lnlambda (M) | none | keep |  |
| Plasma | `nuc` | a | Series | p1+a | nuc | nuc (M) | none | keep |  |
| Plasma | `nc` | a | Series | p1+a | nc | nc (M) | none | keep |  |
| Plasma | `dv` | a | Vector | n/a | dv | dv (M) | none | keep |  |
| Plasma | `cs` | c | Series by S | species | cs | cs (M) | none | keep | conflicts with F79 note |
| Plasma | `sound_speed` | b | Series by S | species | cs | cs (M) | none | delete |  |
| Plasma | `temperature` | b | DataFrame | n/a | temperature | T (M) | none | rename:T | Ion DataFrame .name is T |
| Plasma | `anisotropy` | b | Series by S | species | none | R (M), C=T or P | none | undecided | Ion .name is RT |
| Plasma | `pdynamic` | b | Series | pdynamic | none | pdv (M) | none | undecided | .name and TeX key disagree |
| Plasma | `pdv` | c | Series | pdynamic | none | pdv (M) | none | undecided |  |
| Plasma | `heat_flux` | b | Series/DataFrame by S | species | qpar | q (M), C=par | none | undecided | F52 |
| Plasma | `qpar` | c | same | species | qpar | q (M), C=par | none | undecided | F52 |
| Plasma | `kinetic_energy_flux` | b | Series/DataFrame by S | species | kinetic_energy_flux | Wk (M) | none | delete |  |
| Plasma | `Wk` | c | same | species | kinetic_energy_flux | Wk (M) | none | keep | Units key renames to Wk |
| Plasma | `specific_entropy` | b | Series named S, DataFrame by S | S | specific_entropy | S (M) | none | undecided | S collides with the S level and sulfur |
| Plasma | `S` | c | same | S | specific_entropy | S (M) | none | undecided |  |
| Plasma | `vdf_ratio` | b | Series | p1/a | none | VDFratio (M) | none | undecided | method and TeX key differ in case and form |
| Plasma | `sc` | c | Spacecraft | n/a | n/a | n/a | n/a | silent | container accessor |
| Plasma | `spacecraft` | b | Spacecraft | n/a | n/a | n/a | n/a | silent | container accessor |
| Plasma | `aux` | c | DataFrame or None | n/a | n/a | n/a | n/a | silent | container accessor |
| Plasma | `auxiliary_data` | b | DataFrame or None | n/a | n/a | n/a | n/a | silent | container accessor |
| Ion | `n` | c | Series | n | n | n (M) | n | keep |  |
| Ion | `number_density` | b | Series | n | n | n (M) | n | delete |  |
| Ion | `rho` | c | Series | rho | rho | rho (M) | none | keep | the author's F52 example |
| Ion | `mass_density` | b | Series | rho | rho | rho (M) | none | delete |  |
| Ion | `v` | c | Vector | n/a | v | v (M) | v | keep |  |
| Ion | `velocity` | b | Vector | n/a | v | v (M) | v | delete |  |
| Ion | `w` | c | Tensor | n/a | w | w (M) | w | keep |  |
| Ion | `thermal_speed` | b | Tensor | n/a | w | w (M) | w | delete |  |
| Ion | `pth` | a | DataFrame | pth (ad hoc) | pth | pth (M) | none | keep |  |
| Ion | `cs` | a | DataFrame (C) | cs (ad hoc) | cs | cs (M) | none | keep | Ion.cs is a DataFrame, Plasma.cs a Series |
| Ion | `temperature` | b | DataFrame | T (ad hoc) | temperature | T (M) | none | rename:T |  |
| Ion | `anisotropy` | b | Series | RT | none | R (M), C=T | none | undecided |  |
| Ion | `kinetic_energy_flux` | b | Series | Wk | kinetic_energy_flux | Wk (M) | none | delete |  |
| Ion | `Wk` | c | Series | Wk | kinetic_energy_flux | Wk (M) | none | keep |  |
| Ion | `specific_entropy` | b | Series | S | specific_entropy | S (M) | none | undecided |  |
| Ion | `S` | c | Series | S | specific_entropy | S (M) | none | undecided |  |
| Spacecraft | `pos` | c | Vector | n/a | none | n/a | pos | keep |  |
| Spacecraft | `position` | b | Vector | n/a | none | n/a | pos | delete |  |
| Spacecraft | `r` | d | Vector | n/a | none | r (C) means magnitude | pos | delete | F73 |
| Spacecraft | `v` | c | Vector | n/a | v | v (M) | v | keep |  |
| Spacecraft | `velocity` | b | Vector | n/a | v | v (M) | v | delete |  |
| Spacecraft | `carrington` | b | DataFrame (lat, lon) | n/a | none | carr (M) | carr | rename:carr |  |
| Spacecraft | `distance2sun` | a | Series | distance2sun | distance2sun | Distance2Sun path | none | keep |  |
| Vector | `mag` | a | Series | mag | none | none | none | undecided | mag and r are one quantity, both pass |
| Vector | `r` | d | Series | r | none | r (C) | none | undecided | Spacecraft.r is a Vector (F73) |
| Vector | `magnitude` | c | Series | mag | none | none | none | delete | neither data label |
| Vector | `rho` | d | Series | rho | none | rho (C) | none | undecided | rho is also the M label for mass density (F74) |
| Vector | `colat` | c | Series | colatitude | none | colat (C) | none | keep | .name changes to colat |
| Vector | `colatitude` | b | Series | colatitude | none | colat (C) | none | delete |  |
| Vector | `lat` | c | Series | latitude | none | lat (C) | none | keep | .name changes to lat |
| Vector | `latitude` | b | Series | latitude | none | lat (C) | none | delete |  |
| Vector | `lon` | c | Series | longitude | none | lon (C) | none | keep | .name changes to lon |
| Vector | `longitude` | b | Series | longitude | none | lon (C) | none | delete |  |
| Vector | `uv` | c | Vector | None (uv set on the DataFrame, lost in Vector) | none | none | none | keep | weak: only the code literal decides |
| Vector | `unit_vector` | b | Vector | None | none | none | none | delete |  |
| Vector | `cartesian` | s | DataFrame | n/a | n/a | n/a | n/a | silent |  |
| Vector | `cos_theta` | a | Series | None | none | cos_theta | none | keep |  |
| Vector | `project` | s | DataFrame | n/a | n/a | n/a | n/a | silent | verb |
| BField | `pb` | c | Series | pb | none | none | none | keep |  |
| BField | `pressure` | b | Series | pb | none | none | none | delete |  |
| Tensor | `magnitude` | b | Series | None | none | scalar (C) | w scalar | undecided | F79 asks to add mag; the rule says one name |
| AlfvenicTurbulence | `v` | c | DataFrame | n/a | v | v (M) | v | keep | F76: returns DataFrame |
| AlfvenicTurbulence | `velocity` | b | DataFrame | n/a | v | v (M) | v | delete |  |
| AlfvenicTurbulence | `b` | c | DataFrame | n/a | b | b (M) | b | keep |  |
| AlfvenicTurbulence | `bfield` | b | DataFrame | n/a | b | b (M) | b | delete |  |
| AlfvenicTurbulence | `zp` | c | DataFrame | n/a | none | zp (M) | none | keep |  |
| AlfvenicTurbulence | `z_plus` | b | DataFrame | n/a | none | zp (M) | none | delete |  |
| AlfvenicTurbulence | `zm` | c | DataFrame | n/a | none | zm (M) | none | keep |  |
| AlfvenicTurbulence | `z_minus` | b | DataFrame | n/a | none | zm (M) | none | delete |  |
| AlfvenicTurbulence | `ep` | c | Series | None | none | ep (M) | none | keep | set .name |
| AlfvenicTurbulence | `e_plus` | b | Series | None | none | ep (M) | none | delete |  |
| AlfvenicTurbulence | `em` | c | Series | None | none | em (M) | none | keep | set .name |
| AlfvenicTurbulence | `e_minus` | b | Series | None | none | em (M) | none | delete |  |
| AlfvenicTurbulence | `ev` | c | Series | None | none | ev (M) | none | keep | set .name |
| AlfvenicTurbulence | `kinetic_energy` | b | Series | None | none | ev (M) | none | delete |  |
| AlfvenicTurbulence | `eb` | c | Series | None | none | none | none | keep | no TeX key; add eb |
| AlfvenicTurbulence | `magnetic_energy` | b | Series | None | none | none | none | delete |  |
| AlfvenicTurbulence | `etot` | c | Series | None | none | etot (M) | none | keep | set .name |
| AlfvenicTurbulence | `total_energy` | b | Series | None | none | etot (M) | none | delete |  |
| AlfvenicTurbulence | `eres` | c | Series | None | none | eres (M) | none | keep | set .name |
| AlfvenicTurbulence | `residual_energy` | b | Series | None | none | eres (M) | none | delete |  |
| AlfvenicTurbulence | `sigma_r` | c | Series | None | none | sigma_r (M) | none | keep | set .name |
| AlfvenicTurbulence | `eres_norm` | c | Series | None | none | sigma_r (M) | none | delete | second alias of one quantity |
| AlfvenicTurbulence | `normalized_residual_energy` | b | Series | None | none | sigma_r (M) | none | delete |  |
| AlfvenicTurbulence | `sigma_c` | c | Series | None | none | sigma_c (M) | none | keep | set .name |
| AlfvenicTurbulence | `normalized_cross_helicity` | b | Series | None | none | sigma_c (M) | none | delete |  |
| AlfvenicTurbulence | `cross_helicity` | b | Series | None | none | xhel (M) | none | rename:xhel | no short alias exists today |
| AlfvenicTurbulence | `rA` | c | Series | None | none | ra (M) | none | undecided | case differs from TeX key |
| AlfvenicTurbulence | `alfven_ratio` | b | Series | None | none | ra (M) | none | delete |  |
| AlfvenicTurbulence | `rE` | c | Series | None | none | re (M) | none | undecided | case differs from TeX key |
| AlfvenicTurbulence | `elsasser_ratio` | b | Series | None | none | re (M) | none | delete |  |
| AlfvenicTurbulence | `data / measurements / polarity / species / averaging_info` | s | various | n/a | n/a | n/a | n/a | silent |  |
| StabilityCondition | `growth_rate (init arg)` | b | int exponent of gamma/Omega_p | n/a | none | gamma (M); row level 'Growth Rate' | none | keep | F110; rename the level to growth_rate |
| StabilityContours | `plot_gamma (arg)` | b | int exponent | n/a | none | gamma (M) | none | rename:growth_rate | F110 |
| StabilityContours | `gamma (loop var)` | b | int exponent | n/a | none | gamma (M) | none | rename:growth_rate | private local |
| StabilityCondition | `beta / anisotropy` | a | Series | n/a | beta / none | beta / R | none | undecided | anisotropy follows the Plasma decision |
| BetaRPlot | `ani (arg)` | b | Series | n/a | none | R (M) | none | undecided | follows the anisotropy decision |

Plasma "Series by S" means: one species gives a Series named after the species, several
species give a DataFrame with `columns.names == ['S']`. Two siblings break that pattern:
`Plasma.specific_entropy('p1')` names its Series `'S'` and `Plasma.pdynamic('p1','a')` names
it `'pdynamic'`, so `pd.concat` of `Plasma` results would mix species keys and quantity keys.

## Rule test

**Where it gives one name per concept.** `n`, `rho`, `v`, `w`, `b`, `pth`, `beta`, `ca`,
`caani`, `afsq`, `lnlambda`, `nuc`, `nc`, `dv`, `cs`, `Wk`, `pos`, `carr`, `distance2sun`,
`pb`, the Elsasser family (`zp`, `zm`, `ep`, `em`, `ev`, `etot`, `eres`, `sigma_r`,
`sigma_c`, `xhel`) and the angles (`colat`, `lat`, `lon`). For these the rule picks the short
label and deletes the long name, with no contradiction.

**Where it contradicts the author's earlier notes.**

- F74, "delete the rho alias for mass_density". `rho` is not a stored M label in the example
  data, but it is the label at every layer that exists for mass density:
  `Ion.mass_density.name == 'rho'` (`ions.py:209`), `Units.rho` (`units_constants.py:191`),
  TeX `_templates["rho"] = \rho_{$S}` and `_trans_units["rho"]`. Under the rule `rho` is
  canonical and `mass_density` is the two-home name, the opposite of the note. The F74
  collision is across levels: `rho` is also a C-level key in `_trans_component` (`\rho`,
  the cylindrical radius), which is what `Vector.rho.name == 'rho'` matches. The rule
  resolves it only if it says names are unique per level.
- F79, "sound_speed should be the converged name". `cs` passes every layer
  (`Ion.cs.name`, `Units.cs`, TeX `cs`); `sound_speed` passes none. The rule picks `cs`.
- F79, "the short 'mag' sounds like an alias". `Vector.mag.name == 'mag'`, so the `.name`
  leg calls `mag` canonical; but the TeX component table has `r` and no `mag`, and
  `Vector.r` sets `.name = 'r'`. The rule calls both canonical. The note and the TeX layer
  agree on `r`; the `.name` layer disagrees.

**Where the data labels disagree with each other** (the rule cannot pick until one home is
changed):

- heat flux: `Units.qpar` vs TeX `q` with C `par` (`q_{{$C};{$S}}`), method `heat_flux`.
- dynamic pressure: `.name` `pdynamic` vs TeX `pdv`.
- anisotropy: `Ion.anisotropy.name == 'RT'` vs TeX M `R` with C `T` or `P` (`BetaRPlot`).
- angles: `.name` `colatitude`/`latitude`/`longitude` vs TeX C `colat`/`lat`/`lon`.
- `vdf_ratio` vs TeX `VDFratio`.
- `rA`/`rE` vs TeX `ra`/`re`; and `re` also means Earth radii in `Distance2Sun`
  (`special.py:777`).
- `cross_helicity` vs TeX `xhel`, with no short alias at all.
- temperature: `Units.temperature` vs TeX `T` vs ad hoc `.name` `T`.
- kinetic energy flux: `Units.kinetic_energy_flux` vs TeX and `.name` `Wk`.
- specific entropy: `Units.specific_entropy` vs TeX and `.name` `S`; TeX also has a
  separate key `entropy` with different units (`ln(K cm^-3/2)`).
- magnetic field: `Units` holds both `bfield` (the init field) and `b` (derived from it).

**New collision the rule would entrench.** `S` is the species level name, the sulfur
species code in `_trans_species`, and a `Plasma` method. I verified that a `Plasma` built
with a species named `S` returns the specific-entropy method for `plasma.S`, not the `Ion`,
because `Plasma.__getattr__` (`plasma.py:239`) only runs after normal lookup fails. The
collision exists today; the rule makes `S` the canonical name rather than a removable alias.

**Where the rule is silent.** Container accessors carry no data label: `sc`/`spacecraft`,
`aux`/`auxiliary_data`, `ions`, `species`,
`epoch`, `data`. They are also where usage concentrates (approximate regex counts of attribute access in
package plus `tests/`, import lines excluded: `spacecraft` 46, `auxiliary_data` 25, `sc` 4, `aux` 4), so this is where the
author's churn cost lives. The instability `growth_rate` is labelled `"Growth Rate"`, a row
index level name that is not an identifier, and TeX `gamma` carries Hz units although the
value is an integer log10 exponent of `gamma/Omega_p`.

## Proposed name set

**Keep (canonical, short label is the definition).** `Plasma`/`Ion`: `n`, `rho`, `v`, `w`,
`pth`, `cs`, `Wk`; `Plasma`: `b`, `beta`, `ca`, `caani`, `afsq`, `lnlambda`, `nuc`, `nc`,
`dv`; `Spacecraft`: `pos`, `v`, `distance2sun`; `Vector`: `colat`, `lat`, `lon`, `uv`,
`cos_theta`; `BField`: `pb`; `AlfvenicTurbulence`: `v`, `b`, `zp`, `zm`, `ep`, `em`, `ev`,
`eb`, `etot`, `eres`, `sigma_r`, `sigma_c`; `StabilityCondition(growth_rate=...)`.

**Delete (36 public members).** `Plasma`: `number_density`, `mass_density`, `velocity`,
`thermal_speed`, `bfield`, `sound_speed`, `kinetic_energy_flux`. `Ion`: `number_density`,
`mass_density`, `velocity`, `thermal_speed`, `kinetic_energy_flux`. `Spacecraft`:
`position`, `r`, `velocity`. `Vector`: `magnitude`, `colatitude`, `latitude`, `longitude`,
`unit_vector`. `BField`: `pressure`. `AlfvenicTurbulence`: `velocity`, `bfield`, `z_plus`,
`z_minus`, `e_plus`, `e_minus`, `kinetic_energy`, `magnetic_energy`, `total_energy`,
`residual_energy`, `normalized_residual_energy`, `eres_norm`, `normalized_cross_helicity`,
`alfven_ratio`, `elsasser_ratio`. (`alfven_ratio`/`elsasser_ratio` go whichever case the
author picks for the short name.)

**Rename (4 public members, 1 public keyword).** `Plasma.temperature` and
`Ion.temperature` to `T`; `Spacecraft.carrington` to `carr`;
`AlfvenicTurbulence.cross_helicity` to `xhel`; `StabilityContours.plot_contours(plot_gamma=)`
to `growth_rate=` (and the private loop variable `gamma`).

**Label, `Units` and `.name` strings (17).** `Units`: fold `bfield` into `b`,
`kinetic_energy_flux` to `Wk`, `temperature` to `T`. `.name`: `colatitude`, `latitude`,
`longitude` to `colat`, `lat`, `lon`; set `.name` on the nine `AlfvenicTurbulence` Series
(`ep`, `em`, `ev`, `eb`, `etot`, `eres`, `sigma_r`, `sigma_c`, `xhel`). TeX: add an `eb`
key. Instabilities: rename the `"Growth Rate"` level to `growth_rate`.

**Author decides (18 public members).** Heat flux: `q` or `qpar` (`heat_flux`, `qpar`, and
`Units.qpar`). Dynamic pressure: `pdv` or `pdynamic`. Anisotropy: `R` or `RT` (`Plasma`,
`Ion`, `StabilityCondition`, `BetaRPlot(ani=)`). Specific entropy: `S` despite the
collision, or a new label. Vector magnitude: `r` or `mag`. `Tensor.magnitude`. `Vector.rho`
against mass-density `rho`. `rA`/`rE` vs `ra`/`re`. `vdf_ratio` vs `VDFratio`. And whether
the rule extends to container accessors at all.

## Out of scope but seen

- `Ion.cs` returns a DataFrame over `par`/`per`/`scalar` while `Plasma.cs('p1')` returns the
  scalar Series; the rule makes them one name, so their shapes should match (cf. F75).
- `Plasma.velocity('p1','a')` returns a Series indexed by species (`['a', 'p1']`, `.name None`), not a
  `Vector`; verified, not investigated.
- `Ion.set_species` public vs `Plasma._set_species` private (F79's first clause) is not a
  naming-rule question.

## Card semantics

`survives` in `phaseA-naming.cards.json`: for a card about an earlier author note, whether
that note survives the rule unchanged; for a new card, whether the finding stands.
