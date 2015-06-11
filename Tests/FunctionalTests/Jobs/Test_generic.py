#!/usr/bin/python

import unittest
from Tests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestGENERIC(UnitTest):

    def test(self):
        parameters = {}
        parameters['gt_file'] = '../../../Data/Trajectories/Generic/test.gtf'
        parameters['output_file'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
        job = REGISTRY['job']['generic'](status=False)
        self.assertNotRaises(job.run, parameters)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestGENERIC))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
