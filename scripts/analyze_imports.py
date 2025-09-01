#!/usr/bin/env python3
"""
Import dependency analysis tool for SolarWindPy circular import audit.

This script analyzes all Python files in the solarwindpy package to:
1. Extract import relationships using AST parsing
2. Build a dependency graph using NetworkX
3. Detect circular dependencies algorithmically
4. Generate visualization and reports
"""

import ast
import os
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional
import networkx as nx
import matplotlib.pyplot as plt


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
        if node.module:
            for alias in node.names:
                self.from_imports.append(
                    {
                        "type": "from_import",
                        "module": node.module,
                        "name": alias.name,
                        "alias": alias.asname,
                        "level": node.level,  # For relative imports
                        "line": node.lineno,
                    }
                )
        self.generic_visit(node)


class DependencyGraphBuilder:
    """Builds and analyzes dependency graphs for circular import detection."""

    def __init__(self, package_root: str):
        self.package_root = Path(package_root)
        self.graph = nx.DiGraph()
        self.modules = {}
        self.import_data = defaultdict(list)

    def analyze_file(self, filepath: Path) -> Dict:
        """Analyze a single Python file for imports."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=str(filepath))

            # Get relative module name
            rel_path = filepath.relative_to(self.package_root)
            module_name = str(rel_path.with_suffix("").as_posix().replace("/", "."))

            analyzer = ImportAnalyzer(module_name, str(self.package_root))
            analyzer.visit(tree)

            return {
                "module": module_name,
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
            # Skip test files for now (focus on main package structure)
            if "/tests/" in str(filepath) or filepath.name.startswith("test_"):
                continue

            result = self.analyze_file(filepath)
            if result:
                module_name = result["module"]
                self.modules[module_name] = result

                # Add node to graph
                self.graph.add_node(module_name, **result)

        print(f"Analyzed {len(self.modules)} modules")

    def build_dependency_graph(self) -> None:
        """Build dependency edges based on import relationships."""
        print("Building dependency graph...")

        for module_name, data in self.modules.items():
            # Process regular imports
            for imp in data["imports"]:
                target = self._resolve_import(imp["module"], module_name)
                if target and target in self.modules:
                    self.graph.add_edge(
                        module_name,
                        target,
                        import_type="import",
                        line=imp["line"],
                        original=imp["module"],
                    )

            # Process from imports
            for imp in data["from_imports"]:
                target = self._resolve_import(imp["module"], module_name, imp["level"])
                if target and target in self.modules:
                    self.graph.add_edge(
                        module_name,
                        target,
                        import_type="from_import",
                        line=imp["line"],
                        name=imp["name"],
                        original=imp["module"],
                    )

        print(
            f"Graph has {len(self.graph.nodes)} nodes and {len(self.graph.edges)} edges"
        )

    def _resolve_import(
        self, import_name: str, current_module: str, level: int = 0
    ) -> Optional[str]:
        """Resolve import name to actual module name in our package."""
        # Handle relative imports
        if level > 0:
            parts = current_module.split(".")
            if level >= len(parts):
                return None
            base = ".".join(parts[:-level])
            if import_name:
                resolved = f"{base}.{import_name}" if base else import_name
            else:
                resolved = base
        else:
            resolved = import_name

        # Only consider imports within our package
        if not resolved.startswith("solarwindpy"):
            return None

        return resolved

    def find_circular_dependencies(self) -> List[List[str]]:
        """Find all circular dependencies in the import graph."""
        print("Detecting circular dependencies...")

        try:
            cycles = list(nx.simple_cycles(self.graph))
            print(f"Found {len(cycles)} circular dependency cycles")

            # Sort cycles by length and alphabetically for consistent reporting
            cycles.sort(key=lambda cycle: (len(cycle), cycle))

            return cycles
        except Exception as e:
            print(f"Error detecting cycles: {e}")
            return []

    def generate_report(self) -> Dict:
        """Generate comprehensive analysis report."""
        cycles = self.find_circular_dependencies()

        # Calculate metrics
        strongly_connected = list(nx.strongly_connected_components(self.graph))

        # Find modules with most dependencies
        out_degrees = dict(self.graph.out_degree())
        in_degrees = dict(self.graph.in_degree())

        most_dependencies = sorted(
            out_degrees.items(), key=lambda x: x[1], reverse=True
        )[:10]
        most_dependents = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[
            :10
        ]

        report = {
            "total_modules": len(self.modules),
            "total_dependencies": len(self.graph.edges),
            "circular_dependencies": len(cycles),
            "cycles": cycles,
            "strongly_connected_components": len(strongly_connected),
            "largest_scc_size": (
                max(len(scc) for scc in strongly_connected) if strongly_connected else 0
            ),
            "modules_with_most_dependencies": most_dependencies,
            "modules_with_most_dependents": most_dependents,
            "graph_density": nx.density(self.graph),
        }

        return report

    def visualize_graph(
        self, output_file: str = "dependency_graph.png", highlight_cycles: bool = True
    ) -> None:
        """Generate visualization of the dependency graph."""
        print(f"Creating visualization: {output_file}")

        plt.figure(figsize=(16, 12))

        # Use hierarchical layout for better visualization
        try:
            pos = nx.spring_layout(self.graph, k=1, iterations=50)
        except:
            pos = nx.random_layout(self.graph)

        # Color nodes based on whether they're in cycles
        node_colors = []
        if highlight_cycles:
            cycles = self.find_circular_dependencies()
            cycle_nodes = set()
            for cycle in cycles:
                cycle_nodes.update(cycle)

            for node in self.graph.nodes():
                if node in cycle_nodes:
                    node_colors.append("red")
                else:
                    node_colors.append("lightblue")
        else:
            node_colors = ["lightblue"] * len(self.graph.nodes())

        # Draw graph
        nx.draw(
            self.graph,
            pos,
            node_color=node_colors,
            node_size=100,
            font_size=6,
            font_weight="bold",
            arrows=True,
            edge_color="gray",
            alpha=0.7,
        )

        plt.title(
            "SolarWindPy Import Dependency Graph\n(Red nodes are in circular dependencies)"
        )
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        plt.close()

    def save_detailed_report(
        self, output_file: str = "import_analysis_report.txt"
    ) -> None:
        """Save detailed text report of the analysis."""
        report = self.generate_report()

        with open(output_file, "w") as f:
            f.write("SolarWindPy Import Dependency Analysis Report\n")
            f.write("=" * 50 + "\n\n")

            f.write(f"Total modules analyzed: {report['total_modules']}\n")
            f.write(f"Total import relationships: {report['total_dependencies']}\n")
            f.write(f"Graph density: {report['graph_density']:.3f}\n")
            f.write(
                f"Strongly connected components: {report['strongly_connected_components']}\n"
            )
            f.write(f"Largest SCC size: {report['largest_scc_size']}\n\n")

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
            f.write("\n")

            f.write("Top 10 most depended-upon modules (incoming):\n")
            for module, count in report["modules_with_most_dependents"]:
                f.write(f"  {module}: {count} dependents\n")
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

                        # Find the specific import causing this edge
                        edge_data = self.graph.get_edge_data(current, next_mod)
                        if edge_data:
                            f.write(f"  {current} -> {next_mod}\n")
                            f.write(
                                f"    Import type: {edge_data.get('import_type', 'unknown')}\n"
                            )
                            f.write(f"    Line: {edge_data.get('line', 'unknown')}\n")
                            f.write(
                                f"    Original: {edge_data.get('original', 'unknown')}\n"
                            )


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
    analyzer = DependencyGraphBuilder(package_root)
    analyzer.scan_package()
    analyzer.build_dependency_graph()

    # Generate outputs
    report = analyzer.generate_report()

    # Print summary to console
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

    # Save detailed outputs
    analyzer.save_detailed_report("import_analysis_report.txt")
    analyzer.visualize_graph("dependency_graph.png")

    print(f"\nDetailed report saved to: import_analysis_report.txt")
    print(f"Graph visualization saved to: dependency_graph.png")


if __name__ == "__main__":
    main()
