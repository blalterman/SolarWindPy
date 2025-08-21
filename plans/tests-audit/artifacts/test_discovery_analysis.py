#!/usr/bin/env python3
"""
Test Discovery and Analysis Script for Physics-Focused Test Suite Audit
Phase 1: Discovery & Inventory

This script systematically discovers and analyzes all test functions in the SolarWindPy test suite
to create comprehensive inventory artifacts for the audit process.
"""

import os
import ast
import csv
import glob
import pandas as pd
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Set

class TestFunctionDiscovery:
    """Discovers and analyzes test functions in the SolarWindPy test suite."""
    
    def __init__(self, tests_root: str = "tests"):
        self.tests_root = Path(tests_root)
        self.test_files = []
        self.test_functions = []
        self.classification_data = []
        
    def discover_test_files(self) -> List[Path]:
        """Discover all test files in the test directory."""
        pattern = str(self.tests_root / "**" / "test_*.py")
        files = glob.glob(pattern, recursive=True)
        self.test_files = [Path(f) for f in sorted(files)]
        return self.test_files
    
    def extract_test_functions(self, file_path: Path) -> List[Dict]:
        """Extract test functions from a Python file using AST parsing."""
        functions = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    # Extract docstring if present
                    docstring = ""
                    if (node.body and isinstance(node.body[0], ast.Expr) 
                        and isinstance(node.body[0].value, ast.Str)):
                        docstring = node.body[0].value.s
                    elif (node.body and isinstance(node.body[0], ast.Expr)
                          and isinstance(node.body[0].value, ast.Constant)
                          and isinstance(node.body[0].value.value, str)):
                        docstring = node.body[0].value.value
                    
                    # Count lines of code in function
                    func_lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 1
                    
                    functions.append({
                        'file_path': str(file_path),
                        'function_name': node.name,
                        'line_number': node.lineno,
                        'docstring': docstring,
                        'num_lines': func_lines,
                        'args': len(node.args.args)
                    })
                    
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
        
        return functions
    
    def classify_test_function(self, func_data: Dict) -> Dict:
        """Classify a test function by type and physics domain."""
        func_name = func_data['function_name']
        file_path = func_data['file_path']
        docstring = func_data['docstring'].lower()
        
        # Initialize classification
        classification = {
            'test_type': 'unit',  # Default
            'physics_domain': 'general',
            'complexity': 'simple',
            'is_physics_test': False,
            'is_edge_case': False,
            'is_integration': False,
            'is_performance': False
        }
        
        # Classify by test type based on function name patterns
        if any(keyword in func_name.lower() for keyword in ['edge', 'boundary', 'extreme', 'invalid']):
            classification['test_type'] = 'edge'
            classification['is_edge_case'] = True
        elif any(keyword in func_name.lower() for keyword in ['integration', 'end_to_end', 'full']):
            classification['test_type'] = 'integration'
            classification['is_integration'] = True
        elif any(keyword in func_name.lower() for keyword in ['performance', 'speed', 'benchmark', 'timing']):
            classification['test_type'] = 'performance'
            classification['is_performance'] = True
        elif any(keyword in func_name.lower() for keyword in ['physics', 'thermal', 'alfven', 'magnetic', 'plasma']):
            classification['test_type'] = 'physics'
            classification['is_physics_test'] = True
        
        # Classify by physics domain based on file path and function name
        if 'core/test_plasma' in file_path:
            classification['physics_domain'] = 'plasma'
            classification['is_physics_test'] = True
        elif 'core/test_ions' in file_path:
            classification['physics_domain'] = 'ions'
            classification['is_physics_test'] = True
        elif 'core/test_alfvenic' in file_path:
            classification['physics_domain'] = 'alfvenic_turbulence'
            classification['is_physics_test'] = True
        elif 'core/test_spacecraft' in file_path:
            classification['physics_domain'] = 'spacecraft'
        elif 'fitfunctions' in file_path:
            classification['physics_domain'] = 'fitting'
        elif 'plotting' in file_path:
            classification['physics_domain'] = 'visualization'
        elif 'solar_activity' in file_path:
            classification['physics_domain'] = 'solar_activity'
        elif 'instabilities' in file_path:
            classification['physics_domain'] = 'instabilities'
            classification['is_physics_test'] = True
        
        # Assess complexity based on function characteristics
        if func_data['num_lines'] > 50:
            classification['complexity'] = 'complex'
        elif func_data['num_lines'] > 20 or func_data['args'] > 3:
            classification['complexity'] = 'moderate'
        
        # Physics-specific classifications
        physics_keywords = ['thermal_speed', 'alfven_speed', 'density', 'velocity', 'temperature', 
                           'magnetic_field', 'pressure', 'beta', 'ma', 'conservation', 'units']
        if any(keyword in func_name.lower() or keyword in docstring for keyword in physics_keywords):
            classification['is_physics_test'] = True
            if classification['test_type'] == 'unit':
                classification['test_type'] = 'physics'
        
        return classification
    
    def analyze_test_suite(self) -> Dict:
        """Complete analysis of the test suite."""
        print("🔍 Discovering test files...")
        self.discover_test_files()
        
        print(f"📁 Found {len(self.test_files)} test files")
        
        print("📝 Extracting test functions...")
        all_functions = []
        for file_path in self.test_files:
            functions = self.extract_test_functions(file_path)
            all_functions.extend(functions)
        
        print(f"🧪 Found {len(all_functions)} test functions")
        
        print("🏷️  Classifying test functions...")
        for func_data in all_functions:
            classification = self.classify_test_function(func_data)
            func_data.update(classification)
            self.classification_data.append(func_data)
        
        # Generate summary statistics
        summary = {
            'total_files': len(self.test_files),
            'total_functions': len(self.classification_data),
            'by_type': defaultdict(int),
            'by_domain': defaultdict(int),
            'by_complexity': defaultdict(int),
            'physics_tests': 0,
            'edge_tests': 0,
            'integration_tests': 0
        }
        
        for func in self.classification_data:
            summary['by_type'][func['test_type']] += 1
            summary['by_domain'][func['physics_domain']] += 1
            summary['by_complexity'][func['complexity']] += 1
            if func['is_physics_test']:
                summary['physics_tests'] += 1
            if func['is_edge_case']:
                summary['edge_tests'] += 1
            if func['is_integration']:
                summary['integration_tests'] += 1
        
        return summary

