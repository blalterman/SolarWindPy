---
title: 'SolarWindPy: A Heliophysics Data Analysis Tool Set'
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
    affiliation: 1
affiliations:
  - name: Independent Scientist
    index: 1
date: 13 November 2025
bibliography: paper.bib
---

# Summary

The region of space within the Sun's envelope of influence is called the heliosphere (the bubble of solar influence extending beyond the planets).
The field of heliophysics (the study of the Sun and its influence throughout the solar system) starts in the solar interior and extends out to the very local interstellar medium, just beyond the heliosphere.
The solar wind is a stream of charged particles that continuously flows away from the Sun, carrying, mass, energy, and momentum along with an embedded magnetic field.
In short, it mediates the interaction of the Sun with the heliosphere and this is a feature shared by stars and their astrospheres more broadly.
Changes in the solar wind are one source of space weather, which is a critical threat to our technological infrastructure on Earth and in space.
SolarWindPy provides a unified framework for analyzing the solar wind and related space weather data, filling the gap between packages targeting astronomy, remote observations of the Sun, and general timeseries analysis of spacecraft based data.
The package is available via PyPI^[https://pypi.org/project/solarwindpy/] and conda-forge^[https://anaconda.org/conda-forge/solarwindpy] and can be installed using `pip install solarwindpy` or `conda install -c conda-forge solarwindpy`.



# Statement of Need

There is a growing ecosystem of python libraries to enable astrophysics, solar physics, plasma physics, and space physics.
The table below cites key examples.
Notably, there are several packages that support different elements of space physics, including magnetospheric data analysis (Pysat), integration of magnetospheric observations (SpacePy), and the retrieval and analysis of heliophysics timeseries data (pySpedas and PyTplot).
Tools for the dedicated analysis of solar wind observations are noticeably absent.
SolarWindPy fills this gap by providing a unified framework for analyzing solar wind observations in combination with relevant information about the spacecraft from which the observations were made.
The package targets heliophysics researchers analyzing spacecraft observations, from graduate students learning plasma analysis to experienced scientists conducting multi-mission data studies.

+----------+--------------------------------+---------------------------------------+
| Library  | Purpose                        | Citation                              |
+==========+================================+=======================================+
| AstroPy  | Astronomical observations.     | [@astropy:2013; @astropy:2018;        |
|          |                                | @astropy:2022]                        |
+----------+--------------------------------+---------------------------------------+
| SunPy    | Remote sensing observations    | [@sunpy_community2020; @MFC+20;       |
|          | of the Sun.                    | @Barnes2020]                          |
+----------+--------------------------------+---------------------------------------+
| PlasmaPy | Theoretical plasma physics.    | [@plasmapy_community_2025_16747747]   |
+----------+--------------------------------+---------------------------------------+
| SpacePy  | Timeseries analysis and        | [@niehof2022spacepy;                  |
|          | magnetospheric modeling.       | @spacepy_code]                        |
+----------+--------------------------------+---------------------------------------+
| Pysat    | Magnetospheric mission data    | [@pysatcode; @Stoneback2018;          |
|          | analysis.                      | @Stoneback2023]                       |
+----------+--------------------------------+---------------------------------------+
| pySpedas | Retrieval and plotting of      | [@Grimes2022]                         |
|          | heliophysics timeseries.       |                                       |
+----------+--------------------------------+---------------------------------------+
| PyTplot  | Timeseries and spectrograph    | [@pytplot2019]                        |
|          | data visualization.            |                                       |
+----------+--------------------------------+---------------------------------------+    

The SolarWindPy framework utilizes a pythonic, class-based architecture that combines ion and magnetic field objects into a single, unified plasma.
It is designed for both experienced researchers and to provide an intuitive scaffold for students learning to analyze spacecraft data.
SolarWindPy's primary functionality (core, fitfunctions, plotting, instabilities, and solar_activity submodules) was written by the author and developed or utilized in support of multiple publications [@Alterman2018; @Wind:SWE:Wk; @Wind:SWE:ahe:xhel; @Wind:SWE:ahe:dnn; @Wind:SWE:ahe:phase; @Wind:SWE:ahe:shutoff; @ACE:SWICS:SSN; @ACE:SWICS:FStransition].
The transformation from thesis research code to a production package deployable via PyPI and conda-forge was accomplished using AI-assisted development with specialized quality assurance infrastructure for the supporting infrastructure (test suites, documentation, and deployment workflows), while the core scientific functionality remains human-authored.

The package builds on NumPy [@Harris2020; @VanderWalt2011], SciPy [@scipy], Matplotlib [@Hunter2007], and Pandas [@Mckinney2010; @McKinney2011; @Mckinney2013] to ensure stable dependencies.
The plotting module maintains timeseries-to-observation mappings for interactive data extraction and automatically maps plotted quantities to descriptive filenames for analysis traceability.
Non-linear fitting libraries support multi-step nested regression workflows for parameter estimation.
Submodules provide magnetohydrodynamic turbulence analysis and kinetic instability calculations.
The `solar_activity` submodule provides seamless access to solar activity indicators from LISIRD [@LISIRD] and SIDC [@Vanlommel2005], enabling solar wind analysis across solar cycle phases.
Data storage currently uses pandas DataFrames and Timeseries, with architecture supporting transitions to xarray [@xarray], SunPy, or AstroPy data structures.

## Quality Assurance and AI-Assisted Development

SolarWindPy's evolution from thesis research code [@AltermanThesis; @Alterman2018; @Wind:SWE:ahe:phase] to a production software package required systematic quality assurance for comprehensive testing, documentation, and deployment infrastructure.
To be explicit about the scope of AI assistance: the core scientific modules (`core/`, `fitfunctions/`, `plotting/`, `instabilities/`, `solar_activity/`) containing the physics algorithms and analysis methods were developed by the author without AI assistance and represent the scholarly contribution of this work, validated through eight peer-reviewed publications [@Alterman2018; @Wind:SWE:Wk; @Wind:SWE:ahe:xhel; @Wind:SWE:ahe:dnn; @Wind:SWE:ahe:phase; @Wind:SWE:ahe:shutoff; @ACE:SWICS:SSN; @ACE:SWICS:FStransition].
AI-assisted development was used exclusively for supporting infrastructure: test suites, continuous integration pipelines, package deployment workflows, and completion of docstring documentation.

The quality assurance methodology utilizes Claude Code [@claude_code_2024] with domain-specific validation infrastructure designed for scientific computing correctness.
This approach maintains clear boundaries between deterministic and agentic tasks by combining specialized agents and pre-commit hooks to ensure correctness, while the scientific algorithms remain entirely human-authored as evidenced by their multi-year publication history.
This systematic validation enabled development of comprehensive test suites (targeting ≥95% coverage, with core physics modules achieving ≥95% and overall coverage at 78%), completion of documentation including missing docstrings, and creation of continuous integration and deployment pipelines for PyPI, conda-forge, and ReadTheDocs.

The complete infrastructure, including agent specifications, pre-commit hooks, and workflow automation, is publicly available in the `.claude/` directory of the repository, establishing a reproducible framework for quality assurance in AI-assisted scientific software development.

# Acknowledgements

The author thanks L. Woodham and R. D'Amicis for discussions about Alfvénic turbulence and calculating the Elsasser variables.
In line with the transition to AI-augmented software development, Claude code [@claude_code_2024] was used in writing this paper.

# References
