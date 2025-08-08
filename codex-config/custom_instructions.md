# Codex Custom Settings

## 1. Prompt Refinement & Task Decomposition
- Always check if a prompt needs clarification; if so, propose a concise revision or split into subtasks.
- If clear, skip refinement and list tasks directly:
  - Imperative verbs, short & independent, with relevant context.
- Use **Checkpoints & Summaries** between steps:
  - Summarize outputs, assumptions, variable states.
  - Label sections (e.g., `## ✅ Task 1 Summary`) and prepend before next task.
- See full decomposition rules in `./codex-config/guides/Decomposition-Guide.md`.

## 2. Testing & Linting
- Run all tests and linters; do not skip without explicit approval.
- When writing tests only, do not modify source code.
- See detailed testing rules in `./codex-config/guides/Python-Guide.md`.

## 3. Commit Messages
- Follow [Conventional Commits](https://www.conventionalcommits.org/) (e.g., `feat(parser): …`).

## 4. Code Review & Verification
- For each user requirement:
  1. Confirm correct implementation.
  2. Identify missing/incomplete items.
  3. Propose precise corrections.
- Summarize overall status.

## 5. Dependency Management
- Before task execution, parse `AGENTS.md` and any referenced files (e.g., `requirements.txt`).
- Install missing dependencies idempotently.
- Report which packages were installed vs. already present.
- See full dependency workflow in `./codex-config/guides/Dependency-Guide.md`.
