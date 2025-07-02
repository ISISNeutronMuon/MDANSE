import numpy as np
import pytest
from test_helpers.compare_hdf5 import compare_hdf5
from test_helpers.paths import CONV_DIR, RESULTS_DIR

from MDANSE.Framework.Jobs.IJob import IJob

short_traj = CONV_DIR / "short_trajectory_after_changes.mdt"
mdmc_traj = CONV_DIR / "Ar_mdmc_h5md.h5"
com_traj = CONV_DIR / "com_trajectory.mdt"


@pytest.mark.parametrize("interp_order", [1, 2, 3])
def test_vacf(generate_benchmarks, tmp_path, interp_order):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    result_file = RESULTS_DIR / f"vacf_{interp_order}.mda"

    if generate_benchmarks:
        temp_name = result_file.with_suffix("")

    result_file = RESULTS_DIR / f"vacf_{interp_order}.mda"

    parameters = {
        "frames": (0, 10, 1, 5),
        "interpolation_order": interp_order,
        "output_files": (temp_name, ("MDAFormat",), "INFO"),
        "running_mode": ("single-core",),
        "trajectory": short_traj,
    }

    vacf = IJob.create("VelocityAutoCorrelationFunction")
    vacf.run(parameters, status=True)

    if generate_benchmarks:
        return

    assert out_file.is_file()
    assert log_file.is_file()

    compare_hdf5(
        out_file,
        result_file,
        [f"/vacf/{elem}" for elem in ("Cu", "S", "Sb", "total")],
        scale_result=False,
    )


def test_pps(generate_benchmarks, tmp_path):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    result_file = RESULTS_DIR / "pps.mda"

    if generate_benchmarks:
        temp_name = result_file.with_suffix("")

    parameters = {
        "frames": (0, 10, 1, 5),
        "output_files": (temp_name, ("MDAFormat",), "INFO"),
        "running_mode": ("single-core",),
        "trajectory": short_traj,
    }

    pps = IJob.create("PositionPowerSpectrum")
    pps.run(parameters, status=True)

    if generate_benchmarks:
        return

    assert out_file.is_file()
    assert log_file.is_file()

    compare_hdf5(
        out_file,
        result_file,
        [
            f"{fn}/{elem}"
            for elem in ("Cu", "S", "Sb", "total")
            for fn in ("pacf", "pps")
        ],
        scale_result=True,
        scale_benchmark=True,
    )


################################################################
# Job parameters                                               #
################################################################
@pytest.fixture(scope="function")
def parameters():
    parameters = {
        # "atom_selection": None,
        # "atom_transmutation": None,
        # "frames": (0, 1000, 1),
        "trajectory": short_traj,
        "running_mode": ("multicore", -4),
        "q_vectors": (
            "SphericalLatticeQVectors",
            {
                "seed": 0,
                "shells": (0, 5.0, 0.5),
                "n_vectors": 100,
                "width": 0.5,
            },
        ),
        "q_values": (0.0, 10.0, 0.1),
        "r_values": (0.0, 0.9, 0.01),
        "per_axis": False,
        "reference_direction": (0, 0, 1),
        "instrument_resolution": ("Gaussian", {"sigma": 1.0, "mu": 0.0}),
        "interpolation_order": 3,
        "projection": None,
        "grouping_level": "atom",
        "weights": "equal",
    }
    return parameters


@pytest.mark.parametrize(
    "traj_info",
    [("short_traj", short_traj), ("mdmc_traj", mdmc_traj), ("com_traj", com_traj)],
    ids=lambda x: x[0],
)
@pytest.mark.parametrize(
    "job_info",
    [
        # "AngularCorrelation",
        # "GeneralAutoCorrelationFunction",
        ("DensityOfStates", ["dos", "vacf"], False),
        ("MeanSquareDisplacement", ["msd"], False),
        ("VelocityAutoCorrelationFunction", ["vacf"], False),
        ("VanHoveFunctionDistinct", ["g(r,t)"], False),
        ("VanHoveFunctionSelf", ["g(r,t)"], False),
        # "OrderParameter",
        ("PositionAutoCorrelationFunction", ["pacf"], False),
        ("PositionPowerSpectrum", ["pacf", "pps"], False),
    ],
    ids=lambda x: x[0],
)
@pytest.mark.parametrize(
    "running_mode", [("single-core", 1), ("multicore", -4)], ids=lambda x: x[0]
)
@pytest.mark.parametrize("output_format", ["MDAFormat", "TextFormat"])
def test_dynamics_analysis(
    generate_benchmarks,
    tmp_path,
    parameters,
    traj_info,
    job_info,
    running_mode,
    output_format,
):
    job_type, outputs, normalised = job_info
    outputs = tuple(outputs)

    temp_name = tmp_path / "output"
    log_file = temp_name.with_suffix(".log")
    result_file = RESULTS_DIR / f"dynamics_analysis_{traj_info[0]}_{job_type}.mda"

    if generate_benchmarks:
        temp_name = result_file.with_suffix("")

    parameters["trajectory"] = traj_info[1]
    parameters["running_mode"] = running_mode
    parameters["output_files"] = (temp_name, (output_format,), "INFO")

    job = IJob.create(job_type)
    job.run(parameters, status=True)

    if generate_benchmarks:
        return

    if output_format == "MDAFormat":
        out_file = temp_name.with_suffix(".mda")

        assert out_file.is_file()

        compare_hdf5(
            out_file, result_file, outputs, startswith=True, scale_result=normalised
        )

    elif output_format == "TextFormat":
        out_file = temp_name.parent / (temp_name.stem + "_text.tar")
        assert out_file.is_file()

    assert log_file.is_file()


def test_output_axis_preview(tmp_path, parameters):
    temp_name = tmp_path / "output"

    parameters["running_mode"] = ("single-core", 1)
    parameters["output_files"] = (temp_name, ("MDAFormat",), "INFO")
    job = IJob.create("DensityOfStates")
    job.setup(parameters)
    axes = job.preview_output_axis()
    assert len(axes) == 2  # two configurators return valid arrays
