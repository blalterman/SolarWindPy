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
    figsize = kwargs.pop("figsize", scale * mpl.rcParams["figure.figsize"])

    return plt.subplots(nrows=nrows, ncols=ncols, figsize=figsize, **kwargs)


def save(fig, spath, add_info=True, info_x=0, info_y=0, **kwargs):
    r"""Save `fig` at `spath` as png and eps, tracking the save at alog.

    Note that we add `B.L. Alterman` and the datetime to the bottom left
    corner of every figure.

    kwargs are passed to `fig.savefig`.
    """
    if isinstance(fig, mpl.axes.Axes):
        fig = fig.figure

    assert isinstance(fig, mpl.figure.Figure)
    assert isinstance(spath, Path)

    alog = logging.getLogger(__name__)

    tight_layout = kwargs.pop("tight_layout", True)
    bbox_inches = kwargs.pop("bbox_inches", "tight")

    if tight_layout:
        fig.tight_layout()

    meta = kwargs.pop("metadata", {})
    if "Author" not in meta.keys():
        meta["Author"] = "B. L. Alterman"
    #    pdf_meta = {k: v for k, v in meta.items()}
    #    png_meta = {k: v for k, v in meta.items()}
    #    if "Author" not in pdf_meta:
    #        pdf_meta["Author"] = "B. L. Alterman"

    # Save the PDF without the timestamp so we can create the final LaTeX file
    # without them.
    # Add the datetime stamp to the PNG as those are what we render most often when
    # working, drafting, etc.

    alog.info("Saving figure\n%s", spath.resolve().with_suffix(""))

    fig.savefig(
        spath.with_suffix(".pdf"),
        bbox_inches=bbox_inches,
        format="pdf",
        meta=meta,
        **kwargs
    )
    alog.info("Suffix saved: pdf")

    if add_info:
        info = "B. L. Alterman {}".format(datetime.now().strftime("%Y%m%dT%H%M%S"))
        fig.text(info_x, info_y, info)

    fig.savefig(
        spath.with_suffix(".png"),
        bbox_inches=bbox_inches,
        format="png",
        meta=meta,
        **kwargs
    )
    alog.info("Suffix saved: png")


def joint_legend(ax, tax, **kwargs):
    r"""Create one legend on `ax` that contains information for both `ax` and `tax.
    """

    h0, l0 = ax.get_legend_handles_labels()
    h1, l1 = tax.get_legend_handles_labels()
    hdl = h0 + h1
    lbl = l0 + l1
    ax.legend(hdl, lbl, **kwargs)
