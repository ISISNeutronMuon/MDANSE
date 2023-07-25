
from qtpy.QtGui import QStandardItemModel, QStandardItem
from qtpy.QtWidgets import QTableView, QColorDialog

from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem
from MDANSE_GUI.PyQtGUI.MolecularViewer.MolecularViewer import MolecularViewer
from MDANSE_GUI.PyQtGUI.MolecularViewer.readers.i_reader import IReader


class TrajectoryAtomData(QStandardItemModel):

    def __init__(self, *args, **kwargs):

        super(TrajectoryAtomData, self).__init__(*args, **kwargs)

    def setViewer(self, viewer: MolecularViewer):
        self._viewer = viewer

    def setReader(self, ireader: IReader):
        self._reader = ireader


