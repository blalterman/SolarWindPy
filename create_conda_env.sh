#! /bin/sh

conda create -n $1 pandas scipy numpy numexpr bottleneck pycodestyle pydocstyle setuptools twine wheel matplotlib astropy pycodestyle flake8 black pre_commit sphinx
