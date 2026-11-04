# Spent-When: PERMANENT(the repository stops maintaining a test suite)
# Supersedes: none
"""The quantity registry and the names core methods give their results.

The registry (:mod:`solarwindpy.core.quantities`) holds one entry per quantity,
keyed by the canonical name: the SI value of its display unit and the TeX of its
symbol and units. A short name is canonical when it is the same string at every
layer: the attribute or method, the returned Series ``.name``, the M- or C-level
label, and the registry key. These tests tie the core methods to the registry
keys, in both directions, on ``swp.examples.load_plasma()``.

``Plasma`` names a returned Series after its species, because the result is
gathered over the ``S`` level, so at the ``Plasma`` layer the method name is the
label that must be a registry key. DataFrame, ``Vector`` and ``Tensor`` returns
carry no reliable ``.name`` (it does not survive arithmetic), so for them the
attribute name is the label.

The registry is imported inside each test, so the file collects before the
module exists.
"""

import dataclasses
import importlib

import pandas as pd
import pytest

import solarwindpy as swp

# --- xfail reasons -----------------------------------------------------------


def _author(why):
    """Reason for a name the naming rule and the author's rulings leave open."""
    return f"for the author: {why}; remove this marker when the author decides"


def _xfail(reason):
    return pytest.mark.xfail(strict=True, reason=reason)


def _quantities():
    return importlib.import_module("solarwindpy.core.quantities")


# --- fixtures ----------------------------------------------------------------


@pytest.fixture(scope="module")
def plasma():
    """The packaged example plasma: species a, e, p1, p2, with a spacecraft."""
    return swp.examples.load_plasma()


@pytest.fixture(scope="module")
def turbulence(plasma):
    """Alfvenic turbulence of the protons; the window covers the 3 example rows."""
    return plasma.build_alfvenic_turbulence("p1", window=3, min_periods=1)


# --- the quantity table ------------------------------------------------------
#
# Each case is (owner, attribute, how to evaluate it, registry level, whether the
# result's `.name` is checked, pending reason or None). `how` takes (plasma,
# turbulence) and returns the result. Level "M" is a quantity (`QUANTITIES`),
# level "C" a component (`COMPONENTS`).

_P = "Plasma"
_I = "Ion"
_V = "Vector"
_B = "BField"
_T = "Tensor"
_SC = "Spacecraft"
_AT = "AlfvenicTurbulence"

