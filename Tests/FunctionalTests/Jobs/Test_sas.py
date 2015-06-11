#!/usr/bin/python

import unittest
from Tests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestSAS(UnitTest):

    def test(self):
        parameters = {}
        parameters['atom_selection'] = 'all'
        parameters['frames'] = (0, 2, 1)
        parameters['n_sphere_points'] = 1000
        parameters['output_files'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
        parameters['probe_radius'] = 0.14
        parameters['running_mode'] = ('monoprocessor', 1)
        parameters['trajectory'] = '../../../Data/Trajectories/MMTK/waterbox_in_periodic_universe.nc'
        job = REGISTRY['job']['sas'](status=False)
        self.assertNotRaises(job.run, parameters)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestSAS))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
