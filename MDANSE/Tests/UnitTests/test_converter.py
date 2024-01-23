import os
import tempfile
import pytest
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Jobs.IJob import JobError
from MDANSE.Framework.Configurators.HDFTrajectoryConfigurator import (
    HDFTrajectoryConfigurator,
)


file_wd = os.path.dirname(os.path.realpath(__file__))

lammps_config = os.path.join(file_wd, "Data", "lammps_test.config")
lammps_lammps = os.path.join(file_wd, "Data", "lammps_test.lammps")
vasp_xdatcar = os.path.join(file_wd, "Data", "XDATCAR_version5")
discover_his = os.path.join(file_wd, "Data", "sushi.his")
discover_xtd = os.path.join(file_wd, "Data", "sushi.xtd")
hem_cam_pdb = os.path.join(file_wd, "Data", "hem-cam.pdb")
hem_cam_dcd = os.path.join(file_wd, "Data", "hem-cam.dcd")


def test_lammps_mdt_conversion_file_exists_and_loads_up_successfully():
    temp_name = tempfile.mktemp()

    parameters = {}
    parameters["config_file"] = lammps_config
    parameters["mass_tolerance"] = 0.05
    parameters["n_steps"] = 0
    parameters["output_file"] = (temp_name, "MDTFormat")
    parameters["smart_mass_association"] = True
    parameters["time_step"] = 1.0
    parameters["trajectory_file"] = lammps_lammps

    lammps = Converter.create("LAMMPS")
    lammps.run(parameters, status=True)

    HDFTrajectoryConfigurator("trajectory").configure(temp_name + ".mdt")

    assert os.path.exists(temp_name + ".mdt")
    assert os.path.isfile(temp_name + ".mdt")
    os.remove(temp_name + ".mdt")


def test_lammps_mdt_conversion_raise_exception_with_incorrect_format():
    temp_name = tempfile.mktemp()

    parameters = {}
    parameters["config_file"] = lammps_config
    parameters["mass_tolerance"] = 0.05
    parameters["n_steps"] = 0
    parameters["output_file"] = (temp_name, "IncorrectFormat")
    parameters["smart_mass_association"] = True
    parameters["time_step"] = 1.0
    parameters["trajectory_file"] = lammps_lammps

    lammps = Converter.create("LAMMPS")
    with pytest.raises(JobError):
        lammps.run(parameters, status=True)


def test_vasp_mdt_conversion_file_exists_and_loads_up_successfully():
    temp_name = tempfile.mktemp()

    parameters = {
        "fold": False,
        "output_file": (temp_name, "MDTFormat"),
        "time_step": 1.0,
        "xdatcar_file": vasp_xdatcar,
    }
    vasp = Converter.create("VASP")
    vasp.run(parameters, status=True)

    HDFTrajectoryConfigurator("trajectory").configure(temp_name + ".mdt")

    assert os.path.exists(temp_name + ".mdt")
    assert os.path.isfile(temp_name + ".mdt")
    os.remove(temp_name + ".mdt")


def test_discover_mdt_conversion_file_exists_and_loads_up_successfully():
    temp_name = tempfile.mktemp()

    parameters = {
        "fold": True,
        "his_file": discover_his,
        "output_file": (temp_name, "MDTFormat"),
        "xtd_file": discover_xtd,
    }

    vasp = Converter.create("discover")
    vasp.run(parameters, status=True)

    HDFTrajectoryConfigurator("trajectory").configure(temp_name + ".mdt")

    assert os.path.exists(temp_name + ".mdt")
    assert os.path.isfile(temp_name + ".mdt")
    os.remove(temp_name + ".mdt")


def test_charmm_mdt_conversion_file_exists_and_loads_up_successfully():
    temp_name = tempfile.mktemp()

    parameters = {
        "dcd_file": hem_cam_dcd,
        "fold": False,
        "output_file": (temp_name, "MDTFormat"),
        "pdb_file": hem_cam_pdb,
        "time_step": 1.0,
    }

    vasp = Converter.create("charmm")
    vasp.run(parameters, status=True)

    HDFTrajectoryConfigurator("trajectory").configure(temp_name + ".mdt")

    assert os.path.exists(temp_name + ".mdt")
    assert os.path.isfile(temp_name + ".mdt")
    os.remove(temp_name + ".mdt")
