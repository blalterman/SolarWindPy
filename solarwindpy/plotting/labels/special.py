#!/usr/bin/env python
r"""Special labels not handled by :py:class:`TeXlabel`.
"""
import pdb  # noqa: F401
from pathlib import Path
from abc import abstractproperty, abstractmethod

from . import base


class ArbitraryLabel(base.Base):
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
        self.set_axnorm(norm)
        self.build_label()

    def __str__(self):
        return r"${} \; [{}]$".format(self.tex, self.units)

    @property
    def tex(self):
        return self._tex

    @property
    def units(self):
        return r"\#"

    @property
    def path(self):
        return self._path

    @property
    def axnorm(self):
        return self._axnorm

    def set_axnorm(self, norm):
        if norm is not None:
            norm = norm.lower()

        assert norm in base._trans_axnorm.keys()
        self._axnorm = norm

    def _build_tex(self):
        axnorm = self.axnorm
        if axnorm:
            if self.axnorm in ("r", "c", "t"):
                tex = r"\mathrm{%s Norm Count}" % base._trans_axnorm.get(axnorm)
            else:
                tex = r"\mathrm{Probability Density}"
        else:
            tex = r"\mathrm{Count}"

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


class Probability(ArbitraryLabel):
    def __init__(self, other_label, comparison=None):
        r"""`other_label` is a `TeXlabel` or str identifying the quantity for which we're calculating the probability.

        The `comparison`, if passed, is something like "> 0".
        """
        self.set_other_label(other_label)
        self.set_comparison(comparison)
        self.build_label()

    def __str__(self):
        return r"${} \; [{}]$".format(self.tex, self.units)

    @property
    def tex(self):
        return self._tex

    @property
    def units(self):
        return r"\%"

    @property
    def path(self):
        return self._path

    @property
    def other_label(self):
        return self._other_label

    @property
    def comparison(self):
        return self._comparison

    def set_other_label(self, other):
        assert isinstance(other, (str, base.TeXlabel, ArbitraryLabel))
        self._other_label = other

    def set_comparison(self, new):
        if new is None:
            new = ""
        self._comparison = str(new)

    def _build_tex(self):
        other = self.other_label
        #         try:
        #             tex = other.tex
        #         except AttributeError:
        tex = r"\mathrm{Prob.}(%s %s)" % (other.tex, self.comparison)

        return tex.replace(" ", r" \, ")

    def _build_path(self):
        other = self.other_label

        try:
            other = str(other.path)
        except AttributeError:
            other = (
                other.replace(">", "GT")
                .replace("<", "LT")
                .replace(r"\gt", "GT")
                .replace(r"\lt", "GT")
                .replace(r"\geq", "GEQ")
                .replace(r"\leq", "LEQ")
                .replace(r"\gt", "GT")
                .replace(r"\neq", "NEQ")
                .replace(r"\eq", "EQ")
                .replace(r"==", "EQ")
                .replace(r"!=", "NEQ")
            )

        other = other.replace(" ", "-")

        path = Path("prob-" + other)

        return path

    def build_label(self):
        self._tex = self._build_tex()
        self._path = self._build_path()


class Timedelta(ArbitraryLabel):
    def __init__(self, dt):
        r"""
        Parameters
        ----------
        dt: str
            Classifies the `timedelta` category used for labels, e.g. Year, Month, Day, Date, Epoch, etc.
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


class DateTime(ArbitraryLabel):
    def __init__(self, kind):
        r"""
        Parameters
        ----------
        dt: str
            Classifies the `datetime` category used for labels, e.g. Year, Month, Day, Date, Epoch, etc.
        """
        self.set_kind(kind)

    def __str__(self):
        return r"$%s$" % self.tex

    @property
    def kind(self):
        return self._kind

    @property
    def tex(self):
        return r"\mathrm{%s}" % self.kind

    @property
    def path(self):
        return Path(self.dt.lower())

    def build_label(self):
        pass

    def set_kind(self, new):
        self._kind = new


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
        units = units.lower()
        trans = {"rs": r"R_{\bigodot}", "re": r"R_{\oplus}", "au": r"\mathrm{AU}"}
        units = trans.get(units, units)

        if units not in [*trans.values()] + ["m", "km"]:
            raise NotImplementedError("Unrecognized distance2sun units %s" % units)

        self._units = units

    def build_label(self):
        pass


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
        assert new in ("M", "M13", "D", "Y", "NM", "NM13", "ND", "NY")
        self._kind = new
        self._path = Path(f"""{new.lower()!s}-ssn""")
