import logging
import re

import numpy as np

from waterstay.readers.ascii_reader import ASCIIReader
from waterstay.readers.i_reader import InvalidFileError
from waterstay.readers.reader_registry import register_reader


@register_reader('.pdb')
class PDBReader(ASCIIReader):

    def __init__(self, filename):

        super(PDBReader, self).__init__(filename)

        # Compute the number of atoms
        self._n_atoms = 0
        while True:
            line = self._fin.readline()
            if line[:3] == "TER":
                break
            self._n_atoms += 1

        # Substract the first lines of the files
        self._n_atoms -= 5

        self._fin.seek(0)

        # Loop over the file to get the length of all title lines (:-( they change over the file)
        # Compute also the number of frames
        self._times = []
        self._pbc_starts = []
        self._frame_starts = []
        self._n_frames = 0
        eof = False
        while True:
            for i in range(self._n_atoms + 7):
                line = self._fin.readline()
                if not line:
                    eof = True
                    break
                if i == 1:
                    match = re.search('.* t= (.*) step=', line)
                    if match is None:
                        raise InvalidFileError('Invalid PDB file')
                    self._times.append(float(match.groups()[0]))
                if i == 2:
                    self._pbc_starts.append(self._fin.tell())
                elif i == 4:
                    self._frame_starts.append(self._fin.tell())
            if eof:
                break

            self._n_frames += 1

        self._fin.seek(self._frame_starts[0])

        self._coords_size = 79

        self._frame_size = self._n_atoms*self._coords_size

        self.parse_first_frame()

        logging.info('Read {} successfully'.format(filename))

    def parse_first_frame(self):
        """Parse the first frame to get resp. the residue ids and names and the atoms ids and names.
        """

        # Rewind the file to the beginning of the first frame
        self._fin.seek(self._frame_starts[0])
        data = self._fin.read(self._frame_size)

        self._atom_names = []
        self._atom_ids = []
        self._atom_types = []
        self._residue_names = []
        self._residue_ids = []

        for i in range(self._n_atoms):
            start = i*self._coords_size
            end = start + self._coords_size
            line = data[start:end]
            self._atom_ids.append(int(line[6:11]))
            self._atom_names.append(line[12:16].strip())
            self._residue_names.append(line[17:20].strip())
            self._residue_ids.append(int(line[22:26]))

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
            start = i*self._coords_size
            end = start + self._coords_size
            line = data[start:end]
            x = float(line[30:38])
            y = float(line[38:46])
            z = float(line[46:54])
            coords[i, :] = [x, y, z]

        return coords

    def read_pbc(self, frame):
        """Read the bounding box at a given frame.

        Args:
            frame (int): the selected frame
        """

        # Fold the frame
        frame %= self._n_frames

        # Rewind the file to the beginning of the frame
        self._fin.seek(self._pbc_starts[frame])

        data = self._fin.readline().split()

        a, b, c, alpha, beta, gamma = [float(v) for v in data[1:7]]

        alpha = np.deg2rad(alpha)
        beta = np.deg2rad(beta)
        gamma = np.deg2rad(gamma)

        cos_alpha = np.cos(alpha)
        cos_beta = np.cos(beta)
        cos_gamma = np.cos(gamma)
        sin_gamma = np.sin(gamma)

        pbc = np.zeros((3, 3), dtype=np.float)

        fact = (cos_alpha - cos_beta*cos_gamma)/sin_gamma

        # The a vector
        pbc[0, 0] = a

        # The b vector
        pbc[1, 0] = b*cos_gamma
        pbc[1, 1] = b*sin_gamma

        # The c vector
        pbc[2, 0] = c*cos_beta
        pbc[2, 1] = c*fact
        pbc[2, 2] = c*np.sqrt(1.0 - cos_beta*cos_beta - fact*fact)

        return pbc


if __name__ == '__main__':

    import sys

    pdb_file = sys.argv[1]

    reader = PDBReader(pdb_file)

    indexes = reader.get_atom_indexes('ARG', ['2HH2'])

    print(reader.residue_ids)
