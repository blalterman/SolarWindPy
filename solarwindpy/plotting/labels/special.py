#!/usr/bin/env python
r"""Special labels not handled by :py:class:`TeXlabel`."""
import pdb  # noqa: F401
from pathlib import Path
from string import Template as StringTemplate
from string import Formatter as StringFormatter
from abc import abstractmethod
from . import base


class ArbitraryLabel(base.Base):
    """Abstract base class for custom labels."""

    def __init__(self):
        super().__init__()

    @abstractmethod
    def __str__(self):
        pass


#     @abstractproperty
#     def tex(self):
#         pass

#     @abstractproperty
#     def path(self):
#         pass


class ManualLabel(ArbitraryLabel):
    r"""Label defined by raw LaTeX text and unit."""

    def __init__(self, tex, unit, path=None):
        super().__init__()
        self.set_tex(tex)
        self.set_unit(unit)
        self._path = path

    def __str__(self):
        return (
            r"$\mathrm{%s} \; [%s]$"
            % (
                self.tex.replace(" ", r" \; "),
                self.unit,
            )
        ).replace(r"\; []", "")

    @property
    def tex(self):
        return self._tex

    @property
    def unit(self):
        return self._unit

    @property
    def path(self):
        path = self._path
        if path is None:
            path = self.tex.replace(" ", "-")
        path = Path(path)
        return path

    def set_tex(self, tex):
        self._tex = tex.strip("$")

    def set_unit(self, unit):
        unit = base._inU.get(unit, unit)
        self._unit = unit.strip("$")


class Vsw(base.Base):
    """Solar wind speed."""

    def __init__(self):
        super().__init__()

    #     def __str__(self):
    #         return r"$%s \; [\mathrm{km \, s^{-1}}]$" % self.tex

    @property
    def tex(self):
        return r"V_\mathrm{SW}"

    @property
    def units(self):
        return r"\mathrm{km \, s^{-1}}"

    @property
    def path(self):
        return Path("vsw")


class CarringtonRotation(ArbitraryLabel):
    """Carrington rotation count."""

    def __init__(self, short_label=True):
        """Instantiate the label."""
        super().__init__()
        self._short_label = bool(short_label)

    def __str__(self):
        return r"$%s \; [\#]$" % self.tex

    @property
    def short_label(self):
        return self._short_label

    @property
    def tex(self):
        if self.short_label:
            return r"\mathrm{CR}"
        else:
            return r"\mathrm{Carrington \; Rotation}"

    @property
    def path(self):
        return Path("CarrRot")


class Count(ArbitraryLabel):
    """Count histogram label."""

    def __init__(self, norm=None):
        super().__init__()
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
            if axnorm in ("r", "c", "t"):
                tex = r"\mathrm{%s Norm Count}" % base._trans_axnorm.get(axnorm)
            elif axnorm == "cd":
                tex = r"\mathrm{1D Probability Density}"
            elif axnorm == "rd":
                tex = r"\mathrm{1D Probability Density}"
            elif axnorm == "d":
                tex = r"\mathrm{Probability Density}"
            else:
                raise ValueError(f"Unrecognized axis normalization `{axnorm}`")
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


class Power(ArbitraryLabel):
    """Power spectrum label."""

    def __init__(self):
        super().__init__()

    def __str__(self):
        return rf"${self.tex} \; [{self.units}]$"

    @property
    def tex(self):
        return r"\mathrm{Power}"

    @property
    def units(self):
        return base._inU["dimless"]

    @property
    def path(self):
        return Path("power")


class Probability(ArbitraryLabel):
    """Probability that a quantity meets a comparison criterion."""

    def __init__(self, other_label, comparison=None):
        """Instantiate the label."""
        super().__init__()
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
        assert isinstance(other, (str, base.Base))
        self._other_label = other

    def set_comparison(self, new):
        if new is None:
            new = ""
        self._comparison = str(new)

    def _build_tex(self):
        other = self.other_label
        tex = r"\mathrm{Prob.}(%s %s)" % (other.tex, self.comparison)

        self._tex = tex.replace(" ", r" \, ")

    def _build_path(self):
        other = self.other_label
        other = str(other.path)
        other = other.replace(" ", "-")

        comp = (
            self.comparison.replace(">", "GT")
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
            .replace(r" ", "_")
        )

        path = Path(f"prob-{other}-{comp}")

        self._path = path

    def build_label(self):
        self._build_tex()
        self._build_path()


