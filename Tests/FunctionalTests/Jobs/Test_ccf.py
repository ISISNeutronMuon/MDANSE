#!/usr/bin/python

import unittest
from Tests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestCCF(UnitTest):

    def test(self):
        parameters = {}
        parameters['atom_selection'] = 'all'
        parameters['frames'] = (0, 10, 1)
        parameters['instrument_resolution'] = ('gaussian', {'mu': 0.0, 'sigma': 10.0})
        parameters['normalize'] = False
        parameters['output_files'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
        parameters['q_vectors'] = ('spherical_lattice', {'width': 0.1, 'n_vectors': 50, 'shells': (0, 5, 0.1)})
        parameters['running_mode'] = ('monoprocessor', 1)
        parameters['trajectory'] = '../../../Data/Trajectories/MMTK/waterbox_in_periodic_universe.nc'
        parameters['transmutated_atoms'] = None
        parameters['weights'] = 'b_coherent'
        job = REGISTRY['job']['ccf'](status=False)
        self.assertNotRaises(job.run, parameters)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestCCF))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
