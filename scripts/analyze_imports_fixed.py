#!/usr/bin/env python3
"""
Fixed import dependency analysis tool for SolarWindPy circular import audit.
"""

import ast
import os
import sys
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Optional


class ImportAnalyzer(ast.NodeVisitor):
    """AST visitor to extract import information from Python files."""

    def __init__(self, module_name: str, package_root: str):
        self.module_name = module_name
        self.package_root = package_root
        self.imports = []
        self.from_imports = []

    def visit_Import(self, node):
        """Handle 'import module' statements."""
        for alias in node.names:
            self.imports.append(
                {
                    "type": "import",
                    "module": alias.name,
                    "alias": alias.asname,
                    "line": node.lineno,
                }
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Handle 'from module import ...' statements."""
        if node.module or node.level > 0:
            for alias in node.names:
                self.from_imports.append(
                    {
                        "type": "from_import",
                        "module": node.module or "",
                        "name": alias.name,
                        "alias": alias.asname,
                        "level": node.level,
                        "line": node.lineno,
                    }
                )
        self.generic_visit(node)


class DependencyAnalyzer:
    """Dependency analyzer for the SolarWindPy package."""

    def __init__(self, package_root: str):
        self.package_root = Path(package_root)
        self.package_name = self.package_root.name
        self.modules = {}
        self.dependencies = defaultdict(set)
        self.reverse_deps = defaultdict(set)

    def analyze_file(self, filepath: Path) -> Dict:
        """Analyze a single Python file for imports."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=str(filepath))

            # Get relative module name
            rel_path = filepath.relative_to(self.package_root)
            module_parts = list(rel_path.with_suffix("").parts)

            # Handle __init__.py files
            if module_parts[-1] == "__init__":
                module_parts = module_parts[:-1]

            module_name = ".".join(module_parts) if module_parts else self.package_name
            full_module_name = (
                f"{self.package_name}.{module_name}"
                if module_name != self.package_name
                else self.package_name
            )

            analyzer = ImportAnalyzer(full_module_name, str(self.package_root))
            analyzer.visit(tree)

            return {
                "module": full_module_name,
                "short_name": module_name,
                "file_path": str(filepath),
                "imports": analyzer.imports,
                "from_imports": analyzer.from_imports,
            }

        except Exception as e:
            print(f"Warning: Failed to analyze {filepath}: {e}")
            return None

    def scan_package(self) -> None:
        """Scan entire package for Python files and analyze imports."""
        print(f"Scanning package: {self.package_root}")

        python_files = list(self.package_root.rglob("*.py"))
        print(f"Found {len(python_files)} Python files")

        for filepath in python_files:
            # Skip test files and build artifacts
            if (
                "/tests/" in str(filepath)
                or filepath.name.startswith("test_")
                or "/__pycache__/" in str(filepath)
                or "/build/" in str(filepath)
            ):
                continue

            result = self.analyze_file(filepath)
            if result:
                module_name = result["module"]
                self.modules[module_name] = result

        print(f"Analyzed {len(self.modules)} modules")

    def build_dependency_graph(self) -> None:
        """Build dependency relationships based on imports."""
        print("Building dependency relationships...")

        for module_name, data in self.modules.items():
            # Process regular imports
            for imp in data["imports"]:
                target = self._resolve_import(imp["module"], module_name, 0)
                if target and target in self.modules:
                    self.dependencies[module_name].add(target)
                    self.reverse_deps[target].add(module_name)

            # Process from imports
            for imp in data["from_imports"]:
                target = self._resolve_import(imp["module"], module_name, imp["level"])
                if target and target in self.modules:
                    self.dependencies[module_name].add(target)
                    self.reverse_deps[target].add(module_name)

        total_deps = sum(len(deps) for deps in self.dependencies.values())
        print(f"Found {total_deps} internal dependencies")

    def _resolve_import(
        self, import_name: str, current_module: str, level: int = 0
    ) -> Optional[str]:
        """Resolve import name to actual module name in our package."""

        # Handle relative imports
        if level > 0:
            # Get the parts of the current module
            parts = current_module.split(".")

            # For relative imports, go up 'level' directories
            if level >= len(parts):
                return None

            # Calculate the base module after going up 'level' directories
            base_parts = parts[:-level] if level > 0 else parts
            base = ".".join(base_parts)

            if import_name:
                resolved = f"{base}.{import_name}" if base else import_name
            else:
                resolved = base
        else:
            resolved = import_name

        # For absolute imports, only consider imports within our package
        if not resolved.startswith(self.package_name):
            return None

        # Check if the resolved module exists in our modules
        if resolved in self.modules:
            return resolved

        # Also check for __init__.py modules (module.submodule might resolve to module.submodule.__init__)
        for existing_module in self.modules:
            if existing_module.startswith(resolved + ".") or resolved.startswith(
                existing_module + "."
            ):
                # Return the more specific match
                if len(existing_module) > len(resolved):
                    return existing_module

        return None

    def find_circular_dependencies_dfs(self) -> List[List[str]]:
        """Find circular dependencies using DFS with cycle detection."""
        print("Detecting circular dependencies using DFS...")

        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node):
            if node in rec_stack:
                # Found a cycle - extract it from the path
                try:
                    cycle_start = path.index(node)
                    cycle = path[cycle_start:]
                    if len(cycle) > 1:  # Only report cycles of length > 1
                        cycles.append(cycle[:])
                except ValueError:
                    pass
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.dependencies.get(node, []):
                dfs(neighbor)

            rec_stack.discard(node)
            if path and path[-1] == node:
                path.pop()

        for module in self.modules:
            if module not in visited:
                dfs(module)

        # Remove duplicate cycles
        unique_cycles = []
        for cycle in cycles:
            if cycle:
                # Normalize cycle by rotating to start with lexicographically smallest element
                min_idx = cycle.index(min(cycle))
                normalized = cycle[min_idx:] + cycle[:min_idx]
                if normalized not in unique_cycles:
                    unique_cycles.append(normalized)

        print(f"Found {len(unique_cycles)} unique circular dependency cycles")
        return unique_cycles

    def get_import_details(self, from_module: str, to_module: str) -> List[Dict]:
        """Get detailed information about imports between two modules."""
        details = []
        if from_module not in self.modules:
            return details

        data = self.modules[from_module]

        # Check regular imports
        for imp in data["imports"]:
            target = self._resolve_import(imp["module"], from_module, 0)
            if target == to_module:
                details.append(
                    {
                        "type": "import",
                        "line": imp["line"],
                        "statement": f"import {imp['module']}",
                        "alias": imp["alias"],
                    }
                )

        # Check from imports
        for imp in data["from_imports"]:
            target = self._resolve_import(imp["module"], from_module, imp["level"])
            if target == to_module:
                level_prefix = "." * imp["level"] if imp["level"] > 0 else ""
                module_name = imp["module"] or ""
                stmt = f"from {level_prefix}{module_name} import {imp['name']}"
                if imp["alias"]:
                    stmt += f" as {imp['alias']}"
                details.append(
                    {
                        "type": "from_import",
                        "line": imp["line"],
                        "statement": stmt,
                        "name": imp["name"],
                    }
                )

        return details

    def generate_report(self) -> Dict:
        """Generate comprehensive analysis report."""
        cycles = self.find_circular_dependencies_dfs()

        # Calculate metrics
        total_deps = sum(len(deps) for deps in self.dependencies.values())

        # Find modules with most dependencies
        most_dependencies = sorted(
            [(mod, len(deps)) for mod, deps in self.dependencies.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        most_dependents = sorted(
            [(mod, len(deps)) for mod, deps in self.reverse_deps.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        report = {
            "total_modules": len(self.modules),
            "total_dependencies": total_deps,
            "circular_dependencies": len(cycles),
            "cycles": cycles,
            "modules_with_most_dependencies": most_dependencies,
            "modules_with_most_dependents": most_dependents,
        }

        return report

    def save_detailed_report(
        self, output_file: str = "import_analysis_report.txt"
    ) -> None:
        """Save detailed text report of the analysis."""
        report = self.generate_report()

        with open(output_file, "w") as f:
            f.write("SolarWindPy Import Dependency Analysis Report\n")
            f.write("=" * 50 + "\n\n")

            f.write(f"Total modules analyzed: {report['total_modules']}\n")
            f.write(f"Total import relationships: {report['total_dependencies']}\n\n")

            # List all analyzed modules
            f.write("Analyzed modules:\n")
            for module_name in sorted(self.modules.keys()):
                f.write(f"  {module_name}\n")
            f.write("\n")

            if report["circular_dependencies"] > 0:
                f.write(
                    f"⚠️  CIRCULAR DEPENDENCIES FOUND: {report['circular_dependencies']}\n"
                )
                f.write("-" * 40 + "\n")
                for i, cycle in enumerate(report["cycles"], 1):
                    f.write(f"Cycle {i}: {' → '.join(cycle + [cycle[0]])}\n")
                f.write("\n")
            else:
                f.write("✅ No circular dependencies detected!\n\n")

            f.write("Top 10 modules with most dependencies (outgoing):\n")
            for module, count in report["modules_with_most_dependencies"]:
                f.write(f"  {module}: {count} dependencies\n")
                # Show what they depend on
                deps = sorted(self.dependencies.get(module, []))
                for dep in deps[:3]:  # Show first 3
                    f.write(f"    → {dep}\n")
                if len(deps) > 3:
                    f.write(f"    ... and {len(deps) - 3} more\n")
            f.write("\n")

            f.write("Top 10 most depended-upon modules (incoming):\n")
            for module, count in report["modules_with_most_dependents"]:
                f.write(f"  {module}: {count} dependents\n")
                # Show who depends on them
                deps = sorted(self.reverse_deps.get(module, []))
                for dep in deps[:3]:  # Show first 3
                    f.write(f"    ← {dep}\n")
                if len(deps) > 3:
                    f.write(f"    ... and {len(deps) - 3} more\n")
            f.write("\n")

            # Detailed cycle information
            if report["cycles"]:
                f.write("Detailed Cycle Analysis:\n")
                f.write("-" * 30 + "\n")
                for i, cycle in enumerate(report["cycles"], 1):
                    f.write(f"\nCycle {i} ({len(cycle)} modules):\n")
                    for j in range(len(cycle)):
                        current = cycle[j]
                        next_mod = cycle[(j + 1) % len(cycle)]

                        details = self.get_import_details(current, next_mod)
                        f.write(f"  {current} -> {next_mod}\n")
                        for detail in details:
                            f.write(
                                f"    Line {detail['line']}: {detail['statement']}\n"
                            )

            # Summary of key modules and their dependencies
            f.write("\n\nKey Module Dependencies:\n")
            f.write("-" * 30 + "\n")

            # Focus on main __init__.py and core modules
            key_modules = [
                m
                for m in self.modules.keys()
                if (m.endswith(".__init__") or "core" in m or m == self.package_name)
            ]

            for module in sorted(key_modules):
                deps = sorted(self.dependencies.get(module, []))
                if deps:
                    f.write(f"\n{module}:\n")
                    for dep in deps:
                        details = self.get_import_details(module, dep)
                        for detail in details:
                            f.write(f"  Line {detail['line']}: {detail['statement']}\n")

    def print_summary(self):
        """Print summary to console."""
        report = self.generate_report()

        print("\n" + "=" * 50)
        print("ANALYSIS SUMMARY")
        print("=" * 50)
        print(f"Total modules: {report['total_modules']}")
        print(f"Total dependencies: {report['total_dependencies']}")
        print(f"Circular dependencies: {report['circular_dependencies']}")

        if report["circular_dependencies"] > 0:
            print("\n⚠️  CIRCULAR DEPENDENCIES DETECTED:")
            for i, cycle in enumerate(report["cycles"], 1):
                print(f"  {i}. {' → '.join(cycle + [cycle[0]])}")
        else:
            print("\n✅ No circular dependencies found!")

        if report["modules_with_most_dependencies"]:
            print("\nModules with most dependencies:")
            for module, count in report["modules_with_most_dependencies"][:5]:
                short_name = module.split(".")[-1] if "." in module else module
                print(f"  {short_name}: {count}")

        if report["modules_with_most_dependents"]:
            print("\nMost depended-upon modules:")
            for module, count in report["modules_with_most_dependents"][:5]:
                short_name = module.split(".")[-1] if "." in module else module
                print(f"  {short_name}: {count}")


def main():
    """Main function to run the import analysis."""
    if len(sys.argv) > 1:
        package_root = sys.argv[1]
    else:
        # Default to solarwindpy directory
        script_dir = Path(__file__).parent
        package_root = script_dir.parent / "solarwindpy"

    print(f"Analyzing imports in: {package_root}")

    if not os.path.exists(package_root):
        print(f"Error: Package directory not found: {package_root}")
        sys.exit(1)

    # Create analyzer and run analysis
    analyzer = DependencyAnalyzer(package_root)
    analyzer.scan_package()
    analyzer.build_dependency_graph()

    # Print summary and save report
    analyzer.print_summary()
    analyzer.save_detailed_report("import_analysis_report.txt")

    print(f"\nDetailed report saved to: import_analysis_report.txt")


if __name__ == "__main__":
    main()
