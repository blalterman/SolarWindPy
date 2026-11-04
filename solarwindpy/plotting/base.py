#!/usr/bin/env python
r"""Base classes for plotting utilities.

``Base`` manages the data, axis labels, log scaling, and the path for saving
figures that every plot shares. ``ColorPlot`` adds a z value shown on a
colorbar; ``BinnedPlot`` aggregates a value in the cells of a
:class:`~solarwindpy.plotting.binning.Binning`. Concrete plots derive from
them.
"""

__all__ = [
    "LogAxes",
    "ClipAxes",
    "AxesLabels",
    "RangeLimits",
    "Base",
    "ColorPlot",
    "BinnedPlot",
]

import logging
import numpy as np
import pandas as pd
import matplotlib as mpl

from numbers import Number
from pathlib import Path
from collections import namedtuple
from collections.abc import Mapping
from abc import ABC, abstractmethod

from . import labels
from .binned import BinnedData, _PlotSource, _clip_kind, _clip_to_quantiles
from .binning import FixedGrid

LogAxes = namedtuple("LogAxes", "x,y", defaults=(False,))
#: Clip setting per axis: False, True, or a clip string (see ``Base.clip_data``).
#: ``z`` is clipped by ``Scatter`` only. Test a field, never the record: a
#: ``ClipAxes(False, False)`` is a non-empty tuple, so it is truthy.
ClipAxes = namedtuple("ClipAxes", "x,y,z", defaults=(False, False))
AxesLabels = namedtuple("AxesLabels", "x,y,z", defaults=(None,))
RangeLimits = namedtuple("RangeLimits", "lower,upper", defaults=(None,))


