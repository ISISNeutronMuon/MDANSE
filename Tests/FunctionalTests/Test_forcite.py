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

class TestFORCITE(unittest.TestCase):

    def test_forcite(self):
        parameters = {}
        parameters['output_files'] = ('c:/users/dni83241/appdata/local/temp/output', ['netcdf'])
        parameters['trj_file'] = '../../../Data/Trajectories/Forcite/nylon66_rho100_500K_v300K.trj'
        parameters['xtd_file'] = '../../../Data/Trajectories/Forcite/nylon66_rho100_500K_v300K.xtd'
        job = REGISTRY['job']['forcite']()
        output_path = parameters["output_files"][0]
        reference_data_path = "C:/Users/dni83241/Documents/MDANSE/MDANSE/Data/Jobs_reference_data/forcite"
        print "Launching job in monoprocessor mode"
        parameters["running_mode"] = ("monoprocessor",1)
        job.run(parameters, status=False)
        shutil.copy(output_path + ".nc", reference_data_path + "_mono" + ".nc")
        print "Monoprocessor execution completed"

        print "Comparing monoprocessor output with reference output"
        self.assertTrue(compare("C:/Users/dni83241/Documents/MDANSE/MDANSE/Data/Jobs_reference_data/forcite_reference.nc", reference_data_path + "_mono" + ".nc"))

        try:
            os.remove(reference_data_path + "_mono" + ".nc")
        except OSError:
            pass


def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestFORCITE))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
