#!/usr/bin/env python
r"""Tools for creating physical quantity plot labels."""

__all__ = [
    "Base",
    "TeXlabel",
    "format_with_units",
]

import logging
import re
from abc import ABC
from pathlib import Path
from string import Template
from collections import namedtuple

from ...core import quantities

_MCS = namedtuple("_MCS", "m,c,s")


#: TeX of each species, component and display unit, read from the quantity
#: registry (:mod:`solarwindpy.core.quantities`), their one home.
_trans_species = quantities.SPECIES
_trans_component = quantities.COMPONENTS
_inU = quantities.UNIT_TEX

_trans_axnorm = {
    None: "",
    "c": "Col.",
    "r": "Row",
    "t": "Total",
    "d": "Density",
    "rd": "1D Probability Density",
    "cd": "1D Probability Density",
}

# Longest first, so a species is never matched by a code it starts with
# (``a_bimax`` before ``a``, ``p1`` before ``p``).
_all_species_re = re.compile(
    "|".join(re.escape(s) for s in sorted(_trans_species, key=len, reverse=True))
)
_default_template_string = "{$M}_{{$C};{$S}}"


def _run_species_substitution(pattern):
    """Replace species codes in a string with their LaTeX equivalents.

    Parameters
    ----------
    pattern : str
        String potentially containing species codes.

    Returns
    -------
    tuple
        ``(new_string, count)`` from :func:`re.subn`.

    Notes
    -----
    Only species in the registry's ``SPECIES`` are substituted. Codes are tried
    longest first at each position.
    """

    def repl(x):
        """Return the TeX of the species matched by ``x``."""
        return _trans_species[x.group()]

    substitution = re.subn(_all_species_re, repl, pattern)

    return substitution


def _template_of(m):
    """Return the TeX template of measurement ``m``.

    A registry quantity's own template, or the default
    ``{$M}_{{$C};{$S}}`` with ``m`` as the symbol for a measurement the
    registry does not know.
    """
    entry = quantities.QUANTITIES.get(m)
    if entry is not None and entry.tex is not None:
        return entry.tex
    return _default_template_string


def _units_of(key):
    """Return the TeX of the display unit of ``key``, or ``???`` if it has none."""
    entry = quantities.QUANTITIES.get(key)
    if entry is None or entry.units is None:
        return "???"
    return entry.units


def format_with_units(tex, units, *, new_line=False):
    r"""Return the label-with-units string ``$tex <sep> \left[units\right]$``.

    The one home of this form: every label class builds its string here. The
    brackets are sized, ``\left[ \right]``, so they grow with their content,
    such as a fractional unit.

    Parameters
    ----------
    tex : str
        TeX of the quantity, without ``$``.
    units : str
        TeX of the units, without ``$``.
    new_line : bool, default False
        If True, the units go on a new line; otherwise ``\;`` separates them.

    Returns
    -------
    str
        The label as a TeX math string.
    """
    sep = "$\n$" if new_line else r"\;"
    left, right = r"\left[", r"\right]"
    return f"${tex} {sep} {left}{units}{right}$"


class Base(ABC):
    """Base class for all label objects."""

    def __init__(self):
        """Initialize the logger."""
        self._init_logger()
        self._description = None

    def __str__(self):
        return self.with_units

    def __repr__(self):
        # Makes debugging easier.
        return str(self.tex)

    def __gt__(self, other):
        return str(self) > str(other)

    def __le__(self, other):
        return str(self) <= str(other)

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    @property
    def logger(self):
        r"""Logger named ``<module>.<class name>``."""
        return self._logger

    def _init_logger(self, handlers=None):
        """Create a logger at the INFO level."""
        logger = logging.getLogger("{}.{}".format(__name__, self.__class__.__name__))
        self._logger = logger

    @property
    def description(self):
        """Optional human-readable description shown above the label."""
        return self._description

    def set_description(self, new):
        """Set the description string.

        Parameters
        ----------
        new : str or None
            Human-readable description. None disables the description.
        """
        if new is not None:
            new = str(new)
        self._description = new

    def _format_with_description(self, label_str):
        """Prepend description to label string if set.

        Parameters
        ----------
        label_str : str
            The formatted label (typically with TeX and units).

        Returns
        -------
        str
            Label with description prepended if set, otherwise unchanged.
        """
        if self.description:
            return f"{self.description}\n{label_str}"
        return label_str

    @property
    def with_units(self):
        r"""Label with units, as a TeX math string."""
        result = format_with_units(self.tex, self.units)
        return self._format_with_description(result)

    @property
    def tex(self):
        r"""TeX of the quantity."""
        return self._tex

    @property
    def units(self):
        r"""TeX of the units."""
        return self._units

    @property
    def path(self):
        r"""Save path for figures using this label."""
        return self._path


