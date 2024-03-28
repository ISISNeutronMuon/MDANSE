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

from qtpy import QtWidgets


class Viewer1DDialog(QtWidgets.QDalog):
    def __init__(self, plot_1d_model, *args, **kwargs):
        super(Viewer1DDialog, self).__init__(*args, **kwargs)

        self._plot_1d_model = plot_1d_model

        self._build()

    def _build(self):
        main_layout = QtWidgets.QVBoxLayout()

        self._data_table_view = QtWidgets.QTableView()

        self.setLayout(main_layout)
