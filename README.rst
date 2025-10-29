###########
SolarWindPy
###########

|Build Status| |Docs Status| |Black Code|

|PyPI| |Conda|

|Python| |License| |Zenodo|

Python data analysis tools for solar wind measurements.

Quick Start
-----------

After installation, import the package and create a plasma object:

.. code-block:: python

   import solarwindpy as swp
   # Load plasma data (example with sample data)
   plasma = swp.Plasma()
   # Access ion species and magnetic field data
   print(plasma.data.columns)  # View available measurements

See the documentation for detailed usage examples and API reference.

Installation
============

SolarWindPy requires Python 3.10 or later.

SolarWindPy is available via PyPI and conda-forge:

User
----

Install from PyPI:

.. code-block:: bash

   pip install solarwindpy  # Requires Python 3.10+

Or install from conda-forge:

.. code-block:: bash

   conda install -c conda-forge solarwindpy

Development
-----------

1. Fork the repository and clone your fork.
2. Create a Conda environment using the provided YAML file (Python 3.10+):

   .. code-block:: bash

      conda env create -f solarwindpy.yml  # Python 3.10+
      conda activate solarwindpy
      pip install -e .

   Alternatively generate the environment from ``requirements-dev.txt``:

   .. code-block:: bash

      python scripts/requirements_to_conda_env.py --name solarwindpy
      conda env create -f solarwindpy.yml
      conda activate solarwindpy
      pip install -e .

3. Run the test suite with ``pytest``:

   .. code-block:: bash

      pytest -q

4. Regenerate the Conda recipe if the version or dependencies change:

   .. code-block:: bash

      python scripts/update_conda_recipe.py

5. Optionally install the pre-commit hooks:

   .. code-block:: bash

      pre-commit install

   This will run ``black`` and ``flake8`` automatically when committing.

6. Build the documentation and fail on warnings:

   .. code-block:: bash

      cd docs
      make html SPHINXOPTS=-W


License
=======

SolarWindPy is licensed under a standard 3-clause BSD license. See
`LICENSE.rst`_.

Acknowledging and Citing SolarWindPy
====================================

See `CITATION.rst`_ for instructions on citing SolarWindPy.

.. _LICENSE.rst: ./LICENSE.rst
.. _CITATION.rst: ./CITATION.rst

.. |Build Status| image:: https://github.com/blalterman/SolarWindPy/actions/workflows/ci-master.yml/badge.svg?branch=master
   :target: https://github.com/blalterman/SolarWindPy/actions/workflows/ci-master.yml
.. |Docs Status| image:: https://readthedocs.org/projects/solarwindpy/badge/?version=latest
   :target: https://solarwindpy.readthedocs.io/en/latest/?badge=latest
.. |License| image:: https://img.shields.io/badge/License-BSD%203--Clause-blue.svg
   :target: ./LICENSE.rst
.. |Black Code| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
.. |Zenodo| image:: https://zenodo.org/badge/DOI/10.5281/zenodo.17057804.svg
  :target: https://doi.org/10.5281/zenodo.17057804
.. |PyPI| image:: https://img.shields.io/pypi/v/solarwindpy.svg
   :target: https://pypi.org/project/solarwindpy/
.. |Python| image:: https://img.shields.io/pypi/pyversions/solarwindpy.svg
   :target: https://pypi.org/project/solarwindpy/
.. |Conda| image:: https://img.shields.io/conda/vn/conda-forge/solarwindpy.svg
   :target: https://anaconda.org/conda-forge/solarwindpy
