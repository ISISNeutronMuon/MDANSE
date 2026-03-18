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

from collections.abc import Collection, Iterable, Iterator
from itertools import count, islice
from pathlib import Path
from typing import NamedTuple

import numpy as np
import numpy.typing as npt
from more_itertools import run_length

from MDANSE.Framework.AtomMapping import AtomLabel
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.UnitCell import UnitCell

from .Parser import Parser


class HeaderInfo(NamedTuple):
    unit_cell: UnitCell
    atoms: list[str]
    atom_counts: npt.NDArray[int]
    system_name: str


class XDATCARFileError(Exception):
    pass


class XDATCARFile(Parser):
    """Inputs an XDATCAR file (for the VASP converter)."""

    def __init__(self, filename: Path | str):
        self.filename = filename
        self.fixed_cell, self.frame_numbers = self.check_trajectory(filename)

        with open(self.filename, encoding="utf-8") as file:
            header = self.read_header(file)

            self._init_cell = header.unit_cell
            self.atoms = header.atoms
            self.atom_counts = header.atom_counts
            self.n_atoms = sum(self.atom_counts)

    n_atoms = None

    @staticmethod
    def check_trajectory(filename: str) -> tuple[bool, bool]:
        with open(filename, encoding="utf-8") as source:
            header = XDATCARFile.read_header(source)

            total_atom_number = np.sum(header.atom_counts)
            fixed_cell = True
            frame_numbers = True

            names_found = 0
            direct_configuration_found = False

            for line in islice(source, 2 * total_atom_number + 10):
                if header.system_name in line:
                    names_found += 1
                if "irect configuration=" in line:
                    direct_configuration_found = True
                if not line.strip():
                    frame_numbers = False

        if names_found > 1:
            fixed_cell = False
        if direct_configuration_found and not frame_numbers:
            raise ValueError(
                "File contains both 'direct configuration' and empty lines"
            )

        return fixed_cell, frame_numbers

    UNIT_CONV = {
        "length": measure(1.0, "ang").toval("nm"),
        "time": measure(1.0, "fs").toval("ps"),
    }

    @staticmethod
    def read_header(source: Iterator[str]) -> HeaderInfo:
        test = next(source, None)
        if test is None:
            return None
        system_name = test.strip()
        scale_factor = float(next(source))
        cell = (
            np.array(list(map(str.split, islice(source, 3))), dtype=float)
            * scale_factor
            * XDATCARFile.UNIT_CONV["length"]
        )
        unit_cell = UnitCell(cell)
        atoms = next(source).split()
        atom_numbers = np.array(next(source).split(), dtype=int)
        return HeaderInfo(unit_cell, atoms, atom_numbers, system_name)

    @property
    def frames(self):
        with open(self.filename, encoding="utf-8") as file:
            self.read_header(file)

            for i in count():
                frame = self.read_frame(file)
                if frame is None:
                    break
                frame.setdefault("step", i)
                yield frame

    def read_frame(self, file):
        accum = {
            "unit_cell": (
                XDATCARFile.read_header(file).unit_cell
                if not self.fixed_cell
                else self._init_cell
            ),
        }

        val = next(file, None)
        if val is None:
            return None
        if self.frame_numbers:
            step = int(val.rsplit("configuration=", maxsplit=1)[-1])
            accum["step"] = step

        accum["coords"] = np.array(
            [line.split() for line in islice(file, self.n_atoms)], dtype=float
        )

        return accum

    @property
    def element_list(self) -> Collection[str]:
        """Return a list of elements in the structure.

        Returns
        -------
        Collection[str]
            Elements in
        """
        return list(run_length.decode(zip(self.atoms, self.atom_counts, strict=True)))
