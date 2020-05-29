#!/usr/bin/env python
r""":py:mod:`~solarwindpy.fitfunctions` base class.

A `FitFunction` takes a function, generates a fit with `scipy.curve_fit`, and provides
tools for plotting that fit. It also provies tools for annotating the plot with
well-formatted LaTeX that describes the fit.
"""

import pdb  # noqa: F401
import logging  # noqa: F401
import numpy as np

from abc import ABC, abstractproperty
from collections import namedtuple
from inspect import getfullargspec
from scipy.optimize import curve_fit

from .tex_info import TeXinfo
from .fitfunction_plot import FitFunctionPlot

Observations = namedtuple("Observations", "x,y,w")
UsedRawObs = namedtuple("UsedRawObs", "used,raw,tk_observed")
InitialGuessInfo = namedtuple("InitialGuessInfo", "p0,bounds")


class FitFunction(ABC):
    r"""Assuming that you don't want any special formatting, the typical call
    order is:

        fit_function = FitFunction(function, TeX_string)
        fit_function.make_fit()

    Instances are callable. If the fit fails, calling the instance will return
    an array of NaNs the same shape as the x-values.
    """

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

        if weights is None:
            assert wmin is None
            assert wmax is None

        self.set_fit_obs(
            xobs,
            yobs,
            weights,
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

        try:
            popt_ = self.popt
            popt_ = [popt_[k] for k in self.argnames]

            # NOTE
            # An instance of FitFunction is for a given function. To change the
            # function itself, a new instance of FitFunction should be required.
            # Therefore, we access the function directly.
            y = self.function(x, *popt_)

        except AttributeError as e:
            if "'ULEISPowerLaw' object has no attribute '_popt'" in str(e):
                y = np.full_like(x, np.nan, dtype=np.float64)

        return y

    @property
    def logger(self):
        return self._logger

    def _init_logger(self):
        # return None
        logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
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
    def argnames(self):
        r"""
        The names of the actual function arguments pulled by getfullargspec.
        """
        return self._argnames

    #     @property
    #     def labels(self):
    #         return self._labels

    @property
    def nobs(self):
        r"""The total number of observations used in the fit.
        """
        return self.observations.tk_observed.sum()

    @property
    def observations(self):
        return self._observations

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
        yvals = self.observations.used.y
        yfits = self(self.observations.used.x)
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
    def plotter(self):
        try:
            return self._plotter
        except AttributeError:
            return self.build_plotter()

    @property
    def initial_guess_info(self):

        # If failed to make an initial guess, then don't build the info.
        try:
            p0 = self.p0
            lower, upper = self.fit_bounds
        except AttributeError:
            return None

        names = self.argnames
        info = {
            name: InitialGuessInfo(guess, (lb, ub))
            for name, guess, lb, ub in zip(names, p0, lower, upper)
        }

        #         info = ["\n".join(param) for param in info]
        #         info = "\n\n".join(info)

        return info

    def _clean_raw_obs(self, xobs, yobs, weights):
        r"""
        Set the raw x- and y-values along with weights for the fit.

        Doesn't account for extrema, finite data, etc.
        """
        xobs = np.asarray(xobs)
        yobs = np.asarray(yobs)
        if weights is not None:
            weights = np.asarray(weights)

        if xobs.shape != yobs.shape:
            raise ValueError(
                f"""xobs and yobs must have the same shape.,
xobs: {xobs.shape},
yobs: {yobs.shape}"""
            )

        if weights is not None and weights.shape != xobs.shape:
            raise ValueError(
                f"""weights and xobs must have the same shape.,
weighs: {weights.shape}",
xobs: {xobs.shape}"""
            )

        return xobs, yobs, weights

    def _build_one_obs_mask(self, axis, x, xmin, xmax):
        #         mask = np.full_like(x, True, dtype=bool)

        mask = np.isfinite(x)

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
        args = getfullargspec(self.function).args[1:]
        self._argnames = args

    def set_fit_obs(
        self,
        xobs_raw,
        yobs_raw,
        weights_raw,
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

        xobs_raw, yobs_raw, weights_raw = self._clean_raw_obs(
            xobs_raw, yobs_raw, weights_raw
        )

        xmask = self._build_one_obs_mask("xobs", xobs_raw, xmin, xmax)
        ymask = self._build_one_obs_mask("yobs", yobs_raw, ymin, ymax)
        xout_mask = self._build_outside_mask("xobs", xobs_raw, xoutside)
        yout_mask = self._build_outside_mask("yobs", yobs_raw, youtside)

        mask = xmask & ymask & xout_mask & yout_mask
        if weights_raw is not None:
            weights_for_mask = weights_raw

            if logy:
                # Enables picking weights based on normalized scale for log stuff
                weights_for_mask = weights_for_mask / (yobs_raw * np.log(10))

            wmask = self._build_one_obs_mask("weights", weights_for_mask, wmin, wmax)
            mask = mask & wmask

        xobs = xobs_raw[mask]
        yobs = yobs_raw[mask]
        weights = None
        if weights_raw is not None:
            weights = weights_raw[mask]

        used = Observations(xobs, yobs, weights)
        raw = Observations(xobs_raw, yobs_raw, weights_raw)
        usedrawobs = UsedRawObs(used, raw, mask)
        self._observations = usedrawobs
        #         self._tk_observed = mask

    #         self._labels = AxesLabels(x="x", y=swp.pp.labels.Count())

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

    def build_plotter(self):
        obs = self.observations
        yfit = self(self.observations.raw.x)
        tex_info = self.TeX_info

        #         try:
        #             tex_info = self.TeX_info
        #         except AttributeError as e:
        #             if "'ULEISPowerLaw' object has no attribute '_popt'" in str(e):
        #                 tex_info = None

        plotter = FitFunctionPlot(
            obs, yfit, tex_info, fitfunction_name=self.__class__.__name__
        )
        self._plotter = plotter
        return plotter

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
                self.observations.used.x,
                self.observations.used.y,
                p0=p0,
                sigma=self.observations.used.w,
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

        r = self(self.observations.used.x) - self.observations.used.y

        if pct:
            r = 100.0 * (r / self(self.observations.used.x))

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
            assert new.shape == self.observations.used.x.shape
            self._binsigma = new

        elif isinstance(new, str):
            assert new.lower().startswith("count"), "Unrecognized new string: %s" % new
            self._binsigma = np.sqrt(self.observations.used.y - 1)

        else:
            msg = "Unrecgonized binsigma: %s\ntype: %s" % (new, type(new))
            raise TypeError(msg)

    def build_TeX_info(self):
        chisq_dof = False
        try:
            chisq_dof = self.chisqdof
        except AttributeError:
            pass

        # Allows annotating of TeX_info when fit fails in a manner
        # that is easily identifiable.
        try:
            popt = self.popt
        except AttributeError:
            popt = {k: np.nan for k in self.argnames}

        try:
            psigma = self.psigma
        except AttributeError:
            psigma = {k: np.nan for k in self.argnames}

        tex_info = TeXinfo(
            popt,
            psigma,
            self.TeX_function,
            chisq_dof=chisq_dof,
            initial_guess_info=self.initial_guess_info,
        )
        self._TeX_info = tex_info
        return tex_info

    @property
    def TeX_info(self):
        try:
            return self._TeX_info
        except AttributeError:
            return self.build_TeX_info()
