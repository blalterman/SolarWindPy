#!/usr/bin/env python
r"""Tools for creating physical quantity plot labels."""
import pdb  # noqa: F401
import logging
import re
from abc import ABC
from pathlib import Path
from string import Template as StringTemplate
from collections import namedtuple

MCS = namedtuple("MCS", "m,c,s")


__isotope_species = r"^{%s}\mathrm{%s}"
_trans_species = {
    "e": r"e^-",
    "a": r"\alpha",
    "a1": r"\alpha_1",
    "a2": r"\alpha_2",
    "p": r"p",
    "p_bimax": r"p",
    "p1": r"p_1",
    "p2": r"p_2",
    "he": r"\mathrm{He}",
    "dv": r"\Delta v",  # Because we want pdv in species
    #     "H": r"\mathrm{H}",
    #     "C": r"\mathrm{Fe}",
    #     "Fe": ,
    #     "He": ,
    #     "Mg": ,
    #     "Ne": ,
    #     "N": ,
    #     "O": ,
    #     "Si": ,
    #     "S": ,
    #     "3He": __isotope_species % (3, "He"),
    #     "4He": __isotope_species % (4, "He"),
    #     "12C": __isotope_species % (12, "C"),
    #     "14N": __isotope_species % (14, "N"),
    #     "16O": __isotope_species % (16, "O"),
    #     "20Ne": __isotope_species % (20, "Ne"),
    #     "24Mg": __isotope_species % (24, "Mg"),
    #     "28Si": __isotope_species % (28, "Si"),
    #     "32S": __isotope_species % (32, "S"),
    #     "40Ca": __isotope_species % (40, "Ca"),
    #     "Fe": r"\mathrm{Fe}",
}

for s in ("C", "Fe", "He", "H", "Mg", "Ne", "N", "O", "Si", "S"):
    _trans_species[s] = r"\mathrm{%s}" % s

for i, s in (
    (3, "He"),
    (4, "He"),
    (12, "C"),
    (14, "N"),
    (16, "O"),
    (20, "Ne"),
    (24, "Mg"),
    (28, "Si"),
    (32, "S"),
    (40, "Ca"),
):
    _trans_species[f"{i}{s}"] = __isotope_species % (i, s)

_trans_axnorm = {
    None: "",
    "c": "Col.",
    "r": "Row",
    "t": "Total",
    "d": "Density",
    "rd": "1D Probability Density",
    "cd": "1D Probability Density",
}

