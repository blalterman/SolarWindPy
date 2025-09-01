#!/usr/bin/env python3
"""
Extract and parse code examples from RST documentation and Python docstrings.

This module provides tools for systematically extracting code examples from
SolarWindPy documentation for validation and testing purposes.
"""

import ast
import re
import json
import doctest
from pathlib import Path
from typing import List, Dict, Any, Optional
import importlib.util


class CodeExample:
    """Represents a single code example with metadata."""

    def __init__(
        self,
        code: str,
        file_path: str,
        line_start: int,
        line_end: int,
        example_type: str = "code-block",
        example_id: str = None,
    ):
        self.code = code
        self.file_path = file_path
        self.line_start = line_start
        self.line_end = line_end
        self.example_type = example_type  # "code-block", "doctest", "bash"
        self.example_id = example_id or f"{Path(file_path).stem}_{line_start}"
        self.dependencies = []
        self.issues = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.example_id,
            "code": self.code,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "example_type": self.example_type,
            "dependencies": self.dependencies,
            "issues": self.issues,
        }


class RSTExtractor:
    """Extract code blocks from RST documentation files."""

    def __init__(self):
        self.python_block_pattern = re.compile(
            r"^\s*\.\. code-block::\s*python\s*$.*?(?=^\s*\.\.|^\s*[^\s]|\Z)",
            re.MULTILINE | re.DOTALL,
        )
        self.bash_block_pattern = re.compile(
            r"^\s*\.\. code-block::\s*bash\s*$.*?(?=^\s*\.\.|^\s*[^\s]|\Z)",
            re.MULTILINE | re.DOTALL,
        )

    def extract_from_file(self, file_path: Path) -> List[CodeExample]:
        """Extract all code blocks from an RST file."""
        if not file_path.exists():
            raise FileNotFoundError(f"RST file not found: {file_path}")

        content = file_path.read_text(encoding="utf-8")
        examples = []

        # Extract Python code blocks
        for match in self.python_block_pattern.finditer(content):
            code = self._extract_code_from_block(match.group())
            if code.strip():
                line_start = content[: match.start()].count("\n") + 1
                line_end = content[: match.end()].count("\n") + 1

                example = CodeExample(
                    code=code,
                    file_path=str(file_path),
                    line_start=line_start,
                    line_end=line_end,
                    example_type="code-block",
                )
                examples.append(example)

        # Extract bash code blocks (for installation examples)
        for match in self.bash_block_pattern.finditer(content):
            code = self._extract_code_from_block(match.group())
            if code.strip():
                line_start = content[: match.start()].count("\n") + 1
                line_end = content[: match.end()].count("\n") + 1

                example = CodeExample(
                    code=code,
                    file_path=str(file_path),
                    line_start=line_start,
                    line_end=line_end,
                    example_type="bash",
                )
                examples.append(example)

        return examples

    def _extract_code_from_block(self, block_text: str) -> str:
        """Extract the actual code from a code-block directive."""
        lines = block_text.split("\n")
        code_lines = []
        in_code = False

        for line in lines:
            if re.match(r"^\s*\.\. code-block::", line):
                in_code = True
                continue

            if in_code:
                # Stop at next directive or non-indented line
                if line.strip() and not line.startswith("   "):
                    if not re.match(r"^\s*:", line):  # Not a directive option
                        break

                # Skip directive options (lines starting with :)
                if re.match(r"^\s*:", line):
                    continue

                # Extract indented code
                if line.startswith("   "):
                    code_lines.append(line[3:])  # Remove 3-space indentation
                elif not line.strip():
                    code_lines.append("")  # Preserve blank lines

        return "\n".join(code_lines).strip()


class DocstringExtractor:
    """Extract doctest examples from Python module docstrings."""

    def __init__(self):
        self.finder = doctest.DocTestFinder()

    def extract_from_file(self, file_path: Path) -> List[CodeExample]:
        """Extract all doctest examples from a Python file."""
        if not file_path.exists():
            raise FileNotFoundError(f"Python file not found: {file_path}")

        # Load the module
        try:
            spec = importlib.util.spec_from_file_location("module", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"Warning: Could not import {file_path}: {e}")
            return []

        # Find all doctests
        tests = self.finder.find(module)
        examples = []

        for test in tests:
            if test.examples:
                for i, example in enumerate(test.examples):
                    # Reconstruct the code from the doctest example
                    code = example.source.strip()
                    if example.want:
                        # Include expected output as comment for reference
                        code += f"\n# Expected output:\n# {example.want.strip()}"

                    example_obj = CodeExample(
                        code=code,
                        file_path=str(file_path),
                        line_start=example.lineno,
                        line_end=example.lineno + code.count("\n"),
                        example_type="doctest",
                        example_id=f"{test.name}_example_{i}",
                    )
                    examples.append(example_obj)

        return examples


