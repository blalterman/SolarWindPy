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
    affiliation: Independent Scientist
date: YYYY-MM-DD
bibliography: paper.bib
---

# Summary

The region of space within the Sun's envelope of influence is called the heliosphere.
The field of heliophysics starts in the solar interior and extends out to the very local interstellar medium, just beyond the heliosphere.
The solar wind is a stream of charged particles that continuously flows away from the Sun, carrying, mass, energy, and momentum along with an embedded magnetic field.
In short, it mediates the interaction of the Sun with the heliosphere and this is a feature shared by stars and their astrospheres more broadly.
Changes in the solar wind are one source of space weather, which is a critical threat to our technological infrastructure on Earth and in space.
SolarWindPy provides a unified framework for analyzing the solar wind and related space weather data, filling the gap between packages targeting astronomy, remote observations of the Sun, and general timeseries analysis of spacecraft based data.
The package is available via PyPI^[https://pypi.org/project/solarwindpy/] and conda-forge^[conda-forge distribution for v0.1.5 pending resolution of CI infrastructure issue; see https://github.com/conda-forge/solarwindpy-feedstock/issues/8] and can be installed using `pip install solarwindpy` or `conda install -c conda-forge solarwindpy`.



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
SolarWindPy's primary functionality (core, fitfunctions, plotting, instabilities, and solar_activity submodules) was written by the author and developed or utilized in support of multiple publications [@Alterman2018,@Wind:SWE:Wk, @Wind:SWE:ahe:xhel,@Wind:SWE:ahe:dnn,@Wind:SWE:ahe:phase,@Wind:SWE:ahe:shutoff,@ACE:SWICS:SSN,@ACE:SWICS:FStransition].
The transformation from thesis research code to a production package deployable via PyPI and conda-forge was accomplished using AI-assisted development with specialized quality assurance infrastructure, enabling systematic completion of comprehensive test suites, documentation, and deployment workflows while maintaining scientific correctness.

The package builds on well-established libraries including NumPy [@Harris2020, @VanderWalt2011], SciPy [@scipy], Matplotlib [@Hunter2007], and Pandas [@Mckinney2010, @McKinney2011, @Mckinney2013] to ensure that the dependencies are stable.
The plotting functionality retains the mapping between timeseries and aggregated observations to enable researchers to easily extract subsets of their observations for detailed analysis.
The plot labeling functionality maps the quantities plotted to their file names, improving the mapping from the user's analysis to the saved output.
The non-linear fitting libraries (utilizing scipy optimize) are designed for multi-step fitting in which the user performs nested regression of one variable on parameters derived from fitting other quantities.
Submodules for the analysis of magnetohydrodynamic turbulence parameters and kinetic instabilities are also provided.
The `solar_activity` submodule provides the user with seamless access to solar activity indicators provided by the LASP Interactive Solar IRradiance Datacenter (LISIRD) [@LISIRD] and the Solar Information Data Center (SIDC) at the Royal Observatory of Belgium [@SIDC].
This tool enables easy comparison of solar wind parameters across different phases of the solar cycle and different solar cycles, which is an essential component of solar wind data analysis.
SolarWindPy currently stores data in pandas DataFrames and Timeseries objects.
However, there is a clear separation between the two libraries such that future development could transition to using more nuanced and scientifically-targeted data structures, for example those provided by xarray [@xarray], SunPy, or AstroPy.

## AI-Assisted Development Workflow

SolarWindPy's evolution from thesis research code [@AltermanThesis; @Alterman2018; @Wind:SWE:ahe:phase] to a production software package required comprehensive testing, documentation, and deployment infrastructure.
This was accomplished using Claude Code [@claude_code_2024] with custom AI development infrastructure designed for scientific computing quality assurance.

The implementation includes specialized domain-specific agents and automated validation workflows using pre-commit hooks for physics validation, test execution, and coverage monitoring.
This systematic approach enabled rapid development of test suites for modules outside the original `core` implementation, completion of documentation including missing docstrings, and creation of continuous integration and deployment pipelines for PyPI, conda-forge, and ReadTheDocs.
The current agent system contains 13 specialized agents with an extensible architecture designed for integration with Claude Code's skills system.
The infrastructure incorporates git commit integration, GitHub Issues planning workflows, and comprehensive audit trails to ensure traceability of all AI-generated modifications, establishing an infrastructure for trustworthy AI-assisted scientific software.

The project maintains a ≥95% test coverage target with core physics and plasma functionality comprehensively tested, while tests for advanced features such as fitfunctions and plotting capabilities remain in active development.
All code generated or modified by AI undergoes expert review to ensure scientific accuracy.
The complete AI-assisted development infrastructure, including agent specifications, validation hooks, and workflow automation, is publicly available in the `.claude/` directory of the repository.

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

The author thanks L. Woodham and R. D'Amicis for discussions about Alfvénic turbulence and calculating the Elsasser variables.
In line with the transition to AI-augmented software development, this paper was written using Claude code [@claude_code_2024].