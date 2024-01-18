import os
import tempfile
import pytest
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Jobs.IJob import JobError


lammps_config = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "Data", "lammps_test.config"
)
lammps_lammps = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "Data", "lammps_test.lammps"
)


def test_convert_lammps_mdt_conversion_file_exists():
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

    assert os.path.exists(temp_name + ".mdt")
    assert os.path.isfile(temp_name + ".mdt")
    os.remove(temp_name + ".mdt")


def test_convert_lammps_mdt_conversion_raise_exception_with_incorrect_format():
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
