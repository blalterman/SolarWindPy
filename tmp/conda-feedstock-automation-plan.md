# Conda Feedstock Update Automation Plan

## Overview
Implement comprehensive automation for conda-forge feedstock updates to eliminate manual intervention and reduce release overhead.

## Plan Structure

### Phase 0: Overview Issue
**Objective**: Create comprehensive plan with value propositions framework
- Complete value propositions with 75-82% token optimization
- 47-70 hour total development investment, 12-18 month ROI
- 92/100 SolarWindPy alignment score
- Links to all 5 implementation phases
- Comprehensive success metrics

### Phase 1: Foundation & Documentation
**Estimated Time**: 6-10 hours  
**Objective**: Establish foundation for conda feedstock automation

**Deliverables**:
- `docs/conda-feedstock-update.md` - Step-by-step manual update process
- `scripts/prepare_conda_pr.sh` - Helper script for SHA256 calculation
- `docs/conda-forge-best-practices.md` - Research on automation patterns

**Implementation Approaches**:
1. **Minimal Documentation** (Recommended)
   - Quick implementation (2-3 hours)
   - Essential manual process coverage
   - Foundation for automation
   
2. **Comprehensive Guide**
   - Complete edge case coverage
   - Better for new contributors
   - Longer implementation (8-12 hours)

### Phase 2: Automation Scripts
**Estimated Time**: 12-18 hours  
**Objective**: Develop Python automation script for feedstock updates

**Deliverables**:
- `scripts/update_conda_feedstock.py` - Main automation script
- `scripts/conda_config.py` - Configuration management
- `tests/scripts/test_conda_automation.py` - Test suite with >90% coverage

**Core Functionality**:
```python
class CondaFeedstockUpdater:
    def validate_pypi_release(self):
        # Poll PyPI with exponential backoff
        
    def calculate_sha256(self):
        # Download and hash tarball
        
    def create_tracking_issue(self):
        # Create GitHub issue with template
        
    def generate_pr_template(self):
        # Create PR description for manual submission
```

**Implementation Approaches**:
1. **GitHub Issues Integration** (Recommended)
   - Clear audit trail via issues
   - Maintainer control over PR submission
   - Balances automation with oversight
   
2. **Full Automation with Fork Management**
   - Complete zero-touch automation
   - More complex permissions required
   - Higher risk of automated mistakes

### Phase 3: CI/CD Integration
**Estimated Time**: 11-16 hours  
**Objective**: Integrate automation into GitHub Actions pipeline

**Deliverables**:
- Updated `.github/workflows/publish.yml`
- Conda update job after PyPI publish
- RC filtering logic
- PyPI availability validation

**Key Features**:
```yaml
jobs:
  update-conda-feedstock:
    needs: build-and-publish
    if: success() && !contains(github.ref, 'rc')
    steps:
      - name: Wait for PyPI availability
        run: python scripts/wait_for_pypi.py ${{ github.ref_name }}
        
      - name: Update Conda Feedstock
        run: python scripts/update_conda_feedstock.py ${{ github.ref_name }}
        
      - name: Create tracking issue
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python scripts/update_conda_feedstock.py \
            --version ${{ github.ref_name }} \
            --create-issue
```

**Implementation Approaches**:
1. **Integrated into Publish Workflow** (Recommended)
   - Single workflow to maintain
   - Clear dependency chain
   - Guaranteed execution order
   
2. **Separate Workflow File**
   - Clean separation of concerns
   - Easy to disable/enable
   - Potential race conditions

### Phase 4: Testing & Validation
**Estimated Time**: 10-15 hours  
**Objective**: Comprehensive testing framework

**Test Scenarios**:
- Patch release (v0.1.5)
- Minor release (v0.2.0)  
- RC release (v0.1.5-rc1) - should NOT trigger
- Failed PyPI upload recovery
- Network timeout handling

**Validation Checklist**:
- [ ] RC releases properly filtered (100% accuracy)
- [ ] SHA256 calculations match PyPI
- [ ] PyPI availability check works
- [ ] GitHub issue creation successful
- [ ] Error handling for all failure modes
- [ ] Performance <10 minutes PyPI to conda PR

### Phase 5: Closeout
**Estimated Time**: 8-13 hours  
**Objective**: Decision capture and maintenance documentation

**Deliverables**:
- 85% implementation decision point
- Lessons learned documentation
- Maintenance runbook
- Performance metrics analysis
- Future improvements roadmap

## Technical Specifications

### RC Filtering Logic
```yaml
# In GitHub Actions
if: !contains(github.ref, 'rc')

# In Python
from packaging import version
v = version.parse(tag_name)
if not v.is_prerelease:
    # Trigger conda update
```

### PyPI Availability Check
```python
def wait_for_pypi(version, timeout=300):
    start = time.time()
    while time.time() - start < timeout:
        response = requests.get(f"https://pypi.org/pypi/solarwindpy/{version}/json")
        if response.status_code == 200:
            return True
        time.sleep(30)
    return False
```

