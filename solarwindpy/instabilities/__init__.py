"""Tools for evaluating plasma instabilities.

This subpackage bundles functionality for visualizing and
quantifying kinetic instabilities in the solar wind.  It exposes the
following modules:

``beta_ani``
    Convenience wrappers for creating anisotropy plots.
``verscharen2016``
    Thresholds and utilities based on the fits presented in
    :cite:`Verscharen2016a`.
"""

from . import verscharen2016, beta_ani  # noqa: F401

__all__ = ["verscharen2016", "beta_ani"]
