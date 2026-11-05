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
import matplotlib.pyplot as plt

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


def _within(values, lower, upper, bins):
    r"""Which ``values`` lie between ``lower`` and ``upper``, closed as ``bins`` are.

    Parameters
    ----------
    values : pd.Series or np.ndarray
        Values on the binned scale, ``log10(abs())`` on a log axis.
    lower, upper : scalar
        The bounds.
    bins : pd.IntervalIndex
        The axis's bins. Right-closed bins compare ``lower < v <= upper``;
        left-closed bins compare ``lower <= v < upper`` and, as the last
        left-closed bin also holds its right edge (``np.histogram``), keep
        ``v == upper`` when ``upper`` is that edge.

    Returns
    -------
    pd.Series or np.ndarray of bool
    """
    if bins.closed == "left":
        inside = (lower <= values) & (values < upper)
        if upper == bins.right[-1]:
            inside |= values == upper
        return inside
    return (lower < values) & (values <= upper)


#: ``axnorm`` keys that give each cell a share of a total.
_SHARE_AXNORMS = ("d", "cd", "rd", "w", "wc", "wr")


def _aggregation_kind(fcn):
    r"""``"count"``, ``"sum"`` or ``"value"``: how ``axnorm`` treats ``fcn``.

    Only ``"count"`` is a count and only ``"sum"`` or :func:`numpy.sum` a
    sum; every other aggregation, a custom additive callable included, is a
    per-cell value.
    """
    if isinstance(fcn, str):
        return {"count": "count", "sum": "sum"}.get(fcn, "value")
    if fcn is np.sum:
        return "sum"
    return "value"


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

    def __repr__(self):
        r"""A summary of what the plot holds, one ``key: value`` per line.

        The class, then one line per axis (x, y, and z when the plot has
        one): its label, its bins (``_axis_extent``) and the range of the
        data on it, then the number of rows the plot keeps, the log flags,
        the fields ``_repr_fields`` adds (binning, ``axnorm``, ``clim``,
        ``alim``), and ``path``. ``print`` shows the same text. A plot whose
        constructor has not run shows its class and "(not built)".
        """
        if "_labels" not in self.__dict__:
            return f"{self.__class__.__name__} (not built)"
        labels = self._flat_labels()
        axes = ["x", "y", "z"] if self._has_z_label() else ["x", "y"]
        fields = {k: self._axis_line(k, labels[k]) for k in axes}
        source = self.__dict__.get("_source")
        fields["observations"] = "none" if source is None else source.n_kept
        fields["log"] = ", ".join(f"{k}={v}" for k, v in self.log._asdict().items())
        fields.update(self._repr_fields())
        fields["path"] = self.path
        lines = [f"  {k}: {v}" for k, v in fields.items()]
        return "\n".join([self.__class__.__name__, *lines])

    def _repr_fields(self):
        r"""Fields a subclass adds to ``repr`` before ``path``, as a dict; none here."""
        return {}

    def _axis_extent(self, axis):
        r"""``(prefix, lower, upper)`` of ``axis``'s bins on the binned scale, or None.

        None here: the plot bins nothing. ``BinnedPlot`` asks its binning.
        """
        return None

    def _axis_line(self, axis, label):
        r"""One axis's ``repr`` line: label, bin range and data range.

        Ranges are in data units: on a log axis the bins' edges and the binned
        ``log10(abs())`` values are shown as 10 to that power, so the data
        range is that of ``abs()``. Numbers have four significant figures.
        The aggregated column shows no data range when the caller gave none
        (a count).
        """
        parts = [label]
        source = self.__dict__.get("_source")
        logged = source is not None and source.is_logged(axis)

        def fmt(v):
            return f"{10.0**v if logged else v:.4g}"

        extent = self._axis_extent(axis)
        if extent is not None:
            prefix, lower, upper = extent
            parts.append(f"{prefix} [{fmt(lower)}, {fmt(upper)}]")
        if source is not None and axis in source.columns:
            coords = source.columns[:-1]
            if axis in coords or source.has_value:
                values = source.logged(axis, labels=False).to_numpy(dtype=float)
                parts.append(
                    f"data [{fmt(np.nanmin(values))}, {fmt(np.nanmax(values))}]"
                )
        return "  ".join(parts)

    @staticmethod
    def _format_limits(limits):
        r"""``RangeLimits`` as ``"lower=..., upper=..."``, or None when both are unset."""
        if limits.lower is None and limits.upper is None:
            return None
        return f"lower={limits.lower}, upper={limits.upper}"

    def _flat_labels(self):
        r"""Each axis's label as one line of text, keyed ``x``, ``y`` and ``z``."""
        return {k: str(v).replace("\n", " ") for k, v in self.labels._asdict().items()}

    def _has_z_label(self):
        r"""True when ``labels.z`` is set: neither None nor the string ``"None"``."""
        z = self.labels.z
        return not (z is None or (isinstance(z, str) and z == "None"))

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
        if self._has_z_label():
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


