import logging

import pandas as pd

from solarwindpy.core.base import Core


class DummyCore(Core):
    """Simple Core subclass exposing :meth:`_verify_datetimeindex`."""

    def _clean_species_for_setting(self, *species: str):
        return species

    def verify(self, data: pd.DataFrame) -> None:
        self._verify_datetimeindex(data)


def test_non_datetime_index_warning(caplog):
    core = DummyCore()
    df = pd.DataFrame({"a": [1, 2]})
    with caplog.at_level(logging.WARNING):
        core.verify(df)
    assert "non-DatetimeIndex" in caplog.text


def test_non_monotonic_datetime_index_warning(caplog):
    core = DummyCore()
    idx = pd.to_datetime(["2020-01-02", "2020-01-01"])
    df = pd.DataFrame({"a": [1, 2]}, index=idx)
    with caplog.at_level(logging.WARNING):
        core.verify(df)
    assert "not monotonically increasing" in caplog.text
