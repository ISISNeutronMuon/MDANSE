# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/pygenplot/__init__.py
# @brief     molecular viewer code from the "waterstay" project
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2023-now
# @authors   Eric Pellegrini
#
# **************************************************************************

import numpy as np
import vtk
from qtpy.QtGui import QStandardItemModel, QStandardItem, QColor
from qtpy.QtCore import Signal, Slot

RGB_COLOURS = []
RGB_COLOURS.append((1.00, 0.20, 1.00))  # selection
RGB_COLOURS.append((1.00, 0.90, 0.90))  # background


def ndarray_to_vtkarray(colors, scales, n_atoms):
    """Convert the colors and scales NumPy arrays to vtk arrays.

    Args:
        colors (numpy.array): the colors
        scales (numpy.array): the scales
        n_atoms (int): the number of atoms
    """
    # define the colours
    color_scalars = vtk.vtkFloatArray()
    color_scalars.SetNumberOfValues(len(colors))
    # print("colors")
    for i, c in enumerate(colors):
        # print(i,c)
        color_scalars.SetValue(i, c)
    color_scalars.SetName("colors")

    # some scales
    scales_scalars = vtk.vtkFloatArray()
    scales_scalars.SetNumberOfValues(len(scales))
    # print("scales")
    for i, r in enumerate(scales):
        scales_scalars.SetValue(i, r)
        # print(i,r)
    scales_scalars.SetName("scales")

    # the original index
    index_scalars = vtk.vtkIntArray()
    index_scalars.SetNumberOfValues(n_atoms)
    # print("index")
    for i in range(n_atoms):
        index_scalars.SetValue(i, i)
        # print(i,i)
    index_scalars.SetName("index")

    scalars = vtk.vtkFloatArray()
    scalars.SetNumberOfComponents(3)
    scalars.SetNumberOfTuples(scales_scalars.GetNumberOfTuples())
    scalars.CopyComponent(0, scales_scalars, 0)
    scalars.CopyComponent(1, color_scalars, 0)
    scalars.CopyComponent(2, index_scalars, 0)
    scalars.SetName("scalars")
    return scalars


class AtomProperties(QStandardItemModel):
    new_atom_properties = Signal(object)

    def __init__(self, *args, init_colours: list = None, **kwargs):
        super().__init__(*args, **kwargs)

        self._lut = vtk.vtkColorTransferFunction()
        if init_colours is None:
            self._colour_list = RGB_COLOURS
        else:
            self._colour_list = init_colours
        self.rebuild_colours()
        self.setHorizontalHeaderLabels(["Index", "Element", "Radius", "Colour"])
        self.itemChanged.connect(self.onNewValues)

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

    def initialise_from_database(
        self, atoms: list[str], element_database=None
    ) -> list[int]:
        """Puts colours into the list based on chemical elements list
        and a database with colour values.

        Arguments:
            atoms -- list[str] of chemical element names

        Keyword Arguments:
            element_database -- a dictionary containing RGB values for chemical elements,
               typically the MDANSE_GUI.PyQtGUI.MolecularViewer.database.CHEMICAL_ELEMENTS

        Returns:
            list[int] -- a list of indices of colours, with one numbed per atom.
        """
        index_list = []
        for nat, atom in enumerate(atoms):
            row = []
            rgb = [int(x) for x in element_database["atoms"][atom]["color"].split(";")]
            index_list.append(self.add_colour(rgb))
            row.append(QStandardItem(str(nat + 1)))  # atom number
            row.append(
                QStandardItem(str(element_database["atoms"][atom]["symbol"]))
            )  # chemical element name
            row.append(
                QStandardItem(
                    str(round(element_database["atoms"][atom]["atomic_radius"], 2))
                )
            )
            row.append(
                QStandardItem(
                    QColor(rgb[0], rgb[1], rgb[2]).name(QColor.NameFormat.HexRgb)
                )
            )
            self.appendRow(row)
        return index_list

    @Slot()
    def onNewValues(self):
        colours = []
        radii = []
        numbers = []
        for row in range(self.rowCount()):
            colour = QColor(self.item(row, 3).text())
            red, green, blue = colour.red(), colour.green(), colour.blue()
            colours.append(self.add_colour((red, green, blue)))
            radius = float(self.item(row, 2).text())
            radii.append(radius)
            numbers.append(int(self.item(row, 0).text()))

        scalars = ndarray_to_vtkarray(colours, radii, len(numbers))
        self.new_atom_properties.emit(scalars)
