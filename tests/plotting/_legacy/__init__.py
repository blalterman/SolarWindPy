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

# Spent-Mark: served; migration green under two seeds incl. real Spiral agg and drawn comparisons (d3390351); real-data comparison 90 of 90 cell-14 h2_set histograms identical on 12 objects, old vs new and shared BinnedData+mask (Session C, snapshot 6578e94a), with author-reviewed figures; condition-3 coverage audit closed by d3390351
