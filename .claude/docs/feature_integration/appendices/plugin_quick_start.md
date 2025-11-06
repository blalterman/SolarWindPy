# Plugin Quick Start Guide

[← Back to Index](../INDEX.md)

---

## Create Your First SolarWindPy Plugin in 30 Minutes

This guide walks you through creating a minimal working plugin with one command and one skill.

---

### Step 1: Create Plugin Structure (5 minutes)

```bash
# Create plugin directory
mkdir -p solarwindpy-devtools/.claude-plugin
mkdir -p solarwindpy-devtools/commands
mkdir -p solarwindpy-devtools/skills/physics-validator
```

---

### Step 2: Create Plugin Manifest (5 minutes)

```bash
cat > solarwindpy-devtools/.claude-plugin/plugin.json <<'EOF'
{
  "name": "solarwindpy-devtools",
  "description": "Solar wind physics development toolkit for Claude Code",
  "version": "0.1.0",
  "author": {
    "name": "Your Name",
    "url": "https://github.com/blalterman/SolarWindPy"
  },
  "keywords": ["solar-wind", "heliophysics", "physics"]
}
EOF
```

---

### Step 3: Add Test Command (10 minutes)

```bash
cat > solarwindpy-devtools/commands/test.md <<'EOF'
---
description: Run tests with smart mode selection (changed, physics, fast, all, coverage)
allowed-tools: [Bash]
---

Run tests using the test-runner.sh hook with intelligent mode selection.

Arguments:
- `$1`: Mode (changed|physics|fast|all|coverage) - default: changed

Execute:
!.claude/hooks/test-runner.sh --${1:-changed}

Modes:
- **changed**: Test only modified files (fastest)
- **physics**: Physics validation tests only
- **fast**: Quick smoke test run
- **all**: Complete test suite
- **coverage**: Full suite with detailed coverage report

After tests complete:
- Report pass/fail status
- Show any test failures with details
- Suggest fixes if failures detected
EOF
```

---

### Step 4: Add Physics Validator Skill (10 minutes)

```bash
cat > solarwindpy-devtools/skills/physics-validator/SKILL.md <<'EOF'
---
name: physics-validator
description: Automatically validates solar wind physics correctness (thermal speed mw²=2kT, SI units m/s m⁻³ K T, NaN for missing data, positive densities/temperatures) in Python code when user requests physics validation, unit checking, or mentions thermal speed calculations.
allowed-tools: [Bash, Read, Grep]
---

# Physics Validator Skill

## Activation Triggers
- User mentions "validate physics", "check units", "thermal speed"
- User requests physics correctness review
- User asks about SI unit compliance
- Code changes involve physics calculations

## Validation Checklist

### 1. Thermal Speed Formula
**Critical:** Verify `mw² = 2kT` (NOT 3kT)
- Search for thermal_speed functions
- Check for incorrect factor (1.5, 3)
- Ensure correct formula: `sqrt(2 * k_B * T / m)`

### 2. SI Units
- Velocities: m/s (not km/s unless explicitly converted)
- Densities: m⁻³ (not cm⁻³)
- Temperatures: K (Kelvin)
- Magnetic field: T (Tesla)

### 3. Missing Data Handling
- Use `np.nan` for missing data
- Never use sentinel values (0, -999, -1)

### 4. Physical Constraints
- Densities: Must be ≥ 0
- Temperatures: Must be > 0
- Speeds: Must be ≥ 0

## Execution

Run physics validation script:
```bash
python .claude/hooks/physics-validation.py ${file_path}
```

Report findings with file:line references.
EOF
```

---

### Step 5: Create Local Marketplace (5 minutes)

```bash
mkdir -p solarwindpy-marketplace/.claude-plugin

cat > solarwindpy-marketplace/.claude-plugin/marketplace.json <<'EOF'
{
  "name": "solarwindpy-marketplace",
  "description": "SolarWindPy development tools marketplace",
  "owner": {
    "name": "SolarWindPy Team",
    "url": "https://github.com/blalterman/SolarWindPy"
  },
  "plugins": [
    {
      "name": "solarwindpy-devtools",
      "source": "./solarwindpy-devtools",
      "description": "Core solar wind physics development toolkit"
    }
  ]
}
EOF
```

---

### Step 6: Test Plugin Installation (5 minutes)

```bash
# In Claude Code, add marketplace
/plugin marketplace add ./solarwindpy-marketplace

# Install plugin
/plugin install solarwindpy-devtools

# Test slash command
/test changed

# Test skill (mention physics in prompt)
# "Can you validate the physics in solarwindpy/core/ion.py?"
```

---

## Verification Checklist

- [ ] Plugin structure created correctly
- [ ] `plugin.json` valid JSON
- [ ] Slash command executes successfully
- [ ] Skill activates on physics mention
- [ ] Marketplace accessible via `/plugin marketplace list`
- [ ] Plugin appears in `/plugin list`

---

## Common Issues & Solutions

### Issue: Plugin not found after marketplace add
**Solution:** Check marketplace.json path in "source" field (relative to marketplace dir)

### Issue: Slash command doesn't execute
**Solution:** Verify command frontmatter has valid YAML and bash command has `!` prefix

### Issue: Skill doesn't activate
**Solution:** Check description includes clear trigger words, test with explicit mention

### Issue: Permission denied on bash script
**Solution:** Ensure `.claude/hooks/test-runner.sh` exists and is executable

---

## Next Steps

1. **Add More Commands:** Copy pattern from `/test` to create `/coverage`, `/physics`, `/review`
2. **Add More Skills:** Create `multiindex-architect`, `test-generator`, `plan-executor`
3. **Add Agents:** Package subagents in `plugin-name/agents/`
4. **Version & Distribute:** Bump version, push to GitHub marketplace

---

## Full Plugin Structure Reference

```
solarwindpy-devtools/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   ├── test.md
│   ├── coverage.md
│   ├── physics.md
│   ├── review.md
│   ├── refactor.md
│   ├── plan-create.md
│   ├── plan-phases.md
│   ├── plan-status.md
│   ├── commit.md
│   └── branch.md
├── skills/
│   ├── physics-validator/
│   │   └── SKILL.md
│   ├── multiindex-architect/
│   │   └── SKILL.md
│   ├── test-generator/
│   │   └── SKILL.md
│   └── plan-executor/
│       └── SKILL.md
├── agents/
│   ├── physics-validator.md
│   ├── dataframe-architect.md
│   ├── plotting-engineer.md
│   └── fit-function-specialist.md
├── hooks/
│   └── hooks.json
└── README.md
```

---

## Resources

- **Official Docs:** https://docs.claude.com/en/docs/claude-code/plugins
- **Full Guide:** [Plugin Packaging](../08_plugin_packaging.md)
- **Integration Checklist:** [Integration Checklist](./integration_checklist.md)
- **Findings Report:** `../../tmp/plugin-ecosystem-integration-findings.md`

---

**Last Updated:** 2025-10-31
**Document Version:** 1.1
**Plugin Ecosystem:** Official Anthropic Feature (Oct 2025)
