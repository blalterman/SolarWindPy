# Plan: Private Development Repo + Public Release Repo

## Summary

Create a private development repo (`blalterman/SolarWindPy-dev`) as the primary working
environment, while keeping the existing public repo (`blalterman/SolarWindPy`) as-is for
releases. All current public content stays public. The private repo is a **superset** of
the public repo, adding research code, private data, and experimental features.

## Architecture

```
GitHub:
  blalterman/SolarWindPy      (public, existing)  <- Release repo
  blalterman/SolarWindPy-dev   (private, new)      <- Development repo

Local:
  ~/observatories/code/
  |-- SolarWindPy/             -> public repo clone  (releases only)
  +-- SolarWindPy-dev/         -> private repo clone (daily work)
```

**Relationship**: Private repo is a superset. It contains everything the public repo has,
plus additional private directories. Development happens in private; curated releases flow
to public via an export script.

## Evidence & Justification

### Why two repos instead of branch-based separation?
- Git has no per-remote file filtering. Pushing `master` to two remotes sends ALL files.
- Branch-based approaches (e.g., `develop` with private content, `master` without) require
  careful merge hygiene that is error-prone for a solo developer.
- Two repos with an export script is the standard pattern used by Linux, Android, and
  corporate open-source projects for private-dev -> public-release workflows.
- Zero risk of accidental private content leakage.

### Why copy history rather than start fresh?
- The private repo should have full commit history for `git blame`, bisect, and reference.
- Starting from a bare clone means both repos share the same initial history (1,383 commits).
- setuptools_scm works identically in both (same tags, same version derivation).

### Why keep the public repo unchanged?
- User's explicit requirement: "Everything that currently is public can stay public."
- No external link breakage (PyPI, conda-forge, ReadTheDocs, 4 stars, 3 forks).
- No CI/CD reconfiguration needed for the public repo.
- `.claude/`, `plans/`, `paper/` remain public as they already are.

## Phase 1: Create Private Repository (~15 min)

### Step 1.1: Create private repo on GitHub
```bash
gh repo create blalterman/SolarWindPy-dev \
  --private \
  --description "Private development repository for SolarWindPy"
```

### Step 1.2: Push full history to private repo
```bash
# Clone the public repo as a bare mirror
git clone --bare git@github.com:blalterman/SolarWindPy.git /tmp/swp-mirror

# Push everything to the new private repo
cd /tmp/swp-mirror
git push --mirror git@github.com:blalterman/SolarWindPy-dev.git

# Cleanup
rm -rf /tmp/swp-mirror
```

### Step 1.3: Clone private repo locally
```bash
cd ~/observatories/code
git clone git@github.com:blalterman/SolarWindPy-dev.git SolarWindPy-dev
```

### Step 1.4: Add public repo as a remote in the private clone
```bash
cd ~/observatories/code/SolarWindPy-dev
git remote add public git@github.com:blalterman/SolarWindPy.git
git fetch public
```

**Verification**: `git remote -v` shows both `origin` (private) and `public` (public).

## Phase 2: Configure Private Repo Structure (~30 min)

### Step 2.1: Add private-only directories
```bash
cd ~/observatories/code/SolarWindPy-dev
mkdir -p research/{notebooks,analysis,experiments}
mkdir -p private/{data,configs}
```

### Step 2.2: Create private content manifest
Create `.private-manifest` (tracked in private repo, excluded from export):
```
# Paths that exist only in the private repo.
# The export script excludes these when syncing to public.
research/
private/
.private-manifest
```

### Step 2.3: Update private repo .gitignore
Add to `.gitignore`:
```
# Private data files (never commit even to private repo)
private/data/**/*.h5
private/data/**/*.hdf5
private/configs/secrets.*
```

### Step 2.4: Initial commit of private structure
```bash
git add research/ private/ .private-manifest
git commit -m "feat: add private research and data directories

Establishes private-only directories for research code, analysis
notebooks, experimental features, and private data/configs.
These directories are excluded from public repo syncs.

Co-Authored-By: Claude <noreply@anthropic.com>"
git push origin master
```

