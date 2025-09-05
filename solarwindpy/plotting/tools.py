#!/usr/bin/env python
r"""Comprehensive matplotlib utility functions for solar wind data visualization.

This module provides a complete toolkit of matplotlib helper functions specifically
optimized for solar wind research applications. The utilities handle common plotting
tasks including figure creation, multi-panel layouts, publication-quality output
generation, and complex colorbar management for scientific data visualization.

The module addresses key challenges in solar wind data presentation:

- Multi-panel figure layouts with consistent scaling and shared colorbars
- Publication-ready output in multiple formats (PDF, PNG) with metadata
- Complex axes arrangements for comparative analysis across different parameters
- Automated figure sizing calculations based on subplot grid dimensions
- Intelligent legend management across multiple plot panels

Key Components
--------------
Figure Creation
    - subplots(): Enhanced subplot creation with automatic size scaling
    - calculate_nrows_ncols(): Optimal grid layout determination

Output Management
    - save(): Dual-format publication output with metadata and timestamps
    - Automatic format selection and quality optimization

Layout Utilities
    - build_ax_array_with_common_colorbar(): Complex shared colorbar layouts
    - multipanel_figure_shared_cbar(): Simplified multi-panel figure creation
    - joint_legend(): Combined legend creation across multiple axes

These functions integrate seamlessly with SolarWindPy's plotting classes to provide
a complete visualization framework for solar wind plasma analysis, from simple
parameter plots to complex multi-spacecraft comparative studies.

Examples
--------
Create a multi-panel figure with shared colorbar for parameter comparison:

>>> fig, axes, cax = multipanel_figure_shared_cbar(2, 3, vertical_cbar=True)
>>> # Plot different parameters on each axis with shared color scaling
>>> for ax in axes.flat:
...     # Add individual parameter plots
...     pass

Generate publication-quality output with metadata:

>>> fig, ax = subplots(scale_width=1.5, scale_height=1.2)
>>> # Create visualization
>>> save(fig, Path('solar_wind_analysis'), add_info=True)
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
    r"""Build a sophisticated axes array with integrated shared colorbar for multi-parameter analysis.

    This function creates complex figure layouts optimized for comparative solar wind
    parameter visualization where multiple plots share the same color scale. It handles
    the intricate calculations required for proper colorbar positioning, axes alignment,
    and figure sizing to create publication-quality multi-panel visualizations.

    The function is particularly valuable for solar wind studies requiring parameter
    comparisons across different time periods, spacecraft, or physical regions while
    maintaining consistent color mapping for quantitative interpretation.

    Parameters
    ----------
    nrows, ncols : int, optional, default 1
        Grid dimensions for the main plotting axes array. Total number of plot
        axes will be nrows × ncols. These axes share the common colorbar and
        typically display related but distinct parameter views (e.g., different
        time intervals, spacecraft, or parameter combinations).
    cbar_loc : {"top", "bottom", "left", "right"}, optional, default "top"
        Colorbar placement relative to the main axes grid. Choice affects the
        figure aspect ratio and optimal subplot arrangements:

        - "right": Vertical colorbar, good for wide parameter ranges
        - "left": Vertical colorbar with reversed layout
        - "top": Horizontal colorbar, saves vertical space
        - "bottom": Horizontal colorbar with reversed layout

    fig_kwargs : dict, optional
        Additional parameters passed to matplotlib.pyplot.figure() for overall
        figure configuration. Common options include:

        - 'figsize': Override automatic size calculation
        - 'dpi': Resolution for figure rendering
        - 'facecolor': Background color
        - 'tight_layout': Layout engine selection

    gs_kwargs : dict, optional
        Advanced GridSpec configuration for fine-tuning subplot arrangement.
        Supports all matplotlib.gridspec.GridSpec parameters including:

        - 'width_ratios', 'height_ratios': Custom subplot size ratios
        - 'wspace', 'hspace': Inter-subplot spacing control
        - 'sharex', 'sharey': Axis sharing configuration
        - 'left', 'right', 'top', 'bottom': Figure margin control

    Returns
    -------
    fig : matplotlib.figure.Figure
        Complete figure object containing all axes and colorbar. Sized automatically
        based on grid dimensions and colorbar placement for optimal aspect ratios
        in solar wind data presentation.
    axes : numpy.ndarray of matplotlib.axes.Axes
        Two-dimensional array of plotting axes with shape (nrows, ncols).
        Individual axes accessed via axes[i, j] indexing. All axes are properly
        configured for parameter plotting with shared axis limits when appropriate.
    cax : matplotlib.axes.Axes
        Dedicated colorbar axes positioned according to cbar_loc parameter.
        Pre-configured with appropriate tick and label positioning for the
        specified colorbar orientation and location.

    Notes
    -----
    This function performs complex layout calculations to ensure optimal spacing
    and sizing for solar wind data visualization:

    1. **Automatic Figure Sizing**: Calculates figure dimensions based on grid
       size and colorbar placement, accounting for typical solar wind parameter
       display requirements and publication format constraints.

    2. **GridSpec Configuration**: Sets up sophisticated grid layouts with
       appropriate spacing ratios between main plots and colorbar areas.

    3. **Colorbar Integration**: Creates properly positioned and sized colorbar
       axes with correct tick and label orientation for each placement option.

    4. **Axis Sharing**: Configures intelligent axis sharing to maintain
       consistent scales across related parameter comparisons while allowing
       independent scaling when needed.

    The sizing calculations include scaling factors optimized for solar wind
    parameter ranges and typical publication requirements, ensuring readable
    plots at both screen and print resolutions.

    Examples
    --------
    Create a 2×3 parameter comparison with right-side colorbar:

    >>> fig, axes, cax = build_ax_array_with_common_colorbar(
    ...     2, 3, cbar_loc='right')
    >>> # Plot velocity data on each axis with shared magnetic field coloring
    >>> for i in range(2):
    ...     for j in range(3):
    ...         axes[i, j].scatter(x_data[i,j], y_data[i,j], c=b_field[i,j])

    Setup custom spacing for dense parameter display:

    >>> gs_config = {'hspace': 0.1, 'wspace': 0.05, 'sharex': True, 'sharey': True}
    >>> fig, axes, cax = build_ax_array_with_common_colorbar(
    ...     3, 2, cbar_loc='bottom', gs_kwargs=gs_config)

    Create publication-ready figure with custom size:

    >>> fig_config = {'figsize': (12, 8), 'dpi': 300}
    >>> fig, axes, cax = build_ax_array_with_common_colorbar(
    ...     2, 2, fig_kwargs=fig_config)
    """

    # Initialize configuration dictionaries with defaults
    if fig_kwargs is None:
        fig_kwargs = dict()
    if gs_kwargs is None:
        gs_kwargs = dict()

    # Validate and normalize colorbar location parameter
    cbar_loc = cbar_loc.lower()
    if cbar_loc not in ("top", "bottom", "left", "right"):
        raise ValueError("cbar_loc must be one of: 'top', 'bottom', 'left', 'right'")

    # Start with matplotlib default figure size as baseline
    figsize = np.array(mpl.rcParams["figure.figsize"])
    # Scale base figure size by grid dimensions for proper subplot sizing
    fig_scale = np.array([ncols, nrows])

    # Configure grid layout based on colorbar position
    # Different orientations require different space allocation strategies
    if cbar_loc in ("right", "left"):
        # Vertical colorbar: increase width, maintain height proportions
        cbar_scale = np.array([1.3, 1])  # 30% additional width for colorbar
        height_ratios = nrows * [1]  # Equal height for all subplot rows
        # Width allocation: main plots + gap + colorbar
        width_ratios = (ncols * [1]) + [0.05, 0.075]  # 5% gap + 7.5% colorbar
        if cbar_loc == "left":
            # Reverse order for left-side colorbar placement
            width_ratios = width_ratios[::-1]

    else:
        # Horizontal colorbar: increase height, maintain width proportions
        cbar_scale = np.array([1, 1.3])  # 30% additional height for colorbar
        # Height allocation: colorbar + gap + main plots
        height_ratios = [0.075, 0.05] + (nrows * [1])  # 7.5% colorbar + 5% gap
        if cbar_loc == "bottom":
            # Reverse order for bottom colorbar placement
            height_ratios = height_ratios[::-1]
        width_ratios = ncols * [1]  # Equal width for all subplot columns

    # Calculate final figure size using cascading scaling factors
    # Base size × grid scaling × colorbar space allocation
    figsize = figsize * fig_scale * cbar_scale
    fig = plt.figure(figsize=figsize, **fig_kwargs)

    # Extract axis sharing parameters from gs_kwargs with sensible defaults
    hspace = gs_kwargs.pop("hspace", 0)  # Minimal vertical spacing between subplots
    wspace = gs_kwargs.pop("wspace", 0)  # Minimal horizontal spacing between subplots
    sharex = gs_kwargs.pop("sharex", True)  # Share x-axis limits across subplots
    sharey = gs_kwargs.pop("sharey", True)  # Share y-axis limits across subplots

    # Create the master GridSpec with calculated ratios and spacing
    # GridSpec dimensions = colorbar + gap + main plot array
    gs = mpl.gridspec.GridSpec(
        len(height_ratios),  # Total rows including colorbar and gap
        len(width_ratios),  # Total columns including colorbar and gap
        hspace=hspace,
        wspace=wspace,
        height_ratios=height_ratios,
        width_ratios=width_ratios,
        **gs_kwargs,
    )

    # Define colorbar and main axes grid positions based on colorbar location
    # Each case sets up appropriate indexing ranges for the GridSpec
    if cbar_loc == "left":
        cax = gs[:, 0]  # Colorbar spans all rows, leftmost column
        col_range = range(2, ncols + 2)  # Main plots skip colorbar + gap columns
        row_range = range(nrows)  # Main plots use all rows
    elif cbar_loc == "right":
        cax = gs[:, -1]  # Colorbar spans all rows, rightmost column
        col_range = range(0, ncols)  # Main plots use leftmost columns
        row_range = range(nrows)  # Main plots use all rows
    elif cbar_loc == "top":
        cax = gs[0, :]  # Colorbar spans all columns, topmost row
        col_range = range(ncols)  # Main plots use all columns
        row_range = range(2, nrows + 2)  # Main plots skip colorbar + gap rows
    elif cbar_loc == "bottom":
        cax = gs[-1, :]  # Colorbar spans all columns, bottommost row
        col_range = range(ncols)  # Main plots use all columns
        row_range = range(0, nrows)  # Main plots use topmost rows
    else:
        raise ValueError(f"Invalid cbar_loc: {cbar_loc}")

    # Create the actual subplot objects using GridSpec indexing
    cax = fig.add_subplot(cax)  # Single colorbar axes
    # Create 2D array of main plotting axes matching requested grid shape
    axes = np.array([[fig.add_subplot(gs[i, j]) for j in col_range] for i in row_range])

    # Configure colorbar tick and label positioning based on location
    # Top and left locations require repositioning for proper visibility
    if cbar_loc == "top":
        cax.xaxis.set_ticks_position("top")  # Move ticks to top of colorbar
        cax.xaxis.set_label_position("top")  # Move labels to top of colorbar
    elif cbar_loc == "left":
        cax.yaxis.set_ticks_position("left")  # Move ticks to left of colorbar
        cax.yaxis.set_label_position("left")  # Move labels to left of colorbar

    # Apply axis sharing across the main plotting axes array
    # This ensures consistent parameter scales across all subplots
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
