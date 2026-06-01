from __future__ import annotations

import os
import tempfile

import pytest

from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Jobs.IJob import IJob

ALL_JOBS = [
    "AreaPerMolecule",
    "AverageStructure",
    "CartesianCorrelationFunction",
    "CartesianPowerSpectrum",
    "CenterOfMassesTrajectory",
    "DistanceHistogram",
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
    "NeutronDynamicTotalStructureFactor",
    "PositionCorrelationFunction",
    "RadiusOfGyration",
    "RootMeanSquareDeviation",
    "RootMeanSquareFluctuation",
    "RotationAutocorrelation",
    "ReorientationalTimeCorrelationFunction",
    "ScatteringLengthDensityProfile",
    "SolventAccessibleSurface",
    "StructureFactorFromScatteringFunction",
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
    "Infrared",
    # Converter
    "Converter",
    "ASE",
    "CASTEP",
    "DCD",
    "CP2K",
    "Forcite",
    "DL_POLY",
    "Gromacs",
    "LAMMPS",
    "MDAnalysis",
    "MDTraj",
    "VASP",
    "CHARMM",
    "NAMD",
    "XPLOR",
    "DFTB",
]

CONVERTER_JOBS = [
    "ASE",
    "CASTEP",
    "DCD",
    "CP2K",
    "Forcite",
    "DL_POLY",
    "Gromacs",
    "LAMMPS",
    "MDAnalysis",
    "MDTraj",
    "VASP",
    "CHARMM",
    "NAMD",
    "XPLOR",
    "DFTB",
]


def test_create_template_with_the_wrong_jobname_raises_error():
    temp_name = tempfile.mktemp()
    with pytest.raises(Exception):
        IJob.create("QWERTY").save(temp_name)


def test_indirect_subclasses_creates_list_of_all_possible_jobs():
    assert set(ALL_JOBS) == set(IJob.indirect_subclasses())


def test_indirect_subclasses_creates_list_of_all_possible_converters():
    assert set(CONVERTER_JOBS) == set(Converter.indirect_subclasses())


@pytest.mark.parametrize("jobname", ALL_JOBS)
def test_create_template_with_correct_jobname(tmp_path, jobname):
    temp_name = tmp_path / jobname
    IJob.create(jobname).save(temp_name)
    assert temp_name.is_file()
