from pathlib import Path

import numpy as np
import pytest
from MDANSE.Framework.Configurators.ConfigFileConfigurator import \
    ConfigFileConfigurator
from MDANSE.Framework.Configurators.HDFTrajectoryConfigurator import \
    HDFTrajectoryConfigurator
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Converters.LAMMPS import BoxStyle
from MDANSE.Framework.Jobs.IJob import JobError
from more_itertools import run_length
from test_helpers.compare_hdf5 import compare_hdf5
from test_helpers.paths import CONV_DIR, DATA_DIR

lammps_config = DATA_DIR / "lammps_test.config"
lammps_lammps = DATA_DIR / "lammps_test.lammps"
lammps_moly = DATA_DIR / "structure_moly.lammps"
lammps_custom = DATA_DIR / "lammps_moly_custom.txt"
lammps_xyz = DATA_DIR / "lammps_moly_xyz.txt"
lammps_h5md = CONV_DIR / "lammps_moly_h5md.h5"
lammps_cao_config = DATA_DIR / "lammps_CaO.config"
lammps_cao_run = DATA_DIR / "lammps_CaO.lammps"
lammps_ar = DATA_DIR / "lammps_ar.config"
lammps_fake = DATA_DIR / "lammps_fake.lammps"
lammps_fake_config = DATA_DIR / "lammps_fake.config"
vasp_xdatcar = DATA_DIR / "XDATCAR_version5"
cp2k_pos = DATA_DIR / "CO2GAS-pos-1.xyz"
cp2k_vel = DATA_DIR / "CO2GAS-vel-1.xyz"
cp2k_cell = DATA_DIR / "CO2GAS-1.cell"
cp2k_srtio3_pos = DATA_DIR / "SrTiO3_MD-pos-1.xyz"
cp2k_srtio3_vel = DATA_DIR / "SrTiO3_MD-vel-1.xyz"
cp2k_srtio3_frc = DATA_DIR / "SrTiO3_MD-frc-1.xyz"
cp2k_srtio3_cell = DATA_DIR / "SrTiO3_MD-cell-1.cell"
hem_cam_pdb = DATA_DIR / "hem-cam.pdb"
hem_cam_dcd = DATA_DIR / "hem-cam.dcd"
ase_traj = DATA_DIR / "Cu_5steps_ASEformat.traj"
xyz_traj = DATA_DIR / "traj-100K-npt-1000-res.xyz"
dlp_field_v2 = DATA_DIR / "FIELD_Water"
dlp_history_v2 = DATA_DIR / "HISTORY_Water"
dlp_field_v4 = DATA_DIR / "FIELD4"
dlp_history_v4 = DATA_DIR / "HISTORY4"
dlp_field_meth = DATA_DIR / "FIELD_CH3OH_H20"
dlp_history_meth = DATA_DIR / "HISTORY_CH3OH_H20"
dlp_field_with_grad = DATA_DIR / "FIELD_methanol_short"
dlp_history_with_grad = DATA_DIR / "HISTORY_methanol_short"
dlp_field_awkward = DATA_DIR / "FIELD_CUT"
dlp_history_awkward = DATA_DIR / "HISTORY_CUT"
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
    traj_conf["instance"].close()

    compare_hdf5(out_name, result_name, compare, atol=1e-6)

    assert out_name.is_file()
    assert log_name.is_file()