class CountOther(ArbitraryLabel):
    """Count of samples of another label fulfilling a comparison."""

    def __init__(self, other_label, comparison=None, new_line_for_units=False):
        """Instantiate the label."""
        super().__init__()
        self.set_other_label(other_label)
        self.set_comparison(comparison)
        self.set_new_line_for_units(new_line_for_units)

        self.build_label()

    def __str__(self):
        return r"${tex} {sep} [{units}]$".format(
            tex=self.tex,
            sep="$\n$" if self.new_line_for_units else r"\;",
            units=self.units,
        )

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
    def other_label(self):
        return self._other_label

    @property
    def comparison(self):
        return self._comparison

    @property
    def new_line_for_units(self):
        return self._new_line_for_units

    def set_new_line_for_units(self, new):
        self._new_line_for_units = bool(new)

    def set_other_label(self, other):
        assert isinstance(other, (str, base.Base))
        self._other_label = other

    def set_comparison(self, new):
        if new is None:
            new = ""
        self._comparison = str(new)

    def _build_tex(self):
        other = self.other_label
        tex = r"\mathrm{Count.}(%s %s)" % (other.tex, self.comparison)

        self._tex = tex.replace(" ", r" \, ")

    def _build_path(self):
        other = self.other_label
        other = str(other.path)
        other = other.replace(" ", "-")

        comp = (
            self.comparison.replace(">", "GT")
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

        path = Path(f"cnt-{other}-{comp}")

        self._path = path

    def build_label(self):
        self._build_tex()
        self._build_path()


class MathFcn(ArbitraryLabel):
    """Math function applied to another label."""

    def __init__(self, fcn, other_label, dimensionless=True, new_line_for_units=False):
        """Instantiate the label."""
        super().__init__()
        self.set_other_label(other_label)
        self.set_function(fcn)
        self.set_dimensionless(dimensionless)
        self.set_new_line_for_units(new_line_for_units)
        self.build_label()

    def __str__(self):
        sep = "$\n$" if self.new_line_for_units else r"\;"
        return rf"""${self.tex} {sep} \left[{self.units}\right]$"""

    @property
    def tex(self):
        return self._tex

    @property
    def units(self):
        if self.dimensionless:
            return base._inU["dimless"]

        return r"\mathrm{%s}\left(%s\right)" % (self.function, self.other_label.units)

    @property
    def path(self):
        return self._path

    @property
    def other_label(self):
        return self._other_label

    @property
    def function(self):
        return self._function

    @property
    def dimensionless(self):
        return self._dimensionless

    @property
    def new_line_for_units(self):
        return self._new_line_for_units

    def set_new_line_for_units(self, new):
        self._new_line_for_units = bool(new)

    def set_other_label(self, other):
        assert isinstance(other, (str, base.Base))
        self._other_label = other

    def set_function(self, new):
        if new is None:
            new = ""
        self._function = str(new)

    def set_dimensionless(self, new):
        self._dimensionless = bool(new)

    def _build_tex(self):
        #         try:
        #             tex = other.tex
        #         except AttributeError:
        tex = r"\mathrm{%s}(%s)" % (self.function, self.other_label.tex)

        return tex.replace(" ", r" \, ")

    def _build_path(self):
        other = self.other_label
        other = str(other.path)
        #         fcn = self.function
        fcn = (
            self.function.replace(r"\mathrm", "")
            .replace("{", "")
            .replace("}", "")
            .replace("\\", "")
            .replace(r"/", "-OV-")
        )

        path = Path(f"{fcn}-{other}")

        return path

    def build_label(self):
        self._tex = self._build_tex()
        self._path = self._build_path()


class Distance2Sun(ArbitraryLabel):
    """Distance to the Sun."""

    def __init__(self, units):
        super().__init__()
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


class SSN(ArbitraryLabel):
    """Sunspot number label."""

    def __init__(self, key):
        super().__init__()
        self.set_kind(key)

    def __str__(self):
        return r"$%s \; [\#]$" % self.tex

    @property
    def kind(self):
        return self._kind

    @property
    def path(self):
        return self._path

    @property
    def pretty_kind(self):
        kind = self.kind
        transform = {
            "M": "Monthly",
            "M13": "13 Month Smoothed",
            "D": "Daily",
            "Y": "Annual",
            "NM": "Normalized Monthly",
            "NM13": "Normalized 13 Month Smoothed",
            "ND": "Normalized Daily",
            "NY": "Normalized Yearly",
        }
        return transform[kind]

    @property
    def tex(self):
        return (r"\mathrm{%s SSN}" % self.pretty_kind).replace(" ", r" \; ")

    @property
    def units(self):
        return base._inU["dimless"]

    def set_kind(self, new):
        new = new.upper()
        assert new in ("M", "M13", "D", "Y", "NM", "NM13", "ND", "NY")
        self._kind = new
        self._path = Path(f"""{new.upper()!s}ssn""")


class ComparisonLable(ArbitraryLabel):
    """Label comparing two other labels via a function."""

    def __init__(self, labelA, labelB, fcn_name, fcn=None):
        """Instantiate the label."""
        super().__init__()
        self.set_constituents(labelA, labelB)
        self.set_function(fcn_name, fcn)
        self.build_label()

    def __str__(self):
        return r"${} \; [{}]$".format(self.tex, self.units)

    @property
    def tex(self):
        return self._tex

    @property
    def units(self):
        return self._units

    @property
    def path(self):
        return self._path

    @property
    def labelA(self):
        return self._labelA

    @property
    def labelB(self):
        return self._labelB

    @property
    def function(self):
        return self._function

    @property
    def function_name(self):
        r"""Basically for use with building :py:meth:`path`."""
        return self._function_name

    def set_constituents(self, labelA, labelB):
        if not isinstance(labelA, (str, base.Base)):
            raise TypeError
        if not isinstance(labelB, (str, base.Base)):
            raise TypeError

        if (
            hasattr(labelA, "units")
            and hasattr(labelB, "units")
            and not (labelA.units == labelB.units)
        ):
            raise ValueError(
                rf"""If both {self.__class__.__name__} labels have units, they must be the same.
labelA : {labelA.units}
labelB : {labelB.units}
"""
            )
        elif hasattr(labelA, "units") and hasattr(labelB, "units"):
            units = labelA.units

        else:
            units = "???"

        self._labelA = labelA
        self._labelB = labelB
        self._units = units

    def set_function(self, fcn_name, fcn):

        if fcn is None:
            get_fcn = fcn_name.lower()
            translate = {
                "subtract": r"{$labelA} - {$labelB}",
                "add": r"{$labelA} + {$labelB}",
                "multiply": r"{$labelA} \times {$labelB}",
            }
            fcn = translate.get(get_fcn)

        keys = [x[1] for x in StringFormatter().parse(fcn)]
        if not (("$labelA" in keys) and ("$labelB" in keys)):
            raise ValueError(
                rf"""{self.__class__.__name__}'s function must have the keys "$labelA" and "$labelB".
keys : {",".join(keys)}
"""
            )
        self._function = fcn
        self._function_name = fcn_name

    def _build_tex(self):
        labelA = self.labelA
        labelB = self.labelB
        function = self.function

        try:
            texA = labelA.tex
        except AttributeError:
            texA = labelA

        try:
            texB = labelB.tex
        except AttributeError:
            texB = labelB

        template = StringTemplate(function)
        tex = template.safe_substitute(labelA=texA, labelB=texB)

        while tex.find(r"\,\,") >= 0:
            tex = tex.replace(r"\,\,", r"\,")

        self._tex = tex

    def _build_path(self):
        labelA = self.labelA
        labelB = self.labelB

        try:
            pathA = labelA.path
        except AttributeError:
            pathA = labelA

        try:
            pathB = labelB.path
        except AttributeError:
            pathB = labelB

        pathA = str(pathA).replace(" ", "-")
        pathB = str(pathB).replace(" ", "-")

        function = self.function_name
        path = Path(f"{function}-{pathA}-{pathB}")

        self._path = path

    def build_label(self):
        self._build_tex()
        self._build_path()


class Xcorr(ArbitraryLabel):
    """Cross-correlation coefficient between two labels."""

    def __init__(self, labelA, labelB, method, short_tex=False):
        """Instantiate the label."""
        super().__init__()
        self.set_constituents(labelA, labelB)
        self.set_method(method)
        self.set_short_tex(short_tex)
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
    def short_tex(self):
        return self._short_tex

    @property
    def path(self):
        return self._path

    @property
    def labelA(self):
        return self._labelA

    @property
    def labelB(self):
        return self._labelB

    @property
    def method(self):
        return self._method

    def set_constituents(self, labelA, labelB):
        if not isinstance(labelA, (str, base.Base)):
            raise TypeError
        if not isinstance(labelB, (str, base.Base)):
            raise TypeError

        self._labelA = labelA
        self._labelB = labelB

    def set_method(self, new):
        self._method = str(new).title()

    def set_short_tex(self, new):
        self._short_tex = bool(new)

    def _build_tex(self):
        labelA = self.labelA
        labelB = self.labelB

        try:
            texA = labelA.tex
        except AttributeError:
            texA = labelA

        try:
            texB = labelB.tex
        except AttributeError:
            texB = labelB

        if self.short_tex:
            tex = r"\rho_{%s}(%s,%s)" % (self.method[0], texA, texB)
        else:
            tex = r"\mathrm{{%s}}(%s,%s)" % (self.method, texA, texB)

        tex = tex.replace(" ", r" \, ").replace(r" \, ", r"\,")
        while tex.find(r"\,\,") >= 0:
            tex = tex.replace(r"\,\,", r"\,")

        self._tex = tex

    def _build_path(self):
        labelA = self.labelA
        labelB = self.labelB

        try:
            pathA = labelA.path
        except AttributeError:
            pathA = labelA

        try:
            pathB = labelB.path
        except AttributeError:
            pathB = labelB

        pathA = str(pathA).replace(" ", "-")
        pathB = str(pathB).replace(" ", "-")

        method = self.method
        path = Path(f"Xcorr{method}-{pathA}-{pathB}")

        self._path = path

    def build_label(self):
        self._build_tex()
        self._build_path()
