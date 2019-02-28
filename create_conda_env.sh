#! /bin/sh

conda create -n $1 python=3 \
                   pandas \
                   scipy \
                   numpy \
                   numexpr \
                   bottleneck \
                   setuptools \
                   twine \
                   wheel \
                   matplotlib \
                   astropy \
                   flake8 \
                   black \
                   pre_commit \
                   sphinx \
                   sphinx_rtd_theme \
                   pre_commit
