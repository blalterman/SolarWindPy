"""Tests for ``TeXinfo``, the LaTeX annotation of a fit.

The annotation's wording and spacing are the author's to choose, so these tests
assert properties of it (which lines appear, in what order, whether each is a
closed math expression, whether a printed value reads back as the value given)
and never compare it to fixed text.
"""

import re
from types import SimpleNamespace

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.colors import to_rgba

from solarwindpy.fitfunctions.tex_info import TeXinfo
from tests.tolerances import exact

matplotlib.use("Agg")

# Chosen inputs: ``a`` has a negative exponent and ``b`` a positive one, so
# both branches of the 10^{X} conversion run; the function spans two lines.
POPT = {"a": 0.00123, "b": 456.0}
PSIGMA = {"a": 0.00001, "b": 2.0}
FUNCTION = "f(x)=a x + b\ny = 2"
CHISQ = SimpleNamespace(linear=1.5, robust=2.5)
RSQ = 0.99


def _guess():
    return {
        "a": SimpleNamespace(p0=0.5, bounds=(-1, 1)),
        "b": SimpleNamespace(p0=2.0, bounds=(0, 5)),
    }


@pytest.fixture
def texinfo():
    return TeXinfo(POPT, PSIGMA, FUNCTION, CHISQ, RSQ, _guess())


@pytest.fixture
def texinfo_greek():
    """The fixture with ``a`` and ``b`` written as Greek letters."""
    tex = TeXinfo(POPT, PSIGMA, FUNCTION, CHISQ, RSQ, _guess())
    tex.set_TeX_argnames(a="\\alpha", b="\\beta")
    return tex


def _lines(info):
    return info.split("\n")


def _math(line):
    """The content of a ``$ ... $`` annotation line."""
    return line.strip("$").strip()


def _param_line(info, name):
    """The annotation line reporting ``name = ...``."""
    (line,) = [ln for ln in _lines(info) if _math(ln).startswith(f"{name} = ")]
    return line


def _read_back(line):
    r"""``(value, uncertainty)`` read back from a parameter line, either notation.

    ``x \times 10^{n}`` is turned back into ``xen``; the uncertainty is None
    when the line has none.
    """
    text = _math(line).split(" = ", 1)[1]
    text = text.replace(r" \times 10^{", "e").replace("}", "").replace(" ", "")
    parts = text.split(r"\pm")
    value = float(parts[0])
    uncertainty = float(parts[1]) if len(parts) > 1 else None
    return value, uncertainty


def test_properties_return_the_constructor_inputs(texinfo_greek):
    """Each property returns what the constructor and setters were given.

    ON FAILURE: the code is wrong.
    """
    assert texinfo_greek.popt == POPT
    assert texinfo_greek.psigma == PSIGMA
    assert texinfo_greek.chisq_dof is CHISQ
    assert texinfo_greek.rsq == RSQ
    assert texinfo_greek.TeX_function == FUNCTION
    assert texinfo_greek.TeX_argnames == {"a": "\\alpha", "b": "\\beta"}
    assert texinfo_greek.extra_params == {}
    assert set(texinfo_greek.TeX_popt) == {"\\alpha", "\\beta"}
    assert "\\alpha" in texinfo_greek.initial_guess_info
    info = texinfo_greek.build_info(rsq=True)
    assert str(texinfo_greek) == info == texinfo_greek.info


def test_setters_store_values_without_checking_their_type(texinfo):
    """``set_chisq_dof``, ``set_rsq`` and ``set_TeX_function`` store what they get.

    ON FAILURE: the code is wrong, unless the author added type checks to
    these setters.
    """
    texinfo.set_chisq_dof("bad")
    texinfo.set_rsq("bad")
    texinfo.set_TeX_function(5)
    assert (texinfo.chisq_dof, texinfo.rsq, texinfo.TeX_function) == ("bad", "bad", 5)


def test_errors_name_what_was_wrong():
    """Each refused input raises its documented type, naming the offender.

    The expected substrings are the inputs chosen here: the key ``q``, the
    type ``list``, the TeX name ``zeta``, the keyword ``bogus``.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(ValueError, match=r"\(q\)"):
        TeXinfo({"q": 1}, {"b": 1}, "f", CHISQ, 0)
    with pytest.raises(TypeError, match="list"):
        TeXinfo({"a": 1}, {"a": 1}, "f", CHISQ, 0, [1])
    tex = TeXinfo({"a": 1}, {"a": 1}, "f", CHISQ, 0)
    with pytest.raises(TypeError, match="str"):
        tex.set_initial_guess_info("bad")
    with pytest.raises(ValueError, match="zeta"):
        tex.set_TeX_argnames(zeta="\\zeta")
    with pytest.raises(ValueError, match="bogus"):
        tex.build_info(bogus=True)
    with pytest.raises(TypeError, match="list"):
        tex.set_extra_params([1])
    with pytest.raises(TypeError, match="'A'"):
        tex.set_extra_params({"A": "two"})


def test_set_popt_psigma_refuses_inputs_that_are_not_mappings(texinfo):
    """A ``popt`` key missing from ``psigma``, or a non-mapping, is refused.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(ValueError):
        texinfo.set_popt_psigma("bad", {"a": 1})
    with pytest.raises(AttributeError):
        texinfo.set_popt_psigma({"a": 1}, "bad")
    with pytest.raises(ValueError, match=r"\(a\)"):
        texinfo.set_popt_psigma({"a": 1}, {"b": 1})


