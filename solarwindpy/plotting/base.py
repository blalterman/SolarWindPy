#!/usr/bin/env python
r"""Base classes for plotting utilities.

This module defines abstract helpers that manage axis labels, log scaling, and file
system paths for saving figures.  Concrete plot classes derive from these mixins to
implement specific visualizations.
"""

import pdb  # noqa: F401
import logging
import pandas as pd

from pathlib import Path
from collections import namedtuple
from abc import ABC, abstractmethod

LogAxes = namedtuple("LogAxes", "x,y", defaults=(False,))
AxesLabels = namedtuple("AxesLabels", "x,y,z", defaults=(None,))
RangeLimits = namedtuple("RangeLimits", "lower,upper", defaults=(None,))


class Base(ABC):
    r"""ABC for core plot tools.

    Attributes
    ----------

    Methods
    -------
    """

    @abstractmethod
    def __init__(self):
        self._init_logger()
        self._labels = AxesLabels(x="x", y="y")
        self._log = LogAxes(x=False)
        self.set_path("auto")

    def __str__(self):
        return self.__class__.__name__

    @property
    def logger(self):
        return self._logger

    def _init_logger(self):
        # return None
        logger = logging.getLogger("{}.{}".format(__name__, self.__class__.__name__))
        self._logger = logger

    #     # Old version that cuts at percentiles.
    #     @staticmethod
    #     def clip_data(data, clip):
    #         q0 = 0.0001
    #         q1 = 0.9999
    #         pct = data.quantile([q0, q1])
    #         lo = pct.loc[q0]
    #         up = pct.loc[q1]

    #         if isinstance(data, pd.Series):
    #             ax = 0
    #         elif isinstance(data, pd.DataFrame):
    #             ax = 1
    #         else:
    #             raise TypeError("Unexpected object %s" % type(data))

    #         if isinstance(clip, str) and clip.lower()[0] == "l":
    #             data = data.clip_lower(lo, axis=ax)
    #         elif isinstance(clip, str) and clip.lower()[0] == "u":
    #             data = data.clip_upper(up, axis=ax)
    #         else:
    #             data = data.clip(lo, up, axis=ax)
    #         return data

    #     # New version that uses binning to cut.
    #     #     @staticmethod
    #     #     def clip_data(data, bins, clip):
    #     #         q0 = 0.001
    #     #         q1 = 0.999
    #     #         pct = data.quantile([q0, q1])
    #     #         lo  = pct.loc[q0]
    #     #         up  = pct.loc[q1]
    #     #         lo = bins.iloc[0]
    #     #         up = bins.iloc[-1]
    #     #         if isinstance(clip, str) and clip.lower()[0] == "l":
    #     #             data = data.clip_lower(lo)
    #     #         elif isinstance(clip, str) and clip.lower()[0] == "u":
    #     #             data = data.clip_upper(up)
    #     #         else:
    #     #             data = data.clip(lo, up)
    #     #         return data

    @property
    def data(self):
        return self._data

    @property
    def clip(self):
        return self._clip

    @property
    def log(self):
        return self._log

    @property
    def labels(self):
        return self._labels

    @property
    def path(self):
        r"""Path for saving figure."""
        return self._path

    def set_log(self, x=None, y=None):
        if x is None:
            x = self.log.x
        if y is None:
            y = self.log.y

        log = LogAxes(bool(x), bool(y))
        self._log = log

    def set_labels(self, **kwargs):
        r"""Set or update x, y, or z labels. Any label not specified in kwargs.

        is propagated from `self.labels.<x, y, or z>`.
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
        new: str or Path
            If str and == "auto", then build path from `self.labels`. Otherwise,
            assume parameter specifies the desired path and use `Path(new)`.
        add_scale: bool
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

    #         x = self.data.loc[:, "x"]
    #         minx, maxx = x.min(), x.max()
    #         if self.log.x:
    #             minx, maxx = 10.0**np.array([minx, maxx])

    #         y = self.data.loc[:, "y"]
    #         miny, maxy = y.min(), y.max()
    #         if self.log.y:
    #             minx, maxx = 10.0**np.array([miny, maxy])

    #         # `pulled from the end of `ax.pcolormesh`.
    #         collection.sticky_edges.x[:] = [minx, maxx]
    #         collection.sticky_edges.y[:] = [miny, maxy]
    #         corners = (minx, miny), (maxx, maxy)
    #         self.update_datalim(corners)
    #         self.autoscale_view()

    @abstractmethod
    def set_data(self):
        pass

    @abstractmethod
    def make_plot(self):
        pass


class DataLimFormatter(ABC):
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
    def set_data(self, x, y, z=None, clip_data=False):
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
        z = kwargs.pop("z", self.labels.z)
        super().set_labels(z=z, **kwargs)


# class Plot2D(CbarMaker, Base):
#     def set_data(self, x, y, z=None, clip_data=False):
#         data = pd.DataFrame({"x": x, "y": y})

#         if z is None:
#             z = pd.Series(1, index=data.index)

#         data.loc[:, "z"] = z
#         data = data.dropna()
#         if not data.shape[0]:
#             raise ValueError(
#                 "You can't build a %s with data that is exclusively NaNs"
#                 % self.__class__.__name__
#             )
#         self._data = data
#         self._clip = bool(clip_data)

#     def set_path(self, new, add_scale=True):
#         # Bug: path doesn't auto-set log information.
#         path, x, y, z, scale_info = super().set_path(new, add_scale)

#         if new == "auto":
#             path = path / x / y / z

#         else:
#             assert x is None
#             assert y is None
#             assert z is None

#         if add_scale:
#             assert scale_info is not None

#             scale_info = "-".join(scale_info)

#             if bool(len(path.parts)) and path.parts[-1].endswith("norm"):
#                 # Insert <norm> at end of path so scale order is (x, y, z).
#                 path = path.parts
#                 path = path[:-1] + (scale_info + "-" + path[-1],)
#                 path = Path(*path)
#             else:
#                 path = path / scale_info

#         self._path = path

#     set_path.__doc__ = Base.set_path.__doc__

#     def set_labels(self, **kwargs):
#         z = kwargs.pop("z", self.labels.z)
#         super().set_labels(z=z, **kwargs)

# #     def _make_cbar(self, mappable, **kwargs):
# #         f"""Make a colorbar on `ax` using `mappable`.

