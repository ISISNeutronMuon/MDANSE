#!/usr/bin/python

import unittest
from Tests.UnitTests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestVASP(UnitTest):

    def test(self):
        parameters = {}
        parameters['output_file'] = ('/tmp/output', ['netcdf'])
        parameters['time_step'] = 1.0
        parameters['xdatcar_file'] = '../../../Data/Trajectories/VASP/XDATCAR_version5'
        job = REGISTRY['job']['vasp']()
        self.assertNotRaises(job.run, parameters, status=False)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestVASP))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
