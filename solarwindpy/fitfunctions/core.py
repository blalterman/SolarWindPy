#!/usr/bin/env python
r""":py:mod:`~solarwindpy.fitfunctions` base class.

A `FitFunction` takes a function, generates a fit with `scipy.curve_fit`, and provides
tools for plotting that fit. It also provies tools for annotating the plot with
well-formatted LaTeX that describes the fit.
"""

import pdb  # noqa: F401
import logging  # noqa: F401
import re
import numpy as np
import matplotlib as mpl

from abc import ABC, abstractproperty
from matplotlib import pyplot as plt
from inspect import getargspec
from scipy.optimize import curve_fit


# Compile this once on import to save time.
_remove_exponential_pattern = r"e\+00+"  # Replace the `e+00`for 2 or more zeros.
_remove_exponential_pattern = re.compile(_remove_exponential_pattern)


class FitFunction(ABC):
    r"""

    Assuming that you don't want any special formatting, the typical call order
    is:
        fit_function = FitFunction(function, TeX_string)
        fit_function.make_fit(xobs, yobs)
        fit_function.TeX_parameters()
        fit_function.pretty_result()

    Instances are callable.
    """
    # TODO
    # Setup the verbose and debugging options.
    # Do we need to rename PlasmaPlotBase to PlasmaBase and inherit it?
    def __init__(
        self,
        xobs,
        yobs,
        xmin=None,
        xmax=None,
        ymin=None,
        ymax=None,
        weights=None,
        wmin=None,
        wmax=None,
    ):

        #         self._init_logger()
        self._set_argnames()
        self._set_raw_obs(xobs, yobs, weights)

        if weights is None:
            assert wmin is None
            assert wmax is None

        self.set_fit_obs(
            xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax, wmin=wmin, wmax=wmax
        )

    def __str__(self):
        return self.__class__.__name__

    def __call__(self, x):

        # TODO
        # Do you want to have this function accept optional kwarg parameters?
        # It adds a layer of complexity, but could be helfpul.

        # Sort the parameter keywords into the proper order to pass to the
        # numerical function.
        popt_ = self.popt
        popt_ = [popt_[k] for k in self.argnames]

        # NOTE
        # An instance of FitFunction is for a given function. To change the
        # function itself, a new instance of FitFunction should be required.
        # Therefore, we access the function directly.
        y = self.function(x, *popt_)
        return y

    @abstractproperty
    def function(self):
        r"""Get the function that`curve_fit` fits.

        The function is set at instantiation. It doesn't make sense to change
        it unless you redefine the entire FitFunction, so there is no `new`
        kwarg.
        """
        pass

    @abstractproperty
    def p0(self):
        r"""
        The initial guess for the FitFunction.
        """
        pass

    @abstractproperty
    def TeX_function(self):
        r"""Function written in LaTeX.
        """
        pass

    #     @property
    #     def logger(self):
    #         return self._logger

    @property
    def popt(self):
        r"""Optimized fit parameters.
        """
        return dict(self._popt)

    @property
    def psigma(self):
        return dict(self._psigma)

    @property
    def pcov(self):
        # Return a copy to protect the values.
        return self._pcov.copy()

    @property
    def sufficient_data(self):
        r"""
        A check to ensure that we can fit the data before doing any
        computations.
        """
        chk = self.tk_observed.sum() >= len(self.argnames)
        if not chk:
            msg = "There is insufficient data to fit the model."
            raise ValueError(msg)
        else:
            return True

    @property
    def argnames(self):
        r"""
        The names of the actual function arguments pulled by getargspec.
        """
        return self._argnames

    @property
    def xobs_raw(self):
        r"""Independent values for the fit, not accounting for extrema, finite data, etc.
        """
        return self._xobs_raw

    @property
    def yobs_raw(self):
        r"""Dependent values for the fit, not accounting for extrema, finite data, etc.
        """
        return self._yobs_raw

    @property
    def weights_raw(self):
        r"""Weights used by `curve_fit`, not including extrema, finite data, etc.
        """
        return self._weights_raw

    @property
    def xobs(self):
        r"""x-values, accounting for extrema, finite data, etc.

        These are the values actually fit.
        """
        return self._xobs

    @property
    def yobs(self):
        r"""y-values, accounting for extrema, finite data, etc.

        These are the values actually fit.
        """
        return self._yobs

    @property
    def weights(self):
        r"""
        The weights, having accounted for xlim, ylim, and wlim.
        """
        return self._weights

    @property
    def tk_observed(self):
        r"""The mask used to take the observed data from the raw data.
        """
        return self._tk_observed

    # @property
    # def binsigma_raw(self):
    #     r"""
    #     The std of the data in each bin, not accounting for the extrema
    #     limits.
    #     """
    #     try:
    #         return self._binsigma_raw
    #     except AttributeError:
    #         msg = "Please set binsigma."
    #         raise AttributeError(msg)

    @property
    def binsigma(self):
        r"""
        The std of the data in each bin.

        Only used for the bins meeting the extrema conditions.
        """
        return self._binsigma

    @property
    def chisqdof(self):
        r"""Calculate the chisq/dof for the fit.
        """
        yvals = self.yobs
        yfits = self(self.xobs)
        binsigma = self.binsigma

        # Assign the 0 counts that become negative with -1 to 0.
        # binsigma[~yvals.astype(bool)] = 0

        msg = "Not finite: %s"
        assert np.isfinite(yvals).all(), msg % (~np.isfinite(yvals)).sum()
        assert np.isfinite(yfits).all(), msg % (~np.isfinite(yfits)).sum()
        assert np.isfinite(binsigma).all(), msg % (~np.isfinite(binsigma)).sum()

        chisq = ((yvals - yfits) / binsigma) ** 2.0
        ddof = len(yvals) - len(self.p0) - 1
        chisqdof = chisq.sum() / ddof

        return chisqdof

    @property
    def TeX_chisqdof(self):
        r"""Chisqdof to two decimal places, chosen arbitrarily.
        """
        out = r"\chi^2_\nu = {:.2f}".format(self.chisqdof)
        return out

    @property
    def label(self):
        r"""The label for use when plotting.
        """
        # TODO: What is this? How do I use it?
        return self.function.func_name.title()

    @property
    def TeX_argnames(self):
        try:
            # Saved as tuple, so convert from tuple.
            out = self._TeX_argnames
            out = dict(out)
            return out

        except AttributeError:
            return None

    @property
    def TeX_popt(self):
        r"""Create a dictionary with (k, v) pairs corresponding to
        (self.argnames, popt \pm psigma) with the appropriate uncertainty.

        See `set_TeX_trans_argnames` to translate the argnames for TeX.
        """
        psigma = self.psigma
        popt = self.popt.items()
        TeX_popt = {k: self.val_uncert_2_string(v, psigma[k]) for k, v in popt}

        translate = self.TeX_argnames
        if translate is not None:
            for k0, k1 in translate.items():
                TeX_popt[k1] = TeX_popt[k0]
                del TeX_popt[k0]

        return TeX_popt

    @staticmethod
    def _check_and_add_math_escapes(x):
        r"""
        Add "$" math escapes to a string.

        This function can probably be turned into a
        static method.
        """
        assert isinstance(x, str)
        if not x.count("$"):
            x = r"$%s$" % x

        if x.count("$") % 2:
            msg = (
                "An even number of math escapes are necessary."
                " You have %s" % x.count("$")
            )
            raise ValueError(msg)

        return x

    @staticmethod
    def _calc_precision(value):
        r"""Primarily for use with the `val_uncert_2_string` and other methods that may
        require this.
        """
        # assert 1 > value > 0, \
        #     "Only written to deal with 0 < X < 1 numbers.\nX = %s" % value

        # Convert the fractional part to an exponential string.
        # E.g. 0.0009865 -> 9.865000e-04
        precision = "%e" % value  # (value - int(value))

        # Split the exponential notation at the `e`,  a la
        # "1.250000e-04"; take the exponent "4", excluding the sign.
        precision = int(precision.partition("e")[2])

        return precision

    @staticmethod
    def _check_raw_obs(arr, name):
        if not isinstance(arr, np.ndarray):
            try:
                arr = arr.values
            except AttributeError:
                msg = r"Can't set %s_raw with a `%s`." % (name, type(arr))
                raise TypeError(msg)

        arr = arr.squeeze()

        return arr

    def _set_raw_obs(self, xobs, yobs, weights=None):
        r"""
        Set the raw x- and y-values along with weights for the fit.

        Doesn't account for extrema, finite data, etc.
        """
        if xobs.shape != yobs.shape:
            msg = (
                "xobs and yobs must have the same shape.",
                "xobs: {}".format(xobs.shape),
                "yobs: {}".format(yobs.shape),
            )
            msg = "\n".join(msg)
            raise ValueError(msg)

        if weights is not None and weights.shape != xobs.shape:
            msg = (
                "weights and xobs must have the same shape.",
                "weighs: {}".format(weights.shape),
                "xobs: {}".format(xobs.shape),
            )
            msg = "\n".join(msg)
            raise ValueError(msg)

        xobs = self._check_raw_obs(xobs, "xobs")
        yobs = self._check_raw_obs(yobs, "obs")
        if weights is not None:
            weights = self._check_raw_obs(weights, "weights")

        self._xobs_raw = xobs
        self._yobs_raw = yobs
        self._weights_raw = weights

    def _build_one_obs_mask(self, axis, x, xmin, xmax):
        mask = np.full_like(x, True, dtype=bool)

        mask = np.isfinite(x)
        #         if not mask.all():
        #             self.logger.warning(
        #                 "{} {} observations are NaN. This {:.3%} of the data has been dropped.".format(
        #                     (~mask).sum(), axis, (~mask).mean()
        #                 )
        #             )

        if xmin is not None:
            xmin_mask = x >= xmin
            mask = mask & xmin_mask

        if xmax is not None:
            xmax_mask = x <= xmax
            mask = mask & xmax_mask

        return mask

    #     def _init_logger(self):
    #         self._logger = logging.getLogger(
    #             "{}.{}".format(__file__, self.__class__.__name__)
    #         )

    def _set_argnames(self):
        r"""
        Set the arguments of the function, assuming that the first
        is dependent variable.

        Should be called after function is set.
        """
        args = getargspec(self.function).args[1:]
        self._argnames = args

    def set_fit_obs(
        self, xmin=None, xmax=None, ymin=None, ymax=None, wmin=None, wmax=None
    ):
        r"""
        Set the observed values we'll actually use in the fit by applying limits
        to xobs_raw and yobs_raw and checking for finite values.

        All boundaries are inclusive <= or >=.
        """

        xobs = self.xobs_raw
        yobs = self.yobs_raw
        weights = self.weights_raw

        xmask = self._build_one_obs_mask("xobs", xobs, xmin, xmax)
        ymask = self._build_one_obs_mask("yobs", yobs, ymin, ymax)
        mask = xmask & ymask
        if weights is not None:
            wmask = self._build_one_obs_mask("weights", weights, wmin, wmax)
            mask = mask & wmask

        xobs = xobs[mask]
        yobs = yobs[mask]
        if weights is not None:
            weights = weights[mask]

        self._xobs = xobs
        self._yobs = yobs
        self._weights = weights
        self._tk_observed = mask

    def _set_popt(self, new):
        r"""Save as a tuple of (k, v) pairs so immutable. Convert to a dictionary i
        before returning the actual data with `pcov` method.
        """
        self._popt = list(zip(self.argnames, new))

    def _set_psigma(self, new):
        assert isinstance(new, np.ndarray)
        self._psigma = list(zip(self.argnames, new))

    def _set_pcov(self, new):
        assert isinstance(new, np.ndarray)
        # assert new.shape[0] == new.shape[1] square matrix?
        self._pcov = new

    def make_fit(self, **kwargs):
        r"""Fit the function with the independent values `xobs` and dependent values
        `yobs` using `curve_fit`.

        `kwargs` are passed directly to `curve_fit`.
        `p0` is set up internally, so it can't be passed.
        """

        # This line is legacy. Not sure why it's here, but I'm copying it over
        # assuming I had a good reason to include it. (20170309 0011)
        return_full = kwargs.get("full_output", False)
        if return_full:
            msg = "You haven't decided how to save `return_full` output."
            raise NotImplementedError(msg)

        try:
            assert self.sufficient_data  # Check we have enough data to fit.
        except ValueError as e:
            return e

        #         assert "p0" not in kwargs
        p0 = kwargs.pop("p0", self.p0)
        try:
            result = curve_fit(
                self.function, self.xobs, self.yobs, p0=p0, sigma=self.weights, **kwargs
            )
        except RuntimeError as e:
            return e

        popt, pcov = result[:2]
        sigma = np.sqrt(np.diag(pcov))

        # Need to figure out how/where to save the full output.

        #         # Check that he sigma values are finite.
        #         if not np.isfinite(sigma).all():
        #             msg = (
        #                 "Negative covariances lead to NaN uncertainties. "
        #                 "I don't trust them and don't know if the optimized "
        #                 "parameters are meaningful.\n\nsigma\n-----\n%s\n\npcov\n----\n%s\n\n"
        #             )
        #             self.logger.warning(msg, sigma, pcov)

        self._set_popt(popt)
        self._set_psigma(sigma)
        self._set_pcov(pcov)

        # pdb.set_trace()
        # self._fitinfo = fitinfo

    def residuals(self, pct=False):
        r"""
        Calculate the fit residuals.
        If pct, normalize by fit yvalues.
        """

        # TODO: calculate with all values
        # Make it an option to calculate with either
        # the values used in the fit or all the values,
        # including those excluded by `set_extrema`.

        r = self(self.xobs) - self.yobs

        if pct:
            r = 100.0 * (r / self(self.xobs))

        return r

    def set_binsigma(self, new):
        r"""Set the binsigma to new.

        If new is str, it can be "count", in which case we estimate
        sigma as sqrt(yvals - 1).
        Otherwise, new can be a numpy array of the same shape as
        xobs_raw.
        """

        if isinstance(new, np.ndarray):
            assert new.ndim == 1
            assert new.shape == self.xobs.shape
            self._binsigma = new

        elif isinstance(new, str):
            assert new.lower().startswith("count"), "Unrecognized new string: %s" % new
            self._binsigma = np.sqrt(self.yobs - 1)

        else:
            msg = "Unrecgonized binsigma: %s\ntype: %s" % (new, type(new))
            raise TypeError(msg)

    def val_uncert_2_string(self, value, uncertainty):
        r"""
        Convert a value, uncertainty pair to a string in which the
        value is reported to the first non-zero digit of the uncertainty.

        Require that value > uncertainty.

        Example
        -------
        >>> a = 3.1415
        >>> b = 0.01
        >>> val_uncert_2_string(a, b)
        "3.14 \pm 0.01"
        """

        # if np.isfinite(uncertainty) and value <= uncertainty:
        #     msg = ("Must be that value > uncertainty\n"
        #            "value = %s\nuncertainty = %s")
        #     raise ValueError(msg % (value, uncertainty))

        vprecision = 3
        if np.isfinite(uncertainty):
            uprecision = self._calc_precision(uncertainty)
            vprecision = self._calc_precision(value)
            vprecision = vprecision - uprecision

        #         else:
        #             self.logger.warning(
        #                 "1-sigma fit uncertainty is %s.\nSetting to -3.", uncertainty
        #             )

        template = r"{:.%se} \pm {:.0e}"
        template = template % abs(vprecision)

        out = template.format(value, uncertainty)

        # Clean out unnecessary
        # pdb.set_trace()
        # out = re.subn(_remove_exponential_pattern, "", out)
        # out = out[0] # Drop the number of repetitions removed.
        # pdb.set_trace()
        return out

    def set_TeX_argnames(self, **kwargs):
        r"""Define the mapping to format LaTeX function argnames.
        """
        # Save a tuple so immutable.
        self._TeX_argnames = kwargs.items()

    def set_TeX_info(
        self,
        chisq=False,
        convert_pow_10=True,
        strip_uncertainties=False,
        additional_info=None,
        annotate_fcn=None,
    ):
        r"""
        Generate a TeX-formatted string with the desired info

        Parameters
        ----------
        chisq: bool
            If True, include chisq/dof in the info.
        convert_pow_10: bool
            If True, use 10^{X} format. Otherwise, use eX format.
        strip_uncertaintites: bool
            If True, strip fit uncertainties from reported parameters.
        additional_info: str or iterable of strings
            Additional info added to the fit info annotation box.
        annotate_fcn: FunctionType
           Function that manipulates the final TeX_info str before returning.
        """

        template = "%s = %s"
        info = [template % kv for kv in self.TeX_popt.items()]
        info = [self.TeX_function] + info

        # pdb.set_trace()

        if chisq:
            info += [self.TeX_chisqdof]

        if convert_pow_10:
            # Convert to 10^X notation.
            info = [x.replace(r"e+", r" \times 10^{+") for x in info]
            info = [x.replace(r"e-", r" \times 10^{-") for x in info]
            info = [x.replace(r" \pm", r"} \pm") + r"}" for x in info]

            # Join then re-split info b/c a single iterator is
            # easier than a loop of them.
            info = "\n".join(info)

            # Conver +0X and -0X to +X and -X.
            info, p_sub_cnt = re.subn(r"\+0", r"+", info)
            info, m_sub_cnt = re.subn(r"\-0", r"-", info)

            info = info.split("\n")

        # TODO: convert_to_decimal
        #       option to convert an exponential number to a decimal.
        #       Probably can update val_uncert_2_string to accomplish that.

        info = [r"$ %s $" % x for x in info]
        info = "\n".join(info)

        info = info.replace(r"inf", r"\infty")

        if strip_uncertainties:
            info = info.split("\n")
            info = [x.split(r"\pm")[0] + "$" for x in info]
            info = "\n".join(info).replace("$$", "$")

        if additional_info is not None:
            if hasattr(additional_info, "__iter__"):
                for i, this_info in enumerate(additional_info):
                    additional_info[i] = self._check_and_add_math_escapes(this_info)

                additional_info = "\n".join(additional_info)
                additional_info = self._check_and_add_math_escapes(additional_info)

                info += "\n" + additional_info

        if annotate_fcn is not None:
            info = annotate_fcn(info)

        self._TeX_info = info
        return info

    def TeX_info(self):
        try:
            return self._TeX_info
        except AttributeError:
            return self.set_TeX_info()

    def annotate_TeX_info(self, ax, **kwargs):
        r"""Add the `TeX_info` annotation to ax.

        **kwargs are passed to ax.text. Defaults are listed below.

        Parameters
        ----------
        ax: mpl.Axes.axis_subplot

        bbox: dict
            dict(color="wheat", alpha=0.75)
        xloc, yloc: scalar
            0.05, 0.9
        ha, va: str
            ha - horizontalalignment (defaults "left")
            va - verticalalignment (default "right")
        transform:
            ax.transAxes
        """
        info = self.TeX_info()

        bbox = dict(color="wheat", alpha=0.75)
        xloc = kwargs.pop("xloc", 0.05)
        yloc = kwargs.pop("yloc", 0.9)
        horizontalalignment = kwargs.pop("ha", "left")
        verticalalignment = kwargs.pop("va", "top")
        axtrans = kwargs.pop("transform", ax.transAxes)

        ax.text(
            xloc,
            yloc,
            info,
            bbox=bbox,
            horizontalalignment=horizontalalignment,
            verticalalignment=verticalalignment,
            transform=axtrans,
            **kwargs
        )

    def plot_fit(
        self,
        ax=None,
        ylabel=None,
        drawstyle=None,
        annotate=True,
        subplots_kwargs=None,
        hist_kwargs=None,
        bin_kwargs=None,
        fit_kwargs=None,
        annotate_kwargs=None,
    ):
        r"""
        Make a plot of the fit.

        Parameters
        ----------
        ax: mpl.Axes.axis_subplot

        ylabel: str, None
            If None, defaults to a formatted Counts.
        drawstyle: str, None
            `mpl` `drawstyle`, shared by `hist` and `bins`.
            If None, defaults to "steps-mid".
        annotate: True
            If True, add fit info to the annotation using ax.text.
        subplots_kwargs: dict
            Passed to plt.subplots(**subplots_kwargs)
        hist_kwargs: dict
            Passed to ax.plot(**hist_kwargs) for plotting obs.
        bin_kwargs: dict
            Passed to ax.plot(**bins_kwargs) for plotting raw obs.
        fit_kwargs: dict
            Passed to ax.plot(**fit_kwargs) for plotting fit.
        annotate_kwargs:
            Passed to ax.text.
        """

        if ax is None:
            fig, ax = plt.subplots()

        if hist_kwargs is None:
            hist_kwargs = dict(color="k")

        if bin_kwargs is None:
            bin_kwargs = dict(color="darkgreen")

        if fit_kwargs is None:
            fit_kwargs = dict(color="darkorange")

        if annotate_kwargs is None:
            annotate_kwargs = {}

        if drawstyle is None:
            drawstyle = "steps-mid"

        if ylabel is None:
            # TODO: set defaults with `labels` classes from my plotting class?
            ylabel = r"$\mathrm{Count} \; [\#]$"

        hist_label = hist_kwargs.pop("label", r"$\mathrm{Bins}$")
        bin_label = bin_kwargs.pop("label", r"$\mathrm{in \; Fit}$")
        fit_label = fit_kwargs.pop("label", r"$\mathrm{Fit}$")

        # Plot the raw data histograms.
        ax.plot(
            self.xobs_raw,
            self.yobs_raw,
            drawstyle=drawstyle,
            label=hist_label,
            color=hist_kwargs.pop("color", "k"),
            **hist_kwargs
        )

        # Overplot with the data as selected for the plot.
        ax.plot(
            self.xobs,
            self.yobs,
            drawstyle=drawstyle,
            label=bin_label,
            color=bin_kwargs.pop("color", "darkgreen"),
            **bin_kwargs
        )

        # Overplot the fit.
        ax.plot(
            self.xobs_raw,
            self(self.xobs_raw),
            label=fit_label,
            color=fit_kwargs.pop("color", "darkorange"),
            **fit_kwargs
        )

        if ylabel is not None:
            ax.set_ylabel(ylabel)

        ax.grid(True, which="major", axis="both")

        ax.legend(loc=1, framealpha=0)  # loc chosen so annotation text defaults work.

        # Copied from plt.hist. (20161107_0112)
        ax.update_datalim(
            [(self.xobs_raw[0], 0), (self.xobs_raw[-1], 0)], updatey=False
        )

        if annotate:
            self.annotate_TeX_info(ax, **annotate_kwargs)

        return ax

    def plot_residuals(self, ax=None, pct=True, subplots_kwargs=None, **plot_kwargs):
        r"""Make a plot of the fit function that includes the data and fit,
        but are limited to data included in the fit.

        Residuals are plotted as a percentage, both positive and negative, on
        a symlog scale with `linthreshy=10`.
        """

        if subplots_kwargs is None:
            subplots_kwargs = {}

        if ax is None:
            fig, ax = plt.subplots()

        drawstyle = plot_kwargs.pop("drawstyle", "steps-mid")
        color = plot_kwargs.pop("color", "darkgreen")

        ax.plot(
            self.xobs,
            self.residuals(pct=pct),
            drawstyle=drawstyle,
            color=color,
            **plot_kwargs
        )

        ax.grid(True, which="major", axis="both")

        if pct:
            ax.set_ylabel(r"$\mathrm{Residual} \; [\%]$")
            ax.set_yscale("symlog", linthreshy=10)
            ax.set_ylim(-100, 100)

        else:
            ax.set_ylabel(r"$\mathrm{Residual} \; [\#]$")

        ax.update_datalim(
            [(self.xobs_raw[0], 0), (self.xobs_raw[-1], 0)], updatey=False
        )
        # ax.set_xlim(self.xobs_raw[0], self.xobs_raw[-1])

        return ax

    def plot_fit_resid(
        self, annotate=True, resid_pct=True, fit_resid_axes=None, **kwargs
    ):
        r"""Make a stacked fit, residual plot.

        kwargs passed to `plot_fit`.
        """

        if fit_resid_axes is not None:
            hist_ax, resid_ax = fit_resid_axes

        else:
            fig = plt.figure()
            gs = mpl.gridspec.GridSpec(2, 1, height_ratios=[3, 1], hspace=0.1)
            # sharex in this code requires that I pass the axis object with which the x-axis is being shared.
            # Source for sharex option: http://stackoverflow.com/questions/22511550/gridspec-with-shared-axes-in-python
            resid_ax = fig.add_subplot(gs[1])
            hist_ax = fig.add_subplot(gs[0], sharex=resid_ax)

        self.plot_fit(ax=hist_ax, annotate=annotate, **kwargs)
        self.plot_residuals(ax=resid_ax, pct=resid_pct)

        hist_ax.set_ylabel(r"$\mathrm{Count} \, [\#]$")
        resid_ax.set_ylabel(r"$\mathrm{Residual} \, [\%]$")

        hist_ax.tick_params(labelbottom=False)

        return hist_ax, resid_ax
