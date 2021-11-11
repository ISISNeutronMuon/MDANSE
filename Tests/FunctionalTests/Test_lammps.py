#!C:\Users\dni83241\Documents\Virtualenvs\MDANSE\Scripts\python.exe

import numpy
import os
import shutil
import time
import unittest

from MDANSE import REGISTRY
from Scientific.IO.NetCDF import NetCDFFile
import Comparator

def compare(file1, file2):
    ret = True
    f = NetCDFFile(file1,"r")
    res1 = {}
    for k,v in f.variables.items():
        res1[k] = v.getValue()
    f.close()
    f = NetCDFFile(file2,"r")
    res2 = {}
    for k,v in f.variables.items():
        res2[k] = v.getValue()
    f.close()
    return Comparator.Comparator().compare(res1, res2)

class TestLAMMPS(unittest.TestCase):

    def test_lammps(self):
        parameters = {}
        parameters['config_file'] = '../../../Data/Trajectories/LAMMPS/glycyl_L_alanine_charmm.config'
        parameters['mass_tolerance'] = 0.001
        parameters['n_steps'] = 0
        parameters['output_files'] = ('c:/users/dni83241/appdata/local/temp/output', ['netcdf'])
        parameters['smart_mass_association'] = True
        parameters['time_step'] = 1.0
        parameters['trajectory_file'] = '../../../Data/Trajectories/LAMMPS/glycyl_L_alanine_charmm.lammps'
        job = REGISTRY['job']['lammps']()
        output_path = parameters["output_files"][0]
        reference_data_path = "C:/Users/dni83241/Documents/MDANSE/MDANSE/Data/Jobs_reference_data/lammps"
        print "Launching job in monoprocessor mode"
        parameters["running_mode"] = ("monoprocessor",1)
        job.run(parameters, status=False)
        shutil.copy(output_path + ".nc", reference_data_path + "_mono" + ".nc")
        print "Monoprocessor execution completed"

        print "Comparing monoprocessor output with reference output"
        self.assertTrue(compare("C:/Users/dni83241/Documents/MDANSE/MDANSE/Data/Jobs_reference_data/lammps_reference.nc", reference_data_path + "_mono" + ".nc"))

        try:
            os.remove(reference_data_path + "_mono" + ".nc")
        except OSError:
            pass


def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestLAMMPS))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
