from .special import ManualLabel

mass_per_charge = ManualLabel(
    r"\mathrm{Solar Wind M/Q}".replace(" ", " \, "),  # noqa: W605
    r"\mathrm{AMU \, e^{-1}}",
    path="SolarWind_M-OV-Q",
)

fip = ManualLabel("FIP", r"\mathrm{eV}")

charge = ManualLabel(
    r"\mathrm{Solar Wind Q}".replace(" ", " \, "),  # noqa: W605
    r"\mathrm{e}",
    path="SolarWind_Q",
)

mass = ManualLabel("Ion Mass", r"\mathrm{AMU}")
