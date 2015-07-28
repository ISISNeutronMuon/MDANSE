#!/usr/bin/python

import unittest
from Tests.UnitTests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestRBT(UnitTest):

    def test(self):
        parameters = {}
        parameters['atom_selection'] = 'all'
        parameters['frames'] = (0, 10, 1)
        parameters['grouping_level'] = 'atom'
        parameters['output_files'] = ('output', ['netcdf'])
        parameters['reference'] = 0
        parameters['remove_translation'] = False
        parameters['running_mode'] = ('monoprocessor', 1)
        parameters['stepwise'] = True
        parameters['trajectory'] = '../../../Data/Trajectories/MMTK/waterbox_in_periodic_universe.nc'
        job = REGISTRY['job']['rbt']()
        self.assertNotRaises(job.run, parameters, status=False)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestRBT))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
