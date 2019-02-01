#! /bin/sh python
#  Licensed under a 3-clause BDS license. See LICENSE.md.

from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(
    name="solarwindpy",
    version="0.0.1",
    description="Python data analysis tools for solar wind measurements.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/blalterman/solarwindpy",
    author="B. L. Alterman",
    author_email="balterma@umich.edu",

    # Classifiers help users find your project by categorizing it.
    #
    # For a list of valid classifiers, see https://pypi.org/classifiers/
    classifiers=[  
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Stuff :: Stuff",
        "License :: OSI Approved :: BSD-3-Clause",
        "Programming Language :: Python :: 3.6",
    ],

    keywords=["plasma", "physics", "solar wind", "measurements"]

    #packages=find_packages(exclude=["contrib", "docs", "tests"]),  # Required
    
    python_requires=">=3.5, <4",
    install_requires=["numpy", "scipy", "pandas", "numexpr", "bottleneck", 
        "yaml", "pyyaml", "unittest"],  # Optional

    },

    # List additional URLs that are relevant to your project as a dict.
    #
    # This field corresponds to the "Project-URL" metadata fields:
    # https://packaging.python.org/specifications/core-metadata/#project-url-multiple-use
    #
    # Examples listed include a pattern for specifying where the package tracks
    # issues, where the source is hosted, where to say thanks to the package
    # maintainers, and where to support the project financially. The key is
    # what's used to render the link text on PyPI.
    project_urls={  # Optional
        "Bug Reports": "https://github.com/blalterman/solarwindpy/issues",
        "Source": "https://github.com/blalterman/solarwindpy/",
    },
)
