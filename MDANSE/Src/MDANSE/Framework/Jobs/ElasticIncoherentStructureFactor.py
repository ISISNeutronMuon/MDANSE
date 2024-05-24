#    This file is part of MDANSE.
#
#    MDANSE is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import collections

import numpy as np

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.MolecularDynamics.TrajectoryUtils import sorted_atoms


class ElasticIncoherentStructureFactor(IJob):
    """
    The Elastic Incoherent Structure Factor (EISF ) is defined as the limit of the incoherent
    intermediate scattering function for infinite time.

    The EISF appears as the incoherent amplitude of the elastic line in the neutron scattering spectrum.
    Elastic scattering is only present for systems in which the atomic motion is confined in space, as
    in solids. The Q-dependence of the EISF indicates e.g. the fraction of static/mobile atoms and the spatial dependence of the dynamics.
    """

    label = "Elastic Incoherent Structure Factor"

    # The category of the analysis.
    category = (
        "Analysis",
        "Scattering",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["q_vectors"] = (
        "QVectorsConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["projection"] = (
        "ProjectionConfigurator",
        {"label": "project coordinates"},
    )
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
        {
            "default": "b_incoherent",
            "dependencies": {"atom_selection": "atom_selection"},
        },
    )
    settings["output_files"] = (
        "OutputFilesConfigurator",
        {"formats": ["MDAFormat", "TextFormat"]},
    )
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.numberOfSteps = self.configuration["atom_selection"]["selection_length"]

        self._nQShells = self.configuration["q_vectors"]["n_shells"]

        self._nFrames = self.configuration["frames"]["number"]

        self._outputData.add(
            "q",
            "LineOutputVariable",
            self.configuration["q_vectors"]["shells"],
            units="1/nm",
        )

        for element in self.configuration["atom_selection"]["unique_names"]:
            self._outputData.add(
                "eisf_%s" % element,
                "LineOutputVariable",
                (self._nQShells,),
                axis="q",
                units="au",
                main_result=True,
                partial_result=True,
            )

        self._outputData.add(
            "eisf_total",
            "LineOutputVariable",
            (self._nQShells,),
            axis="q",
            units="au",
            main_result=True,
        )

        self._atoms = sorted_atoms(
            self.configuration["trajectory"]["instance"].chemical_system.atom_list
        )

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
            #. atomicEISF (np.array): The atomic elastic incoherent structure factor
        """

        # get atom index
        indexes = self.configuration["atom_selection"]["indexes"][index]
        atoms = [self._atoms[idx] for idx in indexes]

        series = self.configuration["trajectory"]["instance"].read_com_trajectory(
            atoms,
            first=self.configuration["frames"]["first"],
            last=self.configuration["frames"]["last"] + 1,
            step=self.configuration["frames"]["step"],
        )

        series = self.configuration["projection"]["projector"](series)

        atomicEISF = np.zeros((self._nQShells,), dtype=np.float64)

        for i, q in enumerate(self.configuration["q_vectors"]["shells"]):
            if not q in self.configuration["q_vectors"]["value"]:
                continue

            qVectors = self.configuration["q_vectors"]["value"][q]["q_vectors"]

            a = np.average(np.exp(1j * np.dot(series, qVectors)), axis=0)
            a = np.abs(a) ** 2

            atomicEISF[i] = np.average(a)

        return index, atomicEISF

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        # The symbol of the atom.
        element = self.configuration["atom_selection"]["names"][index]

        self._outputData["eisf_%s" % element] += x

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...)
        """

        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        for element, number in list(nAtomsPerElement.items()):
            self._outputData["eisf_%s" % element][:] /= number

        weights = self.configuration["weights"].get_weights()
        self._outputData["eisf_total"][:] = weight(
            weights, self._outputData, nAtomsPerElement, 1, "eisf_%s"
        )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )

        self.configuration["trajectory"]["instance"].close()