def test_set_tex_argnames_refuses_a_name_missing_from_the_initial_guess():
    """A parameter in ``popt`` but not in the initial guess info is refused.

    The check used to test membership in the formatted guess table, a string
    in which a short name is often a substring: here ``e`` is missing from
    the guess info but appears in the table's ``5.000e-01``, so the old check
    passed it.

    ON FAILURE: the code is wrong.
    """
    guess = {"a": SimpleNamespace(p0=0.5, bounds=(-1, 1))}
    tex = TeXinfo({"a": 1.0, "e": 2.0}, {"a": 0.1, "e": 0.1}, "f", CHISQ, 0, guess)
    assert "e" in tex.initial_guess_info  # the input exists to exercise this
    with pytest.raises(ValueError, match="e has no comparable pair in the initial"):
        tex.set_TeX_argnames(e="\\epsilon")
    tex.set_TeX_argnames(a="\\alpha")
    assert tex.TeX_argnames == {"a": "\\alpha"}


def test_set_tex_argnames_without_initial_guess_checks_only_popt():
    """With no initial guess info, a name in ``popt`` is accepted.

    ON FAILURE: the code is wrong.
    """
    tex = TeXinfo({"a": 1.0}, {"a": 0.1}, "f", CHISQ, 0)
    tex.set_TeX_argnames(a="\\alpha")
    assert set(tex.TeX_popt) == {"\\alpha"}


def test_every_annotation_line_is_blank_or_one_closed_math_expression(texinfo):
    """Under each option, every line is empty or a single ``$...$`` with balanced braces.

    ON FAILURE: the code is wrong.
    """
    options = [
        {},
        {"rsq": True},
        {"relative_error": True},
        {"convert_pow_10": False},
        {"strip_uncertainties": True},
        {"simplify_info_for_paper": True},
        {"chisq_dof": False},
    ]
    for kwargs in options:
        for line in _lines(texinfo.build_info(**kwargs)):
            if not line:
                continue
            assert line.startswith("$") and line.endswith("$"), (kwargs, line)
            assert line.count("$") == 2, (kwargs, line)
            assert line.count("{") == line.count("}"), (kwargs, line)


def test_each_line_of_the_function_is_its_own_annotation_line_in_order(texinfo):
    """The annotation opens with the TeX function, one line per function line.

    ON FAILURE: the code is wrong.
    """
    lines = _lines(texinfo.build_info())
    expected = FUNCTION.split("\n")
    assert [_math(ln) for ln in lines[: len(expected)]] == expected


def test_printed_parameters_read_back_as_the_formatted_values(texinfo):
    """Each parameter line reads back as ``val_uncert_2_string`` of its value.

    In 10^{X} notation and in eX notation, the printed value and uncertainty
    read back as the values ``val_uncert_2_string`` formats, and only the eX
    form keeps a digit followed by ``e+`` or ``e-``.

    ON FAILURE: the code is wrong.
    """
    pow10 = texinfo.build_info()
    plain = texinfo.build_info(convert_pow_10=False)
    for name in POPT:
        formatted = texinfo.val_uncert_2_string(POPT[name], PSIGMA[name])
        value, uncertainty = (float(v) for v in formatted.split(r" \pm "))
        assert _read_back(_param_line(pow10, name)) == exact((value, uncertainty))
        assert _read_back(_param_line(plain, name)) == exact((value, uncertainty))
        assert re.search(r"\de[+-]", _param_line(pow10, name)) is None
        assert formatted in _param_line(plain, name)


def test_strip_uncertainties_alone_removes_every_uncertainty(texinfo):
    r"""``strip_uncertainties=True`` drops the ``\pm`` term and keeps each value.

    ON FAILURE: the code is wrong.
    """
    info = texinfo.build_info(strip_uncertainties=True)
    assert r"\pm" not in info
    for name in POPT:
        value, uncertainty = _read_back(_param_line(info, name))
        assert uncertainty is None
        formatted = texinfo.val_uncert_2_string(POPT[name], PSIGMA[name])
        assert value == exact(float(formatted.split(r" \pm ")[0]))