@pytest.mark.parametrize(
    "converter_type,result,compare,parameters",
    (
        (
            "LAMMPS",
            "lammps.mdt",
            ("/configuration/coordinates", "/unit_cell", "/time", "/charge"),
            {
                "config_file": lammps_config,
                "mass_tolerance": 0.05,
                "n_steps": 0,
                "smart_mass_association": True,
                "time_step": 1.0,
                "trajectory_file": lammps_lammps,
            },
        ),
        (
            "LAMMPS",
            "lammps_cao.mdt",
            ("/configuration/coordinates", "/unit_cell", "/time", "/charge"),
            {
                "config_file": lammps_cao_config,
                "mass_tolerance": 0.05,
                "n_steps": 0,
                "smart_mass_association": True,
                "time_step": 1.0,
                "trajectory_file": lammps_cao_run,
            },
        ),
        (
            "LAMMPS",
            "lammps_fake.mdt",
            ("/configuration/coordinates", "/configuration/gradients", "/configuration/velocities", "/unit_cell", "/time"),
            {
                "config_file": lammps_fake_config,
                "mass_tolerance": 0.05,
                "n_steps": 0,
                "smart_mass_association": True,
                "time_step": 1.0,
                "trajectory_file": lammps_fake,
            },
        ),
        (
            "VASP",
            "vasp.mdt",
            ("/configuration/coordinates", "/unit_cell", "/time"),
            {"fold": False, "time_step": 1.0, "xdatcar_file": vasp_xdatcar},
        ),
        (
            "cp2k",
            "cp2k_velocity.mdt",
            (
                "/configuration/coordinates",
                "/configuration/velocities",
                "/time",
                "/charge",
            ),
            {"pos_file": cp2k_pos, "cell_file": cp2k_cell, "vel_file": cp2k_vel},
        ),
        (
            "cp2k",
            "cp2k.mdt",
            ("/configuration/coordinates", "/time", "/charge"),
            {"pos_file": cp2k_pos, "cell_file": cp2k_cell, "vel_file": None},
        ),
        (
            "cp2k",
            "cp2k.mdt",
            ("/configuration/coordinates", "/time", "/charge"),
            {"pos_file": cp2k_pos, "cell_file": cp2k_cell, "vel_file": ""},
        ),
        (
            "cp2k",
            "cp2k_srtio3.mdt",
            (
                "/configuration/coordinates",
                "/configuration/velocities",
                "/configuration/forces",
                "/time",
            ),
            {
                "pos_file": cp2k_srtio3_pos,
                "cell_file": cp2k_srtio3_cell,
                "vel_file": cp2k_srtio3_vel,
                "force_file": cp2k_srtio3_frc,
            },
        ),
        (
            "cp2k",
            "cp2k_srtio3.mdt",
            ("/configuration/coordinates", "/configuration/forces", "/time"),
            {
                "pos_file": cp2k_srtio3_pos,
                "cell_file": cp2k_srtio3_cell,
                "force_file": cp2k_srtio3_frc,
            },
        ),
        (
            "charmm",
            "hem_cam.mdt",
            ("/configuration/coordinates", "/unit_cell", "/time"),
            {
                "dcd_file": hem_cam_dcd,
                "fold": False,
                "pdb_file": hem_cam_pdb,
                "time_step": 1.0,
            },
        ),
        (
            "ase",
            "ase.mdt",
            ("/configuration/coordinates", "/configuration/velocities", "/time"),
            {
                "trajectory_file": ase_traj,
                "fold": False,
                "n_steps": 0,
                "time_step": 50.0,
                "time_unit": "fs",
            },
        ),
        (
            "ase",
            "ase_xyz.mdt",
            (
                "/configuration/coordinates",
                "/configuration/velocities",
                "/unit_cell",
                "/time",
            ),
            {
                "trajectory_file": xyz_traj,
                "fold": False,
                "n_steps": 0,
                "time_step": 50.0,
                "time_unit": "fs",
            },
        ),
        (
            "improvedase",
            "ase.mdt",
            (),
            {
                "trajectory_file": (lammps_lammps, "lammps-dump-text"),
                "configuration_file": (lammps_config, "lammps-data"),
                "fold": False,
                "n_steps": 0,
                "elements_from_mass": True,
                "time_step": 50.0,
                "time_unit": "fs",
            },
        ),
        (
            "DL_POLY",
            "dlp_v2.mdt",
            ("/configuration/coordinates", "/unit_cell", "/time", "/charge"),
            {
                "atom_aliases": "{}",
                "field_file": dlp_field_v2,
                "fold": False,
                "history_file": dlp_history_v2,
            },
        ),
        (
            "DL_POLY",
            "dlp_v4.mdt",
            ("/configuration/coordinates", "/unit_cell", "/time"),
            {
                "atom_aliases": "{}",
                "field_file": dlp_field_v4,
                "fold": False,
                "history_file": dlp_history_v4,
            },
        ),
        (
            "DL_POLY",
            "dlp_CH3OH_H2O.mdt",
            ("/configuration/coordinates", "/unit_cell", "/time"),
            {
                "atom_aliases": "{}",
                "field_file": dlp_field_meth,
                "fold": False,
                "history_file": dlp_history_meth,
            },
        ),
        (
            "DL_POLY",
            "dlp_with_grad.mdt",
            (
                "/configuration/coordinates",
                "/configuration/velocities",
                "/configuration/gradients",
                "/unit_cell",
                "/time",
                "/charge",
            ),
            {
                "atom_aliases": "{}",
                "field_file": dlp_field_with_grad,
                "fold": False,
                "history_file": dlp_history_with_grad,
            },
        ),
        (
            "DL_POLY",
            "dlp_awkward.mdt",
            (
                "/configuration/coordinates",
                "/unit_cell",
                "/time",
                "/charge",
            ),
            {
                "atom_aliases": "{}",
                "field_file": dlp_field_awkward,
                "fold": False,
                "history_file": dlp_history_awkward,
            },
        ),
        (
            "NAMD",
            "namd.mdt",
            ("/configuration/coordinates", "/unit_cell", "/time"),
            {
                "dcd_file": apoferritin_dcd,
                "fold": False,
                "pdb_file": apoferritin_pdb,
                "time_step": "1.0",
            },
        ),
        (
            "CASTEP",
            "castep.mdt",
            (
                "/configuration/coordinates",
                "/configuration/velocities",
                "/configuration/gradients",
                "/unit_cell",
                "/time",
            ),
            {"atom_aliases": "{}", "castep_file": pbanew_md, "fold": False},
        ),
        (
            "DFTB",
            "dftb.mdt",
            (
                "/configuration/coordinates",
                "/configuration/velocities",
                "/unit_cell",
                "/time",
                "/charge",
            ),
            {
                "atom_aliases": "{}",
                "fold": True,
                "trj_file": h2o_trj,
                "xtd_file": h2o_xtd,
            },
        ),
        (
            "Forcite",
            "forcite.mdt",
            (
                "/configuration/coordinates",
                "/configuration/velocities",
                "/unit_cell",
                "/time",
                "/charge",
            ),
            {
                "atom_aliases": "{}",
                "fold": False,
                "trj_file": h2o_trj,
                "xtd_file": h2o_xtd,
            },
        ),
        (
            "Gromacs",
            "md.mdt",
            ("/configuration/coordinates", "/unit_cell", "/time"),
            {"fold": False, "pdb_file": md_pdb, "xtc_file": md_xtc},
        ),
        (
            "Gromacs",
            "gromacs-nvt.mdt",
            ("/configuration/coordinates", "/unit_cell", "/time"),
            {"fold": False, "pdb_file": gromacs_nvt[0], "xtc_file": gromacs_nvt[1]},
        ),
        (
            "MDAnalysis",
            "md.mdt",
            ("/configuration/coordinates", "/unit_cell", "/time"),
            {
                "topology_file": (md_pdb, "AUTO"),
                "coordinate_files": ([str(md_xtc)], "XTC"),
            },
        ),  # Does not work with Path
        (
            "MDTraj",
            "hem_cam.mdt",
            ("/configuration/coordinates", "/unit_cell", "/time"),
            {
                "topology_file": hem_cam_pdb,
                "coordinate_files": [str(hem_cam_dcd)],  # Does not work with Path
                "time_step": 1.0,
            },
        ),
    ),
)
@pytest.mark.parametrize("compression", ["none", "gzip", "lzf"])
def test_build_mdt_file_and_load(
    tmp_path, converter_type, result, compare, parameters, compression
):
    _converter_test(tmp_path, converter_type, result, compare, parameters, compression)


