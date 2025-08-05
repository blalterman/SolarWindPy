# Dependency Management Guide

1. Parse `AGENTS.md` for direct listings.
2. Identify referenced files (`requirements.txt`, `environment.yml`).
3. Aggregate unique dependencies.
4. For each:
   - Check if installed.
   - If missing, install via appropriate manager (e.g., `pip install`).
5. Ensure idempotence; log installed vs. existing.
6. On failure, halt and report diagnostics.
