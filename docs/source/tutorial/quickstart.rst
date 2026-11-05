Quickstart
==========

This page goes from installation to derived quantities, a histogram and a fit.
Every example runs as a test, so each output shown is the one you get.

.. contents::
   :local:
   :depth: 1

Install
-------

.. code-block:: bash

   pip install solarwindpy

:doc:`/installation` covers conda-forge and development installs.

Load the Example Plasma
-----------------------

SolarWindPy ships a small example: three rows of synthetic solar wind
measurements, chosen for illustration rather than taken from a mission.
:py:func:`~solarwindpy.examples.load_plasma` builds a
:py:class:`~solarwindpy.core.plasma.Plasma` from them:

>>> import solarwindpy as swp
>>> plasma = swp.examples.load_plasma()
>>> plasma.species
('a', 'e', 'p1', 'p2')

The species are alphas (``a``), electrons (``e``), protons (``p1``) and a
proton beam (``p2``).

The measurements live in one pandas DataFrame, ``plasma.data``. Its columns are
a three-level MultiIndex:

>>> list(plasma.data.columns.names)
['M', 'C', 'S']
>>> plasma.data.shape
(3, 31)
>>> plasma.data.columns.get_level_values("M").unique().tolist()
['b', 'n', 'v', 'w']

- ``M``, the measurement: ``n`` (number density), ``v`` (velocity), ``w``
  (thermal speed), ``b`` (magnetic field).
- ``C``, the component: ``x``, ``y``, ``z`` for vectors; ``par``, ``per`` and
  ``scalar`` for thermal speeds, relative to the magnetic field; empty for
  scalars such as density.
- ``S``, the species; empty for the magnetic field.

Derived Quantities
------------------

Each species is an attribute of the plasma. Densities are in
cm\ :sup:`-3` and speeds in km/s. The second proton speed is
:math:`\sqrt{200^2 + 300^2 + 600^2} = 700` km/s:

>>> plasma.p1.n.tolist()
[1.0, 2.0, 3.0]
>>> plasma.p1.v.mag.round(1).tolist()
[458.3, 700.0, 1044.0]

Thermal speeds, in km/s, have parallel, perpendicular and scalar components:

>>> w = plasma.w("p1")
>>> w.columns.tolist()
['par', 'per', 'scalar']
>>> w["par"].tolist()
[10.0, 20.0, 30.0]

Temperatures are stored in units of :math:`10^5` K, under the convention
:math:`m w^2 = 2 k_B T`. ``plasma.units`` holds each quantity's factor to SI,
so multiplying by ``plasma.units.T`` gives kelvin:

>>> T = plasma.T("p1")["scalar"] * plasma.units.T
>>> T.round(-2).tolist()
[4000.0, 35400.0, 49800.0]

The plasma beta and the anisotropy ``R`` are dimensionless. ``R`` is the
perpendicular over the parallel pressure; for one species it is
:math:`(w_\perp / w_\parallel)^2`, so :math:`7^2 / 10^2 = 0.49` at the first
time:

>>> plasma.beta("p1")["scalar"].round(2).tolist()
[0.34, 4.18, 4.93]
>>> plasma.R("p1").round(2).tolist()
[0.49, 1.69, 0.87]

Quantities that add over species, such as density, take a species string
joined with ``+`` and return the total. The alpha and proton densities add:

>>> plasma.a.n.tolist()
[0.5, 1.0, 1.5]
>>> plasma.n("a+p1").tolist()
[1.5, 3.0, 4.5]

:doc:`/missing_data` lists the quantities that take a total, notes that
thermal speeds do not, and explains how a total treats a species missing at some
times.

A 2D Histogram
--------------

:py:class:`~solarwindpy.plotting.hist2d.Hist2D` bins pairs of values. Three
rows make only a demonstration, so this histogram uses three bins per axis:

>>> h = swp.plotting.hist2d.Hist2D(plasma.p1.n, plasma.p1.v.mag, nbins=3)
>>> int(h.agg().sum())
3

Without a ``z`` value, :py:meth:`~solarwindpy.plotting.hist2d.Hist2D.agg`
counts the points in each bin. Axis labels name the quantities, and the
plot's ``path`` is built from them for saving the figure:

>>> TeXlabel = swp.plotting.labels.base.TeXlabel
>>> h.set_labels(x=TeXlabel(("n", "", "p1")), y=TeXlabel(("v", "", "p1")))
>>> h.path.as_posix()
'Hist2D/n_p1/v_p1/count/linX-linY'

:py:meth:`~solarwindpy.plotting.hist2d.Hist2D.make_plot` draws it. The
``Agg`` backend renders without a display:

>>> import matplotlib
>>> matplotlib.use("Agg")
>>> import matplotlib.pyplot as plt
>>> ax, mesh, cbar = h.make_plot()
>>> ax.get_xlabel()
'$n_{p_1} \\; \\left[\\mathrm{cm}^{-3}\\right]$'
>>> plt.close(ax.figure)

A Fit
-----

Every fit function takes observed ``x`` and ``y`` arrays.
:py:class:`~solarwindpy.fitfunctions.lines.Line` fits :math:`y = m x + b`; on
points that lie on :math:`y = 2x + 1` it recovers the slope and intercept:

>>> import numpy as np
>>> x = np.linspace(0, 10, 11)
>>> y = 2.0 * x + 1.0
>>> fit = swp.fitfunctions.lines.Line(x, y)
>>> fit.make_fit()
>>> {name: round(float(value), 3) for name, value in fit.popt.items()}
{'m': 2.0, 'b': 1.0}

:py:attr:`~solarwindpy.fitfunctions.core.FitFunction.results` is the fit's
outcome as a one-row table: each parameter's value and uncertainty, then the
fit quality, the number of observations, the degrees of freedom and the
status:

>>> results = fit.results
>>> results.columns.get_level_values("P").unique().tolist()
['m', 'b', 'chisq_dof', 'rsq', 'nobs', 'dof', 'status']
>>> round(float(results.loc[0, ("m", "value")]), 3)
2.0
>>> results.loc[0, ("status", "")]
'ok'

Next Steps
----------

- :doc:`/usage` builds a plasma from your own DataFrame and saves a fit's plot.
- :doc:`/missing_data` explains how missing measurements propagate.
- :doc:`/api_reference` documents every public class and function.
