import numpy as np
import pytest
from test_helpers.compare_hdf5 import compare_hdf5
from test_helpers.paths import CONV_DIR, RESULTS_DIR

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Jobs.VanHoveFunctionDistinct import van_hove_distinct
from MDANSE.MolecularDynamics.UnitCell import UnitCell

short_traj = CONV_DIR / "short_trajectory_after_changes.mdt"
mdmc_traj = CONV_DIR / "Ar_mdmc_h5md.h5"
com_traj = CONV_DIR / "com_trajectory.mdt"
nonorth_traj = CONV_DIR / "nonorthogonal_cell.mdt"
molecule_traj = CONV_DIR / "named_molecules.mdt"
cubane_traj = CONV_DIR / "four_molecules.mdt"


################################################################
# Job parameters                                               #
################################################################
@pytest.fixture(scope="function")
def parameters():
    parameters = {}
    # parameters['atom_selection'] = None
    # parameters['atom_transmutation'] = None
    # parameters['frames'] = (0, 1000, 1)
    parameters["trajectory"] = short_traj
    parameters["running_mode"] = ("multicore", -4)
    parameters["q_vectors"] = (
        "SphericalLatticeQVectors",
        {
            "seed": 0,
            "shells": (0, 5.0, 0.5),
            "n_vectors": 100,
            "width": 0.5,
        },
    )
    parameters["q_values"] = (0.0, 10.0, 0.1)
    parameters["r_values"] = (0.0, 0.9, 0.1)
    parameters["per_axis"] = False
    parameters["reference_direction"] = (0, 0, 1)
    parameters["instrument_resolution"] = ("Gaussian", {"sigma": 1.0, "mu": 0.0})
    parameters["interpolation_order"] = "3rd order"
    parameters["projection"] = None
    parameters["weights"] = "equal"
    return parameters


@pytest.mark.parametrize(
    "traj_info",
    [
        ("short_traj", short_traj),
        ("mdmc_traj", mdmc_traj),
        ("com_traj", com_traj),
        ("mol_traj", molecule_traj),
    ],
    ids=lambda x: x[0],
)
@pytest.mark.parametrize(
    "job_info",
    [
        ("SolventAccessibleSurface", ["sas/sas"]),
        ("RootMeanSquareDeviation", ["rmsd/total"]),
        ("RootMeanSquareFluctuation", ["rmsf/rmsf"]),
        ("Voronoi", ["voronoi/mean_volume", "voronoi/neighbourhood_histogram"]),
        ("CoordinationNumber", ["cn/cn"]),
        ("PairDistributionFunction", ["pdf/total", "rdf/total", "tcf/total"]),
        ("StaticStructureFactor", ["ssf/total"]),
        ("XRayStaticStructureFactor", ["xssf/total"]),
    ],
    ids=lambda x: x[0],
)
@pytest.mark.parametrize("running_mode", [("single-core", 1)], ids=lambda x: x[0])
@pytest.mark.parametrize("output_format", ["MDAFormat"])
def test_structure_analysis(
    generate_benchmarks,
    tmp_path,
    parameters,
    traj_info,
    job_info,
    running_mode,
    output_format,
):
    job_type, outputs = job_info
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    result_file = RESULTS_DIR / f"structure_analysis_{traj_info[0]}_{job_type}.mda"

    if generate_benchmarks:
        temp_name = result_file.with_suffix("")

    parameters["trajectory"] = traj_info[1]
    parameters["running_mode"] = running_mode
    parameters["output_files"] = (temp_name, (output_format,), "INFO")

    job = IJob.create(job_info[0])
    job.run(parameters, status=True)

    if generate_benchmarks:
        return

    if output_format == "MDAFormat":
        out_file = temp_name.with_suffix(".mda")

        assert out_file.is_file()

        compare_hdf5(out_file, result_file, tuple(outputs), startswith=True)

    elif output_format == "TextFormat":
        out_file = temp_name.parent / (temp_name.stem + "_text.tar")
        assert out_file.is_file()

    assert log_file.is_file()


@pytest.mark.parametrize(
    "traj_info",
    [
        ("short_traj", short_traj),
        ("mdmc_traj", mdmc_traj),
        ("com_traj", com_traj),
        ("nonorthogonal_cell", nonorth_traj),
    ],
    ids=lambda x: x[0],
)
def test_pdf_is_zero_at_low_distances(
    tmp_path,
    parameters,
    traj_info,
):
    temp_name = tmp_path / "output"

    job_type = "PairDistributionFunction"

    parameters["trajectory"] = traj_info[1]
    parameters["r_values"] = (0.0, 0.5, 0.01)
    parameters["output_files"] = (temp_name, ("FileInMemory",), "no logs")

    print(parameters)
    job = IJob.create(job_type)
    job.run(parameters, status=True)
    results = job.results

    print(results.keys())

    assert "pdf/total" in results
    x_axis = results["pdf/axes/r"][:]
    y_axis = results["pdf/total"][:]
    banned_range = y_axis[np.where(x_axis < 0.05)]
    assert np.allclose(banned_range, 0.0)


def test_vhd():
    temp_cell = UnitCell(2 * np.eye(3))
    coords1 = np.array(
        [
            [0.1, 0.1, 0.1],
            [0.0, 0.0, 0.0],
            [0.2, 0.0, 0.0],
            [0.1, 0.2, 0.0],
            [0.2, 0.2, 0.2],
            [0.0, 0.0, 0.2],
        ]
    )
    coords2 = coords1 + np.array([0.0, 0.5, 0.0])
    frac_coords1 = coords1 @ temp_cell.inverse
    frac_coords2 = coords2 @ temp_cell.inverse
    intra, total = van_hove_distinct(
        2 * np.eye(3),
        np.array([0, 1, 1, -3, 1, -5], dtype=int),
        np.array([0, 0, 0, 0, 0, 0], dtype=int),
        np.zeros((1, 1, 30)),
        np.zeros((1, 1, 30)),
        frac_coords1,
        frac_coords2,
        0.0,
        0.05,
    )
    expected_intra = np.array(
        [
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            1.0,
            0.0,
            2.0,
            0.0,
            0.0,
            0.0,
            1.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ]
    )
    expected_inter = np.array(
        [
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            2.0,
            2.0,
            5.0,
            0.0,
            4.0,
            2.0,
            5.0,
            0.0,
            4.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ]
    )
    np.testing.assert_almost_equal(
        intra[0, 0, :], expected_intra, decimal=3, err_msg="Failed at intra"
    )
    np.testing.assert_almost_equal(
        total[0, 0, :] - intra[0, 0, :],
        expected_inter,
        decimal=3,
        err_msg="Failed at inter",
    )


def test_intermolecular_part_is_zero_for_single_molecule(tmp_path, parameters):
    temp_name = tmp_path / "output"

    job_type = "PairDistributionFunction"

    parameters["trajectory"] = cubane_traj
    parameters["r_values"] = (0.0, 0.5, 0.01)
    parameters["atom_selection"] = (
        '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_sphere", "frame_number": 0, "sphere_centre": [1.5, 1.5, 1.5], "sphere_radius": 0.5, "operation_type": "intersection"}}'
    )
    parameters["output_files"] = (temp_name, ("FileInMemory",), "no logs")

    job = IJob.create(job_type)
    job.run(parameters, status=True)
    results = job.results

    print(results.keys())

    assert "pdf/inter/total" in results
    assert "pdf/intra/total" in results
    np.testing.assert_allclose(results["pdf/inter/total"], 0.0, equal_nan=True)
