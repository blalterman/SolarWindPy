#!/bin/bash
# Spent-When: PERMANENT(the pre-commit hooks stop running Python from the solarwindpy conda env)
# Supersedes: none
#
# Run a command inside the solarwindpy conda env.
#
# Pre-commit hooks with `language: system` take python and pytest from PATH.
# In a shell that has not activated the env, PATH resolves the base conda
# install, whose pandas predates the version pyproject.toml requires, so the
# hooks test against the wrong dependencies. This wrapper runs its arguments
# in the env when it exists and is not already active; elsewhere (CI, other
# machines) it runs them unchanged.

set -e

if [[ "${CONDA_DEFAULT_ENV:-}" != "solarwindpy" ]] \
    && command -v conda > /dev/null 2>&1 \
    && conda env list | grep -qE '^solarwindpy[[:space:]]'; then
    exec conda run --no-capture-output -n solarwindpy "$@"
fi

exec "$@"
