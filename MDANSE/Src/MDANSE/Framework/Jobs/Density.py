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


from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Framework.Jobs.IJob import IJob, JobError
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.Trajectory import sorted_atoms

NAVOGADRO = 6.02214129e23


class DensityError(Exception):
    pass


class Density(IJob):
    """
    Computes the atom and mass densities for a given trajectory. These are time dependent if the simulation box volume fluctuates.
    """

    label = "Density"

    category = (
        "Analysis",
        "Thermodynamics",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["output_files"] = (
        "OutputFilesConfigurator",
        {"formats": ["MDAFormat", "TextFormat"]},
    )
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        self.numberOfSteps = self.configuration["frames"]["number"]

        self._n_frames = self.numberOfSteps

        self._n_atoms = self.configuration["trajectory"][
            "instance"
        ].chemical_system.number_of_atoms

        self._symbols = sorted_atoms(
            self.configuration["trajectory"]["instance"].chemical_system.atom_list,
            "symbol",
        )

        # Will store the time.
        self._outputData.add(
            "time",
            "LineOutputVariable",
            self.configuration["frames"]["time"],
            units="ps",
        )

        self._outputData.add(
            "mass_density",
            "LineOutputVariable",
            (self._n_frames,),
            axis="time",
            units="g/cm3",
        )

        self._outputData.add(
            "atomic_density",
            "LineOutputVariable",
            (self._n_frames,),
            axis="time",
            units="1/cm3",
        )

    def run_step(self, index):
        """
        Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.
        """

        # get the Frame index
        frame_index = self.configuration["frames"]["value"][index]

        conf = self.configuration["trajectory"]["instance"].configuration(frame_index)
        if not conf.is_periodic:
            raise DensityError(
                "Density cannot be computed for chemical system without periodc boundary conditions"
            )

        cell_volume = conf.unit_cell.volume * measure(1.0, "nm3").toval("cm3")

        atomic_density = self._n_atoms / cell_volume

        mass_density = (
            sum(
                [
                    ATOMS_DATABASE.get_atom_property(s, "atomic_weight")
                    for s in self._symbols
                ]
            )
            / NAVOGADRO
            / cell_volume
        )

        return index, (atomic_density, mass_density)

    def combine(self, index, x):
        """
        @param index: the index of the step.
        @type index: int.

        @param x:
        @type x: any.
        """

        self._outputData["atomic_density"][index] = x[0]

        self._outputData["mass_density"][index] = x[1]

    def finalize(self):
        """
        Finalize the job.
        """

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            self._info,
        )

        self.configuration["trajectory"]["instance"].close()