_all_species_re = sorted(_trans_species.keys())[
    ::-1
]  # Order so we check for p1 and p2 before p.
_all_species_re = re.compile(r"({})".format("|".join(_all_species_re)))
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
    Only substitutions defined in ``_trans_species`` are performed. The
    implementation relies on the simple mapping used in this module and may
    need to be revisited for more complex patterns.
    """

    def repl(x):
        return _trans_species[x.group()]

    substitution = re.subn(_all_species_re, repl, pattern)

    return substitution


_trans_measurement = {
    "pth": r"P",
    "beta": r"\beta",
    "dbeta": r"\Delta \beta",
    "dv": r"\Delta v",
    "qhat": r"\widehat{q}",
    "Qhat": r"\widehat{q}",
    "ab": r"A",
    "theta": r"\theta",
    "cos_theta": r"\cos\theta",
    "carr": r"\mathrm{Carrington}",
}

_inU = {
    "b": r"\mathrm{nT}",
    "Re": r"\mathrm{R}_\oplus",
    "Rs": r"\mathrm{R}_\odot",
    "kms": r"\mathrm{km \; s^{-1}}",
    "pPa": r"\mathrm{pPa}",
    "cm-3": r"\mathrm{cm}^{-3}",
    "dimless": r"\mathrm{\#}",
    "unknown": r"???",
    "km": r"\mathrm{km}",
    "deg": r"\mathrm{deg.}",
    #     "deg": r"\degree",
    "Hz": r"\mathrm{Hz}",
}

_trans_units = {
    # Vector components.
    "gse": _inU["Re"],
    "hci": _inU["Rs"],
    "colat": _inU["deg"],
    "lat": _inU["deg"],
    "lon": _inU["deg"],
    "carr": _inU["deg"],
    # Trig things.
    "theta": _inU["deg"],
    "phi": _inU["deg"],
    "deg": _inU["deg"],
    "cos": _inU["dimless"],
    "cos_theta": _inU["dimless"],
    # Timestamps.
    "year": r"\mathrm{Year}",
    "fdoy": r"\mathrm{fdoy}",
    # Plasma measurements.
    "b": _inU["b"],
    "n": _inU["cm-3"],
    "rho": r"m_p \; " + _inU["cm-3"],
    "v": _inU["kms"],
    "w": _inU["kms"],
    "dv": _inU["kms"],
    "dn": _inU["cm-3"],
    "cs": _inU["kms"],
    "ca": _inU["kms"],
    "afsq": _inU["dimless"],
    "caani": _inU["kms"],
    # Temperatures, pressures, and anisotropies.
    "p": _inU["pPa"],
    "pth": _inU["pPa"],
    "T": r"10^5 \, \mathrm{K}",
    "q": r"\mathrm{mW \, cm^{-2}}",  # heat flux,
    "qhat": _inU["dimless"],  # normalized heat flux
    "Q": r"\mathrm{mW \, cm^{-2}}",  # heating rate
    "R": r"\perp/\parallel",
    "beta": _inU["dimless"],
    "pdv": _inU["pPa"],
    "edv": _inU["dimless"],
    "S": r"\mathrm{eV \, cm^2 \, m_p^{-5/3}}",  # Specific Entropy
    # Flux
    "flux": r"10^{-9} \, %s \, s^{-1}" % _inU["cm-3"].replace("-3", "-2"),
    # Collisional things
    "lnlambda": _inU["dimless"],
    # TODO: verify that these units are Hertz.
    "nuc": r"10^{-7} \mathrm{Hz}",
    "nc": _inU["dimless"],
    "chisq": _inU["dimless"],
    "chisqnu": _inU["dimless"],
    "VDFratio": _inU["dimless"],
    "ab": r"\%",
    "e": _inU["kms"],
    # Alfvenic Turbulence
    "zp": _inU["kms"],
    "zm": _inU["kms"],
    "ep": r"(%s)^2" % _inU["kms"],
    "em": r"(%s)^2" % _inU["kms"],
    "ev": r"(%s)^2" % _inU["kms"],
    "etot": r"(%s)^2" % _inU["kms"],
    "eres": r"(%s)^2" % _inU["kms"],
    "xhel": r"(%s)^2" % _inU["kms"],
    "sigma_m": _inU["dimless"],
    "sigma_c": _inU["dimless"],
    "sigma_r": _inU["dimless"],
    "sigma_xy": _inU["dimless"],
    "ra": _inU["dimless"],
    "re": _inU["dimless"],
    # Nyquist things
    "Wn": _inU["dimless"],
    "omegaR": _inU["Hz"],
    "gamma": _inU["Hz"],
    "gamma_max": _inU["Hz"],
    "gyro_freq": _inU["Hz"],
    "kvec": _inU["dimless"],
    "k": _inU["dimless"],
    "insta_power": _inU["unknown"],
    # Solar Activity
    "Lalpha": r"\mathrm{W/m^2}",
    "f10.7": r"\mathrm{Solar \, Flux \, Unit \, (SFU)}",
    "CaK": r"Unknown \, Need \, to \, Read \, MetaData",
    "MgII": _inU["dimless"],
    # MISC
    "entropy": r"\mathrm{ln}(K \, \mathrm{cm}^{-3/2})",
    # Spectral things
    "spectral_exponent": _inU["dimless"],
    "MeV/nuc": r"\mathrm{MeV/nuc}",
    #     "SEP_differential_flux": r"\mathrm{\# \, cm^{-2} \, sr^{-1} \, s^{-1} \left(\frac{MeV}{nuc})^{-1}}",
    "SEP_differential_flux": r"\mathrm{\frac{\#}{cm^2 \, sr \, s \, MeV/nuc}}",
    "SEP_intensity": r"\mathrm{cm^2 \, sr \, s \, MeV/nuc}",
    "SEP_energy": r"\mathrm{MeV/nuc}",
    "SEP_spectrum_index": _inU["dimless"],
}

_trans_component = {
    # Coordinates
    "x": r"X",
    "y": r"Y",
    "z": r"Z",
    "r": r"R",
    "rho": r"\rho",
    "colat": r"\lambda",
    "lat": r"\theta",
    "lon": r"\phi",
    "R": r"\mathrm{R}",
    "scalar": r"\mathrm{scalar}",
    "theta": r"\theta",
    "phi": r"\phi",
    "per": r"\perp",
    "par": r"\parallel",
    "T": r"T",  # For use with temperature anisotropy.
    "p": r"p",  # For use with pressure anisotropy.
    "const": r"\mathrm{const}",  # constant for ("w", "const", "") label.
    # These will be replaced by dot products and regex.
    "bv": r"{\mathbf{B} \cdot \mathbf{v}}",
    "dv": r"\Delta v",  # For "e" terms
}

_templates = {
    # Timestamps
    "year": r"\mathrm{Year}",
    "fdoy": r"\mathrm{Fractional \; Day \; of \; Year}",
    # Coordinates, e.g. for location plots.
    "gse": r"{$C}_{\mathrm{GSE}}",
    "hci": r"{$C}_{\mathrm{HCI}}",
    "colat": r"\theta_{$C}",
    "carr": r"{$C}_\mathrm{Carrington}",
    "b": r"B_{$C}",
    "n": r"n_{$S}",
    "rho": r"\rho_{$S}",
    "q": r"q_{{$C};{$S}}",  # heat flux
    "Q": r"Q_{{$C};{$S}}",  # heating rate
    "S": r"S_{$S}",  # Specific entropy logarithm
    "ratio": r"\mathrm{Ratio}",
    "cos": r"\cos",
    "cos_theta": r"\cos \theta_{{$C}_{$S}}",
    "cos_phi": r"\cos \phi_{{$C}_{$S}}",
    # Characteristic Velocities
    "cs": r"C_{s;$S}",
    "ca": r"C_{A;$S}",
    "afsq": r"\mathrm{Anisotropy \, Factor}^2_{$S}",
    "caani": r"C^{(\mathrm{Ani})}_{A;$S} \; ($C)",
    # Collision things.
    "lnlambda": r"\ln\Lambda_{$S}",
    "nuc": r"\nu_{$C,$S}",
    "nc": r"N_{C;$S}",
    # Misc
    "VDFratio": r"\mathrm{ln}(\frac{f_i}{f_j} \left(v_i\right)_{$S})",
    "chisq": r"\chi^2",
    "chisqnu": r"\chi^2_\nu",
    "edv": r"P_{\Delta v}/P_\mathrm{th}|_{$S}",
    "pdv": r"P_{\Delta v_{$S}}",
    "ab": r"A_{$S}",
    "e": r"e\left({$C}_{$S}\right)",
    "entropy": r"\mathrm{S}_{$S}",
    # Alfvenic Turbulence
    "zp": r"Z^+_{{$S}}",
    "zm": r"Z^-_{{$S}}",
    "ep": r"e^+_{{$S}}",
    "em": r"e^-_{{$S}}",
    "ev": r"e^v_{{$S}}",
    "etot": r"E_{{$S}}",
    "eres": r"e^r_{{$S}}",
    "xhel": r"e^c_{{$S}}",
    "sigma_c": r"\sigma_{c;{$S}}",
    "sigma_r": r"\sigma_{r;{$S}}",
    "sigma_m": r"\sigma_{m}",
    "sigma_xy": r"\sigma_{\parallel}",
    "ra": r"r_{A;{$S}}",
    "re": r"r_{E;{$S}}",
    "dn": r"\delta n_{{$S}}",
    # Instability things
    "Wn": r"\mathrm{W_n}",
    "gamma": r"\gamma",
    "gamma_max": r"\gamma_\mathrm{max}",
    "omegaR": r"\omega_R",
    "gyro_freq": r"\Omega_{{$S}}",
    "eth": r"\eth",  # "_{{$C;$S}}"
    "kvec": r"\mathbf{k}_{$C}\rho_{$S}",
    "k": r"k_{$C}\rho_{$S}",
    "insta_power": r"\mathcal{P}_{{$S}}",
    # Solar Activity
    #     "ssn": r"{{$C}} \; \mathrm{SSN}",
    "Lalpha": r"\mathrm{L}\alpha",
    "f10.7": r"\mathrm{F}10.7",
    "CaK": r"\mathrm{CaK}",
    "MgII": r"\mathrm{MgII}",
    # Flux
    "flux": r"\mathrm{Flux}_{$C}({$S})",
    # Spectral Exponents
    "spectral_exponent": r"\mathrm{Spectral \, Exponent}",
    "MeV/nuc": r"\mathrm{Energy}",
    #     "differential_flux": r"\mathrm{\frac{dJ}{dE}}",
    "SEP_differential_flux": r"{{$S}} \: dJ/dE",
    "SEP_intensity": r"{{$S}} \: \mathrm{Intensity}",
    "SEP_energy": r"{{$S}} \: \mathrm{Energy}",
    "SEP_spectrum_index": r"\gamma_{{$S}}",
}


class Base(ABC):
    """Base class for all label objects."""

    def __init__(self):
        """Initialize the logger."""
        self._init_logger()

    def __str__(self):
        return self.with_units

    def __repr__(self):
        # Makes debugging easier.
        return str(self.tex)

    def __gt__(self, other):
        return str(self) > str(other)

    def __le__(self, other):
        return str(self) < str(other)

    def __eq__(self, other):
        return str(self) == str(other)

    def __geq__(self, other):
        return str(self) >= str(other)

    def __leq__(self, other):
        return str(self) <= str(other)

    def __hash__(self):
        return hash(str(self))

    @property
    def logger(self):
        return self._logger

    def _init_logger(self, handlers=None):
        """Create a logger at the INFO level."""
        logger = logging.getLogger("{}.{}".format(__name__, self.__class__.__name__))
        self._logger = logger

    @property
    def with_units(self):
        return rf"${self.tex} \; \left[{self.units}\right]$"

    @property
    def tex(self):
        return self._tex

    @property
    def units(self):
        return self._units

    @property
    def path(self):
        return self._path


class TeXlabel(Base):
    r"""Create a LaTeX label from measurement, component and species information.

    The object can be used directly in plotting routines. String
    representation returns the formatted label with units.

    Notes
    -----
    Comparison operators and hashing use :func:`str` of the object so two
    labels representing the same quantity compare equal.
    """

    def __init__(self, mcs0, mcs1=None, axnorm=None, new_line_for_units=False):
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
        """
        super(TeXlabel, self).__init__()
        self.set_axnorm(axnorm)
        self.set_mcs(mcs0, mcs1)
        self.set_new_line_for_units(new_line_for_units)
        self.build_label()

    @property
    def mcs0(self):
        return self._mcs0

    @property
    def mcs1(self):
        return self._mcs1

    @property
    def new_line_for_units(self):
        return self._new_line_for_units

    @property
    def tex(self):
        return self._tex

    @property
    def units(self):
        return self._units

    @property
    def with_units(self):
        return self._with_units

    @property
    def path(self):
        return self._path

    @property
    def axnorm(self):
        return self._axnorm

    def set_mcs(self, mcs0, mcs1):
        mcs0_ = MCS(*mcs0)

        mcs1_ = None
        if mcs1 is not None:
            mcs1_ = MCS(*mcs1)

        self._mcs0 = mcs0_
        self._mcs1 = mcs1_

    def set_new_line_for_units(self, new):
        self._new_line_for_units = bool(new)

    def set_axnorm(self, new):
        if isinstance(new, str):
            new = new.lower()

        assert new in (None, "c", "r", "t", "d")
        self._axnorm = new

    def make_species(self, pattern):
        r"""Basic substitution of any species within a species string if the.

        species has a substitution in the ion_species dictionary.

        Notes
        -----
        This equation might only work because :math:`a\rightarrow\alpha` is
        the only actual translation made and, based on lexsort order, would be
        the first group. This function may need to be updated for more complex
        patterns, e.g., if we translate something like
        :math:`\mathrm{He}^{2+}\rightarrow\text{He}^{2+}`.
        """

        #         def repl(x):
        #             return _trans_species[x.group()]

        substitution = _run_species_substitution(pattern)

        return substitution[0]

    def _build_one_label(self, mcs):

        m = mcs.m
        c = mcs.c
        s = mcs.s

        #         mcs = MCS(m, c, s)
        path = (
            "_".join(
                [
                    m.replace(r"/", "-OV-"),
                    c.replace(r"/", "-OV-"),
                    s.replace(r"/", "-OV-"),
                ]
            )
            .replace(",", "")
            .replace(",{", "{")
            .replace("{,", "{")
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

        m1 = _trans_measurement.get(m, m)
        c1 = _trans_component.get(c, c)
        s1 = self.make_species(s)
        d = {"M": m1, "C": c1, "S": s1}

        template_string = _templates.get(m, _default_template_string)
        template = StringTemplate(template_string)

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
            .replace("};{}", "}")
            .replace("};}", "}}")
            .replace(";}", "}")
            .replace("_{}", "")
            .rstrip("_")
            .strip(" ")
            #             .lstrip(r"\:")
            #             .rstrip(r"\:")
            #             .strip(r"\:")
            #             .strip(r"\;")
            .strip(" ")
        )

        #         with_units = r"$%s \; [%s]$" % (tex, _trans_units[m])
        ukey = m
        if c in ("lat", "colat", "lon"):
            ukey = c

        units = _trans_units.get(ukey, "???")

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
        """Finalize label pieces with axis normalization."""
        axnorm = self.axnorm
        tex_norm = _trans_axnorm[axnorm]
        if tex_norm:
            units = r"\#"
            tex = r"\mathrm{%s \; Norm} \; %s" % (tex_norm, tex)  # noqa: W605
            path = path / (axnorm.upper() + "norm")

        with_units = r"${tex} {sep} \left[{units}\right]$".format(
            tex=tex,
            sep="$\n$" if self.new_line_for_units else r"\;",
            units=units,
        )

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
                _trans_units.get(m0.replace("_err", ""), "???"),
                _trans_units.get(m1.replace("_err", ""), "???"),
            )
            if u0 == u1:
                units = r"\#"
            else:
                units = r"{}/{}".format(u0, u1)

            tex = "{}/{}".format(tex0, tex1)
            #             with_units = r"$%s \; [%s]$" % (tex, units)
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
