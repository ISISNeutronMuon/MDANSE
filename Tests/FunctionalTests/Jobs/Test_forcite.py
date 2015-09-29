#!/usr/bin/python

import unittest
from Tests.UnitTests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestFORCITE(UnitTest):

    def test(self):
        parameters = {}
        parameters['output_file'] = ('/tmp/output', ['netcdf'])
        parameters['trj_file'] = '../../../Data/Trajectories/Forcite/nylon66_rho100_500K_v300K.trj'
        parameters['xtd_file'] = '../../../Data/Trajectories/Forcite/nylon66_rho100_500K_v300K.xtd'
        job = REGISTRY['job']['forcite']()
        self.assertNotRaises(job.run, parameters, status=False)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestFORCITE))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
