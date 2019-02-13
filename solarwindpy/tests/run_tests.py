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
import pdb  # noqa: F401
import unittest
import os

# def load_all_tests():
#     return unittest.TestLoader().discover(".", pattern="test_*.py")
# def load_plasma_and_related_tests():
#     suites = [unittest.TestLoader().discover(".", pattern="test_%s.py" % m)
#         for m in ["base", "quantities", "ions", "plasma", "alfvenic_turbulence"]]
#     testsuite = unittest.TestSuite(suites)
#     return testsuite


def load_tests(loader, standard_tests, pattern):

    # See https://docs.python.org/3/library/unittest.html#load-tests-protocol
    # for source.

    # top level directory cached on loader instance
    this_dir = os.path.dirname(__file__)
    package_tests = loader.discover(start_dir=this_dir, pattern="test_*.py")
    standard_tests.addTests(package_tests)
    return standard_tests


if __name__ == "__main__":

    # Just make recursion stacks smaller in Terminal.
    # Comment this line if it causes problems with other
    # tests or decrease the denominator.
    # sys.setrecursionlimit(sys.getrecursionlimit() // 10)

    verbose = 1
    unittest.main(verbosity=verbose)
