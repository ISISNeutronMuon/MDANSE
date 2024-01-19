# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/Discover.py
# @brief     Implements module/class/test Discover
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os
import collections

import struct

import numpy as np


from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.IO.XTDFile import XTDFile
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicRealConfiguration,
    RealConfiguration,
)
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class HisFile(dict):
    def __init__(self, hisfilename):
        self["instance"] = open(hisfilename, "rb")

        self.parse_header()

    def parse_header(self):
        hisfile = self["instance"]

        # Record 1
        rec = "!4x"
        recSize = struct.calcsize(rec)
        hisfile.read(recSize)

        rec = "!i8x"
        self._rec1Size = struct.calcsize(rec)
        hisfile.read(self._rec1Size)

        # Record 2
        rec = "!80sd8x"
        recSize = struct.calcsize(rec)
        VERSION_INFO, VERSION = struct.unpack(rec, hisfile.read(recSize))
        VERSION_INFO = VERSION_INFO.strip()

        # Record 3+4
        rec = "!80s8x80s8x"
        recSize = struct.calcsize(rec)
        self["title"] = struct.unpack(rec, hisfile.read(recSize))
        self["title"] = "\n".join([t.decode("utf-8") for t in self["title"]])

        # Record 5
        rec = "!i"
        recSize = struct.calcsize(rec)
        N_ATTYP = struct.unpack(rec, hisfile.read(recSize))[0]
        rec = "!" + "%ds" % (4 * N_ATTYP) + "%dd" % N_ATTYP + "8x"
        recSize = struct.calcsize(rec)
        hisfile.read(recSize)

        # Record 6
        rec = "!i"
        recSize = struct.calcsize(rec)
        N_NMRES = struct.unpack(rec, hisfile.read(recSize))[0]
        rec = "!" + "%ds" % (4 * N_NMRES) + "8x"
        recSize = struct.calcsize(rec)
        hisfile.read(recSize)

        # Record 7
        rec = "!i"
        recSize = struct.calcsize(rec)
        self["n_atoms"] = N_ATOMS = struct.unpack(rec, hisfile.read(recSize))[0]
        rec = "!" + "%di" % N_ATOMS
        if VERSION < 2.9:
            rec += "%ds" % (4 * N_ATOMS)
        else:
            rec += "%ds" % (5 * N_ATOMS)
        rec += "8x"
        recSize = struct.calcsize(rec)
        hisfile.read(recSize)

        # Record 8
        rec = "!ii"
        recSize = struct.calcsize(rec)
        _, N_MOVAT = struct.unpack(rec, hisfile.read(recSize))
        if VERSION >= 2.6:
            rec = "!" + "%di" % N_MOVAT
            recSize = struct.calcsize(rec)
            self["movable_atoms"] = (
                np.array(struct.unpack(rec, hisfile.read(recSize)), dtype=np.int32) - 1
            )
        else:
            self["movable_atoms"] = list(range(self["n_atoms"]))
        rec = "!8x"
        recSize = struct.calcsize(rec)
        hisfile.read(recSize)

        # Record 9
        rec = "!i"
        recSize = struct.calcsize(rec)
        N_MOL = struct.unpack(rec, hisfile.read(recSize))[0]
        rec = "!" + "%di" % N_MOL + "%di" % N_MOL + "8x"
        recSize = struct.calcsize(rec)
        hisfile.read(recSize)

        # Record 10
        rec = "!i"
        recSize = struct.calcsize(rec)
        N_RES = struct.unpack(rec, hisfile.read(recSize))[0]
        rec = "!" + "%di" % (2 * N_RES) + "%di" % N_RES + "8x"
        recSize = struct.calcsize(rec)
        hisfile.read(recSize)

        # Record 11
        rec = "!i"
        recSize = struct.calcsize(rec)
        N_BONDS = struct.unpack(rec, hisfile.read(recSize))[0]
        if N_BONDS > 0:
            rec = "!" + "%di" % (2 * N_BONDS)
            recSize = struct.calcsize(rec)
            _ = struct.unpack(rec, hisfile.read(recSize))
        rec = "!8x"
        recSize = struct.calcsize(rec)
        hisfile.read(recSize)

        # Record 12
        rec = "!6d"
        recSize = struct.calcsize(rec)
        _ = struct.unpack(rec, hisfile.read(recSize))
        rec = "!9d"
        recSize = struct.calcsize(rec)
        self["initial_cell"] = np.reshape(
            np.array(struct.unpack(rec, hisfile.read(recSize)), dtype=np.float64),
            (3, 3),
        ) * measure(1.0, "ang").toval("nm")

        rec = "!4134di4di6d6i8x"
        recSize = struct.calcsize(rec)
        hisfile.read(recSize)

        # Record 13
        rec = "!idii8x"
        recSize = struct.calcsize(rec)
        N_ENER, TIME_STEP, _, _ = struct.unpack(rec, hisfile.read(recSize))
        self["time_step"] = TIME_STEP * measure(1.0, "fs").toval("ps")

        # Record 14
        rec = (
            "!3d"
            + "%dd" % N_ENER
            + "%dd" % N_MOL
            + "%dd" % (N_MOL * N_ENER)
            + "%dd" % (4 * N_MOL + 2 + 54)
            + "8x"
        )
        self._rec14Size = struct.calcsize(rec)
        hisfile.read(self._rec14Size)

        # Record 15
        rec = "!" + "%df" % (3 * N_ATOMS) + "8x"
        recSize = struct.calcsize(rec)
        self["initial_coordinates"] = np.reshape(
            struct.unpack(rec, hisfile.read(recSize)), (N_ATOMS, 3)
        )
        self["initial_coordinates"] *= measure(1.0, "ang").toval("nm")

        # Record 16
        rec = "!" + "%df" % (3 * N_ATOMS) + "8x"
        recSize = struct.calcsize(rec)
        self["initial_velocities"] = np.reshape(
            struct.unpack(rec, hisfile.read(recSize)), (N_ATOMS, 3)
        )
        self["initial_velocities"] *= measure(1.0, "ang / fs").toval("nm/ps")

        self._headerSize = hisfile.tell()

        self._recN2 = "!15d8x"
        self._recN2Size = struct.calcsize(self._recN2)

        if VERSION < 2.6:
            self["n_movable_atoms"] = N_ATOMS
        else:
            self["n_movable_atoms"] = N_MOVAT
        self._recCoord = "!" + "%df" % (3 * self["n_movable_atoms"]) + "8x"
        self._recCoordSize = struct.calcsize(self._recCoord)
        self._recVel = "!" + "%df" % (3 * self["n_movable_atoms"]) + "8x"
        self._recVelSize = struct.calcsize(self._recVel)

        self._frameSize = (
            self._rec1Size
            + self._rec14Size
            + self._recN2Size
            + self._recCoordSize
            + self._recVelSize
        )

        hisfile.seek(0, 2)

        self["n_frames"] = (hisfile.tell() - self._headerSize) // self._frameSize

    def read_step(self, index):
        hisfile = self["instance"]

        time = index * self["time_step"]

        hisfile.seek(
            self._headerSize
            + index * self._frameSize
            + self._rec1Size
            + self._rec14Size
        )

        cell = np.reshape(
            np.array(struct.unpack(self._recN2, hisfile.read(self._recN2Size))[6:]),
            (3, 3),
        ) * measure(1.0, "ang").toval("nm")

        coords = np.reshape(
            struct.unpack(self._recCoord, hisfile.read(self._recCoordSize)),
            (self["n_movable_atoms"], 3),
        )
        coords *= measure(1.0, "ang").toval("nm")

        vels = np.reshape(
            struct.unpack(self._recVel, hisfile.read(self._recVelSize)),
            (self["n_movable_atoms"], 3),
        )
        vels *= measure(1.0, "ang / fs").toval("nm/ps")

        return time, cell, coords, vels

    def close(self):
        self["instance"].close()


