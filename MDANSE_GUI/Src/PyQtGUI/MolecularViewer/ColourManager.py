
import numpy as np
import vtk

RGB_COLOURS = []
RGB_COLOURS.append((1.00, 0.20, 1.00))  # selection
RGB_COLOURS.append((1.00, 0.90, 0.90))  # background


class ColourManager():

    def __init__(self, *args, init_colours: list, **kwargs):

        self._lut = vtk.vtkColorTransferFunction()
        self._colour_list = init_colours
        self.rebuild_colours()

    def rebuild_colours(self):
        self._lut.RemoveAllPoints()

        for index, colour in enumerate(self._colour_list):
            self._lut.AddRGBPoint(index, colour[0], colour[1], colour[2])

    def add_colour(self, rgb: tuple[int,int,int]) -> int:
        float_rgb = tuple([x/255.0 for x in rgb])
        for index, value in enumerate(self._colour_list):
            if value == float_rgb:
                return index
        new_index = len(self._colour_list)
        self._colour_list.append(float_rgb)
        return new_index
    
    def initialise_from_database(self, atoms : list[str], element_database = None) -> list[int]:
        index_list = []
        for atom in atoms:
            rgb = (int(x) for x in element_database['atoms'][atom]['color'].split(';'))
            index_list.append(self.add_colour(rgb))
        return index_list