class _AggregateLimits(Base):
    r"""``alim``: limits on a plot's aggregated or coloured values.

    The one home of ``alim`` for every plot that has it. A ``BinnedPlot``
    applies it to each cell's aggregated value (``_limit_values``); a
    ``Scatter`` to the z of each point.
    """

    _alim = RangeLimits(None, None)
    _alim_kind = "value"

    @property
    def alim(self):
        r"""``RangeLimits`` on the aggregated value; see ``set_alim``."""
        return self._alim

    def _repr_fields(self):
        r"""Add ``alim`` and its kind to ``repr`` when set."""
        fields = super()._repr_fields()
        alim = self._format_limits(self.alim)
        if alim is not None:
            fields["alim"] = f"{alim} ({self.alim_kind})"
        return fields

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


class ColorPlot(_AggregateLimits):
    r"""Base for plots of x and y coloured by a z value, with a colorbar.

    Holds the data intake of (x, y, z) and the z label the colorbar shows;
    ``alim``, the limits on the coloured values, comes from
    ``_AggregateLimits``.
    """

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

    def _apply_alpha_fcn(self, artist, alpha_fcn, face_values):
        r"""Make ``artist``'s faces more transparent the larger ``alpha_fcn`` of z is.

        The one home of ``make_plot``'s ``alpha_fcn`` for every colour plot.
        The values are scaled to [0, 1] and inverted, so the smallest (e.g.
        the smallest standard deviation) is the most opaque, then raised to
        the power 0.25. A face with no value is transparent.

        Parameters
        ----------
        artist : matplotlib.collections.Collection
            The drawn faces.
        alpha_fcn : str, callable or None
            The aggregation of z per face. None leaves the faces as drawn.
        face_values : callable
            Called with ``alpha_fcn``; returns its value for each face of
            ``artist``, in the order of the faces.

        Notes
        -----
        A count plot has no z to aggregate, so there ``alpha_fcn`` is
        ignored, with a warning, and the faces stay as drawn.
        """
        if alpha_fcn is None:
            return
        if self._source.counts:
            self.logger.warning("Ignoring `alpha_fcn` because plotting counts")
            return

        self.logger.warning(
            "Make sure you verify alpha actually set. I don't yet trust this."
        )
        values = np.ma.masked_invalid(np.asarray(face_values(alpha_fcn), dtype=float))
        # Feature scale then invert so smallest STD
        # is most opaque.
        alpha = 1 - mpl.colors.Normalize()(values)
        self.logger.warning("Scaling alpha filter as alpha**0.25")
        alpha = alpha**0.25

        # Set masked values to zero. Otherwise, masked
        # values are rendered as black.
        alpha = alpha.filled(0)
        # Must draw to initialize `facecolor`s
        plt.draw()
        colors = artist.get_facecolors()
        colors[:, 3] = alpha
        artist.set_facecolor(colors)

    #: Default colormap for values of both signs.
    _diverging_cmap = "RdBu_r"

    def _color_scale(self, kwargs, values):
        r"""Pop ``norm`` and ``cmap`` from ``kwargs``, defaulting them by ``values``.

        The one place every colour plot chooses its colour scale. A ``norm``
        or ``cmap`` in ``kwargs`` is used as given, None included. Otherwise,
        when the finite ``values`` hold both signs, the default is a
        :class:`~matplotlib.colors.CenteredNorm` about 0 and the diverging
        colormap ``_diverging_cmap``; values of one sign get
        ``_default_norm`` and matplotlib's colormap.

        Parameters
        ----------
        kwargs : dict
            The caller's keywords; ``norm`` and ``cmap`` are removed.
        values : array-like
            The values to colour, NaN or masked where none.

        Returns
        -------
        norm, cmap
        """
        v = np.ma.filled(np.ma.asarray(values, dtype=float), np.nan)
        v = v[np.isfinite(v)]
        signed = bool((v < 0).any() and (v > 0).any())
        axnorm = getattr(self, "axnorm", None)
        if "norm" in kwargs:
            norm = kwargs.pop("norm")
        else:
            norm = self._default_norm(axnorm, signed)
        if "cmap" in kwargs:
            cmap = kwargs.pop("cmap")
        else:
            cmap = self._diverging_cmap if signed else None
        return norm, cmap

    @staticmethod
    def _default_norm(axnorm, signed=False):
        r"""The colour normalisation a plot uses when the caller passes no ``norm``.

        Parameters
        ----------
        axnorm : str or None
            The plot's ``axnorm``.
        signed : bool, default False
            True when the values hold both signs.

        Returns
        -------
        matplotlib.colors.Normalize or None
            Values of both signs get a
            :class:`~matplotlib.colors.CenteredNorm` about 0, whatever the
            ``axnorm``. Otherwise column- and row-normalised values lie in
            [0, 1], so ``"c"`` and ``"r"`` get ten equal colour bands on
            [0, 1]; densities (``"d"``, ``"cd"``, ``"rd"``) span decades, so
            they get a clipped :class:`~matplotlib.colors.LogNorm`; anything
            else gets None, leaving the choice to matplotlib.
        """
        if signed:
            return mpl.colors.CenteredNorm(vcenter=0.0)
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


