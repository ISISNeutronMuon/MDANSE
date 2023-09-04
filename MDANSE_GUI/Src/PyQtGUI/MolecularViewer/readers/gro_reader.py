import logging
import re
import sys

import numpy as np

from waterstay.readers.ascii_reader import ASCIIReader
from waterstay.readers.i_reader import InvalidFileError
from waterstay.readers.reader_registry import register_reader


@register_reader(".gro")
class GroReader(ASCIIReader):
    def __init__(self, filename):
        super(GroReader, self).__init__(filename)

        # Read the title line and store its length
        first_title = self._fin.readline()

        # Read the number of atoms. Must be an integer.
        try:
            n_atoms = self._fin.readline()
            self._n_atoms_size = len(n_atoms)
            self._n_atoms = int(n_atoms)
        except ValueError:
            print("Invalid type for number of atoms: must be an int")
            sys.exit(1)

        self._fin.seek(0)

        # Loop over the file to get the length of all title lines (:-( they change over the file)
        # Compute also the number of frames
        self._times = []
        self._pbc_starts = []
        self._frame_starts = []
        self._n_frames = 0
        eof = False
        while True:
            for i in range(self._n_atoms + 3):
                line = self._fin.readline()
                if not line:
                    eof = True
                    break
                if i == 0:
                    match = re.search(".* t= (.*) step=", line)
                    if match is None:
                        raise InvalidFileError("Invalid PDB file")
                    self._times.append(float(match.groups()[0]))
                elif i == 1:
                    self._frame_starts.append(self._fin.tell())
                elif i == self._n_atoms + 1:
                    self._pbc_starts.append(self._fin.tell())
            if eof:
                break

            self._n_frames += 1

        self._fin.seek(self._frame_starts[0])

        self._coords_size = 45

        self._frame_size = self._n_atoms * self._coords_size

        self.parse_first_frame()

        logging.info("Read {} successfully".format(filename))

    def parse_first_frame(self):
        """Parse the first frame to get resp. the residue ids and names and the atoms ids and names."""

        # Rewind the file to the beginning of the first frame
        self._fin.seek(self._frame_starts[0])
        data = self._fin.read(self._frame_size)

        self._atom_names = []
        self._atom_ids = []
        self._atom_types = []
        self._residue_names = []
        self._residue_ids = []

        for i in range(self._n_atoms):
            start = i * self._coords_size
            end = start + self._coords_size
            line = data[start:end]
            self._residue_ids.append(int(line[0:5]))
            self._residue_names.append(line[5:10].strip())
            self._atom_names.append(line[10:15].strip())
            self._atom_ids.append(int(line[15:20]))

        self.guess_atom_types()

    def read_frame(self, frame):
        """Read the coordinates at a given frame.

        Args:
            frame (int): the selected frame
        """

        # Fold the frame
        frame %= self._n_frames

        # Rewind the file to the beginning of the frame
        self._fin.seek(self._frame_starts[frame])

        data = self._fin.read(self._frame_size)

        coords = np.empty((self._n_atoms, 3), dtype=np.float)

        for i in range(self._n_atoms):
            start = i * self._coords_size
            end = start + self._coords_size
            line = data[start:end]
            x = float(line[20:28])
            y = float(line[28:36])
            z = float(line[36:44])
            coords[i, :] = [x, y, z]

        coords *= 10.0

        return coords

    def read_pbc(self, frame):
        """Read the bounding box at a given frame.

        Args:
            frame (int): the selected frame
        """

        # Fold the frame
        frame %= self._n_frames

        pbc = np.zeros((3, 3), dtype=np.float)

        # Rewind the file to the beginning of the frame
        self._fin.seek(self._pbc_starts[frame])

        data = self._fin.readline().split()

        n_data = len(data)
        if n_data == 3:
            np.fill_diagonal(pbc, data[0:3])
        elif n_data == 9:
            np.fill_diagonal(pbc, data[0:3])
            pbc[0, 1] = data[3]
            pbc[0, 2] = data[4]
            pbc[1, 0] = data[5]
            pbc[1, 2] = data[6]
            pbc[2, 0] = data[7]
            pbc[2, 1] = data[7]
        else:
            raise ValueError("Invalid PBC line")

        pbc *= 10.0

        return pbc


if __name__ == "__main__":
    import sys

    gro_file = sys.argv[1]

    reader = GromacsReader(gro_file)

    indexes = reader.get_mol_indexes("ARG", ["2HH2"])

    print(indexes)