## Phase 3: Create Export Script (~1 hour)

### Step 3.1: Create `scripts/export-to-public.sh` in private repo

This script:
1. Reads `.private-manifest` for paths to exclude
2. Uses `rsync` to sync everything else to the local public clone
3. Commits and optionally tags in the public clone
4. Pushes to the public GitHub repo

```bash
#!/bin/bash
# export-to-public.sh -- Sync public-safe content from private to public repo
#
# Usage:
#   ./scripts/export-to-public.sh              # Sync without tagging
#   ./scripts/export-to-public.sh v0.4.0       # Sync and tag for release
#   ./scripts/export-to-public.sh --dry-run    # Show what would be synced

set -euo pipefail

PRIVATE_REPO="$(cd "$(dirname "$0")/.." && pwd)"
PUBLIC_REPO="${PRIVATE_REPO}/../SolarWindPy"
MANIFEST="${PRIVATE_REPO}/.private-manifest"

# Parse args
DRY_RUN=false
VERSION_TAG=""
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        v*) VERSION_TAG="$arg" ;;
        *) echo "Unknown arg: $arg"; exit 1 ;;
    esac
done

# Validate
[ -d "$PUBLIC_REPO/.git" ] || { echo "Error: Public repo not found at $PUBLIC_REPO"; exit 1; }
[ -f "$MANIFEST" ] || { echo "Error: .private-manifest not found"; exit 1; }

# Build rsync exclude list from manifest
EXCLUDES=()
while IFS= read -r line; do
    [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
    EXCLUDES+=(--exclude="$line")
done < "$MANIFEST"

# Always exclude git directory and build artifacts
EXCLUDES+=(--exclude=".git" --exclude="dist/" --exclude="*.egg-info/"
           --exclude="htmlcov/" --exclude="__pycache__/" --exclude=".pytest_cache/"
           --exclude=".eggs/" --exclude="build/" --exclude="tmp/"
           --exclude="staged-recipes*/" --exclude="*.pyc")

echo "=== Export to Public Repo ==="
echo "Private: $PRIVATE_REPO"
echo "Public:  $PUBLIC_REPO"
echo "Excludes: ${EXCLUDES[*]}"

if [ "$DRY_RUN" = true ]; then
    echo "--- DRY RUN ---"
    rsync -avn --delete "${EXCLUDES[@]}" "$PRIVATE_REPO/" "$PUBLIC_REPO/"
    exit 0
fi

# Sync
rsync -av --delete "${EXCLUDES[@]}" "$PRIVATE_REPO/" "$PUBLIC_REPO/"

# Commit changes in public repo
cd "$PUBLIC_REPO"
if [ -n "$(git status --porcelain)" ]; then
    git add -A
    git commit -m "$(cat <<EOF
release: sync from development repository

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
    echo "Committed changes to public repo"
else
    echo "No changes to commit"
fi

# Tag if requested
if [ -n "$VERSION_TAG" ]; then
    git tag -a "$VERSION_TAG" -m "SolarWindPy $VERSION_TAG"
    echo "Tagged as $VERSION_TAG"
    echo ""
    echo "Ready to push. Run:"
    echo "  cd $PUBLIC_REPO && git push origin master --tags"
fi

echo "=== Export complete ==="
```

