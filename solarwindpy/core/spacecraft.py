#!/usr/bin/env python
r"""Contais :py:class:`~solarwindpy.core.spacecraft.Spacecraft` class.

Class inherets from :py:class:`~solarwindpy.core.base.Base` and contains :py:class:`~solarwindpy.core.vector.Vector` objects.
"""

import pdb  # noqa: F401
import pandas as pd

# We rely on views via DataFrame.xs to reduce memory size and do not
# `.copy(deep=True)`, so we want to make sure that this doesn't
# accidentally cause a problem.
pd.set_option("mode.chained_assignment", "raise")

try:
    from . import base
    from . import vector
except ImportError:
    import base
    import vector


class Spacecraft(base.Base):
    r"""Spacecraft class.

    Properties
    ----------
    name, frame, data, position, velocity, carrington

    Methods
    -------
    set_<>
    """

    def __init__(self, data, name, frame):
        super(Spacecraft, self).__init__(data)
        self.set_frame_name(frame, name)
        self.set_data(data)

    @property
    def frame(self):
        r"""Spacecraft's frame of reference (e.g. GSE, HCI, etc.).
        """
        return self._frame

    @property
    def name(self):
        r"""Spacecraft name (e.g. WIND, PSP)
        """
        return self._name

    @property
    def position(self):
        pos = self.data.xs("pos", axis=1, level="M").loc[:, ("x", "y", "z")]
        return vector.Vector(pos)

    @property
    def r(self):
        r"""Shortcut to :py:meth:`position`.
        """
        return self.position

    @property
    def velocity(self):
        try:
            v = self.data.xs("v", axis=1, level="M").loc[:, ("x", "y", "z")]
            return vector.Vector(v)
        except KeyError as e:  # noqa: F841
            raise KeyError("Spacecraft doesn't know it's velocity.")

    @property
    def v(self):
        r"""Shortcut to :py:meth:`velocity`.
        """
        return self.velocity

    @property
    def carrington(self):
        r"""Carrington latitude and longitude.
        """
        try:
            return self.data.xs("carr", axis=1, level="M").loc[:, ("lat", "lon")]
        except KeyError as e:  # noqa: F841
            raise KeyError("Spacecraft doesn't know its Carrington location.")

    def set_frame_name(self, frame, name):
        frame = frame.upper()
        name = name.upper()

        if frame not in ("GSE", "HCI"):
            raise NotImplementedError("Unrecognized frame: {}".format(frame))
        if name not in ("WIND", "PSP"):
            raise NotImplementedError("Unrecognized name: {}".format(name))

        self._frame = frame
        self._name = name

    def set_data(self, data):
        p = data.xs("pos", axis=1, level="M")
        assert isinstance(p, pd.DataFrame)
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

        target = pd.concat(target, axis=1, names=["M"])

        self._data = target
