### **Recommended Python-Driven Workflow for Automated Test Plan Management**

#### **1. Initial Checklist → Issue Generation**

**a.** Write or update your test plan in Markdown with GitHub checkboxes.

**b.** Run a Python script (`generate_issues.py`):

* Parses the checklist (e.g., `- [ ] Test item`)
* Creates an individual GitHub issue for each checkbox using the API
* Posts a comment in each issue linking to the master checklist issue, and vice versa (collects issue URLs in the checklist for easy navigation)

**Best practice:** Add a unique ID or short summary in each issue title, e.g.,
`[Test] DataLoader.get_data_ctime parses date-named directories`

---

#### **2. Issue/PR Workflow & Checklist Sync**

**a.** Contributors implement tests and submit PRs that close the individual test issues using GitHub’s “Closes #ISSUE\_NUMBER” keyword in PR descriptions.

**b.** When a PR is merged:

* The linked test issue is automatically closed by GitHub
* The Python script (`sync_checklist.py`), triggered by webhooks, does the following:

  1. Finds closed test issues linked from the master checklist
  2. For each closed issue, updates the master checklist by changing the matching `- [ ]` to `- [x]`
  3. Adds the merged PR number in parentheses next to the checked item

---

#### **3. Automation & Triggering (via Webhooks)**

* **Checklist sync:** The script runs in response to GitHub webhook events:

  * `issues.closed`
  * `pull_request.closed` (if PR is merged and closes an issue)
* This ensures the master checklist is kept up to date automatically with every merged PR or closed issue.
* Issue creation script can still be run locally or triggered via workflow when the checklist changes.

---

#### **4. Conventions & Best Practices**

* **Checklist item format:**
  `- [ ] Description of test (closes #123)` (or keep mapping in the script if not embedding links)
* **Issue title:** Should map unambiguously to a checklist item (use a hash or unique string if test names are similar)
* **PR references:** Always reference the issue being closed with “Closes #123” in the PR body
* **Logging & error handling:** Script should log what it changes, skip ambiguous matches, and handle API errors gracefully (with retries or clear messages)

---

#### **5. Error Recovery**

* **Duplicate issues:** Before creating, script checks if issue with the same title exists
* **Checklist desync:** If checklist and issues get out of sync, rerun the sync script to re-align
* **Manual overrides:** Manual edits are possible; the script should always “recalculate” based on current states, not on a cached snapshot

---

#### **6. Tools/Libraries**

* [`PyGithub`](https://pygithub.readthedocs.io/en/latest/) for API calls
* [`python-markdown`](https://python-markdown.github.io/) or regex for checklist parsing

---

### **Summary Table**

| Step                  | Who/What Runs It       | Outcome                                      |
| --------------------- | ---------------------- | -------------------------------------------- |
| Checklist → Issues    | Python script/manual   | Each test item has a tracked GitHub issue    |
| PR → closes Issue     | Developer/PR reviewer  | PR merges auto-close related test issues     |
| Issue/PR → checklist  | Script via webhook     | Master checklist is updated to match reality |
| Reconciliation/Notify | Scheduled job or error | Manual/auto fix for any desync or error      |
| Retry/metrics/mapping | All scripts            | Reliable, observable, flexible automation    |
| Web UI                | Maintainers            | Low-friction oversight, manual triggers      |
---

**This workflow ensures robustness, reliability, and transparency for all contributors.**
