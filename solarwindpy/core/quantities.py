#!/usr/bin/env python
r"""The quantity registry: one entry per quantity, keyed by its canonical name.

A name is canonical when it is the same string at every layer: the attribute or
method that computes the quantity, the returned Series ``.name``, the M- or
C-level column label, and the key here. Each :class:`Quantity` holds the SI
value of the quantity's display unit, the TeX template of its symbol and the TeX
of its display unit. Stored data stay in display units: ``core`` multiplies by
``si`` to convert, and ``plotting`` reads ``tex`` and ``units`` to label. The
method docstring is the one explanation of each quantity, so entries carry no
description.

This module sits at the bottom layer and imports nothing from the rest of
:mod:`solarwindpy`, so ``core`` and ``plotting`` both read it without importing
each other.

TeX templates are :class:`string.Template` strings: ``$C`` takes the TeX of the
component and ``$S`` the TeX of the species.
"""

__all__ = [
    "COMPONENTS",
    "QUANTITIES",
    "Quantity",
    "SPECIES",
    "UNIT_TEX",
]

from dataclasses import dataclass
from types import MappingProxyType

from scipy import constants


@dataclass(frozen=True)
class Quantity:
    r"""One registry entry.

    Parameters
    ----------
    tex : str or None
        TeX template of the symbol, with ``$C`` and ``$S`` placeholders. None
        when no label renders the quantity.
    units : str or None
        TeX of the display unit. None when no label states one.
    si : float or None, optional
        SI value of one display unit, for quantities ``core`` converts. None for
        a quantity only labels use.
    """

    tex: str | None
    units: str | None
    si: float | None = None


#: TeX of the display units several quantities share.
UNIT_TEX = MappingProxyType(
    {
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
        "Hz": r"\mathrm{Hz}",
    }
)

_U = UNIT_TEX
_KMS_SQ = r"(%s)^2" % _U["kms"]
_FLUX_DENSITY = r"\mathrm{\mu W \, m^{-2}}"

