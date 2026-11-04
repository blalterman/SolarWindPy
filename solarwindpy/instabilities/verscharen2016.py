#!/usr/bin/env python
"""Instability thresholds from Verscharen et al. (2016).

The empirical fits of :cite:`Verscharen2016a`
(`doi:10.3847/0004-637X/831/2/128 <https://doi.org/10.3847/0004-637X/831/2/128>`_)
are implemented to evaluate when a plasma becomes unstable in the
``(beta, R)`` plane.

References
----------
.. bibliography::
   :filter: False

   Verscharen2016a
"""

__all__ = [
    "insta_params",
    "beta_ani_inst",
    "StabilityCondition",
    "StabilityContours",
]

import logging

import numpy as np
import pandas as pd
import matplotlib as mpl

from collections import namedtuple

_inst_type_idx = pd.Index(["AIC", "FMW", "MM", "OFI"], name="Instability")
_param_idx = pd.Index(["a", "b", "c"], name="Fit Parameter")

#: Fit parameters ``a``, ``b`` and ``c`` of each instability threshold
#: (AIC, FMW, MM, OFI), indexed by growth rate as the exponent of
#: gamma / Omega_p = 10^-4, 10^-3 and 10^-2.
insta_params = pd.concat(
    {
        -4: pd.DataFrame(
            [
                [0.367, 0.364, 0.011],
                [-0.408, 0.529, 0.41],
                [0.702, 0.674, -0.009],
                [-1.454, 1.023, -0.178],
            ],
            index=_inst_type_idx,
            columns=_param_idx,
        ),
        -3: pd.DataFrame(
            [
                [0.437, 0.428, -0.003],
                [-0.497, 0.566, 0.543],
                [0.801, 0.763, -0.063],
                [-1.39, 1.005, -0.111],
            ],
            index=_inst_type_idx,
            columns=_param_idx,
        ),
        -2: pd.DataFrame(
            [
                [0.649, 0.4, 0.0],
                [-0.647, 0.583, 0.713],
                [1.04, 0.633, -0.012],
                [-1.447, 1.0, -0.148],
            ],
            index=_inst_type_idx,
            columns=_param_idx,
        ),
    },
    axis=1,
    names=["growth_rate"],
).stack("growth_rate", future_stack=True)

_plot_contour_kwargs = pd.DataFrame(
    [
        ["#ffcb05", "--", "X"],
        ["#00B2A9", "--", "d"],
        ["#00274c", "--", "o"],
        ["#D86018", "--", "P"],
        ["#ffcb05", ":", "X"],
        ["#00B2A9", ":", "d"],
        ["#00274c", ":", "o"],
        ["#D86018", ":", "P"],
        ["#ffcb05", "-.", "X"],
        ["#00B2A9", "-.", "d"],
        ["#00274c", "-.", "o"],
        ["#D86018", "-.", "P"],
    ],
    index=pd.MultiIndex.from_tuples(
        [
            (-4, "AIC"),
            (-4, "FMW"),
            (-4, "MM"),
            (-4, "OFI"),
            (-3, "AIC"),
            (-3, "FMW"),
            (-3, "MM"),
            (-3, "OFI"),
            (-2, "AIC"),
            (-2, "FMW"),
            (-2, "MM"),
            (-2, "OFI"),
        ],
        names=["growth_rate", "Instability"],
    ),
    columns=["color", "linestyle", "marker"],
)

_instability_tests = namedtuple("InstabilityTests", "AIC,MM,FMW,OFI")(
    np.greater, np.greater, np.less, np.less
)


