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
from __future__ import annotations

import collections
import itertools as it

from scipy.signal import correlate

from MDANSE.Framework.AtomGrouping.grouping import (
    add_grouped_totals,
)
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum
from MDANSE.Mathematics.Signal import differentiate


class VelocityCorrelationFunction(IJob):
    r"""Calculates the velocity correlation function of the selected atoms.

    The Velocity Correlation Function (VCF) is a property describing the dynamics
    of a molecular system. It reveals the underlying nature of the forces acting on
    the system. Its Fourier Transform gives the cartesian density of states for a set
    of atoms.
    """

    label = "Velocity Correlation Function"

    category = (
        "Analysis",
        "Dynamics",
    )
    PREDICTORS = ("frames",)

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "CorrelationFramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["interpolation_order"] = (
        "InterpolationOrderConfigurator",
        {
            "label": "velocities",
            "dependencies": {"trajectory": "trajectory", "frames": "frames"},
        },
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
            }
        },
    )
    settings["weights"] = (
        "WeightsConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
                "atom_transmutation": "atom_transmutation",
            }
        },
    )
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    MAIN_RESULTS = "vcf/isotropic/"

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self.numberOfSteps = len(self.trajectory.atom_indices)

        self.labels = [
            (element, (element,)) for element in self.trajectory.get_natoms()
        ]

        selected_weights, all_weights = self.trajectory.get_weights(
            prop=self.configuration["weights"]["property"]
        )
        if self.configuration["weights"]["property"] in ("b_coherent", "b_incoherent"):
            for weights in selected_weights, all_weights:
                for key, value in weights.items():
                    weights[key] = abs(value) ** 2
        self.weight_dict = get_weights(
            selected_weights,
            all_weights,
            self.trajectory.get_natoms(),
            self.trajectory.get_all_natoms(),
            1,
        )

        self.initialize_outputdata()

    def initialize_outputdata(self):
        self._outputData.add(
            "vcf/axes/time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )

        self._vcf_components = ["isotropic"]
        for i, j in it.combinations_with_replacement(["x", "y", "z"], 2):
            self._vcf_components.append(f"{i}{j}")

        for component in self._vcf_components:
            for result in list(self.trajectory.unique_names) + ["total"]:
                main_result = self.MAIN_RESULTS == f"vcf/{component}/"
                partial_result = main_result and "total" != result
                self._outputData.add(
                    f"vcf/{component}/{result}",
                    "LineOutputVariable",
                    (self.configuration["frames"]["n_frames"],),
                    axis="vcf/axes/time",
                    units="nm2/ps2",
                    main_result=main_result,
                    partial_result=partial_result,
                )

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
            #. atomicDOS (np.array): The calculated density of state for atom of index=index
            #. atomicVCF (np.array): The calculated velocity auto-correlation function for atom of index=index
        """

        trajectory = self.trajectory

        # get atom index
        atom_index = self.trajectory.atom_indices[index]

        if self.configuration["interpolation_order"]["value"] == 0:
            series = trajectory.read_configuration_trajectory(
                atom_index,
                first=self.configuration["frames"]["first"],
                last=self.configuration["frames"]["last"] + 1,
                step=self.configuration["frames"]["step"],
                variable="velocities",
            )
        else:
            series = trajectory.read_atomic_trajectory(
                atom_index,
                first=self.configuration["frames"]["first"],
                last=self.configuration["frames"]["last"] + 1,
                step=self.configuration["frames"]["step"],
            )

            order = self.configuration["interpolation_order"]["value"]
            for axis in range(3):
                series[:, axis] = differentiate(
                    series[:, axis],
                    order=order,
                    dt=self.configuration["frames"]["time_step"],
                )

        series = self.configuration["projection"]["projector"](series)
        v_x = series[:, 0]
        v_y = series[:, 1]
        v_z = series[:, 2]

        n_configs = self.configuration["frames"]["n_configs"]
        components = []
        for v_i, v_j in it.combinations_with_replacement([v_x, v_y, v_z], 2):
            components.append(
                correlate(v_i, v_j[:n_configs], mode="valid").T / n_configs
            )
        return index, components

    def combine(self, index, vcfs):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """
        # The symbol of the atom.
        element = self.trajectory.atom_names[self.trajectory.atom_indices[index]]

        isotropic = (vcfs[0] + vcfs[3] + vcfs[5]) / 3
        self._outputData[f"vcf/isotropic/{element}"] += isotropic

        for i, (j, k) in enumerate(
            it.combinations_with_replacement(["x", "y", "z"], 2)
        ):
            self._outputData[f"vcf/{j}{k}/{element}"] += vcfs[i]

    def weight_and_group(self):
        nAtomsPerElement = self.trajectory.get_natoms()
        fact = sum(nAtomsPerElement.values()) / len(self.trajectory.atom_types)

        for component in self._vcf_components:
            for element, number in nAtomsPerElement.items():
                self._outputData[f"vcf/{component}/{element}"][:] /= number

            assign_weights(
                self._outputData, self.weight_dict, f"vcf/{component}/%s", self.labels
            )

            self._outputData[f"vcf/{component}/total"][:] = (
                weighted_sum(self._outputData, f"vcf/{component}/%s", self.labels)
                / fact
            )
            self._outputData[f"vcf/{component}/total"].scaling_factor = fact

            add_grouped_totals(
                self.trajectory,
                self._outputData,
                f"vcf/{component}",
                "LineOutputVariable",
                axis="vcf/axes/time",
                units="nm2/ps2",
                main_result=self.MAIN_RESULTS == f"vcf/{component}/",
                partial_result=self.MAIN_RESULTS == f"vcf/{component}/",
            )

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """
        self.weight_and_group()

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
