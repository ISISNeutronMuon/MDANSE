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

from MDANSE.Framework.Configurators.MoleculeSelectionConfigurator import (
    MoleculeSelectionConfigurator,
)
from MDANSE.MolecularDynamics.TrajectoryUtils import find_atoms_in_molecule


class AxisSelectionConfigurator(MoleculeSelectionConfigurator):
    """Defines a local axis in a molecule.

    The input is the name of a molecule type, and one or two indices
    of atoms within the molecule.

    If the atom indices are not defined, the calculation will use
    the principal axis of the molecule determined from the moment
    of inertia.

    If one index is given, the molecule axis will be a vector from
    the molecule centre to the atom with the given index.

    If two indices are given, the molecule axis will be a vector
    between the atoms with the two indices.
    """

    _default = (None, 0)

    def configure(self, value: tuple[str, str | None, str | None]):
        """Set the molecule name, and the optional atom indices.

        Parameters
        ----------
        value : tuple[str, str  |  None, str  |  None]
            Molecule name, first atom index or None, second atom index or None.

        Raises
        ------
        ValueError
            If too many values were included in the input tuple.

        """
        if not self.update_needed(value):
            return

        self._original_input = value
        self["index1"] = None
        self["index2"] = None
        molecule_name = value[0]
        self["details"] = (
            f"Axis in molecule {molecule_name} determined from moment of inertia"
        )
        super().configure(molecule_name)
        try:
            val1 = int(value[1])
        except (TypeError, ValueError, IndexError):
            val1 = None
            val2 = None
        else:
            try:
                val2 = int(value[2])
            except (TypeError, ValueError, IndexError):
                val2 = None
                self["details"] = (
                    f"Axis in molecule {molecule_name} from atom {val1!s} to the centre of mass"
                )
            else:
                self["details"] = (
                    f"Axis in molecule {molecule_name} from atom {val1!s} to {val2!s}"
                )
        if len(value) == 3:
            self["index1"] = val1
            self["index2"] = val2
        elif len(value) == 2:
            self["index1"] = val1
        elif len(value) > 3:
            raise ValueError(f"Too many items in input: {value}")
