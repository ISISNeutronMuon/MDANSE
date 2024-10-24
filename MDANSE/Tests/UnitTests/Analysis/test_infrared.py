import sys
import tempfile
import os
from os import path

from MDANSE.Framework.Jobs.IJob import IJob


sys.setrecursionlimit(100000)

short_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Data",
    "named_molecules.mdt",
)


def test_dacf_analysis():
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["frames"] = (0, 100, 1, 51)
    parameters["output_files"] = (temp_name, ("MDAFormat",), "INFO")
    parameters["running_mode"] = ("single-core", 1)
    parameters["trajectory"] = short_traj
    parameters["atom_charges"] = "{}"
    parameters["molecule_name"] = "InChI=1S/CO2/c2-1-3"
    job = IJob.create("DipoleAutoCorrelationFunction")
    job.run(parameters, status=True)
    assert path.exists(temp_name + ".mda")
    assert path.isfile(temp_name + ".mda")
    os.remove(temp_name + ".mda")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    os.remove(temp_name + ".log")


def test_ir_analysis():
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["frames"] = (0, 100, 1, 51)
    parameters["instrument_resolution"] = ("Gaussian", {"sigma": 1.0, "mu": 0.0})
    parameters["output_files"] = (temp_name, ("MDAFormat",), "INFO")
    parameters["derivative_order"] = 3
    parameters["running_mode"] = ("single-core", 1)
    parameters["trajectory"] = short_traj
    parameters["atom_charges"] = "{}"
    parameters["molecule_name"] = "InChI=1S/CO2/c2-1-3"
    job = IJob.create("Infrared")
    job.run(parameters, status=True)
    assert path.exists(temp_name + ".mda")
    assert path.isfile(temp_name + ".mda")
    os.remove(temp_name + ".mda")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    os.remove(temp_name + ".log")
