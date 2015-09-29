#!/usr/bin/python

import unittest
from Tests.UnitTests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestTEMP(UnitTest):

    def test(self):
        parameters = {}
        parameters['frames'] = (0, 10, 1)
        parameters['interpolation_order'] = 'no interpolation'
        parameters['output_files'] = ('/tmp/output', ['netcdf'])
        parameters['trajectory'] = '../../../Data/Trajectories/MMTK/waterbox_in_periodic_universe.nc'
        job = REGISTRY['job']['temp']()
        self.assertNotRaises(job.run, parameters, status=False)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestTEMP))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
