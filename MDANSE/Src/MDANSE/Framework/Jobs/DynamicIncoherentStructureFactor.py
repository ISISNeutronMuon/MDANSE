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
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum
from MDANSE.Mathematics.Signal import get_spectrum


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
    settings["projection"] = (
        "ProjectionConfigurator",
        {"label": "project coordinates"},
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
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["atom_transmutation"] = (
        "AtomTransmutationConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
                "grouping_level": "grouping_level",
            }
        },
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
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self.numberOfSteps = self.configuration["atom_selection"]["selection_length"]

        self._nQShells = self.configuration["q_vectors"]["n_shells"]

        self._nFrames = self.configuration["frames"]["n_frames"]

        self._instrResolution = self.configuration["instrument_resolution"]

        self._atoms = self.configuration["trajectory"][
            "instance"
        ].chemical_system.atom_list

        self._nOmegas = self._instrResolution["n_omegas"]

        self.add_ideal_results = (
            self.configuration["instrument_resolution"]["kernel"] != "ideal"
        )

        self.labels = [
            (element, (element,))
            for element in self.configuration["atom_selection"].get_natoms()
        ]

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
                f"f(q,t)_{element}",
                "SurfaceOutputVariable",
                (self._nQShells, self._nFrames),
                axis="q|time",
                units="au",
            )
            self._outputData.add(
                f"s(q,f)_{element}",
                "SurfaceOutputVariable",
                (self._nQShells, self._nOmegas),
                axis="q|omega",
                units="au",
                main_result=True,
                partial_result=True,
            )
            if self.add_ideal_results:
                self._outputData.add(
                    f"s(q,f)_ideal_{element}",
                    "SurfaceOutputVariable",
                    (self._nQShells, self._nOmegas),
                    axis="q|omega",
                    units="au",
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
            units="au",
            main_result=True,
        )
        if self.add_ideal_results:
            self._outputData.add(
                "s(q,f)_ideal_total",
                "SurfaceOutputVariable",
                (self._nQShells, self._nOmegas),
                axis="q|omega",
                units="au",
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

        indices = self.configuration["atom_selection"]["indices"][index]

        if len(indices) == 1:
            series = self.configuration["trajectory"][
                "instance"
            ].read_atomic_trajectory(
                indices[0],
                first=self.configuration["frames"]["first"],
                last=self.configuration["frames"]["last"] + 1,
                step=self.configuration["frames"]["step"],
            )

        else:
            series = self.configuration["trajectory"]["instance"].read_com_trajectory(
                indices,
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
            res = correlate(rho, rho[:n_configs], mode="valid").T[0] / (
                n_configs * rho.shape[1]
            )

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
            self._outputData[f"f(q,t)_{element}"][i, :] += v

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...)
        """
        self.configuration["q_vectors"]["generator"].write_vectors_to_file(
            self._outputData
        )

        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        weights = self.configuration["weights"].get_weights()
        weight_dict = get_weights(weights, nAtomsPerElement, 1)
        assign_weights(self._outputData, weight_dict, "f(q,t)_%s", self.labels)
        assign_weights(self._outputData, weight_dict, "s(q,f)_%s", self.labels)
        if self.add_ideal_results:
            assign_weights(
                self._outputData, weight_dict, "s(q,f)_ideal_%s", self.labels
            )
        for element, number in list(nAtomsPerElement.items()):
            extra_scaling = 1.0 / number
            self._outputData[f"f(q,t)_{element}"] *= extra_scaling
            self._outputData[f"s(q,f)_{element}"][:] = get_spectrum(
                self._outputData[f"f(q,t)_{element}"],
                self.configuration["instrument_resolution"]["time_window"],
                self.configuration["instrument_resolution"]["time_step"],
                axis=1,
            )
            if self.add_ideal_results:
                self._outputData[f"s(q,f)_ideal_{element}"][:] = get_spectrum(
                    self._outputData[f"f(q,t)_{element}"],
                    None,
                    self.configuration["instrument_resolution"]["time_step"],
                    axis=1,
                )

        self._outputData["f(q,t)_total"][:] = weighted_sum(
            self._outputData, "f(q,t)_%s", self.labels
        )

        self._outputData["s(q,f)_total"][:] = weighted_sum(
            self._outputData, "s(q,f)_%s", self.labels
        )
        self.configuration["grouping_level"].add_grouped_totals(
            self._outputData,
            "f(q,t)",
            "SurfaceOutputVariable",
            axis="q|time",
            units="au",
        )
        self.configuration["grouping_level"].add_grouped_totals(
            self._outputData,
            "s(q,f)",
            "SurfaceOutputVariable",
            axis="q|omega",
            units="au",
            main_result=True,
            partial_result=True,
        )

        if self.add_ideal_results:
            self._outputData["s(q,f)_ideal_total"][:] = weighted_sum(
                self._outputData, "s(q,f)_ideal_%s", self.labels
            )
            self.configuration["grouping_level"].add_grouped_totals(
                self._outputData,
                "s(q,f)_ideal",
                "SurfaceOutputVariable",
                axis="q|omega",
                units="au",
            )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.configuration["trajectory"]["instance"].close()
        super().finalize()
