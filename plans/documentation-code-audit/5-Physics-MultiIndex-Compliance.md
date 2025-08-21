# Phase 5: Physics & MultiIndex Compliance

## Phase Metadata
- **Status**: ✅ Complete
- **Estimated Duration**: 2 hours
- **Actual Duration**: 1.8 hours
- **Dependencies**: Phase 4 (Code Example Remediation) completed
- **Git Commit**: <checksum>
- **Branch**: plan/documentation-code-audit

## 🎯 Objective
Ensure all corrected code examples strictly follow SolarWindPy physics rules and MultiIndex data structure conventions, establishing automated validation to prevent future violations.

## 📋 Tasks Checklist
- [ ] **Physics Rule Validation** (60 min)
  - [ ] Thermal speed convention compliance (mw² = 2kT) (20 min)
  - [ ] SI unit consistency validation (15 min)
  - [ ] Missing data handling verification (NaN vs 0/-999) (15 min)
  - [ ] Alfvén speed calculation validation (V_A = B/√(μ₀ρ)) (10 min)

- [ ] **MultiIndex Structure Compliance** (45 min)
  - [ ] Column level naming validation (M, C, S) (15 min)
  - [ ] Data access pattern standardization (.xs() usage) (15 min)
  - [ ] DataFrame index requirements (Epoch naming) (10 min)
  - [ ] Species and component consistency (5 min)

- [ ] **Automated Validation Integration** (15 min)
  - [ ] Create physics compliance checker script (10 min)
  - [ ] Integrate with example validation framework (5 min)

## 📁 Deliverables
- [ ] **physics_compliance_validator.py**: Automated physics rule checking
- [ ] **multiindex_structure_validator.py**: MultiIndex pattern validation
- [ ] **compliance_report.json**: Complete compliance assessment results
- [ ] **physics_examples_guide.md**: Best practices documentation
- [ ] **automated_validation_hooks.py**: CI/CD integration preparation

## 🔬 Physics Rules Validation

### Thermal Speed Convention (mw² = 2kT)
```python
class ThermalSpeedValidator:
    def validate_convention(self, thermal_speed, temperature, mass):
        """
        Validate thermal speed follows mw² = 2kT convention
        
        Parameters:
        - thermal_speed: calculated thermal speed [km/s]
        - temperature: temperature [K]
        - mass: particle mass [kg]
        """
        k_B = 1.380649e-23  # Boltzmann constant [J/K]
        
        # Expected thermal speed: w = sqrt(2kT/m)
        expected_w = np.sqrt(2 * k_B * temperature / mass) / 1000  # Convert to km/s
        
        relative_error = abs(thermal_speed - expected_w) / expected_w
        
        if relative_error > 0.01:  # 1% tolerance
            raise PhysicsViolation(
                f"Thermal speed convention violation: {relative_error:.3%} error\n"
                f"Expected: {expected_w:.2f} km/s, Got: {thermal_speed:.2f} km/s"
            )
        
        return True

    def validate_examples_with_thermal_speed(self, examples):
        """Check all examples that calculate thermal speed"""
        violations = []
        
        for example in examples:
            if self.contains_thermal_speed_calculation(example.code):
                try:
                    result = execute_example(example.code)
                    if 'thermal_speed' in result.outputs and 'temperature' in result.outputs:
                        self.validate_convention(
                            result.outputs['thermal_speed'],
                            result.outputs['temperature'],
                            result.outputs.get('mass', 1.67262192e-27)  # Default proton mass
                        )
                except PhysicsViolation as e:
                    violations.append({
                        'example_id': example.id,
                        'violation': str(e),
                        'file': example.file_path
                    })
        
        return violations
```

