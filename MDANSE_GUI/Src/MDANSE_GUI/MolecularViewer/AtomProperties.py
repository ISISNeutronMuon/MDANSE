#    This file is part of MDANSE_GUI.
#
#    MDANSE_GUI is free software: you can redistribute it and/or modify
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

import numpy as np
import vtk
from qtpy.QtCore import QObject, Qt, Signal, Slot
from qtpy.QtGui import QColor, QStandardItem, QStandardItemModel
from vtk.util.numpy_support import numpy_to_vtk

from MDANSE.MolecularDynamics.Trajectory import Trajectory

RGB_COLOURS = []
RGB_COLOURS.append((1.00, 0.20, 1.00))  # selection
RGB_COLOURS.append((1.00, 0.90, 0.90))  # background


def ndarray_to_vtkarray(colors, scales, indices):
    """Convert the colors and scales NumPy arrays to vtk arrays.

    Args:
        colors (numpy.array): the colors
        scales (numpy.array): the scales
        n_atoms (int): the number of atoms
    """
    # define the colours
    color_scalars = numpy_to_vtk(colors)
    color_scalars.SetName("colors")

    # some scales
    scales_scalars = numpy_to_vtk(scales)
    scales_scalars.SetName("scales")

    # the original index
    index_scalars = numpy_to_vtk(indices)
    index_scalars.SetName("index")

    scalars = vtk.vtkFloatArray()
    scalars.SetNumberOfComponents(3)
    scalars.SetNumberOfTuples(scales_scalars.GetNumberOfTuples())
    scalars.CopyComponent(0, scales_scalars, 0)
    scalars.CopyComponent(1, color_scalars, 0)
    scalars.CopyComponent(2, index_scalars, 0)
    scalars.SetName("scalars")
    return scalars


class AtomEntry(QObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._index = None
        self._indices = []
        self._items = []

    def set_values(
        self, name: str, indices: list[int], colour: QColor, size: float
    ) -> list[QStandardItem]:
        self._indices = indices
        name_item = QStandardItem(str(name))
        name_item.setEditable(False)
        colour_item = QStandardItem(str(colour))
        colour_item.setData(QColor(colour), role=Qt.ItemDataRole.BackgroundRole)
        size_item = QStandardItem(str(size))
        self._items = [name_item, colour_item, size_item]
        return self._items

    def colour(self) -> QColor:
        return QColor(self._items[1].text())

    def size(self) -> float:
        return float(self._items[2].text())

    def indices(self) -> list[int]:
        return self._indices


class AtomProperties(QStandardItemModel):
    new_atom_properties = Signal(object)

    def __init__(self, *args, init_colours: list | None = None, **kwargs):
        super().__init__(*args, **kwargs)

        self._lut = vtk.vtkColorTransferFunction()
        self._colour_list = init_colours if init_colours is not None else RGB_COLOURS

        self.rebuild_colours()
        self.setHorizontalHeaderLabels(["Element", "Colour", "Radius"])
        self.itemChanged.connect(self.onNewValues)
        self._groups = []
        self._total_length = 0
        self.colours = np.array([], dtype=int)
        self.radii = np.array([], dtype=float)

    def clear_table(self):
        """This was meant to be used for cleaning up,
        but the underlying VTK object seems to survive.
        The unit test shows 5 colours in the list when there
        should be 2.
        """
        self._lut.RemoveAllPoints()

    def rebuild_colours(self):
        """Puts the colours from the internal _colour_list
        into the VTK vtkColorTransferFunction object.
        The colours stored internally in self_.colour_list
        should be the same as the colours in self._lut
        AFTER this method has been called.
        """
        self._lut.RemoveAllPoints()

        for index, colour in enumerate(self._colour_list):
            self._lut.AddRGBPoint(index, colour[0], colour[1], colour[2])

    def add_colour(self, rgb: tuple[int, int, int]) -> int:
        """Puts the colour into the list and returns the
        index of the colour in the list, to be used by VTK.

        Arguments:
            rgb -- RGB colour values for the colour

        Returns:
            int - the index of the colour in the list
        """
        float_rgb = tuple([x / 255.0 for x in rgb])
        for index, value in enumerate(self._colour_list):
            if value == float_rgb:
                return index
        new_index = len(self._colour_list)
        self._colour_list.append(float_rgb)
        self.rebuild_colours()
        return new_index

    def reinitialise_from_database(
        self,
        atoms: list[str],
        element_database: Trajectory,
        dummy_size: float | None = None,
    ) -> list[int]:
        """Puts colours into the list based on chemical elements list
        and a database with colour values.

        Parameters
        ----------
        atoms : list[str]
            list[str] of chemical element names
        element_database : AtomsDatabase
            a dictionary containing RGB values for chemical elements,
            typically the MDANSE_GUI.MolecularViewer.database.CHEMICAL_ELEMENTS
        dummy_size : float or None
            Override the size of the dummy atoms.

        Returns
        -------
        list[int]
            A list of indices of colours, with one numbed per atom.
        """
        self.removeRows(0, self.rowCount())
        self._groups = []
        self._total_length = 0

        all_atoms = np.array(atoms)
        unique_atoms = np.unique(all_atoms)
        indices = np.arange(len(all_atoms))
        groups = {}
        for unique in unique_atoms:
            groups[unique] = indices[np.where(all_atoms == unique)]
        colour_index_list = []
        for atom in unique_atoms:
            if (
                element_database.get_atom_property(atom, "element") == "dummy"
                and dummy_size is not None
            ):
                size = dummy_size
            else:
                size = round(element_database.get_atom_property(atom, "vdw_radius"), 2)
            atom_entry = AtomEntry()
            rgb = [
                int(x)
                for x in element_database.get_atom_property(atom, "color").split(";")
            ]
            colour_index_list.append(self.add_colour(rgb))
            item_row = atom_entry.set_values(
                atom,
                groups[atom],
                QColor(rgb[0], rgb[1], rgb[2]).name(QColor.NameFormat.HexRgb),
                size,
            )
            self.appendRow(item_row)
            self._groups.append(atom_entry)
        self._total_length = len(all_atoms)
        return colour_index_list

    @Slot()
    def onNewValues(self):
        self.rebuild_colours()
        colours = np.empty(self._total_length, dtype=int)
        radii = np.empty(self._total_length, dtype=float)
        numbers = np.arange(self._total_length)
        for entry in self._groups:
            colour = entry.colour()
            red, green, blue = colour.red(), colour.green(), colour.blue()
            vtk_colour = self.add_colour((red, green, blue))
            radius = entry.size()
            indices = entry.indices()
            radii[indices] = radius
            colours[indices] = vtk_colour
        self.radii = radii
        self.colours = colours
        self.new_atom_properties.emit((colours, radii, numbers))
