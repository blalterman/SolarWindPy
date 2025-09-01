#!/usr/bin/env python
r"""Utility functions for common :mod:`matplotlib` tasks.

These helpers provide shortcuts for creating figures, saving output, and building grids
of axes with shared colorbars.
"""

import pdb  # noqa: F401
import logging
import numpy as np
import matplotlib as mpl
from matplotlib import pyplot as plt
from datetime import datetime
from pathlib import Path


def subplots(nrows=1, ncols=1, scale_width=1.0, scale_height=1.0, **kwargs):
    r"""Create a grid of subplots with a scaled figure size.

    Parameters
    ----------
    nrows : int, optional
        Number of subplot rows.
    ncols : int, optional
        Number of subplot columns.
    scale_width : float, optional
        Factor applied to the default figure width.
    scale_height : float, optional
        Factor applied to the default figure height.
    **kwargs
        Additional keyword arguments passed directly to
        :func:`matplotlib.pyplot.subplots`.

    Returns
    -------
    fig : :class:`matplotlib.figure.Figure`
    ax : :class:`matplotlib.axes.Axes` or array of Axes

    Examples
    --------
    >>> fig, ax = subplots(2, 2, scale_width=1.5)
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
    **kwargs,
):
    r"""Save a figure in both PDF and PNG formats.

    Parameters
    ----------
    fig : :class:`matplotlib.figure.Figure` or :class:`matplotlib.axes.Axes`
        The figure or axis to save.
    spath : :class:`pathlib.Path`
        Base path for the output files.  The appropriate extension will be
        added automatically.
    add_info : bool, optional
        If ``True``, add an attribution and timestamp to the bottom left of the
        PNG version.
    info_x : float, optional
        X-position of the attribution text in figure coordinates.
    info_y : float, optional
        Y-position of the attribution text in figure coordinates.
    log : bool, optional
        If ``True``, write information about the saved files to ``alog``.
    pdf : bool, optional
        Save a PDF version of the figure.
    png : bool, optional
        Save a PNG version of the figure.
    **kwargs
        Additional keyword arguments passed to :meth:`Figure.savefig`.

    Returns
    -------
    None

    Examples
    --------
    >>> fig, ax = subplots()
    >>> save(fig, Path('my_plot'))
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

    if log:
        alog = logging.getLogger(__name__)
        alog.info("Saving figure\n%s", spath.resolve().with_suffix(""))

    if pdf:

        fig.savefig(
            spath.with_suffix(".pdf"),
            bbox_inches=bbox_inches,
            format="pdf",
            **kwargs,
        )

        if log:
            alog.info("Suffix saved: pdf")

    if png:
        if add_info:
            info = "B. L. Alterman {}".format(datetime.now().strftime("%Y%m%dT%H%M%S"))
            fig.text(info_x, info_y, info)

        fig.savefig(
            spath.with_suffix(".png"),
            bbox_inches=bbox_inches,
            format="png",
            **kwargs,
        )

        if log:
            alog.info("Suffix saved: png")


