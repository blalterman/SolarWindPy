# JOSS Repository Review Plan & Checklist

## Review Plan

This plan outlines the steps required to evaluate a GitHub repository for compliance with the Journal of Open Source Software (JOSS) submission requirements:

1. **Initial Assessment**

   * Confirm the repository is public and accessible without authentication.
   * Check that the repository contains actual research software (not just data, models, or notebooks).

2. **License Verification**

   * Verify the presence of an OSI-approved open-source license file.

3. **Repository Structure & Accessibility**

   * Ensure the repository contains a `paper.md` (and, if used, `paper.bib`) in the root or specified directory.
   * Confirm the repository’s issue tracker is open to the public.
   * Ensure all source code and documentation needed for installation and testing are present.

4. **Scope and Scholarly Effort**

   * Evaluate whether the software represents a substantial scholarly effort (typically at least 3 months by one person).
   * Confirm the software is sufficiently feature-rich and not a trivial or single-function utility.
   * Review the repository history (commits, issues, PRs) for evidence of development activity.

5. **Contributor and Author Eligibility**

   * Confirm the submitting author is a major contributor.
   * Ensure all authors listed in `paper.md` have contributed significantly (beyond supervision).
   * Verify all authors have GitHub accounts (for open peer review).

6. **Paper Content and Formatting**

   * Review `paper.md` for:

     * Non-specialist summary
     * Statement of need (how this software is novel or fills a gap)
     * Author names and affiliations
     * Acknowledgments (if any)
     * References section
     * 250–1000 word count
     * Markdown format

7. **Repository Archive and Release Setup**

   * Confirm the ability to create a tagged release of the software.
   * Plan for archiving the release on Zenodo or Figshare (for DOI assignment).

8. **Final Checklist & Pre-submission Review**

   * Use the checklist below to systematically verify compliance with all JOSS requirements.

---

## JOSS Requirements Review Checklist

* [ ] **Repository is public and accessible without authentication**
* [ ] **Repository contains research software (not just data, models, or notebooks)**
* [ ] **OSI-approved open-source license file is present** (`LICENSE`)
* [ ] **Repository includes `paper.md` in Markdown format**
* [ ] **`paper.md` includes a non-specialist summary**
* [ ] **`paper.md` includes a clear statement of need**
* [ ] **`paper.md` lists all author names and affiliations**
* [ ] **`paper.md` includes acknowledgments (if any)**
* [ ] **`paper.md` includes references section**
* [ ] **`paper.md` length is between 250 and 1000 words**
* [ ] **All source code and documentation are present and installable**
* [ ] **Repository’s issue tracker is open to the public**
* [ ] **Repository demonstrates substantial scholarly effort (≥ 3 months work, non-trivial functionality)**
* [ ] **Development history (commits, issues, PRs) supports claim of scholarly effort**
* [ ] **Submitting author is a major contributor to the project**
* [ ] **All listed authors have contributed significantly (not just supervisors)**
* [ ] **All authors have GitHub accounts (for open peer review)**
* [ ] **Can create a tagged software release**
* [ ] **Can archive software on Zenodo or Figshare to obtain a DOI**
* [ ] **Repository and paper do not focus on research *using* the software, but on the software itself**
* [ ] **No undisclosed conflicts of interest among authors**
* [ ] **All co-authors have agreed to the submission**

---

**Reference:**

* [JOSS Submission Requirements (Official Documentation)](https://joss.readthedocs.io/en/latest/submitting.html)

---