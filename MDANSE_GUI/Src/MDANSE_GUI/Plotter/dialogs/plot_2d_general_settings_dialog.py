# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/Plotter/__init__.py
# @brief     root file of Plotter
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2023-now
# @authors   Eric Pellegrini
#
# **************************************************************************

from PyQt6 import QtWidgets


class Plot2DGeneralSettingsDialog(QtWidgets.QDialog):
    def __init__(self, plot_2d_model, parent):
        super(Plot2DGeneralSettingsDialog, self).__init__(parent)

        self._plot_2d_model = plot_2d_model

        self._build()

        self.setWindowTitle("General settings dialog")

    def _build(self):
        main_layout = QtWidgets.QVBoxLayout()

        titles_groupbox = QtWidgets.QGroupBox(self)
        titles_groupbox.setTitle("Titles")
        titles_groupbox_layout = QtWidgets.QFormLayout()
        figure_title_label = QtWidgets.QLabel("Figure")
        figure_title_lineedit = QtWidgets.QLineEdit()
        figure_title_lineedit.setText(self._plot_2d_model.get_figure_title())
        titles_groupbox_layout.addRow(figure_title_label, figure_title_lineedit)
        plot_title_label = QtWidgets.QLabel("Plot")
        plot_title_lineedit = QtWidgets.QLineEdit()
        plot_title_lineedit.setText(self._plot_2d_model.get_plot_title())
        titles_groupbox_layout.addRow(plot_title_label, plot_title_lineedit)
        titles_groupbox.setLayout(titles_groupbox_layout)
        main_layout.addWidget(titles_groupbox)

        buttons_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
            | QtWidgets.QDialogButtonBox.StandardButton.Ok
        )
        main_layout.addWidget(buttons_box)

        self.setLayout(main_layout)

        figure_title_lineedit.textEdited.connect(self.on_editing_figure_title)
        plot_title_lineedit.textEdited.connect(self.on_editing_plot_title)

        buttons_box.rejected.connect(self.reject)
        buttons_box.accepted.connect(self.accept)

    def on_editing_figure_title(self, title):
        self._plot_2d_model.set_figure_title(title)

    def on_editing_plot_title(self, title):
        self._plot_2d_model.set_plot_title(title)
