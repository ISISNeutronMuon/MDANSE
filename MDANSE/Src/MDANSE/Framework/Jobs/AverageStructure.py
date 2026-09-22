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

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from MDANSE import PLATFORM
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.TrajectoryUtils import group_atom_indices_precalculated

if TYPE_CHECKING:
    from MDANSE.Framework.Configurators.MemoryConfigurator import MemoryConfigurator

try:
    from ase.atoms import Atom, Atoms
    from ase.io import write as ase_write

    ase_available = True
except ImportError:
    ase_available = False


def avgs_memory_per_atom(
    mem_conf: MemoryConfigurator, n_atoms: int = 1
) -> tuple[int, int, int]:
    """Calculate the memory requirements of a DISF calculation.

    The data size is fixed as 8 bytes per number, since the arrays allocated
    by numpy in this analysis are most likely going to be float64, even
    if the coordinates in the input trajectory are float32.

    Parameters
    ----------
    mem_conf : MemoryConfigurator
        The configurator instance which contains the needed inputs
    n_atoms : int, optional
        Use a specific number of atoms in the calculation, by default 1

    Returns
    -------
    tuple[int, int int]
        MB per atom, per chunk and per n_atoms from input, respectively
    """
    trajectory = mem_conf.configurable[mem_conf.dependencies["trajectory"]]["instance"]
    frame_config = mem_conf.configurable[mem_conf.dependencies["frames"]]
    n_dimensions = 3
    n_frames = frame_config["number"]
    data_size = 8
    chunk_size = trajectory.chunk_size(array_name="position")
    prefactor = 5.5 * n_frames * n_dimensions * data_size / 2**20
    return (prefactor, chunk_size * prefactor, n_atoms * prefactor)


@IJob.register("AverageStructure")
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

    enabled = ase_available
    requires_extras = ("ase",)
    label = "Average Structure"

    category = ("Trajectory",)

    PREDICTORS = (
        "memory",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = {}
    settings["trajectory"] = ("HDFTrajectoryConfigurator", {})
    settings["frames"] = (
        "FramesConfigurator",
        {"dependencies": {"trajectory": "trajectory"}, "default": (0, 1, 1)},
    )
    settings["atom_selection"] = (
        "AtomSelectionConfigurator",
        {"dependencies": {"trajectory": "trajectory"}},
    )
    settings["fold"] = (
        "BooleanConfigurator",
        {
            "default": False,
            "label": "Fold coordinates into box. Normally it should not be necessary.",
        },
    )
    settings["output_units"] = (
        "SingleChoiceConfigurator",
        {
            "label": "Distance unit of the output",
            "choices": ["Angstrom", "Bohr", "nm", "pm"],
            "default": "Angstrom",
        },
    )
    settings["memory"] = (
        "MemoryConfigurator",
        {
            "dependencies": {
                "trajectory": "trajectory",
                "frames": "frames",
            },
            "mem_function": avgs_memory_per_atom,
        },
    )
    settings["output_files"] = (
        "OutputStructureConfigurator",
        {"format": "vasp", "label": "Output structure file name and format"},
    )

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        super().initialize()

        self.grouped_indices = group_atom_indices_precalculated(
            self.trajectory,
            self.configuration["frames"]["number"],
            n_proc=1,
            max_group_size=self.configuration["memory"]["atoms_per_step"][0],
        )
        self.numberOfSteps = len(self.grouped_indices)

        self._atoms = self.trajectory.atom_names

        target_unit = self.configuration["output_units"]["value"]
        if target_unit == "Angstrom":
            target_unit = "ang"

        self._conversion_factor = measure(1.0, "nm").toval(target_unit)

        self._ase_atoms = Atoms()

        frame_range = range(
            self.configuration["frames"]["first"],
            self.configuration["frames"]["last"] + 1,
            self.configuration["frames"]["step"],
        )

        try:
            unit_cells = [
                self.trajectory.unit_cell(frame)._unit_cell for frame in frame_range
            ]
        except Exception:
            raise ValueError(
                "Unit cell needs to be defined for the AverageStructure analysis. "
                "You can add a unit cell using TrajectoryEditor."
            ) from None
        else:
            self._unit_cells = unit_cells

    def run_step(self, index):
        """
        Runs a single step of the job.

        Args:
            index (int): the index of the step

        Returns:
            tuple: the result of the step
        """
        atom_index_group = self.grouped_indices[index]
        # get selected atom indices sublist
        series = self.trajectory.read_atomic_trajectory_many(
            atom_index_group,
            first=self.configuration["frames"]["first"],
            last=self.configuration["frames"]["last"] + 1,
            step=self.configuration["frames"]["step"],
        )

        return index, np.mean(series, axis=0) * self._conversion_factor

    def combine(self, step_index, x):
        # The symbol of the atom.
        atom_index_group = self.grouped_indices[step_index]
        for arr_index, at_index in enumerate(atom_index_group):
            element = self._atoms[at_index]

            try:
                the_atom = Atom(element, x[arr_index])
            except KeyError:
                the_atom = Atom(str(element).strip("0123456789"), x[arr_index])

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

        if self.configuration["fold"]["value"]:
            temp = self._ase_atoms.get_scaled_positions()
            correction = np.floor(temp)
            self._ase_atoms.set_scaled_positions(temp - correction)

        PLATFORM.create_directory(
            Path(self.configuration["output_files"]["file"]).parent
        )
        ase_write(
            self.configuration["output_files"]["file"],
            self._ase_atoms,
            self.configuration["output_files"]["format"],
        )
        super().finalize()
