#!/usr/bin/python

import unittest
from Tests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestCASTEP(UnitTest):

    def test(self):
        parameters = {}
        parameters['castep_file'] = '../../../Data/Trajectories/CASTEP/PBAnew.md'
        parameters['output_file'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
        job = REGISTRY['job']['castep'](status=False)
        self.assertNotRaises(job.run, parameters)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestCASTEP))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
