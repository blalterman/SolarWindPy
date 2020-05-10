#!/usr/bin/env python
r""":py:mod:`~solarwindpy.fitfunctions` base class.

A `FitFunction` takes a function, generates a fit with `scipy.curve_fit`, and provides
tools for plotting that fit. It also provies tools for annotating the plot with
well-formatted LaTeX that describes the fit.
"""

import pdb  # noqa: F401
import logging  # noqa: F401

# import re
import numpy as np
import matplotlib as mpl

from abc import ABC, abstractproperty
from collections import namedtuple
from matplotlib import pyplot as plt
from inspect import getargspec
from scipy.optimize import curve_fit
from pathlib import Path

import solarwindpy as swp

from .tex_info import TeXinfo

# # Compile this once on import to save time.
# _remove_exponential_pattern = r"e\+00+"  # Replace the `e+00`for 2 or more zeros.
# _remove_exponential_pattern = re.compile(_remove_exponential_pattern)

AxesLabels = namedtuple("AxesLabels", "x,y,z", defaults=(None,))
LogAxes = namedtuple("LogAxes", "x,y", defaults=(False,))


class FitFunction(ABC):
    r"""Assuming that you don't want any special formatting, the typical call order
    is:

        fit_function = FitFunction(function, TeX_string)
        fit_function.make_fit()

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
        xoutside=None,
        ymin=None,
        ymax=None,
        youtside=None,
        weights=None,
        wmin=None,
        wmax=None,
        logx=False,
        logy=False,
    ):
        self._init_logger()
        self._set_argnames()
        self._set_raw_obs(xobs, yobs, weights)
        self._log = LogAxes(x=logx, y=logy)
        self._labels = AxesLabels("x", "y")

        if weights is None:
            assert wmin is None
            assert wmax is None

        self.set_fit_obs(
            xmin=xmin,
            xmax=xmax,
            xoutside=xoutside,
            ymin=ymin,
            ymax=ymax,
            youtside=youtside,
            wmin=wmin,
            wmax=wmax,
            logx=logx,
            logy=logy,
        )

    def __str__(self):
        return f"{self.__class__.__name__} ({self.TeX_function})"

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

    @property
    def logger(self):
        return self._logger

    def _init_logger(self):
        # return None
        logger = logging.getLogger("{}.{}".format(__name__, self.__class__.__name__))
        self._logger = logger

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

    @property
    def labels(self):
        return self._labels

    @property
    def path(self):
        base = Path(str(self))

        try:
            base /= self.labels.x.path
        except AttributeError:
            base /= str(self.labels.x)

        try:
            base /= self.labels.y.path
        except AttributeError:
            base /= str(self.labels.y)

        if self.labels.z is not None:
            try:
                base = base / self.labels.z.path
            except AttributeError:
                base = base / str(self.labels.z)

        x_scale = "logX" if self.log.x else "linX"
        y_scale = "logY" if self.log.y else "logY"
        scale_info = "_".join([x_scale, y_scale])

        path = base / scale_info
        return path

    @property
    def popt(self):
        r"""Optimized fit parameters.
        """
        return dict(self._popt)

    @property
    def psigma(self):
        return dict(self._psigma)

    @property
    def psigma_relative(self):
        return {k: v / self.popt[k] for k, v in self.psigma.items()}

    @property
    def pcov(self):
        # Return a copy to protect the values.
        return self._pcov.copy()

    @property
    def nobs(self):
        r"""The total number of observations used in the fit.
        """
        return self.tk_observed.sum()

    @property
    def sufficient_data(self):
        r"""A check to ensure that we can fit the data before doing any
        computations.
        """
        chk = self.nobs >= len(self.argnames)
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
        r"""Independent values for the fit, not accounting for extrema,
        finite data, etc.
        """
        return self._xobs_raw

    @property
    def yobs_raw(self):
        r"""Dependent values for the fit, not accounting for extrema,
        finite data, etc.
        """
        return self._yobs_raw

    @property
    def weights_raw(self):
        r"""Weights used by `curve_fit`, not including extrema, finite
        data, etc.
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
    def log(self):
        r"""Log scale for axes

        Only used for plotting purposes, in particular identifying when we need to plot weights/y
        instead of weights.
        """
        return self._log

    #     @property
    #     def TeX_argnames(self):
    #         try:
    #             # Saved as tuple, so convert from tuple.
    #             out = self._TeX_argnames
    #             out = dict(out)
    #             return out
    #
    #         except AttributeError:
    #             return None

    #     @property
    #     def TeX_popt(self):
    #         r"""Create a dictionary with (k, v) pairs corresponding to
    #         (self.argnames, popt \pm psigma) with the appropriate uncertainty.
    #
    #         See `set_TeX_trans_argnames` to translate the argnames for TeX.
    #         """
    #         psigma = self.psigma
    #         popt = self.popt.items()
    #         TeX_popt = {k: self.val_uncert_2_string(v, psigma[k]) for k, v in popt}
    #
    #         translate = self.TeX_argnames
    #         if translate is not None:
    #             for k0, k1 in translate.items():
    #                 TeX_popt[k1] = TeX_popt.pop(k0)
    #
    #         return TeX_popt

    #     @staticmethod
    #     def _calc_precision(value):
    #         r"""Primarily for use with the `val_uncert_2_string` and other methods that may
    #         require this.
    #         """
    #         # assert 1 > value > 0, \
    #         #     "Only written to deal with 0 < X < 1 numbers.\nX = %s" % value
    #
    #         # Convert the fractional part to an exponential string.
    #         # E.g. 0.0009865 -> 9.865000e-04
    #         precision = "%e" % value  # (value - int(value))
    #
    #         # Split the exponential notation at the `e`,  a la
    #         # "1.250000e-04"; take the exponent "4", excluding the sign.
    #         precision = int(precision.partition("e")[2])
    #
    #         return precision

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
        #         mask = np.full_like(x, True, dtype=bool)

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

    def _build_outside_mask(self, axis, x, outside):
        r"""Take data outside of the range `outside[0]:outside[1]`.
        """

        if outside is None:
            return np.full_like(x, True, dtype=bool)

        lower, upper = outside
        assert lower < upper
        l_mask = x <= lower
        u_mask = x >= upper
        mask = l_mask | u_mask

        return mask

    def _set_argnames(self):
        r"""
        Set the arguments of the function, assuming that the first
        is dependent variable.

        Should be called after function is set.
        """
        args = getargspec(self.function).args[1:]
        self._argnames = args

    def set_labels(self, **kwargs):
        r"""Set or update x, y, or z labels. Any label not specified in kwargs
        is propagated from `self.labels.<x, y, or z>`.
        """

        x = kwargs.pop("x", self.labels.x)
        y = kwargs.pop("y", self.labels.y)
        z = kwargs.pop("z", self.labels.z)

        if len(kwargs.keys()):
            extra = "\n".join(["{}: {}".format(k, v) for k, v in kwargs.items()])
            raise KeyError("Unexpected kwarg\n{}".format(extra))

        self._labels = AxesLabels(x, y, z)

    def set_fit_obs(
        self,
        xmin=None,
        xmax=None,
        xoutside=None,
        ymin=None,
        ymax=None,
        youtside=None,
        wmin=None,
        wmax=None,
        logx=False,
        logy=False,
    ):
        r"""
        Set the observed values we'll actually use in the fit by applying limits
        to xobs_raw and yobs_raw and checking for finite values.

        All boundaries are inclusive <= or >=.

        If logy, then make selection of `wmin` and `wmax` based on :math:`w/(y \ln(10))`.
        """

        xobs = self.xobs_raw
        yobs = self.yobs_raw
        weights = self.weights_raw

        xmask = self._build_one_obs_mask("xobs", xobs, xmin, xmax)
        ymask = self._build_one_obs_mask("yobs", yobs, ymin, ymax)
        xout_mask = self._build_outside_mask("xobs", xobs, xoutside)
        yout_mask = self._build_outside_mask("yobs", yobs, youtside)

        mask = xmask & ymask & xout_mask & yout_mask
        if weights is not None:
            weights_for_mask = weights

            if logy:
                # Enables picking weights based on normalized scale for log stuff
                weights_for_mask = weights_for_mask / (yobs * np.log(10))

            wmask = self._build_one_obs_mask("weights", weights_for_mask, wmin, wmax)
            mask = mask & wmask

        xobs = xobs[mask]
        yobs = yobs[mask]
        if weights is not None:
            weights = weights[mask]

        self._xobs = xobs
        self._yobs = yobs
        self._weights = weights
        self._tk_observed = mask
        self._labels = AxesLabels(x="x", y=swp.pp.labels.Count())

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

    def _estimate_markevery(self):
        try:
            # Estimate marker density for readability
            markevery = int(10.0 ** (np.floor(np.log10(self.xobs.size) - 1)))
        except OverflowError:
            # Or we have a huge number of data points, so lets only
            # mark a few of them.
            markevery = 1000

        if not markevery:
            markevery = None

        return markevery

    def make_fit(self, **kwargs):
        f"""Fit the function with the independent values `xobs` and dependent
        values `yobs` using `curve_fit`.

        Parameters
        ----------
        kwargs:
            Unless specified here, defaults are as defined by `curve_fit`.

                ============= ======================================
                    kwarg                    default
                ============= ======================================
                 p0            Setup by `{self.__class__.__name__}`
                 return_full   False
                 method        "trf"
                 loss          "huber"
                 max_nfev      10000
                 f_scale       0.1
                ============= ======================================

        """
        p0 = kwargs.pop("p0", self.p0)
        method = kwargs.pop("method", "trf")
        loss = kwargs.pop("loss", "huber")
        max_nfev = kwargs.pop("max_nfev", 10000)
        f_scale = kwargs.pop("f_scale", 0.1)

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

        #         #         assert "p0" not in kwargs
        #         # Avoid issuing a `logger.warning` with `p0 = kwargs.pop("p0", self.p0)`.
        #         try:
        #             p0 = kwargs.pop("p0")
        #         except KeyError:
        #             p0 = self.p0

        try:
            result = curve_fit(
                self.function,
                self.xobs,
                self.yobs,
                p0=p0,
                sigma=self.weights,
                method=method,
                loss=loss,
                max_nfev=max_nfev,
                f_scale=f_scale,
                **kwargs,
            )
        except (RuntimeError, ValueError) as e:
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

    def set_log(self, **kwargs):
        r"""Set :py:class:`LogAxes`.

        Only used for determining if weights should be :math:`w/(y \ln(10))`.
        """
        log = self._log._asdict()
        for k, v in kwargs.items():
            log[k] = v

        self._log = LogAxes(**log)

    #     def val_uncert_2_string(self, value, uncertainty):
    #         r"""
    #         Convert a value, uncertainty pair to a string in which the
    #         value is reported to the first non-zero digit of the uncertainty.
    #
    #         Require that value > uncertainty.
    #
    #         Example
    #         -------
    #         >>> a = 3.1415
    #         >>> b = 0.01
    #         >>> val_uncert_2_string(a, b)
    #         "3.14 \pm 0.01"
    #         """
    #
    #         # if np.isfinite(uncertainty) and value <= uncertainty:
    #         #     msg = ("Must be that value > uncertainty\n"
    #         #            "value = %s\nuncertainty = %s")
    #         #     raise ValueError(msg % (value, uncertainty))
    #
    #         vprecision = 3
    #         if np.isfinite(uncertainty):
    #             uprecision = self._calc_precision(uncertainty)
    #             vprecision = self._calc_precision(value)
    #             vprecision = vprecision - uprecision
    #
    #         #         else:
    #         #             self.logger.warning(
    #         #                 "1-sigma fit uncertainty is %s.\nSetting to -3.", uncertainty
    #         #             )
    #
    #         template = r"{:.%se} \pm {:.0e}"
    #         template = template % abs(vprecision)
    #
    #         out = template.format(value, uncertainty)
    #
    #         # Clean out unnecessary
    #         # pdb.set_trace()
    #         # out = re.subn(_remove_exponential_pattern, "", out)
    #         # out = out[0] # Drop the number of repetitions removed.
    #         # pdb.set_trace()
    #         return out

    #     def set_TeX_argnames(self, **kwargs):
    #         r"""Define the mapping to format LaTeX function argnames.
    #         """
    #         # Save a tuple so immutable.
    #         for k, v in kwargs.items():
    #             if k not in self.argnames:
    #                 raise ValueError(
    #                     f"The TeX_argname {k} has no comparable pair in the TeX_function"
    #                 )
    #         self._TeX_argnames = kwargs.items()

    def build_TeX_info(self):
        chisq_dof = False
        try:
            chisq_dof = self.chisqdof
        except AttributeError:
            pass

        tex_info = TeXinfo(
            self.popt, self.psigma, self.TeX_function, chisq_dof=chisq_dof
        )
        self._TeX_info = tex_info
        return tex_info

    @property
    def TeX_info(self):
        try:
            return self._TeX_info
        except AttributeError:
            return self.build_TeX_info()

    def _format_hax(self, ax):
        r"""Format the :py:meth:`plot_bins`, :py:meth:`plot_in_fit`, and
        :py:meth:`plot_fit` results.
        """
        ax.grid(True, which="major", axis="both")

        #         ax.legend(loc=1, framealpha=0)  # loc chosen so annotation text defaults work.

        # Copied from plt.hist. (20161107_0112)
        ax.update_datalim(
            [(self.xobs_raw[0], 0), (self.xobs_raw[-1], 0)], updatey=False
        )

        ax.set_xlabel(self.labels.x)
        ax.set_ylabel(self.labels.y)

    def plot_raw(self, ax=None, **kwargs):
        r"""Plot the observations used in the fit from :py:meth:`self.xobs_raw`,
        :py:meth:`self.yobs_raw`, :py:meth:`self.weights_raw`.
        """
        if ax is None:
            fig, ax = swp.pp.subplots()

        kwargs = mpl.cbook.normalize_kwargs(kwargs, mpl.lines.Line2D._alias_map)
        color = kwargs.pop("color", "k")
        label = kwargs.pop("label", r"$\mathrm{Obs}$")

        x = self.xobs_raw
        y = self.yobs_raw
        w = self.weights_raw
        if self.log.y and w is not None:
            w = w / (y * np.log(10.0))

        # Plot the raw data histograms.
        plotline, caplines, barlines = ax.errorbar(
            x, y, yerr=w, label=label, color=color, **kwargs
        )

        self._format_hax(ax)

        return ax, plotline, caplines, barlines

    def plot_used(self, ax=None, **kwargs):
        r"""Plot the observations used in the fit from :py:meth:`self.xobs`,
        :py:meth:`self.yobs`, and :py:meth:`self.weights`.
        """
        if ax is None:
            fig, ax = swp.pp.subplots()

        kwargs = mpl.cbook.normalize_kwargs(kwargs, mpl.lines.Line2D._alias_map)
        color = kwargs.pop("color", "darkgreen")
        marker = kwargs.pop("marker", "P")
        markerfacecolor = kwargs.pop("markerfacecolor", "none")
        markersize = kwargs.pop("markersize", 8)
        markevery = kwargs.pop("markevery", None)
        label = kwargs.pop("label", r"$\mathrm{Used}$")

        x = self.xobs
        y = self.yobs
        w = self.weights
        if self.log.y and w is not None:
            w = w / (y * np.log(10.0))

        if markevery is None:
            markevery = self._estimate_markevery()

        # Plot the raw data histograms.
        plotline, caplines, barlines = ax.errorbar(
            x,
            y,
            yerr=w,
            label=label,
            color=color,
            marker=marker,
            markerfacecolor=markerfacecolor,
            markersize=markersize,
            markevery=markevery,
            **kwargs,
        )

        self._format_hax(ax)

        return ax, plotline, caplines, barlines

    def plot_fit(self, ax=None, annotate=True, annotate_kwargs=None, **kwargs):
        r"""Plot the fit.
        """
        if ax is None:
            fig, ax = swp.pp.subplots()

        if annotate_kwargs is None:
            annotate_kwargs = {}

        kwargs = mpl.cbook.normalize_kwargs(kwargs, mpl.lines.Line2D._alias_map)
        color = kwargs.pop("color", "darkorange")
        label = kwargs.pop("label", r"$\mathrm{Fit}$")
        linestyle = kwargs.pop("linestyle", (0, (7, 3, 1, 3, 1, 3, 1, 3)))

        # Overplot the fit.
        ax.plot(
            self.xobs_raw,
            self(self.xobs_raw),
            label=label,
            color=color,
            linestyle=linestyle,
            **kwargs,
        )

        if annotate:
            self.TeX_info.annotate_info(ax, **annotate_kwargs)
        #             self.annotate_TeX_info(ax, **annotate_kwargs)

        self._format_hax(ax)

        return ax

    def plot_raw_used_fit(
        self,
        ax=None,
        drawstyle=None,
        annotate=True,
        raw_kwargs=None,
        used_kwargs=None,
        fit_kwargs=None,
        annotate_kwargs=None,
    ):
        r"""Make a plot of the raw observations, observations in fit, and the fit.

        Combines the outputs of :py:meth:`self.plot_raw`, :py:meth:`self.plot_used`,
        and :py:meth:`self.plot_fit`.

        Parameters
        ----------
        ax: None, mpl.Axes.axis_subplot

        drawstyle: str, None
            `mpl` `drawstyle`, shared by :py:meth:`self.plot_raw` and :py:meth:`self.plot_used`.
            If None, defaults to "steps-mid".
        annotate: True
            If True, add fit info to the annotation using ax.text.
        raw_kwargs: dict
            Passed to `ax.plot(**kwargs)` in :py:meth:`self.plot_raw`.
        used_kwargs: dict
            Passed to `ax.plot(**kwargs)` in :py:meth:`self.plot_used`.
        fit_kwargs: dict
            Passed to `ax.plot(**fit_kwargs)` for plotting fit.
        annotate_kwargs:
            Passed to `ax.text`.

        Returns
        -------
        ax: mpl.Axes.axis_subplot
        """

        if ax is None:
            fig, ax = swp.pp.subplots()

        if raw_kwargs is None:
            raw_kwargs = (
                dict()
            )  # dict(color="darkgreen", markerfacecolor="none", marker="P")

        if used_kwargs is None:
            used_kwargs = dict()  # dict(color="k")

        if fit_kwargs is None:
            fit_kwargs = dict()  # dict(color="darkorange")

        if drawstyle is None:
            drawstyle = "steps-mid"

        self.plot_raw(ax=ax, drawstyle=drawstyle, **raw_kwargs)
        self.plot_used(ax=ax, drawstyle=drawstyle, **used_kwargs)
        self.plot_fit(
            ax=ax, annotate=annotate, annotate_kwargs=annotate_kwargs, **fit_kwargs
        )

        ax.legend(loc=1, framealpha=0)  # loc chosen so annotation text defaults work.

        #         # Copied from plt.hist. (20161107_0112)
        #         ax.update_datalim(
        #             [(self.xobs_raw[0], 0), (self.xobs_raw[-1], 0)], updatey=False
        #         )

        self._format_hax(ax)

        return ax

    def plot_residuals(self, ax=None, pct=True, subplots_kwargs=None, **kwargs):
        r"""Make a plot of the fit function that includes the data and fit,
        but are limited to data included in the fit.

        Residuals are plotted as a percentage, both positive and negative, on
        a symlog scale with `linthreshy=10`.
        """

        if subplots_kwargs is None:
            subplots_kwargs = {}

        if ax is None:
            fig, ax = plt.subplots(**subplots_kwargs)

        kwargs = mpl.cbook.normalize_kwargs(kwargs, mpl.lines.Line2D._alias_map)
        drawstyle = kwargs.pop("drawstyle", "steps-mid")
        color = kwargs.pop("color", "darkgreen")
        marker = kwargs.pop("marker", "P")
        markerfacecolor = kwargs.pop("markerfacecolor", "none")
        markersize = kwargs.pop("markersize", 8)
        markevery = kwargs.pop("markevery", None)

        if markevery is None:
            markevery = self._estimate_markevery()

        ax.plot(
            self.xobs,
            self.residuals(pct=pct),
            drawstyle=drawstyle,
            color=color,
            marker=marker,
            markerfacecolor=markerfacecolor,
            markersize=markersize,
            markevery=markevery,
            **kwargs,
        )

        ax.grid(True, which="major", axis="both")

        ax.set_xlabel(self.labels.x)
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

    def plot_raw_used_fit_resid(
        self,
        annotate=True,
        fit_resid_axes=None,
        figsize=(6, 4),
        resid_kwargs=None,
        **kwargs,
    ):
        f"""Make a stacked fit, residual plot.

        Parameters
        ----------
        annotate: bool
            If True, add fit annotation to axis.
        fit_resid_axes: None, 2-tuple of mpl.axis.Axis
            If not None, (fit, resid) axis pair to plot the (raw, used, fit)
            and residual on, respectively. Otherwise, use `GridSpec` to build
            a pair of axes where the `raw_used_fit` axis is 3 times the `resid_axis`.
            Additionally, if `fit_resid_axes` is None, the `hax` and `rax` will share
            an x-axis and `hax`'s x-ticks and label will be set invisible.
        figsize:
            Any valid argument for :py:meth:`plt.figure(figsize=figsize)`. This code
            was developed with default size 6x4 and this size helps accomodate annotation.
            So we persist it here.
        resid_kwargs: dict, None
            Passed to :py:meth:`{self.__class__.__name__}.plot_residuals`.
        kwargs:
            Passed to :py:meth:`{self.__class__.__name__}.plot_raw_used_fit`.

        Returns
        -------
        hax: mpl.axis.Axis
            Axis with raw observations, used observations, and fit plotted on it.
        rax: mpl.axis.Axis
            Axis with residuals plotted on it.
        """

        if fit_resid_axes is not None:
            hax, rax = fit_resid_axes

        else:
            fig = plt.figure(figsize=figsize)
            gs = mpl.gridspec.GridSpec(2, 1, height_ratios=[3, 1], hspace=0.1)
            # sharex in this code requires that I pass the axis object with which the x-axis is being shared.
            # Source for sharex option: http://stackoverflow.com/questions/22511550/gridspec-with-shared-axes-in-python
            rax = fig.add_subplot(gs[1])
            hax = fig.add_subplot(gs[0], sharex=rax)

        if resid_kwargs is None:
            resid_kwargs = dict()

        resid_pct = resid_kwargs.pop("resid_pct", True)

        self.plot_raw_used_fit(ax=hax, annotate=annotate, **kwargs)
        self.plot_residuals(ax=rax, pct=resid_pct, **resid_kwargs)

        if fit_resid_axes is None:
            hax.tick_params(labelbottom=False)
            hax.xaxis.label.set_visible(False)

        return hax, rax
