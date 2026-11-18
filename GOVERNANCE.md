<!--
Spent-When: PERMANENT(a later governance of SolarWindPy replaces this one)
Supersedes: none
-->

# Governance of SolarWindPy

## Purpose

The heliophysics community has one coherent, cohesive source of tools for in situ solar wind
data analysis, usable on measurements from any mission. The tools encode our physical
intuition and our intuition for how to analyze the data, in a form that transmits both to the
researchers who use them. Through it, researchers build on each other's capabilities and skills
instead of rebuilding them, and the results they draw are physically correct and reproducible
from the version they cite. The science moves forward more easily, more coherently, and faster.

## Intent

- **Scope.** SolarWindPy ingests the physical parameters that instrument pipelines and other
  tools derive from in situ solar wind measurements, and analyzes them together with the
  context needed to interpret them, such as solar activity indicators and event catalogs. The
  conclusions drawn from that analysis belong to the researcher who draws them.
- **One data model for every mission.** Measurements live in pandas DataFrames whose columns are
  a three-level index of measurement, component, and species. Values are stored in display units
  (km/s, cm⁻³, nT, and so on), each quantity's unit is defined once, calculations convert to SI
  and back through those definitions, and NaN marks missing data. Data from any spacecraft runs
  through the same tools.
- **Defined once, layered.** Each physical quantity, unit, and convention is defined once, each
  name predicts what it holds, and each layer builds only on the layers beneath it.
- **Physics carries its reasoning.** Each implemented result cites its source, and docstrings
  and doctested guides explain how and why each tool is applied.
- **The author's judgment, AI's execution.** The author holds the physics and the public API.
  AI carries the execution against declared conventions and tests, so the author's attention
  goes to the physics. A passing test shows the code does what the test says; whether the
  physics is right is the author's judgment.
- **Test-first, continuously verified.** Changes land test-first, and every change runs the test
  suite, the documentation build, and the doctests on every major operating system.
- **Open, archived releases.** SolarWindPy is BSD-3 licensed and distributed through PyPI and
  conda-forge, and each release is archived on Zenodo under one concept DOI, so a paper cites
  the exact version it used.
- **Part of the heliophysics Python ecosystem.** SolarWindPy meets the community's shared
  standards (PyHC), so researchers install and use it alongside the other heliophysics packages
  they work with.
- **Curated contribution.** Researchers contribute their tools to SolarWindPy, and the author
  curates the physics, the public API, and the design, so that what they contribute joins one
  coherent source. Stewardship widens to others as the coherence of the design is transmitted
  to them.

## Objectives

- Researchers outside the author's group publish results that cite the SolarWindPy concept DOI.
- The documentation carries worked examples that run data from at least two missions through
  the same tools.
- Changes from contributors other than the author are merged, and the design stays coherent
  through them.
- SolarWindPy is listed as a PyHC package.
- Every implemented physical result cites its source (DOI or arXiv, and the equation number) in
  its docstring.
- Public docstrings meet PyHC standard 8, and every example in the documentation runs as a
  doctest.
- On master, the test suite, the documentation build with warnings as errors, and the
  import-layering check pass on Linux for every commit, and on Linux, macOS, and Windows for
  every supported Python version on a weekly schedule and before every release.
- Every release installs from PyPI and conda-forge and carries a Zenodo DOI under the concept
  DOI, and `CITATION.cff` names the current release.
- Dependency floors sit inside the PHEP 3 window apart from the exceptions `CONTRIBUTING.md`
  lists, and the test suite passes at the lowest versions allowed.
