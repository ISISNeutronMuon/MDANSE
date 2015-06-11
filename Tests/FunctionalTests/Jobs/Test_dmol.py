#!/usr/bin/python

import unittest
from Tests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestDMOL(UnitTest):

    def test(self):
        parameters = {}
        parameters['his_file'] = '../../../Data/Trajectories/Discover/sushi.his'
        parameters['output_file'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
        parameters['xtd_file'] = '../../../Data/Trajectories/Discover/sushi.xtd'
        job = REGISTRY['job']['dmol'](status=False)
        self.assertNotRaises(job.run, parameters)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestDMOL))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
