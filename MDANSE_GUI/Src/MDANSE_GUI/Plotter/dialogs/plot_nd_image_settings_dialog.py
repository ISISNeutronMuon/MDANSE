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

from MDANSE_GUI.Plotter.models.plot_nd_model import PlotNDModel


class PlotNDImageSettingsDialog(QtWidgets.QDialog):
    def __init__(self, plot_nd_model, parent):
        """Constructor.

        Args:
            plot_nd_model (Plotter.models.plot_nd_model.PlotNDmodel): the ND data model
            parent (qtpy.QtCore.QObject): the parent
        """
        super(PlotNDImageSettingsDialog, self).__init__(parent)

        self._plot_nd_model = plot_nd_model

        self._build()

        self.on_update()

        self.setWindowTitle("Image settings dialog")

    def _build(self):
        """Build the dialog."""
        main_layout = QtWidgets.QVBoxLayout()

        vlayout = QtWidgets.QVBoxLayout()
        image_groupbox = QtWidgets.QGroupBox("Image")
        image_layout = QtWidgets.QFormLayout()
        aspect_label = QtWidgets.QLabel("Aspect")
        self._aspect_combobox = QtWidgets.QComboBox()
        image_layout.addRow(aspect_label, self._aspect_combobox)
        interpolation_label = QtWidgets.QLabel("Interpolation")
        self._interpolation_combobox = QtWidgets.QComboBox()
        image_layout.addRow(interpolation_label, self._interpolation_combobox)
        cmap_label = QtWidgets.QLabel("Color map")
        self._cmap_combobox = QtWidgets.QComboBox()
        image_layout.addRow(cmap_label, self._cmap_combobox)
        show_colorbar_label = QtWidgets.QLabel("Add colorbar")
        self._show_colorbar_checkbox = QtWidgets.QCheckBox("")
        image_layout.addRow(show_colorbar_label, self._show_colorbar_checkbox)
        image_groupbox.setLayout(image_layout)
        vlayout.addWidget(image_groupbox)

        main_layout.addLayout(vlayout)

        self.setLayout(main_layout)

        self._aspect_combobox.activated.connect(self.on_change_aspect)
        self._interpolation_combobox.activated.connect(self.on_change_interpolation)
        self._cmap_combobox.activated.connect(self.on_change_cmap)

        self._show_colorbar_checkbox.stateChanged.connect(self.on_show_colorbar)

    def on_change_aspect(self, index):
        """Callback called whe the image aspect combobox value is changed.

        Args:
            index (int): the index of the selected image aspect item
        """
        self._plot_nd_model.set_aspect(self._aspect_combobox.currentText())

    def on_change_cmap(self, index):
        """Callback called whe the image colormap combobox value is changed.

        Args:
            index (int): the index of the selected image colormap item
        """
        self._plot_nd_model.set_cmap(self._cmap_combobox.currentText())

    def on_change_interpolation(self, index):
        """Callback called whe the image interpolation combobox value is changed.

        Args:
            index (int): the index of the selected image interpolation item
        """
        self._plot_nd_model.set_interpolation(
            self._interpolation_combobox.currentText()
        )

    def on_show_colorbar(self, state):
        """Callback called when the show colorbar checkbox toggle state is changed.

        Args:
            state (bool): the show colorbar checkbox toggle state
        """
        self._plot_nd_model.set_show_colorbar(state)

    def on_update(self):
        """Update the widgets of the dialog."""
        self._aspect_combobox.clear()
        self._aspect_combobox.addItems(PlotNDModel.aspects)
        self._aspect_combobox.setCurrentText(self._plot_nd_model.get_aspect())

        self._interpolation_combobox.clear()
        self._interpolation_combobox.addItems(PlotNDModel.interpolations)
        self._interpolation_combobox.setCurrentText(
            self._plot_nd_model.get_interpolation()
        )

        self._cmap_combobox.clear()
        self._cmap_combobox.addItems(PlotNDModel.cmaps)
        self._cmap_combobox.setCurrentText(self._plot_nd_model.get_cmap())

        self._show_colorbar_checkbox.setChecked(self._plot_nd_model.get_show_colorbar())
