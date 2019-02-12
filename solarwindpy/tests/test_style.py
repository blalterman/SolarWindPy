#!/usr/bin/env python
"""
Name   : test_style.py
Author : B. L. Alterman
e-mail : balterma@umich.edu

Description
-----------
-Test pycodestyle and pydocstyle.

Propodes Updates
----------------
-

Notes
-----
-

"""

import pdb
import unittest
import pycodestyle as code
from unittest import TestCase
from pathlib import Path


class TestCodeStyle(TestCase):
    def test_conformance(self):
        """Test that we conform to PEP-8."""
        path = Path(__file__).resolve().parent.parent
        cfg_file = path.parent / "setup.cfg"
        source_files = [str(f) for f in path.rglob("*.py")]
        style = code.StyleGuide(config_file=cfg_file)
        result = style.check_files(source_files)
        self.assertEqual(result.total_errors, 0,
                         "Found code style errors (and warnings).")

if __name__ == "__main__":
    import sys

    # Just make recursion stacks smaller in Terminal.
    # Comment this line if it causes problems with other
    # tests or decrease the denominator.
    # sys.setrecursionlimit(sys.getrecursionlimit() // 10)

    try:
        run_this_test = "TestCodeStyle"
        run_this_test = None
        unittest.main(verbosity=2, defaultTest=run_this_test)

    except (AssertionError, AttributeError, ValueError, TypeError, IndexError) as e:
        import sys
        import traceback as tb

        exc_info = sys.exc_info()
        tb.print_exception(*exc_info)
        pdb.post_mortem(exc_info[-1])

