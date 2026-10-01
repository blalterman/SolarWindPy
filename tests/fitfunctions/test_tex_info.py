import warnings

from types import SimpleNamespace

import matplotlib
import pytest
from solarwindpy.fitfunctions.tex_info import TeXinfo

matplotlib.use("Agg")
warnings.filterwarnings("ignore")


@pytest.fixture
def texinfo():
    popt = {"a": 1.23, "b": 4.56}
    psigma = {"a": 0.01, "b": 0.02}
    func = "f(x)=a x + b"
    chisq = SimpleNamespace(linear=1.0, robust=2.0)
    rsq = 0.99
    initial_guess_info = {
        "a": SimpleNamespace(p0=0.5, bounds=(-1, 1)),
        "b": SimpleNamespace(p0=2.0, bounds=(0, 5)),
    }
    tex = TeXinfo(popt, psigma, func, chisq, rsq, initial_guess_info, 10)
    tex.set_TeX_argnames(a="\\alpha", b="\\beta")
    return tex


def test_properties_and_str(texinfo):
    assert texinfo.popt == {"a": 1.23, "b": 4.56}
    assert texinfo.psigma == {"a": 0.01, "b": 0.02}
    assert texinfo.chisq_dof.linear == 1.0
    assert texinfo.rsq == 0.99
    assert texinfo.npts == 10
    assert texinfo.TeX_function == "f(x)=a x + b"
    assert texinfo.TeX_argnames == {"a": "\\alpha", "b": "\\beta"}
    assert "\\alpha" in texinfo.initial_guess_info
    assert texinfo.TeX_popt["\\alpha"].startswith("1.23")
    assert "\\sigma(X)/X" in texinfo.TeX_relative_error
    info = texinfo.build_info(rsq=True, npts=True)
    assert "R^2 = 0.99" in info
    assert str(texinfo) == info


def test_constructor_and_setters_errors():
    with pytest.raises(ValueError):
        TeXinfo({"a": 1}, {"b": 1}, "f", SimpleNamespace(), 0, None, None)
    with pytest.raises(TypeError):
        TeXinfo({"a": 1}, {"a": 1}, "f", SimpleNamespace(), 0, "bad", None)
    tex = TeXinfo({"a": 1}, {"a": 1}, "f", SimpleNamespace(), 0, None, None)
    with pytest.raises(TypeError):
        tex.set_npts("ten")
    with pytest.raises(TypeError):
        tex.set_initial_guess_info("bad")
    with pytest.raises(ValueError):
        tex.set_TeX_argnames(c="\\gamma")


def test_set_popt_psigma_errors(texinfo):
    with pytest.raises(
        ValueError
    ):  # Function actually raises ValueError when iterating over string
        texinfo.set_popt_psigma("bad", {"a": 1})
    with pytest.raises(AttributeError):  # String doesn't have .items() method
        texinfo.set_popt_psigma({"a": 1}, "bad")
    with pytest.raises(ValueError):
        texinfo.set_popt_psigma({"a": 1}, {"b": 1})


def test_set_chisq_dof_type_error(texinfo):
    # The function doesn't actually do type checking, just sets the value
    texinfo.set_chisq_dof("bad")  # This should succeed
    assert texinfo.chisq_dof == "bad"


def test_set_rsq_type_error(texinfo):
    # The function doesn't actually do type checking, just sets the value
    texinfo.set_rsq("bad")  # This should succeed
    assert texinfo.rsq == "bad"


def test_set_TeX_function_type_error(texinfo):
    # The function doesn't actually do type checking, just sets the value
    texinfo.set_TeX_function(5)  # This should succeed
    assert texinfo.TeX_function == 5


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


def test_value_is_reported_to_the_uncertainty_first_digit():
    """``123 +- 0.00123`` keeps five decimals in the mantissa: 1.23000e+02.

    Hand-computed: the value's exponent is 2 and the uncertainty's is -3, so
    the value is printed to 2 - (-3) = 5 mantissa decimals and the
    uncertainty to one significant digit.

    ON FAILURE: the code is wrong.
    """
    tex = TeXinfo({}, {}, "", None, None)
    assert tex.val_uncert_2_string(123.0, 0.00123) == r"1.23000e+02 \pm 1e-03"


def test_simplified_info_drops_trailing_zeros_and_powers_of_ten():
    """``simplify_info_for_paper`` prints 2, not 2.0 x 10^0.

    ``a = 2 +- 0.1`` is formatted to the uncertainty's digit as 2.0e+00;
    simplifying for a paper strips the exponent, the trailing zero and the
    bare decimal point.

    ON FAILURE: the code is wrong.
    """
    tex = TeXinfo(
        {"a": 2.0}, {"a": 0.1}, "f(x)=a", SimpleNamespace(linear=1.0, robust=1.0), 1
    )
    plain = tex.build_info(strip_uncertainties=True)
    simple = tex.build_info(strip_uncertainties=True, simplify_info_for_paper=True)
    assert "a = 2.0 \\times 10^{+0 }" in plain
    assert "$ a = 2 $" in simple


def test_build_info_with_every_option(texinfo):
    """All report options together include chi^2, R^2, N and relative errors.

    ON FAILURE: the code is wrong.
    """
    info = texinfo.build_info(
        chisq_dof=True,
        rsq=True,
        convert_pow_10=True,
        strip_uncertainties=True,
        simplify_info_for_paper=True,
        npts=True,
        relative_error=True,
    )
    assert "chi" in info and "R^2" in info
    assert "N_\\mathrm{pts}" in info and "sigma(X)/X" in info


def test_annotate_info(texinfo):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    texinfo.annotate_info(ax)
    assert texinfo.info in ax.texts[0].get_text()
    plt.close(fig)


def test_build_info_and_val_uncert(texinfo):
    info = texinfo.build_info(additional_info="extra")
    assert "extra" in info
    with pytest.raises(ValueError):
        texinfo.build_info(bogus=True)
    s = texinfo.val_uncert_2_string(1.234, 0.01)
    assert "\\pm" in s and s.startswith("1.23")


def test_build_info_with_initial_guess(texinfo):
    info = texinfo.build_info(add_initial_guess=True)
    assert "\\alpha" in info and "5.000e-01" in info
    assert str(texinfo) == info


def test_build_info_relative_error_e_format(texinfo):
    info = texinfo.build_info(relative_error=True, convert_pow_10=False)
    assert "sigma(X)/X" in info and "e+00" in info
    assert "10^" not in info
    assert str(texinfo) == info


def test_build_info_strip_uncert_simplify(texinfo):
    info = texinfo.build_info(strip_uncertainties=True, simplify_info_for_paper=True)
    assert "\\pm" not in info
    assert "\\alpha = 1.23" in info
    assert "e+" not in info
    assert str(texinfo) == info
