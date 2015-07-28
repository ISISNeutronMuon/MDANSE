#!/usr/bin/python

import unittest
from Tests.UnitTests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestDMOL(UnitTest):

    def test(self):
        parameters = {}
        parameters['his_file'] = '../../../Data/Trajectories/Discover/sushi.his'
        parameters['output_file'] = ('output', ['netcdf'])
        parameters['xtd_file'] = '../../../Data/Trajectories/Discover/sushi.xtd'
        job = REGISTRY['job']['dmol']()
        self.assertNotRaises(job.run, parameters, status=False)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestDMOL))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
