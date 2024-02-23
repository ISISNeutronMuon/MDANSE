# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/InputDirectoryWidget.py
# @brief     Implements module/class/test InputDirectoryWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from qtpy.QtWidgets import QFileDialog

from MDANSE_GUI.InputWidgets.InputFileWidget import InputFileWidget


class InputDirectoryWidget(InputFileWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._file_dialog = QFileDialog.getExistingDirectory

    def configure_using_default(self):
        """This is too specific to have a default value"""
