#!/usr/bin/env python
r"""Contais :py:class:`~solarwindpy.core.spacecraft.Spacecraft` class.

Class inherets from :py:class:`~solarwindpy.core.base.Base` and contains :py:class:`~solarwindpy.core.vector.Vector` objects.
"""

import pandas as pd
import numpy as np

# We rely on views via DataFrame.xs to reduce memory size and do not
# `.copy(deep=True)`, so we want to make sure that this doesn't
# accidentally cause a problem.

from . import base
from . import vector


class Spacecraft(base.Base):
    r"""Representation of a spacecraft trajectory.

    Parameters
    ----------
    data : :class:`pandas.DataFrame`
        Vector position (and optionally velocity) with MultiIndex columns
        ``("M", "C")``.
    name : str
        Identifier of the spacecraft.
    frame : str
        Reference frame of the vectors, e.g. ``"HCI"`` or ``"GSE"``.
    """

    def __init__(self, data, name, frame):
        r"""Initialize a spacecraft with `data`.

        Parameters
        ----------
        data: pd.DataFrame
            2-level MultiIndex columns identifying measurment "M" and component "C".
            Should contain at a minimum vector position. Can also contain vector
            velocity and Carrington location. If vector velocity included, it should be
            in the same frame of reference as the position.
        name: str
            Identify the spacecraft, e.g. Parker Solar Probe (PSP) or Wind. Internally
            stored in all caps for consistency.
        frame: str
            The frame of reference for the spacecraft position and velocity, e.g.
            Geocentric Solar Ecliptic (GSE) or Heliocentric Internal (HCI).

        Examples
        --------
        >>> epoch = pd.Series({0: pd.to_datetime("1995-01-01"),
        ...                    1: pd.to_datetime("2015-03-23"),
        ...                    2: pd.to_datetime("2022-10-09")}, name="Epoch")
        >>> data = {("pos", "x", ""): {0: -42, 1: -22, 2: -34},
        ...         ("pos", "y", ""): {0: 23, 1: 31, 2: 11},
        ...         ("pos", "z", ""): {0: 35, 1: 27, 2: 49},
        ...         ("v", "x", ""): {0: 9.0, 1: 10.0, 2: 8.0},
        ...         ("v", "y", ""): {0: -80.0, 1: -70.0, 2: -90.0},
        ...         ("v", "z", ""): {0: -0.5, 1: 0.5, 2: 1.5},
        ...         ("carr", "lat", ""): {0: -2.0, 1: -1.0, 2: 3.0},
        ...         ("carr", "lon", ""): {0: -26.0, 1: -36.0, 2: -16.0}}
        >>> spacecraft = pd.DataFrame.from_dict(data,
        ...                                     orient="columns",
        ...                                     dtype=np.float64)
        >>> spacecraft.index = epoch
        >>> spacecraft.columns.names = ["M", "C", "S"]
        >>> spacecraft = spacecraft.xs("", axis=1, level="S")
        >>> spacecraft  # doctest: +NORMALIZE_WHITESPACE
        M            pos                 v            carr
        C              x     y     z     x     y    z  lat   lon
        Epoch
        1995-01-01 -42.0  23.0  35.0   9.0 -80.0 -0.5 -2.0 -26.0
        2015-03-23 -22.0  31.0  27.0  10.0 -70.0  0.5 -1.0 -36.0
        2022-10-09 -34.0  11.0  49.0   8.0 -90.0  1.5  3.0 -16.0
        >>> spacecraft = Spacecraft(spacecraft, "PSP", "HCI")
        """
        super(Spacecraft, self).__init__(data)
        self.set_frame_name(frame, name)
        self.set_data(data)
        self._log_spacecraft()

    @property
    def frame(self):
        r"""Spacecraft's frame of reference (e.g. GSE, HCI, etc.)."""
        return self._frame

    @property
    def name(self):
        r"""Spacecraft name (e.g. WIND, PSP)."""
        return self._name

    @property
    def position(self):
        """Position vector of the spacecraft.

        Returns
        -------
        vector.Vector
            Position vector with x, y, z components.
        """
        pos = self.data.xs("pos", axis=1, level="M").loc[:, ("x", "y", "z")]
        return vector.Vector(pos)

    @property
    def pos(self):
        """Shortcut to position property.

        Returns
        -------
        vector.Vector
            Position vector with x, y, z components.
        """
        # Ensures that `sc.pos` returns vector.
        return self.position

    @property
    def r(self):
        r"""Shortcut to :py:attr:`position`."""
        return self.position

    @property
    def velocity(self):
        """Velocity vector of the spacecraft.

        Returns
        -------
        vector.Vector
            Velocity vector with x, y, z components.

        Raises
        ------
        KeyError
            If spacecraft velocity data is not available.
        """
        try:
            v = self.data.xs("v", axis=1, level="M").loc[:, ("x", "y", "z")]
            return vector.Vector(v)
        except KeyError as e:  # noqa: F841
            raise KeyError("Spacecraft doesn't know it's velocity.")

    @property
    def v(self):
        r"""Shortcut to :py:attr:`velocity`."""
        return self.velocity

    @property
    def carrington(self):
        r"""Carrington latitude and longitude."""
        try:
            return self.data.xs("carr", axis=1, level="M").loc[:, ("lat", "lon")]
        except KeyError as e:  # noqa: F841
            raise KeyError("Spacecraft doesn't know its Carrington location.")

    @property
    def distance2sun(self):
        r"""Radial distance to Sun in meters."""
        pos = self.position.data
        frame = self.frame

        if frame == "GSE":
            re = self.constants.misc.loc["Re [m]"]
            au = self.constants.misc.loc["1AU [m]"]
            sign_x = pd.Series(
                [-1.0, 1.0, 1.0], index=pd.Index(("x", "y", "z"), name="C")
            )
            change_origin = pd.Series(
                [au, 0.0, 0.0], index=pd.Index(("x", "y", "z"), name="C")
            )
            pos_SI = (
                pos.multiply(sign_x, axis=1).multiply(re).add(change_origin, axis=1)
            )

        elif frame == "HCI":
            rs = self.constants.misc.loc["Rs [m]"]
            pos_SI = pos.multiply(rs)

        else:
            raise NotImplementedError("Unrecognized reference frame `{}`".format(frame))

        # distance2sun units should be [m], so this shouldn't matter. However, just as
        # beta is treated in this way, we similarly treat distance2sun.
        d2s = pos_SI.pow(2).sum(axis=1).pipe(np.sqrt) / self.units.distance2sun
        d2s.name = "distance2sun"
        return d2s

    def _log_spacecraft(self):
        self.logger.info(
            "Created %s spacecraft with %s reference frame", self.name, self.frame
        )

    def set_frame_name(self, frame, name):
        """Set the coordinate frame and spacecraft name.

        Parameters
        ----------
        frame : str
            Coordinate frame ('GSE' or 'HCI').
        name : str
            Spacecraft name.

        Raises
        ------
        NotImplementedError
            If frame is not 'GSE' or 'HCI'.
        """
        frame = frame.upper()
        name = name.upper()

        if frame not in ("GSE", "HCI"):
            raise NotImplementedError("Unrecognized frame: {}".format(frame))
        if name not in ("WIND", "PSP"):
            raise NotImplementedError("Unrecognized name: {}".format(name))

        self._frame = frame
        self._name = name

    def set_data(self, data):
        """Set the spacecraft data.

        Parameters
        ----------
        data : pd.DataFrame
            Spacecraft position/velocity data.
        """
        super(Spacecraft, self).set_data(data)

        p = data.xs("pos", axis=1, level="M")
        #         assert isinstance(p, pd.DataFrame)

        p = p.loc[:, ["x", "y", "z"]]
        assert p.shape[1] == 3

        target = {"pos": p}

        try:
            v = data.xs("v", axis=1, level="M")
            assert isinstance(v, pd.DataFrame)
            v = v.loc[:, ["x", "y", "z"]]
            assert v.shape[1] == 3
            target["v"] = v
        except KeyError:
            pass

        try:
            c = data.xs("carr", axis=1, level="M")
            assert isinstance(c, pd.DataFrame)
            c = c.loc[:, ["lat", "lon"]]
            assert c.shape[1] == 2
            target["carr"] = c
        except KeyError:
            pass

        target = pd.concat(target, axis=1, names=["M"], sort=False).sort_index(axis=1)

        assert isinstance(target.index, pd.DatetimeIndex)
        self._data = target
