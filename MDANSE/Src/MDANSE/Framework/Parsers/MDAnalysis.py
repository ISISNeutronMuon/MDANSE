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

from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

import MDAnalysis as mda
from more_itertools import first

from MDANSE.Framework.AtomMapping import AtomLabel
from MDANSE.Framework.Parsers.Parser import Parser
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.UnitCell import UnitCell

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from MDANSE.Framework.Parameters.UtilTypes import Depends


class MDAnalysisTopology(Parser):
    UNIT_CONV = {
        "length": measure(1.0, "ang").toval("nm"),
        "velocity": measure(1.0, "ang/ps").toval("nm/ps"),
        "force": measure(1.0, "kJ/mol ang", equivalent=True).toval("Da nm/ps2"),
    }

    def __init__(self, _desc, filename: Path | str, deps: Depends):
        self.filename = filename
        self.trajectory = self.load(deps)

    def load(self, deps):
        coordinate_files = tuple(
            Path(pth).expanduser() for pth in deps["coordinate_files"]
        )
        if len(coordinate_files) <= 1 or deps["coordinate_format"] is None:
            return mda.Universe(
                self.filename,
                *coordinate_files,
                continuous=deps["continuous"],
                format=deps["coordinate_format"],
                topology_format=deps["topology_format"],
            )

        coordinate_loader = [(i, deps["coordinate_format"]) for i in coordinate_files]
        return mda.Universe(
            self.filename,
            *coordinate_loader,
            continuous=deps["continuous"],
            topology_format=deps["topology_format"],
        )

    @property
    def timestep(self) -> float:
        return self.traj.dt

    @property
    def traj(self):
        return self.trajectory.trajectory

    @property
    def frames(self) -> Iterable[tuple[Sequence[float], UnitCell | None]]:
        # convert from MDAnalysis units to MDANSE units
        # see https://userguide.mdanalysis.org/stable/units.html for
        # default units in MDAnalysis
        for frame in self.traj:
            accum = {"coords": frame.positions * self.UNIT_CONV["length"]}
            if self.traj.ts.triclinic_dimensions is not None:
                accum["unit_cell"] = UnitCell(
                    frame.triclinic_dimensions * self.UNIT_CONV["length"]
                )
            if hasattr(self.traj, "velocities"):
                accum["velocities"] = frame.velocities * self.UNIT_CONV["velocity"]
            if hasattr(self.traj, "forces"):
                accum["gradients"] = frame.forces * self.UNIT_CONV["force"]

            yield accum

    @property
    def element_list(self) -> Iterable[str]:
        for at in self.atoms:
            yield at.element.symbol

    @property
    def atoms(self) -> list[int]:
        return self.trajectory.atoms

    @cached_property
    def atom_props(self) -> tuple[str, ...]:
        return tuple(
            arg
            for arg in ("element", "name", "type", "resname", "mass")
            if hasattr(self.atoms[0], arg)
        )

    @property
    def atom_labels(self) -> Iterable[AtomLabel]:
        """
        Yields
        ------
        AtomLabel
            An atom label.
        """

        if not self.atom_props:
            return

        for at in self.atoms:
            kwargs = {arg: getattr(at, arg) for arg in self.atom_props}

            # the first out of the list above will be the main label
            k = first(kwargs)
            main_label = kwargs.pop(k)
            yield AtomLabel(main_label, **kwargs)
