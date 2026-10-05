#!/usr/bin/env python
r"""Base classes used to implement specific fit functions.

The :class:`FitFunction` abstract base class handles selecting the
observations to include in a fit, running SciPy optimizers and
providing convenient plotting helpers.  Subclasses need only define
the functional form and an initial parameter guess.
"""

__all__ = [
    "FitFunctionError",
    "InsufficientDataError",
    "FitFailedError",
    "InvalidParameterError",
    "FitFunctionMeta",
    "FitFunction",
]

import logging  # noqa: F401
import warnings

import numpy as np
import pandas as pd

from abc import ABC, abstractmethod
from collections import namedtuple
from inspect import getfullargspec
from docstring_inheritance import NumpyDocstringInheritanceMeta

from scipy.optimize import least_squares, OptimizeWarning

try:
    from scipy.optimize._minpack_py import (
        _wrap_func,
        _wrap_jac,
        _initialize_feasible,
    )
except ImportError:  # pragma: no cover - fall back for older SciPy versions
    from scipy.optimize.minpack import (
        _wrap_func,
        _wrap_jac,
        _initialize_feasible,
    )
from scipy.optimize._lsq.least_squares import prepare_bounds
from scipy.linalg import svd, cholesky, LinAlgError

from .tex_info import TeXinfo
from .plots import FFPlot

_Observations = namedtuple("_Observations", "x,y,w")
_UsedRawObs = namedtuple("_UsedRawObs", "used,raw,tk_observed")
_InitialGuessInfo = namedtuple("_InitialGuessInfo", "p0,bounds")
_ChisqPerDegreeOfFreedom = namedtuple("_ChisqPerDegreeOfFreedom", "linear,robust")
_FitBounds = namedtuple("_FitBounds", "lower,upper")
_INSUFFICIENT_DATA = "There is insufficient data to fit the model."


class FitFunctionError(Exception):
    """Base exception for fit function errors."""

    pass


class InsufficientDataError(FitFunctionError):
    """Raised when there is insufficient data to perform the fit."""

    pass


class FitFailedError(FitFunctionError):
    """Raised when the fitting algorithm fails to converge."""

    pass


class InvalidParameterError(FitFunctionError):
    """Raised when invalid parameters are provided to fit functions."""

    pass


# Combine ABC and docstring inheritance metaclasses. ABCMeta comes first:
# docstring-inheritance 3.x binds NumpyDocstringInheritanceMeta to plain
# ``type`` when its switch is off, and ``type`` may not precede its subclass
# ABCMeta in a list of bases.
class FitFunctionMeta(type(ABC), NumpyDocstringInheritanceMeta):
    """Metaclass combining ABC and docstring inheritance."""

    pass