class SyntaxValidator:
    """Validate Python code syntax without execution."""

    @staticmethod
    def validate_syntax(code: str) -> Dict[str, Any]:
        """Check if code has valid Python syntax."""
        try:
            ast.parse(code)
            return {"valid": True, "error": None}
        except SyntaxError as e:
            return {
                "valid": False,
                "error": str(e),
                "line": e.lineno,
                "offset": e.offset,
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"Parse error: {str(e)}",
                "line": None,
                "offset": None,
            }

    @staticmethod
    def find_imports(code: str) -> List[str]:
        """Extract import statements from code."""
        try:
            tree = ast.parse(code)
            imports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(
                            f"{module}.{alias.name}" if module else alias.name
                        )

            return imports
        except:
            return []


class ExampleInventory:
    """Manage inventory of all code examples."""

    def __init__(self):
        self.examples = []
        self.rst_extractor = RSTExtractor()
        self.docstring_extractor = DocstringExtractor()
        self.syntax_validator = SyntaxValidator()

    def scan_documentation(self, base_path: Path) -> None:
        """Scan all documentation files for examples."""
        # RST documentation files
        rst_files = [
            base_path / "docs" / "source" / "usage.rst",
            base_path / "docs" / "source" / "installation.rst",
            base_path / "docs" / "source" / "tutorial" / "quickstart.rst",
            base_path / "README.rst",
        ]

        for rst_file in rst_files:
            if rst_file.exists():
                try:
                    examples = self.rst_extractor.extract_from_file(rst_file)
                    self.examples.extend(examples)
                    print(f"Found {len(examples)} examples in {rst_file}")
                except Exception as e:
                    print(f"Error processing {rst_file}: {e}")

        # Python module docstrings
        python_files = [
            base_path / "solarwindpy" / "core" / "plasma.py",
            base_path / "solarwindpy" / "core" / "ions.py",
            base_path / "solarwindpy" / "tools" / "__init__.py",
            base_path / "solarwindpy" / "fitfunctions" / "tex_info.py",
        ]

        for py_file in python_files:
            if py_file.exists():
                try:
                    examples = self.docstring_extractor.extract_from_file(py_file)
                    self.examples.extend(examples)
                    print(f"Found {len(examples)} doctest examples in {py_file}")
                except Exception as e:
                    print(f"Error processing {py_file}: {e}")

    def validate_all_syntax(self) -> None:
        """Validate syntax for all Python examples."""
        for example in self.examples:
            if example.example_type in ["code-block", "doctest"]:
                result = self.syntax_validator.validate_syntax(example.code)
                if not result["valid"]:
                    example.issues.append(
                        {
                            "type": "SyntaxError",
                            "message": result["error"],
                            "line": result.get("line"),
                            "offset": result.get("offset"),
                        }
                    )

                # Extract import dependencies
                example.dependencies = self.syntax_validator.find_imports(example.code)

    def save_to_json(self, output_path: Path) -> None:
        """Save inventory to JSON file."""
        data = {
            "scan_timestamp": "2025-08-21T06:00:00Z",
            "total_examples": len(self.examples),
            "examples": [example.to_dict() for example in self.examples],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"Saved inventory of {len(self.examples)} examples to {output_path}")

    def filter_by_type(self, example_type: str) -> List[CodeExample]:
        """Filter examples by type."""
        return [ex for ex in self.examples if ex.example_type == example_type]

    def filter_with_issues(self) -> List[CodeExample]:
        """Get examples with syntax or other issues."""
        return [ex for ex in self.examples if ex.issues]


if __name__ == "__main__":
    # Example usage
    base_path = Path(".")
    inventory = ExampleInventory()

    print("Scanning documentation for code examples...")
    inventory.scan_documentation(base_path)

    print("Validating syntax...")
    inventory.validate_all_syntax()

    print("Saving inventory...")
    inventory.save_to_json(Path("example_extraction_results.json"))

    # Summary
    print(f"\nSummary:")
    print(f"Total examples found: {len(inventory.examples)}")
    print(f"Python code blocks: {len(inventory.filter_by_type('code-block'))}")
    print(f"Doctest examples: {len(inventory.filter_by_type('doctest'))}")
    print(f"Bash examples: {len(inventory.filter_by_type('bash'))}")
    print(f"Examples with issues: {len(inventory.filter_with_issues())}")
