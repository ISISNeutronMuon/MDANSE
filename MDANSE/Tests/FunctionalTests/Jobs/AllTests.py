# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Tests/FunctionalTests/Jobs/AllTests.py
# @brief     Implements module/class/test AllTests
#
# @homepage https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import unittest
import os
import sys
import glob


def suite():
    files = glob.glob("Test*.py")
    modules = [
        __import__(os.path.splitext(f)[0], globals(), locals(), [], 0) for f in files
    ]
    test_suite = unittest.TestSuite()
    for m in modules:
        print(m.__file__)
        test_suite.addTests(m.suite())
    return test_suite


def run_test():
    if not unittest.TextTestRunner(verbosity=2).run(suite()).wasSuccessful():
        sys.exit(1)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    run_test()
