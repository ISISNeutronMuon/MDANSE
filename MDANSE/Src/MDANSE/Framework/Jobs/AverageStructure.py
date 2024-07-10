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
from ase.io import write as ase_write
from ase.atoms import Atoms, Atom

from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.TrajectoryUtils import sorted_atoms
from MDANSE.Framework.Jobs.IJob import IJob


class AverageStructure(IJob):
    """<p>Outputs a single structure file containing the atom positions
    averaged over time. Only makes sense for crystalline systems
    where atoms remain within a finite distance around their
    equilibrium positions.</p>
    <p><b> Please run Mean Square Displacement analysis on your
    trajectory to make sure that the atoms remain around their
    equilibrium position</b>. Otherwise the time-averaged
    atom positions will be meaningless. (If your system consists
    of a crystalline material with migrating guest atoms,
    you can output just the crystalline part using atom
    selection.)</p>"""

    label = "Average Structure"

    category = (
        "Analysis",
        "Structure",
    )

    ancestor = ["hdf_trajectory", "molecular_viewer"]

    settings = collections.OrderedDict()
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
            "label": "Fold coordinates in to box. Normally it should not be necessary.",
        },
    )
    settings["output_units"] = (
        "SingleChoiceConfigurator",
        {
            "label": "Distance units of the output",
            "choices": ["Angstrom", "Bohr", "nm", "pm"],
            "default": "Angstrom",
        },
    )
    settings["output_file"] = (
        "OutputStructureConfigurator",
        {"format": "vasp"},
    )

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """
        if self.configuration["output_file"]["write_logs"]:
            log_filename = self.configuration["output_file"]["root"] + ".log"
            self.add_log_file_handler(
                log_filename, self.configuration["output_file"]["log_level"]
            )

        self.numberOfSteps = self.configuration["atom_selection"]["selection_length"]

        self._atoms = sorted_atoms(
            self.configuration["trajectory"]["instance"].chemical_system.atom_list
        )

        target_unit = self.configuration["output_units"]["value"]
        if target_unit == "Angstrom":
            target_unit = "ang"

        self._conversion_factor = measure(1.0, "nm").toval(target_unit)

        self._ase_atoms = Atoms()

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

        return index, np.mean(series, axis=0) * self._conversion_factor

    def combine(self, index, x):
        # The symbol of the atom.
        element = self.configuration["atom_selection"]["names"][index]

        the_atom = Atom(element, x)

        self._ase_atoms.append(the_atom)

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        trajectory = self.configuration["trajectory"]["instance"]

        frame_range = range(
            self.configuration["frames"]["first"],
            self.configuration["frames"]["last"] + 1,
            self.configuration["frames"]["step"],
        )

        unit_cells = [trajectory.unit_cell(frame)._unit_cell for frame in frame_range]

        average_unit_cell = np.mean(unit_cells, axis=0) * self._conversion_factor

        self._ase_atoms.set_cell(average_unit_cell)

        if self.configuration["fold"]["value"]:
            temp = self._ase_atoms.get_scaled_positions()
            correction = np.floor(temp)
            self._ase_atoms.set_scaled_positions(temp - correction)

        ase_write(
            self.configuration["output_file"]["file"],
            self._ase_atoms,
            self.configuration["output_file"]["format"],
        )
        super().finalize()
