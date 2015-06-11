#!/usr/bin/python

import unittest
from Tests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestLAMMPS(UnitTest):

    def test(self):
        parameters = {}
        parameters['config_file'] = '../../../Data/Trajectories/LAMMPS/glycyl_L_alanine_charmm.config'
        parameters['n_steps'] = 1
        parameters['output_file'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
        parameters['time_step'] = 1.0
        parameters['trajectory_file'] = '../../../Data/Trajectories/LAMMPS/glycyl_L_alanine_charmm.lammps'
        job = REGISTRY['job']['lammps'](status=False)
        self.assertNotRaises(job.run, parameters)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestLAMMPS))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