def beta_ani_inst(beta, a=None, b=None, c=None):
    r"""Return the anisotropy threshold for a given beta.

    Implements Eq. (5) of :cite:`Verscharen2016a`:

    .. math::

       R_p = 1 + \frac{a}{(\beta_{\parallel,p} - c)^b}

    where $p$ is defined assuming only a single proton population is fit.

    Parameters
    ----------
    beta : array-like
        Parallel proton beta.
    a, b, c : float
        Fit parameters from Verscharen et al. (2016).

    Returns
    -------
    numpy.ndarray
        Threshold anisotropy values.

    Examples
    --------
    The A/IC threshold at gamma / Omega_p = 10^-4, Table 1 of
    :cite:`Verscharen2016a` (``insta_params`` row ``("AIC", -4)``). Beta
    below ``c`` has no threshold:

    >>> beta = np.logspace(-2, 2, 5)
    >>> beta_ani_inst(beta, a=0.367, b=0.364, c=0.011)
    array([       nan, 1.88529518, 1.36848059, 1.15879618, 1.06865678])
    """
    # Effectively, type checking.
    a = float(a)
    b = float(b)
    c = float(c)
    return 1 + (a / ((beta - c) ** b))


class StabilityCondition(object):
    """Evaluate plasma stability using the Verscharen et al. fits.

    Parameters
    ----------
    growth_rate : int
        Index of the growth-rate table to use (``-2``, ``-3`` or ``-4``).
    beta : pandas.Series
        Parallel proton beta.
    R : pandas.Series
        Temperature anisotropy.

    Attributes
    ----------
    instability_thresholds : pandas.DataFrame
        Threshold anisotropies for each instability.
    is_unstable : pandas.DataFrame
        Boolean mask indicating unstable modes.
    stability_bin : pandas.Series
        Integer label describing the dominant instability, named
        ``"Stability"``; the keys of ``stability_map``. A point outside
        every bin carries ``fill`` (-9999).

    Notes
    -----
    A missing value counts as stable. Where a threshold is undefined
    (beta at or below the fit offset ``c`` of Eq. (5), or beta missing) or
    the anisotropy is missing, the measurement is not unstable to that
    instability.
    """

    def __init__(self, growth_rate, beta, R):
        """Initialize the object.

        Parameters
        ----------
        growth_rate : int
            Growth rate index (``-2``, ``-3`` or ``-4``).
        beta, R : pandas.Series
            Arrays of parallel beta and temperature anisotropy.
        """
        self._init_logger()
        self.set_instability_parameters(growth_rate)
        self.set_beta_ani(beta, R)
        self.calculate_stability_criteria()

    def __str__(self):
        """Return the class name."""

        return self.__class__.__name__

    def _init_logger(self):
        """Initialize a logger namespaced to the class."""

        logger = logging.getLogger("{}.{}".format(__name__, self.__class__.__name__))
        self._logger = logger

    @property
    def fill(self):
        r"""Integer ``stability_bin`` label of a point outside every bin.

        ``stability_bin`` starts from it before each bin is assigned. It is
        not a key of ``stability_map``.
        """
        return -9999

    @property
    def instability_parameters(self):
        """The Pandas DataFrame of instability parameters."""

        return self._instability_parameters

    @property
    def data(self):
        """DataFrame with beta and anisotropy measurements."""

        return self._data

    @property
    def beta(self):
        """The beta values of the object."""

        return self.data.loc[:, "beta"]

    @property
    def R(self):
        """The anisotropy values of the object."""

        return self.data.loc[:, "R"]

    @property
    def stability_map(self):
        """The map of ints to strings identifying the instabilities."""

        return {
            4: "MM",
            3: "Between\nAIC &\nMM",
            2: "Stable",
            1: "Between\nFMW &\nOFI",
            0: "OFI",
        }

    @property
    def stability_map_inverse(self):
        """The inverse of ``stability_map``."""

        return {v: k for k, v in self.stability_map.items()}

    @property
    def instability_thresholds(self):
        """The value of the anisotropy for which the plasma goes unstable."""

        return self._instability_thresholds

    @property
    def instability_tests(self):
        """The tests used for each instability threshold.

        The keys are ``"AIC"``, ``"MM"``, ``"FMW"``, and ``"OFI"`` for
        Alfven/Ion-Cyclotron, Mirror Mode, Fast Magnetosonic / Whistler, and
        Oblique Firehose. The values are NumPy ufuncs.
        """

        return _instability_tests._asdict()

    @property
    def is_unstable(self):
        """Boolean DataFrame indicating instability to a given instability."""

        return self._is_unstable

    @property
    def stability_bin(self):
        """The integer corresponding to the (in)stability condition.

        A point outside every bin carries ``fill`` (-9999).
        """

        return self._stability_bin

    @property
    def cmap(self):
        """A linearly segmented colormap for the (in)stability condition."""

        return mpl.colormaps["Paired"].resampled(len(self.stability_map))

    @property
    # TODO: rename to `color_norm` for consistancy w/ plotting code.
    def norm(self):
        """The normalization instance used for plotting the stability bin."""

        # Change the normalization slightly so that the tick marks are
        # centered in their respective regions.

        # TODO: What about using a BoundaryNorm instead and setting
        # the boundaries at the mid points (avgs) between the stability_map
        # keys? (20161112_1505)
        min_norm = min(self.stability_map) - 0.5
        max_norm = max(self.stability_map) + 0.5

        return mpl.colors.Normalize(min_norm, max_norm)

    @property
    def cbar_kwargs(self):
        """Keyword arguments for drawing a colorbar."""

        cbar_formatter = mpl.pyplot.FuncFormatter(
            lambda val, loc: self.stability_map[val]
        )
        ticks = sorted(self.stability_map.keys())

        format_dict = dict(
            format=cbar_formatter,
            ticks=ticks,
            extend="neither",
            cmap=self.cmap,
            norm=self.norm,
        )

        return format_dict

    def set_instability_parameters(self, growth_rate):
        """Take the instability parameters corresponding to ``growth_rate``.

        Parameters
        ----------
        growth_rate : int
            Growth-rate index (``-2``, ``-3`` or ``-4``).
        """

        growth_rate = int(growth_rate)
        temp = insta_params.xs(growth_rate, axis=0, level="growth_rate")
        self._instability_parameters = temp

    def set_beta_ani(self, beta, R):
        """Set the beta and anisotropy values."""

        assert beta.shape == R.shape
        data = pd.concat({"beta": beta, "R": R}, axis=1)
        self._data = data

    def _calc_instability_thresholds(self):
        r"""Calculate the instability thresholds.

        This is a private method that should not be called. See
        :meth:`calculate_stability_criteria`.
        """
        instability_thresholds = {
            k: beta_ani_inst(self.beta, **v)
            for k, v in self.instability_parameters.iterrows()
        }
        instability_thresholds = pd.DataFrame.from_dict(instability_thresholds)
        instability_thresholds = instability_thresholds.sort_index(axis=1)
        self._instability_thresholds = instability_thresholds

    def _calc_is_unstable(self):
        r"""Determine if a measurement is unstable to each instability.

        This is a private method that should not be called. See
        :meth:`calculate_stability_criteria`.
        """
        is_unstable = {
            k: self.instability_tests[k](self.R, v)
            for k, v in self.instability_thresholds.items()
        }
        is_unstable = pd.concat(is_unstable, axis=1).sort_index(axis=1)

        # A missing value counts as stable: no comparison with a NaN threshold
        # or anisotropy holds.
        self._is_unstable = is_unstable.astype(bool)

    def _calc_stability_bin(self):
        r"""Identify which instability (if any) each measurement is unstable to.

        This is a private method that should not be called. See
        :meth:`calculate_stability_criteria`.
        """
        unstable = self.is_unstable
        between_AIC_MM = unstable.AIC & unstable.MM.pipe(np.logical_not)
        between_FMW_OFI = unstable.FMW & unstable.OFI.pipe(np.logical_not)
        stable = unstable.pipe(np.logical_not).all(axis=1)

        # Here, we use integer identifiers b/c they are more
        # computationally efficient to process.
        stability_bin = pd.Series(self.fill, index=unstable.index, name="Stability")

        map_inverse = self.stability_map_inverse
        stability_bin.mask(stable, map_inverse["Stable"], inplace=True)
        stability_bin.mask(
            between_AIC_MM, map_inverse["Between\nAIC &\nMM"], inplace=True
        )
        stability_bin.mask(unstable.MM, map_inverse["MM"], inplace=True)
        stability_bin.mask(
            between_FMW_OFI, map_inverse["Between\nFMW &\nOFI"], inplace=True
        )
        stability_bin.mask(unstable.OFI, map_inverse["OFI"], inplace=True)

        # Every row is now assigned: stable when no instability holds, and
        # otherwise AIC, MM, FMW or OFI each set one of the four other bins.
        self._stability_bin = stability_bin

    def calculate_stability_criteria(self):
        r"""Run the full instability calculation.

        This method calls ``_calc_instability_thresholds``,
        ``_calc_is_unstable``, and ``_calc_stability_bin`` in that
        order. Use this method over calling the private methods individually.
        """
        self._calc_instability_thresholds()
        self._calc_is_unstable()
        self._calc_stability_bin()


