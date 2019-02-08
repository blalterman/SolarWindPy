#!/usr/bin/env python
"""
Name   : run_tests.py
Author : B. L. Alterman
e-mail : balterma@umich.edu

Description
-----------
-Run test suite.

Propodes Updates
----------------
-

Notes
-----
-

"""

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import pdb
import unittest


def load_all_tests():
    return unittest.TestLoader().discover(".", pattern="test_*.py")
def load_plasma_and_related_tests():
    suites = [unittest.TestLoader().discover(".", pattern="test_%s.py" % m)
        for m in ["base", "quantities", "ions", "plasma", "alfvenic_turbulence"]]
    testsuite = unittest.TestSuite(suites)
    return testsuite

if __name__ == "__main__":
    import sys

    # Just make recursion stacks smaller in Terminal.
    # Comment this line if it causes problems with other
    # tests or decrease the denominator.
    # sys.setrecursionlimit(sys.getrecursionlimit() // 10)

#     try:
    verbose = 0
    testsuite = load_plasma_and_related_tests()
    unittest.TextTestRunner(verbosity=verbose).run(testsuite)

#     except (AssertionError, AttributeError, ValueError, TypeError, IndexError) as e:
#         import sys
#         import traceback as tb

#         exc_info = sys.exc_info()
#         tb.print_exception(*exc_info)
#         pdb.post_mortem(exc_info[-1])
