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
cp2k_pos = os.path.join(file_wd, "Data", "CO2GAS-pos-1.xyz")
cp2k_vel = os.path.join(file_wd, "Data", "CO2GAS-vel-1.xyz")
cp2k_cell = os.path.join(file_wd, "Data", "CO2GAS-1.cell")
hem_cam_pdb = os.path.join(file_wd, "Data", "hem-cam.pdb")
hem_cam_dcd = os.path.join(file_wd, "Data", "hem-cam.dcd")
ase_traj = os.path.join(file_wd, "Data", "Cu_5steps_ASEformat.traj")
xyz_traj = os.path.join(file_wd, "Data", "traj-100K-npt-1000-res.xyz")
dlp_field_v2 = os.path.join(file_wd, "Data", "FIELD_Water")
dlp_history_v2 = os.path.join(file_wd, "Data", "HISTORY_Water")
dlp_field_v4 = os.path.join(file_wd, "Data", "FIELD4")
dlp_history_v4 = os.path.join(file_wd, "Data", "HISTORY4")
apoferritin_dcd = os.path.join(file_wd, "Data", "apoferritin.dcd")
apoferritin_pdb = os.path.join(file_wd, "Data", "apoferritin.pdb")
pbanew_md = os.path.join(file_wd, "Data", "PBAnew.md")
h2o_trj = os.path.join(file_wd, "Data", "H2O.trj")
h2o_xtd = os.path.join(file_wd, "Data", "H2O.xtd")
md_pdb = os.path.join(file_wd, "Data", "md.pdb")
md_xtc = os.path.join(file_wd, "Data", "md.xtc")


@pytest.mark.parametrize("compression", ["none", "gzip", "lzf"])
def test_lammps_mdt_conversion_file_exists_and_loads_up_successfully(compression):
    temp_name = tempfile.mktemp()

    parameters = {}
    parameters["config_file"] = lammps_config
    parameters["mass_tolerance"] = 0.05
    parameters["n_steps"] = 0
    parameters["output_file"] = (temp_name, 64, compression)
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
    parameters["output_file"] = (temp_name, ["IncorrectFormat"])
    parameters["smart_mass_association"] = True
    parameters["time_step"] = 1.0
    parameters["trajectory_file"] = lammps_lammps

    lammps = Converter.create("LAMMPS")
    with pytest.raises(JobError):
        lammps.run(parameters, status=True)


@pytest.mark.parametrize("compression", ["none", "gzip", "lzf"])
def test_vasp_mdt_conversion_file_exists_and_loads_up_successfully(compression):
    temp_name = tempfile.mktemp()

    parameters = {
        "fold": False,
        "output_file": (temp_name, 64, compression),
        "time_step": 1.0,
        "xdatcar_file": vasp_xdatcar,
    }
    vasp = Converter.create("VASP")
    vasp.run(parameters, status=True)

    HDFTrajectoryConfigurator("trajectory").configure(temp_name + ".mdt")

    assert os.path.exists(temp_name + ".mdt")
    assert os.path.isfile(temp_name + ".mdt")
    os.remove(temp_name + ".mdt")


@pytest.mark.parametrize("compression", ["none", "gzip", "lzf"])
def test_discover_mdt_conversion_file_exists_and_loads_up_successfully(compression):
    temp_name = tempfile.mktemp()

    parameters = {
        "fold": True,
        "his_file": discover_his,
        "output_file": (temp_name, 64, compression),
        "xtd_file": discover_xtd,
    }

    vasp = Converter.create("discover")
    vasp.run(parameters, status=True)

    HDFTrajectoryConfigurator("trajectory").configure(temp_name + ".mdt")

    assert os.path.exists(temp_name + ".mdt")
    assert os.path.isfile(temp_name + ".mdt")
    os.remove(temp_name + ".mdt")


@pytest.mark.parametrize("velocity", [cp2k_vel, None])
def test_cp2k_mdt_conversion_file_exists_and_loads_up_successfully(velocity):
    temp_name = tempfile.mktemp()

    parameters = {
        "pos_file": cp2k_pos,
        "cell_file": cp2k_cell,
        "vel_file": velocity,
        "output_file": (temp_name, 64, "gzip"),
    }

    vasp = Converter.create("cp2k")
    vasp.run(parameters, status=True)

    HDFTrajectoryConfigurator("trajectory").configure(temp_name + ".mdt")

    assert os.path.exists(temp_name + ".mdt")
    assert os.path.isfile(temp_name + ".mdt")
    os.remove(temp_name + ".mdt")


