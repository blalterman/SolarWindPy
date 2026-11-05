# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#

# -- Path setup --------------------------------------------------------------

import os
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath("../../src"))
import solarwindpy

# A plot block in the Usage guide loads SIDC("m13"), which downloads from
# SILSO. Serve it from the committed snapshot through a private download cache,
# so the build needs no network and leaves the user's own cache alone.
import atexit
import shutil
import tempfile

sys.path.insert(0, os.path.abspath("."))
from _ssn_snapshot import seed_ssn_snapshot

_ssn_cache = tempfile.mkdtemp(prefix="solarwindpy-docs-cache-")
atexit.register(shutil.rmtree, _ssn_cache, ignore_errors=True)
seed_ssn_snapshot(_ssn_cache, os.environ.__setitem__)


# -- Project information -----------------------------------------------------

project = "SolarWindPy"
copyright = "2019, B. L. Alterman"
author = "B. L. Alterman"

# Dynamically fetch the package version
version = solarwindpy.__version__
release = version


# -- General configuration ---------------------------------------------------

needs_sphinx = "7.0"  # the docs extra's floor, sphinx>=7.0 in pyproject.toml

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
    "matplotlib.sphinxext.plot_directive",
    "sphinx_copybutton",
]

bibtex_bibfiles = ['solarwindpy.bib']

# -- Copy button configuration ---------------------------------------------

# Copy doctest examples without their ``>>> `` and ``... `` prompts, so a
# reader can paste them into a session.
copybutton_prompt_text = r">>> |\.\.\. "
copybutton_prompt_is_regexp = True

# -- Plot directive configuration -------------------------------------------

# Every figure in the guide is drawn by the code shown with it, and that code
# must run on its own when pasted into a fresh session: no hidden setup code
# (the default would import numpy and pyplot), one PNG per figure, and the
# package's style, which the directive's per-figure reset would otherwise
# discard after the first import of solarwindpy.plotting.
import matplotlib  # noqa: E402

plot_include_source = True
plot_pre_code = ""
plot_formats = [("png", 100)]
plot_html_show_formats = False
plot_html_show_source_link = False
plot_rcparams = dict(
    matplotlib.rc_params_from_file(
        os.path.join(
            os.path.dirname(solarwindpy.__file__), "plotting", "solarwindpy.mplstyle"
        ),
        use_default_template=False,
    )
)

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
# modules under the names the source imports them by
# (``from . import units_constants`` in ``core/base.py``). Map each spelling to
# the fully qualified name that intersphinx or this build indexes.
# A spelling that is not an import the source uses belongs in the docstring.
numpydoc_xref_aliases = {
    "np.ndarray": "numpy.ndarray",
    "pd.DataFrame": "pandas.DataFrame",
    "pd.Series": "pandas.Series",
    "pd.Index": "pandas.Index",
    "pd.MultiIndex": "pandas.MultiIndex",
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
    "mpl.collections.PathCollection": "matplotlib.collections.PathCollection",
    "mpl.collections.PolyCollection": "matplotlib.collections.PolyCollection",
    "mpl.collections.LineCollection": "matplotlib.collections.LineCollection",
    "mpl.container.ErrorbarContainer": "matplotlib.container.ErrorbarContainer",
    "mpl.lines.Line2D": "matplotlib.lines.Line2D",
    "mpl.colorbar.Colorbar": "matplotlib.colorbar.Colorbar",
    "QuadMesh": "matplotlib.collections.QuadMesh",
    "QuadContourSet": "matplotlib.contour.QuadContourSet",
    "TriContourSet": "matplotlib.tri.TriContourSet",
    "colorbar.Colorbar": "matplotlib.colorbar.Colorbar",
    "Colorbar": "matplotlib.colorbar.Colorbar",
    "FunctionType": "types.FunctionType",
    "Path": "pathlib.Path",
    "units_constants.Units": "solarwindpy.core.units_constants.Units",
    "units_constants.Constants": "solarwindpy.core.units_constants.Constants",
    "vector.Vector": "solarwindpy.core.vector.Vector",
    "Ion": "solarwindpy.core.ions.Ion",
    "Spacecraft": "solarwindpy.core.spacecraft.Spacecraft",
    "BinnedData": "solarwindpy.plotting.binned.BinnedData",
}

# Words of numpydoc type-spec grammar ("array-like, optional", "list of str",
# "dict of str to bool", "default False", "shape (N,)"). They qualify a type;
# they are not names, so linking them can only fail.
numpydoc_xref_ignore = {
    "optional",
    "default",
    "of",
    "to",
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
    # 3.x defines the class in its private ``_internal`` module.
    ("py:class", "docstring_inheritance._internal.NumpyDocstringInheritanceInitMeta"),
    # Private mixin base of plotting.hist1d.Hist1D and hist2d.Hist2D.
    # Private names are not documented, so the show-inheritance line cannot
    # link it.
    ("py:class", "solarwindpy.plotting.base._OnFixedGrid"),
    # Private base holding ``alim`` for plotting.base.ColorPlot and BinnedPlot,
    # named on their show-inheritance line for the same reason.
    ("py:class", "solarwindpy.plotting.base._AggregateLimits"),
    # Private base of core.vector.Vector and core.tensor.Tensor, named on
    # their show-inheritance line for the same reason.
    ("py:class", "solarwindpy.core.base._ComponentFrame"),
    # Private types that public signatures take or return. Their docstrings
    # name the real type; private names are not documented, so the name
    # cannot link.
    ("py:obj", "solarwindpy.plotting.binned._PlotSource"),
    ("py:obj", "solarwindpy.fitfunctions.core._ChisqPerDegreeOfFreedom"),
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

# PDF output configuration
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

# EPUB output configuration
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


# -- API page titles ---------------------------------------------------------

# The autosummary templates title each API page by its short name (``Plasma``,
# ``hist1d``). Where two pages would share a title, such as the ``base``
# modules of ``core`` and ``plotting``, each of them is titled by its path
# below the package instead (``core.base``, ``plotting.base``), so a title
# alone names one object. The pages are the public modules and the public
# objects each defines; ``repeated_titles`` holds the full names of those whose
# short name another shares, and the templates read it.
def _repeated_api_titles():
    import importlib
    import inspect
    import pkgutil

    full_names = []
    for info in pkgutil.walk_packages(solarwindpy.__path__, "solarwindpy."):
        if any(part.startswith("_") for part in info.name.split(".")):
            continue
        module = importlib.import_module(info.name)
        full_names.append(info.name)
        for name, obj in vars(module).items():
            public = not name.startswith("_")
            documented = inspect.isclass(obj) or inspect.isfunction(obj)
            if public and documented and obj.__module__ == info.name:
                full_names.append(f"{info.name}.{name}")
    counts = Counter(name.rsplit(".", 1)[-1] for name in full_names)
    return sorted(name for name in full_names if counts[name.rsplit(".", 1)[-1]] > 1)


autosummary_context = {"repeated_titles": _repeated_api_titles()}