@pytest.mark.parametrize(
    "unit_system", ["real", "metal", "si", "cgs", "electron", "micro", "nano"]
)
def test_lammps_mdt_conversion_unit_system(tmp_path, unit_system):
    _converter_test(
        tmp_path,
        "LAMMPS",
        f"lammps_{unit_system}.mdt",
        ("/configuration/coordinates", "/unit_cell", "/time", "/charge"),
        {
            "config_file": lammps_config,
            "mass_tolerance": 0.05,
            "n_steps": 0,
            "smart_mass_association": True,
            "time_step": 1.0,
            "trajectory_file": lammps_lammps,
            "lammps_units": unit_system,
        },
        "gzip",
    )


@pytest.mark.parametrize(
    "trajectory_file,trajectory_format",
    [(lammps_custom, "custom"), (lammps_xyz, "xyz"), (lammps_h5md, "h5md")],
)
def test_lammps_mdt_conversion_trajectory_format(
    tmp_path, trajectory_file, trajectory_format
):
    _converter_test(
        tmp_path,
        "LAMMPS",
        f"lammps_moly_{trajectory_format}.mdt",
        ("/configuration/coordinates", "/unit_cell", "/time", "/charge"),
        {
            "config_file": lammps_moly,
            "mass_tolerance": 0.05,
            "n_steps": 0,
            "smart_mass_association": True,
            "time_step": 1.0,
            "trajectory_file": trajectory_file,
            "trajectory_format": trajectory_format,
            "lammps_units": "electron",
        },
        "gzip",
    )


