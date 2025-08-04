---
name: SweepAI Task Template
about: Use this template to request a code update, refactor, or documentation change via SweepAI.
labels: [sweep]
---

> Extracted from solarwindpy/plans/combined_plan_with_checklist_documentation.md

## 🧠 Context

Combined Documentation Plan and Task List for SolarWindPy (update-2025 branch)

## 🎯 Overview of the Task

- Add CI workflow `.github/workflows/doc-build.yml` to build documentation and fail on warnings.
- Use GitHub Actions to deploy to `gh-pages`.
- Configure Read the Docs with `.readthedocs.yaml`.
- Validate locally by running `sphinx-apidoc` and `make html` without errors or warnings and testing links and snippets.

## 🔧 Framework & Dependencies

- Sphinx
- Read the Docs

## 📂 Affected Files and Paths

- .github/workflows/doc-build.yml

## 📊 Figures, Diagrams, or Artifacts (Optional)

None

## ✅ Acceptance Criteria

- [ ] Add CI workflow `.github/workflows/doc-build.yml` to install docs requirements and run `make html`
- [ ] Execute `make html` in `docs/` and confirm no errors or warnings
- [ ] Test links, code snippets, and formatting in the generated site
- [ ] Configure Read the Docs with `.readthedocs.yaml`
- [ ] Create `.github/workflows/deploy-docs.yml` to build and push to `gh-pages`

## 🧩 Decomposition Instructions (Optional)

None

## 🤖 Sweep Agent Instructions (Optional)

None

## 💬 Additional Notes

None
