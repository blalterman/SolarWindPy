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
:py:class:`~solarwindpy.core.plasma.Plasma` from them. The session selects
matplotlib's ``Agg`` backend first, so the plot further down renders without a
display:

>>> import matplotlib
>>> matplotlib.use("Agg")
>>> import solarwindpy as swp
>>> plasma = swp.examples.load_plasma()
>>> plasma.species
('a', 'e', 'p1', 'p2')

The species are alphas (``a``), electrons (``e``), the proton core (``p1``)
and a proton beam (``p2``), a second proton population.

The measurements live in one pandas DataFrame, ``plasma.data``. Its columns are
a three-level MultiIndex:

>>> list(plasma.data.columns.names)
['M', 'C', 'S']
>>> plasma.data.shape
(3, 31)
>>> plasma.data.columns.get_level_values("M").unique()
Index(['b', 'n', 'v', 'w'], dtype='str', name='M')

- ``M``, the measurement: ``n`` (number density), ``v`` (velocity), ``w``
  (thermal speed), ``b`` (magnetic field).
- ``C``, the component: ``x``, ``y``, ``z`` for vectors; ``par`` and ``per``
  for thermal speeds, parallel and perpendicular to the magnetic field; empty
  for scalars such as density.
- ``S``, the species; empty for the magnetic field.

The data you give a plasma carry ``par`` and ``per`` thermal speeds. The plasma
computes a ``scalar`` thermal speed for each species from those two (see below)
and adds it to ``plasma.data`` as a ``("w", "scalar", species)`` column; it is
not an input.

Derived Quantities
------------------

Each species is an attribute of the plasma, and each of its quantities is a
pandas Series indexed by the measurement time, ``epoch``. Densities are in
cm\ :sup:`-3` and speeds in km/s. The second proton speed is
:math:`\sqrt{200^2 + 300^2 + 600^2} = 700` km/s:

>>> plasma.p1.n
epoch
1995-01-01 12:35:00.000000    1.0
2022-03-23 19:29:09.000000    2.0
2022-10-09 01:47:01.234560    3.0
Name: n, dtype: float64
>>> plasma.p1.v.mag.round(1)
epoch
1995-01-01 12:35:00.000000     458.3
2022-03-23 19:29:09.000000     700.0
2022-10-09 01:47:01.234560    1044.0
Name: mag, dtype: float64

The magnetic field is in nT:

>>> plasma.b.mag.round(2)
epoch
1995-01-01 12:35:00.000000    0.63
2022-03-23 19:29:09.000000    0.77
2022-10-09 01:47:01.234560    1.03
Name: mag, dtype: float64

Thermal speeds, in km/s, have parallel, perpendicular and scalar components.
The scalar thermal speed is
:math:`w = \sqrt{(w_\parallel^2 + 2 w_\perp^2) / 3}`, the combination of a
temperature :math:`T = (T_\parallel + 2 T_\perp) / 3`; at the first time it is
:math:`\sqrt{(10^2 + 2 \cdot 7^2) / 3} \approx 8.12` km/s. A quantity with
components is a DataFrame whose columns are the components, ``C``:

>>> plasma.w("p1").round(2)
C                            par   per  scalar
epoch
1995-01-01 12:35:00.000000  10.0   7.0    8.12
2022-03-23 19:29:09.000000  20.0  26.0   24.17
2022-10-09 01:47:01.234560  30.0  28.0   28.68

Temperatures are stored in units of :math:`10^5` K, under the convention
:math:`m w^2 = 2 k_B T`. ``plasma.units`` holds each quantity's factor to SI,
so multiplying by ``plasma.units.T`` gives kelvin:

>>> T = plasma.T("p1")["scalar"] * plasma.units.T
>>> T.round(-2)
epoch
1995-01-01 12:35:00.000000     4000.0
2022-03-23 19:29:09.000000    35400.0
2022-10-09 01:47:01.234560    49800.0
Name: scalar, dtype: float64

