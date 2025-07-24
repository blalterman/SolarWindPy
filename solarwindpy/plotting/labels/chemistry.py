"""Common chemistry labels."""

from .special import ManualLabel

mass_per_charge = ManualLabel(
    r"\mathrm{M/Q}",
    r"\mathrm{AMU \, e^{-1}}",
    path="M-OV-Q",
)

fip = ManualLabel(r"\mathrm{FIP}", r"\mathrm{eV}", path="FIP")

charge = ManualLabel(
    r"\mathrm{Q}",
    r"\mathrm{e}",
    path="IonCharge",
)

mass = ManualLabel(r"\mathrm{M}", r"\mathrm{AMU}", path="IonMass")
