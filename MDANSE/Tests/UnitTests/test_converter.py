import os
import tempfile
from pathlib import Path

import h5py
import numpy as np
import pytest
from MDANSE.Framework.Configurators.HDFTrajectoryConfigurator import \
    HDFTrajectoryConfigurator
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Jobs.IJob import JobError

TEST_DIR = Path(__file__).parent
CONV_DIR = TEST_DIR / "Converted"
DATA_DIR = TEST_DIR / "Data"

lammps_config = DATA_DIR / "lammps_test.config"
lammps_lammps = DATA_DIR / "lammps_test.lammps"
lammps_moly = DATA_DIR / "structure_moly.lammps"
lammps_custom = DATA_DIR / "lammps_moly_custom.txt"
lammps_xyz = DATA_DIR / "lammps_moly_xyz.txt"
lammps_h5md = CONV_DIR / "lammps_moly_h5md.h5"
vasp_xdatcar = DATA_DIR / "XDATCAR_version5"
discover_his = DATA_DIR / "sushi.his"
discover_xtd = DATA_DIR / "sushi.xtd"
cp2k_pos = DATA_DIR / "CO2GAS-pos-1.xyz"
cp2k_vel = DATA_DIR / "CO2GAS-vel-1.xyz"
cp2k_cell = DATA_DIR / "CO2GAS-1.cell"
hem_cam_pdb = DATA_DIR / "hem-cam.pdb"
hem_cam_dcd = DATA_DIR / "hem-cam.dcd"
ase_traj = DATA_DIR / "Cu_5steps_ASEformat.traj"
xyz_traj = DATA_DIR / "traj-100K-npt-1000-res.xyz"
dlp_field_v2 = DATA_DIR / "FIELD_Water"
dlp_history_v2 = DATA_DIR / "HISTORY_Water"
dlp_field_v4 = DATA_DIR / "FIELD4"
dlp_history_v4 = DATA_DIR / "HISTORY4"
dlp_field_with_grad = DATA_DIR / "FIELD_methanol_short"
dlp_history_with_grad = DATA_DIR / "HISTORY_methanol_short"
apoferritin_dcd = DATA_DIR / "apoferritin.dcd"
apoferritin_pdb = DATA_DIR / "apoferritin.pdb"
pbanew_md = DATA_DIR / "PBAnew.md"
h2o_trj = DATA_DIR / "H2O.trj"
h2o_xtd = DATA_DIR / "H2O.xtd"
md_pdb = DATA_DIR / "md.pdb"
md_xtc = DATA_DIR / "md.xtc"
gromacs_nvt = (DATA_DIR / "gromacs-nvt.pdb", DATA_DIR / "gromacs-nvt.xtc")


def _converter_test(tmp_path, converter_type, result, compare, parameters, compression):
    temp_name = tmp_path / "output"
    out_name = temp_name.with_suffix(".mdt")
    log_name = temp_name.with_suffix(".log")
    result_name = CONV_DIR / result

    parameters["output_files"] = (temp_name, 64, 128, compression, "INFO")

    converter = Converter.create(converter_type)
    converter.run(parameters, status=True)

    traj_conf = HDFTrajectoryConfigurator("trajectory")
    traj_conf.configure(out_name)
    traj_conf.get_information()
    traj_conf["hdf_trajectory"].close()

    with h5py.File(out_name) as actual, h5py.File(result_name) as desired:
        for prop in compare:
            np.testing.assert_array_almost_equal(actual[prop], desired[prop])

    assert out_name.is_file()
    assert log_name.is_file()

