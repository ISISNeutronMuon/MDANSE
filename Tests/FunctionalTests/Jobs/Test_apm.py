#!/usr/bin/python

import unittest
from Tests.UnitTests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestAPM(UnitTest):

    def test(self):
        parameters = {}
        parameters['axis'] = ['a', 'b']
        parameters['frames'] = (0, 10, 1)
        parameters['name'] = 'DMPC'
        parameters['output_files'] = ('output', ['netcdf'])
        parameters['running_mode'] = ('monoprocessor', 1)
        parameters['trajectory'] = '../../../Data/Trajectories/MMTK/dmpc_in_periodic_universe.nc'
        job = REGISTRY['job']['apm']()
        self.assertNotRaises(job.run, parameters, status=False)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestAPM))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
