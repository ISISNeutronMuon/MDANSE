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

import collections
import struct

import numpy as np

from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter

FORCE_FACTOR = measure(1.0, "kcal_per_mole/ang", equivalent=True).toval("Da nm/ps2 mol")


class TrjFile(dict):
    def __init__(self, trjfilename):
        self["instance"] = open(trjfilename, "rb")

        self.parse_header()

    def parse_header(self):
        trjfile = self["instance"]

        rec = "!4x"
        recSize = struct.calcsize(rec)
        trjfile.read(recSize)

        # Record 1
        rec = "!4s20i8x"
        recSize = struct.calcsize(rec)
        DATA = struct.unpack(rec, trjfile.read(recSize))
        VERSION = DATA[1]
        if VERSION < 2010:
            self._fp = "f"
        else:
            self._fp = "d"

        # Diff with doc --> NTRJTI and TRJTIC not in doc
        rec = "!i"
        recSize = struct.calcsize(rec)
        (NTRJTI,) = struct.unpack(rec, trjfile.read(recSize))
        rec = f"!{80 * NTRJTI}s8x"
        recSize = struct.calcsize(rec)
        self["title"] = struct.unpack(rec, trjfile.read(recSize))
        self["title"] = "\n".join([t.decode("utf-8") for t in self["title"]])

        # Record 2
        rec = "!i"
        recSize = struct.calcsize(rec)
        NEEXTI = struct.unpack(rec, trjfile.read(recSize))[0]
        rec = f"!{80 * NEEXTI}s8x"
        recSize = struct.calcsize(rec)
        trjfile.read(recSize)

        # Record 3
        rec = "!8i8x"
        recSize = struct.calcsize(rec)
        PERTYPE, _, LCANON, DEFCEL, _, _, LNPECAN, LTMPDAMP = struct.unpack(
            rec, trjfile.read(recSize)
        )
        self["pertype"] = PERTYPE
        self["defcel"] = DEFCEL

        # Record 4
        rec = "!i"
        recSize = struct.calcsize(rec)
        NFLUSD = struct.unpack(rec, trjfile.read(recSize))[0]

        rec = f"!{NFLUSD}i{NFLUSD}i{8 * NFLUSD}s8x"
        recSize = struct.calcsize(rec)
        trjfile.read(recSize)

        rec = "!i"
        recSize = struct.calcsize(rec)
        self["totmov"] = struct.unpack(rec, trjfile.read(recSize))[0]

        rec = f"!{self['totmov']}i8x"
        recSize = struct.calcsize(rec)
        self["mvofst"] = (
            np.array(struct.unpack(rec, trjfile.read(recSize)), dtype=np.int32) - 1
        )

        # Record 4a
        rec = "!i"
        recSize = struct.calcsize(rec)
        (LEEXTI,) = struct.unpack(rec, trjfile.read(recSize))
        rec = f"!{LEEXTI}s8x"
        recSize = struct.calcsize(rec)
        trjfile.read(recSize)

        # Record 4b
        rec = "!i"
        recSize = struct.calcsize(rec)
        (LPARTI,) = struct.unpack(rec, trjfile.read(recSize))
        rec = f"!{LPARTI}s8x"
        recSize = struct.calcsize(rec)
        trjfile.read(recSize)

        self._headerSize = trjfile.tell()

        # Frame record 1
        if VERSION == 2000:
            rec1 = f"!{self._fp}i33{self.fp}5i8x"
        elif VERSION == 2010:
            rec1 = f"!{self._fp}i57{self._fp}6i8x"
        else:
            rec1 = f"!{self._fp}i58{self._fp}6i8x"

        recSize = struct.calcsize(rec1)
        DATA = struct.unpack(rec1, trjfile.read(recSize))

        if VERSION < 2010:
            self["velocities_written"] = DATA[-3]
            self["gradients_written"] = 0
        else:
            self["velocities_written"] = DATA[-4]
            self["gradients_written"] = DATA[-3]

        # Frame record 2
        rec = f"!12{self._fp}8x"
        recSize = struct.calcsize(rec)
        trjfile.read(recSize)

        # Frame record 3
        if LCANON:
            rec = f"!4{self._fp}8x"
            recSize = struct.calcsize(rec)
            trjfile.read(recSize)

        if PERTYPE > 0:
            # Frame record 4
            self._defCellRecPos = trjfile.tell() - self._headerSize
            self._defCellRec = f"!22{self._fp}8x"
            self._defCellRecSize = struct.calcsize(self._defCellRec)
            trjfile.read(self._defCellRecSize)

        if PERTYPE > 0:
            # Frame record 5
            rec = f"!i14{self._fp}8x"
            recSize = struct.calcsize(rec)
            trjfile.read(recSize)

        if LNPECAN:
            # Frame record 6
            rec = f"!3{self._fp}8x"
            recSize = struct.calcsize(rec)
            trjfile.read(recSize)

        if LTMPDAMP:
            # Frame record 7
            rec = f"!{self._fp}8x"
            recSize = struct.calcsize(rec)
            trjfile.read(recSize)

        self._configRecPos = trjfile.tell() - self._headerSize

        rec_count = 3

        if self["velocities_written"]:
            rec_count += 3
        if self["gradients_written"]:
            rec_count += 3

        self._configRec = "!" + (f"{self['totmov']}{self._fp}8x" * rec_count)

        self._configRecSize = struct.calcsize(self._configRec)
        trjfile.read(self._configRecSize)

        self._frameSize = trjfile.tell() - self._headerSize

        trjfile.seek(0, 2)

        self["n_frames"] = (trjfile.tell() - self._headerSize) // self._frameSize

    def read_step(self, index):
        """ """

        trjfile = self["instance"]

        pos = self._headerSize + index * self._frameSize

        trjfile.seek(pos, 0)

        rec = f"!{self._fp}"
        recSize = struct.calcsize(rec)
        (timeStep,) = struct.unpack(rec, trjfile.read(recSize))

        if self["defcel"]:
            trjfile.seek(pos + self._defCellRecPos, 0)
            cell = np.zeros((3, 3), dtype=np.float64)
            # ax,by,cz,bz,az,ay
            cellData = np.array(
                struct.unpack(self._defCellRec, trjfile.read(self._defCellRecSize)),
                dtype=np.float64,
            )[2:8] * measure(1.0, "ang").toval("nm")
            cell[0, 0] = cellData[0]
            cell[1, 1] = cellData[1]
            cell[2, 2] = cellData[2]
            cell[1, 2] = cellData[3]
            cell[0, 2] = cellData[4]
            cell[0, 1] = cellData[5]

        else:
            cell = None

        trjfile.seek(pos + self._configRecPos, 0)

        config = struct.unpack(self._configRec, trjfile.read(self._configRecSize))

        rows = 1 + self["velocities_written"] + self["gradients_written"]

        config = np.transpose(np.reshape(config, (rows, 3, self["totmov"])))
        xyz = config[:, :, 0] * measure(1.0, "ang").toval("nm")

        if self["velocities_written"]:
            vel = config[:, :, 1] * measure(1.0, "ang/fs").toval("nm/ps")
        else:
            vel = None

        if self["gradients_written"]:
            gradients = config[:, :, 2] * FORCE_FACTOR
        else:
            gradients = None

        return timeStep, cell, xyz, vel, gradients

    def close(self):
        self["instance"].close()


