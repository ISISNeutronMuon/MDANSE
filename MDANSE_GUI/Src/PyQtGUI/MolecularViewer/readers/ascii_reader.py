import abc

from waterstay.readers.i_reader import IReader
from waterstay.database import CHEMICAL_ELEMENTS, STANDARD_RESIDUES


class ASCIIReader(IReader):
    """This class implements an interface for trajectory readers based on ASCII trajectory file."""

    def __init__(self, filename):
        """Constructor.

        Args:
            filename (str): the trajectory filename
        """

        super(ASCIIReader, self).__init__(filename)

        self._fin = open(self._filename, "r")

    def __del__(self):
        """Called when the object is destructed."""

        # Close the opened file
        self._fin.close()

    @abc.abstractmethod
    def parse_first_frame(self):
        """Parse the first frame to define the topology of the system."""
