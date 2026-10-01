"""Tests for ``solarwindpy.tools``: ``swap_protons`` and ``normal_parameters``.

Expected values come from hand-built frames and ``scipy.stats.lognorm``.
"""

import logging
import math
import re

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from solarwindpy.tools import normal_parameters, swap_protons

# ---------------------------------------------------------------------------
# solarwindpy.tools.swap_protons
# ---------------------------------------------------------------------------


@pytest.fixture
def restore_logging():
    """Put every logger's handlers and level back as they were."""
    manager = logging.Logger.manager

    def snapshot():
        loggers = [logging.getLogger()] + [
            lg for lg in manager.loggerDict.values() if isinstance(lg, logging.Logger)
        ]
        return {lg.name: (lg, list(lg.handlers), lg.level) for lg in loggers}

    before = snapshot()
    yield
    for name, (lg, handlers, level) in snapshot().items():
        old_handlers, old_level = (
            (before[name][1], before[name][2]) if name in before else ([], 0)
        )
        for h in lg.handlers[:]:
            if h not in old_handlers:
                lg.removeHandler(h)
        lg.setLevel(old_level)


def _handler_counts():
    """Number of handlers on every existing logger, by name."""
    loggers = [logging.getLogger()] + [
        lg
        for lg in logging.Logger.manager.loggerDict.values()
        if isinstance(lg, logging.Logger)
    ]
    return {lg.name: len(lg.handlers) for lg in loggers}


class HandlersAccumulated(AssertionError):
    """A repeated call added logging handlers again."""


@pytest.fixture
def protons():
    """Hand-built plasma frame with core (p1), beam (p2), alphas, and B.

    Row 0: n_p1 > n_p2, kept.     Row 1: n_p2 > n_p1, swapped.
    Row 2: n_p1 == n_p2, kept.    Row 3: n_p2 > n_p1, swapped.
    Row 4: n_p1 is NaN, kept (NaN ratio is not > 1).
    """
    cols = pd.MultiIndex.from_tuples(
        [
            ("n", "", "p1"),
            ("n", "", "p2"),
            ("v", "x", "p1"),
            ("v", "x", "p2"),
            ("w", "par", "p1"),
            ("w", "par", "p2"),
            ("n", "", "a"),
            ("b", "x", ""),
        ],
        names=["M", "C", "S"],
    )
    rows = [
        [5.0, 1.0, 400.0, 500.0, 30.0, 60.0, 0.2, 5.0],
        [1.0, 4.0, 401.0, 501.0, 31.0, 61.0, 1.2, 6.0],
        [2.0, 2.0, 402.0, 502.0, 32.0, 62.0, 2.2, 7.0],
        [3.0, 6.0, 403.0, 503.0, 33.0, 63.0, 3.2, 8.0],
        [np.nan, 1.0, 404.0, 504.0, 34.0, 64.0, 4.2, 9.0],
    ]
    return pd.DataFrame(rows, columns=cols)


