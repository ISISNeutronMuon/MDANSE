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

from ase.io import iread, read
from ase.io.trajectory import Trajectory as ASETrajectory

from MDANSE.Framework.AtomMapping import AtomLabel

from .FileWithAtomDataConfigurator import FileWithAtomDataConfigurator


class ASEFileConfigurator(FileWithAtomDataConfigurator):
    """Sets an input file for the ASE converter."""

    def parse(self):
        try:
            self._input = ASETrajectory(self["filename"])
        except Exception:
            self._input = iread(self["filename"], index="[:]")
            first_frame = read(self["filename"], index=0)
        else:
            first_frame = self._input[0]

        self["element_list"] = first_frame.get_chemical_symbols()

    def atom_labels(self) -> Iterable[AtomLabel]:
        """
        Yields
        ------
        AtomLabel
            An atom label.
        """
        for atm_label in self["element_list"]:
            yield AtomLabel(atm_label)
