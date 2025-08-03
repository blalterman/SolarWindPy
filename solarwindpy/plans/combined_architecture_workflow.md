# Automated Test Plan Management: Architecture and Workflow

## Directory Structure

```
automation/
│
├── generate_issues.py           # Parse checklist, create issues, link to master
├── sync_checklist.py            # Update master checklist based on closed issues/PRs
├── webhook_server.py            # Flask/FastAPI server for GitHub webhooks
├── checklist_utils.py           # Shared parsing/mapping/updating logic
├── reconcile.py                 # Scheduled reconciliation of checklist/issues
├── notify.py                    # Email notification logic
├── metrics.py                   # Collect and report stats/logs
├── web_ui.py                    # (Optional but recommended) Simple admin web UI
├── config.yaml                  # Repo info, tokens, checklist file, master issue
└── requirements.txt             # PyGithub, Flask/FastAPI, pyyaml, etc.
```

## Flow Diagram

```plaintext
[Developer]           [GitHub]                    [Automation System]
    |                     |                               |
generate_issues.py -----> | --Creates Issues------------> |
    |                     |                               |
[Master Checklist]        |                               |
    |                     |                               |
[webhook events] -------->|--> webhook_server.py -------->|--> sync_checklist.py
    |                     |                               |       |
    |                     |                               |  updates checklist
    |                     |                               |  logs actions
    |                     |                               |--> notify.py (on error)
    |                     |                               |--> metrics.py (logging)
    |                     |                               |--> web_ui.py (admin)
[nightly schedule] ------>|--> reconcile.py ------------- |  update/notify/log
```

## Workflow Overview

1. Execute `generate_issues.py` to create GitHub issues from the master checklist.
1. Merge pull requests that reference and close those issues.
1. Webhooks trigger `sync_checklist.py` to update the checklist when issues or pull requests close.
1. Scheduled runs of `reconcile.py` resolve mismatches and report results.

## Component Responsibilities and Workflow

### A. `generate_issues.py`

**Responsibilities**

- Parses the Markdown checklist
- Creates a GitHub issue for each checkbox via API
- Posts a comment in each issue linking to the master checklist and updates the master with issue URLs

**Workflow Actions**

