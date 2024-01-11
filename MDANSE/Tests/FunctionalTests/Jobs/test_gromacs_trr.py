import numpy as np
from shutil import copy
import os
import unittest

import netCDF4

from MDANSE.Framework.Converters.Converter import Converter
import Comparator


def compare(file1, file2, array_tolerance):
    res1 = {}
    with netCDF4.Dataset(file1, "r") as f:
        for k, v in f.variables.items():
            if k not in ["velocities", "gradients", "temperature", "kinetic_energy"]:
                res1[k] = v[:]

    res2 = {}
    with netCDF4.Dataset(file2, "r") as f:
        for k, v in f.variables.items():
            if k not in ["velocities", "gradients", "temperature", "kinetic_energy"]:
                res2[k] = v[:]

    return Comparator.Comparator().compare(res1, res2, array_tolerance)


class TestGromacsADK(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trr_copy = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "output_trr.nc"
        )

        job = Converter.create("Gromacs")

        for k, v in job.get_default_parameters().items():
            if k == "output_file":
                cls.output_path = v[0]
                break

        parameters = {}
        parameters["fold"] = False
        parameters["pdb_file"] = "../../../Data/Trajectories/Gromacs/adk_oplsaa.pdb"
        parameters["output_file"] = ("_".join([cls.output_path, "trr"]), "netcdf")
        parameters["xtc_file"] = "../../../Data/Trajectories/Gromacs/adk_oplsaa.trr"
        print("Launching job in monoprocessor mode for trr")
        parameters["running_mode"] = ("monoprocessor", 1)
        job.run(parameters, status=False)
        copy("_".join([cls.output_path, "trr.nc"]), cls.trr_copy)
        print("Monoprocessor execution completed for trr")

    def test_core(self):
        job = job = Converter.create("Gromacs")

        parameters = {}
        parameters["fold"] = False
        parameters["pdb_file"] = "../../../Data/Trajectories/Gromacs/adk_oplsaa.pdb"
        parameters["output_file"] = ("_".join([self.output_path, "xtc"]), "netcdf")
        parameters["xtc_file"] = "../../../Data/Trajectories/Gromacs/adk_oplsaa.xtc"
        print("Launching job in monoprocessor mode for xtc")
        parameters["running_mode"] = ("monoprocessor", 1)
        job.run(parameters, status=False)
        print("Monoprocessor execution completed for xtc")

        print("Comparing monoprocessor output with reference output")
        self.assertTrue(
            compare(
                "_".join([self.output_path, "xtc.nc"]),
                self.trr_copy,
                array_tolerance=(0, 0.00051),
            )
        )

    def test_velocities(self):
        # Load velocities that have been generated from the same trajectory with MDAnalysis + convert angstrom to nm
        expected = np.load(r"../../../Data/Trajectories/Gromacs/adk_oplsaa.npy") / 10

        with netCDF4.Dataset(self.trr_copy, "r") as f:
            velocities = f.variables["velocities"][:]

        self.assertTrue(np.allclose(expected, velocities, 0, 0.000001))

    def test_gradients(self):
        # adk_oplsaa.trr does not contain forces

        with netCDF4.Dataset(self.trr_copy, "r") as f:
            self.assertFalse("gradients" in f.variables)

    @classmethod
    def tearDownClass(cls):
        os.remove(cls.trr_copy)


class TestGromacsCobrotoxin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Run an analysis of the TRR file and copy the resulting file."""
        cls.trr_copy = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "output_trr.nc"
        )

        job = Converter.create("Gromacs")

        for k, v in job.get_default_parameters().items():
            if k == "output_file":
                cls.output_path = v[0]
                break

        parameters = {}
        parameters["fold"] = False
        parameters["pdb_file"] = "../../../Data/Trajectories/Gromacs/cobrotoxin.pdb"
        parameters["output_file"] = ("_".join([cls.output_path, "trr"]), "netcdf")
        parameters["xtc_file"] = "../../../Data/Trajectories/Gromacs/cobrotoxin.trr"
        print("Launching job in monoprocessor mode for trr")
        parameters["running_mode"] = ("monoprocessor", 1)
        job.run(parameters, status=False)
        copy("_".join([cls.output_path, "trr.nc"]), cls.trr_copy)
        print("Monoprocessor execution completed for trr")

    def test_core(self):
        """Run an analysis of the XTC trajectory and compare it with the TRR results."""
        job = Converter.create("Gromacs")

        parameters = {}
        parameters["fold"] = False
        parameters["pdb_file"] = "../../../Data/Trajectories/Gromacs/cobrotoxin.pdb"
        parameters["output_file"] = ("_".join([self.output_path, "xtc"]), "netcdf")
        parameters["xtc_file"] = "../../../Data/Trajectories/Gromacs/cobrotoxin.xtc"
        print("Launching job in monoprocessor mode for xtc")
        parameters["running_mode"] = ("monoprocessor", 1)
        job.run(parameters, status=False)
        print("Monoprocessor execution completed for xtc")

        print("Comparing monoprocessor output with reference output")
        self.assertTrue(
            compare(
                "_".join([self.output_path, "xtc.nc"]),
                self.trr_copy,
                array_tolerance=(0, 0.00051),
            )
        )

    def test_velocities(self):
        # Load velocities that have been generated from the same trajectory with MDAnalysis + convert angstrom to nm
        expected = (
            np.load(r"../../../Data/Trajectories/Gromacs/cobrotoxin_vels.npy") / 10
        )

        with netCDF4.Dataset(self.trr_copy, "r") as f:
            velocities = f.variables["velocities"][:]

        self.assertTrue(np.allclose(expected, velocities, 0, 0.000001))

    def test_gradients(self):
        # Load forces that have been generated from the same trajectory with MDAnalysis + convert angstrom to nm
        expected = (
            np.load(r"../../../Data/Trajectories/Gromacs/cobrotoxin_forces.npy") * 10
        )

        with netCDF4.Dataset(self.trr_copy, "r") as f:
            gradients = f.variables["gradients"][:]

        self.assertTrue(np.allclose(expected, gradients, 0, 0.001))
        # Such a large tolerance is required because most gradients are > 100

    @classmethod
    def tearDownClass(cls):
        """Remove the copied file once all tests are finished."""
        os.remove(cls.trr_copy)


def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    # s.addTest(loader.loadTestsFromTestCase(TestGromacsADK))  # exclude this since it is long and currently duplicate
    s.addTest(loader.loadTestsFromTestCase(TestGromacsCobrotoxin))
    return s


if __name__ == "__main__":
    unittest.main(verbosity=2)
