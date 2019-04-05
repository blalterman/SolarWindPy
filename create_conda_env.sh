#! /bin/sh

if [[ "$#" -eq 0 ]]; then
    read -spt 60 "Environment name?" envname
else
    envname=$1
fi

echo $envname

conda create -n $envname python=3 \
                         pandas \
                         scipy \
                         numpy \
                         numexpr \
                         bottleneck \
                         #matplotlib \
                         pytables \
                         #jupyter \
                         #nbdime \
                         #widgetsnbextension \
                         yaml \
                         "pyyaml>=4.2b1" \
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

conda activate $envname

