###########
SolarWindPy
###########

|Build Status| |Docs Status| |License| |Black Code|

Python data analysis tools for solar wind measurements.

Installation
============

SolarWindPy requires Python 3.10 or later.

SolarWindPy will soon be installable from pip via
``pip install solarwindpy``. We plant to target conda quickly there
after, most likely through the ``conda-forge`` channel.

User
----

Install from pip (when available):

.. code-block:: bash

   pip install solarwindpy  # Requires Python 3.10+

Development
-----------

1. Fork the repository and clone your fork.
2. Create a Conda environment using the provided YAML file (Python 3.10+):

   .. code-block:: bash

      conda env create -f solarwindpy-20250403.yml  # Python 3.10+
      conda activate solarwindpy-20250403
      pip install -e .

   Alternatively generate the environment from ``requirements-dev.txt``:

   .. code-block:: bash

      python scripts/requirements_to_conda_env.py --name solarwindpy-dev
      conda env create -f solarwindpy-dev.yml
      conda activate solarwindpy-dev
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

.. |Build Status| image:: https://github.com/blalterman/SolarWindPy/actions/workflows/ci.yml/badge.svg?branch=master
   :target: https://github.com/blalterman/SolarWindPy/actions/workflows/ci.yml
.. |Docs Status| image:: https://readthedocs.org/projects/solarwindpy/badge/?version=latest
   :target: https://solarwindpy.readthedocs.io/en/latest/?badge=latest
.. |License| image:: https://img.shields.io/badge/License-BSD%203--Clause-blue.svg
   :target: ./LICENSE.rst
.. |Black Code| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
