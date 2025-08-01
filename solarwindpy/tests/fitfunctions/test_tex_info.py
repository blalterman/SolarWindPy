import matplotlib
import matplotlib.pyplot as plt
from solarwindpy.fitfunctions.tex_info import TeXinfo

matplotlib.use("Agg")


class DummyChiSq:
    linear = 0.0
    robust = 0.0


def test_val_uncert_2_string():
    info = TeXinfo({"a": 1.0}, {"a": 0.2}, "f", chisq_dof=DummyChiSq, rsq=None)
    out = info.val_uncert_2_string(3.1415, 0.01)
    assert out == r"3.14e+00 \pm 1e-02"


def test_build_info_basic():
    info = TeXinfo(
        {"a": 2.0, "b": 3.0}, {"a": 0.1, "b": 0.2}, "f", chisq_dof=DummyChiSq, rsq=None
    )
    result = info.build_info(chisq_dof=False, convert_pow_10=False)
    expected = "$ f $\n$ a = 2.0e+00 \\pm 1e-01 $\n$ b = 3.0e+00 \\pm 2e-01 $"
    assert result == expected


def test_annotate_info_adds_text():
    info = TeXinfo({"a": 2.0}, {"a": 0.1}, "f", chisq_dof=DummyChiSq, rsq=None)
    text = str(info)
    fig, ax = plt.subplots()
    info.annotate_info(ax)
    assert len(ax.texts) == 1
    t = ax.texts[0]
    assert t.get_text() == text
    assert t.get_position() == (1.1, 0.95)


def test_TeX_argnames_transformations():
    info = TeXinfo(
        {"a": 2.0, "b": 3.0}, {"a": 0.1, "b": 0.2}, "f", chisq_dof=DummyChiSq, rsq=None
    )
    info.set_TeX_argnames(a="\\alpha", b="\\beta")
    popt = info.TeX_popt
    assert set(popt) == {"\\alpha", "\\beta"}
    rel_err = info.TeX_relative_error
    assert "\\alpha" in rel_err and "\\beta" in rel_err
