Installation
============

.. contents::
   :local:
   :depth: 2

Requirements
------------

``pyproject.toml`` is the single declaration of what SolarWindPy needs:
``requires-python`` gives the supported Python versions and ``dependencies``
gives the supported range of each required package. The
`PyPI page <https://pypi.org/project/solarwindpy/>`_ shows the same metadata for
each published release. :command:`pip` and :command:`conda` enforce these
ranges when they install the package, so you do not need to install the
dependencies yourself.

A published release and the development version can declare different ranges.
Read the ``pyproject.toml`` of the version you install.

Installation from PyPI
----------------------

.. code-block:: bash

   pip install solarwindpy

This installs the latest published release and its required dependencies.

Installation from conda-forge
-----------------------------

.. code-block:: bash

   conda install -c conda-forge solarwindpy

Development Installation
------------------------

To work with the development version, clone the repository and install it in
editable mode:

.. code-block:: bash

   git clone https://github.com/blalterman/SolarWindPy.git
   cd SolarWindPy
   pip install -e .

Contributors can install the testing, documentation, and linting tools
declared in the ``dev`` extra instead:

.. code-block:: bash

   pip install -e ".[dev]"

Conda Environment Setup
-----------------------

The repository's ``solarwindpy.yml`` creates a conda environment with the
dependencies and development tools, but not SolarWindPy itself. Install the
package into the environment afterwards:

.. code-block:: bash

   conda env create -f solarwindpy.yml
   conda activate solarwindpy
   pip install -e .

Verification
------------

To verify your installation, run:

>>> import solarwindpy as swp
>>> print(f"SolarWindPy version: {swp.__version__}")  # doctest: +ELLIPSIS
SolarWindPy version: ...
>>> swp.__version__ != "unknown"  # "unknown" means solarwindpy is not installed
True

Troubleshooting
---------------

If you encounter installation issues:

1. Check that your Python version satisfies ``requires-python`` for the
   version you are installing (see `Requirements`_)
2. Update pip: ``pip install --upgrade pip``
3. Consider using a virtual environment
4. Check the `GitHub Issues <https://github.com/blalterman/SolarWindPy/issues>`_
   for known problems
