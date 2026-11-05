#!/usr/bin/env python
r"""The quantity registry: one entry per quantity, keyed by its canonical key.

A key is canonical when it is the same string at every layer: the attribute or
method that computes the quantity, the returned Series ``.name``, the M- or
C-level column label, and the key here. Each :class:`Quantity` holds the SI
value of the quantity's display unit, the TeX template of its symbol, the TeX
of its display unit and its display name, a few words such as "Number Density"
that a publication-format label prints above the symbol. Stored data stay in
display units: ``core`` multiplies by ``si`` to convert, and ``plotting`` reads
``tex``, ``units`` and ``name`` to label. The method docstring is the one
explanation of each quantity, so entries carry a short display name but no
description.

This module sits at the bottom layer and imports nothing from the rest of
:mod:`solarwindpy`, so ``core`` and ``plotting`` both read it without importing
each other.

TeX templates are :class:`string.Template` strings: ``$C`` takes the TeX of the
component, ``$A`` the component's code in upper case and ``$S`` the TeX of the
species. ``$A`` writes a frame's coordinate axes upper case, as is
conventional (:math:`X_\mathrm{GSE}`), where a vector's components are lower
case (:math:`v_x`).
"""

__all__ = [
    "COMPONENTS",
    "QUANTITIES",
    "Quantity",
    "SPECIES",
    "UNIT_TEX",
]