class Base(ABC):
    r"""Abstract base for SolarWindPy plots.

    Holds the axis labels and the log-scale flags that every concrete plot
    shares, and derives the save path from them. Subclasses implement
    ``_set_data``, which only their constructors call, and ``make_plot``. To
    plot other data, build a new plot.

    A built plot is a snapshot of its data. ``_set_data`` runs once per plot
    (``_claim_data`` raises ``ValueError`` on a second call), and pandas
    copies on write, so editing the caller's frame or Series afterwards does
    not change the plot. Not guarded: editing a NumPy array that a Series
    wraps without a copy (``pd.Series(arr, copy=False)``) after the plot is
    built changes what the plot holds.
    """

    @abstractmethod
    def __init__(self):
        r"""Set default labels ``x`` and ``y`` and linear axes."""
        self._init_logger()
        self._labels = AxesLabels(x="x", y="y")
        self._log = LogAxes(x=False)

    def __str__(self):
        return self.__class__.__name__

    @property
    def logger(self):
        r"""Logger named ``<module>.<class name>``."""
        return self._logger

    def _init_logger(self):
        logger = logging.getLogger("{}.{}".format(__name__, self.__class__.__name__))
        self._logger = logger

    @property
    def data(self):
        r"""The plot's data: a new DataFrame built from its source on each access.

        It holds the rows the plot keeps (no NaN or +/-inf in any column,
        a logarithmic axis taken after ``log10(abs())``, so no 0 there;
        within the caller's ``mask`` and a shared ``BinnedData``'s mask),
        with each logarithmic axis as ``log10(abs())``. Nothing is stored between
        accesses, so edits to the returned frame do not persist, and the
        arrays of its columns (``to_numpy()``) are read-only. The plot's data
        is set once, by its constructor; to plot other data, build a new
        plot.
        """
        return self._source.materialize()

    #: The axes the ``clip`` argument applies to, in ``ClipAxes`` field order.
    _clipped_axes = ("x", "y")

    @property
    def clip(self):
        r"""``ClipAxes`` of each axis's clip setting: False, True, or a clip string.

        Axes the plot does not clip are False.
        """
        return self._clip

    def _clip_by_axis(self, clip):
        r"""Map each axis in ``_clipped_axes`` to its clip setting, None if unset.

        Parameters
        ----------
        clip : bool, str, None, Mapping or ClipAxes
            A scalar applies to every axis in ``_clipped_axes``. A mapping
            gives an axis its own setting; unnamed axes are None. A
            ``ClipAxes`` is read as a mapping of its fields, ignoring False
            fields for axes this plot does not clip.

        Raises
        ------
        KeyError
            If a mapping names an axis this plot does not clip.
        """
        axes = self._clipped_axes
        if isinstance(clip, ClipAxes):
            clip = {k: v for k, v in clip._asdict().items() if k in axes or v}
        if not isinstance(clip, Mapping):
            return {k: clip for k in axes}
        unknown = [k for k in clip if k not in axes]
        if unknown:
            raise KeyError(
                f"{self.__class__.__name__} clips the axes {axes!r}; clip names "
                f"{unknown!r}."
            )
        return {k: clip.get(k) for k in axes}

    def _store_clip(self, clip):
        r"""Store ``clip``, read by ``_clip_by_axis``, as ``ClipAxes``; None is False.

        Raises
        ------
        ValueError
            If an axis's setting is a string other than those
            ``Base.clip_data`` accepts.
        """
        by_axis = self._clip_by_axis(clip)
        for v in by_axis.values():
            _clip_kind(v)
        self._clip = ClipAxes(
            **{k: False if v is None else v for k, v in by_axis.items()}
        )

    @property
    def log(self):
        r"""``LogAxes`` namedtuple of booleans: True where an axis is logarithmic."""
        return self._log

    @property
    def labels(self):
        r"""``AxesLabels`` namedtuple holding the x, y and z labels."""
        return self._labels

    @property
    def path(self):
        r"""Save path describing the plot as it is now.

        Derived on every read, never stored: ``class / x / y [/ z] / scale``.
        Each axis contributes its label's ``path``, or the label string with
        spaces as hyphens; a label that is neither falls back to the axis
        name. The z part is present only when ``labels.z`` is not None. The
        scale tag is ``linX`` or ``logX``, then ``linY`` or ``logY``, joined
        by ``-``. When the last part ends in ``norm`` (a normalized ``Count``
        label, e.g. ``count/Cnorm``), the scale tag goes before it, so the
        last part reads the x, y and z scaling in order
        (``.../count/linX-linY-Cnorm``).

        Returns
        -------
        pathlib.Path
            Relative path; join it to a directory to save under, e.g.
            ``Path("figs") / plot.path``.
        """
        labels = self.labels
        parts = [self._path_part(labels.x, "x"), self._path_part(labels.y, "y")]
        if not (labels.z is None or (isinstance(labels.z, str) and labels.z == "None")):
            parts.append(self._path_part(labels.z, "z"))
        path = Path(self.__class__.__name__, *parts)

        scale = "{}X-{}Y".format(
            "log" if self.log.x else "lin", "log" if self.log.y else "lin"
        )
        if path.name.endswith("norm"):
            return path.with_name(f"{scale}-{path.name}")
        return path / scale

    @staticmethod
    def _path_part(label, axis):
        r"""One axis's part of ``path``: the label's own ``path``, or its string."""
        try:
            return Path(label.path)
        except AttributeError:
            pass
        if isinstance(label, str) and label != "None":
            return Path(label.replace(" ", "-"))
        return Path(axis)

    def set_log(self, x=None, y=None):
        r"""Set which axes use a logarithmic scale.

        A plot's constructor sets the log of the axes its data is built on:
        which rows it keeps, the values it holds (``log10(abs())``) and its
        bins depend on it. Once the plot is built, ``set_log`` cannot change
        those axes; build a new plot (or a new ``BinnedData``) instead. Axes
        only drawn on a log scale, such as the y of a ``Hist1D`` or both axes
        of a ``Scatter``, can still be changed.

        Parameters
        ----------
        x, y : bool, optional
            If True, the axis is logarithmic. None keeps the current value.

        Raises
        ------
        ValueError
            If the plot is built and the call would change the log of an axis
            its data and bins were built on. Passing the value it already has
            is allowed.
        """
        if x is None:
            x = self.log.x
        if y is None:
            y = self.log.y

        log = LogAxes(bool(x), bool(y))
        source = self.__dict__.get("_source")
        if source is not None:
            changed = [
                k
                for k in source.log_columns
                if k in log._fields and getattr(log, k) != getattr(self.log, k)
            ]
            if changed:
                raise ValueError(
                    f"Can't change the log of {changed!r} on a built "
                    f"{self.__class__.__name__}: its data and bins depend on "
                    "log. To use another scale, build a new plot or "
                    "BinnedData."
                )
        self._log = log

    @staticmethod
    def clip_data(data, clip):
        r"""Clip data to its 0.01st and 99.99th percentiles.

        The one clipping rule every plot shares: each axis's setting in a
        plot's ``clip`` (a ``ClipAxes``) is handed here as ``clip``. The
        percentiles are computed over the finite values only; +/-inf is
        clipped to them like any other value beyond a percentile, when that
        tail is clipped, and NaN stays NaN. A column with no finite value is
        unchanged.

        Parameters
        ----------
        data : pd.Series or pd.DataFrame
            Data to clip. A DataFrame is clipped column by column.
        clip : bool or str
            ``"l"`` or ``"lower"`` clips the lower tail only, ``"u"`` or
            ``"upper"`` the upper tail only, in any case; ``"both"`` and any
            value that is not a string clip both tails.

        Returns
        -------
        pd.Series or pd.DataFrame
            The clipped data.

        Raises
        ------
        TypeError
            If ``data`` is neither a Series nor a DataFrame.
        ValueError
            If ``clip`` is any other string, the empty string included.
        """
        return _clip_to_quantiles(data, clip)

    def set_labels(self, **kwargs):
        r"""Set or update the x, y, or z labels.

        Any label not passed keeps its current value in ``self.labels``.

        Parameters
        ----------
        x, y, z : str or solarwindpy.plotting.labels.base.TeXlabel, optional
            New axis labels.

        Raises
        ------
        KeyError
            If any other keyword is passed.
        """
        x = kwargs.pop("x", self.labels.x)
        y = kwargs.pop("y", self.labels.y)
        z = kwargs.pop("z", self.labels.z)

        if len(kwargs.keys()):
            extra = "\n".join(["{}: {}".format(k, v) for k, v in kwargs.items()])
            raise KeyError("Unexpected kwarg\n{}".format(extra))

        self._labels = AxesLabels(x, y, z)

    def _add_axis_labels(self, ax, transpose_axes=False):
        xlbl = self.labels.x
        ylbl = self.labels.y

        if transpose_axes:
            xlbl, ylbl = ylbl, xlbl

        if xlbl is not None:
            ax.set_xlabel(xlbl)

        if ylbl is not None:
            ax.set_ylabel(ylbl)

    def _set_axis_scale(self, ax, transpose_axes=False):
        logx = self.log.x
        logy = self.log.y

        if transpose_axes:
            logx, logy = logy, logx

        if logx:
            ax.set_xscale("log")
        if logy:
            ax.set_yscale("log")

    def _format_axis(self, ax, transpose_axes=False):
        self._add_axis_labels(ax, transpose_axes=transpose_axes)
        self._set_axis_scale(ax, transpose_axes=transpose_axes)
        ax.grid(True, which="major", axis="both")
        ax.tick_params(axis="both", which="both", direction="inout")

    @abstractmethod
    def _set_data(self):
        r"""Store the data to plot. Implemented by each subclass.

        Called only by the constructor, so a plot's data never changes after
        it is built. Each implementation calls ``_claim_data`` first.
        """
        pass

    def _claim_data(self):
        r"""Mark the plot's data as set; raise if it already was.

        Raises
        ------
        ValueError
            If ``_set_data`` already ran on this plot.
        """
        if self.__dict__.get("_data_set", False):
            raise ValueError(
                f"{self.__class__.__name__} data is set once, by the constructor; "
                "to plot other data, build a new plot."
            )
        self._data_set = True

    @abstractmethod
    def make_plot(self):
        r"""Draw the plot. Implemented by each subclass."""
        pass


