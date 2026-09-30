#!/usr/bin/env python
r"""Base classes for plotting utilities.

This module defines abstract helpers that manage axis labels, log scaling, and file
system paths for saving figures.  Concrete plot classes derive from these mixins to
implement specific visualizations.
"""

import logging
import numpy as np
import pandas as pd

from numbers import Number
from pathlib import Path
from collections import namedtuple
from collections.abc import Mapping
from abc import ABC, abstractmethod

LogAxes = namedtuple("LogAxes", "x,y", defaults=(False,))
AxesLabels = namedtuple("AxesLabels", "x,y,z", defaults=(None,))
RangeLimits = namedtuple("RangeLimits", "lower,upper", defaults=(None,))


class Base(ABC):
    r"""Abstract base for SolarWindPy plots.

    Holds the axis labels, the log-scale flags, and the save path that every
    concrete plot shares. Subclasses implement ``set_data``, ``set_path`` and
    ``make_plot``.
    """

    @abstractmethod
    def __init__(self):
        r"""Set default labels ``x`` and ``y``, linear axes, and an automatic path."""
        self._init_logger()
        self._labels = AxesLabels(x="x", y="y")
        self._log = LogAxes(x=False)
        self.set_path("auto")

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
        r"""Data stored by ``set_data``."""
        return self._data

    @property
    def clip(self):
        r"""Clipping option stored by ``set_data``."""
        return self._clip

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
        r"""Path for saving figure."""
        return self._path

    def set_log(self, x=None, y=None):
        r"""Set which axes use a logarithmic scale.

        Parameters
        ----------
        x, y : bool, optional
            If True, the axis is logarithmic. None keeps the current value.
        """
        if x is None:
            x = self.log.x
        if y is None:
            y = self.log.y

        log = LogAxes(bool(x), bool(y))
        self._log = log

    def set_labels(self, **kwargs):
        r"""Set or update the x, y, or z labels.

        Any label not passed keeps its current value in ``self.labels``.

        Parameters
        ----------
        x, y, z : str or solarwindpy.plotting.labels.base.TeXlabel, optional
            New axis labels.
        auto_update_path : bool, optional
            If True (default), rebuild the save path from the new labels.

        Raises
        ------
        KeyError
            If any other keyword is passed.
        """
        auto_update_path = kwargs.pop("auto_update_path", True)

        x = kwargs.pop("x", self.labels.x)
        y = kwargs.pop("y", self.labels.y)
        z = kwargs.pop("z", self.labels.z)

        if len(kwargs.keys()):
            extra = "\n".join(["{}: {}".format(k, v) for k, v in kwargs.items()])
            raise KeyError("Unexpected kwarg\n{}".format(extra))

        self._labels = AxesLabels(x, y, z)

        if auto_update_path:
            self.set_path("auto")

    @abstractmethod
    def set_path(self, new, add_scale=False):
        r"""Build the plot save path.

        Parameters
        ----------
        new : str or Path
            If ``"auto"``, build the path from ``self.labels``. Otherwise,
            use ``Path(new)``.
        add_scale : bool
            If True, add information about the axis scales to the end of the path.
        """
        # TODO: move "auto" methods here to iterate through `AxesLabels` named tuple
        #       and pull the strings for creating the path. Also check for each
        #       label's scale and add that information.

        if new == "auto":
            try:
                x = self.labels.x.path
            except AttributeError:
                x = self.labels.x
                if not (isinstance(x, str) and x != "None"):
                    x = "x"
                elif isinstance(x, str):
                    x = x.replace(" ", "-")

            try:
                y = self.labels.y.path
            except AttributeError:
                y = self.labels.y
                if not (isinstance(y, str) and y != "None"):
                    y = "y"
                elif isinstance(y, str):
                    y = y.replace(" ", "-")

            try:
                z = self.labels.z.path
            except AttributeError:
                z = self.labels.z
                if not (isinstance(z, str) and z != "None"):
                    z = "z"
                elif isinstance(z, str):
                    z = z.replace(" ", "-")

            path = Path(self.__class__.__name__)

        elif new is None:
            path = Path("")
            x = y = z = None

        else:
            path = Path(new)
            x = y = z = None

        scale_info = None
        if add_scale:
            xscale = "logX" if self.log.x else "linX"
            yscale = "logY" if self.log.y else "linY"
            scale_info = [xscale, yscale]

        return path, x, y, z, scale_info

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
    def set_data(self):
        r"""Store the data to plot. Implemented by each subclass."""
        pass

    @abstractmethod
    def make_plot(self):
        r"""Draw the plot. Implemented by each subclass."""
        pass


