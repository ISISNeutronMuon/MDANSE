# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/VASP.py
# @brief     Implements module/class/test VASP
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

import numpy as np

from MDANSE.Core.Error import Error
from MDANSE.Chemistry.ChemicalEntity import Atom, ChemicalSystem
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.Configuration import PeriodicBoxConfiguration
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class XDATCARFileError(Error):
    pass


class VASPConverterError(Error):
    pass


class XDATCARFile(dict):
    def __init__(self, filename):
        self["instance"] = open(filename, "rb")

        # Read header
        self["instance"].readline()
        header = []
        while True:
            self._headerSize = self["instance"].tell()
            line = self["instance"].readline().strip()
            if not line or line.lower().startswith(b"direct"):
                self._frameHeaderSize = self["instance"].tell() - self._headerSize
                break
            header.append(line.decode())

        self["scale_factor"] = float(header[0])

        cell = " ".join(header[1:4]).split()

        cell = np.array(cell, dtype=np.float64)

        self["cell_shape"] = (
            np.reshape(cell, (3, 3))
            * self["scale_factor"]
            * measure(1.0, "ang").toval("nm")
        )

        self["atoms"] = list(
            zip(header[4].split(), [int(v) for v in header[5].split()])
        )

        self["n_atoms"] = sum([v[1] for v in self["atoms"]])

        # The point here is to determine if the trajectory is NVT or NPT. If traj is NPT, the box will change at each iteration and the "header" will appear betwwen every frame
        # We try to read the two first frames to figure it out
        nAtoms = 0
        while True:
            self._frameSize = self["instance"].tell()
            line = self["instance"].readline().strip()
            if not line or line.lower().startswith(b"direct"):
                break
            nAtoms += 1

        if nAtoms == self["n_atoms"]:
            # Traj is NVT
            # Structure is
            # Header
            # FrameHeader
            # Frame 1
            # FrameHeader
            # Frame 2
            # ...
            # With frameHeader being "dummy"
            self._npt = False
            self._frameSize -= self._headerSize
            self._actualFrameSize = self._frameSize - self._frameHeaderSize
        else:
            # Traj is NPT
            # Structure is
            # FrameHeader
            # Frame 1
            # FrameHeader
            # Frame 2
            # ...
            # With FrameHeader containing box size
            self._npt = True
            self._actualFrameSize = self._frameSize
            self._frameSize -= self._headerSize
            self._frameHeaderSize += self._headerSize
            self._headerSize = 0
            self._actualFrameSize = self._frameSize - self._frameHeaderSize
            # Retry to read the first frame
            self["instance"].seek(self._frameHeaderSize)
            nAtoms = 0
            while True:
                self._frameSize = self["instance"].tell()
                line = self["instance"].readline().strip()
                if len(line.split("  ")) != 3:
                    break
                nAtoms += 1

            if nAtoms != self["n_atoms"]:
                # Something went wrong
                raise XDATCARFileError(
                    "The number of atoms (%d) does not match the size of a frame (%d)."
                    % (nAtoms, self["n_atoms"])
                )

        # Read frame number
        self["instance"].seek(0, 2)
        self["n_frames"] = (
            self["instance"].tell() - self._headerSize
        ) / self._frameSize

        # Go back to top
        self["instance"].seek(0)

    def read_step(self, step):
        self["instance"].seek(self._headerSize + step * self._frameSize)

        if self._npt:
            # Read box size
            self["instance"].readline()
            header = []
            while True:
                line = self["instance"].readline().strip()
                if not line or line.lower().startswith("direct"):
                    break
                header.append(line)
            cell = " ".join(header[1:4]).split()
            cell = np.array(cell, dtype=np.float64)
            self["cell_shape"] = (
                np.reshape(cell, (3, 3))
                * self["scale_factor"]
                * measure(1.0, "ang").toval("nm")
            )
        else:
            self["instance"].read(self._frameHeaderSize)

        data = np.array(
            self["instance"].read(self._actualFrameSize).split(), dtype=np.float64
        )

        config = np.reshape(data, (self["n_atoms"], 3))

        return config

    def close(self):
        self["instance"].close()


class VASP(Converter):
    """
    Converts a VASP trajectory to a HDF trajectory.
    """

    label = "VASP (>=5)"

    settings = collections.OrderedDict()
    settings["xdatcar_file"] = (
        "InputFileConfigurator",
        {
            "wildcard": "XDATCAR files (XDATCAR*)|XDATCAR*|All files|*",
            "default": "INPUT_FILENAME",
            "label": "Input XDATCAR file",
        },
    )
    settings["time_step"] = (
        "FloatConfigurator",
        {"label": "time step", "default": 1.0, "mini": 1.0e-9},
    )
    settings["fold"] = (
        "BooleanConfigurator",
        {"default": False, "label": "Fold coordinates into box"},
    )
    settings["output_file"] = (
        "OutputFilesConfigurator",
        {
            "formats": ["MDTFormat"],
            "root": "xdatcar_file",
            "label": "MDANSE trajectory (filename, format)",
        },
    )

    def initialize(self):
        """
        Initialize the job.
        """

        self._xdatcarFile = XDATCARFile(self.configuration["xdatcar_file"]["filename"])

        # The number of steps of the analysis.
        self.numberOfSteps = int(self._xdatcarFile["n_frames"])

        self._chemicalSystem = ChemicalSystem()

        for symbol, number in self._xdatcarFile["atoms"]:
            for i in range(number):
                self._chemicalSystem.add_chemical_entity(
                    Atom(symbol=symbol, name="{:s}_{:d}".format(symbol, i))
                )

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.configuration["output_file"]["files"][0],
            self._chemicalSystem,
            self.numberOfSteps,
        )

    def run_step(self, index):
        """Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop note the index of the frame.
        """

        # Read the current step in the xdatcar file.
        coords = self._xdatcarFile.read_step(index)

        unitCell = UnitCell(self._xdatcarFile["cell_shape"])

        conf = PeriodicBoxConfiguration(
            self._trajectory.chemical_system, coords, unitCell
        )

        # The coordinates in VASP are in box format. Convert them into real coordinates.
        real_conf = conf.to_real_configuration()

        if self.configuration["fold"]["value"]:
            # The real coordinates are folded then into the simulation box (-L/2,L/2).
            real_conf.fold_coordinates()

        # Bind the configuration to the chemcial system
        self._trajectory.chemical_system.configuration = real_conf

        # Compute the actual time
        time = (
            index
            * self.configuration["time_step"]["value"]
            * measure(1.0, "fs").toval("ps")
        )

        # Dump the configuration to the output trajectory
        self._trajectory.dump_configuration(
            time, units={"time": "ps", "unit_cell": "nm", "coordinates": "nm"}
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

        self._xdatcarFile.close()

        # Close the output trajectory.
        self._trajectory.close()

        super(VASP, self).finalize()
