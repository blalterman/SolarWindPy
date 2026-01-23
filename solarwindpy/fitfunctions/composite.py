r"""Composite fit functions combining Gaussians with Heaviside step functions.

This module provides fit functions that combine Gaussian distributions with
Heaviside step functions for modeling distributions with sharp transitions
or truncations.

Classes
-------
GaussianPlusHeavySide
    Gaussian peak with additive step function offset.
GaussianTimesHeavySide
    Gaussian truncated at a threshold (zero below x0).
GaussianTimesHeavySidePlusHeavySide
    Gaussian for x >= x0 with constant plateau for x < x0.
"""

from __future__ import annotations

import numpy as np

from .core import FitFunction


class GaussianPlusHeavySide(FitFunction):
    r"""Gaussian plus Heaviside step function for offset peak modeling.

    Models a Gaussian peak with a step function that adds an offset
    below a threshold:

    .. math::

        f(x) = A \cdot e^{-\frac{1}{2}\left(\frac{x-\mu}{\sigma}\right)^2}
               + y_1 \cdot H(x_0 - x) + y_0

    where :math:`H(z)` is the Heaviside step function.

    Parameters
    ----------
    xobs : array-like
        Independent variable observations.
    yobs : array-like
        Dependent variable observations.
    **kwargs
        Additional arguments passed to :class:`FitFunction`.

    Attributes
    ----------
    x0 : float
        Transition x-coordinate (fitted parameter).
    y0 : float
        Constant offset applied everywhere (fitted parameter).
    y1 : float
        Additional offset for x < x0 (fitted parameter).
    mu : float
        Gaussian mean (fitted parameter).
    sigma : float
        Gaussian standard deviation (fitted parameter).
    A : float
        Gaussian amplitude (fitted parameter).

    Examples
    --------
    >>> import numpy as np
    >>> from solarwindpy.fitfunctions import GaussianPlusHeavySide
    >>> x = np.linspace(0, 10, 100)
    >>> # Gaussian peak at mu=5 with step down at x0=2
    >>> y = 4*np.exp(-0.5*((x-5)/1)**2) + 3*np.heaviside(2-x, 0.5) + 1
    >>> fit = GaussianPlusHeavySide(x, y)
    >>> fit.make_fit()
    >>> print(f"mu={fit.popt['mu']:.2f}, x0={fit.popt['x0']:.2f}")
    mu=5.00, x0=2.00
    """

    def __init__(self, xobs, yobs, **kwargs):
        super().__init__(xobs, yobs, **kwargs)

    @property
    def function(self):
        r"""The Gaussian plus Heaviside function.

        Returns
        -------
        callable
            Function with signature ``f(x, x0, y0, y1, mu, sigma, A)``.
        """

        def gaussian_heavy_side(x, x0, y0, y1, mu, sigma, A):
            r"""Evaluate Gaussian plus Heaviside model.

            Parameters
            ----------
            x : array-like
                Independent variable values.
            x0 : float
                Transition x-coordinate.
            y0 : float
                Constant offset everywhere.
            y1 : float
                Additional offset for x < x0.
            mu : float
                Gaussian mean.
            sigma : float
                Gaussian standard deviation.
            A : float
                Gaussian amplitude.

            Returns
            -------
            numpy.ndarray
                Model values at x.
            """

            def gaussian(x, mu, sigma, A):
                arg = -0.5 * (((x - mu) / sigma) ** 2.0)
                return A * np.exp(arg)

            def heavy_side(x, x0, y0, y1):
                out = (y1 * np.heaviside(x0 - x, 0.5)) + y0
                return out

            out = gaussian(x, mu, sigma, A) + heavy_side(x, x0, y0, y1)
            return out

        return gaussian_heavy_side

    @property
    def p0(self) -> list:
        r"""Calculate initial parameter guess.

        The initial guess is derived from:
        - Weighted mean and std for Gaussian parameters
        - x0 estimated as 0.75 * mean
        - y0 = 0, y1 = 0.8 * peak
        - Gaussian parameters recalculated for x > x0

        Returns
        -------
        list
            Initial guesses as [x0, y0, y1, mu, sigma, A].

        Raises
        ------
        AssertionError
            If insufficient data for estimation.

        Notes
        -----
        # TODO: Convert to data-driven p0 estimation (see GH issue #XX)
        """
        assert self.sufficient_data

        x, y = self.observations.used.x, self.observations.used.y
        mean = (x * y).sum() / y.sum()
        std = np.sqrt(((x - mean) ** 2.0 * y).sum() / y.sum())

        try:
            peak = y.max()
        except ValueError as e:
            chk = (
                r"zero-size array to reduction operation maximum "
                "which has no identity"
            )
            if str(e).startswith(chk):
                msg = (
                    "There is no maximum of a zero-size array. "
                    "Please check input data."
                )
                raise ValueError(msg)
            raise

        x0 = 0.75 * mean
        y1 = 0.8 * peak

        tk = x > x0
        x, y = x[tk], y[tk]
        mean = (x * y).sum() / y.sum()
        std = np.sqrt(((x - mean) ** 2.0 * y).sum() / y.sum())

        p0 = [x0, 0, y1, mean, std, peak]
        return p0

    @property
    def TeX_function(self) -> str:
        r"""LaTeX representation of the model.

        Returns
        -------
        str
            Multi-line LaTeX string describing the function.
        """
        tex = "\n".join(
            [
                r"f(x)=A \cdot e^{-\frac{1}{2} (\frac{x-\mu}{\sigma})^2} +",
                r"\left(y_1 \cdot H(x_0 - x) + y_0\right)",
            ]
        )
        return tex


