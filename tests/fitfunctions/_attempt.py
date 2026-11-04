# Spent-When: PERMANENT(make_fit stops recording a failed fit as FitFunction.error)
# Supersedes: none
"""Run a fit and return its recorded failure instead of raising it."""


def attempt_fit(fit, **kwargs):
    """Call ``fit.make_fit(**kwargs)`` and return ``fit.error``.

    ``fit.error`` is None after a successful fit and the exception after a
    failed one. Only the failure ``make_fit`` records is swallowed: any other
    exception (a usage error it does not record) reaches the test.
    """
    try:
        fit.make_fit(**kwargs)
    except Exception as e:
        # A usage error on a fresh fit leaves error unreadable: re-raise it.
        if getattr(fit, "error", None) is not e:
            raise
    return fit.error
