# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/Widgets/Generator.py
# @brief     Here we can generate some Widgets
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Research Software Group at ISIS (see AUTHORS)
#
# **************************************************************************

from qtpy.QtWidgets import QWidget, QDialog, QVBoxLayout

# THIS in NOT being USED at the moment.
# DELETE it if no other modules need it.


class InputDialog(QDialog):
    """This is the self-constructing Dialog which creates
    all the inputs defined in a Configurable.
    Typically it will be used for trajectory converters
    and analysis jobs.

    Arguments:
        QDialog -- the class inherits a standard QDialog
    """
    
    def __init__(self, parent, configurable, type, *args, **kwargs):

        super().__init__(parent, *args, **kwargs)
        
        self._configurable = configurable
        self._type = type
        
        self._widgets = {}
        layout = QVBoxLayout(self)

        self.setLayout(layout)
        
        self.build_panel()
        
    def build_panel(self):
        
        layout = self.layout()
        self._configurable.build_configuration()

        for cfgName in self._configurable.settings.keys():
            widget = self._configurable.configuration[cfgName].widget
