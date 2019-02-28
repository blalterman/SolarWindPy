#! /bin/sh

conda create -n $1 python=3 \
                   pandas \
                   scipy \
                   numpy \
                   numexpr \
                   bottleneck \
                   matplotlib \
                   jupyter \
                   nbdime \
                   widgetsnbextension \
                   yaml \
                   pyyaml \
                   astropy \
                   setuptools \
                   twine \
                   wheel \
                   flake8 \
                   black \
                   pre_commit \
                   sphinx \
                   sphinx_rtd_theme \
                   pre_commit

conda activate $1

