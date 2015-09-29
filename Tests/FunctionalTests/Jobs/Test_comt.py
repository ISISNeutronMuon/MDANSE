#!/usr/bin/python

import unittest
from Tests.UnitTests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestCOMT(UnitTest):

    def test(self):
        parameters = {}
        parameters['atom_selection'] = 'all'
        parameters['frames'] = (0, 1, 1)
        parameters['grouping_level'] = 'atom'
        parameters['output_files'] = ('/tmp/output', ['netcdf'])
        parameters['trajectory'] = '../../../Data/Trajectories/MMTK/waterbox_in_periodic_universe.nc'
        job = REGISTRY['job']['comt']()
        self.assertNotRaises(job.run, parameters, status=False)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestCOMT))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
