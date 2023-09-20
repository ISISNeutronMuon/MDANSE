# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/pygenplot/__init__.py
# @brief     root file of pygenplot
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2023-now
# @authors   Eric Pellegrini
#
# **************************************************************************

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
