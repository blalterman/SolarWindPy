Missing data
============

Measurements drop out: an instrument misses a component, or a species is not
resolved at some times. :py:class:`~solarwindpy.core.plasma.Plasma` treats a
missing value as NaN and never as zero, with one rule at each of two levels.

Within a species
----------------

A species' value at a time needs every component it is built from. If any
component is missing, that species' value is NaN at that time. A scalar thermal
speed, temperature or pressure needs both the parallel and the perpendicular
component, because one component alone does not describe the distribution. A
species' differential flow speed in
:py:meth:`~solarwindpy.core.plasma.Plasma.pdynamic` needs all three velocity
components, and the field strength in
:py:meth:`~solarwindpy.core.plasma.Plasma.afsq` needs all three field
components.

Across species
--------------

A total over species, such as ``"a+p1"``, uses the species present at that time.
It is NaN only when no species is present. Protons measured without alphas still
give a total temperature and a total pressure.

Weighted means follow the same rule. In the center-of-mass velocity
(:py:meth:`~solarwindpy.core.plasma.Plasma.velocity`) and the electron velocity
(:py:meth:`~solarwindpy.core.plasma.Plasma.estimate_electrons`), a species
without a velocity at a time leaves the density weights as well as the weighted
sum. The electron density still counts every species with a density, because
quasi-neutrality does not depend on the ion velocities.

Thermal speeds do not add across species, so
:py:meth:`~solarwindpy.core.plasma.Plasma.thermal_speed` raises for a total such
as ``"a+p1"``. Only temperatures and pressures form totals.

The two levels
--------------

For temperature (:py:meth:`~solarwindpy.core.plasma.Plasma.temperature`),
``ok`` marks a value present and ``NaN`` a value missing:

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