class Discover(Converter):
    """
    Converts a Discover trajectory to a HDF trajectory.
    """

    label = "Discover"

    category = ("Converters", "Materials Studio")

    settings = collections.OrderedDict()
    settings["xtd_file"] = (
        "InputFileConfigurator",
        {
            "wildcard": "XTD files (*.xtd)|*.xtd|All files|*",
            "default": os.path.join(
                "..", "..", "..", "Data", "Trajectories", "Discover", "sushi.xtd"
            ),
            "label": "Input XTD file",
        },
    )
    settings["his_file"] = (
        "InputFileConfigurator",
        {
            "wildcard": "HIS files (*.his)|*.his|All files|*",
            "default": os.path.join(
                "..", "..", "..", "Data", "Trajectories", "Discover", "sushi.his"
            ),
            "label": "Input HIS file",
        },
    )
    settings["fold"] = (
        "BooleanConfigurator",
        {"default": True, "label": "Fold coordinates into box"},
    )
    settings["output_file"] = (
        "OutputFilesConfigurator",
        {
            "formats": ["MDTFormat"],
            "root": "xtd_file",
            "label": "Output trajectory file name",
        },
    )

    def initialize(self):
        """
        Initialize the job.
        """

        self._xtdfile = XTDFile(self.configuration["xtd_file"]["filename"])

        self._xtdfile.build_chemical_system()

        self._chemicalSystem = self._xtdfile.chemicalSystem

        self._hisfile = HisFile(self.configuration["his_file"]["filename"])

        # The number of steps of the analysis.
        self.numberOfSteps = self._hisfile["n_frames"]

        variables = {}
        variables["velocities"] = self._hisfile["initial_velocities"]

        if self._chemicalSystem.configuration.is_periodic:
            unitCell = UnitCell(self._hisfile["initial_cell"])
            realConf = PeriodicRealConfiguration(
                self._chemicalSystem,
                self._hisfile["initial_coordinates"],
                unitCell,
                **variables,
            )
        else:
            realConf = RealConfiguration(
                self._chemicalSystem, self._hisfile["initial_coordinates"], **variables
            )

        if self.configuration["fold"]["value"]:
            realConf.fold_coordinates()

        self._chemicalSystem.configuration = realConf

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.configuration["output_file"]["file"],
            self._chemicalSystem,
            self.numberOfSteps,
        )

    def run_step(self, index):
        """Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.
        """

        time, cell, config, vel = self._hisfile.read_step(index)

        conf = self._trajectory.chemical_system.configuration
        if conf.is_periodic:
            conf.unit_cell = cell

        movableAtoms = self._hisfile["movable_atoms"]

        conf["coordinates"][movableAtoms, :] = config
        conf["velocities"][movableAtoms, :] = vel

        conf.fold_coordinates()

        self._trajectory.chemical_system.configuration = conf

        self._trajectory.dump_configuration(
            time,
            units={
                "time": "ps",
                "unit_cell": "nm",
                "coordinates": "nm",
                "velocities": "nm/ps",
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

        self._hisfile.close()

        # Close the output trajectory.
        self._trajectory.close()

        super(Discover, self).finalize()