#: Every quantity, keyed by canonical name (M level).
QUANTITIES = MappingProxyType(
    {
        # Coordinates and angles.
        "gse": Quantity(r"{$C}_{\mathrm{GSE}}", _U["Re"]),
        "hci": Quantity(r"{$C}_{\mathrm{HCI}}", _U["Rs"]),
        "colat": Quantity(r"\theta_{$C}", _U["deg"]),
        "lat": Quantity(r"{lat}_{{$C};{$S}}", _U["deg"]),
        "lon": Quantity(r"{lon}_{{$C};{$S}}", _U["deg"]),
        "carr": Quantity(r"{$C}_\mathrm{Carrington}", _U["deg"]),
        "distance2sun": Quantity(
            r"\mathrm{Distance \; to \; Sun}", r"\mathrm{m}", si=1.0
        ),
        # Trigonometry.
        "theta": Quantity(r"{\theta}_{{$C};{$S}}", _U["deg"]),
        "phi": Quantity(r"{phi}_{{$C};{$S}}", _U["deg"]),
        "deg": Quantity(r"{deg}_{{$C};{$S}}", _U["deg"]),
        "cos": Quantity(r"\cos", _U["dimless"]),
        "cos_theta": Quantity(r"\cos \theta_{{$C}_{$S}}", _U["dimless"]),
        "cos_phi": Quantity(r"\cos \phi_{{$C}_{$S}}", _U["dimless"]),
        "ratio": Quantity(r"\mathrm{Ratio}", _U["dimless"]),
        # Timestamps.
        "year": Quantity(r"\mathrm{Year}", r"\mathrm{Year}"),
        "fdoy": Quantity(r"\mathrm{Fractional \; Day \; of \; Year}", r"\mathrm{fdoy}"),
        # Plasma measurements.
        "b": Quantity(r"B_{$C}", _U["b"], si=1e-9),
        "pb": Quantity(r"p_B", _U["pPa"]),
        "n": Quantity(r"n_{$S}", _U["cm-3"], si=1e6),
        "rho": Quantity(r"\rho_{$S}", r"m_p \; " + _U["cm-3"], si=1e6 * constants.m_p),
        "v": Quantity(r"{v}_{{$C};{$S}}", _U["kms"], si=1e3),
        "w": Quantity(r"{w}_{{$C};{$S}}", _U["kms"], si=1e3),
        "dv": Quantity(r"{\Delta v}_{{$C};{$S}}", _U["kms"], si=1e3),
        "dn": Quantity(r"\delta n_{{$S}}", _U["cm-3"]),
        "cs": Quantity(r"C_{s;$S}", _U["kms"], si=1e3),
        "ca": Quantity(r"C_{A;$S}", _U["kms"], si=1e3),
        "cfms": Quantity(None, _U["kms"], si=1e3),
        "afsq": Quantity(r"\mathrm{Anisotropy \, Factor}^2_{$S}", _U["dimless"]),
        "caani": Quantity(r"C^{(\mathrm{Ani})}_{A;$S} \; ($C)", _U["kms"]),
        # Temperatures, pressures, anisotropies and fluxes.
        "p": Quantity(r"{p}_{{$C};{$S}}", _U["pPa"]),
        "pth": Quantity(r"{P}_{{$C};{$S}}", _U["pPa"], si=1e-12),
        "T": Quantity(r"{T}_{{$C};{$S}}", r"10^5 \, \mathrm{K}", si=1e5),
        "qpar": Quantity(r"q_{{\parallel};{$S}}", _FLUX_DENSITY, si=1e-6),
        "qhat": Quantity(r"{\widehat{q}}_{{$C};{$S}}", _U["dimless"]),
        "Qhat": Quantity(r"{\widehat{q}}_{{$C};{$S}}", _U["dimless"]),
        "Wk": Quantity(r"W_{K;{$S}}", _FLUX_DENSITY, si=1e-6),
        "R": Quantity(r"{R}_{{$C};{$S}}", r"\perp/\parallel"),
        "beta": Quantity(r"{\beta}_{{$C};{$S}}", _U["dimless"], si=1.0),
        "dbeta": Quantity(r"{\Delta \beta}_{{$C};{$S}}", _U["dimless"]),
        "pdv": Quantity(r"P_{\Delta v_{$S}}", _U["pPa"]),
        "edv": Quantity(r"P_{\Delta v}/P_\mathrm{th}|_{$S}", _U["dimless"]),
        "flux": Quantity(
            r"\mathrm{Flux}_{$C}({$S})",
            r"10^{-9} \, %s \, s^{-1}" % _U["cm-3"].replace("-3", "-2"),
        ),
        # Collisions.
        "lnlambda": Quantity(r"\ln\Lambda_{$S}", _U["dimless"], si=1.0),
        "nuc": Quantity(r"\nu_{$C,$S}", r"10^{-7} \mathrm{Hz}", si=1e-7),
        "nc": Quantity(r"N_{C;$S}", _U["dimless"], si=1.0),
        # Fits and distributions.
        "chisq": Quantity(r"\chi^2", _U["dimless"]),
        "chisqnu": Quantity(r"\chi^2_\nu", _U["dimless"]),
        "VDFratio": Quantity(
            r"\mathrm{ln}(\frac{f_i}{f_j} \left(v_i\right)_{$S})", _U["dimless"]
        ),
        "ab": Quantity(r"A_{$S}", r"\%"),
        "e": Quantity(r"e\left({$C}_{$S}\right)", _U["kms"]),
        # Alfvenic turbulence.
        "zp": Quantity(r"Z^+_{{$S}}", _U["kms"]),
        "zm": Quantity(r"Z^-_{{$S}}", _U["kms"]),
        "ep": Quantity(r"e^+_{{$S}}", _KMS_SQ),
        "em": Quantity(r"e^-_{{$S}}", _KMS_SQ),
        "ev": Quantity(r"e^v_{{$S}}", _KMS_SQ),
        "eb": Quantity(r"e^b_{{$S}}", _KMS_SQ),
        "etot": Quantity(r"E_{{$S}}", _KMS_SQ),
        "eres": Quantity(r"e^r_{{$S}}", _KMS_SQ),
        "xhel": Quantity(r"e^c_{{$S}}", _KMS_SQ),
        "sigma_m": Quantity(r"\sigma_{m}", _U["dimless"]),
        "sigma_c": Quantity(r"\sigma_{c;{$S}}", _U["dimless"]),
        "sigma_r": Quantity(r"\sigma_{r;{$S}}", _U["dimless"]),
        "sigma_xy": Quantity(r"\sigma_{\parallel}", _U["dimless"]),
        "ra": Quantity(r"r_{A;{$S}}", _U["dimless"]),
        "re": Quantity(r"r_{E;{$S}}", _U["dimless"]),
        # Instabilities.
        "Wn": Quantity(r"\mathrm{W_n}", _U["dimless"]),
        "omegaR": Quantity(r"\omega_R", _U["Hz"]),
        "gamma": Quantity(r"\gamma", _U["Hz"]),
        "gamma_max": Quantity(r"\gamma_\mathrm{max}", _U["Hz"]),
        "gyro_freq": Quantity(r"\Omega_{{$S}}", _U["Hz"]),
        "eth": Quantity(r"\eth", r"\mathrm{eV}"),
        "kvec": Quantity(r"\mathbf{k}_{$C}\rho_{$S}", _U["dimless"]),
        "k": Quantity(r"k_{$C}\rho_{$S}", _U["dimless"]),
        "insta_power": Quantity(r"\mathcal{P}_{{$S}}", _U["unknown"]),
        # Spectra and energetic particles.
        "spectral_exponent": Quantity(r"\mathrm{Spectral \, Exponent}", _U["dimless"]),
        "MeV/nuc": Quantity(r"\mathrm{Energy}", r"\mathrm{MeV/nuc}"),
        "SEP_differential_flux": Quantity(
            r"{{$S}} \: dJ/dE", r"\mathrm{\frac{\#}{cm^2 \, sr \, s \, MeV/nuc}}"
        ),
        "SEP_intensity": Quantity(
            r"{{$S}} \: \mathrm{Intensity}", r"\mathrm{cm^2 \, sr \, s \, MeV/nuc}"
        ),
        "SEP_energy": Quantity(r"{{$S}} \: \mathrm{Energy}", r"\mathrm{MeV/nuc}"),
        "SEP_spectrum_index": Quantity(r"\gamma_{{$S}}", _U["dimless"]),
    }
)

