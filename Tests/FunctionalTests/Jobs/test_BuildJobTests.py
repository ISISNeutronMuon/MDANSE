# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Tests/FunctionalTests/Jobs/test_BuildJobTests.py
# @brief     Implements module/class/test test_BuildJobTests
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************
"""
A test suite for testing BuildJobTests.py. It ensures that a test file is created in the correct directory with the
correct name by using a test double. However, it does not test if the content of the created file itself is correct.
"""

import unittest
import os
from BuildJobTests import JobFileGenerator


class JobForTest:
    """A test double used as a substitute for an actual MDANSE job class."""
    settings = {}
    configuration = {"output_files": {"files": ["./File.nc"]}}
    _type = 'Test'
    
    def set_multi_processor(self):
        self.settings = {'running_mode': True}
    
    def set_mono_processor(self):
        self.settings = {}
        
    def get_default_parameters(self):
        return {}


class TestBuildJobTests(unittest.TestCase):
    def test(self):
        temp = os.path.join(os.path.split(__file__)[0], "Test_Test.py")
        self.job = JobForTest()
        self.object = JobFileGenerator(self.job)
        self.assertTrue(os.path.isfile(temp))
        os.remove(temp)
        self.job.set_multi_processor()
        self.object = JobFileGenerator(self.job)
        self.assertTrue(os.path.isfile(temp))
        os.remove(temp)


def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestBuildJobTests))
    return s


if __name__ == '__main__':
    unittest.main(verbosity=2)