@pytest.mark.parametrize(
    "trajectory",
    (ase_traj, xyz_traj, vasp_xdatcar),
)
def test_improvedase_mdt_conversion_file_exists_and_loads_up_successfully(
    tmp_path, trajectory
):
    _converter_test(
        tmp_path,
        "improvedase",
        "ase.mdt",  # Dummy
        (),
        {
            "trajectory_file": str(trajectory),  # Does not work with Path
            "fold": False,
            "n_steps": 0,
            "time_step": 50.0,
            "time_unit": "fs",
        },
        "gzip",
    )


def test_lammps_mdt_conversion_raise_exception_with_incorrect_format(tmp_path):
    temp_name = tmp_path / "output"

    parameters = {
        "config_file": lammps_config,
        "mass_tolerance": 0.05,
        "n_steps": 0,
        "output_files": (temp_name, ["IncorrectFormat"], "INFO"),
        "smart_mass_association": True,
        "time_step": 1.0,
        "trajectory_file": lammps_lammps,
    }

    lammps = Converter.create("LAMMPS")
    with pytest.raises(JobError):
        lammps.run(parameters, status=True)


@pytest.mark.parametrize(
    "files",
    [
        ("lammps_ix_cubic_wrapped.dump", "lammps_ix_cubic_unwrapped.dump"),
        ("lammps_ix.dump", "lammps_ix_unwrapped.dump"),
    ],
    ids=["cubic", "nonorthogonal"],
)
def test_lammps_ix_unwrap(tmp_path, files):
    out_1 = tmp_path / "unwrapped"
    out_2 = tmp_path / "ix"

    out_1_name = out_1.with_suffix(".mdt")
    out_2_name = out_2.with_suffix(".mdt")

    parameters = {
        "config_file": DATA_DIR / "POSCAR.lmp",
        "mass_tolerance": 0.05,
        "n_steps": 0,
        "output_files": (out_1, 64, 128, "none", "INFO"),
        "smart_mass_association": True,
        "time_step": 1.0,
    }

    parameters["trajectory_file"] = DATA_DIR / files[0]
    converter = Converter.create("LAMMPS")
    converter.run(parameters, status=True)

    parameters["trajectory_file"] = DATA_DIR / files[1]
    parameters["output_files"] = (out_2, 64, 128, "none", "INFO")
    converter = Converter.create("LAMMPS")
    converter.run(parameters, status=True)

    compare_hdf5(out_1_name, out_2_name, ("/configuration/coordinates",), atol=1e-4)


