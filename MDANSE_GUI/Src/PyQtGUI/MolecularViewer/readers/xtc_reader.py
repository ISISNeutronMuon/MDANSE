import logging
import os

import numpy as np

import MDAnalysis

from waterstay.readers.i_reader import InvalidFileError, IReader
from waterstay.readers.reader_registry import register_reader


@register_reader('.xtc')
class XTCReader(IReader):

    def __init__(self, filename):

        super(XTCReader, self).__init__(filename)

        basename, _ = os.path.splitext(filename)

        tpr_file = basename + '.tpr'

        if not os.path.exists(tpr_file):
            raise InvalidFileError('Could not find tpr file {}'.format(tpr_file))

        self._universe = MDAnalysis.Universe(tpr_file, self._filename)

        self._residue_ids = [at.resnum for at in self._universe.atoms]

        self._residue_names = [at.resname for at in self._universe.atoms]

        self._atom_ids = [at.id for at in self._universe.atoms]

        self._atom_names = [at.name for at in self._universe.atoms]

        self._n_atoms = self._universe.trajectory.n_atoms

        self._n_frames = self._universe.trajectory.n_frames

        self._times = [i*self._universe.trajectory.dt for i in range(self._universe.trajectory.n_frames)]

        self.guess_atom_types()

        logging.info('Read {} successfully'.format(filename))

    def read_frame(self, frame):
        """Read the coordinates at a given frame.

        Args:
            frame (int): the selected frame
        """

        return self._universe.trajectory[frame].positions.astype(np.float)

    def read_pbc(self, frame):
        """Read the bounding box at a given frame.

        Args:
            frame (int): the selected frame
        """

        return self._universe.trajectory[frame].triclinic_dimensions.astype(np.float)


if __name__ == '__main__':

    import sys

    xtc_file = sys.argv[1]

    reader = XTCReader(xtc_file)