class ColorPlot(Base):
    r"""Base for plots of x and y coloured by a z value, with a colorbar.

    Holds the data intake of (x, y, z), the z label the colorbar shows, and
    ``alim``, the limits on the coloured values.
    """

    _alim = RangeLimits(None, None)
    _alim_kind = "value"
    #: Default linestyles of the contour levels, cycled when there are more.
    _contour_linestyles = (
        "-",
        ":",
        "--",
        (0, (7, 3, 1, 3, 1, 3, 1, 3, 1, 3)),
        "--",
        ":",
        "-",
        (0, (7, 3, 1, 3, 1, 3)),
    )
    # True where ``_set_data`` stores x and y as ``log10(abs())`` per ``self.log``.
    _log_data = False

    @property
    def alim(self):
        r"""``RangeLimits`` on the aggregated value; see ``set_alim``."""
        return self._alim

    @property
    def alim_kind(self):
        r"""``"value"`` or ``"quantile"``: how ``alim`` is read; see ``set_alim``."""
        return self._alim_kind

    def set_alim(self, lower=None, upper=None, kind="value"):
        r"""Set the minimum (lower) and maximum (upper) allowed aggregated value.

        Unlike ``clim``, which limits the number of points in a bin, ``alim``
        limits the value a bin aggregates to, after ``axnorm``, ``clim`` and
        any cell filter. Bins outside ``[lower, upper]`` become NaN; bounds are
        inclusive and None leaves that side open. A ``Scatter`` applies
        ``alim`` to the z of each point and does not draw the points outside.

        Parameters
        ----------
        lower, upper : float or None
            The limits.
        kind : {"value", "quantile"}
            ``"value"``: the limits are aggregated values. ``"quantile"``: the
            limits are quantiles in [0, 1] of the final aggregated values,
            computed with :func:`numpy.nanquantile` over the finite values
            (NaN and inf excluded) each time the plot aggregates. The
            quantiles pool every bin of the plot: with ``axnorm`` of ``"c"``
            or ``"r"`` they are taken over the whole grid, not per column or
            row.

        Raises
        ------
        ValueError
            If ``kind`` is not ``"value"`` or ``"quantile"``, if ``lower`` is
            not less than ``upper``, or, for ``"quantile"``, if a limit is
            outside [0, 1].
        """
        if kind not in ("value", "quantile"):
            raise ValueError(f"alim kind must be 'value' or 'quantile', not {kind!r}")
        assert isinstance(lower, Number) or lower is None
        assert isinstance(upper, Number) or upper is None
        if kind == "quantile":
            for name, q in (("lower", lower), ("upper", upper)):
                if q is not None and not 0 <= q <= 1:
                    raise ValueError(
                        f"quantile alim {name}={q} must be between 0 and 1"
                    )
        if lower is not None and upper is not None and not lower < upper:
            raise ValueError(
                f"{kind} alim lower={lower} must be less than upper={upper}"
            )
        self._alim = RangeLimits(lower, upper)
        self._alim_kind = kind

    def _apply_alim(self, agg):
        r"""Set to NaN the entries of ``agg`` outside ``alim``, bounds inclusive.

        Parameters
        ----------
        agg : pd.Series
            The final aggregated values, one per bin or cell, or for a
            ``Scatter`` the z of each plotted point. With
            ``alim_kind == "quantile"`` the thresholds are quantiles of all
            of its finite entries.

        Returns
        -------
        pd.Series
            ``agg`` with every entry outside ``alim`` replaced by NaN.
        """
        lower, upper = self.alim
        if lower is None and upper is None:
            return agg

        if self.alim_kind == "quantile":
            values = agg.to_numpy(dtype=float)
            values = values[np.isfinite(values)]
            if values.size == 0:
                return agg
            if lower is not None:
                lower = np.nanquantile(values, lower)
            if upper is not None:
                upper = np.nanquantile(values, upper)

        keep = pd.Series(True, index=agg.index)
        if lower is not None:
            keep = keep & (agg >= lower)
        if upper is not None:
            keep = keep & (agg <= upper)

        return agg.where(keep)

    def _limit_values(self, agg):
        r"""Apply ``alim`` to the aggregated values; see ``BinnedPlot.agg``."""
        return self._apply_alim(agg)

    def _set_data(self, x, y, z=None, clip=None, mask=None, within=None):
        r"""Store x, y and z as the plot's source, keeping rows without NaN or inf.

        Called only by the constructor.

        Parameters
        ----------
        x, y : pd.Series
            Coordinates of each point.
        z : pd.Series, optional
            Value at each point. If None, every point gets ``z = 1``.
        clip : bool, str, Mapping or None, optional
            Stored as ``self.clip``, a ``ClipAxes``, None as False. A scalar
            applies to every axis in ``_clipped_axes``; a mapping such as
            ``{"y": "u"}`` sets single axes. True clips both tails; ``"l"``
            or ``"u"`` clips only the lower or upper tail (see
            ``Base.clip_data``).
        mask : pd.Series of bool, optional
            Rows to keep, aligned by label to the index of x and y; a row is
            kept where it is True and x, y and z are neither NaN nor +/-inf,
            a logarithmic axis taken after ``log10(abs())``.
        within : BinnedData, optional
            The shared ``BinnedData`` passed as ``nbins``: rows its own mask
            excludes are not kept either.

        Raises
        ------
        TypeError
            If ``mask`` is not a boolean ``pd.Series``.
        KeyError
            If ``clip`` names an axis the plot does not clip.
        ValueError
            If no row is left, or ``mask`` lacks a label or holds NaN; if
            ``clip`` holds a string ``Base.clip_data`` does not accept; or if
            the plot's data is already set.
        """
        self._claim_data()
        log = self.log._asdict() if self._log_data else None
        self._source = _PlotSource(
            {"x": x, "y": y},
            "z",
            z,
            log=log,
            owner=self.__class__.__name__,
            mask=mask,
            within=within,
        )
        self._store_clip(clip)
        self._bin_names = {"x": getattr(x, "name", None), "y": getattr(y, "name", None)}
        self._bin_index = getattr(x, "index", None)

    @staticmethod
    def _default_norm(axnorm):
        r"""The colour normalisation a plot uses when the caller passes no ``norm``.

        Parameters
        ----------
        axnorm : str or None
            The plot's ``axnorm``.

        Returns
        -------
        matplotlib.colors.Normalize or None
            Column- and row-normalised values lie in [0, 1], so ``"c"`` and
            ``"r"`` get ten equal colour bands on [0, 1]. Densities (``"d"``,
            ``"cd"``, ``"rd"``) span decades, so they get a clipped
            :class:`~matplotlib.colors.LogNorm`. Otherwise None, leaving the
            choice to matplotlib.
        """
        if axnorm in ("c", "r"):
            return mpl.colors.BoundaryNorm(np.linspace(0, 1, 11), 256, clip=True)
        if axnorm in ("d", "cd", "rd"):
            return mpl.colors.LogNorm(clip=True)
        return None

    @staticmethod
    def _fit_view(ax, artist, minx, maxx, miny, maxy):
        r"""Fit ``ax``'s view to ``[minx, maxx] x [miny, maxy]``, the extent of ``artist``.

        The sticky edges keep autoscaling from padding past the data, as
        ``ax.pcolormesh`` does for its mesh.
        """
        artist.sticky_edges.x[:] = [minx, maxx]
        artist.sticky_edges.y[:] = [miny, maxy]
        ax.update_datalim(((minx, miny), (maxx, maxy)))
        ax.autoscale_view()

    @staticmethod
    def _prepare_cbar_kwargs(cbar_kwargs, ax=None):
        r"""Return a new colorbar kwargs dict, defaulting the colorbar's axes.

        The caller's mapping is copied, never modified, so one dict can be
        reused for several plots.

        Parameters
        ----------
        cbar_kwargs : Mapping or None
            The caller's colorbar kwargs. None is treated as empty.
        ax : matplotlib.axes.Axes, optional
            If given, and ``cbar_kwargs`` names neither ``ax`` nor ``cax``,
            the colorbar is placed beside this axes.

        Returns
        -------
        dict
            A new dict holding ``cbar_kwargs`` and, if added, ``ax``.

        Raises
        ------
        TypeError
            If ``cbar_kwargs`` is neither None nor a mapping.
        """
        if cbar_kwargs is None:
            cbar_kwargs = {}
        if not isinstance(cbar_kwargs, Mapping):
            raise TypeError(
                "cbar_kwargs must be a mapping or None, "
                f"not {type(cbar_kwargs).__name__}"
            )

        prepared = dict(cbar_kwargs)
        if ax is not None and "cax" not in prepared and "ax" not in prepared:
            prepared["ax"] = ax
        return prepared

    def _make_cbar(self, mappable, **kwargs):
        """Make a colorbar on `ax` using `mappable`.

        Parameters
        ----------
        mappable:
            See `figure.colorbar` kwarg of same name.
        ax: mpl.axis.Axis
            See `figure.colorbar` kwarg of same name.
        norm: mpl.colors.Normalize instance
            The normalization used in the plot. Passed here to determine
            y-ticks.
        kwargs:
            Passed to `fig.colorbar`. If `{self.__class__.__name__}` is
            row or column normalized, `ticks` defaults to
            :py:class:`mpl.ticker.MultipleLocator(0.1)`.
        """
        ax = kwargs.pop("ax", None)
        cax = kwargs.pop("cax", None)
        if ax is not None and cax is not None:
            raise ValueError("Can't pass ax and cax.")

        if ax is not None:
            try:
                fig = ax.figure
            except AttributeError:
                fig = ax[0].figure
        elif cax is not None:
            try:
                fig = cax.figure
            except AttributeError:
                fig = cax[0].figure
        else:
            raise ValueError(
                "You must pass `ax` or `cax`. We don't want to rely on `plt.gca()`."
            )

        label = kwargs.pop("label", self.labels.z)
        cbar = fig.colorbar(mappable, label=label, ax=ax, cax=cax, **kwargs)

        return cbar


