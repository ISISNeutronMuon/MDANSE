import numpy as np
import pytest
from test_helpers.compare_hdf5 import compare_hdf5
from test_helpers.paths import CONV_DIR, RESULTS_DIR

from MDANSE.Framework.Jobs.IJob import IJob

short_traj = CONV_DIR / "short_trajectory_after_changes.mdt"
com_traj = CONV_DIR / "com_trajectory.mdt"
mdmc_traj = CONV_DIR / "Ar_mdmc_h5md.h5"


@pytest.mark.parametrize("interp_order", [1, 3])
@pytest.mark.parametrize(
    "traj_info",
    [
        ("short_traj", short_traj),
        ("mdmc_traj", mdmc_traj),
        ("com_traj", com_traj),
    ],
    ids=lambda x: x[0],
)
def test_temperature(generate_benchmarks, tmp_path, traj_info, interp_order):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    result_file = RESULTS_DIR / f"temperature_{traj_info[0]}_{interp_order}.mda"

    if generate_benchmarks:
        temp_name = result_file.with_suffix("")

    parameters = {
        "frames": (0, 10, 1),
        "interpolation_order": interp_order,
        "output_files": (temp_name, ("MDAFormat",), "INFO"),
        "running_mode": ("single-core",),
        "trajectory": traj_info[1],
    }

    temp = IJob.create("Temperature")
    temp.run(parameters, status=True)

    if generate_benchmarks:
        return

    assert out_file.is_file()
    assert log_file.is_file()

    compare_hdf5(
        out_file,
        result_file,
        (
            "temp/kinetic_energy",
            "temp/temperature",
            "temp/avg_kinetic_energy",
            "temp/avg_temperature",
        ),
    )


@pytest.mark.parametrize(
    "traj_info",
    [
        ("short_traj", short_traj),
        ("mdmc_traj", mdmc_traj),
        ("com_traj", com_traj),
    ],
    ids=lambda x: x[0],
)
@pytest.mark.parametrize("output_format", ["MDAFormat", "TextFormat", "FileInMemory"])
def test_density(generate_benchmarks, tmp_path, traj_info, output_format):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    result_file = RESULTS_DIR / f"density_{traj_info[0]}.mda"

    if generate_benchmarks:
        temp_name = result_file.with_suffix("")

    parameters = {
        "frames": (0, 10, 1),
        "output_files": (temp_name, (output_format,), "INFO"),
        "running_mode": ("single-core",),
        "trajectory": traj_info[1],
    }
    den = IJob.create("Density")
    den.run(parameters, status=True)

    if generate_benchmarks:
        return

    if output_format == "MDAFormat":
        out_file = temp_name.with_suffix(".mda")

        assert out_file.is_file()

        compare_hdf5(
            out_file,
            result_file,
            (
                "density/atomic/density",
                "density/mass/density",
                "density/atomic/avg_density",
                "density/mass/avg_density",
            ),
            startswith=True,
        )

    elif output_format == "TextFormat":
        out_file = temp_name.parent / (temp_name.stem + "_text.tar")
        assert out_file.is_file()

    assert log_file.is_file()
