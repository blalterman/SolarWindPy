#!/usr/bin/env python
r"""

The following parameters come from:

[1] Verscharen, D., Chandran, B. D. G., Klein, K. G. & Quataert, E.
    Collisionless Isotropization of the Solar-Wind Protons By Compressive
    Fluctuations and Plasma Instabilities. Astrophys. J. 831, 128 (2016).

for which the Bibtex entry is:

    @article{Verscharen2016a,
    author = {Verscharen, D. and Chandran, Benjamin D. G. and Klein, K. G.
    and Quataert, Eliot},
    doi = {10.3847/0004-637X/831/2/128},
    issn = {1538-4357},
    journal = {Astrophys. J.},
    keywords = {accretion,accretion disks,accretion, accretion
    disks,animation,instabilities,plasmas,solar wind,supporting
    material,turbulence,waves},
    number = {2},
    pages = {128},
    publisher = {IOP Publishing},
    title = {{Collisionless Isotropization of the Solar-Wind Protons By
    Compressive Fluctuations and Plasma Instabilities}},
    url = {http://stacks.iop.org/0004-637X/831/i=2/a=128?key=crossref.765015074c72580bac87603b196556a0},
    volume = {831},
    year = {2016}
    }
"""

import pdb  # noqa: F401
import logging

import numpy as np
import pandas as pd
import matplotlib as mpl

from collections import namedtuple
from matplotlib import pyplot as plt

_inst_type_idx = pd.Index(["AIC", "FMW", "MM", "OFI"], name="Intability")
_param_idx = pd.Index(["a", "b", "c"], name="Fit Parameter")

_inst_type_idx = pd.Index(["AIC", "FMW", "MM", "OFI"], name="Intability")
_param_idx = pd.Index(["a", "b", "c"], name="Fit Parameter")

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
    names=["Growth Rate"],
).stack("Growth Rate")

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
        names=["Growth Rate", "Instability"],
    ),
    columns=["color", "linestyle", "marker"],
)

_instability_tests = namedtuple("InstabilityTests", "AIC,MM,FMW,OFI")(
    np.greater, np.greater, np.less, np.less
)


def beta_ani_inst(beta, a=None, b=None, c=None):
    r"""Constant growth rate isocontours from Eq. (5) in [1].

        $R_p = 1 + \frac{a}{(\beta_{\parallel,p} - c)^b}$

    where $p$ is defined assuming only a single proton population is fit.

    `a`, `b`, and `c` are kwargs so that **kwarg expansion works.
    """
    # Effectively, type checking.
    a = float(a)
    b = float(b)
    c = float(c)
    return 1 + (a / ((beta - c) ** b))


