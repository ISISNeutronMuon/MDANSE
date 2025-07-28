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

from qtpy.QtWidgets import QFileDialog

from MDANSE_GUI.InputWidgets.InputFileWidget import InputFileWidget


class OutputDirectoryWidget(InputFileWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._file_dialog = QFileDialog.getExistingDirectory

    def configure_using_default(self):
        """This is too specific to have a default value"""
