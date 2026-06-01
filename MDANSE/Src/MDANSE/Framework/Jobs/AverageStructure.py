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

import numpy as np
from ase.atoms import Atom, Atoms
from ase.io import write as ase_write

from MDANSE import PLATFORM
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Parameters import (
    ASEOutputFormat,
    AtomSelection,
    Boolean,
    FrameSelect,
    MDANSETrajectory,
    RunningMode,
    SingleChoice,
)
from MDANSE.Framework.Units import measure


class AverageStructure(IJob):
    """Outputs a structure file of the atom positions averaged over time.

    This analysis only makes sense for crystalline systems
    where atoms remain within a finite distance around their
    equilibrium positions.

    Please run Mean Square Displacement or Root Mean Square Displacement analysis
    on your trajectory to make sure that the atoms remain around their equilibrium
    positions. Otherwise the time-averaged atom positions will be meaningless.
    If your system consists of a crystalline material with migrating guest atoms,
    you can output just the crystalline part using a corresponding atom selection.
    """

    label = "Average Structure"

    category = ("Trajectory",)
    PREDICTORS = ("frames",)

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    trajectory = MDANSETrajectory(selection="atom_selection")
    frames = FrameSelect(depends={"trajectory": "trajectory"})
    fold = Boolean(
        label="Fold coordinates in to box. Normally it should not be necessary."
    )
    output_units = SingleChoice[str, str](
        label="Distance units of the output",
        choices=("ang", "Bohr", "nm", "pm"),
        aliases={"Angstrom": "ang"},
        default="ang",
    )
    atom_selection = AtomSelection(depends={"trajectory": "trajectory"})
    running_mode = RunningMode()
    output_files = ASEOutputFormat()

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self.numberOfSteps = self.trajectory.get_total_natoms()

        self._atoms = self.trajectory.atom_names

        target_unit = self.output_units

        self._conversion_factor = measure(1.0, "nm").toval(target_unit)

        self._ase_atoms = Atoms()

        try:
            self._unit_cells = [
                self.trajectory.unit_cell(frame)._unit_cell
                for frame in self.frames.samples
            ]
        except Exception:
            raise ValueError(
                "Unit cell needs to be defined for the AverageStructure analysis. "
                "You can add a unit cell using TrajectoryEditor."
            ) from None

    def run_step(self, index):
        """Runs a single step of the job.

        Parameters
        ----------
        index : int
            the index of the step

        Returns
        -------
        tuple
            the result of the step

        """

        # get selected atom indices sublist
        atom_index = self.trajectory.atom_indices[index]
        series = self.trajectory.read_atomic_trajectory(
            atom_index,
            first=self.frames.index_start,
            last=self.frames.index_stop,
            step=self.frames.index_step,
        )

        return index, np.mean(series, axis=0) * self._conversion_factor

    def combine(self, index, x):
        # The symbol of the atom.
        element = self._atoms[self.trajectory.atom_indices[index]]

        try:
            the_atom = Atom(element, x)
        except KeyError:
            the_atom = Atom(str(element).strip("0123456789"), x)

        self._ase_atoms.append(the_atom)

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        # trajectory = self.trajectory

        # frame_range = range(
        #     self.configuration["frames"]["first"],
        #     self.configuration["frames"]["last"] + 1,
        #     self.configuration["frames"]["step"],
        # )

        average_unit_cell = np.mean(self._unit_cells, axis=0) * self._conversion_factor

        self._ase_atoms.set_cell(average_unit_cell)

        if self.fold:
            temp = self._ase_atoms.get_scaled_positions()
            correction = np.floor(temp)
            self._ase_atoms.set_scaled_positions(temp - correction)

        PLATFORM.create_directory(self.output_files.path.parent)
        ase_write(
            self.output_files.path,
            self._ase_atoms,
            self.output_files.out_format,
        )
        super().finalize()
