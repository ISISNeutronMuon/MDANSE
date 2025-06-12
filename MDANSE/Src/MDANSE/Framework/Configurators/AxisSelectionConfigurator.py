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


from MDANSE.Framework.Configurators.MoleculeSelectionConfigurator import (
    MoleculeSelectionConfigurator,
)
from MDANSE.MolecularDynamics.TrajectoryUtils import find_atoms_in_molecule


class AxisSelectionConfigurator(MoleculeSelectionConfigurator):
    """
    This configurator allows to define a local axis per molecule.

    For each molecule, the axis is defined using the coordinates of two atoms of the molecule.

    :note: this configurator depends on 'trajectory' configurator to be configured.
    """

    _default = (None, 0)

    def configure(self, value):
        self._original_input = value

        self.use_MOI_axes = True
        self.use_COM_reference = True
        self["index1"] = None
        self["index2"] = None
        molecule_name = value[0]
        super().configure(molecule_name)
        if len(value) == 3:
            self["index1"] = int(value[1])
            self["index2"] = int(value[2])
        elif len(value) == 2:
            self["index1"] = int(value[1])
        elif len(value) > 3:
            raise ValueError(f"Too many items in input: {value}")
