#!/usr/bin/python

import unittest
from Tests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestFORCITE(UnitTest):

    def test(self):
        parameters = {}
        parameters['output_file'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
        parameters['trj_file'] = '../../../Data/Trajectories/Forcite/nylon66_rho100_500K_v300K.trj'
        parameters['xtd_file'] = '../../../Data/Trajectories/Forcite/nylon66_rho100_500K_v300K.xtd'
        job = REGISTRY['job']['forcite'](status=False)
        self.assertNotRaises(job.run, parameters)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestFORCITE))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
