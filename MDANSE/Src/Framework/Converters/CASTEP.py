# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/Castep.py
# @brief     Implements module/class/test Castep
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
import itertools
import re

import numpy as np


from MDANSE.Chemistry.ChemicalEntity import Atom, ChemicalSystem
from MDANSE.Core.Error import Error
from MDANSE.Framework.Converters.Converter import Converter
from MDANSE.Framework.Units import measure
from MDANSE.MolecularDynamics.Configuration import PeriodicRealConfiguration
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell

HBAR = measure(1.05457182e-34, "kg m2 / s").toval("uma nm2 / ps")
HARTREE = measure(27.2113845, "eV").toval("uma nm2 / ps2")
BOHR = measure(5.29177210903e-11, "m").toval("nm")


class CASTEPError(Error):
    pass


class MDFile(dict):
    """
    Class representing a .md file format (documentation can be found at
    https://www.tcm.phy.cam.ac.uk/castep/MD/node13.html). It is used to determine the structure of the file (eg. the
    length of each section) and to read the information stored in one frame of the trajectory.
    """

    def __init__(self, filename):
        """
        :param filename: The path to the .md file.
        :type filename: str
        """

        self["instance"] = open(filename, "rt")  # Open the provided file.

        # Skip over the header
        while True:
            line = self["instance"].readline()
            if re.search("END", line):
                self["instance"].readline()
                break
            # If a line storing data is read, something is wrong with the header.
            elif re.match(".*<-- h$", line):
                raise CASTEPError(
                    "The provided input file is corrupted. Due to unexpected END header line, the header"
                    "length could not be determined."
                )

        self._headerSize = self["instance"].tell()  # Record the length of the header

        # Prepare a variable storing information about a non-specific frame.
        self._frameInfo = {"time_step": [0], "cell_data": [], "data": []}

        self["instance"].readline()  # Skip the line storing time information.
        # Save the length of the line storing time information
        self._frameInfo["time_step"].append(self["instance"].tell() - self._headerSize)

        while True:
            prevPos = self["instance"].tell()

            line = self["instance"].readline().strip()

            # If the properties of the cell data have not been determined yet and the current line documents cell data
            if not self._frameInfo["cell_data"] and re.match(".*<-- h$", line):
                # Save how far (in character number) the cell data is from the start of the frame
                self._frameInfo["cell_data"].append(prevPos - self._headerSize)
                # Skip the next two lines since cell data is always three lines long
                self["instance"].readline()
                self["instance"].readline()
                # Save the length of the cell data
                self._frameInfo["cell_data"].append(
                    self["instance"].tell()
                    - self._frameInfo["cell_data"][0]
                    - self._headerSize
                )

            # If the properties of the positional data have not been stored yet and the line stores this data
            elif not self._frameInfo["data"] and re.match(".*<-- R$", line):
                # Save how far (in character number) the positional data is from the start of the frame
                self._frameInfo["data"].append(prevPos - self._headerSize)

            if not line:
                # Save the length of a frame minus one line of ionic data
                self._frameInfo["data"].append(
                    prevPos - self._frameInfo["data"][0] - self._headerSize
                )
                break

        # Save the length of the frame, including a blank line
        self._frameSize = self["instance"].tell() - self._headerSize

        # Read the whole ionic data block (positions, velocities, and forces) of the first frame
        self["instance"].seek(self._headerSize + self._frameInfo["data"][0])
        frame = self["instance"].read(self._frameInfo["data"][1]).splitlines()
        self["n_atoms"] = (
            len(frame) // 3
        )  # Save the number of atoms (length of positional data)

        # Create a list storing the chemical symbol of the element described on each line of positional data
        tmp = [f.split()[0] for f in frame[: self["n_atoms"]]]
        # Save a list of tuples where each tuple consists of the symbol on the amount of those atoms in the simulation
        self["atoms"] = [
            (element, len(list(group))) for element, group in itertools.groupby(tmp)
        ]

        # Move file handle to the end of the file
        self["instance"].seek(0, 2)
        # Save the number of frames
        self["n_frames"] = (
            self["instance"].tell() - self._headerSize
        ) // self._frameSize
        self["instance"].seek(0)  # Move file handle to the beginning of the file

    def read_step(self, step):
        """
        Extracts data from one frame of the trajectory

        :param step: The number of the frame to be read.
        :type step: int

        :return: The time of the chosen frame, the cell vectors, and the positions of all atoms in three different units
        :rtype: (float, tuple, np.array)-tuple
        """

        start = (
            self._headerSize + step * self._frameSize
        )  # Determine where the step-th frame starts in the file

        # Move file handle to the starts of the line storing the information about time
        self["instance"].seek(start + self._frameInfo["time_step"][0])

        # Read the time stored in the line and convert its units
        timeStep = float(self["instance"].read(self._frameInfo["time_step"][1]))
        timeStep *= HBAR / HARTREE

        # Read and process the cell data
        self["instance"].seek(
            start + self._frameInfo["cell_data"][0]
        )  # Move to the start of cell data
        unitCell = (
            self["instance"].read(self._frameInfo["cell_data"][1]).splitlines()
        )  # Read the cell data by line
        # Generate an array of three vectors where each vector is constructed from its components stored in each line
        unitCell = np.array(
            [[float(bb) for bb in b.strip().split()[:3]] for b in unitCell]
        )
        unitCell *= BOHR
        unitCell = UnitCell(unitCell)

        self["instance"].seek(
            start + self._frameInfo["data"][0]
        )  # Move to the start of positional data
        # Create an array composed of the data points in each line of the positional data
        config = np.array(
            self["instance"].read(self._frameInfo["data"][1]).split(), dtype=str
        )
        config = np.reshape(
            config, (3 * self["n_atoms"], 7)
        )  # Reshape the 1D array so that it is organised by lines
        config = config[:, 2:5].astype(np.float64)  # Extract the coordintates only

        # Convert the units of the positions
        config[0 : self["n_atoms"], :] *= BOHR
        config[self["n_atoms"] : 2 * self["n_atoms"], :] *= BOHR * HARTREE / HBAR
        config[2 * self["n_atoms"] : 3 * self["n_atoms"], :] *= HARTREE / BOHR

        return timeStep, unitCell, config

    def close(self):
        """Closes the file."""
        self["instance"].close()