@pytest.mark.parametrize("converter_type,result,compare,parameters", (
    ("LAMMPS", "lammps.mdt",
     ("/configuration/coordinates", "/unit_cell", "/time", "/charge"),
     {"config_file": lammps_config,
      "mass_tolerance": 0.05,
      "n_steps": 0,
      "smart_mass_association": True,
      "time_step": 1.,
      "trajectory_file": lammps_lammps}),
    ("VASP", "vasp.mdt",
     ("/configuration/coordinates", "/unit_cell", "/time"),
     {"fold": False,
      "time_step": 1.0,
      "xdatcar_file": vasp_xdatcar}),
    ("discover", "discover.mdt",
     ("/configuration/coordinates", "/configuration/velocities", "/time", "/charge"),
     {"fold": True,
      "his_file": discover_his,
      "xtd_file": discover_xtd}),
    ("cp2k", "cp2k_velocity.mdt",
     ("/configuration/coordinates", "/configuration/velocities", "/time", "/charge"),
     {"pos_file": cp2k_pos,
      "cell_file": cp2k_cell,
      "vel_file": cp2k_vel}),
    ("cp2k", "cp2k.mdt",
     ("/configuration/coordinates", "/time", "/charge"),
     {"pos_file": cp2k_pos,
      "cell_file": cp2k_cell,
      "vel_file": None}),
    ("charmm", "hem_cam.mdt",
     ("/configuration/coordinates", "/unit_cell", "/time"),
     {"dcd_file": hem_cam_dcd,
      "fold": False,
      "pdb_file": hem_cam_pdb,
      "time_step": 1.0}),
    ("ase", "ase.mdt",
     ("/configuration/coordinates", "/configuration/velocities", "/time"),
     {"trajectory_file": ase_traj,
      "fold": False,
      "n_steps": 0,
      "time_step": 50.0,
      "time_unit": "fs"}),
    ("ase", "ase_xyz.mdt",
     ("/configuration/coordinates", "/configuration/velocities", "/unit_cell", "/time"),
     {"trajectory_file": xyz_traj,
      "fold": False,
      "n_steps": 0,
      "time_step": 50.0,
      "time_unit": "fs"}),
    ("improvedase", "ase.mdt",
     (),
     {"trajectory_file": (lammps_lammps, "lammps-dump-text"),
      "configuration_file": (lammps_config, "lammps-data"),
      "fold": False,
      "n_steps": 0,
      "elements_from_mass": True,
      "time_step": 50.0,
      "time_unit": "fs"}),
    ("DL_POLY", "dlp_v2.mdt",
     ("/configuration/coordinates", "/unit_cell", "/time", "/charge"),
     {"atom_aliases": "{}",
      "field_file": dlp_field_v2,
      "fold": False,
      "history_file": dlp_history_v2}),
    ("DL_POLY", "dlp_v4.mdt",
     ("/configuration/coordinates", "/unit_cell", "/time"),
     {"atom_aliases": "{}",
      "field_file": dlp_field_v4,
      "fold": False,
      "history_file": dlp_history_v4}),
    ("DL_POLY", "dlp_with_grad.mdt",
     ("/configuration/coordinates", "/configuration/velocities", "/configuration/gradients",
      "/unit_cell", "/time", "/charge"),
     {"atom_aliases": "{}",
      "field_file": dlp_field_with_grad,
      "fold": False,
      "history_file": dlp_history_with_grad}),
    ("NAMD", "namd.mdt",
     ("/configuration/coordinates", "/unit_cell", "/time"),
     {"dcd_file": apoferritin_dcd,
      "fold": False,
      "pdb_file": apoferritin_pdb,
      "time_step": "1.0"}),
    ("CASTEP", "castep.mdt",
     ("/configuration/coordinates", "/configuration/velocities", "/configuration/gradients",
      "/unit_cell", "/time"),
     {"atom_aliases": "{}",
      "castep_file": pbanew_md,
      "fold": False}),
    ("DFTB", "dftb.mdt",
     ("/configuration/coordinates", "/configuration/velocities", "/unit_cell", "/time", "/charge"),
     {"atom_aliases": "{}",
      "fold": True,
      "trj_file": h2o_trj,
      "xtd_file": h2o_xtd}),
    ("Forcite", "forcite.mdt",
     ("/configuration/coordinates", "/configuration/velocities", "/unit_cell", "/time", "/charge"),
     {"atom_aliases": "{}",
      "fold": False,
      "trj_file": h2o_trj,
      "xtd_file": h2o_xtd}),
    ("Gromacs", "md.mdt",
     ("/configuration/coordinates", "/unit_cell", "/time"),
     {"fold": False,
      "pdb_file": md_pdb,
      "xtc_file": md_xtc}),
    ("Gromacs", "gromacs-nvt.mdt",
     ("/configuration/coordinates", "/unit_cell", "/time"),
     {"fold": False,
      "pdb_file": gromacs_nvt[0],
      "xtc_file": gromacs_nvt[1]}),
    ("MDAnalysis", "md.mdt",
     ("/configuration/coordinates", "/unit_cell", "/time"),
     {"topology_file": (md_pdb, "AUTO"),
      "coordinate_files": ([str(md_xtc)], "XTC")}),  # Does not work with Path
    ("MDTraj", "hem_cam.mdt",
     ("/configuration/coordinates", "/unit_cell", "/time"),
     {"topology_file": hem_cam_pdb,
      "coordinate_files": [str(hem_cam_dcd)],  # Does not work with Path
      "time_step": 1.0}),
))
@pytest.mark.parametrize("compression", ["none", "gzip", "lzf"])
def test_build_mdt_file_and_load(tmp_path, converter_type, result, compare, parameters, compression):
    _converter_test(tmp_path, converter_type, result, compare, parameters, compression)

