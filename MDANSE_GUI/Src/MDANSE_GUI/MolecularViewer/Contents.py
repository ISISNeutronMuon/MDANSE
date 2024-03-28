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

import numpy as np
from qtpy.QtGui import QStandardItemModel, QStandardItem
from qtpy.QtWidgets import QTableView, QColorDialog

from MDANSE_GUI.MolecularViewer.readers.i_reader import IReader


class TrajectoryAtomData(QStandardItemModel):
    """This object will store the information about the atoms
    present in the trajectory, allowing the user to customise
    the way the trajectory is visualised.
    It is a subclass of QStandardItemModel, allowing the information
    to be used with a QTableView widget.
    """

    def __init__(self, *args, **kwargs):
        super(TrajectoryAtomData, self).__init__(*args, **kwargs)
        self._viewer = None
        self._reader = None

    def setViewer(self, viewer):
        """Associates the data model with an instance of the
        viewer widget, so new settings can be passed to the
        visualiser.

        Arguments:
            viewer -- an instance of the MolecularViewer widget
        """
        self._viewer = viewer
        self.itemChanged.connect(self._viewer._new_atom_parameters)

    def setReader(self, ireader: IReader):
        """Assigns an instance of IReader to the data model,
        so that information about the atoms can be extracted
        from the reader.

        Arguments:
            ireader -- a trajectory reader for the MolecularViewer.
        """
        self._reader = ireader

    def parseInformation(self, unique=True):
        if self._reader is None or self._viewer is None:
            return
        atom_names = self._reader.atom_names
        atom_types = self._reader.atom_types
        atom_ids = self._reader.atom_ids
        grouped_by_type = {}
        name_by_type = {}
        colour_by_type = {}
        radius_by_type = {}
        unique_types = np.unique(atom_types)
        for type in unique_types:
            crit = np.where(atom_types == type)
            grouped_by_type[type] = atom_ids[crit]
            name_by_type[type] = atom_names[crit][0]