class BinnedPlot(_AggregateLimits):
    r"""Base for plots that aggregate a value in the cells of a ``Binning``.

    The plot's ``binning`` places each kept row in one cell. ``agg`` groups
    the aggregated column by cell, applies ``clim`` to the count in each
    cell, drops the cells the binning filters out, normalizes by ``axnorm``
    with the cells' measure, applies ``alim`` to the result, and returns
    every cell.
    """

    _axnorm = None
    _clim = RangeLimits(None, None)

    @property
    def binning(self):
        r"""The ``Binning`` that places each kept row in a cell."""
        return self._binning

    def _axis_extent(self, axis):
        r"""The binning's ``axis_extent``; None before the binning is built."""
        binning = self.__dict__.get("_binning")
        return None if binning is None else binning.axis_extent(axis)

    def _repr_fields(self):
        r"""Add the binning, ``axnorm`` and, when set, ``clim`` to ``repr``."""
        fields = super()._repr_fields()
        binning = self.__dict__.get("_binning")
        if binning is not None:
            fields["bins"] = binning.describe()
        fields["axnorm"] = self.axnorm
        clim = self._format_limits(self.clim)
        if clim is not None:
            fields["clim"] = clim
        if "alim" in fields:
            # Show alim after clim, the order they apply in.
            fields["alim"] = fields.pop("alim")
        return fields

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
        r"""Rebuild ``label`` with ``axnorm`` and the binned axes if it is a ``Count``.

        The binned axes' labels and log scales give a density its units; see
        ``labels.base.density_units``. Returns ``label``.
        """
        if isinstance(label, labels.special.Count):
            label.set_axnorm(self.axnorm)
            label.set_binned_axes(
                {
                    axis: (getattr(self.labels, axis), getattr(self.log, axis))
                    for axis in self._source.columns
                    if axis != self.agg_axes
                }
            )
            label.build_label()
        return label

    def set_labels(self, **kwargs):
        r"""Set axis labels; a ``Count`` label of the aggregated axis follows ``axnorm``.

        The ``Count`` is updated after the labels are set, so a density's
        units follow new labels of the binned axes. See ``Base.set_labels``.
        """
        super().set_labels(**kwargs)
        self._count_with_axnorm(getattr(self.labels, self.agg_axes))

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

    def _cell_codes(self):
        r"""``binning.codes()``, computed once per binning and data, read-only.

        The binning and the data are each set once, by the constructor, but
        the cache is keyed on both objects, so replacing either recomputes.
        """
        binning = self.binning
        source = self._source
        cached = self.__dict__.get("_codes_cache")
        if cached is None or cached[0] is not binning or cached[1] is not source:
            codes = np.asarray(binning.codes())
            codes.setflags(write=False)
            cached = (binning, source, codes)
            self._codes_cache = cached
        return cached[2]

    def _grouped_by_cell(self):
        r"""The aggregated column on the rows in a cell, grouped by cell code."""
        codes = self._cell_codes()
        # By position: the groups are keyed by `codes`, never by row label.
        target = self._source.take(self.agg_axes, labels=False)
        inside = codes >= 0
        if not inside.all():
            target = pd.Series(target.array[inside], name=target.name, copy=False)
            codes = codes[inside]
        return target.groupby(codes)

    def _limit_values(self, agg):
        r"""Apply ``alim`` to the final aggregated values; see ``agg``."""
        return self._apply_alim(agg)

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
        NaN. The cells outside ``alim`` are then set to NaN.

        How ``axnorm`` treats the result depends on the aggregation, which
        is classified as a count (``"count"``), a sum (``"sum"`` or
        :func:`numpy.sum`), or a value (anything else: ``"mean"``,
        ``"median"``, any callable). A custom callable is a value even when
        it adds, so pass ``"sum"`` for a sum. A share of a sum (``axnorm``
        ``"d"``, ``"cd"``, ``"rd"``, ``"w"``, ``"wc"`` or ``"wr"``) needs
        every aggregated value in a cell to be >= 0.

        Raises
        ------
        ValueError
            For a share of a sum when a row in a cell has a negative value.
        """
        tko = self.agg_axes

        lbls = self._flat_labels()
        self.logger.info(
            f"Starting {self.__class__.__name__!s} aggregation of ({tko})\n%s",
            "\n".join([f"""{k!s}: {v!s}""" for k, v in lbls.items()]),
        )

        if fcn is None:
            fcn = "count" if self._source.counts else "mean"
        kind = _aggregation_kind(fcn)

        # Rows per cell straight from the cell codes, kept only for occupied
        # cells, as a groupby count would, so empty cells stay NaN after the
        # reindex below. The aggregated column has no NaN on kept rows, so
        # this equals its groupby count. It serves clim and axnorm.
        codes = self._cell_codes()
        n = np.bincount(codes[codes >= 0], minlength=len(self.binning.cells))
        occupied = np.flatnonzero(n)
        cnt = pd.Series(
            n[occupied].astype(np.int64),
            index=pd.Index(occupied, dtype=np.int64),
            name=self.agg_axes,
        )
        if kind == "count" and isinstance(fcn, str) and not kwargs:
            # Count fast path: the counts are the aggregate; no groupby.
            agg = cnt
        else:
            agg = self._grouped_by_cell().agg(fcn, **kwargs)

        if kind == "sum" and self.axnorm in _SHARE_AXNORMS:
            values = self._source.take(self.agg_axes, labels=False).to_numpy()
            if (values[codes >= 0] < 0).any():
                raise ValueError(
                    f"axnorm={self.axnorm!r} on a sum gives each cell's share of "
                    f"the total {self.agg_axes}, which needs {self.agg_axes} >= 0; "
                    "some values in the cells are negative. Use a value "
                    "aggregation such as 'mean', or axnorm 't', 'c' or 'r'."
                )

        c0, c1 = self.clim
        if c0 is not None or c1 is not None:
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
        index = cells[positions]
        agg = agg.set_axis(index)
        counts = cnt.set_axis(index)
        agg = binning.normalize(agg, self.axnorm, positions, counts=counts, kind=kind)
        return self._limit_values(agg.reindex(cells))

    def _kept_index(self):
        r"""Labels of the rows the plot keeps, the index of ``data``."""
        rows = self._source.rows
        index = self._source.index
        return index if rows is None else index[rows]

    def _plotted_rows(self, fcn=None):
        r"""Boolean array over the kept rows: True where the row's cell is shown.

        A cell is shown where ``agg(fcn)`` is not NaN. Looked up by cell code,
        with code -1 (no cell) mapped to the appended False.
        """
        shown = self.agg(fcn=fcn).notna().to_numpy()
        return np.append(shown, False)[self._cell_codes()]

    def _kept_source_frame(self):
        r"""The caller's values on the kept rows, one column per ``data`` column.

        No ``10**`` round trip: a logged axis holds the values as passed,
        sign included.
        """
        source = self._source
        return pd.DataFrame(
            {k: source.take(k) for k in source.columns},
            index=self._kept_index(),
            copy=False,
        )

    def get_plotted_data(self, fcn=None):
        r"""The rows in the cells the figure shows.

        A cell is shown when ``agg(fcn)`` is not NaN there: after ``clim``,
        ``axnorm``, any cell filter (a spiral mesh's ``cell_filter``) and
        ``alim``. ``alim`` acts on the aggregated value, so
        pass the ``fcn`` you gave ``make_plot``; the default is the same as
        ``make_plot``'s.

        Parameters
        ----------
        fcn : str or callable, optional
            The aggregation, as ``agg`` takes it.

        Returns
        -------
        pd.DataFrame
            One column per column of ``data`` (``x``, ``y`` and, on a 2-D
            plot, ``z``), on the caller's index labels, in the caller's row
            order. The values are the caller's: never logged, sign included,
            whatever ``log`` says.
        """
        return self._kept_source_frame().loc[self._plotted_rows(fcn)]


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

    def take_data_in_yrange_across_x(self, ranges_by_x, get_x_bounds, get_y_bounds):
        r"""Take the rows within a y-range in each of several x-ranges.

        Parameters
        ----------
        ranges_by_x : pd.DataFrame
            Indexed by x-bins of this plot (``intervals["x"]``); each row holds
            what ``get_y_bounds`` reads for that bin.
        get_x_bounds : callable
            ``get_x_bounds(key, expected_logx=bool)`` returns ``left, right``
            for one index entry of `ranges_by_x`. ``expected_logx`` is
            ``log.x``, so the bounds can be given as :math:`\log_{10} x` or
            :math:`x` to match ``data``.
        get_y_bounds : callable
            ``get_y_bounds(row, expected_logy=bool)`` returns ``bottom, top``
            for one row of `ranges_by_x`. ``expected_logy`` is True only on a
            ``Hist2D`` with a log y; a ``Hist1D`` stores y in linear units and
            passes False.

        Returns
        -------
        taken : np.ndarray
            Sorted index labels of the rows with x between `left` and `right`
            and y between `bottom` and `top`, once per range that holds them.
            x compares on the side its bins close: ``left < x <= right`` for
            right-closed bins (explicit edges), ``left <= x < right`` for
            left-closed bins (an integer `nbins`), whose last bin also holds
            its right edge, so ``x == right`` is kept when `right` is that
            edge. A binned y (``Hist2D``) compares likewise with its y-bins;
            a ``Hist1D``'s y is not binned and compares ``bottom < y <= top``.

        Raises
        ------
        ValueError
            If a range has ``left >= right`` or ``bottom >= top`` (the first
            such range in the order of `ranges_by_x` is named), or if an entry
            of `ranges_by_x` names an x-bin the plot does not have. x-bins
            that `ranges_by_x` omits only log a warning.

        Notes
        -----
        When the x-ranges do not overlap, each row's range is found with one
        :func:`numpy.searchsorted` over the sorted left bounds; overlapping
        ranges are taken one range at a time, so a row in two ranges is
        taken twice.
        """
        intervals = self.intervals
        xbins = intervals["x"]
        ybins = intervals.get("y")
        if ranges_by_x.index.symmetric_difference(xbins).size:
            drop = ranges_by_x.index.symmetric_difference(xbins)
            if not drop.isin(xbins).all():
                raise ValueError(
                    "Need a way to drop values in selector that aren't available."
                )
            self.logger.warning(
                f"Dropping {drop.size} intervals from available for selecting."
            )

        logx = bool(self.log.x)
        logy = bool(ybins is not None and self.log.y)
        n = ranges_by_x.shape[0]
        left, right = np.empty(n), np.empty(n)
        bottom, top = np.empty(n), np.empty(n)
        for i, (x, at_x) in enumerate(ranges_by_x.iterrows()):
            lo, hi = get_x_bounds(x, expected_logx=logx)
            b, t = get_y_bounds(at_x, expected_logy=logy)
            if not lo < hi:
                raise ValueError(f"Need left < right for x-bin {x}, got ({lo}, {hi}).")
            if not b < t:
                raise ValueError(f"Need bottom < top for x-bin {x}, got ({b}, {t}).")
            left[i], right[i], bottom[i], top[i] = lo, hi, b, t

        data = self.data
        xv = data.loc[:, "x"].to_numpy()
        yv = data.loc[:, "y"].to_numpy()
        labels = data.index.to_numpy()

        def in_y(values, b, t):
            if ybins is None:
                return (b < values) & (values <= t)
            return _within(values, b, t, ybins)

        order = np.argsort(left, kind="stable")
        left, right = left[order], right[order]
        bottom, top = bottom[order], top[order]
        last = xbins.right[-1]
        overlap = np.any(right[:-1] > left[1:])
        if xbins.closed == "left":
            # A range ending on the last edge also holds that edge, which the
            # next range may start on.
            overlap |= np.any((right[:-1] == last) & (left[1:] == last))
        if overlap:
            taken = [
                labels[_within(xv, lo, hi, xbins) & in_y(yv, b, t)]
                for lo, hi, b, t in zip(left, right, bottom, top)
            ]
            return np.sort(np.concatenate(taken)) if taken else labels[:0]

        # Disjoint ranges: each x is in at most one, found by its left bound.
        # Left-closed: the range with the largest left <= x; right-closed: the
        # largest left < x.
        side = "right" if xbins.closed == "left" else "left"
        j = np.searchsorted(left, xv, side) - 1
        inside = j >= 0
        jj = np.where(inside, j, 0)
        if n == 0:
            return labels[:0]
        r = right[jj]
        if xbins.closed == "left":
            inside &= (xv < r) | ((xv == r) & (r == last))
        else:
            inside &= xv <= r
        b, t = bottom[jj], top[jj]
        if ybins is None:
            inside &= (b < yv) & (yv <= t)
        elif ybins.closed == "left":
            inside &= (b <= yv) & ((yv < t) | ((yv == t) & (t == ybins.right[-1])))
        else:
            inside &= (b < yv) & (yv <= t)
        return np.sort(labels[inside])
