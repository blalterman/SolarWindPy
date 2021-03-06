#! /bin/sh

# If you run into mkl-fft problems, try the following
#
#   conda config --add pinned_packages conda-forge::numpy
#
# to pin numpy to conda-forge.

if [[ "$#" -eq 0 ]]; then
    read -spt 60 "Environment name?" envname
else
    envname=$1
fi

echo $envname

function run_script() {

    echo pwd

    core="pandas scipy numpy numexpr bottleneck matplotlib pytables tqdm"
    dev="setuptools twine wheel flake8 black sphinx sphinx_rtd_theme pre_commit tqdm"
    use="jupyter nbdime ipywidgets yaml pyyaml astropy sunpy heliopy cdflib tabulate zlib numba multiprocess"

    pkgs="$core $dev $use"
    #pkgs="$core $dev"

    conda create -n $1 python=3.8 $pkgs

#    conda init zsh
#
#    conda activate $1
#    pip install blackcellmagic

}

run_script $envname

#core="pandas scipy numpy numexpr bottleneck matplotlib pytables cython"
#dev="setuptools twine wheel flake8 black sphinx sphinx_rtd_theme pre_commit"
#use="jupyter nbdime widgetsnbextension yaml pyyaml astropy sunpy heliopy cdflib tabulate zlib numba multiprocess"
#
#pkgs="$core $dev $use"
##pkgs="$core $dev"
#
#conda create -n $envname python=3.7 $pkgs

# conda activate $envname
# pip install blackcellmagic