class GaussianTimesHeavySide(FitFunction):
    r"""Gaussian multiplied by Heaviside for truncated distribution modeling.

    Models a Gaussian that is truncated (zeroed) below a threshold:

    .. math::

        f(x) = A \cdot e^{-\frac{1}{2}\left(\frac{x-\mu}{\sigma}\right)^2}
               \cdot H(x - x_0)

    where :math:`H(z)` is the Heaviside step function with :math:`H(0) = 1`.

    Parameters
    ----------
    xobs : array-like
        Independent variable observations.
    yobs : array-like
        Dependent variable observations.
    guess_x0 : float, optional
        Initial guess for the transition x-coordinate. If None, must be
        provided for fitting to work properly.
    **kwargs
        Additional arguments passed to :class:`FitFunction`.

    Attributes
    ----------
    x0 : float
        Transition x-coordinate (fitted parameter).
    mu : float
        Gaussian mean (fitted parameter).
    sigma : float
        Gaussian standard deviation (fitted parameter).
    A : float
        Gaussian amplitude (fitted parameter).

    Examples
    --------
    >>> import numpy as np
    >>> from solarwindpy.fitfunctions import GaussianTimesHeavySide
    >>> x = np.linspace(0, 10, 100)
    >>> # Truncated Gaussian: zero for x < 3
    >>> y = 4*np.exp(-0.5*((x-5)/1)**2) * np.heaviside(x-3, 1.0)
    >>> fit = GaussianTimesHeavySide(x, y, guess_x0=3.0)
    >>> fit.make_fit()
    >>> print(f"x0={fit.popt['x0']:.2f}, mu={fit.popt['mu']:.2f}")
    x0=3.00, mu=5.00
    """

    def __init__(self, xobs, yobs, guess_x0=None, **kwargs):
        if guess_x0 is None:
            raise ValueError(
                "guess_x0 is required for GaussianTimesHeavySide. "
                "Provide an initial estimate for the transition x-coordinate."
            )
        super().__init__(xobs, yobs, **kwargs)
        self._guess_x0 = guess_x0

    @property
    def guess_x0(self) -> float:
        r"""Initial guess for transition x-coordinate used in p0 calculation."""
        return self._guess_x0

    @property
    def function(self):
        r"""The Gaussian times Heaviside function.

        Returns
        -------
        callable
            Function with signature ``f(x, x0, mu, sigma, A)``.
        """

        def gaussian_heavy_side(x, x0, mu, sigma, A):
            r"""Evaluate Gaussian times Heaviside model.

            Parameters
            ----------
            x : array-like
                Independent variable values.
            x0 : float
                Transition x-coordinate.
            mu : float
                Gaussian mean.
            sigma : float
                Gaussian standard deviation.
            A : float
                Gaussian amplitude.

            Returns
            -------
            numpy.ndarray
                Model values at x.
            """

            def gaussian(x, mu, sigma, A):
                arg = -0.5 * (((x - mu) / sigma) ** 2.0)
                return A * np.exp(arg)

            out = gaussian(x, mu, sigma, A) * np.heaviside(x - x0, 1.0)
            return out

        return gaussian_heavy_side

    @property
    def p0(self) -> list:
        r"""Calculate initial parameter guess.

        The initial guess is derived from:
        - ``guess_x0`` for x0
        - Weighted mean and std for Gaussian parameters (using x > x0)
        - Peak amplitude from data

        Returns
        -------
        list
            Initial guesses as [x0, mu, sigma, A].

        Raises
        ------
        AssertionError
            If insufficient data for estimation.

        Notes
        -----
        # TODO: Convert to data-driven p0 estimation (see GH issue #XX)
        """
        assert self.sufficient_data

        x, y = self.observations.used.x, self.observations.used.y
        x0 = self.guess_x0
        tk = x > x0

        x, y = x[tk], y[tk]
        mean = (x * y).sum() / y.sum()
        std = np.sqrt(((x - mean) ** 2.0 * y).sum() / y.sum())

        try:
            peak = y.max()
        except ValueError as e:
            chk = (
                r"zero-size array to reduction operation maximum "
                "which has no identity"
            )
            if str(e).startswith(chk):
                msg = (
                    "There is no maximum of a zero-size array. "
                    "Please check input data."
                )
                raise ValueError(msg)
            raise

        p0 = [x0, mean, std, peak]
        return p0

    @property
    def TeX_function(self) -> str:
        r"""LaTeX representation of the model.

        Returns
        -------
        str
            LaTeX string describing the function.
        """
        tex = (
            r"f(x)=A \cdot e^{-\frac{1}{2} (\frac{x-\mu}{\sigma})^2} \times H(x - x_0)"
        )
        return tex


