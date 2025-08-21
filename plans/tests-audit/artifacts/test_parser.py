#!/usr/bin/env python3
"""
Test Suite Parser for SolarWindPy Physics-Focused Test Audit
Systematically parses all test files to extract test functions and metadata.
"""

import ast
import os
import re
import csv
from pathlib import Path
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass


@dataclass
class TestFunction:
    """Represents a test function with metadata."""
    file_path: str
    function_name: str
    line_number: int
    docstring: str
    decorators: List[str]
    has_parametrize: bool
    parametrize_count: int
    test_type: str  # unit, physics, edge, integration, performance
    physics_module: str  # plasma, ions, magnetic_field, instabilities, etc.
    complexity: str  # simple, moderate, complex
    estimated_coverage: float


class TestFileParser:
    """Parses Python test files to extract test function metadata."""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.test_functions: List[TestFunction] = []
        
    def parse_file(self, file_path: Path) -> List[TestFunction]:
        """Parse a single test file and return test functions."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    func = self._extract_function_metadata(node, file_path, content)
                    functions.append(func)
                    
            return functions
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return []
    
    def _extract_function_metadata(self, node: ast.FunctionDef, file_path: Path, content: str) -> TestFunction:
        """Extract metadata from a test function AST node."""
        
        # Basic info
        relative_path = str(file_path.relative_to(self.base_path))
        
        # Docstring
        docstring = ast.get_docstring(node) or ""
        
        # Decorators
        decorators = []
        parametrize_count = 1
        has_parametrize = False
        
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                decorators.append(f"{decorator.attr}")
                if decorator.attr == 'parametrize':
                    has_parametrize = True
                    # Try to count parameters
                    parametrize_count = self._count_parametrize(decorator, content)
            elif isinstance(decorator, ast.Call):
                if hasattr(decorator.func, 'attr'):
                    decorators.append(decorator.func.attr)
                    if decorator.func.attr == 'parametrize':
                        has_parametrize = True
                        parametrize_count = self._count_parametrize(decorator, content)
        
        # Classification
        test_type = self._classify_test_type(node.name, docstring, relative_path)
        physics_module = self._classify_physics_module(relative_path, node.name, docstring)
        complexity = self._assess_complexity(node, docstring, decorators)
        
        # Estimated coverage impact
        estimated_coverage = self._estimate_coverage_impact(node, parametrize_count, complexity)
        
        return TestFunction(
            file_path=relative_path,
            function_name=node.name,
            line_number=node.lineno,
            docstring=docstring,
            decorators=decorators,
            has_parametrize=has_parametrize,
            parametrize_count=parametrize_count,
            test_type=test_type,
            physics_module=physics_module,
            complexity=complexity,
            estimated_coverage=estimated_coverage
        )
    
    def _count_parametrize(self, decorator, content: str) -> int:
        """Estimate number of parametrized test cases."""
        try:
            # Simple heuristic - count commas in parametrize decorator
            lines = content.split('\n')
            # This is a rough estimate
            return max(1, content.count('parametrize') * 3)  # Conservative estimate
        except:
            return 1
    
    def _classify_test_type(self, func_name: str, docstring: str, file_path: str) -> str:
        """Classify test type based on name, docstring, and context."""
        
        # Performance tests
        if 'performance' in file_path or 'benchmark' in func_name.lower():
            return 'performance'
        
        # Integration tests  
        if 'integration' in file_path or 'integration' in func_name.lower():
            return 'integration'
        
        # Edge case tests
        edge_indicators = ['edge', 'boundary', 'limit', 'extreme', 'invalid', 'error']
        if any(indicator in func_name.lower() for indicator in edge_indicators):
            return 'edge'
        
        # Physics validation tests
        physics_indicators = ['physics', 'thermal', 'alfven', 'plasma', 'magnetic', 'temperature']
        if any(indicator in func_name.lower() for indicator in physics_indicators):
            return 'physics'
        
        # Default to unit test
        return 'unit'
    
    def _classify_physics_module(self, file_path: str, func_name: str, docstring: str) -> str:
        """Classify which physics module/domain the test belongs to."""
        
        path_lower = file_path.lower()
        func_lower = func_name.lower()
        doc_lower = docstring.lower()
        
        # Core physics modules
        if 'plasma' in path_lower or 'plasma' in func_lower:
            return 'plasma'
        elif 'ions' in path_lower or 'ion' in func_lower:
            return 'ions'  
        elif 'magnetic' in path_lower or 'magnetic' in func_lower or 'alfven' in func_lower:
            return 'magnetic_field'
        elif 'instabilities' in path_lower:
            return 'instabilities'
        elif 'spacecraft' in path_lower:
            return 'spacecraft'
        elif 'alfvenic' in path_lower or 'turbulence' in path_lower:
            return 'alfvenic_turbulence'
        
        # Utility modules
        elif 'fitfunctions' in path_lower:
            return 'fitfunctions'
        elif 'plotting' in path_lower:
            return 'plotting'
        elif 'solar_activity' in path_lower:
            return 'solar_activity'
        elif 'base' in path_lower:
            return 'base_framework'
        
        # General tests
        else:
            return 'general'
    
    def _assess_complexity(self, node: ast.FunctionDef, docstring: str, decorators: List[str]) -> str:
        """Assess test complexity based on AST analysis."""
        
        # Count lines of code (rough estimate)
        body_lines = len(node.body)
        
        # Count assert statements
        assert_count = 0
        for child in ast.walk(node):
            if isinstance(child, ast.Assert):
                assert_count += 1
        
        # Complexity indicators
        has_loops = any(isinstance(child, (ast.For, ast.While)) for child in ast.walk(node))
        has_conditionals = any(isinstance(child, ast.If) for child in ast.walk(node))
        has_fixtures = 'fixture' in decorators or len(decorators) > 1
        
        # Complex if many lines, multiple asserts, control flow
        if body_lines > 20 or assert_count > 5 or (has_loops and has_conditionals):
            return 'complex'
        elif body_lines > 8 or assert_count > 2 or has_fixtures:
            return 'moderate'
        else:
            return 'simple'
    
    def _estimate_coverage_impact(self, node: ast.FunctionDef, parametrize_count: int, complexity: str) -> float:
        """Estimate coverage percentage impact of this test."""
        
        base_impact = {
            'simple': 0.1,
            'moderate': 0.3, 
            'complex': 0.8
        }.get(complexity, 0.1)
        
        # Parametrized tests have multiplicative effect
        return base_impact * parametrize_count
    
    def parse_all_files(self, test_files: List[str]) -> List[TestFunction]:
        """Parse all test files and return comprehensive metadata."""
        
        all_functions = []
        
        for file_path in test_files:
            full_path = self.base_path / file_path
            if full_path.exists():
                functions = self.parse_file(full_path)
                all_functions.extend(functions)
                print(f"Parsed {len(functions)} functions from {file_path}")
        
        self.test_functions = all_functions
        return all_functions
    
    def generate_csv_report(self, output_path: str):
        """Generate CSV inventory report."""
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'file_path', 'function_name', 'line_number', 'test_type', 
                'physics_module', 'complexity', 'has_parametrize', 
                'parametrize_count', 'estimated_coverage', 'decorators', 'docstring'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for func in self.test_functions:
                writer.writerow({
                    'file_path': func.file_path,
                    'function_name': func.function_name,
                    'line_number': func.line_number,
                    'test_type': func.test_type,
                    'physics_module': func.physics_module,
                    'complexity': func.complexity,
                    'has_parametrize': func.has_parametrize,
                    'parametrize_count': func.parametrize_count,
                    'estimated_coverage': func.estimated_coverage,
                    'decorators': ';'.join(func.decorators),
                    'docstring': func.docstring.replace('\n', ' ')[:200]  # Truncate for CSV
                })
    
    def generate_summary_stats(self) -> Dict[str, Any]:
        """Generate summary statistics for the test suite."""
        
        total_functions = len(self.test_functions)
        
        # Type distribution
        type_counts = {}
        for func in self.test_functions:
            type_counts[func.test_type] = type_counts.get(func.test_type, 0) + 1
        
        # Physics module distribution  
        physics_counts = {}
        for func in self.test_functions:
            physics_counts[func.physics_module] = physics_counts.get(func.physics_module, 0) + 1
        
        # Complexity distribution
        complexity_counts = {}
        for func in self.test_functions:
            complexity_counts[func.complexity] = complexity_counts.get(func.complexity, 0) + 1
        
        # File distribution
        file_counts = {}
        for func in self.test_functions:
            file_counts[func.file_path] = file_counts.get(func.file_path, 0) + 1
        
        return {
            'total_functions': total_functions,
            'total_files': len(file_counts),
            'type_distribution': type_counts,
            'physics_distribution': physics_counts,
            'complexity_distribution': complexity_counts,
            'file_distribution': file_counts,
            'parametrized_tests': sum(1 for f in self.test_functions if f.has_parametrize),
            'estimated_total_test_cases': sum(f.parametrize_count for f in self.test_functions)
        }


if __name__ == '__main__':
    
    # Test file list (from glob results)
    test_files = [
        'tests/core/test_alfvenic_turbulence.py',
        'tests/core/test_base.py',
        'tests/core/test_base_head_tail.py',
        'tests/core/test_base_mi_tuples.py',
        'tests/core/test_core_verify_datetimeindex.py',
        'tests/core/test_ions.py',
        'tests/core/test_plasma.py',
        'tests/core/test_plasma_io.py',
        'tests/core/test_quantities.py',
        'tests/core/test_spacecraft.py',
        'tests/core/test_units_constants.py',
        'tests/fitfunctions/test_core.py',
        'tests/fitfunctions/test_exponentials.py',
        'tests/fitfunctions/test_gaussians.py',
        'tests/fitfunctions/test_lines.py',
        'tests/fitfunctions/test_moyal.py',
        'tests/fitfunctions/test_plots.py',
        'tests/fitfunctions/test_power_laws.py',
        'tests/fitfunctions/test_tex_info.py',
        'tests/fitfunctions/test_trend_fit_properties.py',
        'tests/fitfunctions/test_trend_fits.py',
        'tests/plotting/labels/test_chemistry.py',
        'tests/plotting/labels/test_composition.py',
        'tests/plotting/labels/test_datetime.py',
        'tests/plotting/labels/test_elemental_abundance.py',
        'tests/plotting/labels/test_init.py',
        'tests/plotting/labels/test_labels_base.py',
        'tests/plotting/labels/test_special.py',
        'tests/plotting/test_agg_plot.py',
        'tests/plotting/test_base.py',
        'tests/plotting/test_fixtures_utilities.py',
        'tests/plotting/test_histograms.py',
        'tests/plotting/test_integration.py',
        'tests/plotting/test_orbits.py',
        'tests/plotting/test_performance.py',
        'tests/plotting/test_scatter.py',
        'tests/plotting/test_select_data_from_figure.py',
        'tests/plotting/test_spiral.py',
        'tests/plotting/test_tools.py',
        'tests/plotting/test_visual_validation.py',
        'tests/solar_activity/lisird/test_extrema_calculator.py',
        'tests/solar_activity/lisird/test_lisird_id.py',
        'tests/solar_activity/sunspot_number/test_init.py',
        'tests/solar_activity/sunspot_number/test_sidc.py',
        'tests/solar_activity/sunspot_number/test_sidc_id.py',
        'tests/solar_activity/sunspot_number/test_sidc_loader.py',
        'tests/solar_activity/sunspot_number/test_ssn_extrema.py',
        'tests/solar_activity/test_base.py',
        'tests/solar_activity/test_init.py',
        'tests/solar_activity/test_plots.py',
        'tests/test_circular_imports.py',
        'tests/test_issue_titles.py',
        'tests/test_planning_agents_architecture.py',
        'tests/test_statusline.py'
    ]
    
    base_path = '/Users/balterma/observatories/code/SolarWindPy-2'
    parser = TestFileParser(base_path)
    
    print("SolarWindPy Test Suite Parser")
    print("=" * 50)
    print(f"Parsing {len(test_files)} test files...")
    
    # Parse all test files
    all_functions = parser.parse_all_files(test_files)
    
    print(f"\nDiscovered {len(all_functions)} test functions")
    
    # Generate summary statistics
    stats = parser.generate_summary_stats()
    
    print("\nSummary Statistics:")
    print(f"Total test functions: {stats['total_functions']}")
    print(f"Total test files: {stats['total_files']}")
    print(f"Parametrized tests: {stats['parametrized_tests']}")
    print(f"Estimated test cases: {stats['estimated_total_test_cases']}")
    
    print("\nTest Type Distribution:")
    for test_type, count in sorted(stats['type_distribution'].items()):
        print(f"  {test_type}: {count}")
    
    print("\nPhysics Module Distribution:")
    for module, count in sorted(stats['physics_distribution'].items()):
        print(f"  {module}: {count}")
    
    print("\nComplexity Distribution:")
    for complexity, count in sorted(stats['complexity_distribution'].items()):
        print(f"  {complexity}: {count}")
    
    # Generate CSV report
    csv_path = '/Users/balterma/observatories/code/SolarWindPy-2/plans/tests-audit/artifacts/TEST_INVENTORY.csv'
    parser.generate_csv_report(csv_path)
    print(f"\nCSV inventory saved to: {csv_path}")
    
    print("\nTest discovery and enumeration complete!")