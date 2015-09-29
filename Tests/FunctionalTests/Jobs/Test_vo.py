#!/usr/bin/python

import unittest
from Tests.UnitTests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestVO(UnitTest):

    def test(self):
        parameters = {}
        parameters['atom_selection'] = 'all'
        parameters['frames'] = (0, 5, 1)
        parameters['output_files'] = ('/tmp/output', ['netcdf'])
        parameters['pbc'] = True
        parameters['pbc_border_size'] = 0.0
        parameters['trajectory'] = '../../../Data/Trajectories/MMTK/waterbox_in_periodic_universe.nc'
        job = REGISTRY['job']['vo']()
        self.assertNotRaises(job.run, parameters, status=False)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestVO))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
