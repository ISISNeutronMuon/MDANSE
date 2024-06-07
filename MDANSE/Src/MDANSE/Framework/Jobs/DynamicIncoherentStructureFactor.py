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
from scipy.signal import correlate

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.Mathematics.Signal import get_spectrum
from MDANSE.MolecularDynamics.TrajectoryUtils import sorted_atoms


class DynamicIncoherentStructureFactor(IJob):
    """
    Computes the dynamic incoherent structure factor S_inc(Q,w) for a set of atoms.
        It can be compared to experimental data e.g. the quasielastic scattering due to diffusion processes.
    """

    label = "Dynamic Incoherent Structure Factor"

    category = (
        "Analysis",
        "Scattering",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "CorrelationFramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["instrument_resolution"] = (
        "InstrumentResolutionConfigurator",
        {"dependencies": {"trajectory": "trajectory", "frames": "frames"}},
    )
    settings["q_vectors"] = (
        "QVectorsConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
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
    settings["projection"] = (
        "ProjectionConfigurator",
        {"label": "project coordinates"},
    )
    settings["weights"] = (
        "WeightsConfigurator",
        {
            "default": "b_incoherent2",
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
                "atom_transmutation": "atom_transmutation",
            },
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

        self._nFrames = self.configuration["frames"]["n_frames"]

        self._instrResolution = self.configuration["instrument_resolution"]

        self._atoms = sorted_atoms(
            self.configuration["trajectory"]["instance"].chemical_system.atom_list
        )

        self._nOmegas = self._instrResolution["n_omegas"]

        self._outputData.add(
            "q",
            "LineOutputVariable",
            self.configuration["q_vectors"]["shells"],
            units="1/nm",
        )

        self._outputData.add(
            "time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )
        self._outputData.add(
            "time_window",
            "LineOutputVariable",
            self._instrResolution["time_window"],
            units="au",
        )

        self._outputData.add(
            "omega",
            "LineOutputVariable",
            self._instrResolution["omega"],
            units="rad/ps",
        )
        self._outputData.add(
            "omega_window",
            "LineOutputVariable",
            self._instrResolution["omega_window"],
            axis="omega",
            units="au",
        )

        for element in self.configuration["atom_selection"]["unique_names"]:
            self._outputData.add(
                "f(q,t)_%s" % element,
                "SurfaceOutputVariable",
                (self._nQShells, self._nFrames),
                axis="q|time",
                units="au",
            )
            self._outputData.add(
                "s(q,f)_%s" % element,
                "SurfaceOutputVariable",
                (self._nQShells, self._nOmegas),
                axis="q|omega",
                units="nm2/ps",
                main_result=True,
                partial_result=True,
            )

        self._outputData.add(
            "f(q,t)_total",
            "SurfaceOutputVariable",
            (self._nQShells, self._nFrames),
            axis="q|time",
            units="au",
        )
        self._outputData.add(
            "s(q,f)_total",
            "SurfaceOutputVariable",
            (self._nQShells, self._nOmegas),
            axis="q|omega",
            units="nm2/ps",
            main_result=True,
        )

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
            #. atomicSF (np.array): The atomic structure factor
        """

        indexes = self.configuration["atom_selection"]["indexes"][index]

        if len(indexes) == 1:
            series = self.configuration["trajectory"][
                "instance"
            ].read_atomic_trajectory(
                indexes[0],
                first=self.configuration["frames"]["first"],
                last=self.configuration["frames"]["last"] + 1,
                step=self.configuration["frames"]["step"],
            )

        else:
            selected_atoms = [self._atoms[idx] for idx in indexes]
            series = self.configuration["trajectory"]["instance"].read_com_trajectory(
                selected_atoms,
                first=self.configuration["frames"]["first"],
                last=self.configuration["frames"]["last"] + 1,
                step=self.configuration["frames"]["step"],
            )

        series = self.configuration["projection"]["projector"](series)

        disf_per_q_shell = collections.OrderedDict()
        for q in self.configuration["q_vectors"]["shells"]:
            disf_per_q_shell[q] = np.zeros((self._nFrames,), dtype=np.float64)

        n_configs = self.configuration["frames"]["n_configs"]
        for q in self.configuration["q_vectors"]["shells"]:
            qVectors = self.configuration["q_vectors"]["value"][q]["q_vectors"]

            rho = np.exp(1j * np.dot(series, qVectors))
            res = correlate(rho, rho[:n_configs], mode="valid").T[0] / n_configs

            disf_per_q_shell[q] += res.real

        return index, disf_per_q_shell

    def combine(self, index, disf_per_q_shell):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        element = self.configuration["atom_selection"]["names"][index]
        for i, v in enumerate(disf_per_q_shell.values()):
            self._outputData["f(q,t)_{}".format(element)][i, :] += v

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...)
        """

        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        for element, number in list(nAtomsPerElement.items()):
            self._outputData["f(q,t)_%s" % element][:] /= number
            self._outputData["s(q,f)_%s" % element][:] = get_spectrum(
                self._outputData["f(q,t)_%s" % element],
                self.configuration["instrument_resolution"]["time_window"],
                self.configuration["instrument_resolution"]["time_step"],
                axis=1,
            )

        weights = self.configuration["weights"].get_weights()

        self._outputData["f(q,t)_total"][:] = weight(
            weights, self._outputData, nAtomsPerElement, 1, "f(q,t)_%s"
        )

        self._outputData["s(q,f)_total"][:] = weight(
            weights, self._outputData, nAtomsPerElement, 1, "s(q,f)_%s"
        )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )

        self.configuration["trajectory"]["instance"].close()
