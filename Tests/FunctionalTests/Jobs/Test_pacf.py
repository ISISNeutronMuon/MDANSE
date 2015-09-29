#!/usr/bin/python

import unittest
from Tests.UnitTests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestPACF(UnitTest):

    def test(self):
        parameters = {}
        parameters['atom_selection'] = 'all'
        parameters['frames'] = (0, 10, 1)
        parameters['grouping_level'] = 'atom'
        parameters['normalize'] = False
        parameters['output_files'] = ('/tmp/output', ['netcdf'])
        parameters['projection'] = None
        parameters['running_mode'] = ('monoprocessor', 1)
        parameters['trajectory'] = '../../../Data/Trajectories/MMTK/waterbox_in_periodic_universe.nc'
        parameters['transmutated_atoms'] = None
        parameters['weights'] = 'equal'
        job = REGISTRY['job']['pacf']()
        self.assertNotRaises(job.run, parameters, status=False)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestPACF))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