class TestSwapProtons:
    """``swap_protons`` relabels core and beam where the beam is denser."""

    def test_swaps_every_p1_p2_quantity_where_n_p2_exceeds_n_p1(
        self, protons, restore_logging
    ):
        """Rows 1 and 3 exchange all p1/p2 columns; alphas and B are untouched.

        Expected frame is the fixture with those two rows' pairs exchanged by hand.
        ON FAILURE: the code is wrong.
        """
        expected = protons.copy()
        for m, c in (("n", ""), ("v", "x"), ("w", "par")):
            for row in (1, 3):
                p1, p2 = protons.loc[row, (m, c, "p1")], protons.loc[row, (m, c, "p2")]
                expected.loc[row, (m, c, "p1")] = p2
                expected.loc[row, (m, c, "p2")] = p1

        new, swapped = swap_protons(protons, logger=logging.getLogger("tests.swap"))

        pd.testing.assert_frame_equal(
            new.loc[:, protons.columns], expected, check_like=True
        )

    def test_output_keeps_mcs_level_names_so_it_can_be_swapped_again(
        self, protons, restore_logging
    ):
        """The output keeps the M/C/S column layout, so swapping it again works.

        A second swap finds nothing left to swap.
        ON FAILURE: the code is wrong.
        """
        logger = logging.getLogger("tests.swap")
        new, _ = swap_protons(protons, logger=logger)
        again, swapped_again = swap_protons(
            new.drop(columns="swapped_protons", level=0), logger=logger
        )
        assert list(new.columns.names) == ["M", "C", "S"]
        assert not swapped_again.any()

    def test_mask_and_flag_column_mark_exactly_the_swapped_rows(
        self, protons, restore_logging
    ):
        """The mask and the ``swapped_protons`` column are True for rows 1 and 3.

        Equal densities (row 2) and a NaN density (row 4) are not swapped.
        ON FAILURE: the code is wrong.
        """
        new, swapped = swap_protons(protons, logger=logging.getLogger("tests.swap"))
        expected = [False, True, False, True, False]
        assert swapped.tolist() == expected
        assert new.loc[:, ("swapped_protons", "", "")].tolist() == expected
        added = set(new.columns) - set(protons.columns)
        assert added == {("swapped_protons", "", "")}

    def test_beam_is_never_denser_than_core_afterwards(self, restore_logging):
        """Postcondition: n_p2 <= n_p1 on every row where both are finite.

        ON FAILURE: the code is wrong.
        """
        rng = np.random.default_rng(5)
        cols = pd.MultiIndex.from_tuples(
            [("n", "", "p1"), ("n", "", "p2")], names=["M", "C", "S"]
        )
        data = pd.DataFrame(rng.uniform(0.1, 10.0, size=(200, 2)), columns=cols)
        new, swapped = swap_protons(data, logger=logging.getLogger("tests.swap"))
        n1 = new.loc[:, ("n", "", "p1")]
        n2 = new.loc[:, ("n", "", "p2")]
        assert (n2 <= n1).all()
        assert 0 < swapped.sum() < len(data)

    def test_input_frame_is_not_modified(self, protons, restore_logging):
        """The caller's frame is unchanged.

        ON FAILURE: the code is wrong.
        """
        before = protons.copy()
        swap_protons(protons, logger=logging.getLogger("tests.swap"))
        pd.testing.assert_frame_equal(protons, before)

    def test_given_logger_receives_one_info_record_with_the_count(
        self, protons, caplog, restore_logging
    ):
        """A supplied logger gets one INFO record whose stats include count 2.

        ON FAILURE: the code is wrong.
        """
        caplog.set_level(logging.INFO, logger="tests.swap")
        swap_protons(protons, logger=logging.getLogger("tests.swap"))
        records = [r for r in caplog.records if r.name == "tests.swap"]
        assert len(records) == 1
        assert records[0].levelno == logging.INFO
        assert re.search(r"count\s+2\b", records[0].getMessage())

    def test_default_logger_does_not_accumulate_handlers(
        self, protons, restore_logging
    ):
        """Calling with ``logger=None`` twice leaves the handler counts of one call.

        ON FAILURE: the code is wrong.
        """
        swap_protons(protons)
        after_one = _handler_counts()
        swap_protons(protons)
        after_two = _handler_counts()
        grew = {k: (after_one.get(k, 0), v) for k, v in after_two.items()}
        grew = {k: v for k, v in grew.items() if v[1] > v[0]}
        if grew:
            raise HandlersAccumulated(f"handlers added by a second call: {grew}")


# ---------------------------------------------------------------------------
# solarwindpy.tools.normal_parameters
# ---------------------------------------------------------------------------


