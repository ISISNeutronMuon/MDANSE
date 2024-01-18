# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/CenterOfMassesTrajectory.py
# @brief     Implements module/class/test CenterOfMassesTrajectory
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

import numpy as np


from MDANSE.Chemistry.ChemicalEntity import Atom, ChemicalSystem
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicRealConfiguration,
    RealConfiguration,
)
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.TrajectoryUtils import group_atoms


class CenterOfMassesTrajectory(IJob):
    """
    Creates a trajectory from the centre of masses for selected groups of atoms in a given input trajectory.
        For a molecular system, the centre of mass trajectory will contain only the molecular translations, which are therefore separated from the rotations.
    """

    label = "Center Of Masses Trajectory"

    category = (
        "Analysis",
        "Trajectory",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}, "default": (0, 1, 1)},
    )
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["fold"] = (
        "BooleanConfigurator",
        {"default": False, "label": "Fold coordinates in to box"},
    )
    settings["grouping_level"] = (
        "GroupingLevelConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
            }
        },
    )
    settings["output_file"] = (
        "OutputFilesConfigurator",
        {"formats": ["MDTFormat"]},
    )

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration["frames"]["number"]

        chemical_system = ChemicalSystem()
        for i in range(len(self.configuration["atom_selection"]["indexes"])):
            at = Atom(symbol="H", name="com_{:d}".format(i))
            chemical_system.add_chemical_entity(at)

        # The output trajectory is opened for writing.
        self._output_trajectory = TrajectoryWriter(
            self.configuration["output_file"]["files"][0],
            chemical_system,
            self.numberOfSteps,
        )

        self._grouped_atoms = group_atoms(
            self.configuration["trajectory"]["instance"].chemical_system,
            self.configuration["atom_selection"]["indexes"],
        )

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
            #. None
        """

        # get the Frame index
        frameIndex = self.configuration["frames"]["value"][index]

        n_coms = self._output_trajectory.chemical_system.number_of_atoms

        conf = self.configuration["trajectory"]["instance"].configuration(frameIndex)
        conf = conf.contiguous_configuration()

        com_coords = np.empty((n_coms, 3), dtype=np.float64)
        for i, group in enumerate(self._grouped_atoms):
            com_coords[i, :] = group.center_of_mass(conf)

        if conf.is_periodic:
            com_conf = PeriodicRealConfiguration(
                self._output_trajectory.chemical_system, com_coords, conf.unit_cell
            )
        else:
            com_conf = RealConfiguration(
                self._output_trajectory.chemical_system, com_coords
            )

        if self.configuration["fold"]["value"]:
            com_conf.fold_coordinates()

        self._output_trajectory.chemical_system.configuration = com_conf

        # The times corresponding to the running index.
        time = self.configuration["frames"]["time"][index]

        self._output_trajectory.dump_configuration(time)

        return index, None

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """
        pass

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        # The input trajectory is closed.
        self.configuration["trajectory"]["instance"].close()

        # The output trajectory is closed.
        self._output_trajectory.close()
