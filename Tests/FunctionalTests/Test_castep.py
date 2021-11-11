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

class TestCASTEP(unittest.TestCase):

    def test_castep(self):
        parameters = {}
        parameters['castep_file'] = '../../../Data/Trajectories/CASTEP/PBAnew.md'
        parameters['output_files'] = ('c:/users/dni83241/appdata/local/temp/output', ['netcdf'])
        job = REGISTRY['job']['castep']()
        output_path = parameters["output_files"][0]
        reference_data_path = "C:/Users/dni83241/Documents/MDANSE/MDANSE/Data/Jobs_reference_data/castep"
        print "Launching job in monoprocessor mode"
        parameters["running_mode"] = ("monoprocessor",1)
        job.run(parameters, status=False)
        shutil.copy(output_path + ".nc", reference_data_path + "_mono" + ".nc")
        print "Monoprocessor execution completed"

        print "Comparing monoprocessor output with reference output"
        self.assertTrue(compare("C:/Users/dni83241/Documents/MDANSE/MDANSE/Data/Jobs_reference_data/castep_reference.nc", reference_data_path + "_mono" + ".nc"))

        try:
            os.remove(reference_data_path + "_mono" + ".nc")
        except OSError:
            pass

    def test_short_header(self):
        parameters = {}
        parameters['castep_file'] = '../../../Data/Trajectories/CASTEP/PBAnew_short.md'
        parameters['output_files'] = ('c:/users/dni83241/appdata/local/temp/output', ['netcdf'])
        job = REGISTRY['job']['castep']()
        output_path = parameters["output_files"][0]
        reference_data_path = "C:/Users/dni83241/Documents/MDANSE/MDANSE/Data/Jobs_reference_data/castep"
        print "Launching job in monoprocessor mode"
        parameters["running_mode"] = ("monoprocessor",1)
        job.run(parameters, status=False)
        shutil.copy(output_path + ".nc", reference_data_path + "_mono" + ".nc")
        print "Monoprocessor execution completed"

        print "Comparing monoprocessor output with reference output"
        self.assertTrue(compare("C:/Users/dni83241/Documents/MDANSE/MDANSE/Data/Jobs_reference_data/castep_reference.nc", reference_data_path + "_mono" + ".nc"))

        try:
            os.remove(reference_data_path + "_mono" + ".nc")
        except OSError:
            pass


def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestCASTEP))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
