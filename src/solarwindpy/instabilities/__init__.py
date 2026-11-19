"""Tools for evaluating plasma instabilities.

This subpackage bundles functionality for visualizing and
quantifying kinetic instabilities in the solar wind.  It exposes the
following modules:

``plots``
    Convenience wrappers for creating anisotropy plots.
``verscharen2016``
    Thresholds and utilities based on the fits presented in
    :cite:`Verscharen2016a`.
"""

from . import plots, verscharen2016  # noqa: F401

__all__ = ["plots", "verscharen2016"]