class StabilityContours(object):
    """Precompute and plot instability contours.

    Parameters
    ----------
    beta : numpy.ndarray
        Parallel proton beta values used for the contours.
    """

    def __init__(self, beta):
        self.set_beta(beta)
        self._calc_instability_contours()

    @property
    def beta(self):
        r"""Proton core parallel beta."""
        return self._beta

    def set_beta(self, new):
        assert isinstance(new, np.ndarray)
        self._beta = new

    def _calc_instability_contours(self):
        r"""Calculate instability contours.

        Because we can call the contours many times, but only need to calculate them
        once, move the calculation to a separate method.
        """
        contours = {
            k: beta_ani_inst(self.beta, **v) for k, v in insta_params.iterrows()
        }
        contours = pd.Series(contours).unstack(level=0)

        assert isinstance(contours, pd.DataFrame)
        self._contours = contours

    @property
    def contours(self):
        return self._contours

    def plot_contours(
        self, ax, fix_scale=True, growth_rate=None, tk_kind=None, **kwargs
    ):
        r"""Add the instability contours to the plot.

        Parameters
        ----------
        ax: mpl.axis
        fix_scale: bool
            If True, make x- and y-axes log scaled.
        growth_rate: None, -2, -3, -4
            If not None, plot only the contours of this growth rate.
        tk_kind: None, str, list-like of str
            Contours to plot. Valid options are "MM", "AIC", "FMW", "OFI",
            and any combination thereof.
        kwargs:
            Line styles passed to :meth:`matplotlib.axes.Axes.plot` for every
            contour, overriding the defaults; matplotlib aliases (``ms``,
            ``c``, ``ls``) are accepted. By default each contour has its own
            ``color``, ``linestyle`` and ``marker`` and is labelled with its
            instability, with ``markersize=10``, ``markeredgewidth=0.5``,
            ``markeredgecolor="k"`` and ``markevery=10``.

        Returns
        -------
        ax : matplotlib.axes.Axes
        lines : dict
            Maps each drawn ``(growth_rate, instability)`` pair, e.g.
            ``(-3, "MM")``, to its :class:`matplotlib.lines.Line2D`, in
            drawing order. Only the curves drawn are keys.
        cbar : None
            The contours are lines, not a mappable, so no colorbar is drawn;
            the slot keeps the return order ``(ax, artists..., cbar)``
            shared by every plot.
        """
        assert isinstance(ax, mpl.axes.Axes)

        images_for_table_legend = pd.DataFrame(
            index=self.contours.index, columns=self.contours.columns
        )

        kwargs = mpl.cbook.normalize_kwargs(kwargs, mpl.lines.Line2D)
        common_style = {
            "markersize": 10,
            "markeredgewidth": 0.5,
            "markeredgecolor": "k",
            "markevery": 10,
        }

        if tk_kind is not None:
            if isinstance(tk_kind, str):
                tk_kind = [tk_kind]
            if not np.all([isinstance(x, str) for x in tk_kind]):
                raise TypeError(f"""Unexpected types for `tk_kind` ({tk_kind})""")

            tk_kind = [x.upper() for x in tk_kind]
            if not np.all([x in self.contours.columns for x in tk_kind]):
                raise ValueError(f"""Unexpected values for `tk_kind` ({tk_kind})""")

        target_contours = self.contours
        if tk_kind is not None:
            target_contours = target_contours.loc[:, tk_kind]
        target_contours = target_contours.stack()
        lines = {}

        if growth_rate is not None:
            growth_rate = int(growth_rate)
            assert growth_rate in [-2, -3, -4], (
                "Unrecognized growth_rate: %s" % growth_rate
            )

        for k, v in target_contours.items():
            rate, itype = k

            if growth_rate is not None and rate != growth_rate:
                # Don't plot this growth rate.
                continue

            style = {
                **common_style,
                **_plot_contour_kwargs.loc[(rate, itype)].to_dict(),
                "label": itype,
                **kwargs,
            }
            im = ax.plot(self.beta, v, **style)
            # only want line object, not list of them. so im[0].
            images_for_table_legend.loc[rate, itype] = im[0]
            lines[(rate, itype)] = im[0]

        if fix_scale:
            ax.set_xscale("log")
            ax.set_yscale("log")

        if growth_rate is None:
            # Only need legend table if plotting all contours.
            self._add_table_legend(ax, images_for_table_legend)
        else:
            ax.legend(
                loc=1,
                title=r"$\gamma/\Omega_{p} = 10^{%s}$" % growth_rate,
                framealpha=0,
                ncol=2,
            )

        return ax, lines, None

    @staticmethod
    def _add_table_legend(ax, images):
        r"""Create a compact legend in table format identifying the contours.

        Modified from stackoverflow.
        Source: https://stackoverflow.com/a/25995730/1200989
        """
        assert isinstance(images, pd.DataFrame)

        # create blank rectangle
        extra = mpl.patches.Rectangle(
            (0, 0), 1, 1, fc="w", fill=False, edgecolor="none", linewidth=0
        )

        def handle(rate, itype):
            """The curve plotted for ``(rate, itype)``, or the blank cell."""
            image = images.loc[rate, itype]
            return extra if pd.isna(image) else image

        # Create organized list containing all handles for table.
        # Extra represent empty space, including the cell of an instability
        # not plotted, so the table keeps its layout. Within each column, handles follow
        # the row labels below: AIC, FMW, MM, OFI.
        legend_handles = [
            extra,
            extra,
            extra,
            extra,
            extra,
            extra,
            handle(-2, "AIC"),
            handle(-2, "FMW"),
            handle(-2, "MM"),
            handle(-2, "OFI"),
            extra,
            handle(-3, "AIC"),
            handle(-3, "FMW"),
            handle(-3, "MM"),
            handle(-3, "OFI"),
            extra,
            handle(-4, "AIC"),
            handle(-4, "FMW"),
            handle(-4, "MM"),
            handle(-4, "OFI"),
        ]

        # Define the labels
        label_rows = [
            r"",
            r"$\mathrm{AIC}$",
            r"$\mathrm{FMW}$",
            r"$\mathrm{MM}$",
            r"$\mathrm{OFI}$",
        ]
        label_col_0 = [r"$-2$"]
        label_col_1 = [r"$-3$"]
        label_col_2 = [r"$-4$"]
        label_empty = [""]

        # organize labels for table construction
        legend_labels = (
            label_rows
            + label_col_0
            + label_empty * 4
            + label_col_1
            + label_empty * 4
            + label_col_2
            + label_empty * 4
        )

        # Create legend
        ax.legend(
            legend_handles,
            legend_labels,
            loc=1,
            ncol=4,
            shadow=True,
            handletextpad=-2,
            framealpha=0.75,
        )
