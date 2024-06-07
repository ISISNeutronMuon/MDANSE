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

from MDANSE.MolecularDynamics.Analysis import mean_square_displacement
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Mathematics.Arithmetic import weight
from MDANSE.MolecularDynamics.TrajectoryUtils import sorted_atoms


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

        # Will store the time.
        self._outputData.add(
            "time",
            "LineOutputVariable",
            self.configuration["frames"]["duration"],
            units="ps",
        )

        # Will store the mean square displacement evolution.
        for element in self.configuration["atom_selection"]["unique_names"]:
            self._outputData.add(
                "msd_%s" % element,
                "LineOutputVariable",
                (self.configuration["frames"]["n_frames"],),
                axis="time",
                units="nm2",
                main_result=True,
                partial_result=True,
            )

        self._atoms = sorted_atoms(
            self.configuration["trajectory"]["instance"].chemical_system.atom_list
        )

    def run_step(self, index):
        """
        Runs a single step of the job.

        Args:
            index (int): the index of the step

        Returns:
            tuple: the result of the step
        """

        # get selected atom indexes sublist
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
        element = self.configuration["atom_selection"]["names"][index]

        self._outputData["msd_%s" % element] += result

        IJob.combine(self)

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        # The MSDs per element are averaged.
        nAtomsPerElement = self.configuration["atom_selection"].get_natoms()
        for element, number in list(nAtomsPerElement.items()):
            self._outputData["msd_%s" % element] /= number

        weights = self.configuration["weights"].get_weights()
        msdTotal = weight(weights, self._outputData, nAtomsPerElement, 1, "msd_%s")

        self._outputData.add(
            "msd_total",
            "LineOutputVariable",
            msdTotal,
            axis="time",
            units="nm2",
            main_result=True,
        )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
            self,
        )

        self.configuration["trajectory"]["instance"].close()
