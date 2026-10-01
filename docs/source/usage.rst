Usage Guide
===========

This page walks through a first session: build a plasma from a DataFrame, read
a species' quantities, fit a function, and save a plot. Every example on this
page runs as a doctest (``pytest --doctest-glob='*.rst' docs/source``).

.. contents::
   :local:
   :depth: 1

Build a Plasma
--------------

SolarWindPy holds measurements in one pandas DataFrame whose columns are a
three-level MultiIndex named ``M``, ``C``, ``S``:

- ``M``, the measurement: ``n`` (number density, cm\ :sup:`-3`), ``v``
  (velocity, km/s), ``w`` (thermal speed, km/s), ``b`` (magnetic field, nT).
- ``C``, the component: ``x``, ``y``, ``z`` for vectors, ``par`` and ``per``
  for thermal speeds, empty for scalars.
- ``S``, the species: ``p1`` (protons), ``a`` (alphas), empty for the
  magnetic field.

>>> import pandas as pd
>>> from solarwindpy.core.plasma import Plasma
>>> epoch = pd.date_range("2023-01-01", periods=3, freq="1h")
>>> columns = pd.MultiIndex.from_tuples(
...     [
...         ("n", "", "p1"), ("n", "", "a"),
...         ("v", "x", "p1"), ("v", "x", "a"),
...         ("v", "y", "p1"), ("v", "y", "a"),
...         ("v", "z", "p1"), ("v", "z", "a"),
...         ("w", "par", "p1"), ("w", "par", "a"),
...         ("w", "per", "p1"), ("w", "per", "a"),
...         ("b", "x", ""), ("b", "y", ""), ("b", "z", ""),
...     ],
...     names=["M", "C", "S"],
... )
>>> data = pd.DataFrame(
...     [
...         [5.0, 0.25, 400, 380, 10, 5, -20, -15, 30, 15, 25, 12, 3.5, -1.2, 0.8],
...         [8.0, 0.40, 450, 420, 15, 8, -25, -18, 35, 18, 28, 14, 4.1, -1.5, 1.2],
...         [6.5, 0.30, 420, 400, 12, 6, -22, -16, 32, 16, 26, 13, 3.8, -1.3, 0.9],
...     ],
...     index=epoch,
...     columns=columns,
... )
>>> plasma = Plasma(data, "p1", "a")
>>> plasma.species
('a', 'p1')

Read a Species' Quantities
--------------------------

Each species is an attribute of the plasma. Its density is a Series indexed
by time:

>>> plasma.p1.n
2023-01-01 00:00:00    5.0
2023-01-01 01:00:00    8.0
2023-01-01 02:00:00    6.5
Freq: h, Name: n, dtype: float64

Vectors carry their magnitude. The first proton speed is
:math:`\sqrt{400^2 + 10^2 + 20^2} \approx 400.62` km/s, and the first field
magnitude is :math:`\sqrt{3.5^2 + 1.2^2 + 0.8^2} \approx 3.79` nT:

>>> plasma.p1.v.mag.round(2).tolist()
[400.62, 450.94, 420.75]
>>> plasma.b.mag.round(2).tolist()
[3.79, 4.53, 4.12]

The plasma combines species and field. Proton beta is
:math:`\beta = 2 \mu_0 p / B^2`, with thermal pressure :math:`p = n m w^2 / 2`
under the :math:`m w^2 = 2 k_B T` convention:

>>> plasma.beta("p1")["par"].round(2).tolist()
[0.66, 1.0, 0.83]

Fit a Function
--------------

Every fit function takes observed ``x`` and ``y`` arrays. Fitting a Gaussian
to a noise-free Gaussian recovers the parameters that generated it:

>>> import numpy as np
>>> from solarwindpy.fitfunctions.gaussians import Gaussian
>>> x = np.linspace(300, 600, 61)
>>> y = 50 * np.exp(-0.5 * ((x - 420) / 40) ** 2)
>>> fit = Gaussian(x, y)
>>> fit.make_fit()
>>> {name: round(float(value), 3) for name, value in fit.popt.items()}
{'mu': 420.0, 'sigma': 40.0, 'A': 50.0}

``solarwindpy.fitfunctions.available()`` prints every fit function with its
formula:

>>> import solarwindpy.fitfunctions as ff
>>> ff.available()  # doctest: +ELLIPSIS
Fit function...Gaussian...

Save a Plot
-----------

A fit carries a plotter that draws the observations and the fitted curve. The
``Agg`` backend renders without a display. The figure is written to a
temporary directory:

>>> import tempfile
>>> from pathlib import Path
>>> import matplotlib
>>> matplotlib.use("Agg")
>>> import matplotlib.pyplot as plt
>>> ax = fit.plotter.plot_raw_used_fit()
>>> with tempfile.TemporaryDirectory() as tmp:
...     path = Path(tmp) / "gaussian_fit.png"
...     ax.figure.savefig(path)
...     print(path.exists())
True
>>> plt.close(ax.figure)

``solarwindpy.plotting.labels.available()`` prints every measurement,
component, and species that the plot labels know.

Next Steps
----------

- The :doc:`tutorial` covers more of the library.
- The :doc:`api_reference` documents every public class and function.
