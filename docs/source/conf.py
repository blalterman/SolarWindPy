# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#

# -- Path setup --------------------------------------------------------------

import os
import sys

sys.path.insert(0, os.path.abspath("../.."))
import solarwindpy


# -- Project information -----------------------------------------------------

project = "SolarWindPy"
copyright = "2019, B. L. Alterman"
author = "B. L. Alterman"

# Dynamically fetch the package version
version = solarwindpy.__version__
release = version


# -- General configuration ---------------------------------------------------

needs_sphinx = "1.8"

# Extensions for clean documentation generation
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "numpydoc",
    "sphinxcontrib.bibtex",
    "docstring_inheritance",  # Enable docstring inheritance for fit functions
]

bibtex_bibfiles = ['solarwindpy.bib']

# -- Templates configuration ------------------------------------------------

templates_path = ['_templates']

# -- Autosummary configuration ----------------------------------------------

# Generate separate pages for everything
autosummary_generate = True
autosummary_imported_members = False
autosummary_generate_overwrite = True  # Allow regeneration with custom templates

# -- Autodoc configuration --------------------------------------------------

autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__',
    'inherited-members': True,  # Show inherited members in documentation
    'show-inheritance': True,  # Display inheritance relationships
}

# Don't prepend module names in titles
add_module_names = False

# -- Napoleon configuration -------------------------------------------------

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False

# -- NumPy doc configuration ------------------------------------------------

# Create toctree entries for class members (separate pages)
numpydoc_class_members_toctree = True
numpydoc_show_class_members = False  # Don't show on parent page
numpydoc_show_inherited_class_members = True  # Show inherited docstrings

# -- MathJax configuration ---------------------------------------------------

mathjax3_config = {
    'tex': {
        'inlineMath': [['$', '$'], ['\\(', '\\)']],
        'displayMath': [['$$', '$$'], ['\\[', '\\]']],
    },
}

# -- Intersphinx configuration -----------------------------------------------

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
    'matplotlib': ('https://matplotlib.org/stable/', None),
}

# -- HTML output configuration -----------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'navigation_depth': 4,
    'collapse_navigation': True,  # Cleaner initial view with expand/collapse
    'sticky_navigation': True,
    'includehidden': True,
    'titles_only': False,
    'prev_next_buttons_location': 'both',  # Navigation buttons top and bottom
    'style_nav_header_background': '#2980B9',  # Professional blue header
    'style_external_links': True,  # Mark external links with icon
}

# RTD-specific features and context
html_context = {
    'navigation_depth': 4,  # Workaround for Sphinx ≥6.0 navigation_depth bug
    'github_user': 'blalterman',
    'github_repo': 'SolarWindPy', 
    'github_version': 'master',
    'conf_py_path': '/docs/source/',
    'github_url': 'https://github.com/blalterman/SolarWindPy',
    'display_github': True,
    'commit': os.environ.get('READTHEDOCS_GIT_COMMIT_HASH', 'master'),
    'rtd_version': os.environ.get('READTHEDOCS_VERSION', 'latest'),
}

# Static files (CSS, JavaScript, images)
html_static_path = ['_static']

# Additional CSS files
html_css_files = [
    'custom.css',  # Custom scientific documentation styling
]

# Custom JavaScript files (for enhanced scientific features)
html_js_files = []

# RTD-specific configuration
# Enable version switching and downloads for RTD
if os.environ.get('READTHEDOCS'):
    html_context['versions'] = [('latest', '/en/latest/')]
    html_context['downloads'] = [('pdf', '/en/latest/_downloads/SolarWindPy.pdf')]
    
    # Analytics integration for RTD
    html_theme_options.update({
        'analytics_id': 'G-PLACEHOLDER',  # Replace with actual GA4 tracking ID
        'analytics_anonymize_ip': True,
    })

# Favicon configuration
html_favicon = '_static/favicon.ico'

# -- Options for other output formats ----------------------------------------

# PDF output configuration (enabled for RTD)
latex_engine = 'pdflatex'
latex_elements = {
    'papersize': 'letterpaper',
    'pointsize': '10pt',
    'preamble': r'''
        \usepackage{amsmath,amsfonts,amssymb}
        \usepackage{graphicx}
        \usepackage{hyperref}
        \usepackage[utf8]{inputenc}
    ''',
}

# EPUB output configuration (enabled for RTD)
epub_show_urls = 'footnote'
epub_use_index = True

# Grouping the document tree into LaTeX files
latex_documents = [
    ('index', 'SolarWindPy.tex', 'SolarWindPy Documentation',
     'B. L. Alterman', 'manual'),
]

# TeX files
texinfo_documents = [
    ('index', 'SolarWindPy', 'SolarWindPy Documentation',
     author, 'SolarWindPy', 'Solar wind analysis toolkit.',
     'Miscellaneous'),
]

# Epub
epub_title = project
epub_author = author
epub_publisher = author
epub_copyright = copyright