class TestNormalParameters:
    """Mean and standard deviation of a log-normal from its log-space parameters."""

    def test_matches_scipy_lognorm_mean_and_std(self):
        """``mu``/``sigma`` equal scipy's lognorm(s, scale=e^m) mean and std.

        ON FAILURE: the code is wrong.
        """
        m = pd.Series([0.0, 1.0, -0.5, 2.0])
        s = pd.Series([0.25, 0.5, 1.0, 0.1])
        result = normal_parameters(m, s)
        dist = stats.lognorm(s=s.values, scale=np.exp(m.values))
        assert list(result.columns) == ["mu", "sigma"]
        # rel 1e-10: scipy evaluates equivalent closed forms (expm1) in another order.
        np.testing.assert_allclose(result["mu"], dist.mean(), rtol=1e-10, atol=0)
        np.testing.assert_allclose(result["sigma"], dist.std(), rtol=1e-10, atol=0)

    def test_zero_log_width_is_a_point_mass_at_e_to_the_m(self):
        """With s = 0, X = e^m exactly: mu = e^(ln 2) = 2 and sigma = 0.

        ON FAILURE: the code is wrong.
        """
        mu, sigma = normal_parameters(math.log(2.0), 0.0)
        # rel 1e-12: exp(log(2)) is 2 up to rounding.
        assert mu == pytest.approx(2.0, rel=1e-12, abs=0)
        assert sigma == 0.0

    def test_scalar_inputs_unpack_as_mu_then_sigma(self):
        """Scalars return a two-element result that unpacks as ``mu, sigma``.

        This is the docstring's usage, checked against scipy.
        ON FAILURE: the code is wrong.
        """
        mu, sigma = normal_parameters(1.0, 0.5)
        dist = stats.lognorm(s=0.5, scale=math.e)
        # rel 1e-10: as above.
        assert mu == pytest.approx(dist.mean(), rel=1e-10, abs=0)
        assert sigma == pytest.approx(dist.std(), rel=1e-10, abs=0)

    @pytest.mark.parametrize("base", [10.0, 2.0])
    def test_other_base_matches_scipy_lognorm_scaled_by_ln_base(self, base):
        """A base-b log-normal matches scipy's lognorm(s ln b, scale=b^m).

        For log_b(X) ~ N(m, s), ln X ~ N(m ln b, s ln b).

        ON FAILURE: the code is wrong.
        """
        m = pd.Series([0.0, 1.0, -0.5, 0.3])
        s = pd.Series([0.05, 0.2, 0.4, 0.1])
        result = normal_parameters(m, s, base=base)
        dist = stats.lognorm(s=s.values * np.log(base), scale=base**m.values)
        # rel 1e-10: scipy evaluates equivalent closed forms in another order.
        np.testing.assert_allclose(result["mu"], dist.mean(), rtol=1e-10, atol=0)
        np.testing.assert_allclose(result["sigma"], dist.std(), rtol=1e-10, atol=0)

    def test_base_e_is_the_default(self):
        """``base=np.e`` reproduces the default natural-log result.

        ON FAILURE: the code is wrong.
        """
        m = pd.Series([0.0, 1.0, -0.5])
        s = pd.Series([0.25, 0.5, 1.0])
        # rel 1e-12: ln(e) is 1 up to rounding.
        pd.testing.assert_frame_equal(
            normal_parameters(m, s, base=np.e),
            normal_parameters(m, s),
            rtol=1e-12,
            atol=0,
        )

    @pytest.mark.parametrize("base", [np.e, 10.0])
    def test_sample_mean_of_base_b_lognormal_matches_mu(self, base):
        """Sampled X = b^Z, Z ~ N(m, s), has mean within 4 standard errors of mu.

        Fixed seed; the standard error is sigma / sqrt(N).

        ON FAILURE: the code is wrong.
        """
        m, s, n = 0.5, 0.2, 200_000
        z = np.random.default_rng(20260930).normal(m, s, n)
        x = base**z
        mu, sigma = normal_parameters(m, s, base=base)
        # 4 standard errors: passes for almost any seed, per TEST_PATTERNS.
        assert abs(x.mean() - mu) < 4.0 * sigma / np.sqrt(n)
        # sigma itself: sample std within 4 percent (its own error is ~0.3 %).
        assert x.std() == pytest.approx(sigma, rel=0.04, abs=0)

    @pytest.mark.parametrize("base", [1.0, 0.0, -10.0, np.nan])
    def test_invalid_base_raises_value_error(self, base):
        """A base that is not positive, finite, and != 1 is rejected.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(ValueError, match="base"):
            normal_parameters(0.0, 0.1, base=base)
