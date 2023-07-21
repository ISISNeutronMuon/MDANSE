
from MDANSE_GUI.PyQtGUI.MolecularViewer.readers.i_reader import IReader


class HDF5Wrapper(IReader):

    def __init__(self, trajectory, chemical):
        self.n_atoms = chemical._number_of_atoms
        self.n_frames = len(trajectory)
        self.atom_types = chemical.atoms