@pytest.mark.parametrize(
    "unit_system", ["real", "metal", "si", "cgs", "electron", "micro", "nano"]
)
def test_lammps_mdt_conversion_unit_system(tmp_path, unit_system):
    _converter_test(tmp_path, "LAMMPS", f"lammps_{unit_system}.mdt",
                    ("/configuration/coordinates", "/unit_cell", "/time", "/charge"),
                    {"config_file": lammps_config,
                     "mass_tolerance": 0.05,
                     "n_steps": 0,
                     "smart_mass_association": True,
                     "time_step": 1.0,
                     "trajectory_file": lammps_lammps,
                     "lammps_units": unit_system},
                    "gzip")

@pytest.mark.parametrize(
    "trajectory_file,trajectory_format",
    [(lammps_custom, "custom"), (lammps_xyz, "xyz"), (lammps_h5md, "h5md")],
)
def test_lammps_mdt_conversion_trajectory_format(tmp_path, trajectory_file, trajectory_format):
    _converter_test(tmp_path, "LAMMPS", f"lammps_moly_{trajectory_format}.mdt",
                    ("/configuration/coordinates", "/unit_cell", "/time", "/charge"),
                    {"config_file": lammps_moly,
                     "mass_tolerance": 0.05,
                     "n_steps": 0,
                     "smart_mass_association": True,
                     "time_step": 1.0,
                     "trajectory_file": trajectory_file,
                     "trajectory_format": trajectory_format,
                     "lammps_units": "electron"},
                    "gzip")

@pytest.mark.parametrize(
    "trajectory",
    (ase_traj, xyz_traj, vasp_xdatcar),
)
def test_improvedase_mdt_conversion_file_exists_and_loads_up_successfully(tmp_path, trajectory):
    _converter_test(tmp_path, "improvedase", "ase.mdt", # Dummy
                    (),
                    {"trajectory_file": str(trajectory),  # Does not work with Path
                     "fold": False,
                     "n_steps": 0,
                     "time_step": 50.0,
                     "time_unit": "fs"},
                    "gzip")

def test_lammps_mdt_conversion_raise_exception_with_incorrect_format():
    temp_name = tempfile.mktemp()

    parameters = {}
    parameters["config_file"] = lammps_config
    parameters["mass_tolerance"] = 0.05
    parameters["n_steps"] = 0
    parameters["output_files"] = (temp_name, ["IncorrectFormat"], "INFO")
    parameters["smart_mass_association"] = True
    parameters["time_step"] = 1.0
    parameters["trajectory_file"] = lammps_lammps

    lammps = Converter.create("LAMMPS")
    with pytest.raises(JobError):
        lammps.run(parameters, status=True)
