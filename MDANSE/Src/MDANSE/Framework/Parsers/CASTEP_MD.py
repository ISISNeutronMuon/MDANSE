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
from more_itertools import first, one, split_at

from MDANSE.Framework.AtomMapping import AtomLabel
from MDANSE.Framework.Units import measure

from .Parser import Parser

HBAR = measure(1.05457182e-34, "kg m2 / s").toval("Da nm2 / ps")
HARTREE = measure(27.2113845, "eV").toval("Da nm2 / ps2")
BOHR = measure(5.29177210903e-11, "m").toval("nm")
AUT = measure(2.4188843265864e-17, "s").toval("ps")


class CASTEPMDFile(Parser):
    @staticmethod
    def float_list_handler(x: str) -> npt.NDArray[float]:
        return np.array(x.split(), dtype=np.float64)

    @staticmethod
    def atom_prop_handler(x: str) -> tuple[tuple[str, int], list[float]]:
        x = x.split()
        return (x[0], int(x[1])), np.array(x[2:], dtype=np.float64)

    KEY_HANDLERS = {
        "h": float_list_handler,
        "hv": float_list_handler,
        "E": float_list_handler,
        "T": float,
        "P": float,
        "S": float_list_handler,
        "R": atom_prop_handler,
        "V": atom_prop_handler,
        "F": atom_prop_handler,
    }

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
        with open(self.filename, encoding="utf-8") as castep_file:
            file = map(str.strip, castep_file)

            # Skip header
            file = dropwhile(lambda line: not line.startswith("END"), file)
            next(file)

            file = split_at(file, lambda line: not line)
            file = filter(None, file)

            yield from map(self.parse_frame, file)

    @staticmethod
    def parse_frame(frame: Iterable[str]) -> dict[str, Any]:
        accum = defaultdict(list)

        for line in frame:
            data, *key = line.split("<--")

            if not key:
                accum["time"] = float(data) * AUT
            else:
                key = one(key).strip()
                if key not in "RVF":
                    accum[key].append(
                        CASTEPMDFile.KEY_HANDLERS[key](data)
                        * CASTEPMDFile.UNIT_CONV[key]
                    )
                else:
                    specind, val = CASTEPMDFile.KEY_HANDLERS[key](data)
                    accum[key].append((specind, val * CASTEPMDFile.UNIT_CONV[key]))

        return accum

    @cached_property
    def element_list(self) -> Collection[str]:
        first_frame = first(self.frames)
        return [spec for (spec, ind), _ in first_frame["R"]]
