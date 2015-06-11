#!/usr/bin/python

import unittest
from Tests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestGDISF(UnitTest):

    def test(self):
        parameters = {}
        parameters['atom_selection'] = 'all'
        parameters['frames'] = (0, 10, 1)
        parameters['grouping_level'] = 'atom'
        parameters['instrument_resolution'] = ('gaussian', {'mu': 0.0, 'sigma': 10.0})
        parameters['output_files'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
        parameters['projection'] = None
        parameters['q_shells'] = (0, 10, 1)
        parameters['running_mode'] = ('monoprocessor', 1)
        parameters['trajectory'] = '../../../Data/Trajectories/MMTK/waterbox_in_periodic_universe.nc'
        parameters['transmutated_atoms'] = None
        parameters['weights'] = 'b_incoherent'
        job = REGISTRY['job']['gdisf'](status=False)
        self.assertNotRaises(job.run, parameters)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestGDISF))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
