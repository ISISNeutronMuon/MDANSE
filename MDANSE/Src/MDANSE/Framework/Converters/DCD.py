# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/DCDConverter.py
# @brief     Implements module/class/test DCDConverter
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import os
import struct

import numpy as np

from MDANSE.Core.Error import Error
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Units import measure
from MDANSE.IO.PDBReader import PDBReader
from MDANSE.Mathematics.Geometry import get_basis_vectors_from_cell_parameters
from MDANSE.MolecularDynamics.Configuration import PeriodicRealConfiguration
from MDANSE.MolecularDynamics.Trajectory import (
    resolve_undefined_molecules_name,
    TrajectoryWriter,
)
from MDANSE.MolecularDynamics.UnitCell import UnitCell

PI_2 = 0.5 * np.pi
RECSCALE32BIT = 1
RECSCALE64BIT = 2


class DCDFileError(Error):
    pass


class ByteOrderError(Error):
    pass


class InputOutputError(Error):
    pass


class EndOfFile(Error):
    pass


class FortranBinaryFileError(Error):
    pass


def get_byte_order(filename):
    # Identity the byte order of the file by trial-and-error
    byteOrder = None

    # The DCD file is opened for reading in binary mode.
    data = open(filename, "rb").read(4)

    # Check for low and big endianness byte orders.
    for order in ["<", ">"]:
        reclen = struct.unpack(order + "i", data)[0]
        if reclen == 84:
            byteOrder = order
            break

        if byteOrder is None:
            raise ByteOrderError(
                "Invalid byte order. %s is not a valid DCD file" % filename
            )

    return byteOrder


class FortranBinaryFile(object):
    """Sets up a Fortran binary file reader.

    @note: written by Konrad Hinsen.
    """

    def __init__(self, filename):
        """The constructor.

        @param filename: the input file.
        @type filename: string.

        @param byte_order: the byte order to read the binary file.
        @type byte_order: string being one '@', '=', '<', '>' or '!'.
        """
        self.file = open(filename, "rb")
        self.byteOrder = get_byte_order(filename)

    def __iter__(self):
        return self

    def next_record(self):
        data = self.file.read(struct.calcsize("i"))
        if not data:
            raise StopIteration
        reclen = struct.unpack(self.byteOrder + "i", data)[0]
        data = self.file.read(reclen)
        reclen2 = struct.unpack(
            self.byteOrder + "i", self.file.read(struct.calcsize("i"))
        )[0]
        if reclen != reclen2:
            FortranBinaryFileError("Invalid block")

        return data

    def skip_record(self):
        data = self.file.read(struct.calcsize("i"))
        reclen = struct.unpack(self.byteOrder + "i", data)[0]
        self.file.seek(reclen, 1)
        reclen2 = struct.unpack(self.byteOrder + "i", self.file.read(4))[0]
        assert reclen == reclen2

    def get_record(self, fmt, repeat=False):
        """Reads a record of the binary file.

        @param format: the format corresponding to the binray structure to read.
        @type format: string.

        @param repeat: if True, will repeat the reading.
        @type repeat: bool.
        """

        try:
            data = self.next_record()
        except StopIteration:
            raise EndOfFile()
        if repeat:
            unit = struct.calcsize(self.byteOrder + fmt)
            assert len(data) % unit == 0
            fmt = (len(data) / unit) * fmt
        try:
            return struct.unpack(self.byteOrder + fmt, data)
        except:
            raise


