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


def save(fig, spath, add_info=True, tight_layout=True, **kwargs):
    r"""Save `fig` at `spath` as png and eps, tracking the save at alog.

    Note that we add `B.L. Alterman` and the datetime to the bottom left
    corner of every figure.

    kwargs are passed to `fig.savefig`.
    """
    assert isinstance(fig, mpl.figure.Figure)
    assert isinstance(spath, Path)

    alog = logging.getLogger("analysis.%s" % __name__)

    fig.tight_layout()

    if add_info:
        info = "B. L. Alterman %s" % datetime.now().strftime("%Y%m%dT%H%M%S")
        fig.text(0, 0, info)
        fig.tight_layout()

    alog.debug("Saving figure\n%s" % spath.resolve())

    bbox_inches = kwargs.pop("bbox_inches", "tight")
    meta = kwargs.pop("metadata", {})
    if "Author" not in meta.keys():
        meta["Author"] = "B. L. Alterman"
    #    pdf_meta = {k: v for k, v in meta.items()}
    #    png_meta = {k: v for k, v in meta.items()}
    #    if "Author" not in pdf_meta:
    #        pdf_meta["Author"] = "B. L. Alterman"

    # Save the PDF without the timestamp so we can create the final LaTeX file
    # without them.
    for fmt in (".pdf", ".png"):
        fig.savefig(
            spath.with_suffix(fmt),
            bbox_inches=bbox_inches,
            format=fmt.strip("."),
            meta=meta,
            **kwargs
        )

    # Add the datetime stamp to the PNG as those are what we render most often when
    # working, drafting, etc.

    #     fig.savefig(spath.with_suffix(".png"),
    #                 bbox_inches=bbox_inches,
    #                 format="png",
    #                 meta=meta,
    #                 **kwargs)

    alog.info("Saved figure\n%s" % spath.resolve())
