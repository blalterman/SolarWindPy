#!/usr/bin/env python
r"""Miscelaneous tools for working with plasma data.

These aren't usually tested and this module will be refactored into submodules when it becomes sufficiently large.

Author : Benjamin L. Alterman
e-mail : balterma@umich.edu

Revision History
----------------
-Started module. (2018-03-12)

Propodes Updates
----------------
-

Do Not Try
----------
-

Notes
-----
-

"""

import pdb  # noqa: F401
import logging
import pandas as pd


def swap_protons(data, logger=None):
    r"""
    Swap the beam and core labels when the proton beam has a larger number density than the proton core.

    Parameters
    ----------
    data: pd.DataFrame
        The data to check for swapping.
    logger: None, logging.Logger
        If not None, a logger to log the index of swapped protons and
        the number of protons swapped.

    Returns
    -------
    new_data: pd.DataFrame
        `data` with p1<->p2 labels swapped.
    swap: pd.Series
        Boolean series indicating True where labels swapped.
    """
    p1 = data.xs("p1", axis=1, level="S")
    p2 = data.xs("p2", axis=1, level="S")

    n1 = p1.n
    n2 = p2.n

    swap = n2.divide(n1) > 1.0

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
        [data.drop(["p1", "p2"], axis=1, level="S"), new_protons], axis=1
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
