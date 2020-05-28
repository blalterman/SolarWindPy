#!/usr/bin/env python
r""":py:mod:`~solarwindpy.fitfunctions` base class.

A `FitFunction` takes a function, generates a fit with `scipy.curve_fit`, and provides
tools for plotting that fit. It also provies tools for annotating the plot with
well-formatted LaTeX that describes the fit.
"""

import pdb  # noqa: F401
import logging  # noqa: F401
import warnings
import numpy as np

from abc import ABC, abstractproperty
from collections import namedtuple
from inspect import getfullargspec
from scipy.optimize import curve_fit
from scipy.optimize import least_squares, OptimizeWarning
from scipy.optimize.minpack import _wrap_func, _wrap_jac, _initialize_feasible
from scipy.optimize._lsq.least_squares import prepare_bounds
from scipy.linalg import svd, cholesky, LinAlgError

from .tex_info import TeXinfo
from .fitfunction_plot import FitFunctionPlot

Observations = namedtuple("Observations", "x,y,w")
UsedRawObs = namedtuple("UsedRawObs", "used,raw,tk_observed")
InitialGuessInfo = namedtuple("InitialGuessInfo", "p0,bounds")
ChisqPerDegreeOfFreedom = namedtuple("ChisqPerDegreeOfFreedom", "linear,robust")


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

    @property
    def chisq_dof(self):
        r"""Chisq per degree of freedom :math:`\chi^2_\nu`.

        If None, not calculated by `make_fit_old`. If `np.nan`, fit failed.
        """
        #         r = self.residuals(pct=False)
        #         sigma = self.observations.used.w
        #         if sigma is not None:
        #             r = r / sigma
        #
        #         chisq = (r ** 2).sum()
        #         dof = r.size - len(self.p0)
        #         chisq_dof = chisq / dof
        #         return chisq_dof
        try:
            return self._chisq_dof
        except AttributeError:
            return None

    @property
    def dof(self):
        r"""Degrees of freedom in the fit.
        """
        return self.observations.used.y.size - len(self.p0)

    @property
    def fit_result(self):
        return self._fit_result

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

    @property
    def nobs(self):
        r"""The total number of observations used in the fit.
        """
        return self.observations.tk_observed.sum()

    @property
    def observations(self):
        return self._observations

    @property
    def plotter(self):
        try:
            return self._plotter
        except AttributeError:
            return self.build_plotter()

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

    @property
    def TeX_info(self):
        try:
            return self._TeX_info
        except AttributeError:
            return self.build_TeX_info()

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

    def build_plotter(self):
        obs = self.observations
        yfit = self(self.observations.raw.x)
        tex_info = self.TeX_info

        plotter = FitFunctionPlot(
            obs, yfit, tex_info, fitfunction_name=self.__class__.__name__
        )
        self._plotter = plotter
        return plotter

    def build_TeX_info(self):

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
            chisq_dof=self.chisq_dof,
            initial_guess_info=self.initial_guess_info,
        )
        self._TeX_info = tex_info
        return tex_info

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
        r"""Set the observed values we'll actually use in the fit by applying
        limits to xobs_raw and yobs_raw and checking for finite values.

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

    def make_fit_old(self, **kwargs):
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
        absolute_sigma = kwargs.pop("absolute_sigma", True)

        if not absolute_sigma:
            raise ValueError(
                "Always use `absolute_sigma` so we can calcualte chisq_dof and then renormalize here."
            )

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

        xdata = self.observations.used.x
        ydata = self.observations.used.y
        sigma = self.observations.used.w

        try:
            result = curve_fit(
                self.function,
                xdata,
                ydata,
                p0=p0,
                sigma=sigma,
                method=method,
                loss=loss,
                max_nfev=max_nfev,
                f_scale=f_scale,
                **kwargs,
            )
        except (RuntimeError, ValueError) as e:
            return e

        popt, pcov = result[:2]
        #         psigma = np.sqrt(np.diag(pcov))

        dof = ydata.size - len(p0)
        chisq_dof = np.inf  # Divide by zero => infinity
        if dof:
            r = (self.function(xdata, *popt) - ydata) / sigma
            chisq_dof = (r ** 2).sum() / dof

        pcov = pcov * chisq_dof
        psigma = np.sqrt(np.diag(pcov))
        self._popt = list(zip(self.argnames, popt))
        self._psigma = list(zip(self.argnames, psigma))
        self._pcov = pcov
        #         self._chisq_dof = chisq_dof
        all_chisq = ChisqPerDegreeOfFreedom(chisq_dof, np.nan)
        self._chisq_dof = all_chisq

    def _run_least_squares(self, **kwargs):
        p0 = kwargs.pop("p0", self.p0)
        bounds = kwargs.pop("bounds", (-np.inf, np.inf))
        method = kwargs.pop("method", "trf")
        loss = kwargs.pop("loss", "huber")
        max_nfev = kwargs.pop("max_nfev", 10000)
        f_scale = kwargs.pop("f_scale", 0.1)
        jac = kwargs.pop("jac", "2-point")

        # Copied from `curve_fit` (20200527)
        if p0 is None:
            # determine number of parameters by inspecting the function
            from scipy._lib._util import getargspec_no_self as _getargspec

            args, varargs, varkw, defaults = _getargspec(self.function)
            if len(args) < 2:
                raise ValueError("Unable to determine number of fit parameters.")
            n = len(args) - 1
        else:
            p0 = np.atleast_1d(p0)
            n = p0.size

        # Copied from `curve_fit` (20200527)
        lb, ub = prepare_bounds(bounds, n)
        if p0 is None:
            p0 = _initialize_feasible(lb, ub)

        if "args" in kwargs:
            raise ValueError(
                "Adopted `curve_fit` convention for which'args' is not a supported keyword argument."
            )

        xdata = self.observations.used.x
        ydata = self.observations.used.y
        sigma = self.observations.used.w

        # Copied from `curve_fit` (20200527)
        # Determine type of sigma
        if sigma is not None:
            sigma = np.asarray(sigma)
            # sigma = sigma / np.nansum(sigma)

            # if 1-d, sigma are errors, define transform = 1/sigma
            if sigma.shape == (ydata.size,):
                transform = 1.0 / sigma
            # if 2-d, sigma is the covariance matrix,
            # define transform = L such that L L^T = C
            elif sigma.shape == (ydata.size, ydata.size):
                try:
                    # scipy.linalg.cholesky requires lower=True to return L L^T = A
                    transform = cholesky(sigma, lower=True)
                except LinAlgError:
                    raise ValueError("`sigma` must be positive definite.")
            else:
                raise ValueError("`sigma` has incorrect shape.")
        else:
            transform = None

        # Copied from `curve_fit` (20200527)
        loss_func = _wrap_func(self.function, xdata, ydata, transform)
        # Need to call `_wrap_jac` because we already build loss function
        # with `_wrap_func`.
        if callable(jac):
            jac = _wrap_jac(jac, xdata, transform)

        res = least_squares(
            loss_func,
            p0,
            jac=jac,
            bounds=bounds,
            method=method,
            loss=loss,
            max_nfev=max_nfev,
            f_scale=f_scale,
            **kwargs,
        )

        if not res.success:
            raise RuntimeError("Optimal parameters not found: " + res.message)

        return res, p0

    def _calc_popt_pcov_psigma_chisq(self, res, p0):
        xdata = self.observations.used.x
        ydata = self.observations.used.y
        sigma = self.observations.used.w
        # `cost` is the robust loss, i.e. residuals passed through loss funciton.
        ysize = len(res.fun)
        cost = 2 * res.cost  # res.cost is half sum of squares!
        popt = res.x

        # Linear chisq_dof value.
        dof = ydata.size - len(p0)
        chisq_dof = np.inf  # Divide by zero => infinity
        if dof:
            r = (self.function(xdata, *popt) - ydata) / sigma
            chisq_dof = (r ** 2).sum() / dof

        # Do Moore-Penrose inverse discarding zero singular values.
        _, s, VT = svd(res.jac, full_matrices=False)
        threshold = np.finfo(float).eps * max(res.jac.shape) * s[0]
        s = s[s > threshold]
        VT = VT[: s.size]
        pcov = np.dot(VT.T / s ** 2, VT)

        warn_cov = False
        if ysize > p0.size:
            # Cost is robust residuals, so this is robust chisq per dof.
            s_sq = cost / (ysize - p0.size)
            pcov = pcov * s_sq
        else:
            s_sq = np.nan
            pcov.fill(np.inf)
            warn_cov = True

        if warn_cov:
            warnings.warn(
                "Covariance of the parameters could not be estimated",
                category=OptimizeWarning,
            )

        psigma = np.sqrt(np.diag(pcov))

        # Based on `curve_fit`'s `absolute_sigma` documentation and reading
        # `least_square`, `s_sq` should be chisq_nu based on robust residuals
        # that account for `f_scale`(20200527).
        all_chisq = ChisqPerDegreeOfFreedom(chisq_dof, s_sq)

        return popt, pcov, psigma, all_chisq

    def make_fit(self, **kwargs):
        f"""Fit the function with the independent values `xobs` and dependent
        values `yobs` using `least_squares` and returning the `OptimizeResult`
        object, but treating weights as in `curve_fit`.

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
        try:
            assert self.sufficient_data  # Check we have enough data to fit.
        except ValueError as e:
            return e

        try:
            res, p0 = self._run_least_squares(**kwargs)
        except (RuntimeError, ValueError) as e:
            print("fitting failed", flush=True)
            return e

        popt, pcov, psigma, all_chisq = self._calc_popt_pcov_psigma_chisq(res, p0)

        self._popt = list(zip(self.argnames, popt))
        self._psigma = list(zip(self.argnames, psigma))
        self._pcov = pcov
        self._chisq_dof = all_chisq
        self._fit_result = res