def joint_legend(*axes, idx_for_legend=-1, **kwargs):
    r"""Create a combined legend for multiple axes.

    Parameters
    ----------
    *axes : :class:`matplotlib.axes.Axes`
        Axes objects from which to collect legend handles and labels.
    idx_for_legend : int, optional
        Index of the axis (after flattening) on which to place the legend.
        By default the legend is placed on the last axis. ``idx_for_legend=-1``
        assumes that the last axis is on the right hand side of the figure.
    **kwargs
        Extra keyword arguments forwarded to :meth:`Axes.legend`.

    Returns
    -------
    legend : :class:`matplotlib.legend.Legend`

    Examples
    --------
    >>> fig, ax = subplots(1, 2)
    >>> ax[0].plot([1, 2], label='a')  # doctest: +ELLIPSIS
    [<matplotlib.lines.Line2D object at 0x...>]
    >>> ax[1].plot([2, 3], label='b')  # doctest: +ELLIPSIS
    [<matplotlib.lines.Line2D object at 0x...>]
    >>> joint_legend(ax[0], ax[1])  # doctest: +ELLIPSIS
    <matplotlib.legend.Legend object at 0x...>
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


def multipanel_figure_shared_cbar(
    nrows: int,
    ncols: int,
    vertical_cbar: bool = True,
    sharex: bool = True,
    sharey: bool = True,
    **kwargs,
):
    r"""Create a grid of axes that share a single colorbar.

    This is a lightweight wrapper around
    :func:`build_ax_array_with_common_colorbar` for backward compatibility.

    Parameters
    ----------
    nrows, ncols : int
        Shape of the axes grid.
    vertical_cbar : bool, optional
        If ``True`` the colorbar is placed to the right of the axes; otherwise
        it is placed above them.
    sharex, sharey : bool, optional
        If ``True`` share the respective axis limits across all panels.
    **kwargs
        Additional arguments controlling layout such as ``figsize`` or grid
        ratios.

    Returns
    -------
    fig : :class:`matplotlib.figure.Figure`
    axes : ndarray of :class:`matplotlib.axes.Axes`
    cax : :class:`matplotlib.axes.Axes`

    Examples
    --------
    >>> fig, axs, cax = multipanel_figure_shared_cbar(2, 2)  # doctest: +SKIP
    """

    fig_kwargs = {}
    gs_kwargs = {}

    if "figsize" in kwargs:
        fig_kwargs["figsize"] = kwargs.pop("figsize")

    for key in ("width_ratios", "height_ratios", "wspace", "hspace"):
        if key in kwargs:
            gs_kwargs[key] = kwargs.pop(key)

    fig_kwargs.update(kwargs)

    cbar_loc = "right" if vertical_cbar else "top"

    return build_ax_array_with_common_colorbar(
        nrows,
        ncols,
        cbar_loc=cbar_loc,
        fig_kwargs=fig_kwargs,
        gs_kwargs=dict(gs_kwargs, sharex=sharex, sharey=sharey),
    )


def build_ax_array_with_common_colorbar(
    nrows=1, ncols=1, cbar_loc="top", fig_kwargs=None, gs_kwargs=None
):
    r"""Build an array of axes that share a colour bar.

    Parameters
    ----------
    nrows, ncols : int, optional
        Desired grid shape.
    cbar_loc : {"top", "bottom", "left", "right"}, optional
        Location of the colorbar relative to the axes grid.
    fig_kwargs : dict, optional
        Keyword arguments forwarded to :func:`matplotlib.pyplot.figure`.
    gs_kwargs : dict, optional
        Additional options for :class:`matplotlib.gridspec.GridSpec`.

    Returns
    -------
    fig : :class:`matplotlib.figure.Figure`
    axes : ndarray of :class:`matplotlib.axes.Axes`
    cax : :class:`matplotlib.axes.Axes`

    Examples
    --------
    >>> fig, axes, cax = build_ax_array_with_common_colorbar(2, 3, cbar_loc='right')  # doctest: +SKIP
    """

    if fig_kwargs is None:
        fig_kwargs = dict()
    if gs_kwargs is None:
        gs_kwargs = dict()

    cbar_loc = cbar_loc.lower()
    if cbar_loc not in ("top", "bottom", "left", "right"):
        raise ValueError

    figsize = np.array(mpl.rcParams["figure.figsize"])
    fig_scale = np.array([ncols, nrows])

    if cbar_loc in ("right", "left"):
        cbar_scale = np.array([1.3, 1])
        height_ratios = nrows * [1]
        width_ratios = (ncols * [1]) + [0.05, 0.075]
        if cbar_loc == "left":
            width_ratios = width_ratios[::-1]

    else:
        cbar_scale = np.array([1, 1.3])
        height_ratios = [0.075, 0.05] + (nrows * [1])
        if cbar_loc == "bottom":
            height_ratios = height_ratios[::-1]
        width_ratios = ncols * [1]

    figsize = figsize * fig_scale * cbar_scale
    fig = plt.figure(figsize=figsize, **fig_kwargs)

    hspace = gs_kwargs.pop("hspace", 0)
    wspace = gs_kwargs.pop("wspace", 0)
    sharex = gs_kwargs.pop("sharex", True)
    sharey = gs_kwargs.pop("sharey", True)

    #     print(cbar_loc)
    #     print(nrows, ncols)
    #     print(len(height_ratios), len(width_ratios))
    #     print()

    gs = mpl.gridspec.GridSpec(
        len(height_ratios),
        len(width_ratios),
        hspace=hspace,
        wspace=wspace,
        height_ratios=height_ratios,
        width_ratios=width_ratios,
        **gs_kwargs,
    )

    if cbar_loc == "left":
        cax = gs[:, 0]
        col_range = range(2, ncols + 2)
        row_range = range(nrows)
    elif cbar_loc == "right":
        cax = gs[:, -1]
        col_range = range(0, ncols)
        row_range = range(nrows)
    elif cbar_loc == "top":
        cax = gs[0, :]
        col_range = range(ncols)
        row_range = range(2, nrows + 2)
    elif cbar_loc == "bottom":
        cax = gs[-1, :]
        col_range = range(ncols)
        row_range = range(0, nrows)
    else:
        raise ValueError

    cax = fig.add_subplot(cax)
    axes = np.array([[fig.add_subplot(gs[i, j]) for j in col_range] for i in row_range])

    if cbar_loc == "top":
        cax.xaxis.set_ticks_position("top")
        cax.xaxis.set_label_position("top")
    elif cbar_loc == "left":
        cax.yaxis.set_ticks_position("left")
        cax.yaxis.set_label_position("left")

    if sharex:
        axes.flat[0].get_shared_x_axes().join(*axes.flat)
    if sharey:
        axes.flat[0].get_shared_y_axes().join(*axes.flat)

    if axes.shape != (nrows, ncols):
        raise ValueError(
            f"""Unexpected axes shape
Expected : {(nrows, ncols)}
Created  : {axes.shape}
"""
        )

    #     print("rows")
    #     print(list(row_range))
    #     print(height_ratios)
    #     print()

    #     print("cols")
    #     print(list(col_range))
    #     print(width_ratios)

    axes = axes.squeeze()
    return fig, axes, cax


def calculate_nrows_ncols(n):
    r"""Determine a sensible ``(nrows, ncols)`` pair for ``n`` axes.

    The heuristic attempts to generate a nearly square layout while also taking
    typical display aspect ratios into account.

    Parameters
    ----------
    n : int
        Total number of axes required.

    Returns
    -------
    nrows : int
    ncols : int

    Examples
    --------
    >>> calculate_nrows_ncols(5)  # doctest: +ELLIPSIS
    (...2..., ...3...)
    """
    root = int(np.fix(np.sqrt(n)))
    while n % root:
        root -= 1
    other = int(n / root)

    if ((other == 1) or (root == 1)) and (n > 4):
        n += 1
        root = int(np.fix(np.sqrt(n)))
        while n % root:
            root -= 1
    other = int(n / root)

    nrows = np.max([root, other])
    ncols = np.min([root, other])
    if nrows < 4:
        nrows, ncols = ncols, nrows

    return nrows, ncols
