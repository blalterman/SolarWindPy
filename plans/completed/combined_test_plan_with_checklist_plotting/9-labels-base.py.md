---
name: 'Combined Plan and Checklist: Base Labels'
about: Unified documentation and checklist for base label utilities in plotting.
labels: [sweep, plotting, TeXlabel, LaTeX]
---

> Extracted from solarwindpy/plans/combined_test_plan_with_checklist_plotting.md

## 🧠 Context

The `solarwindpy.plotting` subpackage offers high-level plotting utilities built on pandas
and Matplotlib. This unified plan combines the narrative test rationale and the
actionable checklist for validating every class, method, property (including non-public
interfaces), and helper function across:

- `base.py`
- `agg_plot.py`
- `histograms.py` (`hist1d.py`, `hist2d.py`)
- `scatter.py`
- `spiral.py`
- `orbits.py`
- `tools.py`
- `select_data_from_figure.py`
- `labels/base.py`
- `labels/special.py`

Tests are grouped by module. Each module section includes context from the original
narrative plan followed by a deduplicated checklist of actionable items.

- Namedtuples: `LogAxes`, `AxesLabels`, `RangeLimits` with defaults and custom
  values.
- Class `Base`: shared logic with `plotting/base`.

## 🎯 Overview of the Task

Implement comprehensive tests for `labels/base.py` within the `solarwindpy.plotting` package.

## 🔧 Framework & Dependencies

- pandas
- matplotlib
- pytest

## 📂 Affected Files and Paths

- solarwindpy/plotting/labels/base.py

## 📊 Figures, Diagrams, or Artifacts (Optional)

None

## ✅ Acceptance Criteria

- [x] Verify `MCS` namedtuple functionality
- [x] Test `Base` class properties and methods
- [x] Test `TeXlabel` initialization and properties
- [x] Test species substitution functionality
- [x] Test measurement and component translation
- [x] Test units translation and assignment
- [x] Test path generation with special characters
- [x] Test ratio labels with same/different units
- [x] Test template substitution patterns
- [x] Test tex cleanup and formatting
- [x] Test comparison operators and hashing
- [x] Test axis normalization types
- [x] Test error measurement handling
- [x] Test newline units formatting
- [x] Test setter methods validation
- [x] Test empty string handling

## 🧩 Decomposition Instructions (Optional)

None

## 🤖 Sweep Agent Instructions (Optional)

None

## 💬 Additional Notes

- Ensures correct functionality, edge-case handling, API stability, and protects
  non-public internals.

**Status**: ✅ COMPLETED
**Commit**: 5b47880
**Tests Added**: 23 comprehensive test cases
**Time Invested**: 1 hour  
**Test Results**: 23/23 passing (100% success rate)
