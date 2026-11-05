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
An empty cell is NaN; when there are any, the filter averages only the
occupied cells and leaves the empty ones empty, rather than spreading each NaN
over its neighbours. ``plot_edges=True`` also draws the
edges of the occupied distribution
(:py:meth:`~solarwindpy.plotting.hist2d.Hist2D.plot_edges`): in each column of
``x`` bins, the highest and the lowest occupied ``y`` bin, smoothed by a
Savitzky-Golay filter unless ``edges_kwargs=dict(smooth=False)``. The
filter's default window is a tenth of the number of ``x`` bins, widened to fit
its cubic polynomial when there are few bins; set ``window_length`` in
``edges_kwargs=dict(sg_kwargs=...)`` to choose another. Here
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
   h2.plot_contours(use_contourf=True, gaussian_filter_std=2, plot_edges=True)

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

``Scatter(x, y, z)`` draws one marker per point, colored by ``z`` through a
colormap, beside a colorbar labelled with ``labels.z``; here ``z`` is the
density of a few hundred points. Its ``logx`` and ``logy`` set only the axis
scale; the data stay linear. ``make_plot`` returns
``(ax, points, segments, cbar)``: the axes, the markers' ``PathCollection``,
the segments joining the points (None here, see below) and the colorbar (None
when ``cbar=False`` or ``z`` does not vary).

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
   ax, points, segments, cbar = sc.make_plot(s=8)

``make_plot(connect=True)`` also joins the points with line segments in
increasing ``z``. The sort is stable, so points with equal ``z`` keep the order
of their rows, and the rows need not be sorted: below they are shuffled. Each
segment is colored by the mean ``z`` of its two points, through the markers'
colormap and norm, so the one colorbar reads both. With ``z`` the time of each
point, as here, the segments trace the trajectory; with any other ``z`` they
trace how ``(x, y)`` changes as ``z`` increases. A point that is not drawn (NaN
or infinite, outside ``mask`` or ``alim``, or not positive on a log axis) is
skipped, not a gap: the points either side of it in ``z`` are joined.
``connect_kwargs`` styles the segments, which sit just below the markers.

.. plot::

   import numpy as np
   import pandas as pd
   from solarwindpy.plotting.scatter import Scatter
   from solarwindpy.plotting.labels.base import TeXlabel

   rng = np.random.default_rng(1)
   N = 120
   epoch = pd.date_range("2020-01-01", periods=N, freq="3D")
   days = pd.Series((epoch - epoch[0]).days, index=epoch, name="days")

   # A slow drift through (v, n) with a solar-rotation wobble and noise.
   phase = 2 * np.pi * days / 27
   v = pd.Series(
       400 + 1.2 * days.to_numpy() ** 0.8 + 60 * np.sin(phase) + rng.normal(0, 15, N),
       index=epoch,
       name="v",
   )
   n = pd.Series(
       8 * np.exp(-days / 400) + 2 * np.cos(phase) + rng.normal(0, 0.4, N),
       index=epoch,
       name="n",
   )

   # Shuffle the rows: the points are joined in increasing z, not row order.
   shuffled = rng.permutation(N)
   v, n, days = v.iloc[shuffled], n.iloc[shuffled], days.iloc[shuffled]

   sc = Scatter(v, n, days)
   sc.set_labels(
       x=TeXlabel(("v", "", "p1")),
       y=TeXlabel(("n", "", "p1")),
       z="Days from start",
   )
   ax, points, segments, cbar = sc.make_plot(
       s=12, cmap="viridis", connect=True, connect_kwargs={"linewidth": 0.8, "alpha": 0.8}
   )

