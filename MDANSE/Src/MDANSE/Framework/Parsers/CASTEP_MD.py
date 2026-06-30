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

from collections import defaultdict
from collections.abc import Collection, Iterable, Iterator
from functools import cached_property
from itertools import dropwhile
from typing import Any

import numpy as np
import numpy.typing as npt
from ase.io.trajectory import Trajectory as ASETrajectory
from castep_outputs.tools.md_geom_parser import MDGeomParser, MDGeomTimestepInfo
from more_itertools import first, one, split_at

from MDANSE.Framework.AtomMapping import AtomLabel
from MDANSE.Framework.Units import measure

from .Parser import Parser

HBAR = measure(1.05457182e-34, "kg m2 / s").toval("Da nm2 / ps")
HARTREE = measure(27.2113845, "eV").toval("Da nm2 / ps2")
BOHR = measure(5.29177210903e-11, "m").toval("nm")
AUT = measure(2.4188843265864e-17, "s").toval("ps")


class CASTEPMDFile(Parser):
    UNIT_CONV = defaultdict(
        lambda: 1.0,
        h=BOHR,
        hv=BOHR / AUT,
        E=HARTREE,
        F=HARTREE / BOHR,
        S=HARTREE / BOHR**3,
        P=HARTREE / BOHR**3,
        V=BOHR / AUT,
        R=BOHR,
    )

    @property
    def frames(self) -> Iterator:
        parser = MDGeomParser(self.filename)

        yield from map(self.parse_frame, parser)

    def parse_frame(self, frame: MDGeomTimestepInfo) -> dict[str, Any]:
        accum = defaultdict(list)

        accum["time"] = frame["time"] * AUT
        accum["h"] = np.array(frame["lattice_vectors"]) * self.UNIT_CONV["h"]
        for prop in "RVF":
            accum[prop] = (
                np.array([ion[prop] for ion in frame["ions"].values()])
                * self.UNIT_CONV[prop]
            )

        return accum

    @cached_property
    def n_frames(self) -> int:
        return len(MDGeomParser(self.filename))

    @cached_property
    def element_list(self) -> Collection[str]:
        first_frame = MDGeomParser(self.filename)[0]
        return [spec for spec, _ind in first_frame["ions"]]