CASES = [
    # Plasma: the method name is the label; the Series is named by species.
    (_P, "n", lambda p, t: p.n("p1"), "M", False, None),
    (_P, "rho", lambda p, t: p.rho("p1"), "M", False, None),
    (_P, "v", lambda p, t: p.v("p1"), "M", False, None),
    (_P, "w", lambda p, t: p.w("p1"), "M", False, None),
    (_P, "b", lambda p, t: p.b, "M", False, None),
    (_P, "pth", lambda p, t: p.pth("p1"), "M", False, None),
    (_P, "T", lambda p, t: p.T("p1"), "M", False, None),
    (_P, "beta", lambda p, t: p.beta("p1"), "M", False, None),
    (_P, "R", lambda p, t: p.R("p1"), "M", False, None),
    (_P, "dv", lambda p, t: p.dv("p1", "a"), "M", False, None),
    (_P, "pdv", lambda p, t: p.pdv("p1", "a"), "M", False, None),
    (_P, "cs", lambda p, t: p.cs("p1"), "M", False, None),
    (_P, "ca", lambda p, t: p.ca("p1"), "M", False, None),
    (_P, "afsq", lambda p, t: p.afsq("p1"), "M", False, None),
    (_P, "caani", lambda p, t: p.caani("p1"), "M", False, None),
    (_P, "lnlambda", lambda p, t: p.lnlambda("p1", "a"), "M", False, None),
    (_P, "nuc", lambda p, t: p.nuc("p1", "a"), "M", False, None),
    (_P, "nc", lambda p, t: p.nc("p1", "a"), "M", False, None),
    (_P, "vdf_ratio", lambda p, t: p.vdf_ratio(), "M", False, None),
    (_P, "qpar", lambda p, t: p.qpar("p1+a"), "M", False, None),
    (_P, "Wk", lambda p, t: p.Wk("p1"), "M", False, None),
    # Ion: a Series result carries the label as its `.name`.
    (_I, "n", lambda p, t: p.p1.n, "M", True, None),
    (_I, "rho", lambda p, t: p.p1.rho, "M", True, None),
    (_I, "v", lambda p, t: p.p1.v, "M", False, None),
    (_I, "w", lambda p, t: p.p1.w, "M", False, None),
    (_I, "pth", lambda p, t: p.p1.pth, "M", False, None),
    (_I, "T", lambda p, t: p.p1.T, "M", False, None),
    (_I, "R", lambda p, t: p.p1.R, "M", True, None),
    (_I, "cs", lambda p, t: p.p1.cs, "M", False, None),
    (_I, "Wk", lambda p, t: p.p1.Wk, "M", True, None),
    # Vector and BField.
    (_V, "mag", lambda p, t: p.p1.v.mag, "C", True, None),
    # The xy-plane magnitude shares the string `rho` with mass density (F74),
    # one level apart.
    (_V, "rho", lambda p, t: p.p1.v.rho, "C", True, None),
    (_V, "colat", lambda p, t: p.p1.v.colat, "C", True, None),
    (_V, "lat", lambda p, t: p.p1.v.lat, "C", True, None),
    (_V, "lon", lambda p, t: p.p1.v.lon, "C", True, None),
    (_V, "cos_theta", lambda p, t: p.p1.v.cos_theta(p.b), "M", True, None),
    (_B, "pb", lambda p, t: p.b.pb, "M", True, None),
    # Tensor.
    (_T, "mag", lambda p, t: p.p1.w.mag, "C", True, None),
    # Spacecraft.
    (_SC, "pos", lambda p, t: p.sc.pos, "M", False, None),
    (_SC, "v", lambda p, t: p.sc.v, "M", False, None),
    (_SC, "carr", lambda p, t: p.sc.carr, "M", False, None),
    (_SC, "distance2sun", lambda p, t: p.sc.distance2sun, "M", True, None),
    # AlfvenicTurbulence.
    (_AT, "v", lambda p, t: t.v, "M", False, None),
    (_AT, "b", lambda p, t: t.b, "M", False, None),
    (_AT, "zp", lambda p, t: t.zp, "M", False, None),
    (_AT, "zm", lambda p, t: t.zm, "M", False, None),
    (_AT, "ep", lambda p, t: t.ep, "M", True, None),
    (_AT, "em", lambda p, t: t.em, "M", True, None),
    (_AT, "ev", lambda p, t: t.ev, "M", True, None),
    (_AT, "eb", lambda p, t: t.eb, "M", True, None),
    (_AT, "etot", lambda p, t: t.etot, "M", True, None),
    (_AT, "eres", lambda p, t: t.eres, "M", True, None),
    (_AT, "sigma_r", lambda p, t: t.sigma_r, "M", True, None),
    (_AT, "sigma_c", lambda p, t: t.sigma_c, "M", True, None),
    (
        _AT,
        "cross_helicity",
        lambda p, t: t.cross_helicity,
        "M",
        True,
        None,
    ),
    (
        _AT,
        "rA",
        lambda p, t: t.rA,
        "M",
        True,
        None,
    ),
    (
        _AT,
        "rE",
        lambda p, t: t.rE,
        "M",
        True,
        None,
    ),
]

