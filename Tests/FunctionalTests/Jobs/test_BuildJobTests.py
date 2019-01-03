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
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import unittest
import os
from BuildJobTests import JobFileGenerator

class JobForTest():
    settings = {}
    configuration = {"output_files":{"files":["./File.nc"]}}
    _type = 'Test'
    
    def set_multi_processor(self):
        self.settings = {'running_mode':True}
    
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
        
if __name__ == '__main__':
    unittest.main(verbosity=2)