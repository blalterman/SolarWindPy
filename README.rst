###########
SolarWindPy
###########

|Build Status| |License| |Black Code|

Python data analysis tools for solar wind measurements.

Installation
============

SolarWindPy will soon be installable from pip via
``pip install solarwindpy``. We plant to target conda quickly there
after, most likely through the ``conda-forge`` channel.

User
----

TODO

Development
-----------

1) Fork the repo.
2) Clone the repo.
3) Build and install development repo. From ``SolarWindPy`` directiory,
   execute
      >>> python setup.py sdist bdist_wheel
      >>> python setup.py develop
      
4) Intall ``flake8`` and ``black``
      >>> pre-commit install
   These are tools for checking code style, variable definitions, etc.
5) Verify the current tests pass.

   >>> python -m solarwindpy.tests.run_tests

License
=======

SolarWindPy is licensed under a standard 3-clause BSD license. See
:doc:`LICENSE.rst`.

Acknowledging and Citing SolarWindPy
====================================

See :doc:`CITATION.rst` for instructions on citing SolarWindPy.

.. _LICENSE.rst: ./LICENSE.rst
.. _CITATION.rst: ./CITATION.rst

.. |Build Status| image:: https://travis-ci.com/blalterman/SolarWindPy.svg?token=tsZeqtLHgqx3UJh7uvM8&branch=master
   :target: https://travis-ci.com/blalterman/SolarWindPy
.. |License| image:: https://img.shields.io/badge/License-BSD%203--Clause-blue.svg
   :target: ./LICENSE.rst
.. |Black Code| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
