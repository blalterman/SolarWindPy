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

The region of space within the Sun's envelope of influence is called the heliosphere.
The field of heliophysics starts in the solar interior and extends out to the very local interstellar medium, just beyond the heliosphere.
The solar wind is a stream of charged particles that continuously flows away from the Sun, carrying, mass, energy, and momentum along with an embedded magnetic field.
In short, it mediates the interaction of the Sun with the heliosphere and this is a feature shared by stars and their astrospheres more broadly.
Changes in the solar wind create space weather, which is a critical threat to our technological infrastructure on Earth and in space.
SolarWindPy provides a unified framework for analyzing the solar wind and space weather data, filling the gap between packages targeting astronomy, remote observations of the Sun, and general timeseries analysis of spacecraft based data.
The package is now available via PyPI and can be installed using `pip install solarwindpy`.



# Statement of Need

There is a growing ecosystem of python libraries to enable astrophysics, solar physics, plasma physics, and space physics.
The table below cites key examples.
Notably, there are several packages that support different elements of space physics, including magnetospheric data analysis (Pysat), integration of magnetospheric observations (SpacePy), and the retrieval and analysis of heliophysics timeseries data (pySpedas and PyTplot).
Tools for the dedicated analysis of solar wind observations are noticeably absent.
SolarWindPy fills this gap by providing a unified framework for analyzing solar wind observations in combination with relevant information about the spacecraft from which the observations were made.

 Library  | Purpose                                                                                                      | Citation 
:--------:|:------------------------------------------------------------------------------------------------------------:|:--------:
 AstroPy  |  Astronomical observations.                                                                                  | [@astropy:2013, @astropy:2018, @astropy:2022]    
 SunPy    |  Remote sensing observations of the Sun.                                                                     | [@sunpy_community2020, @MFC+20, @Barnes2020]    
 PlasmaPy |  Theoretical plasma physics.                                                                                 | [@plasmapy_community_2025_16747747]    
 SpacePy  |  Analysis of timeseries data and integration with numerical modeling with a focus on mangetospheric physics. | [@niehof2022spacepy, @spacepy_code]    
 Pysat    |  Analysis of data from magnetospheric missions.                                                              | [@pysatcode, @Stoneback2018, @Stoneback2023]    
 pySpedas |  Retrieval and plotting of heliophysics timeseries data.                                                     | [@Grimes2022]    
 PyTplot  |  Focus on timeseries and spectrograph spacecraft data.                                                       | [@pytplot2019]    

The SolarWindPy framework utilizes a pythonic, class-based architecture that combines ion and magnetic field objects into a single, unified plasma.
It is designed for both experienced researchers and to provide an intuitive scaffold for students learning to analyze spacecraft data.
SolarWindPy's primary functionality (core, fitfunctions, plotting, instabilities, and solar_activity submodules along with the core tests) were written by the author and developed in support of multiple publications [@Alterman2018; @Wind:SWE:Wk; @Wind:SWE:ahe:xhel; @Wind:SWE:ahe:dnn, @Wind:SWE:ahe:phase; @Wind:SWE:ahe:shutoff,ACE:SWICS:SSN,ACE:SWICS:FStransition].
It contains a well-developed test suite, which supports future development and provides quality assurance.

The package builds on well-established libraries including NumPy [@Harris2020; @VanderWalt2011], SciPy [@scipy], Matplotlib [@Hunter2007], and Pandas [@Mckinney2010; @McKinney2011; @Mckinney2013] to ensure that the dependencies are stable.
The plotting functionality retains the mapping between timeseries and aggregated observations to enable researchers to easily extract subsets of their observations for detailed analysis.
It also contains a submodule to map the quantities plotted to their file names, improving the mapping from the user's analysis to the saved output.
The non-linear fitting libraries (utilizing scipy optimize) are designed for multi-step fitting in which the user performs nested regression of one variable on parameters derived from fitting other quantities.
Submodules for the analysis of magnetohydrodynamic turbulence parameters and kinetic instabilities are also provided.
The `solar_activity` submodule provides the user with seamless access to solar activity indicators provided by the LASP Interactive Solar IRradiance Datacenter (LISIRD) [@LISIRD] and the Solar Information Data Center (SIDC) at the Royal Observatory of Belgium [@SIDC].
This tool enables easy comparison of solar wind parameters across different phases of the solar cycle and different solar cycles, which is an essential component of solar wind data analysis.
SolarWindPy currently stores data in pandas DataFrames and Timeseries objects.
However, there is a clear separation between the two libraries such that future development could transition to using more nuanced and scientifically-targeted data structures, for example those provided by xarray [@xarray], SunPy, or AstroPy.


# References

[@astropy:2013]
[@astropy:2018]
[@astropy:2022]
[@sunpy_community2020]
[@MFC+20]
[@Barnes2020]
[@plasmapy_community_2025_16747747]
[@niehof2022spacepy]
[@spacepy_code]
[@pysatcode]
[@Stoneback2018]
[@Stoneback2023]
[@Grimes2022]
[@pytplot2019]
[@Alterman2018]
[@Wind:SWE:Wk]
[@Wind:SWE:ahe:xhel]
[@Wind:SWE:ahe:dnn]
[@Wind:SWE:ahe:phase]
[@Wind:SWE:ahe:shutoff]
[@ACE:SWICS:SSN]
[@ACE:SWICS:FStransition]
[@Harris2020]
[@VanderWalt2011]
[@scipy]
[@Hunter2007]
[@Mckinney2010]
[@McKinney2011]
[@Mckinney2013]
[@LISIRD]
[@SIDC]
[@Vanlommel2005]
[@claude_code_2024]
[@xarray]

# Acknowledgements

Recognize anyone who helped or contributed but does not meet authorship criteria (funders, contributors, mentors, etc.).
The author acknowledges NASA contrat NNX14AR78G and grants 80NSSC22K1011, 80NSSC22K0645, and 80NSSC20K1844.
The author thanks L. Woodham and R. D'Amicis for discussions about Alfvénic turbulence and calculating the Elsasser variables.
Claude-code [@claude_code_2024] was used to develop tests for submodules outside of `core`, write missing docstrings, and create the deployment workflow (including readthedocs).
Code written by Claude-code was reviewed and verified by the author.