@pytest.mark.parametrize(
    "config_file, expected",
    [
        (
            DATA_DIR / "POSCAR.lmp",
            {
                "atom_types": list(run_length.decode([(1, 16), (2, 92), (3, 178)])),
                "charges": [0] * 286,
                "elements": {1: "V", 2: "Bi", 3: "O"},
                "mass": [50.942, 208.98, 15.999],
                "n_angle_types": 0,
                "n_angles": 0,
                "n_atom_types": 3,
                "n_atoms": 286,
                "n_bond_types": 0,
                "n_bonds": 0,
                "n_dihedral_types": 0,
                "n_dihedrals": 0,
                "n_improper_types": 0,
                "n_impropers": 0,
                "origin": [0, 0, 0],
                "style": BoxStyle.NONORTHOGONAL,
                "unit_cell": [
                    [20.0293808, 0, 0],
                    [0, 11.59621143, 0],
                    [-7.68758428, 0, 19.68041541],
                ],
            },
        ),
        (
            DATA_DIR / "lammps_test.config",
            {
                "atom_types": [
                    1,
                    2,
                    3,
                    4,
                    5,
                    5,
                    5,
                    6,
                    6,
                    7,
                    8,
                    9,
                    10,
                    11,
                    10,
                    12,
                    6,
                    13,
                    13,
                    13,
                ],
                "bonds": [
                    (1, 2),
                    (1, 5),
                    (1, 6),
                    (1, 7),
                    (2, 3),
                    (2, 9),
                    (2, 8),
                    (3, 4),
                    (3, 10),
                    (10, 11),
                    (10, 16),
                    (11, 12),
                    (11, 14),
                    (11, 17),
                    (12, 13),
                    (12, 15),
                    (14, 18),
                    (14, 19),
                    (14, 20),
                ],
                "charges": [
                    -0.3,
                    0.13,
                    0.51,
                    -0.51,
                    0.33,
                    0.33,
                    0.33,
                    0.09,
                    0.09,
                    -0.47,
                    0.07,
                    0.34,
                    -0.67,
                    -0.27,
                    -0.67,
                    0.31,
                    0.09,
                    0.09,
                    0.09,
                    0.09,
                ],
                "elements": {
                    1: "1",
                    2: "2",
                    3: "3",
                    4: "4",
                    5: "5",
                    6: "6",
                    7: "7",
                    8: "8",
                    9: "9",
                    10: "10",
                    11: "11",
                    12: "12",
                    13: "13",
                },
                "mass": [
                    14.0067,
                    12.0107,
                    12.0107,
                    15.9994,
                    1.0079,
                    1.0079,
                    14.0067,
                    12.0107,
                    12.0107,
                    15.9994,
                    12.0107,
                    1.0079,
                    1.0079,
                ],
                "n_angle_types": 21,
                "n_angles": 33,
                "n_atom_types": 13,
                "n_atoms": 20,
                "n_bond_types": 12,
                "n_bonds": 19,
                "n_dihedral_types": 10,
                "n_dihedrals": 41,
                "n_improper_types": 3,
                "n_impropers": 3,
                "origin": [0, 0, 0],
                "style": BoxStyle.ORTHOGONAL,
                "unit_cell": [[40, 0, 0], [0, 40, 0], [0, 0, 40]],
            },
        ),
        (
            DATA_DIR / "lammps_2.config",
            {
                "atom_types": list(run_length.decode([(1, 250), (2, 250)])),
                "charges": [0] * 500,
                "elements": {1: "Mg", 2: "O"},
                "mass": [35.0, 16.0],
                "n_angle_types": 0,
                "n_angles": 0,
                "n_atom_types": 2,
                "n_atoms": 500,
                "n_bond_types": 0,
                "n_bonds": 0,
                "n_dihedral_types": 0,
                "n_dihedrals": 0,
                "n_improper_types": 0,
                "n_impropers": 0,
                "origin": [0, 0, 0],
                "style": BoxStyle.TRICLINIC,
                "timestep": "0",
                "unit_cell": [[17.6, 0.0, 0.0], [8.8, 17.6, 0.0], [0.0, 0.0, 8.8]],
                "units": "metal",
            },
        ),
        (
            lammps_cao_config,
            {
                "atom_types": (
                    ([5, 2] * (5966 // 2))  # O, Ca
                    + ([4, 5] * ((6984 - 5966) // 2))  # Mg, O
                    + ([1, 5] * ((8028 - 6983) // 2))  # Al, O
                    + ([1, 5, 5] * ((9594 - 8028) // 3))  # Al, O, O
                    + ([6, 5, 5] * ((16140 - 9594) // 3))  # Si, O, O,
                    + ([3, 5] * ((16150 - 16140) // 2))  # Fe, O
                ),  # Fe, O
                "charges": [0] * 16150,
                "elements": {1: "Al", 2: "Ca", 3: "Fe", 4: "Mg", 5: "O", 6: "Si"},
                "mass": [26.981539, 40.077999, 55.845001, 24.305, 15.9994, 28.085501],
                "n_angle_types": 0,
                "n_angles": 0,
                "n_atom_types": 6,
                "n_atoms": 16150,
                "n_bond_types": 0,
                "n_bonds": 0,
                "n_dihedral_types": 0,
                "n_dihedrals": 0,
                "n_improper_types": 0,
                "n_impropers": 0,
                "origin": [0.0, 0.0, 0.0],
                "style": BoxStyle.ORTHOGONAL,
                "unit_cell": [[59.6, 0.0, 0.0], [0.0, 59.6, 0.0], [0.0, 0.0, 59.6]],
            },
        ),
        (
            lammps_ar,
            {
                "atom_types": [1, 1, 1, 1],
                "charges": [0.0, 0.0, 0.0, 0.0],
                "elements": {1: "1"},
                "mass": [36.0],
                "n_angle_types": 0,
                "n_angles": 0,
                "n_atom_types": 1,
                "n_atoms": 4,
                "n_bond_types": 0,
                "n_bonds": 0,
                "n_dihedral_types": 0,
                "n_dihedrals": 0,
                "n_improper_types": 0,
                "n_impropers": 0,
                "origin": [0.0, 0.0, 0.0],
                "style": BoxStyle.ORTHOGONAL,
                "unit_cell": [[5.73, 0.0, 0.0], [0.0, 5.73, 0.0], [0.0, 0.0, 5.73]],
            },
        ),
    ], ids=lambda x: x.name if isinstance(x, Path) else None,
)
def test_lammps_config_parser(config_file, expected):
    conf = ConfigFileConfigurator("dummy_in")
    conf.parse(config_file)

    from pprint import pprint

    pprint(conf)

    for key in expected.keys() | conf.keys():
        if isinstance(conf[key], np.ndarray):
            np.testing.assert_allclose(conf[key], expected[key])
        else:
            assert conf.get(key) == expected.get(key)
