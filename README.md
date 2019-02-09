# SolarWindPy
[![Build Status](https://travis-ci.com/blalterman/SolarWindPy.svg?token=tsZeqtLHgqx3UJh7uvM8&branch=master)](https://travis-ci.com/blalterman/SolarWindPy)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](./LICENSE.md)

Python data analysis tools for solar wind measurements.


## Installation
SolarWindPy will soon be installable from pip via ``pip install solarwindpy``.
We plant to target conda quickly there after, most likely through the ``conda-forge`` channel.

### User
TODO

### Development
1) Fork the repo.
2) Clone the repo.
3) Build and install development repo.
  From `SolarWindPy` directiory, execute 
    ```
    >>> python setup.py sdist bdist_wheel
    >>> python setup.py develop
    ```
4) Verify the current tests pass.
  ```
  >>> python -m solarwindpy.tests.run_tests
  ```
  

## License

SolarWindPy is licensed under a standard 3-clause BSD license. See [``LICENSE.md``](LICENSE.md).

## Acknowledging and Citing SolarWindPy

See [``CITATION.md``](CITATION.md) for instructions on citing SolarWindPy.