class DataLimFormatter(ABC):
    r"""Mixin that limits the axes to the range of the x and y data."""

    def _format_axis(self, ax, collection, **kwargs):
        super()._format_axis(ax, **kwargs)

        x = self.data.loc[:, "x"]
        minx, maxx = x.min(), x.max()

        y = self.data.loc[:, "y"]
        miny, maxy = y.min(), y.max()

        # `pulled from the end of `ax.pcolormesh`.
        collection.sticky_edges.x[:] = [minx, maxx]
        collection.sticky_edges.y[:] = [miny, maxy]
        corners = (minx, miny), (maxx, maxy)
        ax.update_datalim(corners)
        ax.autoscale_view()


class CbarMaker(ABC):
    r"""Mixin that draws a colorbar labelled with ``labels.z``."""

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


class PlotWithZdata(Base):
    r"""Base for plots of x, y data with an optional z value per point."""

    _alim = (None, None)
    _alim_kind = "value"

    @property
    def alim(self):
        r"""``(lower, upper)`` limits on the aggregated value; see ``set_alim``."""
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
        inclusive and None leaves that side open.

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
            row, and an orbit plot pools all of its legs.

        Raises
        ------
        ValueError
            If ``kind`` is not ``"value"`` or ``"quantile"``, or, for
            ``"quantile"``, if a limit is outside [0, 1] or ``lower`` is not
            less than ``upper``.
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
                    f"quantile alim lower={lower} must be less than upper={upper}"
                )
        self._alim = (lower, upper)
        self._alim_kind = kind

    def _apply_alim(self, agg):
        r"""Set to NaN the entries of ``agg`` outside ``alim``, bounds inclusive.

        Parameters
        ----------
        agg : pd.Series
            The final aggregated values, one per bin or cell. With
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

    def set_data(self, x, y, z=None, clip_data=False):
        r"""Store x, y and z as columns of one DataFrame, dropping rows with NaN.

        Parameters
        ----------
        x, y : pd.Series
            Coordinates of each point.
        z : pd.Series, optional
            Value at each point. If None, every point gets ``z = 1``.
        clip_data : bool, optional
            Stored as ``self.clip``.

        Raises
        ------
        ValueError
            If no row is left after dropping NaNs.
        """
        data = pd.DataFrame({"x": x, "y": y})

        if z is None:
            z = pd.Series(1, index=data.index)

        data.loc[:, "z"] = z
        data = data.dropna()
        if not data.shape[0]:
            raise ValueError(
                "You can't build a %s with data that is exclusively NaNs"
                % self.__class__.__name__
            )
        self._data = data
        self._clip = bool(clip_data)

    def set_path(self, new, add_scale=True):
        # Bug: path doesn't auto-set log information.
        path, x, y, z, scale_info = super().set_path(new, add_scale)

        if new == "auto":
            path = path / x / y / z

        else:
            assert x is None
            assert y is None
            assert z is None

        if add_scale:
            assert scale_info is not None

            scale_info = "-".join(scale_info)

            if bool(len(path.parts)) and path.parts[-1].endswith("norm"):
                # Insert <norm> at end of path so scale order is (x, y, z).
                path = path.parts
                path = path[:-1] + (scale_info + "-" + path[-1],)
                path = Path(*path)
            else:
                path = path / scale_info

        self._path = path

    set_path.__doc__ = Base.set_path.__doc__

    def set_labels(self, **kwargs):
        r"""Set or update the x, y, or z labels; see ``Base.set_labels``."""
        z = kwargs.pop("z", self.labels.z)
        super().set_labels(z=z, **kwargs)
