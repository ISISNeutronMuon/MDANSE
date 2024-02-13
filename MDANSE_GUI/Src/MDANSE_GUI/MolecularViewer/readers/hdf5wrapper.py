# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/Plotter/__init__.py
# @brief     extension of the waterstay code
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2023-now
# @authors   Maciej Bartkowiak
#
# **************************************************************************

import numpy as np

from MDANSE_GUI.MolecularViewer.readers.i_reader import IReader


class HDF5Wrapper(IReader):
    def __init__(self, fname, trajectory, chemical):
        super(HDF5Wrapper, self).__init__(fname)
        self._n_atoms = chemical._number_of_atoms
        self._n_frames = len(trajectory)
        self._trajectory = trajectory
        self._chemical_system = chemical
        self._filename = fname
        self._atom_ids = [atom.index for atom in chemical.atoms]
        self._atom_types = [atom.symbol for atom in chemical.atoms]
        self._atom_names = [
            "_".join([str(x) for x in [atom.symbol, atom.index]])
            for atom in chemical.atoms
        ]

    def read_frame(self, frame: int) -> "np.array":
        coords = self._trajectory[frame]["coordinates"]
        return np.array(coords)

    def read_pbc(self, frame: int) -> "np.array":
        unit_cell = self._chemical_system.configuration.unit_cell
        return unit_cell
