Installation
============

.. contents::
   :local:
   :depth: 2

Requirements
------------

SolarWindPy requires Python 3.11 or later and has the following core
dependencies:

- NumPy ≥ 1.20.0
- Pandas ≥ 1.3.0
- SciPy ≥ 1.7.0
- Matplotlib ≥ 3.5.0
- Astropy ≥ 5.0.0

Installation from PyPI
----------------------

The recommended way to install SolarWindPy is from PyPI using :command:`pip`:

.. code-block:: bash

   pip install solarwindpy

This will install the latest stable release along with all required
dependencies.

Development Installation
------------------------

To work with the latest development version, clone the repository and install
in development mode:

.. code-block:: bash

   git clone https://github.com/blalterman/SolarWindPy.git
   cd SolarWindPy
   pip install -e .

For contributors, install the additional development tools:

.. code-block:: bash

   pip install -r requirements-dev.txt

Conda Environment Setup
------------------------

For a complete scientific Python environment, use the provided conda
environment file:

.. code-block:: bash

   conda env create -f solarwindpy-20250403.yml
   conda activate solarwindpy-20250403

Verification
------------

To verify your installation, run:

.. code-block:: python

   import solarwindpy as swp
   print(f"SolarWindPy version: {swp.__version__}")

Troubleshooting
---------------

If you encounter installation issues:

1. Ensure you have Python 3.11 or later
2. Update pip: ``pip install --upgrade pip``
3. Consider using a virtual environment
4. Check the `GitHub Issues <https://github.com/blalterman/SolarWindPy/issues>`_ for known problems
