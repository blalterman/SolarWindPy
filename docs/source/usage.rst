Usage Guide
===========

This page walks through a first session: build a plasma from a DataFrame, read
a species' quantities, fit a function, and make and save plots. Every ``>>>``
example on this page runs as a doctest
(``pytest --doctest-glob='*.rst' docs/source``), and every figure is drawn by
the code shown above it when the documentation is built.

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
  for thermal speeds, empty for scalars. The plasma computes a ``scalar``
  thermal speed from ``par`` and ``per``; it is not an input.
- ``S``, the species: ``p1`` (protons), ``a`` (alphas), empty for the
  magnetic field.

>>> import pandas as pd
>>> from solarwindpy.core.plasma import Plasma
>>> epoch = pd.date_range("2023-01-01", periods=3, freq="1h")
>>> columns = pd.MultiIndex.from_tuples(
...     [
...         ("n", "", "p1"),  # density
...         ("n", "", "a"),
...         ("v", "x", "p1"),  # velocity
...         ("v", "x", "a"),
...         ("v", "y", "p1"),
...         ("v", "y", "a"),
...         ("v", "z", "p1"),
...         ("v", "z", "a"),
...         ("w", "par", "p1"),  # thermal speed
...         ("w", "par", "a"),
...         ("w", "per", "p1"),
...         ("w", "per", "a"),
...         ("b", "x", ""),  # magnetic field
...         ("b", "y", ""),
...         ("b", "z", ""),
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

>>> plasma.p1.v.mag.round(2)
2023-01-01 00:00:00    400.62
2023-01-01 01:00:00    450.94
2023-01-01 02:00:00    420.75
Freq: h, Name: mag, dtype: float64
>>> plasma.b.mag.round(2)
2023-01-01 00:00:00    3.79
2023-01-01 01:00:00    4.53
2023-01-01 02:00:00    4.12
Freq: h, Name: mag, dtype: float64

The plasma combines species and field. Proton beta is
:math:`\beta = 2 \mu_0 p / B^2`, with thermal pressure :math:`p = n m w^2 / 2`
under the :math:`m w^2 = 2 k_B T` convention. Like temperature and thermal
speed, it has ``par``, ``per`` and ``scalar`` columns:

>>> plasma.beta("p1").round(2)
C                     par   per  scalar
2023-01-01 00:00:00  0.66  0.46    0.53
2023-01-01 01:00:00  1.00  0.64    0.76
2023-01-01 02:00:00  0.83  0.55    0.64

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
>>> ff.available()  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
Fit function  Module  LaTeX
...
Gaussian  gaussians  f(x)=A \cdot e^{-\frac{1}{2} \left(\frac{x-\mu}{\sigma}\right)^2}
...

Make a Plot
-----------

:py:mod:`solarwindpy.plotting` has four plot classes. Each takes pandas
Series, so a plasma's quantities pass straight in:

- :py:class:`~solarwindpy.plotting.hist1d.Hist1D` bins one quantity: the
  distribution of ``x``, or the mean of a ``y`` in each bin of ``x``.
- :py:class:`~solarwindpy.plotting.hist2d.Hist2D` bins two quantities on a
  fixed grid: their joint distribution, or the mean of a ``z`` in each cell.
- :py:class:`~solarwindpy.plotting.spiral.SpiralPlot2D` bins two quantities on
  an adaptive mesh, which splits a cell into four while it holds more than
  ``min_per_bin`` points. Use it when the data are dense in some places and
  sparse in others, so one grid is either too coarse for the core or too noisy
  in the tails.
- :py:class:`~solarwindpy.plotting.scatter.Scatter` draws every point,
  optionally colored by ``z``. Use it for few points; past a few thousand they
  overlap and a histogram shows more.

The figures below use synthetic, seeded data that look like solar wind: a slow
population near 380 km/s and a fast one near 650 km/s, with a log-normal
density that falls as speed rises. Each block is complete: paste it into a
fresh Python session and it draws the figure shown under it.

One quantity
~~~~~~~~~~~~

``make_plot`` draws the histogram. ``set_labels`` takes a
:py:class:`~solarwindpy.plotting.labels.base.TeXlabel` per axis; `Labels`_
explains them.

.. plot::

   import numpy as np
   import pandas as pd
   from solarwindpy.plotting.hist1d import Hist1D
   from solarwindpy.plotting.labels.base import TeXlabel

   rng = np.random.default_rng(0)
   N = 20_000
   fast = rng.random(N) < 0.3
   v = pd.Series(np.where(fast, rng.normal(650, 60, N), rng.normal(380, 50, N)), name="v")

   h1 = Hist1D(v, nbins=60)
   h1.set_labels(x=TeXlabel(("v", "", "p1")))
   h1.make_plot()

Every plot also has a ``path``, built from its class, its labels and its axis
scales, to file the figure under when you save it: join it to your figure
directory and add an extension, as :doc:`tutorial/quickstart` does.

>>> import pandas as pd
>>> from solarwindpy.plotting.hist1d import Hist1D
>>> from solarwindpy.plotting.labels.base import TeXlabel
>>> h1 = Hist1D(pd.Series([380.0, 650.0], name="v"))
>>> h1.set_labels(x=TeXlabel(("v", "", "p1")))
>>> h1.path.as_posix()
'Hist1D/v_p1/count/linX-linY'

Two quantities
~~~~~~~~~~~~~~

Density spans a decade, so ``logy=True`` bins it in :math:`\log_{10}` and
draws a log axis. ``make_plot`` colors each cell by its count:

.. plot::

   import numpy as np
   import pandas as pd
   from solarwindpy.plotting.hist2d import Hist2D
   from solarwindpy.plotting.labels.base import TeXlabel

   rng = np.random.default_rng(0)
   N = 20_000
   fast = rng.random(N) < 0.3
   v = pd.Series(np.where(fast, rng.normal(650, 60, N), rng.normal(380, 50, N)), name="v")
   n = (8 * 10 ** (-0.0015 * (v - 400) + rng.normal(0, 0.15, N))).rename("n")

   h2 = Hist2D(v, n, logy=True, nbins=50)
   h2.set_labels(x=TeXlabel(("v", "", "p1")), y=TeXlabel(("n", "", "p1")))
   h2.make_plot()

:py:meth:`~solarwindpy.plotting.hist2d.Hist2D.plot_contours` draws the same
histogram as contours. ``gaussian_filter_std`` smooths the values with a
Gaussian whose standard deviation is in bins before the contours are drawn.
Set ``nan_aware_filter=True`` with it whenever the histogram has empty cells:
an empty cell is NaN, and the plain filter spreads each NaN over its
neighbours until no contour is left to draw. ``plot_edges=True`` also draws the
edges of the occupied distribution
(:py:meth:`~solarwindpy.plotting.hist2d.Hist2D.plot_edges`): in each column of
``x`` bins, the highest and the lowest occupied ``y`` bin, smoothed by a
Savitzky-Golay filter unless ``edges_kwargs=dict(smooth=False)``. The
filter's default window is a tenth of the number of ``x`` bins, so with fewer
than 50 bins set ``window_length`` in ``edges_kwargs=dict(sg_kwargs=...)``. Here
``axnorm="t"``, explained in `Normalizations`_, scales the peak to 1, and
``use_contourf=True`` fills the contours:

.. plot::

   import numpy as np
   import pandas as pd
   from solarwindpy.plotting.hist2d import Hist2D
   from solarwindpy.plotting.labels.base import TeXlabel

   rng = np.random.default_rng(0)
   N = 20_000
   fast = rng.random(N) < 0.3
   v = pd.Series(np.where(fast, rng.normal(650, 60, N), rng.normal(380, 50, N)), name="v")
   n = (8 * 10 ** (-0.0015 * (v - 400) + rng.normal(0, 0.15, N))).rename("n")

   h2 = Hist2D(v, n, logy=True, nbins=50, axnorm="t")
   h2.set_labels(x=TeXlabel(("v", "", "p1")), y=TeXlabel(("n", "", "p1")))
   h2.plot_contours(
       use_contourf=True, gaussian_filter_std=2, nan_aware_filter=True, plot_edges=True
   )

:py:meth:`~solarwindpy.plotting.hist2d.Hist2D.plot_hist_with_contours` draws
the histogram and its smoothed contours on the same axes, with one colorbar,
the histogram's. Black contour lines (``contour_kwargs=dict(colors="k")``)
stand out over the colored cells; the line style changes with the level:

.. plot::

   import numpy as np
   import pandas as pd
   from solarwindpy.plotting.hist2d import Hist2D
   from solarwindpy.plotting.labels.base import TeXlabel

   rng = np.random.default_rng(0)
   N = 20_000
   fast = rng.random(N) < 0.3
   v = pd.Series(np.where(fast, rng.normal(650, 60, N), rng.normal(380, 50, N)), name="v")
   n = (8 * 10 ** (-0.0015 * (v - 400) + rng.normal(0, 0.15, N))).rename("n")

   h2 = Hist2D(v, n, logy=True, nbins=50, axnorm="t")
   h2.set_labels(x=TeXlabel(("v", "", "p1")), y=TeXlabel(("n", "", "p1")))
   h2.plot_hist_with_contours(
       use_contourf=False,
       contour_kwargs=dict(colors="k"),
       gaussian_filter_std=2,
       nan_aware_filter=True,
   )

:py:meth:`~solarwindpy.plotting.hist2d.Hist2D.make_joint_h2_h1_plot` draws the
histogram with its projections on the top and right margins. Each margin is a
:py:class:`~solarwindpy.plotting.hist1d.Hist1D` from
:py:meth:`~solarwindpy.plotting.hist2d.Hist2D.project_1d`, on the histogram's
own bins; the right one is drawn with ``make_plot(transpose_axes=True)``, so
its counts run along ``x``. Call those two methods yourself to lay out the
margins differently.

.. plot::

   import numpy as np
   import pandas as pd
   from solarwindpy.plotting.hist2d import Hist2D
   from solarwindpy.plotting.labels.base import TeXlabel

   rng = np.random.default_rng(0)
   N = 20_000
   fast = rng.random(N) < 0.3
   v = pd.Series(np.where(fast, rng.normal(650, 60, N), rng.normal(380, 50, N)), name="v")
   n = (8 * 10 ** (-0.0015 * (v - 400) + rng.normal(0, 0.15, N))).rename("n")

   h2 = Hist2D(v, n, logy=True, nbins=50)
   h2.set_labels(x=TeXlabel(("v", "", "p1")), y=TeXlabel(("n", "", "p1")))
   h2.make_joint_h2_h1_plot()

An adaptive mesh
~~~~~~~~~~~~~~~~

:py:class:`~solarwindpy.plotting.spiral.SpiralPlot2D` takes the same data. Its
cells are small in the two cores and large in the sparse region between them,
so each cell holds enough points to be trusted. Because the cells differ in
size, plot it with ``axnorm="d"``: a raw count would make a large, sparse cell
look as full as a small, dense one. The mesh is its smoothing: it has no
Gaussian filter, by design.

.. plot::

   import numpy as np
   import pandas as pd
   from solarwindpy.plotting.spiral import SpiralPlot2D
   from solarwindpy.plotting.labels.base import TeXlabel

   rng = np.random.default_rng(0)
   N = 20_000
   fast = rng.random(N) < 0.3
   v = pd.Series(np.where(fast, rng.normal(650, 60, N), rng.normal(380, 50, N)), name="v")
   n = (8 * 10 ** (-0.0015 * (v - 400) + rng.normal(0, 0.15, N))).rename("n")

   sp = SpiralPlot2D(v, n, logy=True, axnorm="d", min_per_bin=50)
   sp.set_labels(x=TeXlabel(("v", "", "p1")), y=TeXlabel(("n", "", "p1")))
   sp.make_plot()

Individual points
~~~~~~~~~~~~~~~~~

:py:class:`~solarwindpy.plotting.scatter.Scatter` colors each point by ``z``,
here the density of a few hundred points. Its ``logx`` and ``logy`` set only
the axis scale; the data stay linear.

.. plot::

   import numpy as np
   import pandas as pd
   from solarwindpy.plotting.scatter import Scatter
   from solarwindpy.plotting.labels.base import TeXlabel

   rng = np.random.default_rng(0)
   N = 300
   fast = rng.random(N) < 0.3
   v = pd.Series(np.where(fast, rng.normal(650, 60, N), rng.normal(380, 50, N)), name="v")
   n = (8 * 10 ** (-0.0015 * (v - 400) + rng.normal(0, 0.15, N))).rename("n")
   w = pd.Series(0.1 * v + rng.normal(0, 5, v.size), name="w")

   sc = Scatter(v, w, n)
   sc.set_labels(
       x=TeXlabel(("v", "", "p1")),
       y=TeXlabel(("w", "", "p1")),
       z=TeXlabel(("n", "", "p1")),
   )
   sc.make_plot(s=8)

Bins
~~~~

``nbins`` chooses the bins of a :py:class:`~solarwindpy.plotting.hist1d.Hist1D`
or :py:class:`~solarwindpy.plotting.hist2d.Hist2D`:

- an integer, that many equal bins between the data's extremes
  (:func:`numpy.histogram_bin_edges`);
- a rule name such as ``"fd"`` or ``"auto"``, passed to the same function, or
  ``"knuth"`` for astropy's ``knuth_bin_width``;
- an array of edges, or another histogram's ``intervals``;
- in 2-D, a pair giving each axis its own specification.

``logx`` and ``logy`` bin :math:`\log_{10}|x|` instead of ``x``, so the bins
are equal in ratio. ``clip=True`` drops the points outside the 0.01st and
99.99th percentiles when the points are placed in bins (``"l"`` or ``"u"``
clips one tail); the bin edges still come from all the data.
:py:class:`~solarwindpy.plotting.spiral.SpiralPlot2D` instead takes
``initial_bins`` and ``min_per_bin``.

Edges given as an array are used as given:

>>> import pandas as pd
>>> from solarwindpy.plotting.hist1d import Hist1D
>>> rng = np.random.default_rng(0)
>>> v = pd.Series(rng.normal(400, 50, 1000), name="v")
>>> Hist1D(v, nbins=[250, 350, 450, 550]).intervals["x"]
IntervalIndex([(250, 350], (350, 450], (450, 550]], dtype='interval[int64, right]')

Normalizations
~~~~~~~~~~~~~~

``axnorm`` normalizes the aggregated values:

- ``None``: no normalization; counts, or the aggregated ``y`` or ``z``.
- ``"t"``: divide by the maximum, so the peak is 1.
- ``"d"``: divide by the total and by each bin's width (1-D) or area (2-D), a
  probability density. On a log axis the width is measured in
  :math:`\log_{10}`.
- ``"c"`` and ``"r"``: divide each column (``x`` bin) or row (``y`` bin) by its
  own maximum, so every column or row peaks at 1. Use them to compare shapes
  across ``x`` when the counts vary greatly with ``x``.
- ``"cd"`` and ``"rd"``: make each column or row a probability density along
  the other axis: divide by its total and by the bin width along that axis.

The binning decides which keys a plot accepts.
:py:class:`~solarwindpy.plotting.hist2d.Hist2D` accepts all six;
:py:class:`~solarwindpy.plotting.hist1d.Hist1D` and
:py:class:`~solarwindpy.plotting.spiral.SpiralPlot2D` accept ``"d"`` and
``"t"``, since they have no rows or columns; a
:py:class:`~solarwindpy.plotting.scatter.Scatter` has no bins and no
``axnorm``. Any other key raises:

>>> Hist1D(v).binning.allowed_axnorm
('d', 't')
>>> Hist1D(v, axnorm="c")
Traceback (most recent call last):
...
ValueError: Unrecognized axnorm 'c'; expected one of: d, t

With ``"c"`` or ``"r"`` the colorbar defaults to ten bands on [0, 1]; with the
densities it is logarithmic. Four normalizations of the same data:

.. plot::

   import numpy as np
   import pandas as pd
   import matplotlib.pyplot as plt
   from solarwindpy.plotting.hist2d import Hist2D
   from solarwindpy.plotting.labels.base import TeXlabel

   rng = np.random.default_rng(0)
   N = 20_000
   fast = rng.random(N) < 0.3
   v = pd.Series(np.where(fast, rng.normal(650, 60, N), rng.normal(380, 50, N)), name="v")
   n = (8 * 10 ** (-0.0015 * (v - 400) + rng.normal(0, 0.15, N))).rename("n")

   fig, axes = plt.subplots(2, 2, figsize=(9, 7), sharex=True, sharey=True)
   for ax, axnorm in zip(axes.flat, [None, "d", "c", "cd"]):
       h2 = Hist2D(v, n, logy=True, nbins=40, axnorm=axnorm)
       h2.set_labels(x=TeXlabel(("v", "", "p1")), y=TeXlabel(("n", "", "p1")))
       h2.make_plot(ax=ax)
       ax.set_title(f"axnorm={axnorm!r}")
       ax.label_outer()
   fig.tight_layout()

Labels
~~~~~~

A :py:class:`~solarwindpy.plotting.labels.base.TeXlabel` builds an axis label
from the same ``(M, C, S)`` key that names a column of the plasma's data: the
measurement's symbol, subscripted by the component and the species, and its
display units. The symbols and units come from the quantity registry,
:py:mod:`solarwindpy.core.quantities`. Leave the component or species empty
when there is none:

>>> from solarwindpy.plotting.labels.base import TeXlabel
>>> print(TeXlabel(("n", "", "p1")))
$n_{p_1} \; \left[\mathrm{cm}^{-3}\right]$
>>> print(TeXlabel(("b", "", "")))
$B \; \left[\mathrm{nT}\right]$
>>> print(TeXlabel(("v", "x", "a")))
${v}_{{X};{\alpha}} \; \left[\mathrm{km \; s^{-1}}\right]$

A derived quantity uses its plasma method's name as ``M``. Methods such as
:py:meth:`~solarwindpy.core.plasma.Plasma.T` and
:py:meth:`~solarwindpy.core.plasma.Plasma.beta` return columns ``par``,
``per`` and ``scalar``, and the label prints the component as given, so the
scalar column's key gives a literal "scalar" subscript. For the scalar, leave
the component empty:

>>> print(TeXlabel(("T", "par", "p1")))
${T}_{{\parallel};{p_1}} \; \left[10^5 \, \mathrm{K}\right]$
>>> print(TeXlabel(("T", "scalar", "p1")))
${T}_{{\mathrm{scalar}};{p_1}} \; \left[10^5 \, \mathrm{K}\right]$
>>> print(TeXlabel(("T", "", "p1")))
${T}_{{p_1}} \; \left[10^5 \, \mathrm{K}\right]$
>>> print(TeXlabel(("beta", "", "p1")))
${\beta}_{{p_1}} \; \left[\mathrm{\#}\right]$

A dimensionless quantity, such as :math:`\beta`, has the units
:math:`[\#]`. A second key makes a ratio:

>>> print(TeXlabel(("n", "", "a"), ("n", "", "p1")))
$n_{\alpha}/n_{p_1} \; \left[\#\right]$

A plot labels its axes ``x``, ``y`` and ``z`` until ``set_labels`` sets them.
A histogram's counts carry the special label
:py:class:`~solarwindpy.plotting.labels.special.Count`, which follows the
plot's ``axnorm``:

>>> from solarwindpy.plotting.hist2d import Hist2D
>>> h2 = Hist2D(v, (2 * v).rename("y"), axnorm="cd")
>>> print(h2.labels.z)
$\mathrm{1D \, Probability \, Density} \; \left[\#\right]$

``solarwindpy.plotting.labels.available()`` prints every measurement,
component and species ``TeXlabel`` knows, and the special labels.

Plot a Fit
----------

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

:py:meth:`~solarwindpy.fitfunctions.plots.FFPlot.plot_raw_used_fit_resid`
adds the residuals. The top panel shows the observations, the fitted curve and
an annotation with the fit function, its parameters and their uncertainties,
and the reduced chi-squared of each kind. The bottom panel shows the residuals,
observed minus fitted, against ``x``; the default ``resid_pct=True`` shows them
in percent of the fit instead, which is large wherever the fit nears zero.
The plotter labels its axes ``x`` and ``y`` until its ``set_labels`` sets
them, as for the plots above; here the counts of a velocity component. The
Gaussian is the seeded, noisy one whose results table
:doc:`tutorial/quickstart` prints:

.. plot::

   import numpy as np
   from solarwindpy.fitfunctions.gaussians import Gaussian
   from solarwindpy.plotting.labels.base import TeXlabel
   from solarwindpy.plotting.labels.special import Count

   rng = np.random.default_rng(1)
   x = np.linspace(-5, 5, 41)
   y = 10.0 * np.exp(-0.5 * ((x - 0.5) / 1.2) ** 2) + rng.normal(0.0, 0.3, x.size)
   fit = Gaussian(x, y)
   fit.make_fit()
   fit.plotter.set_labels(x=TeXlabel(("v", "x", "p1")), y=Count())
   fit.plotter.plot_raw_used_fit_resid(resid_kwargs=dict(resid_pct=False))

Next Steps
----------

- :doc:`missing_data` explains how missing measurements propagate.
- The :doc:`api_reference` documents every public class and function.