### Step 3.2: Make executable and commit
```bash
chmod +x scripts/export-to-public.sh
git add scripts/export-to-public.sh
git commit -m "feat(scripts): add export-to-public sync script

Provides one-command sync from private dev repo to public release
repo, reading .private-manifest for paths to exclude.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

## Phase 4: CI/CD Configuration (~30 min)

### Private repo CI/CD
No file changes needed. Existing CI/CD workflows work as-is because the private
repo is a superset of the public repo (same structure, same files, same tests).

### Public repo CI/CD stays as-is
The `publish.yml` workflow already triggers on `v*` tags and publishes to PyPI.
The `docs.yml` workflow already builds documentation. No changes needed.

### Optional: Disable publishing from private repo
To prevent accidental publishing from the wrong repo, remove the `PYPI_API_TOKEN`
secret from the private repo's GitHub settings. The private repo's `publish.yml`
would fail on tag push (harmless), ensuring you never accidentally publish from
the wrong source.

**Action**: GitHub Settings (no file changes) -> Private repo -> Settings -> Secrets -> Remove `PYPI_API_TOKEN`

## Phase 5: Development Workflow (Reference)

### Daily development
```bash
cd ~/observatories/code/SolarWindPy-dev    # Work in private repo
git checkout -b feature/my-feature          # Feature branch
# ... develop, test, commit ...
git push origin feature/my-feature          # Push to private
# Create PR on private repo (for your own tracking)
```

### Research & experiments
```bash
cd ~/observatories/code/SolarWindPy-dev
# Research code goes in research/ -- never synced to public
vim research/notebooks/ion_temperature_analysis.ipynb
vim research/experiments/new_fitting_approach.py
git add research/
git commit -m "research: preliminary ion temperature analysis"
git push origin master
```

### Release workflow
```bash
cd ~/observatories/code/SolarWindPy-dev
# 1. Ensure master is clean and tests pass
pytest -q
# 2. Update CHANGELOG.md
# 3. Dry-run the export
./scripts/export-to-public.sh --dry-run
# 4. Export and tag
./scripts/export-to-public.sh v0.4.0
# 5. Push to public
cd ~/observatories/code/SolarWindPy
git push origin master --tags
# 6. publish.yml fires -> PyPI -> conda-forge
```

### Pulling community contributions (if any)
```bash
cd ~/observatories/code/SolarWindPy-dev
git fetch public
git merge public/master    # Pull any external PRs into private
```

## Phase 6: Keeping Repos in Sync (Reference)

### When to sync
- **Always sync before release**: Run export script before tagging
- **Don't sync on every commit**: The public repo receives batch updates at release time
- **Pull from public after external PRs**: If someone contributes to the public repo

### Conflict prevention
- All development happens in private repo -> public is never ahead of private
  (except for external contributions, which are rare for a solo project)
- The export script uses `rsync --delete`, so public repo always matches the
  private repo's public-safe content exactly

### Private content safety
- `.private-manifest` lists all private-only paths
- `rsync --delete` with exclusions ensures private paths never appear in public
- No complex git gymnastics needed -- it's just a file sync

## Risk Analysis

| Risk | Severity | Probability | Mitigation |
|------|----------|-------------|------------|
| Forget to sync before release | Medium | Medium | Add to CHANGELOG/release checklist |
| Private content leaks to public | High | Very Low | `.private-manifest` + `rsync` excludes |
| setuptools_scm version mismatch | Medium | Low | Both repos have same tags; verify with `python -m setuptools_scm` |
| Divergent histories after external PR | Low | Low | `git fetch public && git merge public/master` |
| Accidental PyPI publish from private | Medium | Low | Remove PYPI_API_TOKEN from private repo secrets |

## Cost Analysis (GitHub Organization Question)

If an org is desired later, these are the costs:
- **Free tier**: Unlimited public + private repos, 2,000 CI min/month. No branch protection on private repos.
- **Team**: $4/user/month. Adds branch protection, required reviewers.
- **Recommendation**: Not needed now. Revisit if the project grows to multiple contributors.

## Verification Checklist

After implementation, verify:
- [ ] `git remote -v` in private clone shows both `origin` and `public`
- [ ] `pytest -q` passes in private repo
- [ ] `./scripts/export-to-public.sh --dry-run` shows correct file list
- [ ] Private-only directories (`research/`, `private/`) do NOT appear in dry-run output
- [ ] `python -m setuptools_scm` reports correct version in both repos
- [ ] `.claude/` infrastructure works normally in private repo
- [ ] Public repo CI passes after first sync

## Critical Files

- `SolarWindPy/.gitignore` -- needs private-data patterns (in private clone only)
- `SolarWindPy/pyproject.toml` -- URLs stay as-is (public repo)
- `SolarWindPy/.pre-commit-config.yaml` -- works in both repos unchanged
- New: `scripts/export-to-public.sh` -- the sync script (private repo only)
- New: `.private-manifest` -- private content manifest (private repo only)