def test_simplified_info_prints_plain_decimals():
    """``simplify_info_for_paper`` prints 2, not 2.0 x 10^0.

    ``a = 2 +- 0.1`` is formatted to the uncertainty's digit as 2.0e+00;
    simplifying for a paper strips the exponent, the trailing zero and the
    bare decimal point.

    ON FAILURE: the code is wrong.
    """
    tex = TeXinfo({"a": 2.0}, {"a": 0.1}, "f(x)=a", CHISQ, 1)
    simple = tex.build_info(simplify_info_for_paper=True)
    assert _math(_param_line(simple, "a")) == "a = 2"


def test_an_infinite_uncertainty_is_shown_as_infinity():
    r"""An infinite uncertainty prints as ``\infty``, braces balanced, no bare inf.

    ON FAILURE: the code is wrong.
    """
    tex = TeXinfo({"a": 1.23}, {"a": np.inf}, "f", CHISQ, 0.5)
    line = _param_line(tex.build_info(), "a")
    assert r"\infty" in line
    assert re.search(r"(?<!\\)inf", line) is None, line
    assert line.count("{") == line.count("}"), line


def test_build_info_defaults_are_the_documented_options(texinfo):
    """``build_info()`` equals the call spelling out each documented default.

    Defaults: chi^2 shown; R^2, relative errors, stripped uncertainties,
    paper format and the initial guess not shown; 10^{X} notation.

    ON FAILURE: the code is wrong.
    """
    explicit = texinfo.build_info(
        chisq_dof=True,
        rsq=False,
        relative_error=False,
        convert_pow_10=True,
        strip_uncertainties=False,
        simplify_info_for_paper=False,
        add_initial_guess=False,
    )
    assert texinfo.build_info() == explicit


def test_the_fixture_separates_every_build_info_option(texinfo):
    """Flipping any one ``build_info`` option changes the fixture's annotation.

    Without this, the defaults test above could pass with a default flipped.

    ON FAILURE: the fixture no longer separates an option from its default;
    fix the fixture.
    """
    default = texinfo.build_info()
    for flipped in [
        {"chisq_dof": False},
        {"rsq": True},
        {"relative_error": True},
        {"convert_pow_10": False},
        {"strip_uncertainties": True},
        {"simplify_info_for_paper": True},
        {"add_initial_guess": True},
    ]:
        assert texinfo.build_info(**flipped) != default, flipped


def test_options_add_their_rows(texinfo_greek):
    """R^2, relative errors and the initial guess each add their content.

    R^2 is printed to two decimals, so 0.99 appears; the relative error of
    ``a`` is ``1e-5 / 1.23e-3``; the initial guess table holds ``a``'s start.

    ON FAILURE: the code is wrong.
    """
    assert "0.99" in texinfo_greek.build_info(rsq=True)
    rel = texinfo_greek.build_info(relative_error=True, convert_pow_10=False)
    assert f"{PSIGMA['a'] / POPT['a']:.3e}" in rel
    assert "5.000e-01" in texinfo_greek.build_info(add_initial_guess=True)


def test_a_failed_fit_shows_the_function_and_no_parameters():
    """With every parameter NaN, the annotation is the function and no values.

    ON FAILURE: the code is wrong.
    """
    tex = TeXinfo({"a": np.nan}, {"a": np.nan}, "f(x)=a", CHISQ, 0.5)
    info = tex.build_info()
    assert isinstance(info, str)
    assert "f(x)=a" in info
    assert r"\pm" not in info and "nan" not in info


def test_initial_guess_on_a_failed_guess_still_gives_a_string():
    """``add_initial_guess`` with no guess info appends a note, not None.

    ON FAILURE: the code is wrong.
    """
    tex = TeXinfo({"a": 1.0}, {"a": 0.1}, "f", CHISQ, 0.5)
    with_note = tex.build_info(add_initial_guess=True)
    assert isinstance(with_note, str)
    assert with_note.startswith(tex.build_info()) and len(with_note) > len(
        tex.build_info()
    )


def test_annotate_fcn_receives_the_annotation_and_its_result_is_kept(texinfo):
    """``annotate_fcn`` is applied last and its return value is the annotation.

    ON FAILURE: the code is wrong.
    """
    plain = texinfo.build_info()
    wrapped = texinfo.build_info(annotate_fcn=lambda s: "<" + s + ">")
    assert wrapped == "<" + plain + ">"
    assert str(texinfo) == wrapped


def test_additional_info_items_are_wrapped_in_math_escapes(texinfo):
    """Each item of a list ``additional_info`` is appended as math.

    An item without ``$`` gains a pair; one already escaped is kept as is; an
    odd number of ``$`` is rejected.

    ON FAILURE: the code is wrong.
    """
    info = texinfo.build_info(additional_info=["x", "$y$"])
    assert info.endswith("\n$x$\n$y$")
    with pytest.raises(ValueError, match="even number of math escapes"):
        texinfo.build_info(additional_info=["$x$$"])