class Forcite(Converter):
    """Converts a Forcite trajectory to an MDT trajectory."""

    label = "Forcite"

    settings = collections.OrderedDict()
    settings["xtd_file"] = (
        "XTDFileConfigurator",
        {
            "wildcard": "XTD files (*.xtd);;All files (*)",
            "default": "INPUT_FILENAME.xtd",
            "label": "Input XTD file",
        },
    )
    settings["trj_file"] = (
        "InputFileConfigurator",
        {
            "wildcard": "TRJ files (*.trj);;All files (*)",
            "default": "INPUT_FILENAME.trj",
            "label": "Input TRJ file",
        },
    )
    settings["atom_aliases"] = (
        "AtomMappingConfigurator",
        {
            "default": "{}",
            "label": "Atom mapping",
            "dependencies": {"input_file": "xtd_file"},
        },
    )
    settings["fold"] = (
        "BooleanConfigurator",
        {"default": False, "label": "Fold coordinates into box"},
    )
    settings["output_files"] = (
        "OutputTrajectoryConfigurator",
        {
            "formats": ["MDTFormat"],
            "root": "xtd_file",
            "label": "MDANSE trajectory (filename, format)",
        },
    )

    def initialize(self):
        """
        Initialize the job.
        """
        super().initialize()

        self._atomicAliases = self.configuration["atom_aliases"]["value"]

        self._xtdfile = self.configuration["xtd_file"]

        self._xtdfile.build_chemical_system(self._atomicAliases)

        self._chemical_system = self._xtdfile.chemicalSystem

        self._trjfile = TrjFile(self.configuration["trj_file"]["filename"])

        # The number of steps of the analysis.
        self.numberOfSteps = self._trjfile["n_frames"]

        if self._trjfile["velocities_written"]:
            self._velocities = np.zeros(
                (self._chemical_system.number_of_atoms, 3), dtype=np.float64
            )
        else:
            self._velocities = None

        if self._trjfile["gradients_written"]:
            self._gradients = np.zeros(
                (self._chemical_system.number_of_atoms, 3), dtype=np.float64
            )
        else:
            self._gradients = None

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.configuration["output_files"]["file"],
            self._chemical_system,
            self.numberOfSteps,
            positions_dtype=self.configuration["output_files"]["dtype"],
            chunking_limit=self.configuration["output_files"]["chunk_size"],
            compression=self.configuration["output_files"]["compression"],
            initial_charges=self.configuration["xtd_file"].get_atom_charges(),
        )

    def run_step(self, index):
        """Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.
        """

        # The x, y and z values of the current frame.
        time, cell, xyz, velocities, gradients = self._trjfile.read_step(index)

        # If the universe is periodic set its shape with the current dimensions of the unit cell.
        conf = self._xtdfile._configuration
        movableAtoms = self._trjfile["mvofst"]
        conf["coordinates"][movableAtoms, :] = xyz
        if conf.is_periodic:
            if self._trjfile["defcel"]:
                conf.unit_cell = cell
            if self._configuration["fold"]["value"]:
                conf.fold_coordinates()

        if self._velocities is not None:
            self._velocities[movableAtoms, :] = velocities
            conf["velocities"] = self._velocities

        if self._gradients is not None:
            self._gradients[movableAtoms, :] = gradients
            conf["gradients"] = self._gradients

        self._trajectory.dump_configuration(
            conf,
            time,
            units={
                "time": "ps",
                "unit_cell": "nm",
                "coordinates": "nm",
                "velocities": "nm/ps",
                "gradients": "Da nm/ps2",
            },
        )

        return index, None

    def combine(self, index, x):
        """
        @param index: the index of the step.
        @type index: int.

        @param x:
        @type x: any.
        """

        pass

    def finalize(self):
        """
        Finalize the job.
        """

        self._trjfile.close()

        # Close the output trajectory.
        self._trajectory.write_standard_atom_database()
        self._trajectory.close()

        super().finalize()
