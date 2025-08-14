#!/usr/bin/env python3
"""
Script to automatically add :no-index: to module RST files to prevent duplicate warnings.
This runs after sphinx-apidoc generates the API documentation.
"""

import os
import glob
import re

def add_no_index_to_modules():
    """Add :no-index: to all module RST files (not package files)."""
    
    api_dir = "source/api"
    
    # Find all module RST files (exclude package files and modules.rst)
    pattern = os.path.join(api_dir, "*.rst")
    rst_files = glob.glob(pattern)
    
    modified_count = 0
    
    for rst_file in rst_files:
        if os.path.basename(rst_file) == "modules.rst":
            continue
            
        with open(rst_file, 'r') as f:
            content = f.read()
        
        # Check if this has automodule directive
        if ".. automodule::" in content:
            # Check if :no-index: is already present
            if ":no-index:" not in content:
                # Add :no-index: after the automodule directive
                pattern = r'(\.\. automodule:: [^\n]+\n   :members:\n   :show-inheritance:\n   :undoc-members:)'
                replacement = r'\1\n   :no-index:'
                
                new_content = re.sub(pattern, replacement, content)
                
                if new_content != content:
                    with open(rst_file, 'w') as f:
                        f.write(new_content)
                    modified_count += 1
                    print(f"Added :no-index: to {rst_file}")
    
    print(f"Modified {modified_count} module files")

if __name__ == "__main__":
    add_no_index_to_modules()