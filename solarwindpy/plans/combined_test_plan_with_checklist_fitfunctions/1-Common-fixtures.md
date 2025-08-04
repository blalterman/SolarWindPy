---
name: 'FitFunction Combined Plan and Checklist: Common Fixtures'
about: Summarizes shared test fixtures for fitfunction tests with checklist items.
labels: [sweep, FitFunction]
---

> Extracted from solarwindpy/plans/combined_test_plan_with_checklist_fitfunctions.md

## 🧠 Context

Verify correctness, robustness, and coverage of the `solarwindpy.fitfunctions` submodule. This task focuses on shared fixtures used across tests. Testing uses `pytest` with fixtures and adheres to `AGENTS.md` guidelines (`pytest -q`, no skipping, style with `flake8` and `black`).

## 🎯 Overview of the Task

```python
import numpy as np
import pandas as pd
import pytest
from scipy.optimize import OptimizeResult

from solarwindpy.fitfunctions import core, gaussians, trend_fits, plots, tex_info
```

- `simple_linear_data`: 1D arrays `x = np.linspace(0, 1, 20)`, `y = 2 * x + 1 + noise`, `w = np.ones_like(x)`.
- `gauss_data`: sample `x`, generate `y = A · exp(-0.5((x - μ)/σ)²) + noise`.
- `small_n`: too few points to trigger `sufficient_data -> ValueError`.

## 🔧 Framework & Dependencies

- `pytest`
- `numpy`
- `pandas`
- `scipy`

## 📂 Affected Files and Paths

- `tests/fitfunctions/conftest.py`

## 📊 Figures, Diagrams, or Artifacts (Optional)

None.

## ✅ Acceptance Criteria

- [ ] Implement `simple_linear_data` fixture.
- [ ] Implement `gauss_data` fixture.
- [ ] Implement `small_n` fixture.

## 🧩 Decomposition Instructions (Optional)

None.

## 🤖 Sweep Agent Instructions (Optional)

None.

## 💬 Additional Notes

Follow repository style guidelines and run tests with `pytest -q`.