@pytest.mark.parametrize("compression", ["none", "gzip", "lzf"])
def test_charmm_mdt_conversion_file_exists_and_loads_up_successfully(compression):
    temp_name = tempfile.mktemp()

    parameters = {
        "dcd_file": hem_cam_dcd,
        "fold": False,
        "output_file": (temp_name, 64, compression),
        "pdb_file": hem_cam_pdb,
        "time_step": 1.0,
    }

    vasp = Converter.create("charmm")
    vasp.run(parameters, status=True)

    HDFTrajectoryConfigurator("trajectory").configure(temp_name + ".mdt")

    assert os.path.exists(temp_name + ".mdt")
    assert os.path.isfile(temp_name + ".mdt")
    os.remove(temp_name + ".mdt")


@pytest.mark.parametrize("compression", ["none", "gzip", "lzf"])
def test_ase_mdt_conversion_file_exists_and_loads_up_successfully(compression):
    temp_name = tempfile.mktemp()

    parameters = {
        "trajectory_file": ase_traj,
        "fold": False,
        "output_file": (temp_name, 64, compression),
        "n_steps": 0,
        "time_step": 50.0,
        "time_unit": "fs",
    }

    ase_conv = Converter.create("ase")
    ase_conv.run(parameters, status=True)

    HDFTrajectoryConfigurator("trajectory").configure(temp_name + ".mdt")

    assert os.path.exists(temp_name + ".mdt")
    assert os.path.isfile(temp_name + ".mdt")
    os.remove(temp_name + ".mdt")


@pytest.mark.parametrize("trajectory", [ase_traj, xyz_traj, vasp_xdatcar])
def test_improvedase_mdt_conversion_file_exists_and_loads_up_successfully(trajectory):
    temp_name = tempfile.mktemp()

    parameters = {
        "trajectory_file": trajectory,
        "fold": False,
        "output_file": (temp_name, 64, "gzip"),
        "n_steps": 0,
        "time_step": 50.0,
        "time_unit": "fs",
    }

    ase_conv = Converter.create("improvedase")
    ase_conv.run(parameters, status=True)

    HDFTrajectoryConfigurator("trajectory").configure(temp_name + ".mdt")

    assert os.path.exists(temp_name + ".mdt")
    assert os.path.isfile(temp_name + ".mdt")
    os.remove(temp_name + ".mdt")


def test_improvedase_lammps_two_files():
    temp_name = tempfile.mktemp()

    parameters = {
        "trajectory_file": (lammps_lammps, "lammps-dump-text"),
        "configuration_file": (lammps_config, "lammps-data"),
        "fold": False,
        "output_file": (temp_name, 64, "gzip"),
        "n_steps": 0,
        "elements_from_mass": True,
        "time_step": 50.0,
        "time_unit": "fs",
    }

    ase_conv = Converter.create("improvedase")
    ase_conv.run(parameters, status=True)

    HDFTrajectoryConfigurator("trajectory").configure(temp_name + ".mdt")

    assert os.path.exists(temp_name + ".mdt")
    assert os.path.isfile(temp_name + ".mdt")
    os.remove(temp_name + ".mdt")


@pytest.mark.parametrize("compression", ["none", "gzip", "lzf"])
def test_xyz_mdt_conversion_file_exists_and_loads_up_successfully(compression):
    temp_name = tempfile.mktemp()

    parameters = {
        "trajectory_file": xyz_traj,
        "fold": False,
        "output_file": (temp_name, 64, compression),
        "n_steps": 0,
        "time_step": 50.0,
        "time_unit": "fs",
    }

    ase_conv = Converter.create("ase")
    ase_conv.run(parameters, status=True)

    HDFTrajectoryConfigurator("trajectory").configure(temp_name + ".mdt")

    assert os.path.exists(temp_name + ".mdt")
    assert os.path.isfile(temp_name + ".mdt")
    os.remove(temp_name + ".mdt")


@pytest.mark.parametrize("compression", ["none", "gzip", "lzf"])
def test_dlp_mdt_conversion_file_exists_and_loads_up_successfully_with_dlp_version_2(
    compression,
):
    temp_name = tempfile.mktemp()

    parameters = {
        "atom_aliases": "{}",
        "field_file": dlp_field_v2,
        "fold": False,
        "history_file": dlp_history_v2,
        "output_file": (temp_name, 64, compression),
    }
    dl_poly = Converter.create("DL_POLY")
    dl_poly.run(parameters, status=True)

    HDFTrajectoryConfigurator("trajectory").configure(temp_name + ".mdt")

    assert os.path.exists(temp_name + ".mdt")
    assert os.path.isfile(temp_name + ".mdt")
    os.remove(temp_name + ".mdt")


