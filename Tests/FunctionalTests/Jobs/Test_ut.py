#!/usr/bin/python

import unittest
from Tests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestUT(UnitTest):

    def test(self):
        parameters = {}
        parameters['atom_selection'] = 'all'
        parameters['frames'] = (0, 10, 1)
        parameters['output_files'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
        parameters['trajectory'] = '../../../Data/Trajectories/MMTK/waterbox_in_periodic_universe.nc'
        job = REGISTRY['job']['ut'](status=False)
        self.assertNotRaises(job.run, parameters)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestUT))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
