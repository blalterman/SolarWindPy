#!/usr/bin/env python
r"""Special labels not handled by :py:class:`TeXlabel`.
"""
import pdb  # noqa: F401
from pathlib import Path
from abc import ABC, abstractproperty, abstractmethod

from . import base


class ArbitraryLabel(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def __str__(self):
        pass

    @abstractproperty
    def tex(self):
        pass

    @abstractproperty
    def path(self):
        pass

    @abstractmethod
    def build_label(self):
        pass


class Vsw(ArbitraryLabel):
    def __init__(self):
        pass

    def __str__(self):
        return r"$%s \; [\mathrm{km \, s^{-1}}]$" % self.tex

    @property
    def tex(self):
        return r"V_\mathrm{SW}"

    @property
    def path(self):
        return Path("vsw")

    def build_label(self):
        pass


class Count(ArbitraryLabel):
    def __init__(self, norm=None):
        self.set_axnorm(None)
        self.build_label()

    def __str__(self):
        return r"${} \; [\#]$".format(self.tex)

    @property
    def tex(self):
        return self._tex

    @property
    def path(self):
        return self._path

    @property
    def axnorm(self):
        return self._axnorm

    def set_axnorm(self, norm):
        norm = norm.lower()
        #         assert norm in (None, "c", "r", "t", "d")
        assert norm in base._trans_axnorm.keys()
        self._axnorm = norm

    def _build_tex(self):
        #        norm = self.axnorm
        #        if norm is None:
        #            tex = "{}"
        #
        #        elif norm == "c":
        #            tex = r"Col. Norm {}"
        #
        #        elif norm == "r":
        #            tex = r"Row Norm {}"
        #
        #        elif norm == "t":
        #            tex = r"Total Norm {}"
        #
        #        elif norm == "d":
        #            tex = r"Density Norm {}"
        #
        #        else:
        #            raise ValueError("Unrecognized normalization {}".format(norm))

        tex = r"\mathrm{%s Norm Count}" % base._trans_axnorm[self.norm]
        return tex.replace(" ", r" \, ")

    def _build_path(self):
        path = Path("count")

        norm = self.axnorm
        if norm is not None:
            path = path / (norm.upper() + "norm")

        return path

    def build_label(self):
        self._tex = self._build_tex()
        self._path = self._build_path()


class DateTime(ArbitraryLabel):
    def __init__(self, dt):
        r"""
        Parameters
        ----------
        dt: str
            Classifies the `datetime` category used for labels, e.g. Year, Month, Day, Date, Epoch, etc.
        """
        self.set_dt(dt)

    def __str__(self):
        return r"$%s$" % self.tex

    @property
    def dt(self):
        return self._dt

    @property
    def tex(self):
        return r"\mathrm{%s}" % self.dt.replace(" ", r" \, ")

    @property
    def path(self):
        return Path(self.dt.lower())

    def build_label(self):
        pass

    def set_dt(self, new):
        self._dt = new


class Distance2Sun(ArbitraryLabel):
    def __init__(self, units):
        self.set_units(units)

    def __str__(self):
        return r"$%s \; [\mathrm{%s}]$" % (self.tex, self.units)

    @property
    def units(self):
        return self._units

    @property
    def path(self):
        return Path("distance2sun")

    @property
    def tex(self):
        return r"\mathrm{Distance \; to \; Sun}"

    def set_units(self, units):
        trans = {"Rs": r"R_\bigodot", "Re": r"R_\oplus"}
        units = trans.get(units, units)

        if units not in ("m", "km", r"R_\bigodot"):
            raise NotImplementedError("Unrecognized distance2sun units %s" % units)

        self._units = units


class SSN(ArbitraryLabel):
    def __init__(self, key):
        self.set_kind(key)

    def __str__(self):
        return r"$%s \; [\#]$" % self.tex

    @property
    def units(self):
        return base._inU["dimless"]

    @property
    def path(self):
        return self._path

    @property
    def tex(self):
        return r"\mathrm{%s} \; \mathrm{SSN}" % self.kind

    @property
    def kind(self):
        return self._kind

    def build_label(self):
        pass

    def set_kind(self, new):
        new = new.upper()
        assert new in ("M", "M13", "D", "Y")
        self._kind = new
        self._path = Path(f"""{new.lower()!s}-ssn""")
