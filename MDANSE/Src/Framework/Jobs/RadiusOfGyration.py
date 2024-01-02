# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/RadiusOfGyration.py
# @brief     Implements module/class/test RadiusOfGyration
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
from MDANSE.MolecularDynamics.Analysis import radius_of_gyration


class RadiusOfGyration(IJob):
    """
    Radius Of Gyration (ROG) is a measure of the size of an object,
    a surface, or an ensemble of points. It is calculated as the Root Mean Square Distance between
    the system and a reference which, in MDANSE, is the centre of gravity of the system.
    """

    label = "Radius of Gyration"

    category = (
        "Analysis",
        "Structure",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = ("FramesConfigurator", {"dependencies": {"trajectory": "trajectory"}})
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["weights"] = (
        "WeightsConfigurator",
        {"dependencies": {"atom_selection": "atom_selection"}},
    )
    settings["output_files"] = ("OutputFilesConfigurator", {"formats": ["HDFFormat", "ASCIIFormat"]})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """
        Computes the pair distribution function for a set of atoms.
        """
        self.numberOfSteps = self.configuration["frames"]["number"]

        # Will store the time.
        self._outputData.add(
            "time", "LineOutputVariable", self.configuration["frames"]["time"], units="ps"
        )

        self._outputData.add(
            "rog",
            "LineOutputVariable",
            (self.configuration["frames"]["number"],),
            axis="time",
            units="nm",
        )

        self._indexes = [
            idx
            for idxs in self.configuration["atom_selection"]["indexes"]
            for idx in idxs
        ]

        self._masses = np.array(
            [
                m
                for masses in self._configuration["atom_selection"]["masses"]
                for m in masses
            ],
            dtype=np.float64,
        )

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
            #. rog (float): The radius of gyration
        """

        # get the Frame index
        frameIndex = self.configuration["frames"]["value"][index]

        conf = self.configuration["trajectory"]["instance"].configuration(frameIndex)

        rog = radius_of_gyration(
            conf["coordinates"][self._indexes, :], masses=self._masses, root=True
        )

        return index, rog

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        self._outputData["rog"][index] = x

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """
        # Write the output variables.
        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
        )

        self.configuration["trajectory"]["instance"].close()
