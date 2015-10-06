#!/usr/bin/python

import unittest
from Tests.UnitTests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestXSSF(UnitTest):

    def test(self):
        parameters = {}
        parameters['atom_selection'] = 'all'
        parameters['atom_transmutation'] = None
        parameters['frames'] = (0, 10, 1)
        parameters['output_files'] = ('/tmp/output', ['netcdf'])
        parameters['q_values'] = (0, 10, 1)
        parameters['r_values'] = (0, 10, 1)
        parameters['running_mode'] = ('monoprocessor', 1)
        parameters['trajectory'] = '../../../Data/Trajectories/MMTK/waterbox_in_periodic_universe.nc'
        job = REGISTRY['job']['xssf']()
        self.assertNotRaises(job.run, parameters, status=False)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestXSSF))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