The plasma beta and the anisotropy ``R`` are dimensionless. Each column of
``beta`` is the thermal pressure of that component over the magnetic pressure,
:math:`\beta = n k_B T / (B^2 / 2 \mu_0) = 2 \mu_0 p_{th} / B^2`, where
:math:`p_{th} = \rho w^2 / 2 = n k_B T` uses the parallel, perpendicular or
scalar thermal speed and :math:`B` is the field magnitude. ``R`` is the
perpendicular over the parallel pressure; for one species it is
:math:`(w_\perp / w_\parallel)^2`, so :math:`7^2 / 10^2 = 0.49` at the first
time:

>>> plasma.beta("p1").round(2)
C                            par   per  scalar
epoch
1995-01-01 12:35:00.000000  0.52  0.26    0.34
2022-03-23 19:29:09.000000  2.86  4.84    4.18
2022-10-09 01:47:01.234560  5.39  4.70    4.93
>>> plasma.R("p1").round(2)
epoch
1995-01-01 12:35:00.000000    0.49
2022-03-23 19:29:09.000000    1.69
2022-10-09 01:47:01.234560    0.87
Name: p1, dtype: float64

Quantities that add over species, such as density, take a species string
joined with ``+`` and return the total. The alpha and proton densities add:

>>> plasma.a.n
epoch
1995-01-01 12:35:00.000000    0.5
2022-03-23 19:29:09.000000    1.0
2022-10-09 01:47:01.234560    1.5
Name: n, dtype: float64
>>> plasma.n("a+p1")
epoch
1995-01-01 12:35:00.000000    1.5
2022-03-23 19:29:09.000000    3.0
2022-10-09 01:47:01.234560    4.5
Name: a+p1, dtype: float64

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
counts the points in each bin. Axis labels name the quantities, and the plot's
``path`` is built from them:

>>> TeXlabel = swp.plotting.labels.base.TeXlabel
>>> h.set_labels(x=TeXlabel(("n", "", "p1")), y=TeXlabel(("v", "", "p1")))
>>> h.path.as_posix()
'Hist2D/n_p1/v_p1/count/linX-linY'

:py:meth:`~solarwindpy.plotting.hist2d.Hist2D.make_plot` draws the histogram:

>>> import matplotlib.pyplot as plt
>>> ax, mesh, cbar = h.make_plot()
>>> ax.get_xlabel()
'$n_{p_1} \\; \\left[\\mathrm{cm}^{-3}\\right]$'

``path`` is relative: join it to the directory you save figures under and add
a file extension. Nothing is saved for you. Here the directory is a temporary
one:

>>> import tempfile
>>> from pathlib import Path
>>> with tempfile.TemporaryDirectory() as figures:
...     target = (Path(figures) / h.path).with_suffix(".png")
...     target.parent.mkdir(parents=True)
...     ax.figure.savefig(target)
...     print(target.relative_to(figures).as_posix(), target.exists())
Hist2D/n_p1/v_p1/count/linX-linY.png True
>>> plt.close(ax.figure)

A Fit
-----

Every fit function takes observed ``x`` and ``y`` arrays.
:py:class:`~solarwindpy.fitfunctions.lines.Line` fits :math:`y = m x + b`.
Here it fits points scattered about :math:`y = 2x + 1` by noise from a seeded
random number generator:

>>> import numpy as np
>>> rng = np.random.default_rng(42)
>>> x = np.linspace(0, 10, 21)
>>> y = 2.0 * x + 1.0 + rng.normal(0.0, 0.5, x.size)
>>> fit = swp.fitfunctions.lines.Line(x, y)
>>> fit.make_fit()
>>> {name: round(float(value), 2) for name, value in fit.popt.items()}
{'m': 1.99, 'b': 1.08}
>>> {name: round(float(value), 2) for name, value in fit.psigma.items()}
{'m': 0.03, 'b': 0.19}

``popt`` holds the fitted parameters and ``psigma`` their uncertainties. Each
uncertainty is the square root of a diagonal element of the parameter
covariance ``pcov``, and ``pcov`` is always rescaled by the fit's robust reduced
chi-squared; ``make_fit(absolute_sigma=True)`` raises ``NotImplementedError``.
Measurement uncertainties enter through the ``weights`` argument, the 1-sigma
uncertainties of ``y``, one per observation.

