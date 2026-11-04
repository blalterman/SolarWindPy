# Spent-When: PERMANENT(the hinge fit functions are removed from solarwindpy.fitfunctions)
# Supersedes: none
r"""Every hinge fit function names the hinge ``(h, yh)`` the same way.

The hinge x-location is ``h`` and the hinge y-location ``yh`` in every class
of :mod:`solarwindpy.fitfunctions.hinge`: as a fit parameter where the class
fits it, and as a derived property on :class:`TwoLine`, which fits the two
lines and derives their intersection. No class keeps the older ``xh``,
``xs`` or ``s``, and the start keyword is ``guess_h``.
"""

import inspect

import numpy as np

from solarwindpy.fitfunctions.hinge import (
    HingeAtPoint,
    HingeMax,
    HingeMin,
    HingeSaturation,
    Saturation,
    TwoLine,
)

OLD_NAMES = {"xh", "xs", "s"}

# The classes that fit the hinge x, and whether they fit the hinge y too.
FITS_HINGE = {
    HingeSaturation: True,
    Saturation: True,
    HingeMin: False,
    HingeMax: False,
    HingeAtPoint: True,
}


def _fit_function(cls):
    x = np.linspace(0.0, 15.0, 50)
    y = np.minimum(2.0 * x, -(x - 15.0))
    return cls(x, y)


def test_every_hinge_class_names_the_hinge_h_and_yh():
    r"""``h`` and ``yh`` name the hinge in all six hinge classes.

    For the five classes that fit the hinge x, ``argnames`` holds ``h`` (and
    ``yh`` where the y is fitted) and none of ``xh``, ``xs`` or ``s``.
    :class:`TwoLine` has the derived properties ``h`` and ``yh`` and neither
    ``xs`` nor ``s``. Every class takes ``guess_h``, not ``guess_xh``.

    ON FAILURE: a hinge class names the hinge another way; the code is wrong.
    """
    problems = []
    for cls, fits_y in FITS_HINGE.items():
        names = set(_fit_function(cls).argnames)
        if "h" not in names:
            problems.append(f"{cls.__name__}: no h in {sorted(names)}")
        if fits_y and "yh" not in names:
            problems.append(f"{cls.__name__}: no yh in {sorted(names)}")
        if names & OLD_NAMES:
            problems.append(f"{cls.__name__}: old names {sorted(names & OLD_NAMES)}")

    for name in ("h", "yh"):
        if not isinstance(getattr(TwoLine, name, None), property):
            problems.append(f"TwoLine: no derived property {name}")
    for name in ("xs", "s"):
        if hasattr(TwoLine, name):
            problems.append(f"TwoLine: old derived property {name}")

    for cls in (*FITS_HINGE, TwoLine):
        keywords = inspect.signature(cls.__init__).parameters
        if "guess_h" not in keywords or "guess_xh" in keywords:
            problems.append(f"{cls.__name__}: keywords {sorted(keywords)}")

    assert not problems, problems
