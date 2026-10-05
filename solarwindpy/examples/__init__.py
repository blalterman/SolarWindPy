# Spent-When: PERMANENT(SolarWindPy stops shipping example data)
# Supersedes: none
r"""Example data shipped with SolarWindPy.

The example is three rows of synthetic solar wind measurements: magnetic
field, and the moments of alphas (``a``), electrons (``e``), protons
(``p1``) and a proton beam (``p2``), with a spacecraft trajectory. The values
are chosen for illustration and testing, not taken from a mission.
"""

from importlib import resources

import numpy as np
import pandas as pd

__all__ = ["load_plasma"]

_DATA = resources.files("solarwindpy.core").joinpath("data")


def _read_example(name):
    """Read ``core/data/example_<name>.csv`` as an ``(M, C, S)`` frame.

    Each CSV header is ``M|C|S``, for example ``v|x|p1`` or ``b|x|`` for a
    quantity without a species. Rows are indexed by the times in
    ``example_epoch.csv``.

    Parameters
    ----------
    name : str
        ``"plasma"``, ``"spacecraft"`` or ``"auxiliary_data"``.

    Returns
    -------
    pandas.DataFrame
        float64 values, columns sorted, index named ``epoch``.
    """
    with _DATA.joinpath("example_epoch.csv").open() as f:
        epoch = pd.read_csv(f)["epoch"].map(pd.to_datetime)
    with _DATA.joinpath(f"example_{name}.csv").open() as f:
        data = pd.read_csv(f)
    data.columns = pd.MultiIndex.from_tuples(
        [tuple(c.split("|")) for c in data.columns], names=["M", "C", "S"]
    )
    data = data.astype(np.float64).sort_index(axis=1)
    data.index = epoch
    return data


def load_plasma():
    r"""Build the example :class:`~solarwindpy.core.plasma.Plasma`.

    Every species in the example data is loaded. The spacecraft is Parker
    Solar Probe in the heliocentric inertial (HCI) frame, with position,
    velocity and Carrington location. Auxiliary data is loaded from
    ``example_auxiliary_data.csv`` when the package ships one.

    Returns
    -------
    :class:`~solarwindpy.core.plasma.Plasma`
        Three rows with species ``a``, ``e``, ``p1`` and ``p2``, and a
        spacecraft. No auxiliary data ships with the example.

    Examples
    --------
    >>> import solarwindpy as swp
    >>> plasma = swp.examples.load_plasma()
    >>> plasma.species
    ('a', 'e', 'p1', 'p2')
    >>> times = plasma.epoch.strftime("%Y-%m-%d %H:%M:%S.%f")
    >>> times.tolist()  # doctest: +NORMALIZE_WHITESPACE
    ['1995-01-01 12:35:00.000000', '2022-03-23 19:29:09.000000',
     '2022-10-09 01:47:01.234560']
    >>> plasma.data.loc[:, ("n", "", "p1")].tolist()
    [1.0, 2.0, 3.0]
    >>> plasma.spacecraft.name, plasma.spacecraft.frame
    ('PSP', 'HCI')
    >>> plasma.spacecraft.position.data.loc[:, "x"].tolist()
    [-42.0, -22.0, -34.0]
    """
    # Imported here so the package namespace binds only its own objects.
    from ..core.plasma import Plasma
    from ..core.spacecraft import Spacecraft

    data = _read_example("plasma")
    species = sorted(s for s in data.columns.get_level_values("S").unique() if s)

    sc = _read_example("spacecraft").xs("", axis=1, level="S")
    psp = pd.concat(
        {
            "pos": sc.xs("pos_HCI", axis=1, level="M"),
            "v": sc.xs("v_HCI", axis=1, level="M"),
            "carr": sc.xs("Carr", axis=1, level="M"),
        },
        axis=1,
        names=["M"],
    ).sort_index(axis=1)
    spacecraft = Spacecraft(psp, "PSP", "HCI")

    auxiliary_data = None
    if _DATA.joinpath("example_auxiliary_data.csv").is_file():
        auxiliary_data = _read_example("auxiliary_data")

    return Plasma(data, *species, spacecraft=spacecraft, auxiliary_data=auxiliary_data)
