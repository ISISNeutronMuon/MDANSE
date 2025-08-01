import os
import tempfile

import h5py
import numpy as np
import pytest
from test_helpers.compare_hdf5 import compare_hdf5
from test_helpers.paths import CONV_DIR, RESULTS_DIR

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Trajectory import Trajectory

short_traj = CONV_DIR / "Ar_mdmc_h5md.h5"


@pytest.fixture(scope="module")
def trajectory():
    trajectory = Trajectory(short_traj)
    yield trajectory


@pytest.mark.parametrize("interp_order", [1, 3])
def test_h5md_temperature(generate_benchmarks, tmp_path, trajectory, interp_order):
    pos = trajectory.coordinates(0)
    result_file = RESULTS_DIR / f"h5md_temperature_{interp_order}.mda"

    print(f"Coordinates span: {pos.min()}, {pos.max()}")
    print(f"Trajectory length: {len(trajectory)}")
    print(f"Positions array shape: {trajectory.variable('position').shape}")

    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    result_file = RESULTS_DIR / f"h5md_temperature_{interp_order}.mda"

    if generate_benchmarks:
        temp_name = result_file.with_suffix("")

    parameters = {
        "frames": (0, 39, 1),
        "interpolation_order": interp_order,
        "output_files": (temp_name, ("MDAFormat",), "INFO"),
        "running_mode": ("single-core",),
        "trajectory": short_traj,
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
        compare_axis=True,
    )
