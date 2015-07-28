#!/usr/bin/python

import unittest
from Tests.UnitTests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestOP(UnitTest):

    def test(self):
        parameters = {}
        parameters['axis_selection'] = ('C284H438N84O79S7', ('C', 'C_beta'))
        parameters['frames'] = (0, 10, 1)
        parameters['output_files'] = ('output', ['netcdf'])
        parameters['per_axis'] = False
        parameters['reference_direction'] = [0, 0, 1]
        parameters['running_mode'] = ('monoprocessor', 1)
        parameters['trajectory'] = '../../../Data/Trajectories/MMTK/protein_in_periodic_universe.nc'
        job = REGISTRY['job']['op']()
        self.assertNotRaises(job.run, parameters, status=False)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestOP))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