class TeXlabel(Base):
    r"""Create a LaTeX label from measurement, component and species information.

    The object can be used directly in plotting routines. String
    representation returns the formatted label with units.

    Notes
    -----
    Comparison operators and hashing use :class:`str` of the object so two
    labels representing the same quantity compare equal.
    """

    def __init__(
        self, mcs0, mcs1=None, axnorm=None, new_line_for_units=False, description=None
    ):
        """Instantiate the label.

        Parameters
        ----------
        mcs0 : tuple of str
            ``("M", "C", "S")`` where ``m`` is the measurement, ``c`` the
            component and ``s`` the species. Empty strings are allowed for
            components or species.
        mcs1 : tuple of str or None, optional
            Denominator for fraction style labels. Units are compared and set
            to dimensionless when equal.
        axnorm : {"c", "r", "t", "d"}, optional
            Axis normalization used when building colorbar labels.
        new_line_for_units : bool, default ``False``
            If ``True`` a newline separates label and units.
        description : str or None, optional
            Human-readable description displayed above the mathematical label.
        """
        super(TeXlabel, self).__init__()
        self.set_axnorm(axnorm)
        self.set_mcs(mcs0, mcs1)
        self.set_new_line_for_units(new_line_for_units)
        self.set_description(description)
        self.build_label()

    @property
    def mcs0(self):
        r"""``_MCS`` namedtuple (measurement, component, species) of the numerator."""
        return self._mcs0

    @property
    def mcs1(self):
        r"""``_MCS`` namedtuple of the denominator, or None."""
        return self._mcs1

    @property
    def new_line_for_units(self):
        r"""If True, units are placed on a new line."""
        return self._new_line_for_units

    @property
    def tex(self):
        r"""TeX of the quantity, set by ``build_label``."""
        return self._tex

    @property
    def units(self):
        r"""TeX of the units, set by ``build_label``."""
        return self._units

    @property
    def with_units(self):
        r"""Label with units, set by ``build_label``."""
        return self._with_units

    @property
    def path(self):
        r"""Save path, set by ``build_label``."""
        return self._path

    @property
    def axnorm(self):
        r"""Axis normalization key, or None."""
        return self._axnorm

    def set_mcs(self, mcs0, mcs1):
        r"""Store the numerator and optional denominator as ``_MCS`` namedtuples."""
        mcs0_ = _MCS(*mcs0)

        mcs1_ = None
        if mcs1 is not None:
            mcs1_ = _MCS(*mcs1)

        self._mcs0 = mcs0_
        self._mcs1 = mcs1_

    def set_new_line_for_units(self, new):
        r"""Set whether units are placed on a new line."""
        self._new_line_for_units = bool(new)

    def set_axnorm(self, new):
        r"""Set the axis normalization.

        Parameters
        ----------
        new : str, optional
            One of ``"c"``, ``"r"``, ``"t"``, ``"d"`` (case-insensitive), or None.
        """
        if isinstance(new, str):
            new = new.lower()

        assert new in (None, "c", "r", "t", "d")
        self._axnorm = new

    def make_species(self, pattern):
        r"""Replace each species code in ``pattern`` that has a TeX translation.

        Notes
        -----
        This equation might only work because :math:`a\rightarrow\alpha` is
        the only actual translation made and, based on lexsort order, would be
        the first group. This function may need to be updated for more complex
        patterns, e.g., if we translate something like
        :math:`\mathrm{He}^{2+}\rightarrow\text{He}^{2+}`.
        """

        substitution = _run_species_substitution(pattern)

        return substitution[0]

    def _build_one_label(self, mcs):
        m = mcs.m
        c = mcs.c
        s = mcs.s

        path = (
            "_".join(
                [
                    m.replace(r"/", "-OV-"),
                    c.replace(r"/", "-OV-"),
                    s.replace(r"/", "-OV-"),
                ]
            )
            .replace(",", "")
            .replace("__", "_")
            .replace(".", "")
            .strip("_")
            # The following two work jointly to remove cases
            # where the species leads the label and it is empty.
            .strip(r"{} \\")
            .strip(r", ")
        )

        err = False
        if "_err" in m:
            m = m.replace("_err", "")
            err = True

        m1 = m
        c1 = _trans_component.get(c, c)
        s1 = self.make_species(s)
        d = {"M": m1, "C": c1, "S": s1}

        template_string = _template_of(m)
        template = Template(template_string)

        tex = template.safe_substitute(**d)
        if err:
            tex = r"\sigma(%s)" % tex

        # clean up empty parentheses
        tex = (
            tex.replace(r"\; ()", "")
            .replace(r"\; {}", "")
            .replace("()", "")
            .replace("_{}", "")
            .replace("{{}}", "")
            .replace("{},", "")
            .replace("{};", "")
            .replace("{}", "")
            .replace(",}", "}")
            .replace("{,", "{")
            .replace(";}", "}")
            .replace("_{}", "")
            .rstrip("_")
            .strip(" ")
        )

        ukey = m
        if c in ("lat", "colat", "lon"):
            ukey = c

        units = _units_of(ukey)

        self.logger.debug(
            r"""Built TeX label
TeX        : %s
units      : %s
save path  : %s
template   : %s
         M : %s -> %s
         C : %s -> %s
         S : %s -> %s""",
            tex,
            units,
            path,
            template_string,
            m,
            m1,
            c if c else None,
            c1 if c1 else None,
            s if s else None,
            s1 if s1 else None,
        )

        return tex, units, path

    def _combine_tex_path_units_axnorm(self, tex, path, units):
        # TODO: Re-evaluate method name - "path" in name is misleading for a
        # display-focused method
        """Finalize label pieces with axis normalization."""
        axnorm = self.axnorm
        tex_norm = _trans_axnorm[axnorm]
        if tex_norm:
            units = r"\#"
            tex = r"\mathrm{%s \; Norm} \; %s" % (tex_norm, tex)  # noqa: W605
            path = path / (axnorm.upper() + "norm")

        with_units = format_with_units(tex, units, new_line=self.new_line_for_units)

        # Apply description formatting
        with_units = self._format_with_description(with_units)

        return tex, path, units, with_units

    def build_label(self):
        """Construct the complete label."""
        mcs0 = self.mcs0
        mcs1 = self.mcs1

        tex0, units0, path0 = self._build_one_label(mcs0)

        if mcs1 is not None:
            tex1, units1, path1 = self._build_one_label(mcs1)

            m0, m1 = mcs0.m, mcs1.m
            u0, u1 = (
                _units_of(m0.replace("_err", "")),
                _units_of(m1.replace("_err", "")),
            )
            if u0 == u1:
                units = r"\#"
            else:
                units = r"{}/{}".format(u0, u1)

            tex = "{}/{}".format(tex0, tex1)
            path = Path("-OV-".join([path0, path1]))

        else:
            tex = tex0
            units = units0
            path = Path(path0)

            tex1 = None
            units1 = None
            path1 = None

        tex, path, units, with_units = self._combine_tex_path_units_axnorm(
            tex, path, units
        )

        self.logger.debug(
            r"""Joined ratio label
TeX        : %s
units      : %s
with units : %s
save path  : %s
        T0 : %s
        U0 : %s
        P0 : %s
        T1 : %s
        U1 : %s
        P1 : %s""",
            tex,
            units,
            with_units,
            path,
            tex0,
            units0,
            path0,
            tex1,
            units1,
            path1,
        )

        self._tex = tex
        self._units = units
        self._with_units = with_units
        self._path = Path(path)