### SHA256 Calculation
```python
def calculate_sha256(version):
    url = f"https://pypi.org/packages/source/s/solarwindpy/solarwindpy-{version}.tar.gz"
    response = requests.get(url)
    return hashlib.sha256(response.content).hexdigest()
```

### Configuration Structure
```python
# conda_config.py
TIMEOUTS = {
    'pypi_check': 30,      # seconds
    'download': 300,       # seconds  
    'github_api': 10       # seconds
}

RETRY_CONFIG = {
    'max_attempts': 3,
    'backoff_factor': 2,
    'base_delay': 1        # seconds
}
```

## Manual Fallback Process

Even with automation, maintain manual process:

1. **Verify PyPI Release**
   ```bash
   curl -s https://pypi.org/pypi/solarwindpy/json | jq '.info.version'
   ```

2. **Calculate SHA256**
   ```bash
   VERSION=0.1.5
   curl -sL https://pypi.org/packages/source/s/solarwindpy/solarwindpy-${VERSION}.tar.gz | sha256sum
   ```

3. **Update Feedstock**
   - Fork conda-forge/solarwindpy-feedstock
   - Update `recipe/meta.yaml` with version and SHA256
   - Create PR with checklist

4. **Monitor PR**
   - Wait for conda-forge bot checks
   - Address any linter issues
   - Merge when approved

## Success Criteria

### Automation Metrics
- **Reliability**: >95% successful automated updates
- **Speed**: <10 minutes from PyPI to conda PR
- **RC Filtering**: 100% accuracy
- **Error Rate**: <5% false positives

### Development Metrics  
- **Code Coverage**: >90% for automation scripts
- **Documentation**: Complete for both auto and manual
- **Testing**: All scenarios validated
- **Maintenance**: <2 hours annually

## Risk Mitigation

### Technical Risks
1. **conda-forge API Changes** (Medium)
   - Mitigation: Version API calls, comprehensive error handling
   - Fallback: Manual update process always available

2. **PyPI Availability Delays** (Low)
   - Mitigation: Polling with exponential backoff
   - Fallback: Manual trigger after confirmation

3. **GitHub Actions Rate Limits** (Low)
   - Mitigation: Authenticated requests, retry logic
   - Fallback: Local script execution

### Project Risks
1. **Release Pipeline Disruption** (Medium)
   - Mitigation: Phased rollout, non-blocking automation
   - Rollback: Disable automation, revert to manual

2. **Maintenance Burden** (Low)
   - Mitigation: Comprehensive documentation, modular design
   - Planning: Annual review cycle

## Implementation Commands

### Creating GitHub Issues (Correct Way)
```bash
# Step 1: Create overview issue with proper labels
.claude/scripts/gh-plan-create.sh "Conda Feedstock Update Automation" -p high -d infrastructure

# Step 2: Create phase issues linked to overview
.claude/scripts/gh-plan-phases.sh [overview-issue-number]
# Then interactively add 5 phases

# Step 3: Monitor plan status
.claude/scripts/gh-plan-status.sh
```

### Manual Issue Creation (Fallback)
```bash
# Create with template and labels
gh issue create \
  --template plan-overview.yml \
  --label "plan:overview,priority:high,status:planning,domain:infrastructure" \
  --title "[Plan Overview]: Conda Feedstock Update Automation"
```

## Files to Create/Modify

### New Files
1. `docs/conda-feedstock-update.md` - Manual process guide
2. `scripts/prepare_conda_pr.sh` - Helper script
3. `scripts/update_conda_feedstock.py` - Main automation
4. `scripts/conda_config.py` - Configuration
5. `scripts/wait_for_pypi.py` - PyPI availability checker
6. `tests/scripts/test_conda_automation.py` - Test suite

### Modified Files
1. `.github/workflows/publish.yml` - Add conda update job
2. `requirements-dev.txt` - Add automation dependencies

## Dependencies

### Python Packages
```python
# requirements-dev.txt additions
requests>=2.28.0        # PyPI API interaction
click>=8.0.0           # CLI interface
pyyaml>=6.0            # YAML manipulation
packaging>=21.0        # Version parsing
```

### GitHub Secrets
- `GITHUB_TOKEN` - For creating issues (already available)
- `CONDA_FORGE_TOKEN` - Optional for future PR automation

## Timeline

- **Week 1**: Foundation & Documentation (Phase 1)
- **Week 2-3**: Automation Development (Phase 2)
- **Week 4**: CI/CD Integration (Phase 3)
- **Week 5**: Testing & Validation (Phase 4)
- **Week 6**: Closeout & Documentation (Phase 5)

Total: 6 weeks with proper testing cycles

## Notes

- Keep automation simple and maintainable
- Prioritize reliability over speed
- Always maintain manual fallback
- Document all automation decisions
- Test with actual releases before full deployment