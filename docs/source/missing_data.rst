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

Across species
--------------

A total over species, such as ``"a+p1"``, uses the species present at that time.
It is NaN only when no species is present. Protons measured without alphas still
give a total density, temperature and pressure. Weighted means, such as the
center-of-mass velocity (:py:meth:`~solarwindpy.core.plasma.Plasma.velocity`)
and the electron velocity
(:py:meth:`~solarwindpy.core.plasma.Plasma.estimate_electrons`), likewise
average over the species present.

A quantity built from a pair of species needs both. The combined thermal speed
and the mass-density ratio in :py:meth:`~solarwindpy.core.plasma.Plasma.nuc`,
and the reduced mass in :py:meth:`~solarwindpy.core.plasma.Plasma.pdynamic`, are
NaN at a time when either species is missing.

Thermal speeds do not add across species, so
:py:meth:`~solarwindpy.core.plasma.Plasma.thermal_speed` raises for a total such
as ``"a+p1"``. Only temperatures and pressures form totals.

The two levels
--------------

For temperature (:py:meth:`~solarwindpy.core.plasma.Plasma.temperature`),
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
