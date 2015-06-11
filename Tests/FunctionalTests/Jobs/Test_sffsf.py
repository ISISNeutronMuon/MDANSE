#!/usr/bin/python

import unittest
from Tests.UnitTest import UnitTest
from MDANSE import REGISTRY

class TestSFFSF(UnitTest):

    def test(self):
        parameters = {}
        parameters['instrument_resolution'] = ('gaussian', {'mu': 0.0, 'sigma': 10.0})
        parameters['netcdf_input_file'] = '../../../Data/NetCDF/disf_prot.nc'
        parameters['output_files'] = ('/users/pellegrini/workspace/MDANSE/Tests/FunctionalTests/Jobs', 'output', ['netcdf'])
        job = REGISTRY['job']['sffsf'](status=False)
        self.assertNotRaises(job.run, parameters)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestSFFSF))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
