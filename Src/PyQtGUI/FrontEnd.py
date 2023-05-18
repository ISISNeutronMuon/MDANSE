# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/FrontEnd.py
# @brief     A FrontEnd connects to the BackEnd. I _may_ be a GUI.
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Research Software Group at ISIS (see AUTHORS)
#
# **************************************************************************

from collections import defaultdict

from qtpy.QtCore import Slot, Signal, QMetaObject, QLocale, QObject,\
                         QThread, QMutex, QSortFilterProxyModel,\
                         Qt
from qtpy.QtGui import QFont, QAction


# it seems that the FrontEnd has become obsolete.
# DELETE it, if nobody needs it

class FrontEnd(QObject):
    """This object will connect to a BackEnd by means
    of Qt slots and signals.
    The idea is that we can use either a GUI or a CLI,
    or even a script, to connect to a BackEnd.

    Args:
        QObject - the base class.
    """

    file_name_for_loading = Signal(str)

    def __init__(self, *args, parent = None, **kwargs):
        super().__init__(parent)
        self._views = defaultdict(list)
        self._actions = []

    def setBackend(self, backend = None):
        """Attaches a MDANSE backend to the GUI.
        This handle is stored so we can connect
        all the QActions from the GUI
        to the correct backend slots.
        """
        self.backend = backend
        self.connectViews()
        self.attachActions()
    
    @Slot()
    def connectViews(self):
        for key in self.backend.data_holders.keys():
            skey = str(key)
            data_holder = self.backend.data_holders[skey]
            for view in self._views[skey]:
                view.setModel(data_holder)
    
    def attachActions(self):
        self.file_name_for_loading.connect(self.backend.loadFile)
        # backend_actions = self.backend.getActions()
        # for act in backend_actions:
        #     a_text = act[1]
        #     a_slot = act[0]
        #     temp = QAction(a_text, parent=self)
        #     temp.triggered.connect(a_slot)
        #     self._actions.append(temp)