#!/usr/bin/env python
"""Utility functions for manipulating solar wind data.

This module contains helper functions that are not yet organized into
their own submodules. The functions are primarily used for handling
proton data and for converting log-normal parameters to their normal
form.

Functions
---------
swap_protons
    Swap beam and core proton labels when the beam density exceeds the
    core density.
normal_parameters
    Convert log-normal distribution parameters to normal parameters.

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

import pdb  # noqa: F401
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

    chk = new_data.loc[:, ("n", "", "p2")].divide(
        new_data.loc[:, ("n", "", "p2")], axis=0
    )
    assert (chk.dropna() <= 1.0).all()

    if logger is None:
        logger = logging.getLogger("main.{}".format(__name__))
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


def normal_parameters(m, s):
    r"""Convert log-normal parameters to normal distribution parameters.

    Parameters
    ----------
    m : pandas.Series or numpy.ndarray
        Mean of the log-normal distribution.
    s : pandas.Series or numpy.ndarray
        Standard deviation of the log-normal distribution.

    Returns
    -------
    pandas.DataFrame
        Data frame with columns ``mu`` and ``sigma``.

    Notes
    -----
    The conversion uses

    .. math::
       \mu = \exp[m + s^2/2]

    .. math::
       \sigma = \sqrt{\exp[s^2 + 2m]\,(\exp[s^2] - 1)}

    These expressions apply to both natural logarithms and base-10 logarithms.

    Examples
    --------
    >>> import numpy as np
    >>> m, s = 1.0, 0.5  # log-normal parameters
    >>> mu, sigma = normal_parameters(m, s)
    >>> mu > 1.0  # Normal mean should be > 1
    True
    """
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