class FitFunction(ABC, metaclass=FitFunctionMeta):
    r"""Assuming that you don't want special formatting, call order is:

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
        """Initialize fit function with observed data.

        Parameters
        ----------
        xobs : array-like
            Observed x values (independent variable).
            Shape must match yobs.
        yobs : array-like
            Observed y values (dependent variable).
            Shape must match xobs.
        xmin, xmax : float, optional
            Range limits for x used in fitting. Values outside
            this range are excluded from the fit. All boundaries
            are inclusive (>= or <=).
        xoutside : tuple(float, float), optional
            Include only data outside this range in the fit.
            Useful for excluding a central region. Format: (lower, upper)
            where lower < upper.
        ymin, ymax : float, optional
            Range limits for y used in fitting. Values outside
            this range are excluded from the fit.
        youtside : tuple(float, float), optional
            Include only data outside this range.
            Format: (lower, upper) where lower < upper.
        weights : array-like, optional
            Uncertainties (1-sigma) associated with y values.
            Used for weighted least squares fitting. If 1-d array,
            interpreted as diagonal covariance matrix. If 2-d,
            must be positive definite covariance matrix.
        wmin, wmax : float, optional
            Weight limits. Observations with weights outside
            this range are excluded from the fit.
        logx, logy : bool, default False
            Whether to interpret x or y on a log10 scale.
            If logy=True, weight selection uses w/(y*ln(10))
            for proper error propagation in log space.

        Notes
        -----
        The fitting procedure uses scipy.optimize.least_squares
        with robust loss functions (Huber by default) to handle
        outliers. The initial parameter guess is provided by the
        p0 property, which must be implemented by subclasses.

        All subclasses inherit this documentation automatically
        through the docstring-inheritance metaclass.

        Examples
        --------
        Fit a Gaussian with mu=1, sigma=0.8, A=3 plus seeded noise and
        recover those parameters:

        >>> import numpy as np
        >>> from solarwindpy.fitfunctions.gaussians import Gaussian
        >>> rng = np.random.default_rng(0)
        >>> x = np.linspace(-5, 5, 100)
        >>> y = 3 * np.exp(-0.5 * ((x - 1) / 0.8) ** 2) + rng.normal(0, 0.1, 100)
        >>> fit = Gaussian(x, y, xmin=-3, xmax=4)
        >>> fit.make_fit()
        >>> {k: round(float(v), 1) for k, v in fit.popt.items()}
        {'mu': 1.0, 'sigma': 0.8, 'A': 3.0}

        See Also
        --------
        make_fit : Execute the fitting procedure
        popt : Access optimized parameters
        rsq : Calculate coefficient of determination
        """

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
        """Evaluate the fitted model at ``x``."""

        # Design decision: Keep interface simple - __call__ evaluates the fitted
        # function using stored parameters. For parameter overrides, users should
        # call self.function(x, param1, param2, ...) directly.

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
        """Create a module-level logger for the instance."""

        logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._logger = logger

    @property
    @abstractmethod
    def function(self):
        r"""Get the function that`curve_fit` fits.

        The function is set at instantiation. It doesn't make sense to change
        it unless you redefine the entire FitFunction, so there is no `new`
        kwarg.
        """
        pass

    @property
    @abstractmethod
    def p0(self):
        r"""The initial guess for the FitFunction, or None.

        This docstring states the contract every subclass's ``p0`` follows.

        Returns
        -------
        list of float or None
            One finite guess per parameter, in :attr:`argnames` order. When
            the data make a guess impossible (an empty region, an undefined
            slope, a zero total weight, and so on), ``p0`` returns ``None``
            rather than a guess holding NaN or infinity, and :meth:`make_fit`
            starts from the feasible default for the bounds: ones when
            unbounded, as :func:`scipy.optimize.curve_fit` does.

        Raises
        ------
        ~solarwindpy.fitfunctions.core.InsufficientDataError
            If fewer observations are used than the model has parameters.

        Notes
        -----
        :meth:`make_fit` rejects a guess holding NaN or infinity, whether it
        comes from ``p0`` or from the caller's ``p0=``, with a ``ValueError``
        naming the class and each offending parameter.
        """
        pass

    @property
    @abstractmethod
    def TeX_function(self):
        r"""Function written in LaTeX."""
        pass

    @property
    def argnames(self):
        r"""The names of the actual function arguments pulled by getfullargspec."""
        return self._argnames

    @property
    def fit_bounds(self):
        r"""Bounds used when running the fit."""
        return dict(self._fit_bounds)

    @property
    def chisq_dof(self):
        r"""Chisq per degree of freedom :math:`\chi^2_\nu`.

        If None, not calculated by `make_fit_old`. If `np.nan`, fit failed.
        """
        try:
            return self._chisq_dof
        except AttributeError:
            return None

    @property
    def dof(self):
        r"""Degrees of freedom in the fit."""
        return self.observations.used.y.size - len(self.argnames)

    @property
    def fit_result(self):
        return self._fit_result

    @property
    def initial_guess_info(self):
        r"""Initial guess and bounds for each parameter, or None.

        Returns
        -------
        dict or None
            ``{name: _InitialGuessInfo(p0, bounds)}``, or None when no initial
            guess was made (``p0`` is None) or no fit has set the bounds.
        """
        try:
            p0 = self.p0
            bounds = self.fit_bounds
        except AttributeError:
            return None
        if p0 is None:
            return None

        names = self.argnames
        info = {
            name: _InitialGuessInfo(guess, tuple(bounds[name]))
            for name, guess in zip(names, p0)
        }

        return info

    @property
    def nobs(self):
        r"""The total number of observations used in the fit."""
        return self.observations.tk_observed.sum()

    @property
    def observations(self):
        return self._observations

    @property
    def plotter(self):
        return self._plotter

    @property
    def popt(self):
        r"""Optimized fit parameters."""
        return dict(self._popt)

    @property
    def psigma(self):
        return dict(self._psigma)

    @property
    def combined_popt_psigma(self):
        r"""Return optimized parameters and uncertainties as a DataFrame.

        Returns
        -------
        pd.DataFrame
            DataFrame with columns 'popt' and 'psigma', indexed by parameter names.
            Relative uncertainty can be computed as: df['psigma'] / df['popt']
        """
        return pd.DataFrame({"popt": self.popt, "psigma": self.psigma})

    @property
    def pcov(self):
        r"""Returns a copy so that the matrix isn't accidentally edited."""
        return self._pcov.copy()

    @property
    def rsq(self):
        r"""Coefficient of determination.

        Source: <en.wikipedia.org/wiki/Coefficient_of_determination#Definitions>

        Returns
        -------
        float
            ``1 - SS_res / SS_tot``. When the used ``y`` have no spread (a single
            point, or constant data), ``SS_tot = 0`` and R² is undefined, so
            ``nan`` is returned without a divide-by-zero warning.
        """
        y = self.observations.used.y
        if np.ptp(y) == 0:
            return np.nan

        ybar = y.mean()
        yfit = self(self.observations.used.x)
        sum_squares_total = ((y - ybar) ** 2).sum()
        sum_squares_residual = ((y - yfit) ** 2).sum()
        rsq = 1 - (sum_squares_residual / sum_squares_total)

        return rsq

    @property
    def sufficient_data(self):
        r"""Ensure that we can fit the data before doing any computations."""
        chk = self.nobs >= len(self.argnames)
        if not chk:
            raise InsufficientDataError(_INSUFFICIENT_DATA)
        else:
            return True

    def _require_sufficient_data(self):
        r"""Raise :class:`InsufficientDataError` unless the data can be fit.

        The explicit form of ``assert self.sufficient_data``, which ``python
        -O`` removes. It also covers a subclass whose :attr:`sufficient_data`
        returns False instead of raising.
        """
        if not self.sufficient_data:
            raise InsufficientDataError(_INSUFFICIENT_DATA)

    def _feasible_p0(self, bounds=(-np.inf, np.inf)):
        r"""The feasible default guess for ``bounds``, used when ``p0`` is None.

        Parameters
        ----------
        bounds : 2-tuple or dict, optional
            As accepted by :meth:`make_fit`.

        Returns
        -------
        numpy.ndarray
            One value per parameter, as :func:`scipy.optimize.curve_fit`
            chooses: ones when unbounded, otherwise a point inside the bounds.
        """
        # The fit parameters are the function's arguments after x.
        n = len(self.argnames)
        if n < 1:
            raise ValueError("Unable to determine number of fit parameters.")
        lb, ub = prepare_bounds(self._bounds_array(bounds), n)
        return _initialize_feasible(lb, ub)

    def _bounds_array(self, bounds):
        r"""Convert ``bounds`` stored as ``{name: (lower, upper)}`` to an array."""
        if isinstance(bounds, dict):
            # Monkey patch to work with bounds being stored as
            # dict for TeX_info. (20201202)
            bounds = [bounds[k] for k in self.argnames]
            bounds = np.array(bounds).T
        return bounds

    def _reject_nonfinite_p0(self, p0):
        r"""Raise ``ValueError`` naming each parameter whose guess is NaN or inf.

        Without this, SciPy reports a NaN guess as "Initial guess is outside
        of provided bounds", which names neither the class nor the parameter.
        """
        bad = ~np.isfinite(np.asarray(p0, dtype=float))
        if not bad.any():
            return
        names = (
            self.argnames
            if len(self.argnames) == p0.size
            else [f"p0[{i}]" for i in range(p0.size)]
        )
        detail = ", ".join(f"{k}={v}" for k, v, b in zip(names, p0, bad) if b)
        raise ValueError(
            f"{self.__class__.__name__} initial guess is not finite: {detail}. "
            "A p0 that cannot make a guess returns None, and the fit then "
            "starts from the feasible default."
        )

    @property
    def TeX_info(self):
        return self._TeX_info

    def _clean_raw_obs(self, xobs, yobs, weights):
        r"""Set the raw x- and y-values along with weights for the fit.

        Doesn't account for extrema, finite data, etc.
        """
        xobs = np.asarray(xobs)
        yobs = np.asarray(yobs)
        if weights is not None:
            weights = np.asarray(weights)

        if xobs.shape != yobs.shape:
            raise InvalidParameterError(f"""xobs and yobs must have the same shape.
xobs: {xobs.shape}, yobs: {yobs.shape}""")

        if weights is not None and weights.shape != xobs.shape:
            raise InvalidParameterError(f"""weights and xobs must have the same shape.
weights: {weights.shape}, xobs: {xobs.shape}""")

        return xobs, yobs, weights

    def _build_one_obs_mask(self, axis, x, xmin, xmax):
        """Build observation mask with in-place operations for efficiency."""
        mask = np.isfinite(x)

        if xmin is not None:
            mask &= x >= xmin  # In-place AND instead of creating xmin_mask

        if xmax is not None:
            mask &= x <= xmax  # In-place AND instead of creating xmax_mask

        return mask

    def _build_outside_mask(self, axis, x, outside):
        """Build outside mask with in-place operations for efficiency."""
        if outside is None:
            return np.full_like(x, True, dtype=bool)

        lower, upper = outside
        assert lower < upper
        mask = x <= lower
        mask |= x >= upper  # In-place OR instead of creating separate u_mask
        return mask

    def _set_argnames(self):
        r"""Set the arguments of the function/

        Assume that the first is dependent variable.
        Should be called after function is set.
        """
        args = getfullargspec(self.function).args[1:]
        self._argnames = args

    def build_plotter(self):
        obs = self.observations
        try:
            yfit = self(self.observations.raw.x)
        except AttributeError:
            yfit = np.full_like(self.observations.raw.x, np.nan)
        tex_info = self.TeX_info
        fit_result = self.fit_result

        plotter = FFPlot(
            obs,
            yfit,
            tex_info,
            fit_result,
            fitfunction_name=self.__class__.__name__,
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
            self.chisq_dof,
            self.rsq,
            initial_guess_info=self.initial_guess_info,
        )
        self._TeX_info = tex_info
        return tex_info

    def residuals(self, pct=False, use_all=False):
        r"""
        Calculate fit residuals.

        Parameters
        ----------
        pct : bool, default=False
            If True, return percentage residuals.
        use_all : bool, default=False
            If True, calculate residuals for all input data including
            points excluded by constraints (xmin, xmax, etc.) passed
            during initialization.
            If False (default), calculate only for points used in fit.

        Returns
        -------
        numpy.ndarray
            Residuals as observed - fitted.

        Examples
        --------
        >>> import numpy as np
        >>> from solarwindpy.fitfunctions.gaussians import Gaussian
        >>> x = np.linspace(0, 10, 101)
        >>> y = 4 * np.exp(-0.5 * ((x - 5) / 1) ** 2)
        >>> # Create FitFunction with constraints
        >>> ff = Gaussian(x, y, xmin=3, xmax=7)
        >>> ff.make_fit()

        >>> # Residuals for fitted region only
        >>> r_fit = ff.residuals()
        >>> bool(r_fit.size == ((x >= 3) & (x <= 7)).sum())
        True

        >>> # Residuals for all original data
        >>> r_all = ff.residuals(use_all=True)
        >>> r_all.size == x.size
        True

        >>> # Percentage residuals
        >>> r_pct = ff.residuals(pct=True)

        Notes
        -----
        Addresses TODO: "calculate with all values...including those
        excluded by set_extrema" (though set_extrema doesn't exist -
        constraints are passed in __init__).
        """
        if use_all:
            # Use all original observations
            x = self.observations.raw.x
            y = self.observations.raw.y
        else:
            # Use only observations included in fit (default)
            x = self.observations.used.x
            y = self.observations.used.y

        # Calculate residuals (observed - fitted)
        fitted_values = self(x)
        r = y - fitted_values

        if pct:
            # Avoid division by zero
            with np.errstate(divide="ignore", invalid="ignore"):
                r = 100.0 * (r / fitted_values)
                r[fitted_values == 0] = np.nan

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
        r"""Set the observed values we'll actually use in the fit.

        By applying limits to xobs_raw and yobs_raw and checking for finite values.

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

        used = _Observations(xobs, yobs, weights)
        raw = _Observations(xobs_raw, yobs_raw, weights_raw)
        usedrawobs = _UsedRawObs(used, raw, mask)
        self._observations = usedrawobs

    def _run_least_squares(self, **kwargs):
        """Execute :func:`scipy.optimize.least_squares` with defaults."""

        p0 = kwargs.pop("p0", self.p0)
        bounds = kwargs.pop("bounds", (-np.inf, np.inf))
        method = kwargs.pop("method", "trf")
        loss = kwargs.pop("loss", "huber")
        max_nfev = kwargs.pop("max_nfev", 10000)
        f_scale = kwargs.pop("f_scale", 0.1)
        jac = kwargs.pop("jac", "2-point")

        bounds = self._bounds_array(bounds)

        # Adapted from `curve_fit` lines 704 and 715 (20200527)
        if p0 is None:
            p0 = self._feasible_p0(bounds)
        else:
            p0 = np.atleast_1d(p0)
            self._reject_nonfinite_p0(p0)

        lb, ub = prepare_bounds(bounds, p0.size)

        if "args" in kwargs:
            raise ValueError(
                "Adopted `curve_fit` convention for which'args' is not a supported keyword argument."
            )

        xdata = self.observations.used.x
        ydata = self.observations.used.y
        sigma = self.observations.used.w

        # Copied from `curve_fit` line 749 (20200527)
        # Determine type of sigma
        if sigma is not None:
            sigma = np.asarray(sigma)

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

        # Copied from `curve_fit` line 769 (20200527)
        loss_func = _wrap_func(self.function, xdata, ydata, transform)
        # Already define default `jac` with `kwargs`. Don't need ELSE clause.
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
            raise FitFailedError("Optimal parameters not found: " + res.message)

        fit_bounds = np.concatenate([lb, ub]).reshape((2, -1)).T
        fit_bounds = {k: _FitBounds(*b) for k, b in zip(self.argnames, fit_bounds)}
        fit_bounds = tuple(fit_bounds.items())
        self._fit_bounds = fit_bounds

        return res, p0

    def _calc_popt_pcov_psigma_chisq(self, res, p0):
        """Compute optimized parameters and statistics from the result."""

        xdata = self.observations.used.x
        ydata = self.observations.used.y
        sigma = self.observations.used.w

        # The following is from `curve_fit` line 801 and following. (20200625)
        # `cost` is the robust loss, i.e. residuals passed through loss funciton.
        ysize = len(res.fun)
        cost = 2 * res.cost  # res.cost is half sum of squares!
        popt = res.x

        # Linear chisq_dof value.
        dof = ydata.size - len(p0)
        chisq_dof = np.inf  # Divide by zero => infinity
        if dof:
            r = self.function(xdata, *popt) - ydata
            if sigma is not None:
                r /= sigma
            chisq_dof = (r**2).sum() / dof

        # Do Moore-Penrose inverse discarding zero singular values.
        _, s, VT = svd(res.jac, full_matrices=False)
        threshold = np.finfo(float).eps * max(res.jac.shape) * s[0]
        s = s[s > threshold]
        VT = VT[: s.size]
        pcov = np.dot(VT.T / (s**2), VT)

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
        all_chisq = _ChisqPerDegreeOfFreedom(chisq_dof, s_sq)

        return popt, pcov, psigma, all_chisq

    def make_fit(self, return_exception=False, **kwargs):
        """Fit the function with the independent `xobs` and dependent `yobs`.

        Uses `least_squares` and returns the `OptimizeResult` object, but
        treats weights as in `curve_fit`.

        Parameters
        ----------
        return_exception: bool
            If True, return exceptions from fitting routine, instead of raising.
            This is useful when looping through many fits and wanting to
            identify failed fits after the fact.

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
            self._require_sufficient_data()
        except (ValueError, InsufficientDataError) as e:
            if return_exception:
                return e
            else:
                raise e

        absolute_sigma = kwargs.pop("absolute_sigma", False)
        if absolute_sigma:
            raise NotImplementedError("We want to rescale fit errors by chisq_dof")

        try:
            res, p0 = self._run_least_squares(**kwargs)
        except (RuntimeError, ValueError, FitFailedError) as e:
            if return_exception:
                return e
            else:
                raise

        popt, pcov, psigma, all_chisq = self._calc_popt_pcov_psigma_chisq(res, p0)

        self._popt = list(zip(self.argnames, popt))
        self._psigma = list(zip(self.argnames, psigma))
        self._pcov = pcov
        self._chisq_dof = all_chisq
        self._fit_result = res

        self.build_TeX_info()
        self.build_plotter()
