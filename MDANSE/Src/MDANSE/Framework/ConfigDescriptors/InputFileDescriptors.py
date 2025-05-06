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
from abc import ABC, abstractmethod
from collections.abc import Iterable
from functools import cachedproperty

from ase.io import iread, read
from ase.io.trajectory import Trajectory as ASETrajectory
from MDANSE.Framework.AtomMapping import AtomLabel

from .BaseTypesDescriptor import PathConfigDesc


class InputFileDescriptor(PathConfigDesc, ABC):
    def __init__(
        self,
        **params,
    ):

        super().__init__(mode="r", directory=False, **params)

    @abstractmethod
    def __get__(self):
        super().__get__()


class InputFileWithAtomData(InputFileDescriptor):
    @abstractmethod
    def parse(self) -> None:
        """Parse the file."""

    @abstractmethod
    def atom_labels(self) -> Iterable[AtomLabel]:
        """Yields atom labels"""

    def unique_labels(self) -> list[AtomLabel]:
        """
        Returns
        -------
        list[AtomLabel]
            An ordered list of atom labels.
        """
        return list(set(self.atom_labels()))


class ASEFileDesc(InputFileWithAtomData):
    @property
    def first_frame(self):
        if isinstance(self.parsed, ASETrajectory):
            return self.parsed[0]
        return read(self.value, index=0)

    @property
    def element_list(self):
        return self.first_frame.get_chemical_symbols()

    @cachedproperty
    def parsed(self, owner, objtype=None):
        try:
            input = ASETrajectory(self.value)
        except Exception:
            input = iread(self.value, index="[:]")
        return input

    def atom_labels(self) -> Iterable[AtomLabel]:
        """
        Yields
        ------
        AtomLabel
            An atom label.
        """
        for atm_label in self.element_list:
            yield AtomLabel(atm_label)
