#!/usr/bin/python

import unittest
from Tests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestDL_POLY(UnitTest):

    def test(self):
        parameters = {}
        parameters['atom_aliases'] = {}
        parameters['field_file'] = '../../../Data/Trajectories/DL_Poly/FIELD_cumen'
        parameters['history_file'] = '../../../Data/Trajectories/DL_Poly/HISTORY_cumen'
        parameters['output_file'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
        parameters['version'] = '2'
        job = REGISTRY['job']['dl_poly'](status=False)
        self.assertNotRaises(job.run, parameters)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestDL_POLY))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