#: Public members that are not quantities: containers, verbs, setters and the
#: machinery every core object shares.
_SHARED = {"constants", "data", "head", "logger", "mi_tuples", "set_data", "tail"}
NOT_QUANTITIES = {
    _P: {
        "aux",
        "build_alfvenic_turbulence",
        "drop_species",
        "epoch",
        "estimate_electrons",
        "ions",
        "load_from_file",
        "save",
        "sc",
        "set_aux",
        "set_sc",
        "species",
    },
    _I: {"species"},
    _V: {"cartesian", "project", "uv"},
    _T: set(),
    _SC: {"frame", "name", "set_frame_name"},
    _AT: {"averaging_info", "measurements", "polarity", "species"},
}
NOT_QUANTITIES[_B] = NOT_QUANTITIES[_V]
_SHARED |= {"units"}


def _with_marks(case):
    owner, attr, how, level, check_name, pending = case
    marks = [] if pending is None else [_xfail(pending)]
    return pytest.param(
        owner, attr, how, level, check_name, id=f"{owner}.{attr}", marks=marks
    )


@pytest.mark.parametrize(
    "owner, attr, how, level, check_name", [_with_marks(c) for c in CASES]
)
def test_quantity_name_is_a_registry_key(
    plasma, turbulence, owner, attr, how, level, check_name
):
    """Each core quantity's label is a registry key, the same string as its attribute.

    At the Ion, Vector, BField, Tensor, Spacecraft and AlfvenicTurbulence layers a
    Series result also carries that label as its ``.name``.

    ON FAILURE: the code is wrong, unless the author renames the quantity; then
    update its row in CASES.
    """
    quantities = _quantities()
    table = quantities.QUANTITIES if level == "M" else quantities.COMPONENTS
    result = how(plasma, turbulence)
    assert attr in table
    if check_name:
        assert isinstance(result, pd.Series)
        assert result.name == attr


def _owner_classes():
    from solarwindpy.core import alfvenic_turbulence, ions, plasma, spacecraft
    from solarwindpy.core import tensor, vector

    return {
        _P: plasma.Plasma,
        _I: ions.Ion,
        _V: vector.Vector,
        _B: vector.BField,
        _T: tensor.Tensor,
        _SC: spacecraft.Spacecraft,
        _AT: alfvenic_turbulence.AlfvenicTurbulence,
    }


@pytest.mark.parametrize(
    "owner",
    [_P, _I, _V, _B, _T, _SC, _AT],
)
def test_every_public_member_is_a_quantity_or_named_as_not_one(owner):
    """Every public member is a quantity in CASES or listed in NOT_QUANTITIES.

    A long name kept beside its short label (an alias) is neither, so it fails here.

    ON FAILURE: the code is wrong, unless a member was added; then add it to
    CASES or NOT_QUANTITIES.
    """
    cls = _owner_classes()[owner]
    public = {n for n in dir(cls) if not n.startswith("_")}
    owners = (_V, _B) if owner == _B else (owner,)
    quantities = {c[1] for c in CASES if c[0] in owners}
    known = quantities | NOT_QUANTITIES[owner] | _SHARED
    assert sorted(public - known) == []


def test_every_converted_quantity_is_returned_by_a_method():
    """Every registry key with an SI factor is the label of some core quantity.

    ON FAILURE: the code is wrong, unless the entry was added for a new method;
    then add the method to CASES.
    """
    quantities = _quantities()
    returned = {c[1] for c in CASES if c[3] == "M"}
    converted = {k for k, q in quantities.QUANTITIES.items() if q.si is not None}
    assert sorted(converted - returned) == []


def test_every_registry_entry_is_used_by_a_method_or_a_label():
    """Every quantity is either returned by a method or labelled with TeX.

    A key with neither is reachable from nothing.

    ON FAILURE: the code is wrong.
    """
    quantities = _quantities()
    returned = {c[1] for c in CASES if c[3] == "M"}
    unused = {
        k
        for k, q in quantities.QUANTITIES.items()
        if q.tex is None and k not in returned
    }
    assert sorted(unused) == []


