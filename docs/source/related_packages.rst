Related packages
================

Other Python packages in heliophysics overlap with parts of SolarWindPy.

`PlasmaPy <https://www.plasmapy.org>`_
   A general plasma formulary of single-value, unit-aware functions.
   SolarWindPy computes such quantities over multi-species *in situ* time
   series in its (M, C, S) MultiIndex data model, and can be used alongside
   PlasmaPy.

`PyRFU <https://github.com/louis-richard/irfu-python>`_
   Analysis tools for the Magnetospheric Multiscale (MMS) mission
   specifically. Its scope differs from SolarWindPy's mission-agnostic tools.

SAVIC
   Stability Analysis Vitalizing Instability Classification, a Python package
   for predicting, quantifying and classifying ion-driven plasma
   instabilities. Its machine-learning classification complements the
   published instability thresholds of :cite:`Verscharen2016a` in
   :py:mod:`solarwindpy.instabilities`.
