#!/usr/bin/python

import unittest
from Tests.UnitTests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestRMT(UnitTest):

    def test(self):
        parameters = {}
        parameters['axis'] = 'c'
        parameters['frames'] = (0, 10, 1)
        parameters['lower_leaflet'] = 'DMPC'
        parameters['output_files'] = ('output', ['netcdf'])
        parameters['trajectory'] = '../../../Data/Trajectories/MMTK/dmpc_in_periodic_universe.nc'
        parameters['upper_leaflet'] = 'DMPC'
        job = REGISTRY['job']['rmt']()
        self.assertNotRaises(job.run, parameters, status=False)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestRMT))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