def test_units_holds_exactly_the_registry_si_factors():
    """``Units`` holds the registry's SI factors, under the registry keys.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.core import units_constants

    quantities = _quantities()
    expected = {k: q.si for k, q in quantities.QUANTITIES.items() if q.si is not None}
    units = units_constants.Units()
    got = {f.name: getattr(units, f.name) for f in dataclasses.fields(units)}
    assert got == expected


# --- the author's rulings on names (o9) --------------------------------------


@pytest.mark.parametrize(
    "alias",
    [
        "pdynamic",
        "heat_flux",
    ],
)
def test_plasma_has_one_name_per_quantity(alias):
    """``pdv`` and ``qpar`` are the canonical names; the long aliases are gone.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.core import plasma

    assert not hasattr(plasma.Plasma, alias)


@pytest.mark.parametrize("method", ["afsq", "caani"])
def test_dynamic_pressure_keyword_is_pdv(plasma, method):
    """The keyword that would add dynamic pressure is ``pdv=``, the method's name.

    Including it is not implemented, so passing it raises NotImplementedError.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(NotImplementedError):
        getattr(plasma, method)("p1", pdv=True)


def test_heat_flux_is_qpar_at_every_layer():
    """Heat flux is ``qpar``: the registry key and the ``Units`` field; ``q`` is free.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.core import units_constants

    quantities = _quantities()
    assert "qpar" in quantities.QUANTITIES
    assert "q" not in quantities.QUANTITIES
    assert hasattr(units_constants.Units(), "qpar")


def test_vdf_ratio_is_the_registry_key():
    """The beam-to-core VDF ratio is ``vdf_ratio`` in the registry, not ``VDFratio``.

    ON FAILURE: the code is wrong.
    """
    quantities = _quantities()
    assert "vdf_ratio" in quantities.QUANTITIES
    assert "VDFratio" not in quantities.QUANTITIES


def test_fast_magnetosonic_speed_is_not_in_the_registry():
    """No method computes ``cfms``, so neither the registry nor ``Units`` holds it.

    ON FAILURE: the code is wrong, unless a method computes the fast
    magnetosonic speed again; then add its row to CASES.
    """
    from solarwindpy.core import units_constants

    assert "cfms" not in _quantities().QUANTITIES
    assert not hasattr(units_constants.Units(), "cfms")


def test_magnetic_pressure_is_capital_p_like_every_pressure():
    """Magnetic pressure renders P_B, as thermal pressure renders P.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.plotting.labels.base import TeXlabel

    assert TeXlabel(("pb", "", "")).tex == "P_B"


def test_position_is_pos_with_the_symbol_r(plasma):
    r"""Position is ``pos``: the stored M label, the accessor and the registry key.

    Its TeX symbol is the position vector, ``\mathbf{r}``. The radial
    component ``r`` at the C level is a different quantity and keeps its name.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.core import spacecraft

    quantities = _quantities()
    assert not hasattr(spacecraft.Spacecraft, "r")
    assert plasma.sc.pos.data.equals(plasma.sc.data.xs("pos", axis=1, level="M"))
    assert quantities.QUANTITIES["pos"].tex.startswith(r"\mathbf{r}")
    assert "r" in quantities.COMPONENTS


# --- species (F128) ----------------------------------------------------------


def test_registry_knows_every_species_core_knows():
    """Every species with a mass in core has a TeX symbol in the registry.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.core import units_constants

    quantities = _quantities()
    core_species = set(units_constants.Constants().m_in_mp.index)
    assert sorted(core_species - set(quantities.SPECIES)) == []


@pytest.mark.parametrize(
    "species, tex",
    [
        # TeX from the author's ruling: the base symbol, then the fit model.
        ("a_bimax", r"n_{\alpha,\mathrm{bimax}}"),
        ("p_bimax", r"n_{p,\mathrm{bimax}}"),
        # Guards: the species beside them keep their TeX.
        ("a", r"n_{\alpha}"),
        ("p1", r"n_{p_1}"),
    ],
)
def test_bimax_species_have_their_own_tex(species, tex):
    """A bimaxwellian fit species renders its own symbol, not a mangled neighbour.

    ON FAILURE: the code is wrong.
    """
    from solarwindpy.plotting.labels.base import TeXlabel

    assert TeXlabel(("n", "", species)).tex == tex