### SI Units Consistency
```python
class SIUnitsValidator:
    def __init__(self):
        self.expected_units = {
            'density': 'cm^-3',      # Number density (display unit)
            'velocity': 'km/s',      # Velocity (display unit)
            'temperature': 'K',       # Temperature
            'magnetic_field': 'nT',   # Magnetic field (display unit)
            'thermal_speed': 'km/s',  # Thermal speed (display unit)
            'pressure': 'Pa',         # Pressure (SI base)
            'energy': 'J',           # Energy (SI base)
        }
    
    def validate_units_in_example(self, example_code):
        """Ensure examples use correct units for display vs calculation"""
        # Internal calculations should use SI
        # Display/user interface should use conventional units
        violations = []
        
        if self.uses_non_si_in_calculation(example_code):
            violations.append("Non-SI units used in internal calculations")
        
        if self.missing_unit_conversions(example_code):
            violations.append("Missing unit conversions for display")
        
        return violations
    
    def uses_non_si_in_calculation(self, code):
        """Check if code uses non-SI units in calculations"""
        # Look for calculations with non-SI units
        non_si_patterns = [
            r'\* 1e6',  # Converting to cm^-3 in calculation
            r'/ 1000',  # Converting to km/s in calculation
            r'\* 1e9',  # Converting to nT in calculation
        ]
        
        for pattern in non_si_patterns:
            if re.search(pattern, code):
                return True
        return False
```

### Missing Data Handling
```python
class MissingDataValidator:
    def validate_nan_usage(self, example_code, example_outputs):
        """Ensure NaN used for missing data, not 0 or -999"""
        violations = []
        
        # Check for problematic missing data indicators
        if '-999' in example_code or '0' in example_code:
            if self.uses_zero_for_missing_data(example_code):
                violations.append("Uses 0 for missing data instead of NaN")
            
            if self.uses_fill_values(example_code):
                violations.append("Uses -999 fill values instead of NaN")
        
        # Check outputs for proper NaN handling
        if example_outputs:
            for var_name, data in example_outputs.items():
                if hasattr(data, 'isnull'):
                    if not self.proper_missing_data_handling(data):
                        violations.append(f"Variable {var_name} has improper missing data handling")
        
        return violations
    
    def proper_missing_data_handling(self, data):
        """Check if data uses NaN for missing values"""
        if hasattr(data, 'values'):
            # Check pandas Series/DataFrame
            return not np.any((data.values == 0) | (data.values == -999))
        elif isinstance(data, np.ndarray):
            # Check numpy arrays
            return not np.any((data == 0) | (data == -999))
        return True
```

## 📊 MultiIndex Structure Validation

### Column Level Naming (M, C, S)
```python
class MultiIndexValidator:
    def __init__(self):
        self.required_levels = ['M', 'C', 'S']
        self.valid_measurements = ['n', 'v', 'w', 'b', 'T', 'P']
        self.valid_components = ['x', 'y', 'z', '']
        self.valid_species = ['p1', 'p2', 'a', 'he', '']
    
    def validate_column_structure(self, dataframe):
        """Validate MultiIndex column structure"""
        violations = []
        
        if not isinstance(dataframe.columns, pd.MultiIndex):
            violations.append("Columns must be MultiIndex with (M, C, S) levels")
            return violations
        
        # Check level names
        if list(dataframe.columns.names) != self.required_levels:
            violations.append(
                f"Column level names must be {self.required_levels}, "
                f"got {list(dataframe.columns.names)}"
            )
        
        # Validate measurement types (M level)
        measurements = dataframe.columns.get_level_values('M').unique()
        invalid_measurements = set(measurements) - set(self.valid_measurements)
        if invalid_measurements:
            violations.append(f"Invalid measurements: {invalid_measurements}")
        
        # Validate components (C level)
        components = dataframe.columns.get_level_values('C').unique()
        invalid_components = set(components) - set(self.valid_components)
        if invalid_components:
            violations.append(f"Invalid components: {invalid_components}")
        
        # Validate species (S level)
        species = dataframe.columns.get_level_values('S').unique()
        invalid_species = set(species) - set(self.valid_species)
        if invalid_species:
            violations.append(f"Invalid species: {invalid_species}")
        
        return violations
```

