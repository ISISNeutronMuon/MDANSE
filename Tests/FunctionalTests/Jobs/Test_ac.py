#!/usr/bin/python

import unittest
from Tests.UnitTests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestAC(UnitTest):

    def test(self):
        parameters = {}
        parameters['axis_selection'] = ('Water', ('OW', 'HW'))
        parameters['frames'] = (0, 10, 1)
        parameters['output_files'] = ('output', ['netcdf'])
        parameters['per_axis'] = False
        parameters['running_mode'] = ('monoprocessor', 1)
        parameters['trajectory'] = '../../../Data/Trajectories/MMTK/waterbox_in_periodic_universe.nc'
        job = REGISTRY['job']['ac']()
        self.assertNotRaises(job.run, parameters, status=False)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestAC))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
