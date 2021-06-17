#!/usr/bin/env python
r""":py:mod:`~solarwindpy.plotting` helper functions.
"""

import pdb  # noqa: F401
import logging
import numpy as np
import matplotlib as mpl
from matplotlib import pyplot as plt
from datetime import datetime
from pathlib import Path


def subplots(nrows=1, ncols=1, scale_width=1.0, scale_height=1.0, **kwargs):
    r"""Wrapper for `plt.subplots` that calculates figsize from `nrows`,
    `ncols` when `figsize` not specified. Can optionally scale the figure
    width and hight with respect to the figsize in mpl.rcParams using
    `scale_width` and `scale_height`.
    """
    scale = np.array([scale_width * ncols, scale_height * nrows])
    figsize = scale * kwargs.pop("figsize", mpl.rcParams["figure.figsize"])

    return plt.subplots(nrows=nrows, ncols=ncols, figsize=figsize, **kwargs)


def save(
    fig,
    spath,
    add_info=True,
    info_x=0,
    info_y=0,
    log=True,
    pdf=True,
    png=True,
    **kwargs
):
    r"""Save `fig` at `spath` as png and eps, tracking the save at alog.

    Note that we add `B.L. Alterman` and the datetime to the bottom left
    corner of every figure.

    kwargs are passed to `fig.savefig`.
    """
    if isinstance(fig, mpl.axes.Axes):
        fig = fig.figure

    assert isinstance(fig, mpl.figure.Figure)
    assert isinstance(spath, Path)

    #     tight_layout = kwargs.pop("tight_layout", True)
    bbox_inches = kwargs.pop("bbox_inches", "tight")

    #     if tight_layout:
    #         fig.tight_layout()

    # Save the PDF without the timestamp so we can create the final LaTeX file
    # without them.
    # Add the datetime stamp to the PNG as those are what we render most often when
    # working, drafting, etc.

    if pdf:
        if log:
            alog = logging.getLogger(__name__)
            alog.info("Saving figure\n%s", spath.resolve().with_suffix(""))

        fig.savefig(
            spath.with_suffix(".pdf"), bbox_inches=bbox_inches, format="pdf", **kwargs
        )

        if log:
            alog.info("Suffix saved: pdf")

    if png:
        if add_info:
            info = "B. L. Alterman {}".format(datetime.now().strftime("%Y%m%dT%H%M%S"))
            fig.text(info_x, info_y, info)

        fig.savefig(
            spath.with_suffix(".png"), bbox_inches=bbox_inches, format="png", **kwargs
        )

        if log:
            alog.info("Suffix saved: png")


def joint_legend(*axes, idx_for_legend=-1, **kwargs):
    r"""Make a single legend combining handles and labels from all axes.

    Place the legend on the axis located at the raveled `idx_for_legend`.
    Assuming the last axis is on the right hand side of the figure, the default
    index is -1.
    """
    axes = np.array(axes).ravel()

    handles = []
    labels = []

    for ax in axes:
        hdl, lbl = ax.get_legend_handles_labels()
        for i, l in enumerate(lbl):
            if l not in labels:
                h = hdl[i]
                if isinstance(h, mpl.container.ErrorbarContainer):
                    h = h[0]
                #                 h = hdl[i]
                #                 try:
                #                     if len(h) == 3:
                #                         # Used `ax.errorbar`, not `ax.plot`.
                #                         h = h[0]
                #                 except TypeError:
                #                     pass

                labels.append(l)
                handles.append(h)

    handles = np.array(handles)
    labels = np.array(labels)

    sorter = np.argsort(labels)
    labels = labels[sorter]
    handles = handles[sorter]

    loc = kwargs.pop("loc", (1.05, 0.1))
    return axes[idx_for_legend].legend(handles, labels, loc=loc, **kwargs)
