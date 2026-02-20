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

import struct
from collections.abc import Collection
from typing import NamedTuple

import numpy as np
from more_itertools import chunked, consume, prepend, take

from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.UnitCell import UnitCell

from .FortranUnformat import binary_file_reader
from .Parser import Parser


class Options(NamedTuple):
    pertype: int
    molxtl: int
    lcanon: int
    defcel: int
    prtthrm: int
    lnose: int
    lnpecan: int
    ltmpdamp: int


class StepInfo(NamedTuple):
    time: float
    index: int
    temperature: float
    average_tempure: float
    timestep: float
    initial_temperature: float
    final_temperature: float
    potential_energy: float


class NoseInfo(NamedTuple):
    snose: float
    snoseh: float
    dsstot: float
    dqcanonNodse: float


class CellPropInfo(NamedTuple):
    pressure: float
    volume: float
    radius_of_gyration: float
    average_pressure: float
    average_volume: float
    average_radius_of_gyration: float


class TrjFile(Parser):
    itype = np.dtype(np.int32).newbyteorder(">")
    ftype = np.dtype(np.float32).newbyteorder(">")
    dtype = np.dtype(np.float64).newbyteorder(">")

    def __init__(self, filename):
        super().__init__(filename)

        self.parse_header()

    def parse_header(self):
        with open(self.filename, "rb") as trjfile:
            parser = binary_file_reader(trjfile)

            rec = next(parser)

            version = int.from_bytes(rec[4:8], "big")

            self._fp = "f" if version < 2010 else "d"
            self._ftype = self.ftype if version < 2010 else self.dtype

            # Diff with doc --> NTRJTI and TRJTIC not in doc

            rec = next(parser)
            self.title = "\n".join(
                bytes(x).decode("utf-8").strip() for x in chunked(rec[4:], 80)
            )
            rec = next(parser)
            self.comment = "\n".join(
                bytes(x).decode("utf-8").strip() for x in chunked(rec[4:], 80)
            )

            rec = next(parser)
            self.options = Options(*struct.unpack("!8i", rec))

            # Skip NFLUSD line [NFLUSD=a=1*int, MVATPF=a*int, NATPFU=a*int, DECUSD=a*8*char]
            next(parser)

            rec = next(parser)
            self.totmov = int.from_bytes(rec[:4], "big")

            self.movable_atoms = np.frombuffer(rec[4:], self.itype) - 1

            # Skip LEEXTI line [LEEXTI=a=1*int, a*char]
            next(parser)
            # Skip LPARTI line [LPARTI=a=1*int, a*char]
            next(parser)
            self._header_size = 8

            # FRAME
            if version <= 2000:
                self.main_rec_size = f"!{self._fp}i33{self._fp}5i"
            elif 2000 < version <= 2010:
                self.main_rec_size = f"!{self._fp}i57{self._fp}6i"
            elif version > 2010:
                self.main_rec_size = f"!{self._fp}i58{self._fp}6i"

            # Step info (1)
            rec = next(parser)

            data = struct.unpack(self.main_rec_size, rec)
            # time, ind, temp, avtemp, timestep, inittemp, finaltemp, pe = data[:8]
            # Cell prop info (2)
            # data = np.frombuffer(rec, dtype=self._ftype)
            # press, vol, rog, av_press, av_vol, av_rog = (data[i] for i in (0, 1, 5, 6, 7, 11))
            # Nosé data (3)
            # snose, snoseh, dsstot, dqcanonNose = np.frombuffer(rec, dtype=self._ftype)
            # Cell info (4)
            # data = np.frombuffer(rec, dtype=self._ftype)
            # xx, yy, zz, xy, xz, yz = data[2:8]
            # N atoms (5)
            # self.n_atoms = int.from_bytes(rec[:4], "big")
            # Tasty pecans? (6)
            # Temperature damping (7)

            if version < 2010:
                self.velocities_written = data[-3]
                self.gradients_written = False
            else:
                self.velocities_written = data[-4]
                self.gradients_written = data[-3]

            frame_data = [
                "step_info",
                "cell_prop_info",
            ]
            if self.options.lcanon:
                frame_data.append("nose")
            if self.options.pertype:
                frame_data.extend(("cell", "natoms"))
            if self.options.lnpecan:
                frame_data.append("pecan")
            if self.options.ltmpdamp:
                frame_data.append("temp_damp")

            frame_data.extend(("pos_x", "pos_y", "pos_z"))

            if self.velocities_written:
                frame_data.extend(("vel_x", "vel_y", "vel_z"))
            if self.gradients_written:
                frame_data.extend(("force_x", "force_y", "force_z"))

            self.frame_data = tuple(frame_data)
            self.framesize = len(self.frame_data)
            parser.send(-1)

    def _process_step_info(self, rec: bytes) -> StepInfo:
        data = struct.unpack(self.main_rec_size, rec)
        return StepInfo(*data[:8])

    def _process_cell_prop_info(self, rec: bytes) -> CellPropInfo:
        data = np.frombuffer(rec, dtype=self._ftype)
        return CellPropInfo(*(data[[0, 1, 5, 6, 7, 11]]))

    def _process_nose_info(self, rec: bytes):
        return NoseInfo(*np.frombuffer(rec, dtype=self._ftype))

    def _process_cell_info(self, rec: bytes):
        data = np.frombuffer(rec, dtype=self._ftype)
        xx, yy, zz, yz, xz, xy = data[2:8]
        cell = np.array([[xx, xy, xz], [0.0, yy, yz], [0.0, 0.0, zz]])
        return UnitCell(cell)

    processors = {
        "step_info": _process_step_info,
        "cell_prop_info": _process_cell_prop_info,
        "nose": _process_nose_info,
        "cell": _process_cell_info,
    }

    UNIT_CONV = {
        "pos": measure(1.0, "ang").toval("nm"),
        "vel": measure(1.0, "ang/fs").toval("nm/ps"),
        "force": measure(1.0, "kcal_per_mole/ang", equivalent=True).toval(
            "Da nm/ps2 mol"
        ),
    }

    def read_frame(self, parser: binary_file_reader):
        accum = {}
        iter = zip(self.frame_data, parser, strict=False)
        for typ, rec in iter:
            if typ.startswith(("pos", "vel", "force")):
                key = typ.split("_")[0]
                data = np.vstack(
                    [
                        np.frombuffer(rec, dtype=self._ftype)
                        for _, rec in prepend(("", rec), take(2, iter))
                    ]
                ).T
                accum[key] = data * self.UNIT_CONV[key]
            elif typ in self.processors:
                accum[typ] = self.processors[typ](self, rec)

        return accum

    @property
    def frames(self):
        with open(self.filename, "rb") as trjfile:
            parser = binary_file_reader(trjfile)
            consume(parser, self._header_size)
            while frame := self.read_frame(parser):
                yield frame

    @property
    def element_list(self) -> Collection[str]:
        return ("du",)
