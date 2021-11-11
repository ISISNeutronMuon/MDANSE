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

class TestDACF(unittest.TestCase):

    def test_dacf(self):
        parameters = {}
        parameters['atom_charges'] = {0: 0.5, 1: 1.2, 2: -0.2}
        parameters['atom_selection'] = 'atom_index 0,1,2'
        parameters['frames'] = (0, 10, 1)
        parameters['output_files'] = ('c:/users/dni83241/appdata/local/temp/output', ['netcdf'])
        parameters['running_mode'] = ('monoprocessor', 1)
        parameters['trajectory'] = '../../../Data/Trajectories/MMTK/waterbox_in_periodic_universe.nc'
        job = REGISTRY['job']['dacf']()
        output_path = parameters["output_files"][0]
        reference_data_path = "C:/Users/dni83241/Documents/MDANSE/MDANSE/Data/Jobs_reference_data/dacf"
        print "Launching job in monoprocessor mode"
        parameters["running_mode"] = ("monoprocessor",1)
        job.run(parameters, status=False)
        shutil.copy(output_path + ".nc", reference_data_path + "_mono" + ".nc")
        print "Monoprocessor execution completed"

        print "Launching job in multiprocessor mode"
        parameters["running_mode"] = ("multiprocessor",2)
        job.run(parameters,False)
        shutil.copy(output_path + ".nc", reference_data_path + "_multi" + ".nc")
        print "Multiprocessor execution completed"

        print "Comparing monoprocessor output with reference output"
        self.assertTrue(compare("C:/Users/dni83241/Documents/MDANSE/MDANSE/Data/Jobs_reference_data/dacf_reference.nc", reference_data_path + "_mono" + ".nc"))

        print "Comparing multiprocessor output with reference output"
        self.assertTrue(compare("C:/Users/dni83241/Documents/MDANSE/MDANSE/Data/Jobs_reference_data/dacf_reference.nc", reference_data_path + "_multi" + ".nc"))

        try:
            os.remove(reference_data_path + "_mono" + ".nc")
            os.remove(reference_data_path + "_multi" + ".nc")
        except OSError:
            pass


def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestDACF))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