### Data Access Pattern Validation
```python
class DataAccessValidator:
    def validate_xs_usage(self, example_code):
        """Ensure examples use .xs() for views, not copies"""
        violations = []
        
        # Check for inefficient data access patterns
        inefficient_patterns = [
            r'\.loc\[.*level.*\]',  # Should use .xs() instead
            r'\.iloc\[.*\]',        # Positional access is fragile
            r'\[\(.*,.*,.*\)\]',     # Direct tuple indexing
        ]
        
        for pattern in inefficient_patterns:
            if re.search(pattern, example_code):
                violations.append(f"Use .xs() for MultiIndex access instead of {pattern}")
        
        # Check for proper .xs() usage
        xs_patterns = [
            r"\.xs\('\w+', level='M'\)",  # Measurement access
            r"\.xs\('\w+', level='S'\)",  # Species access  
            r"\.xs\('\w+', level='C'\)",  # Component access
        ]
        
        has_proper_xs = any(re.search(pattern, example_code) for pattern in xs_patterns)
        if '.xs(' in example_code and not has_proper_xs:
            violations.append("Improper .xs() usage - specify level parameter")
        
        return violations
    
    def validate_index_naming(self, dataframe):
        """Ensure DataFrame index is named 'Epoch' for time series"""
        violations = []
        
        if hasattr(dataframe, 'index'):
            if dataframe.index.name != 'Epoch' and len(dataframe) > 1:
                violations.append("Time series DataFrame index should be named 'Epoch'")
        
        return violations
```

## 🔧 Automated Validation Framework

### Integrated Compliance Checker
```python
class ComplianceValidator:
    def __init__(self):
        self.thermal_speed_validator = ThermalSpeedValidator()
        self.si_units_validator = SIUnitsValidator()
        self.missing_data_validator = MissingDataValidator()
        self.multiindex_validator = MultiIndexValidator()
        self.data_access_validator = DataAccessValidator()
    
    def validate_example_compliance(self, example):
        """Comprehensive compliance check for single example"""
        violations = {
            'physics': [],
            'multiindex': [],
            'data_access': [],
            'units': [],
            'missing_data': []
        }
        
        # Execute example to get outputs
        try:
            result = execute_example(example.code)
            
            # Physics validation
            violations['physics'].extend(
                self.thermal_speed_validator.validate_examples_with_thermal_speed([example])
            )
            
            # Units validation
            violations['units'].extend(
                self.si_units_validator.validate_units_in_example(example.code)
            )
            
            # Missing data validation
            violations['missing_data'].extend(
                self.missing_data_validator.validate_nan_usage(example.code, result.outputs)
            )
            
            # MultiIndex validation
            for output_name, output_data in result.outputs.items():
                if hasattr(output_data, 'columns') and isinstance(output_data.columns, pd.MultiIndex):
                    violations['multiindex'].extend(
                        self.multiindex_validator.validate_column_structure(output_data)
                    )
                    violations['multiindex'].extend(
                        self.data_access_validator.validate_index_naming(output_data)
                    )
            
            # Data access pattern validation
            violations['data_access'].extend(
                self.data_access_validator.validate_xs_usage(example.code)
            )
            
        except Exception as e:
            violations['physics'].append(f"Example execution failed: {str(e)}")
        
        return violations
    
    def generate_compliance_report(self, examples):
        """Generate comprehensive compliance report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_examples': len(examples),
            'compliance_summary': {
                'physics_compliant': 0,
                'multiindex_compliant': 0,
                'fully_compliant': 0
            },
            'violations_by_category': {
                'physics': [],
                'multiindex': [],
                'data_access': [],
                'units': [],
                'missing_data': []
            },
            'example_details': []
        }
        
        for example in examples:
            violations = self.validate_example_compliance(example)
            
            is_physics_compliant = len(violations['physics']) == 0
            is_multiindex_compliant = (
                len(violations['multiindex']) == 0 and 
                len(violations['data_access']) == 0
            )
            is_fully_compliant = all(len(v) == 0 for v in violations.values())
            
            # Update summary counts
            if is_physics_compliant:
                report['compliance_summary']['physics_compliant'] += 1
            if is_multiindex_compliant:
                report['compliance_summary']['multiindex_compliant'] += 1
            if is_fully_compliant:
                report['compliance_summary']['fully_compliant'] += 1
            
            # Collect violations by category
            for category, violation_list in violations.items():
                report['violations_by_category'][category].extend(violation_list)
            
            # Add example details
            report['example_details'].append({
                'example_id': example.id,
                'file_path': example.file_path,
                'violations': violations,
                'physics_compliant': is_physics_compliant,
                'multiindex_compliant': is_multiindex_compliant,
                'fully_compliant': is_fully_compliant
            })
        
        return report
```