class StabilityCondition(object):
    r"""
    Determines the stability condition of a plasma based on it"s location in
    the (beta, anisotropy) plane.

    Call signature
    --------------

        StabilityCondition(growth_rate, beta, anisotropy, fill=-9999)

    Methods
    -------
    set_instability_parameters:
        Take the instability parameters corresponding to the passed growth rate.
    set_beta_ani:
        Set the be    set_fill :
        Set the fill value.ta and anistropy values.
    _calc_instability_thresholds:
        Calculate the instability thresholds. This is a private method that
        should not be called. See `calculate_stability_criteria`.
    _calc_is_unstable:
        Determine if a measurement is unstable to each instability. This is a
        private method that should not be called. See
        `calculate_stability_criteria`.
    _calc_stability_bin:
        Identify which instability (if any) each measurement is unstale to.
        This is a private method that should not be called. See
        `calculate_stability_criteria`.
    calculate_stability_criteria:
        Run `_calc_instability_thresholds`, `_calc_is_unstable`, and
        `_calc_stability_bin` in that order. Use this method over the others
        individually.

    Properties
    ----------
    instability_parameters:
        The Pandas DataFrame of instability parameters.
    beta:
        The beta values of the object.
    anisotropy:
        The anisotropy values of the object.
    stability_map: dict
        The map of ints to strings identifying the instabilities.
    stability_map_inverse: dict
        The inverse of `stability_map`.
    instability_tests: dict
        The tests used for each instability threshold. The keys are "AIC", "MM",
        "FMW", and "OFI" for Alfven/Ion-Cyclotron, Mirror Mode, Fast
        Magnetosonic / Whistler, and Oblique Firehose. The values are numpy
        ufuncs.
    instability_thresholds: pd.DataFrame
        The value of the anisotropy for which the plasma goes unstable.
    is_unstable: pd.DataFrame
        Boolean DataFrame indicating if a measurement is unstable to a given
        instability.
    stability_bin: pd.Series
        The integer corresponding to the (in)stability condition of the
        measurement. The string identifying the instability is given by the
        `stability_map`.
    norm: mpl.colors.Normalize(min(stability_map), max(stability_map))
        The normalization instance used for plotting the stability bin.
    cmap: matplotlib colormap
        A linearly segmented to have one level for each (in)stability condition.
    """

    def __init__(self, growth_rate, beta, anisotropy):
        r"""
        growth_rate: int
            Should correspond the the growth rate minor_axis index of the
            `insta_params` Pandas.Panel in the containing module. Unless something
            has changed, these where [-2, -3, -4] when the class was written.
        beta, anisotropy: pd.Series
            The 1D array-like objects containing the beta and anisotropy
            measurements.
        """
        self._init_logger()
        self.set_instability_parameters(growth_rate)
        self.set_beta_ani(beta, anisotropy)
        self.calculate_stability_criteria()

    def __str__(self):
        return self.__class__.__name__

    def _init_logger(self):
        logger = logging.getLogger("{}.{}".format(__name__, self.__class__.__name__))
        self._logger = logger

    @property
    def fill(self):
        r"""Used for building data containers and checking that all entries are visited.
        """
        return -9999.0

    @property
    def instability_parameters(self):
        return self._instability_parameters

    @property
    def data(self):
        return self._data

    @property
    def beta(self):
        return self.data.loc[:, "beta"]

    @property
    def anisotropy(self):
        return self.data.loc[:, "anisotropy"]

    @property
    def stability_map(self):
        return {
            4: "MM",
            3: "Between\nAIC &\nMM",
            2: "Stable",
            1: "Between\nFMW &\nOFI",
            0: "OFI",
        }

    @property
    def stability_map_inverse(self):
        return {v: k for k, v in self.stability_map.items()}

    @property
    def instability_thresholds(self):
        return self._instability_thresholds

    @property
    def instability_tests(self):
        return _instability_tests._asdict()

    @property
    def is_unstable(self):
        return self._is_unstable

    @property
    def stability_bin(self):
        return self._stability_bin

    @property
    def cmap(self):
        return plt.cm.get_cmap("Paired", len(self.stability_map))

    @property
    # TODO: rename to `color_norm` for consistancy w/ plotting code.
    def norm(self):

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
        growth_rate = int(growth_rate)
        temp = insta_params.xs(growth_rate, axis=0, level="Growth Rate")
        self._instability_parameters = temp

    def set_beta_ani(self, beta, anisotropy):
        assert beta.shape == anisotropy.shape
        data = pd.concat({"beta": beta, "anisotropy": anisotropy}, axis=1)
        self._data = data

    def _calc_instability_thresholds(self):
        r"""Calculate the beta for which a given anisotropy is unstable.
        """
        instability_thresholds = {
            k: beta_ani_inst(self.beta, **v)
            for k, v in self.instability_parameters.iterrows()
        }
        instability_thresholds = pd.DataFrame.from_dict(instability_thresholds)
        instability_thresholds = instability_thresholds.sort_index(axis=1)
        self._instability_thresholds = instability_thresholds

    def _calc_is_unstable(self):
        r"""Calculate if the plasma is unstable to a given mode for the `growth_rate`.
        """
        is_unstable = {
            k: self.instability_tests[k](self.anisotropy, v)
            for k, v in self.instability_thresholds.iteritems()
        }
        is_unstable = pd.concat(is_unstable, axis=1).sort_index(axis=1)

        # If the value is NaN in `instability_thresholds`, the comparison
        # returns False. We want to propagate it so that we can check the
        # other instabilities.
        is_unstable.mask(self.instability_thresholds.isnull(), inplace=True)

        # When an instability is NaN, we have to check the other instabilities.
        for key, column in is_unstable.iteritems():

            # Temporarily replace the NaNs here with False because NaNs don"t
            # qualify as unstable on their own. We make the replacement here
            # and not earlier because we are relying on those NaNs to indicate
            # the spectra we must actually check against the other
            # instabilities.
            others = is_unstable.drop(key, axis=1)
            others = others.replace(np.nan, False).all(axis=1)
            column = column.mask(column.isnull(), others).astype(bool)

            is_unstable.loc[:, key] = column

        if is_unstable.isnull().any().any():
            msg = "Did you visit every data point? " "It looks like you missed %s."
            msg = msg % (not is_unstable.isnull()).sum()
            raise ValueError(msg)

        self._is_unstable = is_unstable

    def _calc_stability_bin(self):
        r"""Using the results of `self._calc_instability_threshold` and `self._calc_is_unstable`,
        determine the category each spectrum belongs in:
            MM, between_AIC_MM, Stable, between_FMW_OFI, OFI
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

        if (stability_bin == self.fill).any():
            msg = "Did you visit every data point? " "It looks like you missed %s."
            msg = msg % (stability_bin == self.fill).sum()
            raise ValueError(msg)

        self._stability_bin = stability_bin

    def calculate_stability_criteria(self):
        r"""
        Run the full instability calculation.

        N.B. This function was written to collect all steps. The steps are broken into:

            1)  `_calc_instability_thresholds` calculates each stability
                threshold in anisotropy given beta.
            2)  `_calc_is_unstable` determines if the plasma is unstable to (1).
            3)  `_calc_stability_bin` categorize the instabilities according to
                the `stability_map`.

        so that we can refactor or expand functionality later should that be desired.

        Also, while one could call the `.stability_bin` property to automatically calculate the different steps,
        that function doesn"t force recalculation if we have, for example, changed the growth rate.
        """
        self._calc_instability_thresholds()
        self._calc_is_unstable()
        self._calc_stability_bin()


class StabilityContours(object):
    r"""
    Calculate stability contours in the (beta, Rt) plane with a simple
    API to add them to a matplotlib plot axis.

    Parameters
    ----------
    describe inputs

    Methods
    -------
    describe methods

    See Also
    --------
    what else should I look at?

    Notes
    -----
    -last test :
    -pass?
        --condition:
            -version  :
            -location :
        --failure:
    -Development history:
        -Started class. (20170530 1630)
    --major challenges:

    Proposed updates
    ----------------
    -Add beta limits for the range of parameters from the Verscharen2016a
     fits. (20170530 1631)

    Do not try
    ----------

    """

    def __init__(self, beta):
        self.set_beta(beta)
        self._calc_instability_contours()

    @property
    def beta(self):
        r"""
        Proton core parallel beta.
        """
        return self._beta

    def set_beta(self, new):
        assert isinstance(new, np.ndarray)
        self._beta = new

    def _calc_instability_contours(self):
        r"""
        Because we can call the contours many times, but only
        need to calculate them once, move the calculation to
        a separate method.
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
        self, ax, fix_scale=True, plot_gamma=None, tk_kind=None, **kwargs
    ):
        r"""
        Add the instability contours to the plot.

        Parameters
        ----------
        ax: mpl.axis
        fix_scale: bool
            If True, make x- and y-axes log scaled.
        plot_gamma: None, -2, -3, -4
            If not None, the instability parameter to plot.
        tk_kind: None, str, list-like of str
            Contours to plot. Valid options are "MM", "AIC", "FMW", "OFI",
            and any combination thereof.
        """
        assert isinstance(ax, mpl.axes.Axes)

        images_for_table_legend = pd.DataFrame(
            index=self.contours.index, columns=self.contours.columns
        )

        kwargs = mpl.cbook.normalize_kwargs(kwargs, mpl.lines.Line2D._alias_map)
        ms = kwargs.pop("markersize", 10)
        mew = kwargs.pop("markeredgewidth", 0.5)
        mec = kwargs.pop("markeredgecolor", "k")
        markevery = kwargs.pop("markevery", 10)

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

        for k, v in target_contours.iteritems():
            gamma, itype = k

            if plot_gamma is not None:
                plot_gamma = int(plot_gamma)
                assert plot_gamma in [-2, -3, -4], "Unrecognized gamma: %s" % plot_gamma
                if gamma != plot_gamma:
                    # Don't plot this gamma.
                    continue

            plot_kwargs = _plot_contour_kwargs.loc[gamma, itype]
            if gamma is not None:
                plot_kwargs["label"] = itype
            im = ax.plot(
                self.beta,
                v,
                # label=k,
                markevery=markevery,
                ms=ms,
                mew=mew,
                mec=mec,
                **plot_kwargs,
                **kwargs,
            )
            # only want line object, not list of them. so im[0].
            images_for_table_legend.loc[gamma, itype] = im[0]

        if fix_scale:
            ax.set_xscale("log")
            ax.set_yscale("log")

        if plot_gamma is None:
            # Only need legend table if plotting all contours.
            self._add_table_legend(ax, images_for_table_legend)
        else:
            ax.legend(
                loc=1,
                title=r"$\gamma/\Omega_{p} = 10^{%s}$" % plot_gamma,
                framealpha=0,
                ncol=2,
            )

    @staticmethod
    def _add_table_legend(ax, images):
        r"""
        Create a legend in compact table format for identifying the
        instability contours.

        Modified from stackoverflow.
        Source: https://stackoverflow.com/a/25995730/1200989
        """
        assert isinstance(images, pd.DataFrame)
        #         assert images.shape == _plot_contour_kwargs.shape

        # create blank rectangle
        extra = mpl.patches.Rectangle(
            (0, 0), 1, 1, fc="w", fill=False, edgecolor="none", linewidth=0
        )

        # Create organized list containing all handles for table.
        # Extra represent empty space
        legend_handles = [
            extra,
            extra,
            extra,
            extra,
            extra,
            extra,
            images.loc[-2, "MM"],
            images.loc[-2, "AIC"],
            images.loc[-2, "FMW"],
            images.loc[-2, "OFI"],
            extra,
            images.loc[-3, "MM"],
            images.loc[-3, "AIC"],
            images.loc[-3, "FMW"],
            images.loc[-3, "OFI"],
            extra,
            images.loc[-4, "MM"],
            images.loc[-4, "AIC"],
            images.loc[-4, "FMW"],
            images.loc[-4, "OFI"],
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

        # plt.show()


# if __name__ == "__main__":
#     import unittest
#     unittest.runner
