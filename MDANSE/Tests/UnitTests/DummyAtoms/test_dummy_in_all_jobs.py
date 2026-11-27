import copy
import pytest

import pytest
from test_helpers.compare_hdf5 import compare_hdf5
from test_helpers.paths import CONV_DIR, RESULTS_DIR

from MDANSE.Framework.Jobs.IJob import IJob

dummy_atom_traj = CONV_DIR / "mini_TIP4P_water.mdt"

ALL_ANALYSIS_JOBS = [
    "AreaPerMolecule",
    "AverageStructure",
    "CenterOfMassesTrajectory",
    "CurrentCorrelationFunction",
    "Density",
    "DensityOfStates",
    "DipoleAutoCorrelationFunction",
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
    "RotationAutocorrelation",
    "ReorientationalTimeCorrelationFunction",
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
    "StaticStructureFactor3D",
    "XRayStaticStructureFactor",
    "Infrared",
]


start_parameters = {
    'derivative_order': 2,  # Order of the derivative of the dipole moment
    'grouping_level': 'molecule',  # Grouping level. The partial results can be separated between different molecule types.
    'frames': [0, 100, 1, 50],  # Frame sampling and correlation frames. The values are: first frame, last frame, step size.
    'instrument_resolution': ('ideal', {}),  # Instrument resolution function
    'molecule_name': 'Du1_H2_O1',  # Molecule type
    'molecule_and_axis': ('Du1_H2_O1', 1, 2),  # Axis in a molecule. Molecule type and the indices of atoms defining a vector in the molecule.
    'per_axis': False,  # Decompose the results into per-axis contributions
    'polynomial_order': '2',  # Maximum Legendre polynomial order. All the orders up to this one will be calculated.
    'trajectory_filter': """{
        "filter": "Butterworth",
        "attributes": {
            "order": 2,
            "attenuation_type": "lowpass",
            "cutoff_freq": 10.0
        }
    }"""
}


@pytest.mark.parametrize("jobname", ALL_ANALYSIS_JOBS)
def test_analysis_one_atom_total(generate_benchmarks, jobname, tmp_path):
    trajname = dummy_atom_traj
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    result_file = RESULTS_DIR / f"{trajname}_{jobname}.mda"

    if generate_benchmarks:
        temp_name = result_file.with_suffix("")

    parameters = copy.deepcopy(start_parameters)
    parameters.update({
        "output_files": (temp_name, ("MDAFormat",), "INFO"),
        "r_values": (0.0, 0.8, 0.01),
        "frames": None,
        "running_mode": ("single-core",),
        "trajectory": trajname,
    })
    if jobname in {"CenterOfMassesTrajectory", "TrajectoryEditor", "TrajectoryFilter"}:
        parameters["output_files"] = (temp_name,  64, (128, 128), "none", "INFO")
        out_file = temp_name.with_suffix(".mdt")
    elif jobname in {"AverageStructure"}:
        parameters["output_files"] = (temp_name, "vasp", "INFO")
        out_file = temp_name

    job = IJob.create(jobname, trajectory_input="mdanse")
    job.run(parameters, status=True)

    if generate_benchmarks:
        return

    print(temp_name, out_file, job.configuration["output_files"]._original_input)

    assert out_file.is_file()
    assert log_file.is_file()
