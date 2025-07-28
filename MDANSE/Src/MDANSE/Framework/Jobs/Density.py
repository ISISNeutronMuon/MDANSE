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

import numpy as np

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Units import measure

NAVOGADRO = 6.02214129e23


class DensityError(Exception):
    pass


class Density(IJob):
    """Computes the atom and mass densities for a given trajectory.

    These are time dependent if the simulation box volume fluctuates.
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
    settings["output_files"] = ("OutputFilesConfigurator", {})
    settings["running_mode"] = ("RunningModeConfigurator", {})

    def initialize(self):
        super().initialize()

        self.numberOfSteps = self.configuration["frames"]["number"]

        self._n_frames = self.numberOfSteps

        self._n_atoms = self.configuration["trajectory"][
            "instance"
        ].chemical_system.number_of_atoms

        self._symbols = self.configuration["trajectory"][
            "instance"
        ].chemical_system.atom_list

        # Will store the time.
        self._outputData.add(
            "density/axes/time",
            "LineOutputVariable",
            self.configuration["frames"]["time"],
            units="ps",
        )

        self._outputData.add(
            "density/mass/density",
            "LineOutputVariable",
            (self._n_frames,),
            axis="density/axes/time",
            units="g/cm3",
            main_result=True,
        )
        self._outputData.add(
            "density/mass/avg_density",
            "LineOutputVariable",
            (self._n_frames,),
            axis="density/axes/time",
            units="g/cm3",
            main_result=True,
        )

        self._outputData.add(
            "density/atomic/density",
            "LineOutputVariable",
            (self._n_frames,),
            axis="density/axes/time",
            units="1/cm3",
        )
        self._outputData.add(
            "density/atomic/avg_density",
            "LineOutputVariable",
            (self._n_frames,),
            axis="density/axes/time",
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

        conf = self.trajectory.configuration(frame_index)

        try:
            cell_volume = conf.unit_cell.volume * measure(1.0, "nm3").toval("cm3")
        except Exception:
            raise DensityError(
                "Density cannot be computed for chemical system without a defined simulation box. "
                "You can add a box using TrajectoryEditor."
            )
        if abs(cell_volume) < 1e-31:
            raise DensityError(
                f"Non-physical cell volume: {cell_volume}. Density will not be calculated."
                "You can change the unit cell using TrajectoryEditor."
            )

        atomic_density = self._n_atoms / cell_volume

        mass_density = (
            sum(
                [
                    self.trajectory.get_atom_property(s, "atomic_weight")
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

        self._outputData["density/atomic/density"][index] = x[0]

        self._outputData["density/mass/density"][index] = x[1]

    def finalize(self):
        """
        Finalize the job.
        """

        norm = np.arange(1, self._outputData["density/atomic/density"].shape[0] + 1)
        self._outputData["density/atomic/avg_density"][:] = (
            np.cumsum(self._outputData["density/atomic/density"]) / norm
        )
        self._outputData["density/mass/avg_density"][:] = (
            np.cumsum(self._outputData["density/mass/density"]) / norm
        )

        self._outputData.write(
            self.configuration["output_files"]["root"],
            self.configuration["output_files"]["formats"],
            str(self),
            self,
        )

        self.trajectory.close()
        super().finalize()
