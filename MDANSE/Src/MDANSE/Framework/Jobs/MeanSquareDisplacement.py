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

from MDANSE.Chemistry.GroupingTool import GroupingTool
from MDANSE.MolecularDynamics.Analysis import mean_square_displacement
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum


class MeanSquareDisplacement(IJob):
    """
    Molecules in liquids and gases do not stay in the same place, but move constantly. This
    process is called diffusion and it takes place in
    liquids at equilibrium.

    During this process, the motion of an individual molecule does not follow a simple path
    since molecules undergo collisions. The path is to a good approximation to a random walk.

    Mathematically, a random walk is a series of steps where each step is taken in a completely
    random direction from the one before, as analyzed by Albert Einstein
    in a study of Brownian motion. The MSD of a particle in this case
    is proportional to the time elapsed:

    .. math:: <r^{2}> = 6Dt + C

    where :math:`<r^{2}>` is the MSD and t is the time. D and C are constants. The constant D is
    the so-called diffusion coefficient.

        More generally the MSD reveals the distance or volume explored by atoms and molecules as a function of time.
        In crystals, the MSD quickly saturates at a constant value which corresponds to the vibrational amplitude.
        Diffusion in a volume will also have a limiting value of the MSD  which corresponds to the diameter of the volume
        and the saturation value is reached more slowly.
        The MSD can also reveal e.g. sub-diffusion regimes for the translational diffusion of lipids in membranes.
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
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["grouping_level"] = (
        "GroupingLevelConfigurator",
        {},
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
            "dependencies": {
                "trajectory": "trajectory",
                "atom_selection": "atom_selection",
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

        self._grouper = GroupingTool(
            self.configuration["trajectory"]["instance"].chemical_system,
            self._outputData,
        )
        self._grouper.set_selection(
            self.configuration["atom_selection"]["flatten_indices"]
        )
        self._grouper.set_dataset_parameters(
            {
                "output_type": "LineOutputVariable",
                "dimensions": (self.configuration["frames"]["n_frames"],),
                "axis": "time",
                "units": "nm2",
                "main_result": True,
                "partial_result": True,
            }
        )

        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        weights = self.configuration["weights"].get_weights()
        weight_dict = get_weights(weights, nAtomsPerElement, 1)
        self._grouper.set_weight_dictionary(weight_dict)

        self.numberOfSteps = self.configuration["atom_selection"]["selection_length"]

        # Will store the time.
        self._outputData.add(
            "time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )

        # Will store the mean square displacement evolution.
        self._grouper.set_grouping(self.configuration["grouping_level"]["value"])
        self._grouper.create_result_groups("msd")
        self._grouper.set_atom_masses(self.configuration["trajectory"]["instance"])

    def run_step(self, index):
        """
        Runs a single step of the job.

        Args:
            index (int): the index of the step

        Returns:
            tuple: the result of the step
        """

        series = self.configuration["trajectory"]["instance"].read_atomic_trajectory(
            self.configuration["atom_selection"]["flatten_indices"][index],
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
        self._grouper.assign_result(
            self.configuration["atom_selection"]["flatten_indices"][index], result
        )

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        self._grouper.finalise_centre_of_mass()
        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )

        self.configuration["trajectory"]["instance"].close()
        super().finalize()
