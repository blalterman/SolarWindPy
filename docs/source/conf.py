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

# numpydoc is the only docstring processor. Running napoleon beside it made
# both rewrite every docstring; napoleon's ``Attributes`` sections then emitted
# ``.. attribute::`` directives that collided with ``autoclass :members:``.
# ``docstring_inheritance`` is not listed: it is a runtime dependency
# (``fitfunctions/core.py`` uses its metaclass), not a Sphinx extension.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.coverage",  # `sphinx-build -b coverage`, run by docs CI
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "numpydoc",
    "sphinxcontrib.bibtex",
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

# -- NumPy doc configuration ------------------------------------------------

# Create toctree entries for class members (separate pages)
numpydoc_class_members_toctree = True
numpydoc_show_class_members = False  # Don't show on parent page
numpydoc_show_inherited_class_members = True  # Show inherited docstrings

# Link parameter and return types. numpydoc splits a type spec on whitespace,
# commas and "or", and wraps every token it does not ignore in :obj:.
numpydoc_xref_param_type = True

# Docstring type specs are written with the names the source imports: numpy,
# pandas and matplotlib under their conventional short names, and package
# modules under their import aliases (``from pandas import MultiIndex as MI``
# and ``from . import units_constants as uc`` in ``core/base.py``). Map each
# spelling to the fully qualified name that intersphinx or this build indexes.
# A spelling that is not an import the source uses belongs in the docstring.
numpydoc_xref_aliases = {
    "np.ndarray": "numpy.ndarray",
    "pd.DataFrame": "pandas.DataFrame",
    "pd.Series": "pandas.Series",
    "pd.Index": "pandas.Index",
    "pd.MultiIndex": "pandas.MultiIndex",
    "MI": "pandas.MultiIndex",
    "pd.DatetimeIndex": "pandas.DatetimeIndex",
    "pd.Timestamp": "pandas.Timestamp",
    "pd.Timedelta": "pandas.Timedelta",
    "pd.Interval": "pandas.Interval",
    "pd.IntervalIndex": "pandas.IntervalIndex",
    "pd.Categorical": "pandas.Categorical",
    "DataFrame": "pandas.DataFrame",
    "Series": "pandas.Series",
    "mpl.axes.Axes": "matplotlib.axes.Axes",
    "plt.Axes": "matplotlib.axes.Axes",
    "Axes": "matplotlib.axes.Axes",
    "mpl.axis.Axis": "matplotlib.axis.Axis",
    "mpl.collections.QuadMesh": "matplotlib.collections.QuadMesh",
    "QuadMesh": "matplotlib.collections.QuadMesh",
    "QuadContourSet": "matplotlib.contour.QuadContourSet",
    "colorbar.Colorbar": "matplotlib.colorbar.Colorbar",
    "Colorbar": "matplotlib.colorbar.Colorbar",
    "FunctionType": "types.FunctionType",
    "Path": "pathlib.Path",
    "uc.Units": "solarwindpy.core.units_constants.Units",
    "uc.Constants": "solarwindpy.core.units_constants.Constants",
    "vector.Vector": "solarwindpy.core.vector.Vector",
    "Ion": "solarwindpy.core.ions.Ion",
    "Spacecraft": "solarwindpy.core.spacecraft.Spacecraft",
}

# Words of numpydoc type-spec grammar ("array-like, optional", "list of str",
# "default False", "shape (N,)"). They qualify a type; they are not names, so
# linking them can only fail.
numpydoc_xref_ignore = {
    "optional",
    "default",
    "of",
    "or",
    "and",
    "shape",
    "length",
    "len",
    "type",
    "instance",
    "object",
    "objects",
    "like",
}

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
    'scipy': ('https://docs.scipy.org/doc/scipy/', None),
    'matplotlib': ('https://matplotlib.org/stable/', None),
}

# -- Nitpicky reference exceptions -------------------------------------------

# Each entry names a target that cannot resolve and says why. A reference that
# fails because a docstring is wrong is fixed in the docstring, not listed here.
nitpick_ignore = [
    # Base of fitfunctions.core.FitFunctionMeta. docstring-inheritance publishes
    # no Sphinx inventory: its documentation site returns 404 for objects.inv.
    ("py:class", "docstring_inheritance.NumpyDocstringInheritanceMeta"),
]

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