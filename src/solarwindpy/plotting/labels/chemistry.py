"""Common chemistry labels."""

__all__ = [
    "mass_per_charge",
    "fip",
    "charge",
    "mass",
]

from .special import ManualLabel

#: Ion mass per charge, in AMU per elementary charge.
mass_per_charge = ManualLabel(
    r"\mathrm{M/Q}",
    r"\mathrm{AMU \, e^{-1}}",
    path="M-OV-Q",
)

#: First ionization potential, in eV.
fip = ManualLabel(r"\mathrm{FIP}", r"\mathrm{eV}", path="FIP")

#: Ion charge, in elementary charges.
charge = ManualLabel(
    r"\mathrm{Q}",
    r"\mathrm{e}",
    path="IonCharge",
)

#: Ion mass, in AMU.
mass = ManualLabel(r"\mathrm{M}", r"\mathrm{AMU}", path="IonMass")
