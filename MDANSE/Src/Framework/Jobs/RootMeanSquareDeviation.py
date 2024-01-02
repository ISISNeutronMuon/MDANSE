# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/RootMeanSquareDeviation.py
# @brief     Implements module/class/test RootMeanSquareDeviation
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

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.MolecularDynamics.TrajectoryUtils import sorted_atoms


class RootMeanSquareDeviation(IJob):
    """
    The Root Mean-Square Deviation (RMSD) is one of the most popular measures of structural similarity.
    It is a numerical measure of the difference between two structures. Typically, the RMSD is used to
    quantify the structural evolution of the system during the simulation.
    It can provide essential information about the structure, if it reached equilibrium or conversely
    if major structural changes occurred during the simulation.
    """

    label = "Root Mean Square Deviation"

    category = (
        "Analysis",
        "Structure",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = ("FramesConfigurator", {"dependencies": {"trajectory": "trajectory"}})
    settings["reference_frame"] = ("IntegerConfigurator", {"mini": 0, "default": 0})
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["grouping_level"] = (
        "GroupingLevelConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
                "atom_transmutation": "atom_transmutation",
            }
        },
    )
    settings["atom_transmutation"] = (
        "AtomTransmutationConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
            }
        },
    )
    settings["weights"] = (
        "WeightsConfigurator",
        {"dependencies": {"atom_selection": "atom_selection"}},
    )
    settings["output_files"] = ("OutputFilesConfigurator", {"formats": ["HDFFormat", "ASCIIFormat"]})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        self.numberOfSteps = self.configuration["atom_selection"]["selection_length"]

        self._referenceIndex = self.configuration["reference_frame"]["value"]

        # Will store the time.
        self._outputData.add(
            "time", "LineOutputVariable", self.configuration["frames"]["duration"], units="ps"
        )

        # Will store the mean square deviation
        for element in self.configuration["atom_selection"]["unique_names"]:
            self._outputData.add(
                "rmsd_{}".format(element),
                "LineOutputVariable",
                (self.configuration["frames"]["number"],),
                axis="time",
                units="nm",
            )

        self._atoms = sorted_atoms(
            self.configuration["trajectory"]["instance"].chemical_system.atom_list
        )

    def run_step(self, index):
        """
        Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.
        """

        indexes = self.configuration["atom_selection"]["indexes"][index]
        atoms = [self._atoms[idx] for idx in indexes]

        series = self.configuration["trajectory"]["instance"].read_com_trajectory(
            atoms,
            first=self.configuration["frames"]["first"],
            last=self.configuration["frames"]["last"] + 1,
            step=self.configuration["frames"]["step"],
        )

        # Compute the squared sum of the difference between all the coordinate of atoms i and the reference ones
        squaredDiff = np.sum((series - series[self._referenceIndex, :]) ** 2, axis=1)

        return index, squaredDiff

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        element = self.configuration["atom_selection"]["names"][index]

        self._outputData["rmsd_%s" % element] += x

    def finalize(self):
        """
        Finalize the job.
        """

        # The RMSDs per element are averaged.
        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        for element, number in nAtomsPerElement.items():
            self._outputData["rmsd_{}".format(element)] /= number

        weights = self.configuration["weights"].get_weights()
        rmsdTotal = weight(weights, self._outputData, nAtomsPerElement, 1, "rmsd_%s")
        rmsdTotal = np.sqrt(rmsdTotal)
        self._outputData.add("rmsd_total", "LineOutputVariable", rmsdTotal, axis="time", units="nm")

        for element, number in nAtomsPerElement.items():
            self._outputData["rmsd_{}".format(element)] = np.sqrt(
                self._outputData["rmsd_{}".format(element)]
            )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
        )

        self.configuration["trajectory"]["instance"].close()
