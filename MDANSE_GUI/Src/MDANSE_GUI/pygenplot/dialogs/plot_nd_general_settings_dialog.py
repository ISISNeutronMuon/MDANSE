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

from qtpy import QtWidgets


class PlotNDGeneralSettingsDialog(QtWidgets.QDialog):
    def __init__(self, plot_nd_model, parent):
        """Constructor.

        Args:
            plot_nd_model (Plotter.models.plot_nd_model.PlotNDmodel): the ND data model
            parent (qtpy.QtCore.QObject): the parent
        """
        super(PlotNDGeneralSettingsDialog, self).__init__(parent)

        self._plot_nd_model = plot_nd_model

        self._build()

        self.on_update()

        self.setWindowTitle("General settings dialog")

    def _build(self):
        """Build the dialog."""
        main_layout = QtWidgets.QVBoxLayout()

        titles_groupbox = QtWidgets.QGroupBox(self)
        titles_groupbox.setTitle("Titles")
        titles_groupbox_layout = QtWidgets.QFormLayout()
        figure_title_label = QtWidgets.QLabel("Figure")
        self._figure_title_lineedit = QtWidgets.QLineEdit()
        titles_groupbox_layout.addRow(figure_title_label, self._figure_title_lineedit)
        plot_title_label = QtWidgets.QLabel("Plot")
        self._plot_title_lineedit = QtWidgets.QLineEdit()
        titles_groupbox_layout.addRow(plot_title_label, self._plot_title_lineedit)
        titles_groupbox.setLayout(titles_groupbox_layout)
        main_layout.addWidget(titles_groupbox)

        self.setLayout(main_layout)

        self._figure_title_lineedit.textEdited.connect(self.on_editing_figure_title)
        self._plot_title_lineedit.textEdited.connect(self.on_editing_plot_title)

    def on_editing_figure_title(self, title):
        """Callback called when the figure title is edited.

        Args:
            title (str): the new figure title
        """
        self._plot_nd_model.set_figure_title(title)

    def on_editing_plot_title(self, title):
        """Callback called when the plot title is edited.

        Args:
            title (str): the new plot title
        """
        self._plot_nd_model.set_plot_title(title)

    def on_update(self):
        """Updates the widgets of the dialog."""
        self._figure_title_lineedit.setText(self._plot_nd_model.get_figure_title())
        self._plot_title_lineedit.setText(self._plot_nd_model.get_plot_title())
