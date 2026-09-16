# Spent-When: PERMANENT(the tests/drift/ suite is retired)
# Supersedes: none
"""Drift detection: assertions that an external fact SolarWindPy records still holds.

See ``_drift.py`` for the shared ``drift_message`` reporting helper and
predicate functions. Every test module here sets ``pytestmark =
pytest.mark.drift`` (except ``test_drift_controls.py``, which runs unmarked
in the default suite so the predicates stay exercised while the network
assertions are skipped).
"""
