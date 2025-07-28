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

from collections.abc import Iterable

import numpy as np

from MDANSE.Core.Error import Error
from MDANSE.Framework.AtomMapping import AtomLabel
from MDANSE.Framework.Units import measure

from .FileWithAtomDataConfigurator import FileWithAtomDataConfigurator


class XDATCARFileError(Error):
    pass


def read_modern_header(source):
    cell = []
    system_name = source.readline().strip()
    scale_factor = float(source.readline())
    for _ in range(3):
        cell.append([float(x) for x in source.readline().split()])
    atoms = source.readline().split()
    atom_numbers = [int(x) for x in source.readline().split()]
    unit_cell = np.array(cell) * scale_factor
    return unit_cell, atoms, atom_numbers, system_name


def check_trajectory(filename: str):
    with open(filename, encoding="utf-8") as source:
        _, _, atom_numbers, system_name = read_modern_header(source)

        total_atom_number = np.sum(atom_numbers)
        fixed_cell = True
        frame_numbers = True

        source.seek(0)

        lines_read = 0
        names_found = 0
        empty_found = 0
        direct_configuration_found = 0

        for line in source:
            lines_read += 1
            if lines_read > 2 * total_atom_number + 10:
                break
            if system_name in line:
                names_found += 1
            if "irect configuration=" in line:
                direct_configuration_found += 1
            if len(line.split()) == 0:
                empty_found += 1

    if names_found > 1:
        fixed_cell = False
    if empty_found > 0:
        frame_numbers = False
    if direct_configuration_found > 0:
        if not frame_numbers:
            raise ValueError(
                "File contains both 'direct configuration' and empty lines"
            )
        frame_numbers = True
    return fixed_cell, frame_numbers


class XDATCARFileConfigurator(FileWithAtomDataConfigurator):
    """Inputs an XDATCAR file (for the VASP converter)."""

    def parse(self):
        filename = self["filename"]
        self["instance"] = open(filename, encoding="utf-8")

        lines_read = sum(1 for _ in self["instance"])

        self["instance"].seek(0)

        self._has_fixed_cell, self._has_frame_numbers = check_trajectory(filename)

        self._conversion_factor = measure(1.0, "ang").toval("nm")

        unit_cell, atoms, atom_numbers, _ = read_modern_header(self["instance"])
        self._init_cell = unit_cell

        self["cell_shape"] = unit_cell * self._conversion_factor

        self["atoms"] = atoms
        self["atom_numbers"] = atom_numbers

        self["n_atoms"] = sum(atom_numbers)

        if self._has_fixed_cell:
            n_frames = round((lines_read - 7) / (self["n_atoms"] + 1))
        else:
            n_frames = round(lines_read / (self["n_atoms"] + 1 + 7))
        self["n_frames"] = int(n_frames)

        self._coordinates = np.empty((self["n_atoms"], 3))

    def read_step(self, step):
        if step > 0 and not self._has_fixed_cell:
            unit_cell, atoms, atom_numbers, system_name = read_modern_header(
                self["instance"]
            )
        else:
            unit_cell = self._init_cell

        self["cell_shape"] = unit_cell * self._conversion_factor

        if self._has_frame_numbers:
            step_string = self["instance"].readline().split("configuration=")[-1]
            step_number = int(step_string)
        else:
            self["instance"].readline()
            step_number = step
        self["step_number"] = step_number

        for atom_number in range(self["n_atoms"]):
            self._coordinates[atom_number] = [
                float(x) for x in self["instance"].readline().split()
            ]

        return self._coordinates

    def close(self):
        self["instance"].close()

    def atom_labels(self) -> Iterable[AtomLabel]:
        """
        Yields
        ------
        AtomLabel
            An atom label.
        """
        for symbol in self["atoms"]:
            yield AtomLabel(symbol)
