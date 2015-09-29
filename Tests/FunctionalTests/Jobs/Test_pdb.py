#!/usr/bin/python

import unittest
from Tests.UnitTests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestPDB(UnitTest):

    def test(self):
        parameters = {}
        parameters['nb_frame'] = (0, 2, 1)
        parameters['output_file'] = ('/tmp/output', ['netcdf'])
        parameters['pdb_file'] = '../../../Data/Trajectories/PDB/2f58_nma.pdb'
        parameters['time_step'] = 1.0
        job = REGISTRY['job']['pdb']()
        self.assertNotRaises(job.run, parameters, status=False)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestPDB))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