- [ ] Write or update the test plan in Markdown with GitHub checkboxes (#PR_NUMBER)
- [ ] Run `generate_issues.py` to parse the checklist and create GitHub issues (#PR_NUMBER)
- [ ] Include a unique ID or summary in each issue title (#PR_NUMBER)
- [ ] Prevent duplicate issues by checking existing titles (#PR_NUMBER)

### B. `sync_checklist.py`

**Responsibilities**

- Triggered by webhook events
- Fetches the master checklist and maps to linked issues
- Updates the checklist: toggles `[ ]` to `[x]` for closed issues and adds merged PR numbers
- Logs all actions for auditability

**Workflow Actions**

- [ ] Configure PRs to reference issues with "Closes #ISSUE_NUMBER" (#PR_NUMBER)
- [ ] Set up webhooks for `issues.closed` and `pull_request.closed` to trigger `sync_checklist.py` (#PR_NUMBER)
- [ ] Update the master checklist with `[x]` and append the PR number when an issue closes (#PR_NUMBER)
- [ ] Log checklist updates for auditability (#PR_NUMBER)

### C. `webhook_server.py`

**Responsibilities**

- Receives GitHub webhook POSTs
- Verifies signature/security
- Dispatches to `sync_checklist.py` and `notify.py`
- Logs events

**Workflow Actions**

- [ ] Deploy a webhook server to handle GitHub events (#PR_NUMBER)
- [ ] Verify webhook signatures for security (#PR_NUMBER)
- [ ] Dispatch events to `sync_checklist.py` and `notify.py` (#PR_NUMBER)
- [ ] Log all webhook events (#PR_NUMBER)

### D. `checklist_utils.py`

**Responsibilities**

- Parses and updates Markdown checklists
- Manages checklist ↔ issue mapping (using issue links, hashes, or front matter)
- Provides utilities for updating, searching, and maintaining consistency

**Workflow Actions**

- [ ] Maintain mapping between checklist items and issue URLs (#PR_NUMBER)
- [ ] Parse and update checklist files consistently (#PR_NUMBER)
- [ ] Log parsing and mapping operations (#PR_NUMBER)

### E. `reconcile.py`

**Responsibilities**

- Runs as a scheduled job (e.g., nightly)
- Scans all checklist items and related issues
- Resolves desynchronizations between checklist and issues
- Updates the master checklist and logs reconciliation actions

**Workflow Actions**

- [ ] Schedule a nightly reconciliation job (#PR_NUMBER)
- [ ] Recalculate checklist status to resolve desynchronization (#PR_NUMBER)
- [ ] Log reconciliation outcomes (#PR_NUMBER)
- [ ] Notify maintainers when manual intervention is needed (#PR_NUMBER)

### F. `notify.py`

**Responsibilities**

- Sends email notifications on failed sync attempts
- Alerts on reconciliation mismatches
- Notifies when manual intervention is needed
- Can be triggered by any component

**Workflow Actions**

- [ ] Send notifications for failed sync attempts (#PR_NUMBER)
- [ ] Alert on reconciliation mismatches (#PR_NUMBER)
- [ ] Provide manual override notifications (#PR_NUMBER)

### G. `metrics.py`

**Responsibilities**

- Collects statistics: number of open/closed issues, time-to-close, reconciliation runs, sync failures
- Outputs logs and optionally posts metrics to a dashboard or Slack

**Workflow Actions**

- [ ] Gather metrics on open and closed issues (#PR_NUMBER)
- [ ] Record time-to-close and reconciliation runs (#PR_NUMBER)
- [ ] Post metrics to a dashboard or Slack (#PR_NUMBER)

### H. `web_ui.py`

**Responsibilities**

- Provides a minimal web interface for maintainers
- Allows manual triggering of sync or reconciliation
- Displays logs and metrics
- Lets maintainers edit mappings or resolve errors

**Workflow Actions**

- [ ] Provide routes `/logs`, `/metrics`, `/sync`, and `/reconcile` (#PR_NUMBER)
- [ ] Expose manual triggers for sync and reconciliation (#PR_NUMBER)
- [ ] Present logs and metrics to maintainers (#PR_NUMBER)
- [ ] Allow editing of mappings or resolving errors (#PR_NUMBER)

### I. `config.yaml`

**Responsibilities**

- Stores repository info and auth tokens
- Tracks master checklist issue number and checklist file path
- Holds notification settings and mapping strategy

**Workflow Actions**

- [ ] Store repository information and tokens securely (#PR_NUMBER)
- [ ] Track the master checklist issue number (#PR_NUMBER)
- [ ] Define the checklist file path and notification settings (#PR_NUMBER)
- [ ] Choose a mapping/matching strategy (#PR_NUMBER)

## Key Functions and Classes

- [ ] Implement `create_issues_from_checklist()` in `generate_issues.py` (#PR_NUMBER)
- [ ] Implement `update_mapping()` and `gather_metrics()` in metrics and checklist utilities (#PR_NUMBER)
- [ ] Implement `sync_checklist_with_closed_issues()` in `sync_checklist.py` (#PR_NUMBER)
- [ ] Implement `reconcile_checklist_and_issues()` in `reconcile.py` (#PR_NUMBER)
- [ ] Implement `send_notification()` in `notify.py` (#PR_NUMBER)
- [ ] Implement `/logs`, `/metrics`, `/sync`, and `/reconcile` routes in `web_ui.py` (#PR_NUMBER)
- [ ] Implement `load_config()` and `get_token()` for `config.yaml` and environment variables (#PR_NUMBER)

## Deployment and Execution

- [ ] Manually run `generate_issues.py` when the checklist changes (#PR_NUMBER)
- [ ] Run `webhook_server.py` continuously via cloud, container, or serverless platform (#PR_NUMBER)
- [ ] Schedule `reconcile.py` nightly via cron, GitHub Actions, or another scheduler (#PR_NUMBER)
- [ ] Invoke `metrics.py`, `notify.py`, and `web_ui.py` from sync and reconciliation flows as needed (#PR_NUMBER)

## Conventions and Best Practices

- [ ] Format checklist items as `- [ ] Description of test (closes #123)` (#PR_NUMBER)
- [ ] Ensure issue titles map unambiguously to checklist items (#PR_NUMBER)
- [ ] Reference issues in PR bodies using "Closes #123" (#PR_NUMBER)
- [ ] Log script operations and handle API errors with retries or clear messages (#PR_NUMBER)

## Error Recovery

- [ ] Check for duplicate issues before creation (#PR_NUMBER)
- [ ] Rerun sync scripts to fix checklist desynchronization (#PR_NUMBER)
- [ ] Allow manual overrides with recalculation based on current states (#PR_NUMBER)

## Tools and Libraries

- [ ] Install and configure `PyGithub` for API calls (#PR_NUMBER)
- [ ] Use `python-markdown` or regex for checklist parsing (#PR_NUMBER)

## Security and Maintenance

- [ ] Store tokens and credentials in secrets or environment variables (#PR_NUMBER)
- [ ] Validate webhook authenticity (#PR_NUMBER)
- [ ] Log and handle errors in all modules (#PR_NUMBER)
- [ ] Provide an admin web UI for manual intervention (#PR_NUMBER)

## Workflow Summary

| Step | Who/What Runs It | Outcome |
| --- | --- | --- |
| Checklist → Issues | Python script/manual | Each test item has a tracked GitHub issue |
| PR → closes Issue | Developer/PR reviewer | PR merges auto-close related test issues |
| Issue/PR → checklist | Script via webhook | Master checklist is updated to match reality |
| Reconciliation/Notify | Scheduled job or error | Manual/auto fix for any desync or error |
| Retry/metrics/mapping | All scripts | Reliable, observable, flexible automation |
| Web UI | Maintainers | Low-friction oversight, manual triggers |

This combined reference links architectural components with their operational workflow and actionable steps.
