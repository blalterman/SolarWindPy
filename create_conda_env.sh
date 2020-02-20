#! /bin/sh

if [[ "$#" -eq 0 ]]; then
    read -spt 60 "Environment name?" envname
else
    envname=$1
fi

echo $envname


core="pandas scipy numpy numexpr bottleneck matplotlib pytables"
dev="setuptools twine wheel flake8 black sphinx sphinx_rtd_theme pre_commit"
use="jupyter nbdime widgetsnbextension yaml pyyaml astropy sunpy heliopy"

pkgs="$core $dev $use"

conda create -n $envname python=3.7 $pkgs

#conda activate $envname

