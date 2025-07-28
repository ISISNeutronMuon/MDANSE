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

import traceback
from collections.abc import Iterable
from pathlib import Path

import mdtraj as md
from mdtraj.core.trajectory import _TOPOLOGY_EXTS

from MDANSE.Framework.AtomMapping import AtomLabel

from .FileWithAtomDataConfigurator import FileWithAtomDataConfigurator


class MDTrajTopologyFileConfigurator(FileWithAtomDataConfigurator):
    """Uses MDTraj to read the system topology information from a file."""

    def configure(self, value: str | None):
        """
        Parameters
        ----------
        value : str or None
            The path of the MDTraj topology file can be None if
            topology information is contained in the trajectory files.
        """
        if not self.update_needed(value):
            return

        if not self.configurable[self.dependencies["coordinate_files"]].valid:
            self.error_status = "Trajectory file not valid"
            return

        if not value:
            self.error_status = "OK"
            self["filename"] = value

            extension = self.configurable[
                self.dependencies["coordinate_files"]
            ].extension

            supported = list(i[1:] for i in _TOPOLOGY_EXTS)
            if extension not in supported:
                self.error_status = (
                    f"Trajectory file does not contain topology information. "
                    f"File '{extension}' not support should be one of the following: {supported}"
                )
                return

            try:
                self.parse()
            except Exception as e:
                self.error_status = f"File parsing error {e}: {traceback.format_exc()}"
                return

            self.labels = self.unique_labels()
            if len(self.labels) == 0:
                self.error_status = "Unable to generate atom labels"

        else:
            extension = "".join(Path(value).suffixes)[1:]
            supported = list(i[1:] for i in _TOPOLOGY_EXTS)
            if extension not in supported:
                self.error_status = f"File '{extension}' not supported. Should be one of the following: {supported}"
                return
            super().configure(value)

    def parse(self) -> None:
        coord_files = self.configurable[self.dependencies["coordinate_files"]][
            "filenames"
        ]
        if self["filename"]:
            self.atoms = [
                at for at in md.load(coord_files, top=self["filename"]).topology.atoms
            ]

        else:
            self.atoms = [at for at in md.load(coord_files).topology.atoms]

    def atom_labels(self) -> Iterable[AtomLabel]:
        """
        Yields
        ------
        AtomLabel
            An atom label.
        """
        for at in self.atoms:
            yield AtomLabel(
                at.name,
                symbol=at.element.symbol,
                residue=at.residue.name,
                number=at.element.number,
                mass=at.element.mass,
            )
