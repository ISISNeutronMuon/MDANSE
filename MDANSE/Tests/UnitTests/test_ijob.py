import os
import pytest
import tempfile
from MDANSE.Framework.Jobs.IJob import IJob


ALL_JOBS = [
    "AreaPerMolecule",
    "AverageStructure",
    "CenterOfMassesTrajectory",
    "DistanceHistogram",
    "CroppedTrajectory",
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
    "GeneralAutoCorrelationFunction",
    "GlobalMotionFilteredTrajectory",
    "McStasVirtualInstrument",
    "MeanSquareDisplacement",
    "MolecularTrace",
    "NeutronDynamicTotalStructureFactor",
    "OrderParameter",
    "PositionAutoCorrelationFunction",
    "RadiusOfGyration",
    "RigidBodyTrajectory",
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
    "UnfoldedTrajectory",
    "VanHoveFunctionDistinct",
    "VanHoveFunctionSelf",
    "VelocityAutoCorrelationFunction",
    "Voronoi",
    "Converter",
    "CoordinationNumber",
    "PairDistributionFunction",
    "StaticStructureFactor",
    "XRayStaticStructureFactor",
    "ASE",
    "CASTEP",
    "DCD",
    "CP2K",
    "Forcite",
    "DL_POLY",
    "Gromacs",
    "ImprovedASE",
    "LAMMPS",
    "MDAnalysis",
    "MDTraj",
    "VASP",
    "CHARMM",
    "NAMD",
    "XPLOR",
    "DFTB",
    "Infrared",
]


def test_create_template_with_the_wrong_jobname_raises_error():
    temp_name = tempfile.mktemp()
    with pytest.raises(Exception):
        IJob.create("QWERTY").save(temp_name)


def test_indirect_subclasses_creates_list_of_all_possible_jobs():
    assert set(ALL_JOBS) == set(IJob.indirect_subclasses())


@pytest.mark.parametrize("jobname", ALL_JOBS)
def test_create_template_with_correct_jobname(jobname):
    temp_name = tempfile.mktemp()
    IJob.create(jobname).save(temp_name)
    assert os.path.exists(temp_name)
    assert os.path.isfile(temp_name)
    os.remove(temp_name)