#: TeX of each component (C level).
COMPONENTS = MappingProxyType(
    {
        # Coordinates.
        "x": r"X",
        "y": r"Y",
        "z": r"Z",
        "r": r"R",
        # A vector's magnitude is its bare symbol: B, not B_mag.
        "mag": r"",
        "rho": r"\rho",
        "colat": r"\theta",
        "lat": r"\lambda",
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
)


def _species_tex():
    """Return the TeX of every species: ions, then elements and isotopes."""
    tex = {
        "e": r"e^-",
        "a": r"\alpha",
        "a1": r"\alpha_1",
        "a2": r"\alpha_2",
        "a_bimax": r"\alpha,\mathrm{bimax}",
        "p": r"p",
        "p1": r"p_1",
        "p2": r"p_2",
        "p_bimax": r"p,\mathrm{bimax}",
        "pm": r"p,\mathrm{moment}",
        "he": r"\mathrm{He}",
        "dv": r"\Delta v",  # Because we want pdv in species
    }
    for s in ("C", "Fe", "He", "H", "Mg", "Ne", "N", "O", "Si", "S"):
        tex[s] = r"\mathrm{%s}" % s
    for mass, s in (
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
        tex[f"{mass}{s}"] = r"^{%s}\mathrm{%s}" % (mass, s)
    return tex


#: TeX of each species (S level): every species ``core`` knows, plus the
#: elements and isotopes composition labels use.
SPECIES = MappingProxyType(_species_tex())
