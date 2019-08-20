#! /bin/sh

if [[ "$#" -eq 0 ]]; then
    read -spt 60 "Environment name?" envname
else
    envname=$1
fi

echo $envname


core="pandas scipy numpy numexpr bottleneck matplotlib pytables"
dev="setuptools twine wheel flake8 black sphinx sphinx_rtd_theme pre_commit"
use="ipython jupyter nbdime widgetsnbextension yaml pyyaml astropy sunpy"

pkgs="$core $dev $use"

conda create -n $envname python=3 $pkgs
#                         pandas \
#                         scipy \
#                         numpy \
#                         numexpr \
#                         bottleneck \
#                         matplotlib \
#                         pytables \
#                         #jupyter \
#                         #nbdime \
#                         #widgetsnbextension \
#                         #"mkl_fft=1.0.6" \
#                         yaml \
#                         pyyaml \
#                         #"pyyaml>=4.2b1" \
#                         astropy \
#                         #setuptools \
#                         #twine \
#                         #wheel \
#                         #flake8 \
#                         #black \
#                         #sphinx \
#                         #sphinx_rtd_theme \
#                         #pre_commit
#

# conda activate $envname

# conda info
