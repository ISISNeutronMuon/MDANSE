#!/usr/bin/python

import unittest
from Tests.UnitTests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestDISCOVER(UnitTest):

    def test(self):
        parameters = {}
        parameters['his_file'] = '../../../Data/Trajectories/Discover/sushi.his'
        parameters['output_file'] = ('/tmp/output', ['netcdf'])
        parameters['xtd_file'] = '../../../Data/Trajectories/Discover/sushi.xtd'
        job = REGISTRY['job']['discover']()
        self.assertNotRaises(job.run, parameters, status=False)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestDISCOVER))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
