#!/usr/bin/env python
"""Utility functions for manipulating solar wind data.

This module contains helper functions that are not yet organized into
their own submodules. The functions are primarily used for handling
proton data and for the mean and standard deviation of a log-normal
variable.

Functions
---------
swap_protons
    Swap beam and core proton labels when the beam density exceeds the
    core density.
normal_parameters
    Mean and standard deviation of a log-normal variable.

Examples
--------
>>> import pandas as pd  # doctest: +SKIP
>>> import numpy as np  # doctest: +SKIP
>>> columns = pd.MultiIndex.from_tuples([  # doctest: +SKIP
...     ('n', '', 'p1'), ('n', '', 'p2')
... ], names=['M', 'C', 'S'])
>>> df = pd.DataFrame([[1, 0.1], [2, 0.2]], columns=columns)  # doctest: +SKIP
>>> new_df, mask = swap_protons(df)  # doctest: +SKIP
>>> 'swapped_protons' in new_df.columns.get_level_values('M')  # doctest: +SKIP
True
"""

__all__ = [
    "swap_protons",
    "normal_parameters",
]

import logging
import numpy as np
import pandas as pd


def swap_protons(data, logger=None):
    """Swap beam and core proton labels when the beam density dominates.

    Parameters
    ----------
    data : pandas.DataFrame
        Data containing proton information. Proton species are stored in the
        ``S`` level of the column index.
    logger : logging.Logger, optional
        Logger used to report indices of swapped protons. If ``None`` a simple
        logger is created.

    Returns
    -------
    new_data : pandas.DataFrame
        Copy of ``data`` with ``p1`` and ``p2`` columns swapped where the beam
        density exceeds the core density.
    swap : pandas.Series
        Boolean mask indicating where swaps occurred.

    Examples
    --------
    >>> import pandas as pd  # doctest: +SKIP
    >>> import numpy as np  # doctest: +SKIP
    >>> columns = pd.MultiIndex.from_tuples([  # doctest: +SKIP
    ...     ('n', '', 'p1'), ('n', '', 'p2')
    ... ], names=['M', 'C', 'S'])
    >>> df = pd.DataFrame([[2, 1], [1, 2]], columns=columns)  # p1 < p2 in first row  # doctest: +SKIP
    >>> new_df, mask = swap_protons(df)  # doctest: +SKIP
    >>> mask.iloc[0]  # First row should be swapped  # doctest: +SKIP
    True
    """
    p1 = data.xs("p1", axis=1, level="S")
    p2 = data.xs("p2", axis=1, level="S")

    n1 = p1.n
    n2 = p2.n

    swap = n2.divide(n1) > 1.0
    swapped = swap.to_frame(name=("swapped_protons", "", ""))

    p1_into_p2 = p1.where(swap, axis=0).dropna(axis=0, how="all")
    p2_into_p1 = p2.where(swap, axis=0).dropna(axis=0, how="all")

    p1 = p1.mask(swap, p2_into_p1, axis=0)

    p2 = p2.mask(swap, p1_into_p2, axis=0)

    new_protons = (
        pd.concat([p1, p2], axis=1, keys=["p1", "p2"], names=["S"])
        .reorder_levels(["M", "C", "S"], axis=1)
        .sort_index(axis=1)
    )

    new_data = pd.concat(
        [data.drop(["p1", "p2"], axis=1, level="S"), new_protons, swapped], axis=1
    ).sort_index(axis=1)
    # `swapped` carries unnamed columns, so the concat drops the level names;
    # restore the caller's (M, C, S) so the output can be swapped again.
    new_data.columns = new_data.columns.set_names(data.columns.names)

    chk = new_data.loc[:, ("n", "", "p2")].divide(
        new_data.loc[:, ("n", "", "p2")], axis=0
    )
    assert (chk.dropna() <= 1.0).all()

    if logger is None:
        logger = logging.getLogger("main.{}".format(__name__))
        # The logger is module-global: add its handler once, not per call, or
        # the Nth call prints its stats N times.
        if not logger.handlers:
            hdlr = logging.StreamHandler()
            hdlr.setLevel(logging.INFO)
            logger.addHandler(hdlr)
        logger.setLevel(logging.DEBUG)

    assert isinstance(logger, logging.Logger)
    stats = pd.Series(
        {"mean": swap.mean(), "count": swap.sum()}, name="stats", dtype=object
    )  # `dtype=object` lets the count print as an int.
    logger.info("Swap proton labels when n2/n1 > 1\nstats\n%s", stats.to_string())

    return new_data, swap


