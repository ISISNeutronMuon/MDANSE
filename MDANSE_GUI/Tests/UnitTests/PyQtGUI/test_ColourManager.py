
import pytest
import tempfile
from importlib import reload

import vtk
import numpy as np

from MDANSE_GUI.PyQtGUI.MolecularViewer.ColourManager import ColourManager, RGB_COLOURS
from MDANSE_GUI.PyQtGUI.MolecularViewer.database import CHEMICAL_ELEMENTS


@pytest.fixture(scope='function', params=[None, RGB_COLOURS])
def colour_manager(request):
    temp = ColourManager(init_colours = request.param)
    yield temp
    temp.clear_table()
    reload(vtk)

def test_ColourList(colour_manager: ColourManager):
    lut_size = colour_manager._lut.GetSize()
    assert(lut_size==2)  # we initialised with 2 colours
    indices = colour_manager.initialise_from_database(['O', 'C', 'Fe'], CHEMICAL_ELEMENTS)
    assert(np.all(np.array(indices) == [2,3,4]))
    lut_size = colour_manager._lut.GetSize()
    assert(lut_size==5)  # we added 3 colours, so it should be 5 now.


