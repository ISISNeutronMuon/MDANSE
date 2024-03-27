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
# Copyright (C)  Institut Laue Langevin 2023-now
# Authors:    Maciej Bartkowiak

import numpy as np
import vtk

RGB_COLOURS = []
RGB_COLOURS.append((1.00, 0.20, 1.00))  # selection
RGB_COLOURS.append((1.00, 0.90, 0.90))  # background


class ColourManager:
    def __init__(self, *args, init_colours: list = None, **kwargs):
        self._lut = vtk.vtkColorTransferFunction()
        if init_colours is None:
            self._colour_list = RGB_COLOURS
        else:
            self._colour_list = init_colours
        self.rebuild_colours()

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
               typically the MDANSE_GUI.MolecularViewer.database.CHEMICAL_ELEMENTS

        Returns:
            list[int] -- a list of indices of colours, with one numbed per atom.
        """
        index_list = []
        for atom in atoms:
            rgb = (int(x) for x in element_database["atoms"][atom]["color"].split(";"))
            index_list.append(self.add_colour(rgb))
        return index_list