def normal_parameters(m, s, base=np.e):
    r"""Mean and standard deviation of a log-normal variable.

    Given :math:`\log_b X \sim \mathcal{N}(m, s^2)`, return the mean and the
    standard deviation of :math:`X` itself.

    Parameters
    ----------
    m : float, pandas.Series or numpy.ndarray
        Mean of :math:`\log_b X`.
    s : float, pandas.Series or numpy.ndarray
        Standard deviation of :math:`\log_b X`.
    base : float, default ``np.e``
        Base :math:`b` of the logarithm in which ``m`` and ``s`` are given,
        e.g. ``10`` for a base-10 log-normal. Must be positive, finite, and
        not 1.

    Returns
    -------
    pandas.DataFrame or pandas.Series
        ``mu`` (mean of :math:`X`) and ``sigma`` (standard deviation of
        :math:`X`): DataFrame columns for Series input, Series entries for
        scalar input, so ``mu, sigma = normal_parameters(m, s)`` unpacks.

    Raises
    ------
    ValueError
        If ``base`` is not positive, finite, and different from 1.

    Notes
    -----
    Since :math:`\ln X = \ln(b)\,\log_b X`, :math:`\ln X \sim
    \mathcal{N}(\mu_e, \sigma_e^2)` with :math:`\mu_e = m \ln b` and
    :math:`\sigma_e = s \ln b`. The log-normal moments are then
    [1]_ (eq. 8)

    .. math::
       \mu = \exp[\mu_e + \sigma_e^2/2]

    .. math::
       \sigma = \sqrt{\exp[2\mu_e + \sigma_e^2]\,(\exp[\sigma_e^2] - 1)}

    and the median is :math:`\exp(\mu_e) = b^m`. The rescaling by
    :math:`\ln b` is the decibel-to-natural-unit conversion of [1]_ (eq. 9).
    Base-``b`` parameters must be rescaled, not substituted into these
    formulas as :math:`b^{m + s^2/2}`.

    References
    ----------
    .. [1] Fenton, L. F. (1960). The sum of log-normal probability
       distributions in scatter transmission systems. IRE Transactions on
       Communications Systems, 8(1), 57-67. doi:10.1109/TCOM.1960.1097606

    Examples
    --------
    >>> m, s = 1.0, 0.5  # mean and std of ln(X)
    >>> mu, sigma = normal_parameters(m, s)
    >>> bool(mu > np.exp(m))  # the mean exceeds the median e^m
    True
    >>> mu10, _ = normal_parameters(0.0, 0.1, base=10)  # log10(X) ~ N(0, 0.1)
    >>> bool(mu10 > 1.0)
    True
    """
    base = float(base)
    if not (np.isfinite(base) and base > 0.0 and base != 1.0):
        raise ValueError(f"base must be positive, finite, and != 1, got {base}")

    ln_base = np.log(base)
    m = m * ln_base
    s = s * ln_base

    mu = np.exp(m + ((s**2.0) / 2.0))
    sigma = np.exp(s**2.0 + 2.0 * m)
    sigma *= np.exp(s**2.0) - 1.0
    sigma = np.sqrt(sigma)

    out = {"mu": mu, "sigma": sigma}
    try:
        out = pd.concat(out, axis=1)
    except TypeError:
        out = pd.Series(out)

    return out
