# Spent-When: MARKED(tests/plotting/_legacy/__init__.py)
# Supersedes: none
"""Frozen copy of the plotting modules, the oracle for the binned-data migration.

Each module here is a verbatim copy of its source at master commit
4bc1c08eb5c610151e9a4905cdb171dc26202653:

- ``base``, ``agg_plot``, ``hist1d``, ``hist2d``, ``scatter`` and ``spiral``
  from ``solarwindpy/plotting/``;
- ``beta_ani`` from ``solarwindpy/instabilities/``.

Only the imports are rewritten, so the package is self-contained. Imports
between these modules stay relative and resolve here (``beta_ani`` imports
``.hist2d``). Everything else (``labels``, ``tools.nan_gaussian_filter``,
``labels.base.TeXlabel``) imports from the live ``solarwindpy.plotting``,
because the migration does not change it.

``tests/plotting/test_binned_migration.py`` compares the live classes with
these. The package is deleted together with that file; its module docstring
lists the conditions.
"""
