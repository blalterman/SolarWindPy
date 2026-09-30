#!/usr/bin/env python
r"""Labels for times, time intervals, and frequencies."""

from pathlib import Path
from pandas.tseries.frequencies import to_offset
from . import base
from . import special


class Timedelta(special.ArbitraryLabel):
    """Label for a time interval."""

    def __init__(self, offset, description=None):
        """Instantiate the label.

        Parameters
        ----------
        offset : str or pandas offset
            Value convertible via :func:`pandas.tseries.frequencies.to_offset`.
        description : str or None, optional
            Human-readable description displayed above the mathematical label.
        """
        super().__init__()
        self.set_offset(offset)
        self.set_description(description)

    def __str__(self):
        return self.with_units

    @property
    def with_units(self):
        r"""Label with units, as a TeX math string."""
        result = rf"${self.tex} \; [{self.units}]$"  # noqa: W605
        return self._format_with_description(result)

    @property
    def offset(self):
        r"""Pandas offset, or the raw value if it could not be converted."""
        return self._offset

    @property
    def tex(self):
        r"""TeX of the label."""
        return r"\Delta t"

    @property
    def path(self):
        r"""Save path ``dt-<freqstr>``, or ``dt-UNK`` without a valid offset."""
        try:
            return Path(f"dt-{self.offset.freqstr}")
        except AttributeError:
            return Path("dt-UNK")

    @property
    def units(self):
        r"""TeX of the offset's multiple and unit, or unknown units."""
        try:
            return r"%s \; \mathrm{%s}" % (
                self.offset.n,
                self.offset.name,
            )  # noqa: W605
        except AttributeError:
            return base._inU["unknown"]

    def set_offset(self, new):
        r"""Store ``new`` converted with ``to_offset``, or unchanged if that fails."""
        try:
            new = to_offset(new)
        except ValueError:
            pass

        self._offset = new


class DateTime(special.ArbitraryLabel):
    """Generic datetime label."""

    def __init__(self, kind, description=None):
        """Instantiate the label.

        Parameters
        ----------
        kind : str
            Text used to build the label, e.g. ``"Year"`` or ``"Month"``.
        description : str or None, optional
            Human-readable description displayed above the mathematical label.
        """
        super().__init__()
        self.set_kind(kind)
        self.set_description(description)

    def __str__(self):
        return self.with_units

    @property
    def with_units(self):
        r"""Label as a TeX math string; it has no units."""
        result = r"$%s$" % self.tex
        return self._format_with_description(result)

    @property
    def kind(self):
        r"""Text of the label, e.g. ``Year``."""
        return self._kind

    @property
    def tex(self):
        r"""TeX of the label."""
        return r"\mathrm{%s}" % self.kind.replace(" ", r" \; ")  # noqa: W605

    @property
    def path(self):
        r"""Save path, ``kind`` lower-cased with spaces replaced by ``-``."""
        return Path(self.kind.lower().replace(" ", "-"))

    def set_kind(self, new):
        r"""Store the text of the label."""
        self._kind = new


class Epoch(special.ArbitraryLabel):
    r"""Create epoch analysis labels, e.g. ``Hour of Day``."""

    def __init__(self, kind, of_thing, space=r"\,", description=None):
        r"""Instantiate the label.

        Parameters
        ----------
        kind : str
            The smaller time unit, e.g. ``"Hour"``.
        of_thing : str
            The larger time unit, e.g. ``"Day"``.
        space : str, default ``"\,"``
            TeX spacing command placed between words.
        description : str or None, optional
            Human-readable description displayed above the mathematical label.
        """
        super().__init__()
        self.set_smaller(kind)
        self.set_larger(of_thing)
        self.set_space(space)
        self.set_description(description)

    def __str__(self):
        return self.with_units

    @property
    def larger(self):
        r"""Larger time unit, title-cased."""
        return self._larger

    @property
    def path(self):
        r"""Save path ``<smaller>-of-<larger>``."""
        return Path(f"{self.smaller}-of-{self.larger}")

    @property
    def smaller(self):
        r"""Smaller time unit, title-cased."""
        return self._smaller

    @property
    def space(self):
        r"""TeX spacing command placed between words."""
        return self._space

    @property
    def tex(self):
        r"""TeX of the label."""
        return r"\mathrm{%s %s of %s %s}" % (
            self.smaller,
            self.space,
            self.space,
            self.larger,
        )

    @property
    def with_units(self):
        r"""Label as a TeX math string; it has no units."""
        result = r"$%s$" % self.tex
        return self._format_with_description(result)

    def set_larger(self, new):
        r"""Store the larger time unit, title-cased."""
        self._larger = new.title()

    def set_smaller(self, new):
        r"""Store the smaller time unit, title-cased."""
        self._smaller = new.title()

    def set_space(self, new):
        r"""Set the spacing between words.

        Raises
        ------
        ValueError
            If ``new`` is not a space or one of the TeX spaces ``\,``, ``\;``, ``\:``.
        """
        if new not in (" ", r"\,", r"\;", r"\:"):
            raise ValueError(f"Unrecognized Space {new}")

        self._space = new


class Frequency(special.ArbitraryLabel):
    """Frequency of another quantity."""

    def __init__(self, other, description=None):
        """Instantiate the label.

        Parameters
        ----------
        other : Timedelta or str
            The time interval for frequency calculation.
        description : str or None, optional
            Human-readable description displayed above the mathematical label.
        """
        super().__init__()
        self.set_other(other)
        self.set_description(description)
        self.build_label()

    def __str__(self):
        result = rf"${self.tex} \; [{self.units}]$"
        return self._format_with_description(result)

    @property
    def other(self):
        r"""``Timedelta`` label whose inverse this frequency is."""
        return self._other

    @property
    def tex(self):
        r"""TeX of the label."""
        return r"\mathrm{Frequency}"

    @property
    def units(self):
        r"""TeX of the inverse of the other label's units."""
        return f"({self.other.units})^{-1}"

    @property
    def path(self):
        r"""Save path, set by ``build_label``."""
        return self._path

    def set_other(self, other):
        r"""Store ``other``, wrapping it in a ``Timedelta`` if it is not one."""
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
        r"""Rebuild ``path`` from the units."""
        self._path = self._build_path()


class January1st(special.ArbitraryLabel):
    """Label for the first day of the year."""

    def __init__(self, description=None):
        """Instantiate the label.

        Parameters
        ----------
        description : str or None, optional
            Human-readable description displayed above the mathematical label.
        """
        super().__init__()
        self.set_description(description)

    def __str__(self):
        return self.with_units

    @property
    def with_units(self):
        r"""Label as a TeX math string; it has no units."""
        result = r"$%s$" % self.tex
        return self._format_with_description(result)

    @property
    def tex(self):
        r"""TeX of the label."""
        return r"\mathrm{January 1^{st} of Year}".replace(" ", r" \; ")  # noqa: W605

    @property
    def path(self):
        r"""Save path ``January-1st-of-Year``."""
        return Path("January-1st-of-Year")
