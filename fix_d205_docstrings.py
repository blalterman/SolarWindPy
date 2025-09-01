#!/usr/bin/env python3
"""
Fix D205 docstring errors by adding blank lines between summary and description.
"""

import re
import sys
from pathlib import Path


def fix_d205_in_file(filepath):
    """Fix D205 errors in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Pattern to match docstrings with summary followed immediately by description
    # This handles both """ and ''' style docstrings
    pattern = r'([ \t]*)("""|\'\'\')(.*?)\n([ \t]*)((?!\2).+?)(\n[ \t]*\2)'
    
    def add_blank_line(match):
        indent = match.group(1)
        quotes = match.group(2)
        summary = match.group(3)
        desc_indent = match.group(4)
        description = match.group(5)
        end = match.group(6)
        
        # Check if description starts with parameters or other sections
        if description.strip().startswith(('Parameters', 'Returns', 'Raises', 'Notes', 
                                          'Examples', 'Attributes', 'See Also', 'Yields')):
            # Don't add blank line before parameter sections
            return match.group(0)
        
        # Check if this is a single-line docstring that was incorrectly matched
        if '\n' not in description:
            return match.group(0)
            
        # Add blank line between summary and description
        return f"{indent}{quotes}{summary}\n{desc_indent}\n{desc_indent}{description}{end}"
    
    # Apply the fix
    fixed_content = re.sub(pattern, add_blank_line, content, flags=re.MULTILINE | re.DOTALL)
    
    # Alternative pattern for multiline docstrings
    pattern2 = r'([ \t]*)("""|\'\'\')(.*?)(\n)([ \t]+)([A-Z].*?)(\n)'
    
    def add_blank_line2(match):
        indent = match.group(1)
        quotes = match.group(2)
        summary = match.group(3)
        newline = match.group(4)
        desc_indent = match.group(5)
        description = match.group(6)
        end = match.group(7)
        
        # Check if description starts with parameters or other sections
        if description.strip().startswith(('Parameters', 'Returns', 'Raises', 'Notes', 
                                          'Examples', 'Attributes', 'See Also', 'Yields')):
            return match.group(0)
        
        # Check if there's already a blank line (would have more indentation)
        if len(desc_indent) > len(indent):
            # Add blank line
            return f"{indent}{quotes}{summary}{newline}\n{desc_indent}{description}{end}"
        
        return match.group(0)
    
    fixed_content = re.sub(pattern2, add_blank_line2, fixed_content, flags=re.MULTILINE)
    
    # Write back only if changed
    if fixed_content != content:
        with open(filepath, 'w') as f:
            f.write(fixed_content)
        return True
    return False


def main():
    """Main function to fix D205 errors in all affected files."""
    files = [
        "solarwindpy/core/alfvenic_turbulence.py",
        "solarwindpy/core/plasma.py",
        "solarwindpy/fitfunctions/core.py",
        "solarwindpy/fitfunctions/gaussians.py",
        "solarwindpy/fitfunctions/lines.py",
        "solarwindpy/fitfunctions/plots.py",
        "solarwindpy/fitfunctions/tex_info.py",
        "solarwindpy/fitfunctions/trend_fits.py",
        "solarwindpy/instabilities/verscharen2016.py",
        "solarwindpy/plotting/agg_plot.py",
        "solarwindpy/plotting/base.py",
        "solarwindpy/plotting/hist1d.py",
        "solarwindpy/plotting/hist2d.py",
        "solarwindpy/plotting/labels/base.py",
        "solarwindpy/plotting/orbits.py",
        "solarwindpy/plotting/scatter.py",
        "solarwindpy/plotting/spiral.py",
        "solarwindpy/solar_activity/base.py",
        "solarwindpy/solar_activity/plots.py",
        "solarwindpy/solar_activity/sunspot_number/sidc.py",
    ]
    
    fixed_count = 0
    for filepath in files:
        if Path(filepath).exists():
            if fix_d205_in_file(filepath):
                print(f"Fixed: {filepath}")
                fixed_count += 1
        else:
            print(f"Not found: {filepath}")
    
    print(f"\nFixed {fixed_count} files")


if __name__ == "__main__":
    main()