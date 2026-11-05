Missing data
============

Measurements drop out: an instrument misses a component, or a species is not
resolved at some times. :py:class:`~solarwindpy.core.plasma.Plasma` treats a
missing value as NaN and never as zero, with one rule at each of two levels.

Within a species
----------------

A species' moments stand or fall together. If any of its density, velocity
components or thermal-speed components is missing at a time, every measurement
of that species is invalid then. When the data are set,
:py:class:`~solarwindpy.core.plasma.Plasma` masks that species to NaN at that
time and logs a warning with the number of times it masked. A species therefore
never has a density without a velocity, or one thermal-speed component without
the other.

A species' value at a time needs every component it is built from. A scalar
thermal speed, temperature or pressure needs both the parallel and the
perpendicular component, because one component alone does not describe the
distribution. The field strength in
:py:meth:`~solarwindpy.core.plasma.Plasma.afsq` needs all three field
components.
The rule covers every vector and tensor in ``solarwindpy.core``,
:py:class:`~solarwindpy.core.spacecraft.Spacecraft` included, so a magnitude,
a component sum or a dot product is NaN wherever one of its components is
missing.

Across species
--------------

A total over species, such as ``"a+p1"``, uses the species present at that time.
It is NaN only when no species is present. Protons measured without alphas still
give a total density, temperature and pressure. Weighted means, such as the
center-of-mass velocity (:py:meth:`~solarwindpy.core.plasma.Plasma.v`)
and the electron velocity
(:py:meth:`~solarwindpy.core.plasma.Plasma.estimate_electrons`), likewise
average over the species present.

A quantity built from a pair of species needs both. The combined thermal speed
and the mass-density ratio in :py:meth:`~solarwindpy.core.plasma.Plasma.nuc`,
and the reduced mass in :py:meth:`~solarwindpy.core.plasma.Plasma.pdv`, are
NaN at a time when either species is missing.

Quantities that sum over species take a total: number density
(:py:meth:`~solarwindpy.core.plasma.Plasma.n`), mass density
(:py:meth:`~solarwindpy.core.plasma.Plasma.rho`), thermal pressure
(:py:meth:`~solarwindpy.core.plasma.Plasma.pth`), temperature
(:py:meth:`~solarwindpy.core.plasma.Plasma.T`) and kinetic energy flux
(:py:meth:`~solarwindpy.core.plasma.Plasma.Wk`). So do the quantities built
from those totals, such as the plasma beta
(:py:meth:`~solarwindpy.core.plasma.Plasma.beta`), the anisotropy
(:py:meth:`~solarwindpy.core.plasma.Plasma.R`), the sound speed
(:py:meth:`~solarwindpy.core.plasma.Plasma.cs`) and the Alfvén speed
(:py:meth:`~solarwindpy.core.plasma.Plasma.ca`). Thermal speeds do not add
across species, so :py:meth:`~solarwindpy.core.plasma.Plasma.w` raises for a
total such as ``"a+p1"``.

A total density can also be strict:
``plasma.n("a+p1", skipna=False)`` is NaN at a time when any of its species is
missing.

The two levels
--------------

For temperature (:py:meth:`~solarwindpy.core.plasma.Plasma.T`),
``ok`` marks a measured value present and ``NaN`` one missing. A species missing
either component is masked as a whole at that time, so its result there is NaN:

.. code-block:: text

             protons (p1)                   alphas (a)                     total "a+p1"
   time   T_par   T_perp  ->  T_p1      T_par   T_perp  ->  T_a
   t0      ok      ok     ->  ok         ok      ok     ->  ok      ->   p1 + a
   t1      ok      NaN    ->  NaN        ok      ok     ->  ok      ->   a only
   t2      ok      ok     ->  ok         NaN     NaN    ->  NaN     ->   p1 only
   t3      NaN     ok     ->  NaN        NaN     ok     ->  NaN     ->   NaN

Pressure (:py:meth:`~solarwindpy.core.plasma.Plasma.pth`) follows the same
pattern:

.. code-block:: text

             protons (p1)                   alphas (a)                     total "a+p1"
   time   p_par   p_perp  ->  p_p1      p_par   p_perp  ->  p_a
   t0      ok      ok     ->  ok         ok      ok     ->  ok      ->   p1 + a
   t1      ok      NaN    ->  NaN        ok      ok     ->  ok      ->   a only
   t2      ok      ok     ->  ok         NaN     NaN    ->  NaN     ->   p1 only
   t3      NaN     ok     ->  NaN        NaN     ok     ->  NaN     ->   NaN

The per-species result at each time is the within-species rule; the total is the
across-species rule applied to those results.
