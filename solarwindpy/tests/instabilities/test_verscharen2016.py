import matplotlib
import numpy as np
import pandas as pd
from solarwindpy.instabilities import verscharen2016 as v

matplotlib.use("Agg")


def test_beta_ani_inst_basic():
    beta = np.array([1.0, 2.0])
    result = v.beta_ani_inst(beta, a=0.367, b=-0.408, c=0.011)
    expected = 1 + (0.367 / ((beta - 0.011) ** -0.408))
    assert np.allclose(result, expected)


def test_stability_condition_shapes():
    beta = pd.Series([1.0, 2.0, 3.0])
    ani = pd.Series([1.1, 0.9, 1.3])
    cond = v.StabilityCondition(-2, beta, ani)
    assert cond.instability_thresholds.shape == (3, 4)
    assert cond.is_unstable.shape == (3, 4)
    assert cond.stability_bin.shape[0] == 3


def test_stability_contours_lengths():
    beta = np.logspace(-2, 1, 5)
    sc = v.StabilityContours(beta)
    for values in sc.contours.to_numpy().ravel():
        assert len(values) == len(beta)
