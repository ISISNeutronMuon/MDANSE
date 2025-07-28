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

from MDANSE.Framework.AtomGrouping.grouping import (
    add_grouped_totals,
)
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum
from MDANSE.MolecularDynamics.Analysis import mean_square_displacement


class MeanSquareDisplacement(IJob):
    r"""Calculates the mean square displacement (MSD) of atoms in the trajectory.

    The MSD is a representation of diffusion in the system. The motion of an individual
    atom or molecule does not follow a simple path since particles undergo collisions.
    The path is to a good approximation to a random walk.

    Mathematically, a random walk is a series of steps where each step is taken in a
    completely random direction from the one before, as analyzed by Albert Einstein
    in a study of Brownian motion. The MSD of a particle in this case
    is proportional to the time elapsed:

    .. math:: \langle d^{2}(t) \rangle = 6Dt + C

    where :math:`\langle d^{2}(t) \rangle` is the MSD and :math:`t` is the time.
    :math:`D` and :math:`C` are constants. The constant :math:`D` is the so-called
    diffusion coefficient.

    More generally the MSD reveals the distance or volume explored by atoms and
    molecules as a function of time. In crystals, the MSD quickly saturates at a
    constant value which corresponds to the vibrational amplitude.
    Diffusion in a volume will also have a limiting value of the MSD which corresponds
    to the diameter of the volume and the saturation value is reached more slowly.
    The MSD can also reveal e.g. sub-diffusion regimes for the translational
    diffusion of lipids in membranes.
    """

    label = "Mean Square Displacement"

    category = (
        "Analysis",
        "Dynamics",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "CorrelationFramesConfigurator",
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

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self.numberOfSteps = len(self.trajectory.atom_indices)

        self.labels = [
            (element, (element,)) for element in self.trajectory.get_natoms()
        ]

        # Will store the time.
        self._outputData.add(
            "msd/axes/time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )

        # Will store the mean square displacement evolution.
        for element in self.trajectory.unique_names:
            self._outputData.add(
                f"msd/{element}",
                "LineOutputVariable",
                (self.configuration["frames"]["n_frames"],),
                axis="msd/axes/time",
                units="nm2",
                main_result=True,
                partial_result=True,
            )

        self._atoms = self.trajectory.atom_names

    def run_step(self, index):
        """
        Runs a single step of the job.

        Args:
            index (int): the index of the step

        Returns:
            tuple: the result of the step
        """

        # get selected atom indices sublist
        atom_index = self.trajectory.atom_indices[index]
        series = self.configuration["trajectory"]["instance"].read_atomic_trajectory(
            atom_index,
            first=self.configuration["frames"]["first"],
            last=self.configuration["frames"]["last"] + 1,
            step=self.configuration["frames"]["step"],
        )

        series = self.configuration["projection"]["projector"](series)

        msd = mean_square_displacement(
            series, self.configuration["frames"]["n_configs"]
        )

        return index, msd

    def combine(self, index, result):
        """
        Combines returned results of run_step.

        Args:
            result (tuple): the output of run_step method
        """

        # The symbol of the atom.
        element = self._atoms[self.trajectory.atom_indices[index]]

        self._outputData[f"msd/{element}"] += result

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        # The MSDs per element are averaged.
        nAtomsPerElement = self.trajectory.get_natoms()
        for element, number in list(nAtomsPerElement.items()):
            self._outputData[f"msd/{element}"] /= number

        selected_weights, all_weights = self.trajectory.get_weights(
            prop=self.configuration["weights"]["property"]
        )
        weight_dict = get_weights(
            selected_weights,
            all_weights,
            nAtomsPerElement,
            self.trajectory.get_all_natoms(),
            1,
        )
        assign_weights(self._outputData, weight_dict, "msd/%s", self.labels)

        n_selected = sum(nAtomsPerElement.values())
        n_total = sum(self.trajectory.get_all_natoms().values())
        fact = n_selected / n_total

        msdTotal = weighted_sum(self._outputData, "msd/%s", self.labels) / fact
        self._outputData.add(
            "msd/total",
            "LineOutputVariable",
            msdTotal,
            axis="msd/axes/time",
            units="nm2",
            main_result=True,
        )
        self._outputData["msd/total"].scaling_factor = fact

        add_grouped_totals(
            self.trajectory,
            self._outputData,
            "msd",
            "LineOutputVariable",
            axis="msd/axes/time",
            units="nm2",
            main_result=True,
            partial_result=True,
        )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
