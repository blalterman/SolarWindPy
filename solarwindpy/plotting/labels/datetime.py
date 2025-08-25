#!/usr/bin/env python
r"""Special labels not handled by :py:class:`TeXlabel`."""
import pdb  # noqa: F401
from pathlib import Path
from pandas.tseries.frequencies import to_offset
from . import base
from . import special


class Timedelta(special.ArbitraryLabel):
    """Label for a time interval."""

    def __init__(self, offset):
        """Instantiate the label.

        Parameters
        ----------
        offset : str or pandas offset
            Value convertible via :func:`pandas.tseries.frequencies.to_offset`.
        """
        super().__init__()
        self.set_offset(offset)

    def __str__(self):
        return self.with_units

    @property
    def with_units(self):
        return rf"${self.tex} \; [{self.units}]$"  # noqa: W605

    #     @property
    #     def dt(self):
    #         return self._dt

    @property
    def offset(self):
        return self._offset

    @property
    def tex(self):
        return r"\Delta t"

    @property
    def path(self):
        try:
            return Path(f"dt-{self.offset.freqstr}")
        except AttributeError:
            return Path("dt-UNK")

    @property
    def units(self):
        try:
            return r"%s \; \mathrm{%s}" % (
                self.offset.n,
                self.offset.name,
            )  # noqa: W605
        except AttributeError:
            return base._inU["unknown"]

    def set_offset(self, new):
        try:
            new = to_offset(new)
        except ValueError:
            pass

        self._offset = new


class DateTime(special.ArbitraryLabel):
    """Generic datetime label."""

    def __init__(self, kind):
        """Instantiate the label.

        Parameters
        ----------
        kind : str
            Text used to build the label, e.g. ``"Year"`` or ``"Month"``.
        """
        super().__init__()
        self.set_kind(kind)

    def __str__(self):
        return self.with_units

    @property
    def with_units(self):
        return r"$%s$" % self.tex

    @property
    def kind(self):
        return self._kind

    @property
    def tex(self):
        return r"\mathrm{%s}" % self.kind.replace(" ", r" \; ")  # noqa: W605

    @property
    def path(self):
        return Path(self.kind.lower().replace(" ", "-"))

    def set_kind(self, new):
        self._kind = new


class Epoch(special.ArbitraryLabel):
    r"""Create epoch analysis labels, e.g. ``Hour of Day``."""

    def __init__(self, kind, of_thing, space=r"\,"):
        """Instantiate the label.

        Parameters
        ----------
        kind : str
            The smaller time unit, e.g. ``"Hour"``.
        of_thing : str
            The larger time unit, e.g. ``"Day"``.
        space : str, default ``","``
            TeX spacing command placed between words.
        """
        super().__init__()
        self.set_smaller(kind)
        self.set_larger(of_thing)
        self.set_space(space)

    def __str__(self):
        return self.with_units

    @property
    def larger(self):
        return self._larger

    @property
    def path(self):
        return Path(f"{self.smaller}-of-{self.larger}")

    @property
    def smaller(self):
        return self._smaller

    @property
    def space(self):
        return self._space

    @property
    def tex(self):
        return r"\mathrm{%s %s of %s %s}" % (
            self.smaller,
            self.space,
            self.space,
            self.larger,
        )

    @property
    def with_units(self):
        return r"$%s$" % self.tex

    def set_larger(self, new):
        self._larger = new.title()

    def set_smaller(self, new):
        self._smaller = new.title()

    def set_space(self, new):
        if new not in (" ", r"\,", r"\;", r"\:"):
            raise ValueError(f"Unrecognized Space {new}")

        self._space = new


class Frequency(special.ArbitraryLabel):
    """Frequency of another quantity."""

    def __init__(self, other):
        super().__init__()
        self.set_other(other)
        self.build_label()

    def __str__(self):
        return rf"${self.tex} \; [{self.units}]$"

    @property
    def other(self):
        return self._other

    @property
    def tex(self):
        return r"\mathrm{Frequency}"

    @property
    def units(self):
        return f"({self.other.units})^{-1}"

    @property
    def path(self):
        return self._path

    def set_other(self, other):
        if not isinstance(other, Timedelta):
            other = Timedelta(other)

        self._other = other

    def _build_path(self):
        units = self.units
        if "??" in units:
            units = "UNK"

        path = Path(f"frequency_of_{units}")
        return path

    def build_label(self):
        self._path = self._build_path()


class January1st(special.ArbitraryLabel):
    """Label for the first day of the year."""

    def __init__(self):
        super().__init__()

    def __str__(self):
        return self.with_units

    @property
    def with_units(self):
        return r"$%s$" % self.tex

    @property
    def tex(self):
        return r"\mathrm{January 1^{st} of Year}".replace(" ", r" \; ")  # noqa: W605

    @property
    def path(self):
        return Path("January-1st-of-Year")
