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
import re

import numpy as np


from MDANSE.Core.Error import Error
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Chemistry.ChemicalEntity import Atom, AtomCluster, ChemicalSystem
from MDANSE.Core.Error import Error
from MDANSE.Framework.Units import measure
from MDANSE.Mathematics.Graph import Graph
from MDANSE.MolecularDynamics.Configuration import (
    PeriodicBoxConfiguration,
    PeriodicRealConfiguration,
)
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class XYZFileError(Error):
    pass


class XYZFile(dict):
    """This class loads the contents of an XYZ file,
    which in the case of CP2K may contain either the
    positions of atoms, or velocities. In either case
    there will be 3 components per atom.
    """

    def __init__(self, filename):
        self["instance"] = open(filename, "r")

        self["instance"].seek(0, 0)

        try:
            self["n_atoms"] = int(self["instance"].readline().strip())
        except ValueError:
            raise XYZFileError(
                "Could not read the number of atoms in %s file" % filename
            )

        self._nAtomsLineSize = self["instance"].tell()
        self["instance"].readline()
        self._headerSize = self["instance"].tell()
        self["atoms"] = []
        for _ in range(self["n_atoms"]):
            line = self["instance"].readline()
            atom = line.split()[0].strip()
            self["atoms"].append(atom)

        # The frame size define the total size of a frame (number of atoms header + time info line + coordinates block)
        self._frameSize = self["instance"].tell()
        self._coordinatesSize = self._frameSize - self._headerSize

        # Compute the frame number
        self["instance"].seek(0, 2)
        self["n_frames"] = self["instance"].tell() // self._frameSize

        # If the trajectory has more than one step, compute the time step as the difference between the second and the first time step
        if self["n_frames"] > 1:
            firstTimeStep = self.fetch_time_step(0)
            secondTimeStep = self.fetch_time_step(1)
            self["time_step"] = secondTimeStep - firstTimeStep
        else:
            self["time_step"] = self.fetch_time_step(0)

        # Go back to top
        self["instance"].seek(0)

    def fetch_time_step(self, step: int):
        """Finds the value of simulation time at the
        nth simulation step.

        Arguments:
            step -- number of the simulation frame to check

        Raises:
            XYZFileError: If a valid time stamp could not be find

        Returns:
            float -- the time stamp of the frame
        """
        self["instance"].seek(step * self._frameSize + self._nAtomsLineSize)
        timeLine = self["instance"].readline().strip()
        matches = re.findall("^i =.*, time =(.*), E =.*$", timeLine)
        if len(matches) != 1:
            raise XYZFileError("Could not fetch the time step from XYZ file")
        try:
            timeStep = float(matches[0])
        except ValueError:
            raise XYZFileError("Could not cast the timestep to a floating")
        else:
            return timeStep

    def read_step(self, step: int):
        """Reads and returns an array of atom coordinates the nth
        simulation frame.

        Arguments:
            step -- the number of the simulation step (frame) to be returned.

        Returns:
            ndarray -- an (N,3) array containing the coordinates of N atoms
               at the requested simulation step.
        """
        self["instance"].seek(step * self._frameSize + self._headerSize)

        temp = np.array(self["instance"].read(self._coordinatesSize).split()).reshape(
            (self["n_atoms"], 4)
        )

        config = np.array(temp[:, 1:], dtype=np.float64)

        return config

    def close(self):
        """Closes the file that was, until now, open for reading."""
        self["instance"].close()


class CellFileError(Error):
    pass


class CellFile(dict):
    """Opens and reads the CP2K output file containing the
    unit cell size for each simulation step.
    """

    def __init__(self, filename):
        self["instance"] = open(filename, "r")

        # Skip the first line
        self["instance"].readline()

        contents = self["instance"].readlines()
        if not contents:
            raise CellFileError("No cell contents found in the cell file")

        self["n_frames"] = len(contents)

        time_steps = []
        self["cells"] = []
        for line in contents:
            words = line.strip().split()

            if len(words) != 12:
                raise CellFileError("Invalid format for cell line")

            try:
                time_steps.append(float(words[1]))
            except ValueError:
                raise CellFileError("Can not cast time step to floating")

            try:
                cell = np.array(words[2:11], dtype=np.float64).reshape((3, 3))
            except ValueError:
                raise CellFileError("Can not cast cell coordinates to floating")

            self["cells"].append(cell)

        if len(time_steps) == 1:
            self["time_step"] = 0.0
        else:
            self["time_step"] = time_steps[1] - time_steps[0]

    def read_step(self, step: int):
        """Reads and returns the unit cell constants at the requested
        simulation step (frame)

        Arguments:
            step -- number of the simulation frame to be read

        Raises:
            CellFileError: if the frame with the number *step* cannot be read

        Returns:
            ndarray -- a (3,3) array of unit cell constants
        """

        if step < 0 or step >= self["n_frames"]:
            raise CellFileError("Invalid step number")

        return self["cells"][step]

    def close(self):
        """Closes the file that was, until now, open for reading."""
        self["instance"].close()


