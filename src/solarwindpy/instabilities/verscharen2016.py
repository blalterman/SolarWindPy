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


import numpy as np
import pandas as pd
import matplotlib as mpl

from collections import namedtuple

from ..plotting.base import Guides

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

#: Growth rates of Table 1, in display order: -2, -3, -4.
_growth_rates = [
    int(r) for r in sorted(insta_params.index.unique("growth_rate"), reverse=True)
]

#: Contour colour and marker of each instability.
_instability_styles = pd.DataFrame(
    {
        "color": ["#ffcb05", "#00B2A9", "#00274c", "#D86018"],
        "marker": ["X", "d", "o", "P"],
    },
    index=_inst_type_idx,
)

#: Contour linestyle of each growth rate.
_growth_rate_linestyles = pd.Series(
    {-4: "--", -3: ":", -2: "-."}, name="linestyle"
).rename_axis("growth_rate")

#: Default style of each (growth_rate, instability) contour.
_plot_contour_kwargs = pd.DataFrame(
    [
        [style.color, linestyle, style.marker]
        for linestyle in _growth_rate_linestyles
        for style in _instability_styles.itertuples()
    ],
    index=pd.MultiIndex.from_product(
        [_growth_rate_linestyles.index, _inst_type_idx],
        names=["growth_rate", "Instability"],
    ),
    columns=["color", "linestyle", "marker"],
)

_instability_tests = namedtuple("InstabilityTests", "AIC,FMW,MM,OFI")(
    np.greater, np.less, np.greater, np.less
)

#: Integer of each stability bin, by short name.
_stability_bins = {"MM": 4, "AIC_MM": 3, "stable": 2, "FMW_OFI": 1, "OFI": 0}

#: Colorbar label of each stability bin, by short name.
_stability_labels = {
    "MM": "MM",
    "AIC_MM": "Between\nAIC &\nMM",
    "stable": "Stable",
    "FMW_OFI": "Between\nFMW &\nOFI",
    "OFI": "OFI",
}


