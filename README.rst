###########
SolarWindPy
###########

|Build Status| |Docs Status| |Black Code|

|PyPI| |Conda|

|Python| |License| |Zenodo|

Python data analysis tools for solar wind measurements.

Quick Start
-----------

After installation, import the package and create a plasma object with sample data:

.. code-block:: python

   import solarwindpy as swp
   import pandas as pd

   # Create sample solar wind data (3 time points)
   epoch = pd.date_range('2023-01-01', periods=3, freq='1h')
   columns = pd.MultiIndex.from_tuples([
       ('n', '', 'p1'), ('n', '', 'a'),           # Number density
       ('v', 'x', 'p1'), ('v', 'x', 'a'),         # Velocity components
       ('v', 'y', 'p1'), ('v', 'y', 'a'),
       ('v', 'z', 'p1'), ('v', 'z', 'a'),
       ('w', 'par', 'p1'), ('w', 'par', 'a'),     # Thermal speeds
       ('w', 'per', 'p1'), ('w', 'per', 'a'),
       ('b', 'x', ''), ('b', 'y', ''), ('b', 'z', '')  # Magnetic field
   ], names=['M', 'C', 'S'])

   # Realistic solar wind values
   data = pd.DataFrame([
       [5.0, 0.25, 400, 380, 10, 5, -20, -15, 30, 15, 25, 12, 3.5, -1.2, 0.8],
       [8.0, 0.40, 450, 420, 15, 8, -25, -18, 35, 18, 28, 14, 4.1, -1.5, 1.2],
       [6.5, 0.30, 420, 400, 12, 6, -22, -16, 32, 16, 26, 13, 3.8, -1.3, 0.9],
   ], index=epoch, columns=columns)

   # Create plasma object with protons and alphas
   plasma = swp.Plasma(data, 'p1', 'a')

   # Access ion species
   print(plasma.species)  # ('a', 'p1')
   print(f"Proton density: {plasma.p1.n.mean():.1f} cm⁻³")

See the documentation for detailed usage examples and API reference.

Installation
============

The supported Python versions and dependency ranges are declared in
`pyproject.toml <https://github.com/blalterman/SolarWindPy/blob/master/pyproject.toml>`_
(``requires-python`` and ``dependencies``); the PyPI page
shows them for each published release.

SolarWindPy is available via PyPI and conda-forge:

User
----

Install from PyPI:

.. code-block:: bash

   pip install solarwindpy

Or install from conda-forge:

.. code-block:: bash

   conda install -c conda-forge solarwindpy

Development
-----------

1. Fork the repository and clone your fork.
2. Install development dependencies:

   .. code-block:: bash

      git clone https://github.com/YOUR-USERNAME/SolarWindPy.git
      cd SolarWindPy
      pip install -e ".[dev]"  # Includes all dev tools

   **Alternative (Conda environment)**:

   .. code-block:: bash

      conda env create -f solarwindpy.yml
      conda activate solarwindpy
      pip install -e .

3. Run the test suite with ``pytest``:

   .. code-block:: bash

      pytest -q

**Note**: ``pyproject.toml`` is the only dependency declaration; there are no lockfiles.

4. Optionally install the pre-commit hooks:

   .. code-block:: bash

      pre-commit install

   This will run ``black`` and ``flake8`` automatically when committing.

5. Build the documentation and fail on warnings:

   .. code-block:: bash

      cd docs
      make html SPHINXOPTS=-W


License
=======

SolarWindPy is licensed under a standard 3-clause BSD license. See
`LICENSE`_.

Acknowledging and Citing SolarWindPy
====================================

See `CITATION.rst`_ for instructions on citing SolarWindPy.

.. _LICENSE: ./LICENSE
.. _CITATION.rst: ./CITATION.rst

.. |Build Status| image:: https://github.com/blalterman/SolarWindPy/actions/workflows/ci-master.yml/badge.svg?branch=master
   :target: https://github.com/blalterman/SolarWindPy/actions/workflows/ci-master.yml
.. |Docs Status| image:: https://readthedocs.org/projects/solarwindpy/badge/?version=latest
   :target: https://solarwindpy.readthedocs.io/en/latest/?badge=latest
.. |License| image:: https://img.shields.io/badge/License-BSD%203--Clause-blue.svg
   :target: ./LICENSE
.. |Black Code| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
.. |Zenodo| image:: https://img.shields.io/badge/DOI-10.5281%2Fzenodo.17042839-blue.svg
   :target: https://doi.org/10.5281/zenodo.17042839
.. |PyPI| image:: https://img.shields.io/pypi/v/solarwindpy.svg
   :target: https://pypi.org/project/solarwindpy/
.. |Python| image:: https://img.shields.io/pypi/pyversions/solarwindpy.svg
   :target: https://pypi.org/project/solarwindpy/
.. |Conda| image:: https://img.shields.io/conda/vn/conda-forge/solarwindpy.svg
   :target: https://anaconda.org/conda-forge/solarwindpy
