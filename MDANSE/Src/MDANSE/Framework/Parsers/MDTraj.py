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

import mdtraj as md

from MDANSE.Framework.AtomMapping import AtomLabel
from MDANSE.MolecularDynamics.UnitCell import UnitCell

from .Parser import Parser

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from MDANSE.Framework.Parameters.UtilTypes import Depends


class MDTrajTopology(Parser):
    def __init__(self, _desc, filename: Sequence[Path | str], deps: Depends):
        self.filename = tuple(Path(pth).expanduser() for pth in filename)
        self.trajectory = self.load(deps)

    def load(self, deps: Depends):
        if deps["topology"] is not None:
            return md.load(
                self.filename,
                top=deps["topology"],
                discard_overlapping_frames=deps["discard"],
            )

        return md.load(self.filename, discard_overlapping_frames=deps["discard"])

    @property
    def timestep(self) -> float:
        return self.trajectory.timestep

    @property
    def frames(self) -> Iterable[tuple[Sequence[float], UnitCell | None]]:
        if self.trajectory.unitcell_vectors is None:
            for index in range(self.trajectory.n_frames):
                yield (self.trajectory.xyz[index], None)
        else:
            for index in range(self.trajectory.n_frames):
                yield (
                    self.trajectory.xyz[index],
                    UnitCell(
                        self.trajectory.unitcell_vectors[index],
                    ),
                )

    @property
    def bonds(self) -> Iterable[tuple[int, int]]:
        yield from self.trajectory.topology.bonds

    @property
    def element_list(self) -> Iterable[str]:
        for at in self.atoms:
            yield at.element.symbol

    @property
    def atoms(self) -> list[int]:
        return self.trajectory.topology.atoms

    @property
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
