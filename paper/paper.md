---
title: 'SolarWindPy'
tags:
  - heliophysics
  - solar wind
  - space weather
  - plasma physics
  - space science
  - magnetohydrodynamics
  - data analysis
  - python
authors:
  - name: B. L. Alterman    
    orcid: 0000-0001-6673-3432
    affiliation: NASA Goddard Space Flight Center
date: YYYY-MM-DD
bibliography: paper.bib
---

# Summary

A brief, non-specialist summary describing what your software does, the scientific problem it addresses, and its major features and capabilities. (Approx. 2-4 sentences.)

The region of space within the Sun's envelope of influence is called the heliosphere.
The field of heliophysics starts in the solar interior and extends out to the very local interstellar medium, just beyond the heliosphere.
The solar wind is a stream of charged particles that continuously flows away from the Sun, carrying, mass, energy, and momentum along with an embedded magnetic field.
In short, it mediates the interaction of the Sun with the heliosphere and this is a feature shared by stars and their astrospheres more broadly.
Changes in the solar wind create space weather, which is a critical threat to our technological infrastructure on Earth and in space.
This software provides a unified framework for analyzing the solar wind and space weather data, filling the gap between packages targeting astronomy, remote observations of the Sun, and general timeseries analysis of spacecraft based data.



# Statement of Need

Clearly state the purpose of the software and the gap it fills in the current ecosystem. Explain why this package is needed, who it is for, and how it differs from or improves on existing solutions.


There is a growing ecosystem of python libraries to enable astrophysics, solar physics, plasma physics, and space physics.
The table below cites key examples.
Notably, there are several packages that support different elements of space physics, including magnetospheric data analysis (Pysat), integration of magnetospheric observations (SpacePy), and the retrieval and analysis of heliophysics timeseries data (pySpedas and PyTplot).
Tools for the dedicated analysis of solar wind observations are noticeably absent.
SolarWindPy fills this gap by providing a unified framework for analyzing solar wind observations in combination with relevant information about the spacecraft from which the observations were made.

 Library  | Purpose                                                                                                      | Citation 
:--------:|:------------------------------------------------------------------------------------------------------------:|:--------:
 AstroPy  |  Astronomical observations.                                                                                  | [key]    
 SunPy    |  Remote sensing observations of the Sun.                                                                     | [key]    
 PlasmaPy |  Theoretical plasma physics.                                                                                 | [key]    
 SpacePy  |  Analysis of timeseries data and integration with numerical modeling with a focus on mangetospheric physics. | [key]    
 Pysat    |  Analysis of data from magnetospheric missions.                                                              | [key]    
 pySpedas |  Retrieval and plotting of heliophysics timeseries data.                                                     | [key]    
 PyTplot  |  Focus on timeseries and spectrograph spacecraft data.                                                       | [key]    

The SolarWindPy framework utilizes a pythonic, class-based architecture that combines ion and magnetic field objects into a single, unified plasma.
It is designed for both experienced researchers and to provide an intuitive scaffold for students learning to analyze spacecraft data.
The package builds on well-established libraries [matplotlib, numpy, scipy, and pandas] to ensure that the dependencies are stable.
The plotting functionality retains the mapping between timeseries and aggregated observations to enable researchers to easily extract subsets of their observations for detailed analysis.
It also contains a submodule to map the quantities plotted to their file names, improving the mapping from the user's analysis to the saved output.
The non-linear fitting libraries are designed for multi-step fitting in which the user performs nested regression of one variable on parameters derived from fitting other quantities.
Submodules for the analysis of magnetohydrodynamic turbulence parameters and kinetic instabilities are also provided.
The `solar_activity` submodule provides the user with seamless access to solar activity indicators provided by the LASP Interactive Solar IRradiance Datacenter (LISIRD) [LISIRD] and the Solar Information Data Center (SIDC) [SIDC].
This tool enables easy comparison of solar wind parameters across different phases of the solar cycle and different solar cycles, which is an essential component of solar wind data analysis.


# References

<!--
Cite any works or software referenced above using the [@citation-key] format.
All references must be listed in a separate BibTeX file (paper.bib).
-->

AstroPy
SunPy
PlasmaPy
SpacePy
Pysat
pySpedas
PyTPlot
matplotlib
numpy
scipy
pandas
LISIRD
SIDC
Alterman2018
Wind:SWE:ahe:xhel
Wind:SWE:ahe:dnn
Wind:SWE:ahe:phase
Wind:SWE:ahe:herald
Claude-code

# Acknowledgements

Recognize anyone who helped or contributed but does not meet authorship criteria (funders, contributors, mentors, etc.).
The author acknowledges NASA contrat NNX14AR78G and grants 80NSSC22K1011, 80NSSC22K0645, and 80NSSC20K1844.
The author thanks L. Woodham and R. D'Amicis for discussions about Alfvénic turbulence and calculating the Elsasser variables.
The primary functionality of this software (core, fitfunctions, plotting, instabilities, and solar_activity submodules along with the core tests) were written by the author and developed in support of multiple publications [Alterman2018,Wind:SWE:ahe:xhel,Wind:SWE:ahe:dnn,Wind:SWE:ahe:phase,Wind:SWE:ahe:herald].
[Claude-code] was used to develop tests for the other submodules, write missing docstrings, and create the deployment workflow (including readthedocs).
Code written by Claude-code was reviewed and verified by the author.

