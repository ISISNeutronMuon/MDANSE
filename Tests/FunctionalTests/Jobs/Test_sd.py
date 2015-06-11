#!/usr/bin/python

import unittest
from Tests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestSD(UnitTest):

    def test(self):
        parameters = {}
        parameters['frames'] = (0, 10, 1)
        parameters['output_files'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
        parameters['reference_basis'] = {'origin': ('O',), 'y_axis': ('C_delta',), 'x_axis': ('C_beta',), 'molecule': 'C284H438N84O79S7'}
        parameters['running_mode'] = ('monoprocessor', 1)
        parameters['spatial_resolution'] = 0.1
        parameters['target_molecule'] = 'atom_index 151'
        parameters['trajectory'] = '../../../Data/Trajectories/MMTK/protein_in_periodic_universe.nc'
        job = REGISTRY['job']['sd'](status=False)
        self.assertNotRaises(job.run, parameters)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestSD))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