class BinnedPlot(Base):
    r"""Base for plots that aggregate a value in the cells of a ``Binning``.

    The plot's ``binning`` places each kept row in one cell. ``agg`` groups
    the aggregated column by cell, applies ``clim`` to the count in each
    cell, drops the cells the binning filters out, normalizes by ``axnorm``
    with the cells' measure, and returns every cell. A ``ColorPlot`` then
    applies ``alim``.
    """

    _axnorm = None
    _clim = RangeLimits(None, None)

    @property
    def binning(self):
        r"""The ``Binning`` that places each kept row in a cell."""
        return self._binning

    @property
    def clim(self):
        r"""``RangeLimits`` of the minimum and maximum counts per cell; see ``set_clim``."""
        return self._clim

    def set_clim(self, lower=None, upper=None):
        r"""Set the minimum (lower) and maximum (upper) allowed counts per cell.

        A cell with fewer than ``lower`` or more than ``upper`` rows is NaN in
        ``agg``. Bounds are inclusive; None leaves that side open.
        """
        assert isinstance(lower, Number) or lower is None
        assert isinstance(upper, Number) or upper is None
        self._clim = RangeLimits(lower, upper)

    @property
    def axnorm(self):
        r"""Data normalization in plot.

        Not `mpl.colors.Normalize` instance. That is passed as a `kwarg` to
        `make_plot`.
        """
        return self._axnorm

    def set_axnorm(self, new):
        r"""Set how ``agg`` normalizes the aggregated values.

        The keys the plot's cells support are ``binning.allowed_axnorm``; see
        ``binning.normalize``. A ``Count`` label on the aggregated axis is
        rebuilt to name the normalization.

        Raises
        ------
        TypeError
            If ``new`` is neither a string nor None.
        ValueError
            If ``new`` is not a key the cells support.
        """
        self._axnorm = self._validate_axnorm(new, self.binning.allowed_axnorm)
        self._count_with_axnorm(getattr(self.labels, self.agg_axes))

    def _count_with_axnorm(self, label):
        r"""Rebuild ``label`` with ``axnorm`` if it is a ``Count``; return it."""
        if isinstance(label, labels.special.Count):
            label.set_axnorm(self.axnorm)
            label.build_label()
        return label

    def set_labels(self, **kwargs):
        r"""Set axis labels; a ``Count`` label of the aggregated axis follows ``axnorm``.

        See ``Base.set_labels``.
        """
        axis = self.agg_axes
        kwargs[axis] = self._count_with_axnorm(
            kwargs.get(axis, getattr(self.labels, axis))
        )
        super().set_labels(**kwargs)

    @staticmethod
    def _validate_axnorm(new, allowed):
        r"""Check an ``axnorm`` key and return it in its normalized form.

        Parameters
        ----------
        new : str or None
            The requested key. Matching is case-insensitive and exact.
        allowed : tuple of str
            The lowercase keys the plot's cells support.

        Returns
        -------
        str or None
            ``None`` unchanged, otherwise the lowercase key.

        Raises
        ------
        TypeError
            If `new` is neither a string nor None.
        ValueError
            If `new` is not one of `allowed`.
        """
        if new is None:
            return None
        if not isinstance(new, str):
            raise TypeError(
                f"axnorm must be a string or None; got {type(new).__name__}"
            )
        key = new.lower()
        if key not in allowed:
            raise ValueError(
                f"Unrecognized axnorm '{new}'; expected one of: {', '.join(allowed)}"
            )
        return key

    @property
    def agg_axes(self):
        r"""The axis to aggregate into, e.g. the z variable in an (x, y, z) heatmap."""
        return self._source.columns[-1]

    def _grouped_by_cell(self):
        r"""The aggregated column on the rows in a cell, grouped by cell code."""
        codes = self.binning.codes()
        # By position: the groups are keyed by `codes`, never by row label.
        target = self._source.take(self.agg_axes, labels=False)
        inside = codes >= 0
        if not inside.all():
            target = pd.Series(target.array[inside], name=target.name, copy=False)
            codes = codes[inside]
        return target.groupby(codes)

    def _limit_values(self, agg):
        r"""Limits on the final aggregated values: none here; ``ColorPlot`` has ``alim``."""
        return agg

    def agg(self, fcn=None, **kwargs):
        r"""Aggregate the values in each cell.

        ``fcn`` allows you to specify a specific function for aggregation.
        Otherwise, automatically choose "count" or "mean" based on the
        uniqueness of the aggregated values. ``kwargs`` are passed to the
        aggregation.

        A cell whose count is outside ``clim`` is NaN, and so is a cell the
        binning's ``postfilter`` drops. The occupied cells are then
        normalized by ``axnorm`` (``binning.normalize``). Every cell is in
        the result, indexed by ``binning.cells``; a cell no row falls in is
        NaN. A ``ColorPlot`` then sets the cells outside ``alim`` to NaN.
        """
        tko = self.agg_axes

        lbls = {k: str(v).replace("\n", " ") for k, v in self.labels._asdict().items()}
        self.logger.info(
            f"Starting {self.__class__.__name__!s} aggregation of ({tko})\n%s",
            "\n".join([f"""{k!s}: {v!s}""" for k, v in lbls.items()]),
        )

        gb = self._grouped_by_cell()

        if fcn is None:
            fcn = "count" if self._source.counts else "mean"

        agg = gb.agg(fcn, **kwargs)

        c0, c1 = self.clim
        if c0 is not None or c1 is not None:
            cnt = gb.agg("count")
            tk = pd.Series(True, index=agg.index)
            if c0 is not None:
                tk = tk & (cnt >= c0)
            if c1 is not None:
                tk = tk & (cnt <= c1)

            agg = agg.where(tk)

        binning = self.binning
        agg = binning.postfilter(agg)

        # Normalize the occupied cells only, so sums over cells never see the
        # NaN of an empty one; then fill in every cell.
        cells = binning.cells
        positions = agg.index.to_numpy()
        agg = agg.set_axis(cells[positions])
        agg = binning.normalize(agg, self.axnorm, positions)
        return self._limit_values(agg.reindex(cells))

    def _kept_index(self):
        r"""Labels of the rows the plot keeps, the index of ``data``."""
        rows = self._source.rows
        index = self._source.index
        return index if rows is None else index[rows]

    def _rows_in_cells(self, positions):
        r"""Boolean ``pd.Series`` marking each kept row whose cell is in ``positions``.

        Parameters
        ----------
        positions : np.ndarray of int
            Cell codes, positions in ``binning.cells``.

        Returns
        -------
        pd.Series
            On the index of ``data``.
        """
        codes = self.binning.codes()
        keep = np.isin(codes, positions) & (codes >= 0)
        return pd.Series(keep, index=self._kept_index())

    def get_plotted_data_boolean_series(self):
        """Return a boolean ``pd.Series`` identifying each plotted measurement.

        A measurement is plotted when its cell (e.g. its joint (x, y) bin in
        2-D) survives aggregation. The series shares the same index as the
        stored data. To align with a different index you may need to adjust
        the returned series.
        """
        agg = self.agg()
        tk = self._rows_in_cells(np.flatnonzero(agg.notna().to_numpy()))

        self.logger.info(
            f"Taking {tk.sum()!s} ({100 * tk.mean():.1f}%) {self.__class__.__name__} spectra"
        )

        return tk

    def get_subset_above_threshold(self, threshold, fcn="count"):
        r"""Get the subset of data above a given threshold using `fcn` to.

        aggregate. If `axnorm` set, this is used. A row is kept when its cell
        (e.g. its joint (x, y) bin in 2-D) meets `threshold`.

        Returns
        -------
        subset : pd.DataFrame
            The kept rows, one column per column of ``data``, holding the
            values the caller passed: never logged, sign included, whatever
            ``log`` says.
        tk : pd.Series of bool
            True for each kept row, on the index of ``data``.
        """
        agg = self.agg(fcn=fcn)
        tk = self._rows_in_cells(np.flatnonzero((agg >= threshold).to_numpy()))

        # The source's values on the kept rows: no 10** round trip, so only
        # what was stored logged differs from `data`, and it is not inverted.
        source = self._source
        subset = pd.DataFrame(
            {k: source.take(k) for k in source.columns},
            index=self._kept_index(),
            copy=False,
        )
        subset = subset.loc[tk.to_numpy(dtype=bool)]

        return subset, tk