@pytest.mark.parametrize("compression", ["none", "gzip", "lzf"])
def test_dlp_mdt_conversion_file_exists_and_loads_up_successfully_with_dlp_version_4(
    compression,
):
    temp_name = tempfile.mktemp()

    parameters = {
        "atom_aliases": "{}",
        "field_file": dlp_field_v4,
        "fold": False,
        "history_file": dlp_history_v4,
        "output_file": (temp_name, 64, compression),
    }
    dl_poly = Converter.create("DL_POLY")
    dl_poly.run(parameters, status=True)

    HDFTrajectoryConfigurator("trajectory").configure(temp_name + ".mdt")

    assert os.path.exists(temp_name + ".mdt")
    assert os.path.isfile(temp_name + ".mdt")
    os.remove(temp_name + ".mdt")


@pytest.mark.parametrize("compression", ["none", "gzip", "lzf"])
def test_namd_mdt_conversion_file_exists_and_loads_up_successfully_and_chemical_system_has_correct_number_of_atoms(
    compression,
):
    temp_name = tempfile.mktemp()

    parameters = {
        "dcd_file": apoferritin_dcd,
        "fold": False,
        "output_file": (temp_name, 64, compression),
        "pdb_file": apoferritin_pdb,
        "time_step": "1.0",
    }
    namd = Converter.create("NAMD")
    namd.run(parameters, status=True)
    assert os.path.exists(temp_name + ".mdt")
    assert os.path.isfile(temp_name + ".mdt")

    hdftradj = HDFTrajectoryConfigurator("trajectory")
    hdftradj.configure(temp_name + ".mdt")
    assert hdftradj["instance"].chemical_system.number_of_atoms == 12397

    hdftradj["instance"].close()
    os.remove(temp_name + ".mdt")


@pytest.mark.parametrize("compression", ["none", "gzip", "lzf"])
def test_castep_md_conversion_file_exists_and_loads_up_successfully(compression):
    temp_name = tempfile.mktemp()

    parameters = {
        "atom_aliases": "{}",
        "castep_file": pbanew_md,
        "fold": False,
        "output_file": (temp_name, 64, compression),
    }

    castep = Converter.create("CASTEP")
    castep.run(parameters, status=True)

    HDFTrajectoryConfigurator("trajectory").configure(temp_name + ".mdt")

    assert os.path.exists(temp_name + ".mdt")
    assert os.path.isfile(temp_name + ".mdt")
    os.remove(temp_name + ".mdt")


@pytest.mark.parametrize("compression", ["none", "gzip", "lzf"])
def test_dftb_conversion_file_exists_and_loads_up_successfully(compression):
    temp_name = tempfile.mktemp()

    parameters = {
        "atom_aliases": "{}",
        "fold": True,
        "output_file": (temp_name, 64, compression),
        "trj_file": h2o_trj,
        "xtd_file": h2o_xtd,
    }

    dftb = Converter.create("DFTB")
    dftb.run(parameters, status=True)

    HDFTrajectoryConfigurator("trajectory").configure(temp_name + ".mdt")

    assert os.path.exists(temp_name + ".mdt")
    assert os.path.isfile(temp_name + ".mdt")
    os.remove(temp_name + ".mdt")


@pytest.mark.parametrize("compression", ["none", "gzip", "lzf"])
def test_forcite_conversion_file_exists_and_loads_up_successfully(compression):
    temp_name = tempfile.mktemp()

    parameters = {
        "atom_aliases": "{}",
        "fold": False,
        "output_file": (temp_name, 64, compression),
        "trj_file": h2o_trj,
        "xtd_file": h2o_xtd,
    }

    forcite = Converter.create("Forcite")
    forcite.run(parameters, status=True)

    HDFTrajectoryConfigurator("trajectory").configure(temp_name + ".mdt")

    assert os.path.exists(temp_name + ".mdt")
    assert os.path.isfile(temp_name + ".mdt")
    os.remove(temp_name + ".mdt")


@pytest.mark.parametrize("compression", ["none", "gzip", "lzf"])
def test_gromacs_conversion_file_exists_and_loads_up_successfully(compression):
    temp_name = tempfile.mktemp()

    parameters = {
        "fold": False,
        "output_file": (temp_name, 64, compression),
        "pdb_file": md_pdb,
        "xtc_file": md_xtc,
    }

    gromacs = Converter.create("Gromacs")
    gromacs.run(parameters, status=True)

    HDFTrajectoryConfigurator("trajectory").configure(temp_name + ".mdt")

    assert os.path.exists(temp_name + ".mdt")
    assert os.path.isfile(temp_name + ".mdt")
    os.remove(temp_name + ".mdt")
