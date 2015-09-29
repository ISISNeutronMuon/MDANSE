#!/usr/bin/python

import unittest
from Tests.UnitTests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestROG(UnitTest):

    def test(self):
        parameters = {}
        parameters['atom_selection'] = 'all'
        parameters['frames'] = (0, 10, 1)
        parameters['output_files'] = ('/tmp/output', ['netcdf'])
        parameters['running_mode'] = ('monoprocessor', 1)
        parameters['trajectory'] = '../../../Data/Trajectories/MMTK/waterbox_in_periodic_universe.nc'
        parameters['weights'] = 'equal'
        job = REGISTRY['job']['rog']()
        self.assertNotRaises(job.run, parameters, status=False)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestROG))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