class _OnFixedGrid:
    r"""The bins of a plot whose ``binning`` is a ``FixedGrid``, and its rows in them.

    Mixed into ``Hist1D`` and ``Hist2D``; ``_grid_axes`` names the binned axes.
    """

    def _set_grid_data(self, inputs, nbins, log, clip, precision, mask):
        r"""Store the data and bin it on a ``FixedGrid``.

        Parameters
        ----------
        inputs : dict
            The ``_set_data`` arguments in order, keyed by column.
        nbins, precision
            The grid's bins; see ``FixedGrid``.
        log : dict
            The caller's log setting per binned axis, None to inherit.
        clip, mask
            The caller's ``clip`` and ``mask``.
        """
        names = {k: getattr(inputs[k], "name", None) for k in self._grid_axes}
        log, clip = FixedGrid.resolve(
            nbins, names, log, self._clip_by_axis(clip), precision
        )
        self.set_log(**log)
        within = nbins if isinstance(nbins, BinnedData) else None
        self._set_data(*inputs.values(), clip, mask=mask, within=within)
        self._binning = FixedGrid(
            self._source,
            nbins,
            axes=self._grid_axes,
            precision=precision,
            names=self._bin_names,
            index=self._bin_index,
            log=self.log,
            clip=self.clip,
            logger=self.logger,
        )

    @property
    def edges(self):
        r"""Bin edges per axis, a float ``pd.Index`` each.

        The edges the rows were binned by, as the plot's ``BinnedData`` stores
        them.
        """
        return self.binning.edges

    @property
    def intervals(self):
        r"""Bins per axis, a ``pd.IntervalIndex`` each."""
        return self.binning.intervals

    @property
    def categoricals(self):
        r"""Alias of ``intervals``: the bins per axis, a ``pd.IntervalIndex`` each."""
        return self.intervals

    @property
    def cut(self):
        r"""Bin of each row the plot keeps: a DataFrame of categoricals.

        One column per binned axis, indexed by the kept rows' labels. Built on
        each access from the bin codes.
        """
        return self.binning.cut()

    @property
    def joint(self):
        r"""Combines the categorical and continuous data for `Groupby`."""
        cut = self.cut
        target = self._source.take(self.agg_axes)

        mi = pd.MultiIndex.from_frame(cut)
        return target.set_axis(mi)

    @property
    def grouped(self):
        r"""`joint.groupby` with appropriate axes passes."""
        return self.joint.groupby(list(self._grid_axes), observed=True)