class DCDFile(FortranBinaryFile, dict):
    def __init__(self, filename):
        FortranBinaryFile.__init__(self, filename)

        self["filename"] = filename

        self.read_header()

    def read_header(self):
        # Read a block
        data = self.next_record()

        if data[:4] != "CORD":
            raise DCDFileError("Unrecognized DCD format")

        temp = struct.unpack(self.byteOrder + "20i", data[4:])

        self["charmm"] = temp[-1]

        if self["charmm"]:
            temp = struct.unpack(self.byteOrder + "9if10i", data[4:])
        else:
            temp = struct.unpack(self.byteOrder + "9id9i", data[4:])

        # Store the number of sets of coordinates
        self["nset"] = self["n_frames"] = temp[0]

        # Store the starting time step
        self["istart"] = temp[1]

        # Store the number of timesteps between dcd saves
        self["nsavc"] = temp[2]

        # Stores the number of fixed atoms
        self["namnf"] = temp[8]

        # Stop if there are fixed atoms.
        if self["namnf"] > 0:
            raise DCDFileError("Can not handle fixed atoms yet.")

        self["delta"] = temp[9]

        # The time step is in AKMA time
        self["time_step"] = (
            self["nsavc"] * self["delta"] * measure(1.0, "akma_time").toval("ps")
        )

        self["has_pbc_data"] = temp[10]

        self["has_4d"] = temp[11]

        # Read a block
        data = self.next_record()

        nLines = struct.unpack(self.byteOrder + b"I", data[0:4])[0]

        self["title"] = []
        for i in range(nLines):
            temp = struct.unpack(
                self.byteOrder + "80c", data[4 + 80 * i : 4 + 80 * (i + 1)]
            )
            self["title"].append("".join(temp).strip())

        self["title"] = "\n".join(self["title"])

        # Read a block
        data = self.next_record()

        # Read the number of atoms.
        self["natoms"] = struct.unpack(self.byteOrder + b"I", data)[0]

    def read_step(self):
        """
        Reads a frame of the DCD file.
        """

        if self["has_pbc_data"]:
            unitCell = np.array(self.get_record("6d"), dtype=np.float64)
            unitCell = unitCell[[0, 2, 5, 1, 3, 4]]
            # The unit cell is converted from ang to nm
            unitCell[0:3] *= measure(1.0, "ang").toval("nm")
            # This file was generated by CHARMM, or by NAMD > 2.5, with the angle
            # cosines of the periodic cell angles written to the DCD file.
            # This formulation improves rounding behavior for orthogonal cells
            # so that the angles end up at precisely 90 degrees, unlike acos().
            # See https://github.com/MDAnalysis/mdanalysis/wiki/FileFormats for info
            if np.all(abs(unitCell[3:]) <= 1):
                unitCell[3:] = PI_2 - np.arcsin(unitCell[3:])
            else:
                # assume the angles are stored in degrees (NAMD <= 2.5)
                unitCell[3:] = np.deg2rad(unitCell[3:])

        else:
            unitCell = None

        fmt = "%df" % self["natoms"]
        config = np.empty((self["natoms"], 3), dtype=np.float64)
        config[:, 0] = np.array(self.get_record(fmt), dtype=np.float64)
        config[:, 1] = np.array(self.get_record(fmt), dtype=np.float64)
        config[:, 2] = np.array(self.get_record(fmt), dtype=np.float64)
        config *= measure(1.0, "ang").toval("nm")

        if self["has_4d"]:
            self.skip_record()

        return unitCell, config

    def skip_step(self):
        """Skips a frame of the DCD file."""
        nrecords = 3
        if self["has_pbc_data"]:
            nrecords += 1
        if self["has_4d"]:
            nrecords += 1
        for _ in range(nrecords):
            self["binary"].skip_record()

    def __iter__(self):
        return self

    def next_step(self):
        try:
            return self.read_step()
        except EndOfFile:
            raise StopIteration


class DCD(Converter):
    """
    Converts a DCD trajectory to a HDF trajectory.
    """

    settings = collections.OrderedDict()
    settings["pdb_file"] = (
        "InputFileConfigurator",
        {
            "wildcard": "PDB files (*.pdb)|*.pdb|All files|*",
            "default": "INPUT_FILENAME.pdb",
            "label": "Input PDB file",
        },
    )
    settings["dcd_file"] = (
        "InputFileConfigurator",
        {
            "wildcard": "DCD files (*.dcd)|*.dcd|All files|*",
            "default": "INPUT_FILENAME.dcd",
            "label": "Input DCD file",
        },
    )
    settings["time_step"] = (
        "FloatConfigurator",
        {"default": 1.0, "label": "Time step (ps)"},
    )
    settings["fold"] = (
        "BooleanConfigurator",
        {"default": False, "label": "Fold coordinates into box"},
    )
    settings["output_file"] = (
        "SingleOutputFileConfigurator",
        {
            "format": "MDTFormat",
            "root": "pdb_file",
            "label": "MDANSE trajectory (filename, format)",
        },
    )

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        self.configuration["dcd_file"]["instance"] = DCDFile(
            self.configuration["dcd_file"]["filename"]
        )

        # The number of steps of the analysis.
        self.numberOfSteps = self.configuration["dcd_file"]["instance"]["n_frames"]

        # Create all chemical entities from the PDB file.
        pdb_reader = PDBReader(self.configuration["pdb_file"]["filename"])
        self._chemical_system = pdb_reader.build_chemical_system()

        resolve_undefined_molecules_name(self._chemical_system)

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.configuration["output_file"]["file"],
            self._chemical_system,
            self.numberOfSteps,
        )

    def run_step(self, index):
        """
        Runs a single step of the job.\n

        :Parameters:
            #. index (int): The index of the step.
        :Returns:
            #. index (int): The index of the step.
        """

        # The x, y and z values of the current frame.
        unit_cell, config = self.configuration["dcd_file"]["instance"].read_step()
        unit_cell = get_basis_vectors_from_cell_parameters(unit_cell)
        unit_cell = UnitCell(unit_cell)

        conf = PeriodicRealConfiguration(
            self._trajectory._chemical_system, config, unit_cell
        )

        if self.configuration["fold"]["value"]:
            conf.fold_coordinates()

        self._trajectory._chemical_system.configuration = conf

        # The current time.
        time = (index + 1) * self.configuration["time_step"]["value"]

        # Store a snapshot of the current configuration in the output trajectory.
        self._trajectory.dump_configuration(
            time, units={"time": "ps", "unit_cell": "nm", "coordinates": "nm"}
        )

        return index, None

    def combine(self, index, x):
        """
        Combines returned results of run_step.\n
        :Parameters:
            #. index (int): The index of the step.\n
            #. x (any): The returned result(s) of run_step
        """

        pass

    def finalize(self):
        """
        Finalizes the calculations (e.g. averaging the total term, output files creations ...).
        """

        # Close the output trajectory.
        self._trajectory.close()

        super(DCD, self).finalize()
