import os
import pytest
import tempfile
from MDANSE.Framework.Jobs.IJob import IJob


ALL_JOBS = [
    "AngularCorrelation",
    "AreaPerMolecule",
    "CenterOfMassesTrajectory",
    "DistanceHistogram",
    "CroppedTrajectory",
    "CurrentCorrelationFunction",
    "Density",
    "DensityOfStates",
    "DensityProfile",
    "DipoleAutoCorrelationFunction",
    "DynamicCoherentStructureFactor",
    "DynamicIncoherentStructureFactor",
    "Eccentricity",
    "ElasticIncoherentStructureFactor",
    "GaussianDynamicIncoherentStructureFactor",
    "GeneralAutoCorrelationFunction",
    "GlobalMotionFilteredTrajectory",
    "McStasVirtualInstrument",
    "MeanSquareDisplacement",
    "MolecularTrace",
    "MoleculeFinder",
    "NeutronDynamicTotalStructureFactor",
    "OrderParameter",
    "PositionAutoCorrelationFunction",
    "RadiusOfGyration",
    "RigidBodyTrajectory",
    "RootMeanSquareDeviation",
    "RootMeanSquareFluctuation",
    "SolventAccessibleSurface",
    "StructureFactorFromScatteringFunction",
    "Temperature",
    "UnfoldedTrajectory",
    "VelocityAutoCorrelationFunction",
    "Voronoi",
    "InteractiveConverter",
    "Converter",
    "CoordinationNumber",
    "PairDistributionFunction",
    "StaticStructureFactor",
    "XRayStaticStructureFactor",
    "ASEInteractiveConverter",
    "ASE",
    "CASTEP",
    "DCD",
    "CP2K",
    "Forcite",
    "Discover",
    "DL_POLY",
    "Gromacs",
    "ImprovedASE",
    "LAMMPS",
    "VASP",
    "CHARMM",
    "NAMD",
    "XPLOR",
    "DFTB",
    "DMol",
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
