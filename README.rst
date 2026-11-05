###########
SolarWindPy
###########

.. image:: https://raw.githubusercontent.com/blalterman/SolarWindPy/master/docs/source/_static/branding/solarwindpy-readme-banner-1600.png
   :alt: SolarWindPy: A Python Library for in situ solar wind data analysis
   :width: 100%

|Build Status| |Docs Status| |Ruff|

|PyPI| |Conda|

|Python| |License| |Zenodo|

A Python Library for *in situ* solar wind data analysis.

Quick Start
-----------

After installation, import the package and create a plasma object with sample data:

>>> import pandas as pd
>>> from solarwindpy.core.plasma import Plasma

>>> # Create sample solar wind data (3 time points)
>>> epoch = pd.date_range('2023-01-01', periods=3, freq='1h')
>>> columns = pd.MultiIndex.from_tuples([
...     ('n', '', 'p1'), ('n', '', 'a'),           # Number density
...     ('v', 'x', 'p1'), ('v', 'x', 'a'),         # Velocity components
...     ('v', 'y', 'p1'), ('v', 'y', 'a'),
...     ('v', 'z', 'p1'), ('v', 'z', 'a'),
...     ('w', 'par', 'p1'), ('w', 'par', 'a'),     # Thermal speeds
...     ('w', 'per', 'p1'), ('w', 'per', 'a'),
...     ('b', 'x', ''), ('b', 'y', ''), ('b', 'z', '')  # Magnetic field
... ], names=['M', 'C', 'S'])

>>> # Realistic solar wind values
>>> data = pd.DataFrame([
...     [5.0, 0.25, 400, 380, 10, 5, -20, -15, 30, 15, 25, 12, 3.5, -1.2, 0.8],
...     [8.0, 0.40, 450, 420, 15, 8, -25, -18, 35, 18, 28, 14, 4.1, -1.5, 1.2],
...     [7.1, 0.30, 420, 400, 12, 6, -22, -16, 32, 16, 26, 13, 3.8, -1.3, 0.9],
... ], index=epoch, columns=columns)

>>> # Create plasma object with protons and alphas
>>> plasma = Plasma(data, 'p1', 'a')

>>> # Access ion species
>>> print(plasma.species)
('a', 'p1')

>>> # Mean proton density: (5.0 + 8.0 + 7.1) / 3 = 6.7
>>> print(f"Proton density: {plasma.p1.n.mean():.1f} cm⁻³")
Proton density: 6.7 cm⁻³

See the `documentation <https://solarwindpy.readthedocs.io>`_ for the
quickstart, usage examples and the API reference.

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
      pip install -e ".[dev]"

3. Run the test suite with ``pytest``:

   .. code-block:: bash

      pytest -q

**Note**: ``pyproject.toml`` is the only dependency declaration; there are no lockfiles.

4. Optionally install the pre-commit hooks:

   .. code-block:: bash

      pre-commit install

   Each commit then runs the hooks that ``.pre-commit-config.yaml`` lists, and
   that file is the full list. Expect a commit that stages a ``.py`` file to
   run the full test suite.

5. Build the documentation and fail on warnings:

   .. code-block:: bash

      cd docs
      make html SPHINXOPTS="-W --keep-going -n"


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
.. |Docs Status| image:: https://img.shields.io/readthedocs/solarwindpy.svg
   :target: https://solarwindpy.readthedocs.io/en/latest/?badge=latest
.. |License| image:: https://img.shields.io/badge/License-BSD%203--Clause-blue.svg
   :target: ./LICENSE
.. |Ruff| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
   :target: https://github.com/astral-sh/ruff
.. |Zenodo| image:: https://img.shields.io/badge/DOI-10.5281%2Fzenodo.17042839-blue.svg
   :target: https://doi.org/10.5281/zenodo.17042839
.. |PyPI| image:: https://img.shields.io/pypi/v/solarwindpy.svg
   :target: https://pypi.org/project/solarwindpy/
.. |Python| image:: https://img.shields.io/pypi/pyversions/solarwindpy.svg
   :target: https://pypi.org/project/solarwindpy/
.. |Conda| image:: https://img.shields.io/conda/vn/conda-forge/solarwindpy.svg
   :target: https://anaconda.org/conda-forge/solarwindpy