from dataclasses import KW_ONLY, dataclass
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
    name : str
        Keyword only. The quantity's display name, a few words in title case,
        such as "Number Density": the first line of a publication-format
        label. The quantity only, without species or component.
    """

    tex: str | None
    units: str | None
    si: float | None = None
    _: KW_ONLY
    name: str


#: TeX of the display units several quantities share.
UNIT_TEX = MappingProxyType(
    {
        "b": r"\mathrm{nT}",
        "Re": r"\mathrm{R}_\oplus",
        "Rs": r"\mathrm{R}_\odot",
        "kms": r"\mathrm{km \; s^{-1}}",
        "pPa": r"\mathrm{pPa}",
        "cm-3": r"\mathrm{cm}^{-3}",
        "dimless": r"\#",
        "unknown": r"???",
        "km": r"\mathrm{km}",
        "deg": r"\mathrm{deg.}",
        "Hz": r"\mathrm{Hz}",
    }
)

# IAU 2015 Resolution B3 nominal values, Prsa et al. (2016), AJ 152, 41,
# doi:10.3847/0004-6256/152/2/41: the units of GSE and HCI position.
_EARTH_EQUATORIAL_RADIUS = 6.3781e6  # [m]
_SOLAR_RADIUS = 695.7e6  # [m]

_U = UNIT_TEX
_KMS_SQ = r"(%s)^2" % _U["kms"]
_FLUX_DENSITY = r"\mathrm{\mu W \, m^{-2}}"

#: Every quantity, keyed by canonical key (M level).
QUANTITIES = MappingProxyType(
    {
        # Coordinates and angles.
        # A frame's position is in its body's radius; `Spacecraft.distance2sun`
        # converts with it.
        "gse": Quantity(
            r"{$A}_{\mathrm{GSE}}",
            _U["Re"],
            si=_EARTH_EQUATORIAL_RADIUS,
            name="GSE Position",
        ),
        "hci": Quantity(
            r"{$A}_{\mathrm{HCI}}", _U["Rs"], si=_SOLAR_RADIUS, name="HCI Position"
        ),
        "colat": Quantity(r"\theta_{$C}", _U["deg"], name="Colatitude"),
        "lat": Quantity(r"{lat}_{{$C};{$S}}", _U["deg"], name="Latitude"),
        "lon": Quantity(r"{lon}_{{$C};{$S}}", _U["deg"], name="Longitude"),
        "carr": Quantity(
            r"{$C}_\mathrm{Carrington}", _U["deg"], name="Carrington Coordinate"
        ),
        # The unit depends on the frame, so the entry states none: the frame
        # entries (gse, hci) carry it, and `Spacecraft.pos_units` exposes it.
        "pos": Quantity(r"\mathbf{r}_{$C}", None, name="Position"),
        "distance2sun": Quantity(
            r"\mathrm{Distance \; to \; Sun}",
            r"\mathrm{m}",
            si=1.0,
            name="Distance to Sun",
        ),
        # Trigonometry.
        "theta": Quantity(r"{\theta}_{{$C};{$S}}", _U["deg"], name="Polar Angle"),
        "phi": Quantity(r"{phi}_{{$C};{$S}}", _U["deg"], name="Azimuthal Angle"),
        "deg": Quantity(r"{deg}_{{$C};{$S}}", _U["deg"], name="Angle"),
        "cos": Quantity(r"\cos", _U["dimless"], name="Cosine"),
        "cos_theta": Quantity(
            r"\cos \theta_{{$C}_{$S}}", _U["dimless"], name="Angle Cosine"
        ),
        "cos_phi": Quantity(
            r"\cos \phi_{{$C}_{$S}}", _U["dimless"], name="Azimuthal Angle Cosine"
        ),
        "ratio": Quantity(r"\mathrm{Ratio}", _U["dimless"], name="Ratio"),
        # Timestamps.
        "year": Quantity(r"\mathrm{Year}", r"\mathrm{Year}", name="Year"),
        "fdoy": Quantity(
            r"\mathrm{Fractional \; Day \; of \; Year}",
            r"\mathrm{fdoy}",
            name="Fractional Day of Year",
        ),
        # Plasma measurements.
        "b": Quantity(r"B_{$C}", _U["b"], si=1e-9, name="Magnetic Field"),
        "pb": Quantity(r"P_B", _U["pPa"], name="Magnetic Pressure"),
        "n": Quantity(r"n_{$S}", _U["cm-3"], si=1e6, name="Number Density"),
        "rho": Quantity(
            r"\rho_{$S}",
            r"m_p \; " + _U["cm-3"],
            si=1e6 * constants.m_p,
            name="Mass Density",
        ),
        "v": Quantity(r"{v}_{{$C};{$S}}", _U["kms"], si=1e3, name="Velocity"),
        "w": Quantity(r"{w}_{{$C};{$S}}", _U["kms"], si=1e3, name="Thermal Speed"),
        "dv": Quantity(
            r"{\Delta v}_{{$C};{$S}}", _U["kms"], si=1e3, name="Differential Flow"
        ),
        "dn": Quantity(r"\delta n_{{$S}}", _U["cm-3"], name="Density Fluctuation"),
        "cs": Quantity(r"C_{s;$S}", _U["kms"], si=1e3, name="Sound Speed"),
        "ca": Quantity(r"C_{A;$S}", _U["kms"], si=1e3, name="Alfven Speed"),
        "afsq": Quantity(
            r"\mathrm{Anisotropy \, Factor}^2_{$S}",
            _U["dimless"],
            name="Anisotropy Factor Squared",
        ),
        "caani": Quantity(
            r"C^{(\mathrm{Ani})}_{A;$S} \; ($C)",
            _U["kms"],
            name="Anisotropic Alfven Speed",
        ),
        # Temperatures, pressures, anisotropies and fluxes.
        "p": Quantity(r"{p}_{{$C};{$S}}", _U["pPa"], name="Pressure"),
        "pth": Quantity(
            r"{P}_{{$C};{$S}}", _U["pPa"], si=1e-12, name="Thermal Pressure"
        ),
        "T": Quantity(
            r"{T}_{{$C};{$S}}", r"10^5 \, \mathrm{K}", si=1e5, name="Temperature"
        ),
        "qpar": Quantity(
            r"q_{{\parallel};{$S}}", _FLUX_DENSITY, si=1e-6, name="Parallel Heat Flux"
        ),
        "qhat": Quantity(
            r"{\widehat{q}}_{{$C};{$S}}", _U["dimless"], name="Normalized Heat Flux"
        ),
        "Qhat": Quantity(
            r"{\widehat{q}}_{{$C};{$S}}", _U["dimless"], name="Normalized Heat Flux"
        ),
        "Wk": Quantity(
            r"W_{K;{$S}}", _FLUX_DENSITY, si=1e-6, name="Kinetic Energy Flux"
        ),
        "R": Quantity(r"{R}_{{$C};{$S}}", _U["dimless"], name="Temperature Anisotropy"),
        "beta": Quantity(
            r"{\beta}_{{$C};{$S}}", _U["dimless"], si=1.0, name="Plasma Beta"
        ),
        "dbeta": Quantity(
            r"{\Delta \beta}_{{$C};{$S}}", _U["dimless"], name="Beta Difference"
        ),
        "pdv": Quantity(r"P_{\Delta v_{$S}}", _U["pPa"], name="Drift Pressure"),
        "edv": Quantity(
            r"P_{\Delta v}/P_\mathrm{th}|_{$S}",
            _U["dimless"],
            name="Drift to Thermal Pressure",
        ),
        "flux": Quantity(
            r"\mathrm{Flux}_{$C}({$S})",
            r"10^{-9} \, %s \, s^{-1}" % _U["cm-3"].replace("-3", "-2"),
            name="Particle Flux",
        ),
        # Collisions.
        "lnlambda": Quantity(
            r"\ln\Lambda_{$S}", _U["dimless"], si=1.0, name="Coulomb Logarithm"
        ),
        "nuc": Quantity(
            r"\nu_{$C,$S}", r"10^{-7} \mathrm{Hz}", si=1e-7, name="Collision Rate"
        ),
        "nc": Quantity(r"N_{C;$S}", _U["dimless"], si=1.0, name="Coulomb Number"),
        # Fits and distributions.
        "chisq": Quantity(r"\chi^2", _U["dimless"], name="Chi-Squared"),
        "chisqnu": Quantity(r"\chi^2_\nu", _U["dimless"], name="Reduced Chi-Squared"),
        "vdf_ratio": Quantity(
            r"\mathrm{ln}(\frac{f_i}{f_j} \left(v_i\right)_{$S})",
            _U["dimless"],
            name="VDF Ratio",
        ),
        "ab": Quantity(r"A_{$S}", r"\%", name="Abundance"),
        "e": Quantity(r"e\left({$C}_{$S}\right)", _U["kms"], name="E Term"),
        # Alfvenic turbulence.
        "zp": Quantity(r"Z^+_{{$S}}", _U["kms"], name="Elsasser Variable Z+"),
        "zm": Quantity(r"Z^-_{{$S}}", _U["kms"], name="Elsasser Variable Z-"),
        "ep": Quantity(r"e^+_{{$S}}", _KMS_SQ, name="Z+ Energy"),
        "em": Quantity(r"e^-_{{$S}}", _KMS_SQ, name="Z- Energy"),
        "ev": Quantity(r"e^v_{{$S}}", _KMS_SQ, name="Kinetic Fluctuation Energy"),
        "eb": Quantity(r"e^b_{{$S}}", _KMS_SQ, name="Magnetic Fluctuation Energy"),
        "etot": Quantity(r"E_{{$S}}", _KMS_SQ, name="Total Fluctuation Energy"),
        "eres": Quantity(r"e^r_{{$S}}", _KMS_SQ, name="Residual Energy"),
        "cross_helicity": Quantity(r"e^c_{{$S}}", _KMS_SQ, name="Cross Helicity"),
        "sigma_m": Quantity(
            r"\sigma_{m}", _U["dimless"], name="Normalized Magnetic Helicity"
        ),
        "sigma_c": Quantity(
            r"\sigma_{c;{$S}}", _U["dimless"], name="Normalized Cross Helicity"
        ),
        "sigma_r": Quantity(
            r"\sigma_{r;{$S}}", _U["dimless"], name="Normalized Residual Energy"
        ),
        "sigma_xy": Quantity(
            r"\sigma_{\parallel}", _U["dimless"], name="Parallel Sigma"
        ),
        "rA": Quantity(r"r_{A;{$S}}", _U["dimless"], name="Alfven Ratio"),
        "rE": Quantity(r"r_{E;{$S}}", _U["dimless"], name="Elsasser Ratio"),
        # Instabilities.
        "Wn": Quantity(r"\mathrm{W_n}", _U["dimless"], name="Wn"),
        "omegaR": Quantity(r"\omega_R", _U["Hz"], name="Real Frequency"),
        "gamma": Quantity(r"\gamma", _U["Hz"], name="Growth Rate"),
        "gamma_max": Quantity(
            r"\gamma_\mathrm{max}", _U["Hz"], name="Maximum Growth Rate"
        ),
        "gyro_freq": Quantity(r"\Omega_{{$S}}", _U["Hz"], name="Gyrofrequency"),
        "eth": Quantity(r"\eth", r"\mathrm{eV}", name="Eth"),
        "kvec": Quantity(
            r"\mathbf{k}_{$C}\rho_{$S}", _U["dimless"], name="Wave Vector"
        ),
        "k": Quantity(r"k_{$C}\rho_{$S}", _U["dimless"], name="Wavenumber"),
        "insta_power": Quantity(
            r"\mathcal{P}_{{$S}}", _U["unknown"], name="Instability Power"
        ),
        # Spectra and energetic particles.
        "spectral_exponent": Quantity(
            r"\mathrm{Spectral \, Exponent}", _U["dimless"], name="Spectral Exponent"
        ),
        "MeV/nuc": Quantity(
            r"\mathrm{Energy}", r"\mathrm{MeV/nuc}", name="Energy per Nucleon"
        ),
        "SEP_differential_flux": Quantity(
            r"{{$S}} \: dJ/dE",
            r"\mathrm{\frac{\#}{cm^2 \, sr \, s \, MeV/nuc}}",
            name="SEP Differential Flux",
        ),
        "SEP_intensity": Quantity(
            r"{{$S}} \: \mathrm{Intensity}",
            r"\mathrm{cm^2 \, sr \, s \, MeV/nuc}",
            name="SEP Intensity",
        ),
        "SEP_energy": Quantity(
            r"{{$S}} \: \mathrm{Energy}", r"\mathrm{MeV/nuc}", name="SEP Energy"
        ),
        "SEP_spectrum_index": Quantity(
            r"\gamma_{{$S}}", _U["dimless"], name="SEP Spectral Index"
        ),
    }
)

#: TeX of each component (C level).
COMPONENTS = MappingProxyType(
    {
        # Cartesian components subscript lower case (v_x); a frame entry's
        # template writes its axes upper case with `$A` (X_GSE).
        "x": r"x",
        "y": r"y",
        "z": r"z",
        "r": r"R",
        # A vector's magnitude is its bare symbol: B, not B_mag.
        "mag": r"",
        "rho": r"\rho",
        "colat": r"\theta",
        "lat": r"\lambda",
        "lon": r"\phi",
        "R": r"\mathrm{R}",
        # A tensor quantity's scalar is its bare symbol, like a magnitude.
        "scalar": r"",
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
