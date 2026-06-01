from __future__ import annotations

import os
import tempfile

import pytest
from test_helpers.compare_hdf5 import compare_hdf5
from test_helpers.paths import CONV_DIR, RESULTS_DIR

from MDANSE.Framework.Jobs.IJob import IJob

one_atom_traj = CONV_DIR / "one_atom_traj.mdt"
two_atom_traj = CONV_DIR / "two_atom_traj.mdt"


ALL_ANALYSES = (
    "CurrentCorrelationFunction",
    "Density",
    "DensityOfStates",
    "DynamicCoherentStructureFactor",
    "DynamicIncoherentStructureFactor",
    "Eccentricity",
    "ElasticIncoherentStructureFactor",
    "PositionPowerSpectrum",
    "GaussianDynamicIncoherentStructureFactor",
    "MeanSquareDisplacement",
    "MolecularTrace",
    "PositionCorrelationFunction",
    "RadiusOfGyration",
    "RootMeanSquareDeviation",
    "RootMeanSquareFluctuation",
    "ScatteringLengthDensityProfile",
    "SolventAccessibleSurface",
    "Temperature",
    "TrajectoryEditor",
    "TrajectoryFilter",
    "VanHoveFunctionDistinct",
    "VanHoveFunctionSelf",
    "VelocityCorrelationFunction",
    "Voronoi",
    "CoordinationNumber",
    "PairDistributionFunction",
    "StaticStructureFactor",
    "XRayStaticStructureFactor",
)


@pytest.mark.parametrize("jobname", ALL_ANALYSES)
def test_analysis_one_atom_total(generate_benchmarks, jobname, tmp_path):
    trajname = one_atom_traj
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    result_file = RESULTS_DIR / f"{trajname}_{jobname}.mda"

    if generate_benchmarks:
        temp_name = result_file.with_suffix("")

    parameters = {
        "output_files": (temp_name, ("MDAFormat",), "INFO"),
        "r_values": (0.0, 0.8, 0.01),
        "frames": "all",
        "running_mode": ("single-core",),
        "trajectory": trajname,
        "q_vectors": (
            "SphericalLatticeQVectors",
            {"shells": (0.1, 5, 0.1), "width": 0.1, "n_vectors": 50, "seed": 0},
        ),
    }
    if jobname in {"TrajectoryEditor", "TrajectoryFilter"}:
        parameters["output_files"] = (temp_name, 64, 128, "none", "INFO")
        out_file = temp_name.with_suffix(".mdt")

    elif jobname in ["AverageStructure"]:
        parameters["output_files"] = (temp_name, "vasp", "INFO")
        out_file = temp_name

    job = IJob.create(jobname)
    job.configuration = {
        key: value for key, value in parameters.items() if key in job.parameters
    }
    print(job)
    job.run(status=True)

    if generate_benchmarks:
        return

    print(temp_name, out_file, job)

    assert out_file.is_file()
    assert log_file.is_file()


@pytest.mark.parametrize("jobname", ALL_ANALYSES)
def test_analysis_one_atom_selected(generate_benchmarks, jobname, tmp_path):
    trajname = two_atom_traj
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    result_file = RESULTS_DIR / f"{trajname}_{jobname}.mda"

    if generate_benchmarks:
        temp_name = result_file.with_suffix("")

    parameters = {
        "output_files": (temp_name, ("MDAFormat",), "INFO"),
        "running_mode": ("single-core",),
        "r_values": (0.0, 0.7, 0.01),
        "frames": None,
        "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_dummy", "operation_type": "difference"}, "2": {"function_name": "select_atoms", "index_list": [0], "operation_type": "intersection"}}',
        "trajectory": trajname,
        "q_vectors": (
            "SphericalLatticeQVectors",
            {"shells": (0.1, 5, 0.1), "width": 0.1, "n_vectors": 50, "seed": 0},
        ),
    }

    if jobname in ["TrajectoryEditor", "TrajectoryFilter"]:
        parameters["output_files"] = (temp_name, 64, 128, "none", "INFO")
        out_file = temp_name.with_suffix(".mdt")
    elif jobname in ["AverageStructure"]:
        parameters["output_files"] = (temp_name, "vasp", "INFO")
        out_file = temp_name

    job = IJob.create(jobname)
    job.configuration = {
        key: value for key, value in parameters.items() if key in job.parameters
    }
    job.run(status=True)

    if generate_benchmarks:
        return

    print(temp_name, out_file)
    assert out_file.is_file()
    assert log_file.is_file()
