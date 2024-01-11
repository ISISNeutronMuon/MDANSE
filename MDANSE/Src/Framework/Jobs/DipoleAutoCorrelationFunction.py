# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/DipoleAutoCorrelationFunction.py
# @brief     Implements module/class/test DipoleAutoCorrelationFunction
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


from MDANSE.Framework.Jobs.IJob import IJob, JobError
from MDANSE.Mathematics.Signal import correlation


class DipoleAutoCorrelationFunction(IJob):
    """ """

    label = "Dipole AutoCorrelation Function"

    category = (
        "Analysis",
        "Infrared",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {"dependencies": {"trajectory": "trajectory"}, "default": "atom_index 0,1,2"},
    )
    settings["atom_charges"] = (
        "PartialChargesConfigurator",
        {
            "dependencies": {"trajectory": "trajectory"},
            "default": {0: 0.5, 1: 1.2, 2: -0.2},
        },
    )
    settings["output_files"] = (
        "OutputFilesConfigurator",
        {"formats": ["HDFFormat", "ASCIIFormat"]},
    )
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration["frames"]["number"]

        # Will store the time.
        self._outputData.add(
            "time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )

        self._dipoleMoments = np.zeros(
            (self.configuration["frames"]["number"], 3), dtype=np.float64
        )

        self._outputData.add(
            "dacf",
            "LineOutputVariable",
            (self.configuration["frames"]["number"],),
            axis="time",
        )

        if not isinstance(self.configuration["atom_charges"]["charges"], dict):
            raise JobError(
                self,
                "Invalid type for partial charges. Must be a dictionary that maps atom index to to partial charge.",
            )

        self._indexes = [
            idx
            for idxs in self.configuration["atom_selection"]["indexes"]
            for idx in idxs
        ]
        for idx in self._indexes:
            if idx not in self.configuration["atom_charges"]["charges"]:
                raise JobError(self, "Partial charge not defined for atom: %d" % idx)

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
            #. dipoleMomemt (np.array): The calculated dipolar auto-correlation function for atom of index=index
        """

        # get the Frame index
        frameIndex = self.configuration["frames"]["value"][index]

        conf = self.configuration["trajectory"]["instance"].configuration(frameIndex)
        conf = conf.continuous_configuration()

        dipoleMoment = np.zeros((3,), dtype=np.float64)
        for idx in self._indexes:
            temp = (
                self.configuration["atom_charges"]["charges"][idx]
                * conf["coordinates"][idx, :]
            )
            for k in range(len(temp)):
                dipoleMoment[k] = dipoleMoment[k] + temp[k]

        return index, dipoleMoment

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        self._dipoleMoments[index] = x

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        self._outputData["dacf"][:] = correlation(
            self._dipoleMoments, axis=0, average=1
        )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
        )

        self.configuration["trajectory"]["instance"].close()