# #         Parameters
# #         ----------
# #         mappable:
# #             See `figure.colorbar` kwarg of same name.
# #         ax: mpl.axis.Axis
# #             See `figure.colorbar` kwarg of same name.
# #         norm: mpl.colors.Normalize instance
# #             The normalization used in the plot. Passed here to determine
# #             y-ticks.
# #         kwargs:
# #             Passed to `fig.colorbar`. If `{self.__class__.__name__}` is
# #             row or column normalized, `ticks` defaults to
# #             :py:class:`mpl.ticker.MultipleLocator(0.1)`.
# #         """
# #         ax = kwargs.pop("ax", None)
# #         cax = kwargs.pop("cax", None)
# #         if ax is not None and cax is not None:
# #             raise ValueError("Can't pass ax and cax.")

# #         if ax is not None:
# #             try:
# #                 fig = ax.figure
# #             except AttributeError:
# #                 fig = ax[0].figure
# #         elif cax is not None:
# #             try:
# #                 fig = cax.figure
# #             except AttributeError:
# #                 fig = cax[0].figure
# #         else:
# #             raise ValueError(
# #                 "You must pass `ax` or `cax`. We don't want to rely on `plt.gca()`."
# #             )

# #         label = kwargs.pop("label", self.labels.z)
# #         cbar = fig.colorbar(mappable, label=label, ax=ax, cax=cax, **kwargs)

# #         return cbar