def beta_ani_inst(beta, a, b, c):
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
    r"""Evaluate plasma stability using the Verscharen et al. fits.

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
        ``"Stability"``; the keys of ``stability_map``. Every point carries
        one.

    Notes
    -----
    A missing value counts as stable. Where a threshold is undefined
    (beta at or below the fit offset ``c`` of Eq. (5), or beta missing) or
    the anisotropy is missing, the measurement is not unstable to that
    instability.

    Examples
    --------
    Four measurements at the same beta and increasing anisotropy, tested
    against the thresholds for gamma / Omega_p = 10^-3:

    >>> import pandas as pd
    >>> beta = pd.Series([1.0, 1.0, 1.0, 1.0])
    >>> R = pd.Series([0.2, 1.0, 1.5, 3.0])
    >>> sc = StabilityCondition(-3, beta, R)
    >>> sc.instability_thresholds.loc[0].round(3).to_dict()
    {'AIC': 1.436, 'FMW': 0.226, 'MM': 1.765, 'OFI': -0.25}
    >>> sc.stability_bin.tolist()
    [1, 2, 3, 4]
    >>> [sc.stability_map[k].replace("\n", " ") for k in sc.stability_bin]
    ['Between FMW & OFI', 'Stable', 'Between AIC & MM', 'MM']
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
        self.set_instability_parameters(growth_rate)
        self.set_beta_ani(beta, R)
        self.calculate_stability_criteria()

    def __str__(self):
        """Return the class name."""

        return self.__class__.__name__

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

        return {_stability_bins[k]: label for k, label in _stability_labels.items()}

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

        A key of ``stability_map`` for every point.
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
        """Set the beta and anisotropy values.

        Parameters
        ----------
        beta : pandas.Series
            Parallel proton beta.
        R : pandas.Series
            Temperature anisotropy, with the same shape as ``beta``.

        Raises
        ------
        ValueError
            If ``beta`` and ``R`` differ in shape.
        """

        if beta.shape != R.shape:
            raise ValueError(
                f"beta and R must have the same shape, not {beta.shape} and {R.shape}"
            )
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

        # Here, we use integer identifiers b/c they are more
        # computationally efficient to process.
        bins = _stability_bins
        stability_bin = pd.Series(
            bins["stable"], index=unstable.index, name="Stability"
        )
        stability_bin.mask(between_AIC_MM, bins["AIC_MM"], inplace=True)
        stability_bin.mask(unstable.MM, bins["MM"], inplace=True)
        stability_bin.mask(between_FMW_OFI, bins["FMW_OFI"], inplace=True)
        stability_bin.mask(unstable.OFI, bins["OFI"], inplace=True)

        # ``is_unstable`` is boolean, so a row is stable exactly when none of
        # the masks above holds, and every row carries a stability_map key.
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

    Examples
    --------
    >>> import numpy as np
    >>> import matplotlib.pyplot as plt
    >>> contours = StabilityContours(np.logspace(0, 1, 3))
    >>> contours.contours.shape
    (3, 4)
    >>> contours.contours.loc[-3, "AIC"].round(3)
    array([1.436, 1.267, 1.163])
    >>> fig, ax = plt.subplots()
    >>> ax, lines, guides = contours.plot_contours(ax, growth_rate=-3)
    >>> sorted(lines)
    [(-3, 'AIC'), (-3, 'FMW'), (-3, 'MM'), (-3, 'OFI')]
    >>> plt.close("all")
    """

    def __init__(self, beta):
        self.set_beta(beta)
        self._calc_instability_contours()

    @property
    def beta(self):
        r"""Proton core parallel beta."""
        return self._beta

    def set_beta(self, new):
        r"""Set :attr:`beta`.

        Parameters
        ----------
        new : numpy.ndarray
            Parallel proton beta values at which to evaluate the contours.

        Raises
        ------
        TypeError
            If ``new`` is not a :class:`numpy.ndarray`.
        """
        if not isinstance(new, np.ndarray):
            raise TypeError(f"beta must be a numpy.ndarray, not {type(new).__name__}")
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
        r"""Threshold anisotropy of each instability at every :attr:`beta`.

        A :class:`pandas.DataFrame` indexed by growth rate (``-4``, ``-3``,
        ``-2``) with one column per instability (``AIC``, ``FMW``, ``MM``,
        ``OFI``); each cell is the :func:`beta_ani_inst` array evaluated at
        :attr:`beta` with that row's ``insta_params``.
        """
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
        guides : Guides
            Every field None: the contours are lines, not a mappable, so no
            colorbar is drawn. The slot keeps the return order
            ``(ax, artists..., guides)`` shared by every plot.

        Raises
        ------
        TypeError
            If ``ax`` is not a :class:`matplotlib.axes.Axes`, or ``tk_kind``
            holds an entry that is not a string.
        ValueError
            If ``growth_rate`` is not None or one of the Table 1 rates
            (-2, -3, -4), naming them, or ``tk_kind`` names an unknown
            instability.
        """
        if not isinstance(ax, mpl.axes.Axes):
            raise TypeError(
                f"ax must be a matplotlib.axes.Axes, not {type(ax).__name__}"
            )

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
            if growth_rate not in _growth_rates:
                raise ValueError(
                    f"growth_rate must be None or one of {_growth_rates}; "
                    f"got {growth_rate}"
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

        return ax, lines, Guides()

    @staticmethod
    def _add_table_legend(ax, images):
        r"""Draw a legend on ``ax`` laid out as a table of instability contours.

        The legend has five rows and four columns. The first column is a row
        header naming the instability type (AIC, FMW, MM, OFI). The remaining
        columns hold growth-rate exponents -2, -3, and -4, each headed by its
        exponent. Each body cell shows the handle for that (exponent, type)
        pair, or an invisible placeholder when the pair is missing, so the
        grid stays aligned.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            Axes on which to draw the legend.
        images : pandas.DataFrame
            Legend handles indexed by growth-rate exponent (-2, -3, -4) with
            columns for instability type ("AIC", "FMW", "MM", "OFI"). Missing
            cells hold NaN or None.
        """
        assert isinstance(images, pd.DataFrame)

        def placeholder():
            return mpl.patches.Rectangle(
                (0, 0), 1, 1, fill=False, edgecolor="none", linewidth=0
            )

        types = list(_inst_type_idx)
        rates = _growth_rates

        # Matplotlib fills multi-column legends column by column, so entries
        # are listed one table column at a time, top to bottom.
        handles = []
        labels = []

        handles.append(placeholder())
        labels.append("")
        for t in types:
            handles.append(placeholder())
            labels.append(r"$\mathrm{%s}$" % t)

        for rate in rates:
            handles.append(placeholder())
            labels.append(r"$%s$" % rate)
            for t in types:
                h = images.loc[rate, t]
                if h is None or (not isinstance(h, mpl.artist.Artist) and pd.isna(h)):
                    h = placeholder()
                handles.append(h)
                labels.append("")

        ax.legend(
            handles,
            labels,
            loc=1,
            ncol=4,
            shadow=True,
            handletextpad=-2,
            framealpha=0.75,
        )