class GaussianTimesHeavySidePlusHeavySide(FitFunction):
    r"""Gaussian times Heaviside plus Heaviside for plateau-to-peak modeling.

    Models a distribution that transitions from a constant plateau to a
    Gaussian peak:

    .. math::

        f(x) = A \cdot e^{-\frac{1}{2}\left(\frac{x-\mu}{\sigma}\right)^2}
               \cdot H(x - x_0) + y_1 \cdot H(x_0 - x)

    where :math:`H(z)` is the Heaviside step function.

    This gives:
    - Constant :math:`y_1` for :math:`x < x_0`
    - Gaussian for :math:`x > x_0`
    - Transition at :math:`x = x_0`

    Parameters
    ----------
    xobs : array-like
        Independent variable observations.
    yobs : array-like
        Dependent variable observations.
    guess_x0 : float, optional
        Initial guess for the transition x-coordinate. If None, must be
        provided for fitting to work properly.
    **kwargs
        Additional arguments passed to :class:`FitFunction`.

    Attributes
    ----------
    x0 : float
        Transition x-coordinate (fitted parameter).
    y1 : float
        Constant plateau value for x < x0 (fitted parameter).
    mu : float
        Gaussian mean (fitted parameter).
    sigma : float
        Gaussian standard deviation (fitted parameter).
    A : float
        Gaussian amplitude (fitted parameter).

    Examples
    --------
    >>> import numpy as np
    >>> from solarwindpy.fitfunctions import GaussianTimesHeavySidePlusHeavySide
    >>> x = np.linspace(0, 10, 100)
    >>> # Plateau at y=2 for x<3, then Gaussian peak
    >>> y = 4*np.exp(-0.5*((x-5)/1)**2)*np.heaviside(x-3, 0.5) + 2*np.heaviside(3-x, 0.5)
    >>> fit = GaussianTimesHeavySidePlusHeavySide(x, y, guess_x0=3.0)
    >>> fit.make_fit()
    >>> print(f"x0={fit.popt['x0']:.2f}, y1={fit.popt['y1']:.2f}")
    x0=3.00, y1=2.00
    """

    def __init__(self, xobs, yobs, guess_x0=None, **kwargs):
        if guess_x0 is None:
            raise ValueError(
                "guess_x0 is required for GaussianTimesHeavySidePlusHeavySide. "
                "Provide an initial estimate for the transition x-coordinate."
            )
        super().__init__(xobs, yobs, **kwargs)
        self._guess_x0 = guess_x0

    @property
    def guess_x0(self) -> float:
        r"""Initial guess for transition x-coordinate used in p0 calculation."""
        return self._guess_x0

    @property
    def function(self):
        r"""The Gaussian times Heaviside plus Heaviside function.

        Returns
        -------
        callable
            Function with signature ``f(x, x0, y1, mu, sigma, A)``.
        """

        def gaussian_heavy_side(x, x0, y1, mu, sigma, A):
            r"""Evaluate Gaussian times Heaviside plus Heaviside model.

            Parameters
            ----------
            x : array-like
                Independent variable values.
            x0 : float
                Transition x-coordinate.
            y1 : float
                Constant plateau value for x < x0.
            mu : float
                Gaussian mean.
            sigma : float
                Gaussian standard deviation.
            A : float
                Gaussian amplitude.

            Returns
            -------
            numpy.ndarray
                Model values at x.
            """

            def gaussian(x, mu, sigma, A):
                arg = -0.5 * (((x - mu) / sigma) ** 2.0)
                return A * np.exp(arg)

            def heavy_side(x, x0, y1):
                out = y1 * np.heaviside(x0 - x, 1.0)
                return out

            out = gaussian(x, mu, sigma, A) * np.heaviside(x - x0, 1.0) + heavy_side(
                x, x0, y1
            )
            return out

        return gaussian_heavy_side

    @property
    def p0(self) -> list:
        r"""Calculate initial parameter guess.

        The initial guess is derived from:
        - ``guess_x0`` for x0
        - Mean of y values for x < x0 as y1 estimate
        - Weighted mean and std for Gaussian parameters (using x > x0)
        - Peak amplitude from data

        Returns
        -------
        list
            Initial guesses as [x0, y1, mu, sigma, A].

        Raises
        ------
        AssertionError
            If insufficient data for estimation.

        Notes
        -----
        # TODO: Convert to data-driven p0 estimation (see GH issue #XX)
        """
        assert self.sufficient_data

        x, y = self.observations.used.x, self.observations.used.y
        x0 = self.guess_x0
        tk = x > x0

        y1 = y[~tk].mean()
        if np.isnan(y1):
            y1 = 0

        x, y = x[tk], y[tk]
        mean = (x * y).sum() / y.sum()
        std = np.sqrt(((x - mean) ** 2.0 * y).sum() / y.sum())

        try:
            peak = y.max()
        except ValueError as e:
            chk = (
                r"zero-size array to reduction operation maximum "
                "which has no identity"
            )
            if str(e).startswith(chk):
                msg = (
                    "There is no maximum of a zero-size array. "
                    "Please check input data."
                )
                raise ValueError(msg)
            raise

        p0 = [x0, y1, mean, std, peak]
        return p0

    @property
    def TeX_function(self) -> str:
        r"""LaTeX representation of the model.

        Returns
        -------
        str
            Multi-line LaTeX string describing the function.
        """
        tex = "\n".join(
            [
                r"f(x)=A \cdot e^{-\frac{1}{2} (\frac{x-\mu}{\sigma})^2} \times H(x - x_0) + ",
                r"y_1 \cdot H(x_0 - x)",
            ]
        )
        return tex
