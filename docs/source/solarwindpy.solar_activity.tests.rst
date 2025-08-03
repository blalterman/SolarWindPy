solarwindpy.solar_activity test plan
====================================

.. note::
   All tests described below should reside in ``solarwindpy/tests/solar_activity``.

__init__.py
------------
- Ensure ``get_all_indices`` returns a ``DataFrame`` with columns ``Lalpha``, ``ssn``, ``MgII`` and ``CaK``.
- Validate that the returned index is a :class:`pandas.DatetimeIndex`.
- Confirm that the module-level alias ``ssn`` refers to :mod:`solarwindpy.solar_activity.sunspot_number`.

base.py
-------
- ``ID.set_key`` accepts known keys and raises ``NotImplementedError`` for unknown keys.
- ``DataLoader.get_data_ctime`` handles an empty cache and derives creation time from file names.
- ``DataLoader.get_data_age`` returns the time difference between today and the cached date.
- ``DataLoader.maybe_update_stale_data`` calls ``download_data`` when cached data are out of date.
- ``ActivityIndicator.interpolate_data`` interpolates without extrapolating past the source range.
- ``IndicatorExtrema.calculate_intervals`` produces rise, fall and full-cycle intervals.
- ``IndicatorExtrema.calculate_extrema_bands`` builds intervals around minima and maxima.

lisird.lisird module
--------------------
- ``LISIRD_ID`` builds correct URLs for supported keys and rejects invalid keys.
- ``LISIRDLoader.convert_nans`` replaces LISIRD specific missing values.
- ``LISIRDLoader.verify_monotonic_epoch`` removes duplicate timestamps.
- ``LISIRDLoader.download_data`` writes CSV and JSON files and deletes previous versions.
- ``LISIRD.load_data`` populates the loader and metadata attributes.
- ``LISIRD.interpolate_data`` maps the selected column onto a target index.
- ``LISIRDExtrema.load_or_set_data`` obtains extrema from :class:`ExtremaCalculator`.

lisird.extrema_calculator module
--------------------------------
- ``ExtremaCalculator.set_threshold`` accepts scalars, callables and defaults correctly.
- ``cut_data_into_extrema_finding_intervals`` segments the rolled series using threshold crossings.
- ``_find_extrema`` and ``find_extrema`` detect minima and maxima in example data.
- ``format_extrema`` returns a table indexed by cycle number.

plots.py
--------
- ``IndicatorPlot.make_plot`` renders a basic line plot with formatted axes.
- ``SSNPlot`` sets the y-axis label and limits appropriate for sunspot number.

sunspot_number.sidc module
--------------------------
- ``SIDC_ID`` maps keys to URLs and raises on invalid keys.
- ``SIDCLoader.convert_nans`` converts ``-1`` values to ``NaN``.
- ``SIDCLoader.download_data`` loads SIDC CSV data and saves cleaned files.
- ``SIDC.load_data`` attaches the loader and adds cycle labels.
- ``SIDC.interpolate_data`` interpolates the ``ssn`` column onto a new index.
- ``SIDC.calculate_extrema_kind`` and ``calculate_edge`` classify rising and falling periods.
- ``SIDC.run_normalization`` computes a ``nssn`` column for each cycle.
- ``SSNExtrema.load_or_set_data`` reads ``ssn_extrema.csv`` into a :class:`pandas.DataFrame`.