class CASTEP(Converter):
    """
    Converts a Castep Trajectory into a HDF trajectory file.
    """

    label = "CASTEP"

    settings = collections.OrderedDict()
    settings["castep_file"] = (
        "input_file",
        {
            "wildcard": "MD files (*.md)|*.md|All files|*",
            "default": os.path.join(
                "..", "..", "..", "Data", "Trajectories", "CASTEP", "PBAnew.md"
            ),
            "label": "Input MD file",
        },
    )
    settings["fold"] = (
        "BooleanConfigurator",
        {"default": False, "label": "Fold coordinates into box"},
    )
    settings["output_file"] = (
        "single_output_file",
        {
            "format": "HDFFormat",
            "root": "castep_file",
            "label": "Output trajectory file name",
        },
    )

    def initialize(self):
        """
        Initialize the input parameters and analysis self variables
        """

        # Create a representation of md file
        self._castepFile = MDFile(self.configuration["castep_file"]["filename"])

        # Save the number of steps
        self.numberOfSteps = self._castepFile["n_frames"]

        # Create a bound universe
        self._chemical_system = ChemicalSystem()

        # Populate the universe with atoms based on how many of each atom is in the read trajectory
        for symbol, number in self._castepFile["atoms"]:
            for i in range(number):
                self._chemical_system.add_chemical_entity(
                    Atom(symbol=symbol, name="%s_%d" % (symbol, i))
                )

        # A trajectory is opened for writing.
        self._trajectory = TrajectoryWriter(
            self.configuration["output_file"]["file"],
            self._chemical_system,
            self.numberOfSteps,
        )

    def run_step(self, index):
        """Runs a single step of the job.

        @param index: the index of the step.
        @type index: int.

        :return: The index of the step and None
        :rtype: (int, None)-tuple

        @note: the argument index is the index of the loop not the index of the frame.
        """

        # Retrieve the number of atoms
        nAtoms = self._castepFile["n_atoms"]

        # Read the informatino in the frame
        time_step, unit_cell, config = self._castepFile.read_step(index)

        coords = config[0:nAtoms, :]
        variables = {}
        variables["velocities"] = config[nAtoms : 2 * nAtoms, :]
        variables["gradients"] = config[2 * nAtoms : 3 * nAtoms, :]

        conf = PeriodicRealConfiguration(
            self._trajectory.chemical_system, coords, unit_cell, **variables
        )

        if self.configuration["fold"]["value"]:
            conf.fold_coordinates()

        self._trajectory.chemical_system.configuration = conf

        self._trajectory.dump_configuration(
            time_step,
            units={
                "time": "ps",
                "coordinates": "nm",
                "unit_cell": "nm",
                "velocities": "nm/ps",
                "gradients": "uma nm/ps2",
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

        self._castepFile.close()  # Close the .md file.

        # Close the output trajectory.
        self._trajectory.close()

        super(CASTEP, self).finalize()
