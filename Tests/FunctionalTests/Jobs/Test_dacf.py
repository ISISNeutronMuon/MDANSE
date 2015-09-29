#!/usr/bin/python

import unittest
from Tests.UnitTests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestDACF(UnitTest):

    def test(self):
        parameters = {}
        parameters['atom_charges'] = {0: 0.5, 1: 1.2, 2: -0.2}
        parameters['atom_selection'] = 'atom_index 0,1,2'
        parameters['frames'] = (0, 10, 1)
        parameters['output_files'] = ('/tmp/output', ['netcdf'])
        parameters['running_mode'] = ('monoprocessor', 1)
        parameters['trajectory'] = '../../../Data/Trajectories/MMTK/waterbox_in_periodic_universe.nc'
        job = REGISTRY['job']['dacf']()
        self.assertNotRaises(job.run, parameters, status=False)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestDACF))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
