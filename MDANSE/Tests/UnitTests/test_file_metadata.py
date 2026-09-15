from collections.abc import Iterable

import numpy as np
import pytest
from pathlib import Path

from MDANSE.Framework.Formats.HDFFormat import get_input_params
from test_helpers.paths import CONV_DIR, RESULTS_DIR

from MDANSE.Framework.Jobs.IJob import IJob

one_atom_traj = CONV_DIR / "one_atom_traj.mdt"
two_atom_traj = CONV_DIR / "two_atom_traj.mdt"


ALL_ANALYSES = [
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
]

SKIP_ENTRIES = ["output_files", "frames"]


def values_match(val1, val2) -> bool:
    """Check if the values are the same.
    
    This is meant to ignore type differences and return True when comparing
    a list [1,2,3] to a tuple (1,2,3)."""
    if isinstance(val1, Path) or isinstance(val2, Path):
        val1, val2 = str(val1), str(val2)
    if isinstance(val1, str) and isinstance(val2, str):
        return val1 == val2
    elif isinstance(val1, Iterable) and isinstance(val2, Iterable):
        return all(values_match(x[0], x[1]) for x in zip(val1, val2, strict=True))
    else:
        return val1 == val2



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
        "frames": None,
        "running_mode": ("single-core",),
        "trajectory": trajname,
    }
    if jobname in ["TrajectoryEditor", "TrajectoryFilter"]:
        parameters["output_files"] = (temp_name,  64, 128, "none", "INFO")
        out_file = temp_name.with_suffix(".mdt")
    elif jobname in ["AverageStructure"]:
        parameters["output_files"] = (temp_name, "vasp", "INFO")
        out_file = temp_name

    job = IJob.create(jobname, trajectory_input="mdanse")
    try:
        job.run(parameters, status=True)
    except:
        for name, conf in job.configuration.items():
            print(name, conf.error_status)
        raise RuntimeError()

    if generate_benchmarks:
        return

    print(temp_name, out_file, job.configuration["output_files"]._original_input)

    assert out_file.is_file()
    mdata = get_input_params(out_file)
    print(f"params - file: {set(parameters.keys()) - set(mdata.keys())}")
    print(f"file - params: {set(mdata.keys()) - set(parameters.keys())}")
    mismatched = {}
    correct = {}
    for key, value in mdata.items():
        if key in SKIP_ENTRIES or parameters[key] is None or parameters[key] == '':
            continue
        if not values_match(value, parameters[key]):
            mismatched[key] = (value, parameters[key])
        else:
            correct[key] = value
    print(f"mismatched: {mismatched}")
    print(f"correct: {correct}")
    assert not len(mismatched)
