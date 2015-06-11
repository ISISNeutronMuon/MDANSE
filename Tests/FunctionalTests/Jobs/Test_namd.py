#!/usr/bin/python

import unittest
from Tests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestNAMD(UnitTest):

    def test(self):
        parameters = {}
        parameters['dcd_file'] = '../../../Data/Trajectories/CHARMM/2vb1.dcd'
        parameters['fold'] = False
        parameters['output_file'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
        parameters['pdb_file'] = '../../../Data/Trajectories/CHARMM/2vb1.pdb'
        job = REGISTRY['job']['namd'](status=False)
        self.assertNotRaises(job.run, parameters)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestNAMD))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