def main():
    """Main execution function."""
    print("🚀 Starting Phase 1: Test Suite Discovery & Inventory")
    print("=" * 60)
    
    # Initialize discovery
    discoverer = TestFunctionDiscovery()
    
    # Perform complete analysis
    summary = discoverer.analyze_test_suite()
    
    # Print summary
    print(f"\n📊 DISCOVERY SUMMARY:")
    print(f"Total test files: {summary['total_files']}")
    print(f"Total test functions: {summary['total_functions']}")
    print(f"Physics-focused tests: {summary['physics_tests']}")
    print(f"Edge case tests: {summary['edge_tests']}")
    print(f"Integration tests: {summary['integration_tests']}")
    
    print(f"\n🏷️  By Test Type:")
    for test_type, count in sorted(summary['by_type'].items()):
        print(f"  {test_type}: {count}")
    
    print(f"\n🧪 By Physics Domain:")
    for domain, count in sorted(summary['by_domain'].items()):
        print(f"  {domain}: {count}")
    
    print(f"\n📈 By Complexity:")
    for complexity, count in sorted(summary['by_complexity'].items()):
        print(f"  {complexity}: {count}")
    
    # Save detailed data to CSV
    output_dir = Path('plans/tests-audit/artifacts')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = output_dir / 'TEST_INVENTORY.csv'
    df = pd.DataFrame(discoverer.classification_data)
    df.to_csv(csv_path, index=False)
    print(f"\n💾 Detailed inventory saved to: {csv_path}")
    
    return summary, discoverer.classification_data

if __name__ == "__main__":
    summary, data = main()