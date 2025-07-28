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

import re
from collections.abc import Iterable

import numpy as np

from MDANSE.Core.Error import Error
from MDANSE.Framework.AtomMapping import AtomLabel

from .FileWithAtomDataConfigurator import FileWithAtomDataConfigurator


class XYZFileError(Error):
    pass


class XYZFileConfigurator(FileWithAtomDataConfigurator):
    """Reads information from an XYZ file for the CP2K converter.

    This class loads the contents of an XYZ file.
    This file may contain the atom positions, velocities or forces.
    In either case there will be 3 components per atom.

    If you have an ExtendedXYZ file, load it with the ASE converter instead.

    """

    def parse(self):
        self._lastline = 0
        self._header_lines = 2
        self._frame_lines = 0
        filename = self["filename"]

        self["instance"] = open(filename, encoding="utf-8")

        self["instance"].seek(0, 0)  # go to the beginning of file

        try:
            self["n_atoms"] = int(self["instance"].readline().strip())
        except ValueError:
            raise XYZFileError(f"Could not read the number of atoms in {filename} file")

        self._nAtomsLineSize = self["instance"].tell()
        self["instance"].readline()
        self._headerSize = self["instance"].tell()
        self["atoms"] = []
        for _ in range(self["n_atoms"]):
            line = self["instance"].readline()
            atom = line.split()[0].strip()
            self["atoms"].append(atom)
            self._frame_lines += 1

        # The frame size define the total size of a frame (number of atoms header + time info line + coordinates block)
        self._frameSize = self["instance"].tell()
        self._coordinatesSize = self._frameSize - self._headerSize

        # Compute the frame number
        self["instance"].seek(0, 2)  # go to the end of file
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
            raise XYZFileError(
                "Could not cast the timestep to a floating point number."
            )
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
        starting_line = (
            step * (self._frame_lines + self._header_lines) + self._header_lines
        )
        lines_to_skip = starting_line - self._lastline
        if lines_to_skip < 0:
            self["instance"].seek(0)
            lines_to_skip = starting_line
        for _ in range(lines_to_skip):
            next(self["instance"])
            self._lastline += 1

        templines = []
        for _ in range(self._frame_lines):
            templines.append(
                [float(x) for x in self["instance"].readline().split()[1:]]
            )
            self._lastline += 1

        config = np.array(templines, dtype=np.float64)

        return config

    def close(self):
        """Closes the file that was, until now, open for reading."""
        self["instance"].close()

    def atom_labels(self) -> Iterable[AtomLabel]:
        """
        Yields
        ------
        AtomLabel
            An atom label.
        """
        for atm_label in self["atoms"]:
            yield AtomLabel(atm_label)
