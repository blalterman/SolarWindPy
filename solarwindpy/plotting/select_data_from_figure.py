"""Interactive selection utilities for plotted data."""

__all__ = ["SelectFromPlot2D"]
import pdb  # noqa: F401
import logging

import numpy as np
import pandas as pd
import matplotlib as mpl
from collections import namedtuple

DateAxes = namedtuple("DateAxes", "x,y")


class SelectFromPlot2D(object):
    def __init__(
        self, plotter, ax, has_colorbar=True, xdate=False, ydate=False, text_kwargs=None
    ):
        self._plotter = plotter
        self.set_ax(ax, has_colorbar)
        self._init_corners()
        #         self._init_centers()

        if text_kwargs is None:
            text_kwargs = {}

        self.start_selector()
        self.set_date_axes(xdate, ydate)
        self.start_text(**text_kwargs)

    @property
    def ax(self):
        return self._ax

    @property
    def corners(self):
        return self._corners

    @property
    def date_axes(self):
        return self._date_axes

    @property
    def is_multipanel(self):
        return self._is_multipanel

    @property
    def plotter(self):
        return self._plotter

    @property
    def sampled_indices(self):
        return self._sampled_indices

    @property
    def failed_samples(self):
        return self._failed_samples

    @property
    def sampled_per_patch(self):
        return self._sampled_per_patch

    @property
    def selector(self):
        return self._selector

    @property
    def text(self):
        return self._text

    @property
    def num_initial_patches(self):
        return self._num_initial_patches

    @property
    def num_selection_patches(self):
        return len(self.ax.patches) - self.num_initial_patches

    @property
    def logger(self):
        return logging.getLogger(f"analysis.{__name__}")

    def _init_corners(self):
        self._corners = tuple()

    def _add_corners(self, corners):
        self._corners = self.corners + (corners,)

    def _finalize_text(self):
        tx = f"""{self.num_selection_patches} Patches
{self.sampled_per_patch} Spectra / Patch
{self.sampled_indices.size} Spectra Selected
{len(self.failed_samples)} Empty Patches"""

        if not self.is_multipanel:
            tx = tx.replace("\n", "  -  ")

        self.text.set_text(tx)

    def _update_text(self):
        x0, x1, y0, y1 = self.selector.extents

        if self.date_axes.x:
            x0, x1 = mpl.dates.num2date([x0, x1])
            x0 = x0.strftime("%Y-%m-%d %H:%M:%s")
            x1 = x1.strftime("%Y-%m-%d %H:%M:%s")
        else:
            x0 = f"{x0:.3e}"
            x1 = f"{x1:.3e}"

        if self.date_axes.y:
            y0, y1 = mpl.dates.num2date([y0, y1])
            y0 = y0.strftime("%Y-%m-%d %H:%M:%s")
            y1 = y1.strftime("%Y-%m-%d %H:%M:%s")
        else:
            y0 = f"{y0:.3e}"
            y1 = f"{y1:.3e}"

        tx = f"""Patch {self.num_selection_patches}
Lower Left  {x0, y0}
Upper Right {x1, y1}"""

        self.text.set_text(tx)

    def disconnect(self, other_SelectFromPlot2D=None, scatter_kwargs=None, **kwargs):

        if scatter_kwargs is None:
            scatter_kwargs = dict()

        self.sample_data(other_SelectFromPlot2D=other_SelectFromPlot2D, **kwargs)
        self.scatter_sample(**scatter_kwargs)
        self.plot_failed_samples()
        self._finalize_text()

        self.selector.disconnect_events()

    def onselect(self, press, release):
        *xy, w, h = self.selector._rect_bbox
        rect = mpl.patches.Rectangle(
            xy, w, h, color="cyan", alpha=0.2, fill=True, edgecolor="k", linewidth=1
        )
        self.ax.add_patch(rect)
        self._add_corners(self.selector.extents)

        self._update_text()
        self.ax.figure.canvas.draw_idle()

    def set_ax(self, ax, has_colorbar):
        is_multipanel = (len(ax.figure.axes) - bool(has_colorbar)) > 1

        self._ax = ax
        self._is_multipanel = is_multipanel

    def start_text(self, **kwargs):
        ax = self.ax
        is_multipanel = self.is_multipanel

        kwargs = mpl.cbook.normalize_kwargs(kwargs, mpl.text.Text._alias_map)

        xloc = kwargs.pop("x", 0.015 if is_multipanel else 0.00)
        yloc = kwargs.pop("y", 0.975 if is_multipanel else 1.05)
        va = kwargs.pop("va", "top" if is_multipanel else "bottom")
        ha = kwargs.pop("ha", "left")
        transform = kwargs.pop("transform", ax.transAxes)
        fontdict = kwargs.pop("fontdict", dict(fontsize="small"))
        bbox = kwargs.pop("bbox", dict(color="wheat", alpha=0.5))

        text = ax.text(
            xloc,
            yloc,
            "Selection Info Will Appear Here",
            va=va,
            ha=ha,
            transform=transform,
            fontdict=fontdict,
            bbox=bbox,
        )

        self._text = text

    def start_selector(self):
        self._selector = mpl.widgets.RectangleSelector(
            self.ax, self.onselect, rectprops=dict(color="lime", alpha=0.25, fill=True)
        )
        self._num_initial_patches = len(self.ax.patches)

    def sample_data(self, other_SelectFromPlot2D=None, **kwargs):
        n = kwargs.pop("n", 3)
        random_state = kwargs.pop("random_state", 20200629)
        frac = kwargs.pop("frac", None)
        if frac is not None:
            raise NotImplementedError("Please use the `n` kwarg")

        plotter = self.plotter
        logx = plotter.log.x
        logy = plotter.log.y

        xdata = plotter.data.loc[:, "x"]
        ydata = plotter.data.loc[:, "y"]

        if other_SelectFromPlot2D is not None:
            if not hasattr(other_SelectFromPlot2D, "__iter__"):
                other_SelectFromPlot2D = [other_SelectFromPlot2D]

            already_selected = []
            for other in other_SelectFromPlot2D:

                try:
                    already_selected.extend(other.sampled_indices.tolist())
                except AttributeError:
                    pass

            already_selected = pd.Index(already_selected)

            try:
                xdata = xdata.drop(already_selected, axis=0)
                ydata = ydata.drop(already_selected, axis=0)
            except KeyError:
                self.logger.warning(
                    f"""None of `already_selected` found in xdata or ydata
x : ({self.ax.xaxis.get_label().get_text()})
y : ({self.ax.yaxis.get_label().get_text()}).
"""
                )

        indices = []
        failed = []
        for corner in self.corners:
            # Expand here so keep original `corner` for `failed.append`.
            x0, x1, y0, y1 = corner
            if logx:
                x0, x1 = np.log10([x0, x1])
            if logy:
                y0, y1 = np.log10([y0, y1])

            tk_x = (x0 < xdata) & (xdata <= x1)
            tk_y = (y0 < ydata) & (ydata <= y1)
            tk = tk_x & tk_y

            if not tk.sum():
                failed.append(corner)
                continue

            idx = tk.loc[tk].index.to_series()
            try:
                sample = idx.sample(n=n, random_state=random_state, **kwargs)
            except ValueError as e:
                if (
                    str(e)
                    == "Cannot take a larger sample than population when 'replace=False'"
                ):
                    self.logger.warning(
                        "Sample failed without replacement. Attempting with replacement and then dropping duplicates."
                    )
                    sample = idx.sample(
                        n=n, random_state=random_state, replace=True, **kwargs
                    )
                    sample.drop_duplicates(inplace=True)
                else:
                    raise e

            indices.extend(sample.values)

        self._sampled_indices = pd.Index(indices).sort_values()
        self._failed_samples = tuple(failed)
        self._sampled_per_patch = n

    def scatter_sample(self, **kwargs):
        plotter = self.plotter
        ax = self.ax
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        data = plotter.data.loc[self.sampled_indices].drop("z", axis=1)

        x = data.loc[:, "x"]
        y = data.loc[:, "y"]
        if self.plotter.log.x:
            x = 10.0**x
        if self.plotter.log.y:
            y = 10.0**y

        kwargs = mpl.cbook.normalize_kwargs(
            kwargs, mpl.collections.PatchCollection._alias_map
        )
        label = kwargs.pop("label", "Sample")
        s = kwargs.pop("s", 20)
        c = kwargs.pop("c", "fuchsia")
        marker = kwargs.pop("marker", ".")
        ax.scatter(
            x,
            y,
            label=label,
            s=s,
            c=c,
            #             edgecolors="k",
            #             linewidths=1,
            marker=marker,
            **kwargs,
            #             alpha=0.75,
            #             data=data,
        )

        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)

    def plot_failed_samples(self):
        ax = self.ax
        for x0, x1, y0, y1 in self.failed_samples:
            w = x1 - x0
            h = y1 - y0
            rect = mpl.patches.Rectangle(
                (x0, y0),
                w,
                h,
                color="dodgerblue",
                #                                          alpha=0.75,
                fill=False,
                hatch="///",
                edgecolor="k",
                #                                          linewidth=1,
            )
            ax.add_patch(rect)

        ax.figure.canvas.draw_idle()

    def set_date_axes(self, xdate, ydate):
        dates = DateAxes(xdate, ydate)
        self._date_axes = dates
