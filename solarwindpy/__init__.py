r"""Package for solar wind data analysis.

Primary focus is in situ solar wind measurements and the additional tools necessary for
context (e.g. solar activity indicies) and some simple plotting methods.
"""


def _enable_docstring_inheritance() -> None:
    """Switch on docstring-inheritance before any subpackage imports it.

    docstring-inheritance 3.x reads ``DOCSTRING_INHERITANCE_ENABLE`` once, at
    its own import, and without it binds its metaclasses to plain ``type``, so
    subclass methods lose the help text they inherit. ``setdefault`` keeps a
    value the user set explicitly.
    """
    import os

    os.environ.setdefault("DOCSTRING_INHERITANCE_ENABLE", "1")


_enable_docstring_inheritance()

from . import (  # noqa: E402
    core,
    examples,
    fitfunctions,
    instabilities,
    plotting,
    solar_activity,
    tools,
)


def _check_docstring_inheritance() -> None:
    """Warn when docstring inheritance was requested but is not active.

    The library reads its switch only at first import, so a program that
    imported it with the switch off before importing solarwindpy keeps it off.
    """
    import os
    import warnings

    import docstring_inheritance

    requested = bool(os.environ.get("DOCSTRING_INHERITANCE_ENABLE"))
    if requested and docstring_inheritance.NumpyDocstringInheritanceMeta is type:
        warnings.warn(
            "docstring inheritance is off: docstring_inheritance was imported "
            "before solarwindpy with DOCSTRING_INHERITANCE_ENABLE unset, so "
            "fit-function methods show no inherited help text. Import "
            "solarwindpy first, or set DOCSTRING_INHERITANCE_ENABLE=1 before "
            "starting Python.",
            stacklevel=2,
        )


_check_docstring_inheritance()


def _configure_pandas() -> None:
    """Configure global pandas options used throughout SolarWindPy."""
    # Imported here, not at module level, so ``solarwindpy`` binds no
    # third-party names.
    import pandas as pd

    pd.set_option("mode.chained_assignment", "raise")


_configure_pandas()

# ``pp`` is the one temporary nickname in the package: every other public
# object has exactly one import path, the module that defines it. It stays
# only until the author's analysis code migrates to ``solarwindpy.plotting``.
pp = plotting

__all__ = [
    "core",
    "examples",
    "fitfunctions",
    "instabilities",
    "plotting",
    "solar_activity",
    "tools",
]

__author__ = "B. L. Alterman <blaltermanphd@gmail.com>"

__name__ = "solarwindpy"


def _installed_version() -> str:
    """The installed distribution's version, or ``"unknown"`` if not installed."""
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version(__name__)
    except PackageNotFoundError:
        return "unknown"


__version__ = _installed_version()