``chisq_dof`` has two kinds. ``linear`` is the sum of squared residuals,
divided by ``weights`` when given, per degree of freedom. ``robust`` is the
same sum after the fit's loss function (``make_fit`` uses a Huber loss by
default), and it is the one that rescales ``pcov``:

>>> [round(float(value), 3) for value in fit.chisq_dof]
[0.197, 0.064]

:py:attr:`~solarwindpy.fitfunctions.core.FitFunction.results` is the same
outcome as a one-row table. Its columns are a MultiIndex of the parameter or
quality name (``P``) and the kind (``K``): each parameter's ``value`` and
``uncertainty``, then the fit quality, the number of observations, the degrees
of freedom and the status:

>>> results = fit.results
>>> print(results.round(3).T.to_string(header=False, index_names=False))
m         value        1.992
          uncertainty  0.029
b         value        1.078
          uncertainty  0.189
chisq_dof linear       0.197
          robust       0.064
rsq                    0.995
nobs                      21
dof                       19
status                    ok

Printed on its side, the table reads as a checklist. Each parameter's
``value`` is the fit and its ``uncertainty`` the 1-sigma error from ``pcov``.
``chisq_dof`` gives the ``linear`` and ``robust`` reduced chi-squared, ``rsq``
the coefficient of determination, ``nobs`` the observations used and ``dof``
the degrees of freedom, ``nobs`` less the number of parameters. ``status`` is
``"ok"`` for a fit that converged; a failed fit holds NaN values and names the
exception instead. A cell reads by its column pair:

>>> round(float(results.loc[0, ("m", "uncertainty")]), 2)
0.03
>>> results.loc[0, ("status", "")]
'ok'

Every fit function's table has this layout, with one pair of columns per
parameter. A :py:class:`~solarwindpy.fitfunctions.gaussians.Gaussian` fit to a
seeded, noisy peak of height 10 at :math:`\mu = 0.5` with width
:math:`\sigma = 1.2` recovers all three within their uncertainties:

>>> rng = np.random.default_rng(1)
>>> x = np.linspace(-5, 5, 41)
>>> y = 10.0 * np.exp(-0.5 * ((x - 0.5) / 1.2) ** 2) + rng.normal(0.0, 0.3, x.size)
>>> gaussian = swp.fitfunctions.gaussians.Gaussian(x, y)
>>> gaussian.make_fit()
>>> print(gaussian.results.round(3).T.to_string(header=False, index_names=False))
mu        value        0.502
          uncertainty  0.015
sigma     value        1.201
          uncertainty  0.018
A         value         9.93
          uncertainty  0.131
chisq_dof linear       0.084
          robust       0.035
rsq                    0.993
nobs                      41
dof                       38
status                    ok

Next Steps
----------

- :doc:`/usage` shows the input DataFrame layout for bringing your own data:
  the ``M``, ``C``, ``S`` columns a plasma needs. It builds a plasma from that
  DataFrame and saves a fit's plot.
- :doc:`/missing_data` explains how missing measurements propagate.
- :py:class:`~solarwindpy.core.plasma.Plasma` documents every derived quantity.
  Methods worth knowing next: :py:meth:`~solarwindpy.core.plasma.Plasma.pth`
  (thermal pressure), :py:meth:`~solarwindpy.core.plasma.Plasma.ca` (Alfvén
  speed), :py:meth:`~solarwindpy.core.plasma.Plasma.cs` (sound speed),
  :py:meth:`~solarwindpy.core.plasma.Plasma.afsq` (firehose anisotropy factor)
  and :py:meth:`~solarwindpy.core.plasma.Plasma.estimate_electrons` (electrons
  from quasi-neutrality and zero current).
- :py:class:`~solarwindpy.plotting.hist2d.Hist2D` documents the histogram's
  binning, normalization and contour options.
- :py:attr:`~solarwindpy.fitfunctions.core.FitFunction.results` documents every
  column of a fit's table.
- :doc:`/api_reference` documents every public class and function.
