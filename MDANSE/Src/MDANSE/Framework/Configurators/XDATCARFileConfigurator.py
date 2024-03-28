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
import numpy as np

from MDANSE.Core.Error import Error
from MDANSE.Framework.Units import measure
from MDANSE.Framework.AtomMapping import AtomLabel
from .FileWithAtomDataConfigurator import FileWithAtomDataConfigurator


class XDATCARFileError(Error):
    pass


class XDATCARFileConfigurator(FileWithAtomDataConfigurator):

    def parse(self):
        filename = self["filename"]
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

    def get_atom_labels(self) -> list[AtomLabel]:
        """
        Returns
        -------
        list[AtomLabel]
            An ordered list of atom labels.
        """
        labels = []
        for symbol, _ in self["atoms"]:
            label = AtomLabel(symbol)
            if label not in labels:
                labels.append(label)
        return labels