def test_additional_info_string_is_appended_and_other_types_rejected(texinfo):
    """A string ``additional_info`` is appended on its own line; an int is refused.

    ON FAILURE: the code is wrong.
    """
    assert texinfo.build_info(additional_info="extra").endswith("\nextra")
    with pytest.raises(TypeError, match="Additional info must be a string"):
        texinfo.build_info(additional_info=5)


def test_extra_params_follow_the_fitted_parameters_without_an_uncertainty():
    r"""``extra_params`` print after the fitted parameters, value only.

    The chosen ``A = 2.5`` reads back as 2.5 and has no ``\pm`` term.

    ON FAILURE: the code is wrong.
    """
    tex = TeXinfo(POPT, PSIGMA, FUNCTION, CHISQ, RSQ, None, {"A": 2.5})
    info = tex.build_info()
    lines = _lines(info)
    a_line = _param_line(info, "A")
    assert lines.index(a_line) > lines.index(_param_line(info, "b"))
    assert _read_back(a_line) == (2.5, None)
    assert tex.extra_params == {"A": 2.5}
    assert "A = " not in TeXinfo(POPT, PSIGMA, FUNCTION, CHISQ, RSQ).build_info()


@pytest.mark.parametrize("value", [True, 1 + 2j], ids=["bool", "complex"])
def test_extra_params_refuse_values_that_are_not_real_numbers(texinfo, value):
    """A bool or complex extra value raises TypeError naming its key; reals pass.

    ``True`` is a Number (an int) but not a quantity to report, and a
    complex value has no place on a real axis.

    ON FAILURE: the code is wrong.
    """
    with pytest.raises(TypeError, match="'A'.*not a real number"):
        texinfo.set_extra_params({"A": value})
    texinfo.set_extra_params({"A": 2, "B": 2.5, "C": np.float64(3.0)})
    assert texinfo.extra_params == {"A": 2, "B": 2.5, "C": 3.0}


def test_setting_extra_params_rebuilds_the_annotation(texinfo):
    """After ``set_extra_params``, ``str`` shows the new values, then drops them.

    ON FAILURE: the code is wrong.
    """
    texinfo.build_info()
    texinfo.set_extra_params({"A": 2.5})
    assert _read_back(_param_line(str(texinfo), "A")) == (2.5, None)
    texinfo.set_extra_params(None)
    assert "A = " not in str(texinfo)


def test_value_is_reported_to_the_uncertainty_first_digit():
    """``123 +- 0.00123`` keeps five decimals in the mantissa: 1.23000e+02.

    Hand-computed: the value's exponent is 2 and the uncertainty's is -3, so
    the value is printed to 2 - (-3) = 5 mantissa decimals and the
    uncertainty to one significant digit.

    ON FAILURE: the code is wrong.
    """
    tex = TeXinfo({}, {}, "", None, None)
    assert tex.val_uncert_2_string(123.0, 0.00123) == r"1.23000e+02 \pm 1e-03"


def _annotation(ax):
    (text,) = ax.texts
    return text


def test_annotate_info_draws_the_annotation_with_the_default_style(texinfo):
    """Without options, the text sits at axes (1.1, 0.95), left/top, in a wheat box.

    The author decided plot-styling defaults are pinned by tests; the values
    are the documented defaults of ``annotate_info``.

    ON FAILURE: the code is wrong, unless the author changed a default.
    """
    fig, ax = plt.subplots()
    try:
        texinfo.annotate_info(ax)
        text = _annotation(ax)
        assert text.get_text() == str(texinfo)
        assert text.get_position() == (1.1, 0.95)
        assert text.get_transform() is ax.transAxes
        assert text.get_horizontalalignment() == "left"
        assert text.get_verticalalignment() == "top"
        box = text.get_bbox_patch()
        assert box.get_facecolor() == to_rgba("wheat", 0.75)
    finally:
        plt.close(fig)


def test_annotate_info_honours_every_option(texinfo):
    """Each option replaces its default, and other keywords reach ``ax.text``.

    ON FAILURE: the code is wrong.
    """
    fig, ax = plt.subplots()
    try:
        texinfo.annotate_info(
            ax,
            bbox=dict(color="red", alpha=0.5),
            xloc=0.2,
            yloc=0.3,
            ha="right",
            va="bottom",
            transform=ax.transData,
            fontsize=7,
        )
        text = _annotation(ax)
        assert text.get_position() == (0.2, 0.3)
        assert text.get_transform() is ax.transData
        assert text.get_horizontalalignment() == "right"
        assert text.get_verticalalignment() == "bottom"
        assert text.get_bbox_patch().get_facecolor() == to_rgba("red", 0.5)
        assert text.get_fontsize() == 7
    finally:
        plt.close(fig)
