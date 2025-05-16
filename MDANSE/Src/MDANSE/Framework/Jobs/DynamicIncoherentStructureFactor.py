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

from MDANSE.Chemistry.GroupingTool import GroupingTool
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
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["grouping_level"] = (
        "GroupingLevelConfigurator",
        {"choices": ["atom", "average over molecules"]},
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

        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        weights = self.configuration["weights"].get_weights()
        weight_dict = get_weights(weights, nAtomsPerElement, 1)

        self._groupers = {}
        self._groupers["fqt"] = GroupingTool(
            self.configuration["trajectory"]["instance"].chemical_system,
            self._outputData,
        )
        self._groupers["sqf"] = GroupingTool(
            self.configuration["trajectory"]["instance"].chemical_system,
            self._outputData,
        )
        if self.add_ideal_results:
            self._groupers["sqf_ideal"] = GroupingTool(
                self.configuration["trajectory"]["instance"].chemical_system,
                self._outputData,
            )
        dimensions = {
            "fqt": (self._nQShells, self._nFrames),
            "sqf": (self._nQShells, self._nOmegas),
            "sqf_ideal": (self._nQShells, self._nOmegas),
        }
        units = {
            "fqt": "au",
            "sqf": "nm2/ps",
            "sqf_ideal": "nm2/ps",
        }
        axes = {
            "fqt": "q|time",
            "sqf": "q|omega",
            "sqf_ideal": "q|omega",
        }
        name_roots = {
            "fqt": "f(q,t)",
            "sqf": "s(q,f)",
            "sqf_ideal": "s(q,f)_ideal",
        }
        for key, grouper in self._groupers.items():
            grouper.set_selection(
                self.configuration["atom_selection"]["flatten_indices"]
            )
            grouper.set_dataset_parameters(
                {
                    "output_type": "SurfaceOutputVariable",
                    "dimensions": dimensions[key],
                    "axis": axes[key],
                    "units": units[key],
                    "main_result": True,
                    "partial_result": True,
                }
            )
            grouper.set_weight_dictionary(weight_dict)
            grouper.set_grouping(self.configuration["grouping_level"]["value"])
            grouper.create_result_groups(name_roots[key])
            grouper.set_atom_masses(self.configuration["trajectory"]["instance"])

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
        self._groupers["fqt"].assign_result(
            self.configuration["atom_selection"]["flatten_indices"][index],
            np.array([v for v in disf_per_q_shell.values()]),
        )

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...)
        """
        self.configuration["q_vectors"]["generator"].write_vectors_to_file(
            self._outputData
        )
        self._groupers["fqt"].finalise_centre_of_mass()

        for inkey in self._outputData.keys():
            if "f(q,t)" in inkey:
                outkey = "_".join(["s(q,f)"] + inkey.split("_")[1:])
                self._outputData[outkey][:] = get_spectrum(
                    self._outputData[inkey],
                    self.configuration["instrument_resolution"]["time_window"],
                    self.configuration["instrument_resolution"]["time_step"],
                    axis=1,
                )
                if self.add_ideal_results:
                    outkey = "_".join(["s(q,f)_ideal"] + inkey.split("_")[1:])
                    self._outputData[outkey][:] = get_spectrum(
                        self._outputData[inkey],
                        None,
                        self.configuration["instrument_resolution"]["time_step"],
                        axis=1,
                    )

        for group in self._groupers:
            if group != "fqt":
                self._groupers[group].finalise_centre_of_mass()
        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )

        self.configuration["trajectory"]["instance"].close()
        super().finalize()
