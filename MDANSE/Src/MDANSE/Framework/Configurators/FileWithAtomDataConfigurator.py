from abc import abstractmethod

from MDANSE.Framework.AtomMapping import AtomLabel
from .InputFileConfigurator import InputFileConfigurator


class FileWithAtomDataConfigurator(InputFileConfigurator):

    def configure(self, filepath: str) -> None:
        """
        Parameters
        ----------
        filepath : str
            The file path.
        """
        super().configure(filepath)
        if self.error_status != "OK":
            return
        try:
            self.parse()
        except Exception:
            self.error_status = "File parsing error"

    @abstractmethod
    def parse(self) -> None:
        """Parse the file."""
        pass

    @abstractmethod
    def get_atom_labels(self) -> list[AtomLabel]:
        """Return the atoms labels in the file."""
        pass