Over decades, the colorbar can carry the solar cycle. With ``z`` the time of
each point in matplotlib's date units, ``SIDC("m13").plot_on_colorbar`` draws
the 13-month smoothed sunspot number along the colorbar, so each segment's
color places it in the cycle. ``SIDC("m13")`` downloads the series from SILSO
(https://www.sidc.be/SILSO/) and keeps it in SolarWindPy's download cache for
a day. The sunspot number's own scale is left unlabelled here: the line shows
the cycle's phase, not its amplitude.

.. plot::

   import matplotlib.dates as mdates
   import numpy as np
   import pandas as pd
   from solarwindpy.plotting.scatter import Scatter
   from solarwindpy.plotting.labels.base import TeXlabel
   from solarwindpy.solar_activity.sunspot_number.sidc import SIDC

   rng = np.random.default_rng(3)
   epoch = pd.date_range("1994-01-01", "2026-01-01", freq="QS")
   N = epoch.size

   # Quarterly means that circle once per 11-year cycle, peaking near 2002,
   # 2013 and 2024.
   year = epoch.year + (epoch.month - 1) / 12
   phase = 2 * np.pi * (year - 1996.5) / 11
   v = pd.Series(440 + 50 * np.sin(phase) + rng.normal(0, 6, N), index=epoch, name="v")
   b = pd.Series(
       5.75 - 1.25 * np.cos(phase) + rng.normal(0, 0.15, N), index=epoch, name="b"
   )
   # Time as z, in matplotlib's date units: the units the colorbar's SSN uses.
   t = pd.Series(mdates.date2num(epoch), index=epoch, name="t")

   sc = Scatter(v, b, t)
   sc.set_labels(x=TeXlabel(("v", "", "p1")), y=TeXlabel(("b", "", "")), z="Year")
   ax, points, segments, cbar = sc.make_plot(
       s=14, cmap="viridis", connect=True, cbar_kwargs={"aspect": 8}
   )
   cbar.ax.yaxis.set_major_locator(mdates.YearLocator(4))
   cbar.ax.yaxis.set_major_formatter(mdates.DateFormatter("%Y"))

   # The 13-month smoothed sunspot number along the colorbar, downloaded from SILSO.
   SIDC("m13").plot_on_colorbar(cbar.ax, epoch[0], epoch[-1])
   cbar.ax.set_xlabel("")
   cbar.ax.xaxis.set_major_locator(mdates.ticker.NullLocator())
   cbar.ax.xaxis.set_minor_locator(mdates.ticker.NullLocator())
   cbar.ax.set_title("SSN", fontsize="medium")

Without ``z``, ``Scatter(x, y)`` draws every point in one color and no
colorbar, so ``cbar`` is None. ``connect=True`` then joins the points in the
order of their rows, in the markers' color, skipping any point that is not
drawn. Here the rows are in time order, so the segments trace the field's
rotation:

.. plot::

   import numpy as np
   import pandas as pd
   from solarwindpy.plotting.scatter import Scatter
   from solarwindpy.plotting.labels.base import TeXlabel

   rng = np.random.default_rng(2)
   N = 80
   epoch = pd.date_range("2020-01-01", periods=N, freq="15min")
   angle = np.linspace(0, 1.5 * np.pi, N)
   bx = pd.Series(5 * np.cos(angle) + rng.normal(0, 0.3, N), index=epoch, name="bx")
   by = pd.Series(5 * np.sin(angle) + rng.normal(0, 0.3, N), index=epoch, name="by")

   sc = Scatter(bx, by)
   sc.set_labels(x=TeXlabel(("b", "x", "")), y=TeXlabel(("b", "y", "")))
   ax, points, segments, cbar = sc.make_plot(s=12, connect=True)

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

Share bins across plots
~~~~~~~~~~~~~~~~~~~~~~~

Plots over the same columns and bins can share one
:py:class:`~solarwindpy.plotting.binned.BinnedData`. It bins each column once,
when it is built, and stores the bin of every row as a small integer code.
Passed as ``nbins``, it gives a :py:class:`~solarwindpy.plotting.hist1d.Hist1D`
or :py:class:`~solarwindpy.plotting.hist2d.Hist2D` its bins and codes, so the
plot neither bins nor stores its own. A plot finds its columns by the names of
its inputs, so build the ``BinnedData`` from a DataFrame whose columns carry
those names, and pass that frame's columns. It takes explicit edges only: a
count or a rule would give each plot edges that depend on the rows it keeps.
``log`` names the columns binned in :math:`\log_{10}`, and the plots take
their log axes from it. A plot's ``mask`` keeps a subset of the rows on the
same bins:

>>> import numpy as np
>>> import pandas as pd
>>> from solarwindpy.plotting.binned import BinnedData
>>> from solarwindpy.plotting.hist2d import Hist2D
>>> rng = np.random.default_rng(0)
>>> N = 10_000
>>> fast = rng.random(N) < 0.3
>>> speed = np.where(fast, rng.normal(650, 60, N), rng.normal(380, 50, N))
>>> frame = pd.DataFrame(
...     {
...         "v": speed,
...         "n": 8 * 10 ** (-0.0015 * (speed - 400) + rng.normal(0, 0.15, N)),
...         "w": 0.1 * speed + rng.normal(0, 5, N),
...     }
... )
>>> edges = {"v": np.linspace(0, 1000, 51), "n": np.linspace(-1, 2.5, 36)}
>>> binned = BinnedData(frame, edges, log={"n": True})
>>> binned.codes("v").dtype
dtype('int8')
>>> counts = Hist2D(frame["v"], frame["n"], nbins=binned)
>>> mean_w = Hist2D(frame["v"], frame["n"], frame["w"], nbins=binned)
>>> slow = Hist2D(frame["v"], frame["n"], nbins=binned, mask=frame["v"] < 500)
>>> counts.agg().index.equals(mean_w.agg().index)
True
>>> int(counts.agg().sum()) == N
True
>>> int(slow.agg().sum()) == int((frame["v"] < 500).sum())
True

Every point lies inside the edges, so the counts add up to the rows a plot
keeps. A plot passed an unnamed Series, or one renamed after the
``BinnedData`` was built, cannot find its column:

>>> Hist2D(pd.Series(speed), frame["n"], nbins=binned)
Traceback (most recent call last):
...
KeyError: "The BinnedData has no column None, the name of x; its columns are ('v', 'n')."

Sharing saves time and memory. Building and aggregating ten ``Hist2D`` of
different ``z`` over one 70 by 50 grid of :math:`10^6` points took 0.17 s with
a shared ``BinnedData`` and 0.34 s when each plot binned its own columns, the
median of three runs on an Apple M3 (Python 3.12, pandas 3.1, NumPy 2.5).
Measured with :mod:`tracemalloc`, which counts Python and NumPy allocations,
the ten plots and their aggregates kept 3 MB against 21 MB, and the build
peaked at 52 MB against 71 MB. The script that measures them,
:download:`benchmark_binned_data.py <../../scripts/benchmark_binned_data.py>`,
prints the numbers for your machine.

Two plots on one ``BinnedData``, the counts and the mean thermal speed in each
cell:

.. plot::

   import numpy as np
   import pandas as pd
   import matplotlib.pyplot as plt
   from solarwindpy.plotting.binned import BinnedData
   from solarwindpy.plotting.hist2d import Hist2D
   from solarwindpy.plotting.labels.base import TeXlabel

   rng = np.random.default_rng(0)
   N = 20_000
   fast = rng.random(N) < 0.3
   v = np.where(fast, rng.normal(650, 60, N), rng.normal(380, 50, N))
   frame = pd.DataFrame(
       {
           "v": v,
           "n": 8 * 10 ** (-0.0015 * (v - 400) + rng.normal(0, 0.15, N)),
           "w": 0.1 * v + rng.normal(0, 5, N),
       }
   )
   edges = {"v": np.linspace(150, 950, 51), "n": np.linspace(-0.2, 1.8, 41)}
   binned = BinnedData(frame, edges, log={"n": True})

   counts = Hist2D(frame["v"], frame["n"], nbins=binned)
   mean_w = Hist2D(frame["v"], frame["n"], frame["w"], nbins=binned)
   mean_w.set_labels(z=TeXlabel(("w", "", "p1")))

   fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
   for h2, ax in zip([counts, mean_w], axes):
       h2.set_labels(x=TeXlabel(("v", "", "p1")), y=TeXlabel(("n", "", "p1")))
       h2.make_plot(ax=ax)
   axes[1].set_ylabel("")
   fig.tight_layout()

Normalizations
~~~~~~~~~~~~~~

``axnorm`` normalizes the aggregated values, and what it computes depends on
the aggregation, ``make_plot``'s ``fcn``. For cell :math:`i`, let
:math:`n_i` be its rows, :math:`A_i` its area (its width in 1-D, measured in
:math:`\log_{10}` along a log axis), :math:`v_i` its aggregated value and
:math:`S_i` the sum of ``z`` over its rows; :math:`N = \sum_i n_i` and
:math:`S = \sum_i S_i` run over the cells the plot shows. There are three
families, a density ``"d"``, a weight ``"w"`` and a scaling ``"t"``:

.. list-table::
   :header-rows: 1

   * - aggregation
     - ``"d"``
     - ``"w"``
     - ``"t"``
   * - a count (no ``z``, or ``fcn="count"``)
     - :math:`n_i / (N A_i)`
     - :math:`n_i / N`
     - :math:`n_i / \max_j n_j`
   * - a sum (``fcn="sum"`` or :func:`numpy.sum`)
     - :math:`S_i / (S A_i)`
     - :math:`S_i / S`
     - :math:`S_i / \max_j |S_j|`
   * - any other (``"mean"``, ``"median"``, a callable)
     - :math:`v_i n_i / (N A_i)`
     - :math:`v_i n_i / N`
     - :math:`v_i / \max_j |v_j|`

- A count's ``"d"`` is the probability density, :math:`\sum_i d_i A_i = 1`,
  and its ``"w"`` the fraction of the rows in each cell, which sums to 1.
- A sum's ``"d"`` and ``"w"`` are each cell's share of the total ``z``, per
  unit area for ``"d"``. A share needs ``z`` >= 0, so a negative ``z`` in a
  cell raises ``ValueError``. A callable that adds is still "any other"; pass
  ``"sum"`` for a share.
- Any other aggregation is weighted by its rows: ``"d"`` integrates, and
  ``"w"`` sums, to :math:`\sum_i v_i n_i / N`, the count-weighted average of
  :math:`v`. For a mean that is the mean ``z`` of the rows shown, so ``"w"``
  shows how much each cell contributes to it.
- ``"t"`` divides by the largest magnitude, so the peak is 1, or -1 when the
  largest value is negative.

``"cd"``, ``"wc"`` and ``"c"`` do the same within each column (``x`` bin):
:math:`N` and :math:`S` are the column's, the area is the bin's height, and
``"c"`` divides by the column's largest magnitude. ``"rd"``, ``"wr"`` and
``"r"`` do it within each row (``y`` bin). Use ``"c"`` or ``"cd"`` to compare
the shape of ``y`` across ``x`` when the counts vary greatly with ``x``. The
sums hold to rounding:

>>> from solarwindpy.plotting.hist2d import Hist2D
>>> h1 = Hist1D(v, nbins=20, axnorm="d")
>>> round(float((h1.agg() * h1.intervals["x"].length).sum()), 6)
1.0
>>> y = (v / 100 + rng.normal(0, 0.5, v.size)).rename("y")
>>> round(float(Hist2D(v, y, nbins=10, axnorm="w").agg().sum()), 6)
1.0
>>> z = (v - 400).rename("z")
>>> mean_z = Hist2D(v, y, z, nbins=10, axnorm="w").agg(fcn="mean")
>>> bool(np.isclose(mean_z.sum(), z.mean()))
True

The binning decides which keys a plot accepts.
:py:class:`~solarwindpy.plotting.hist2d.Hist2D` accepts all nine;
:py:class:`~solarwindpy.plotting.hist1d.Hist1D` and
:py:class:`~solarwindpy.plotting.spiral.SpiralPlot2D` accept ``"d"``, ``"t"``
and ``"w"``, since they have no rows or columns; a
:py:class:`~solarwindpy.plotting.scatter.Scatter` has no bins and no
``axnorm``. Any other key raises:

>>> Hist1D(v).binning.allowed_axnorm
('d', 't', 'w')
>>> Hist1D(v, axnorm="c")
Traceback (most recent call last):
...
ValueError: Unrecognized axnorm 'c'; expected one of: d, t, w

The colour scale follows the values. Values of both signs get a scale centred
on zero, :class:`~matplotlib.colors.CenteredNorm` with the diverging colormap
``RdBu_r``, whatever the ``axnorm``. Otherwise ``"c"`` and ``"r"`` get ten
bands on [0, 1] and the densities a logarithmic scale. A ``norm`` or ``cmap``
passed to ``make_plot`` is used as given. Four normalizations of the same
counts:

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

A density of the counts against the weight of a signed mean: the left panel
is where the rows are, and the right is how much each cell adds to the mean
:math:`B_x`, here positive in the fast wind and negative in the slow. Its
values hold both signs, so the scale is centred on zero, and its cells sum to
the mean :math:`B_x` of all the rows:

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
   bx = (0.01 * (v - 450) + rng.normal(0, 2, N)).rename("bx")

   pdf = Hist2D(v, n, logy=True, nbins=40, axnorm="d")
   weight = Hist2D(v, n, bx, logy=True, nbins=40, axnorm="w")
   weight.set_labels(z=TeXlabel(("b", "x", ""), axnorm="w"))

   fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
   for h2, ax in zip([pdf, weight], axes):
       h2.set_labels(x=TeXlabel(("v", "", "p1")), y=TeXlabel(("n", "", "p1")))
   pdf.make_plot(ax=axes[0])
   weight.make_plot(ax=axes[1], fcn="mean")
   axes[0].set_title('count, axnorm="d"')
   axes[1].set_title('mean $B_x$, axnorm="w"')
   axes[1].set_ylabel("")
   fig.tight_layout()

Select the data a figure shows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Two limits decide which cells a binned plot shows. ``set_clim`` bounds the
number of rows in a cell; ``set_alim`` bounds the aggregated value, after
``axnorm`` and ``clim``. Bounds are inclusive and None leaves a side open;
``set_alim(..., kind="quantile")`` reads them as quantiles of the aggregated
values. A cell outside either limit is NaN in ``agg`` and blank in the figure.
Every binned plot, ``Hist1D`` included, has both. Here the bins with at least
20 rows, then the bins at least a tenth of the peak:

>>> h1 = Hist1D(v, nbins=20)
>>> counts = h1.agg()
>>> h1.set_clim(20, None)
>>> h1.agg().notna().equals(counts >= 20)
True
>>> peak = Hist1D(v, nbins=20, axnorm="t")
>>> peak.set_alim(0.1, None)
>>> peak.agg().notna().equals(counts >= 0.1 * counts.max())
True

``get_plotted_data`` returns the rows in the cells the figure shows: the
values you passed, on your index, in your order. Its rows are the ones the
shown bins count:

>>> len(h1.get_plotted_data()) == int(counts[counts >= 20].sum())
True

``alim`` acts on the aggregated value, so pass the ``fcn`` you give
``make_plot``. Here the cells with at least 10 rows whose mean ``z`` is not
negative:

>>> h2 = Hist2D(v, y, z, nbins=10)
>>> h2.set_clim(10, None)
>>> h2.set_alim(0, None)
>>> rows = h2.get_plotted_data(fcn="mean")
>>> list(rows.columns)
['x', 'y', 'z']
>>> shown = h2.agg(fcn="mean").notna()
>>> len(rows) == int(Hist2D(v, y, nbins=10).agg()[shown].sum())
True

For a boolean mask over your data, use ``v.index.isin(rows.index)`` on a
unique index.

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
${v}_{{x};{\alpha}} \; \left[\mathrm{km \; s^{-1}}\right]$

A derived quantity uses its plasma method's name as ``M``. Methods such as
:py:meth:`~solarwindpy.core.plasma.Plasma.T` and
:py:meth:`~solarwindpy.core.plasma.Plasma.beta` return columns ``par``,
``per`` and ``scalar``. The scalar column's label is the bare symbol, the same
as with the component left empty:

>>> print(TeXlabel(("T", "par", "p1")))
${T}_{{\parallel};{p_1}} \; \left[10^5 \, \mathrm{K}\right]$
>>> print(TeXlabel(("T", "scalar", "p1")))
${T}_{{p_1}} \; \left[10^5 \, \mathrm{K}\right]$
>>> print(TeXlabel(("beta", "", "p1")))
${\beta}_{{p_1}} \; \left[\#\right]$

A dimensionless quantity, such as :math:`\beta`, has the units
:math:`[\#]`. A second key makes a ratio:

>>> print(TeXlabel(("n", "", "a"), ("n", "", "p1")))
$n_{\alpha}/n_{p_1} \; \left[\#\right]$

A plot labels its axes ``x``, ``y`` and ``z`` until ``set_labels`` sets them.
A histogram's counts carry the special label
:py:class:`~solarwindpy.plotting.labels.special.Count`, which follows the
plot's ``axnorm``. A count divided by a maximum is a pure number, :math:`[\#]`;
a density is per unit width or area of the bins, so its label states the
inverse of the binned axes' units, :math:`\mathrm{dex}^{-1}` for a log axis. Here
the axes are labelled by plain strings, which state no units:

>>> from solarwindpy.plotting.hist2d import Hist2D
>>> h2 = Hist2D(v, (2 * v).rename("y"), axnorm="t")
>>> print(h2.labels.z)
$\mathrm{Count \, / \, Max} \; \left[\#\right]$
>>> h2 = Hist2D(v, (2 * v).rename("y"), axnorm="cd")
>>> print(h2.labels.z)
$\mathrm{Column \, Probability \, Density}$

``solarwindpy.plotting.labels.available()`` prints every measurement,
component and species ``TeXlabel`` knows, and the special labels.

Publication format
~~~~~~~~~~~~~~~~~~

In publication format a label is two lines: its name in words over its symbol
and units. Turn it on for one label with ``publication_format=True``, or for
every label with
:py:func:`~solarwindpy.plotting.labels.base.set_publication_format`, which
:py:func:`~solarwindpy.plotting.labels.base.publication_format` reads back. A
label's own setting overrides the default. The name comes from the quantity
registry; ``name=`` replaces it, and a ratio is named after its parts:

>>> print(TeXlabel(("n", "", "p1"), publication_format=True))
Number Density
$n_{p_1} \; \left[\mathrm{cm}^{-3}\right]$
>>> print(TeXlabel(("v", "", "p1"), name="Solar Wind Speed", publication_format=True))
Solar Wind Speed
${v}_{{p_1}} \; \left[\mathrm{km \; s^{-1}}\right]$
>>> print(TeXlabel(("n", "", "a"), ("n", "", "p1"), publication_format=True))
Number Density Ratio
$n_{\alpha}/n_{p_1} \; \left[\#\right]$

A :py:class:`~solarwindpy.plotting.labels.special.Count` in publication format
is its normalization's name over a symbol: :math:`N` for a count,
:math:`N / N_{\max}` for ``"t"``, :math:`N / N_{\mathrm{tot}}` for ``"w"``
and :math:`p` for a probability density. A density's units are the inverse of
the binned axes' units, :math:`\mathrm{dex}^{-1}` along a log axis, read from
the plot's axis labels:

>>> from solarwindpy.plotting.labels.base import set_publication_format
>>> from solarwindpy.plotting.labels.special import Count
>>> print(Count(norm="w", publication_format=True))
Count Fraction
$N / N_{\mathrm{tot}} \; \left[\#\right]$
>>> h2 = Hist2D(v, y, logy=True, axnorm="d")
>>> h2.set_labels(x=TeXlabel(("v", "", "p1")), y=TeXlabel(("n", "", "p1")))
>>> set_publication_format(True)
>>> print(h2.labels.z)
Probability Density
$p \; \left[\left(\mathrm{km \; s^{-1}}\right)^{-1} \, \mathrm{dex}^{-1}\right]$
>>> print(TeXlabel(("n", "", "p1"), publication_format=False))
$n_{p_1} \; \left[\mathrm{cm}^{-3}\right]$
>>> set_publication_format(False)

Labels read the default when they are drawn, so ``set_publication_format``
also changes the labels of plots already built. A figure in publication
format, its speed axis renamed:

.. plot::

   import numpy as np
   import pandas as pd
   from solarwindpy.plotting.hist2d import Hist2D
   from solarwindpy.plotting.labels.base import TeXlabel, set_publication_format

   set_publication_format(True)  # every label: its name over its symbol

   rng = np.random.default_rng(0)
   N = 20_000
   fast = rng.random(N) < 0.3
   v = pd.Series(np.where(fast, rng.normal(650, 60, N), rng.normal(380, 50, N)), name="v")
   n = (8 * 10 ** (-0.0015 * (v - 400) + rng.normal(0, 0.15, N))).rename("n")

   h2 = Hist2D(v, n, logy=True, nbins=50, axnorm="d")
   h2.set_labels(
       x=TeXlabel(("v", "", "p1"), name="Solar Wind Speed"),  # replaces the name
       y=TeXlabel(("n", "", "p1")),  # the registry's name, "Number Density"
   )
   h2.make_plot()

   set_publication_format(False)  # restore the one-line default

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
fitted to the data whose unweighted results table :doc:`tutorial/quickstart`
prints, here with ``yerr``, the 1-sigma uncertainty of each ``y`` (the
noise's 0.3). The plot shades the observations :math:`\pm` ``yerr``, and the
annotation is this weighted fit's:

.. plot::

   import numpy as np
   from solarwindpy.fitfunctions.gaussians import Gaussian
   from solarwindpy.plotting.labels.base import TeXlabel
   from solarwindpy.plotting.labels.special import Count

   rng = np.random.default_rng(1)
   x = np.linspace(-5, 5, 41)
   y = 10.0 * np.exp(-0.5 * ((x - 0.5) / 1.2) ** 2) + rng.normal(0.0, 0.3, x.size)
   fit = Gaussian(x, y, yerr=np.full(x.size, 0.3))
   fit.make_fit()
   fit.plotter.set_labels(x=TeXlabel(("v", "x", "p1")), y=Count())
   fit.plotter.plot_raw_used_fit_resid(resid_kwargs=dict(resid_pct=False))

Next Steps
----------

- :doc:`missing_data` explains how missing measurements propagate.
- The :doc:`api_reference` documents every public class and function.