class CP2KConverterError(Error):
    pass


class CP2K(Converter):
    """
    Converts a CP2K trajectory to an HDF5 trajectory in the MDANSE format.
    """

    label = "CP2K"

    settings = collections.OrderedDict()
    settings["pos_file"] = (
        "InputFileConfigurator",
        {
            "wildcard": "XYZ files (*.xyz)|*.xyz|All files|*",
            "default": os.path.join(
                "..",
                "..",
                "..",
                "Data",
                "Trajectories",
                "CP2K",
                "p1-supercell-pos-ejemplo.xyz",
            ),
            "label": "Positions file (XYZ)",
        },
    )
    settings["vel_file"] = (
        "InputFileConfigurator",
        {
            "wildcard": "XYZ files (*.xyz)|*.xyz|All files|*",
            "default": os.path.join(
                "..",
                "..",
                "..",
                "Data",
                "Trajectories",
                "CP2K",
                "p1-supercell-vel-ejemplo.xyz",
            ),
            "optional": True,
            "label": "Velocity file (XYZ, optional)",
        },
    )
    settings["cell_file"] = (
        "InputFileConfigurator",
        {
            "wildcard": "Cell files (*.cell)|*.cell|All files|*",
            "default": os.path.join(
                "..", "..", "..", "Data", "Trajectories", "CP2K", "p1-supercell-1.cell"
            ),
            "label": "CP2K unit cell file (.cell)",
        },
    )
    settings["output_file"] = (
        "OutputFilesConfigurator",
        {
            "formats": ["MDTFormat"],
            "root": "xdatcar_file",
            "label": "Output trajectory file name",
        },
    )

    def initialize(self):
        """
        Initialize the job.
        Opens the input files and checks them for consistency.
        """

        self._xyzFile = XYZFile(self.configuration["pos_file"]["filename"])

        if self.configuration["vel_file"]:
            self._velFile = XYZFile(self.configuration["vel_file"]["filename"])
            if abs(self._xyzFile["time_step"] - self._velFile["time_step"]) > 1.0e-09:
                raise CP2KConverterError(
                    "Inconsistent time step between pos and vel files"
                )

            if self._xyzFile["n_frames"] != self._velFile["n_frames"]:
                raise CP2KConverterError(
                    "Inconsistent number of frames between pos and vel files"
                )

        self._cellFile = CellFile(self.configuration["cell_file"]["filename"])

        if abs(self._cellFile["time_step"] - self._xyzFile["time_step"]) > 1.0e-09:
            print((self._cellFile["time_step"], self._xyzFile["time_step"]))
            raise CP2KConverterError(
                "Inconsistent time step between pos and cell files"
            )

        if self._cellFile["n_frames"] != self._xyzFile["n_frames"]:
            raise CP2KConverterError(
                "Inconsistent number of frames between pos and cell files"
            )

        # The number of steps of the analysis.
        self.numberOfSteps = self._xyzFile["n_frames"]

        self._chemical_system = ChemicalSystem()

        for i, symbol in enumerate(self._xyzFile["atoms"]):
            self._chemical_system.add_chemical_entity(
                Atom(symbol=symbol, name="%s_%d" % (symbol, i + 1))
            )

        self._trajectory = TrajectoryWriter(
            self.configuration["output_file"]["file"],
            self._chemical_system,
            self.numberOfSteps,
        )
        # A MMTK trajectory is opened for writing.

        data_to_be_written = ["configuration", "time"]
        if self.configuration["vel_file"]:
            data_to_be_written.append("velocities")

    def run_step(self, index):
        """Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.

        @note: the argument index is the index of the loop not the index of the frame.
        """

        # Read the current coordinates in the XYZ file.
        coords = self._xyzFile.read_step(index) * measure(1.0, iunit="ang").toval("nm")

        unitcell = UnitCell(
            self._cellFile.read_step(index) * measure(1.0, iunit="ang").toval("nm")
        )

        variables = {}

        variables["velocities"] = self._velFile.read_step(index) * measure(
            1.0, iunit="ang/fs"
        ).toval("nm/ps")

        realConf = PeriodicRealConfiguration(
            self._trajectory.chemical_system, coords, unitcell, **variables
        )

        realConf.fold_coordinates()

        self._trajectory.chemical_system.configuration = realConf

        time = index * self._xyzFile["time_step"] * measure(1.0, iunit="fs").toval("ps")

        # A snapshot is created out of the current configuration.
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
        Closes the files and calls the
        superclass finalize method.
        """

        self._xyzFile.close()

        if self.configuration["vel_file"]:
            self._velFile.close()

        self._cellFile.close()

        # Close the output trajectory.
        self._trajectory.close()

        super(CP2K, self).finalize()
