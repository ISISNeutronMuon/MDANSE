#!/usr/bin/python

import unittest
from Tests.UnitTests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestMVI(UnitTest):

    def test(self):
        parameters = {}
        parameters['display'] = False
        parameters['frames'] = (0, 10, 1)
        parameters['instrument'] = '../../../Data/McStas/Instruments/Simple_ToF_Flat_Sample.out'
        parameters['options'] = {'ncount': 10000, 'dir': '/tmp/mdanse_mcstas_ZJtYbd'}
        parameters['output_files'] = ('output', ['netcdf'])
        parameters['parameters'] = {'beam_wavelength_Angs': 2.0, 'container_thickness_m': 5e-05, 'environment_radius_m': 0.025, 'sample_detector_distance_m': 4.0, 'container': '/users/pellegrini/workspace/MDANSE/Data/McStas/Samples/Al.laz', 'environment_thickness_m': 0.002, 'detector_height_m': 3.0, 'beam_resolution_meV': 0.1, 'sample_height_m': 0.05, 'sample_thickness_m': 0.001, 'environment': '/users/pellegrini/workspace/MDANSE/Data/McStas/Samples/Al.laz', 'sample_width_m': 0.02, 'sample_rotation_deg': 45.0}
        parameters['sample_coh'] = '../../../Data/NetCDF/dcsf_prot.nc'
        parameters['sample_inc'] = '../../../Data/NetCDF/disf_prot.nc'
        parameters['temperature'] = 298.0
        parameters['trajectory'] = '../../../Data/Trajectories/MMTK/protein_in_periodic_universe.nc'
        job = REGISTRY['job']['mvi']()
        self.assertNotRaises(job.run, parameters, status=False)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestMVI))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