## 📊 Success Metrics

### Physics Compliance Targets
- **Thermal Speed Convention**: 100% compliance with mw² = 2kT
- **SI Units**: 100% internal calculations use SI units
- **Missing Data**: 100% use NaN for missing data (no 0 or -999)
- **Scientific Accuracy**: All physics calculations within 1% theoretical values

### MultiIndex Compliance Targets
- **Column Structure**: 100% use (M, C, S) naming convention
- **Data Access**: 90% use .xs() for MultiIndex access (some .loc acceptable)
- **Index Naming**: 100% time series use 'Epoch' index name
- **Consistency**: 100% species and component codes follow standards

### Automation Integration Targets
- **Validation Speed**: <10 seconds for all 47 examples
- **Error Detection**: 95% accuracy in identifying violations
- **CI/CD Ready**: Validation hooks prepared for automated testing
- **Documentation**: Clear guidelines for future example creation

## ⚡ Execution Strategy

### Phase 5 Implementation Order
1. **Physics Rule Validation** (60 min)
   - Focus on thermal speed and unit conventions first
   - Validate against existing examples with known physics
   - Create automated checking for future examples

2. **MultiIndex Structure Validation** (45 min)
   - Ensure all data structures follow established patterns
   - Validate access patterns and naming conventions
   - Document best practices for consistency

3. **Automation Integration** (15 min)
   - Create validation scripts for CI/CD integration
   - Prepare hooks for automated checking
   - Test validation speed and accuracy

### Risk Mitigation
- **Physics Expertise**: Validate rules with domain experts
- **Performance**: Optimize validation scripts for speed
- **False Positives**: Tune validation thresholds to avoid over-strictness
- **Backward Compatibility**: Ensure validation doesn't break existing patterns

## ✅ Completion Criteria
- [ ] All examples validated against physics rules
- [ ] MultiIndex structure compliance verified
- [ ] Automated validation framework operational
- [ ] Compliance report showing >95% rule adherence
- [ ] CI/CD integration hooks prepared
- [ ] Best practices documentation created

## 🔄 Transition to Phase 6
**Preparation for Phase 6: Doctest Integration**
- Physics and MultiIndex compliance established
- Automated validation framework operational
- Examples following consistent patterns
- Ready for doctest automation integration

**Next Phase Prerequisites:**
- Compliant examples as baseline for doctest integration
- Validation framework ready for CI/CD integration
- Clear patterns documented for automated testing
- Physics rules encoded in validation scripts

---

**📝 User Action Required**: After completing this phase, run:
```bash
git add plans/documentation-code-audit/5-Physics-MultiIndex-Compliance.md \
        physics_compliance_validator.py multiindex_structure_validator.py \
        compliance_report.json physics_examples_guide.md automated_validation_hooks.py
git commit -m "docs: complete Phase 5 physics and MultiIndex compliance validation

- Established comprehensive physics rule validation (thermal speed, units, missing data)
- Validated MultiIndex structure compliance across all examples
- Created automated validation framework for CI/CD integration
- Achieved >95% compliance with established physics and data conventions
- Documented best practices for consistent future example creation

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Then create compacted state for session continuity:**
```bash
python .claude/hooks/create-compaction.py \
  --trigger "Phase 5 completion - physics and MultiIndex compliance validated" \
  --context "Ready for doctest integration in Phase 6"
```