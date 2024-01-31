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

from qtpy import QtCore, QtWidgets

<<<<<<<< HEAD:MDANSE_GUI/Src/MDANSE_GUI/Plotter/dialogs/plot_1d_general_settings_dialog.py
from MDANSE_GUI.Plotter.models.plot_1d_model import Plot1DModel
========
from MDANSE_GUI.pygenplot.models.plot_1d_model import Plot1DModel
>>>>>>>> a3e31864e3d7a47375ecf27c20e78ea49e783dc8:MDANSE_GUI/Src/MDANSE_GUI/pygenplot/dialogs/plot_1d_general_settings_dialog.py


class Plot1DGeneralSettingsDialog(QtWidgets.QDialog):
    def __init__(self, plot_1d_model, parent):
        """Constructor.

        Args:
            plot_1d_model (Plotter.models.plot_1d_model.Plot1DModel): the 1D data model
        """
        super(Plot1DGeneralSettingsDialog, self).__init__(parent)

        self._plot_1d_model = plot_1d_model

        self._build()

        self.on_update()

        self.setWindowTitle("General settings dialog")

    def _build(self):
        """Build te dialog."""
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

        self._legend_groupbox = QtWidgets.QGroupBox(self)
        self._legend_groupbox.setTitle("Legend")
        self._legend_groupbox.setCheckable(True)
        legend_groupbox_layout = QtWidgets.QHBoxLayout()
        vlayout = QtWidgets.QVBoxLayout()
        hlayout = QtWidgets.QHBoxLayout()
        legend_location_label = QtWidgets.QLabel("Location")
        hlayout.addWidget(legend_location_label)
        self._legend_location_combobox = QtWidgets.QComboBox()
        hlayout.addWidget(self._legend_location_combobox)
        vlayout.addLayout(hlayout)
        vlayout.addStretch()
        legend_style_groupbox = QtWidgets.QGroupBox(self)
        legend_style_groupbox.setTitle("Styles")
        legend_style_groupbox_layout = QtWidgets.QVBoxLayout()
        self._legend_frameon_checkbox = QtWidgets.QCheckBox("Frame on")
        legend_style_groupbox_layout.addWidget(self._legend_frameon_checkbox)
        self._legend_fancybox_checkbox = QtWidgets.QCheckBox("Fancy box")
        legend_style_groupbox_layout.addWidget(self._legend_fancybox_checkbox)
        self._legend_shadow_checkbox = QtWidgets.QCheckBox("Shadow")
        legend_style_groupbox_layout.addWidget(self._legend_shadow_checkbox)
        legend_style_groupbox.setLayout(legend_style_groupbox_layout)
        legend_groupbox_layout.addLayout(vlayout)
        legend_groupbox_layout.addStretch()
        legend_groupbox_layout.addWidget(legend_style_groupbox)
        self._legend_groupbox.setLayout(legend_groupbox_layout)
        main_layout.addWidget(self._legend_groupbox)

        self._grid_groupbox = QtWidgets.QGroupBox(self)
        self._grid_groupbox.setTitle("Grid")
        self._grid_groupbox.setCheckable(True)
        grid_groupbox_layout = QtWidgets.QFormLayout()
        grid_line_style_label = QtWidgets.QLabel("Line style")
        self._grid_line_style_combobox = QtWidgets.QComboBox()
        grid_groupbox_layout.addRow(
            grid_line_style_label, self._grid_line_style_combobox
        )
        grid_width_label = QtWidgets.QLabel("Width")
        self._grid_width_doublespinbox = QtWidgets.QDoubleSpinBox()
        self._grid_width_doublespinbox.setMinimum(0)
        self._grid_width_doublespinbox.setMaximum(10)
        self._grid_width_doublespinbox.setDecimals(1)
        self._grid_width_doublespinbox.setSingleStep(0.1)
        grid_groupbox_layout.addRow(grid_width_label, self._grid_width_doublespinbox)
        grid_color_label = QtWidgets.QLabel("Color")
        self._grid_color_pushbutton = QtWidgets.QPushButton()
        grid_groupbox_layout.addRow(grid_color_label, self._grid_color_pushbutton)
        self._grid_groupbox.setLayout(grid_groupbox_layout)
        main_layout.addWidget(self._grid_groupbox)

        self.setLayout(main_layout)

        self._figure_title_lineedit.textEdited.connect(self.on_editing_figure_title)
        self._plot_title_lineedit.textEdited.connect(self.on_editing_plot_title)
        self._legend_groupbox.clicked.connect(self.on_show_legend)
        self._legend_location_combobox.activated.connect(self.on_change_legend_location)
        self._legend_fancybox_checkbox.clicked.connect(self.on_check_legend_fancybox)
        self._legend_frameon_checkbox.clicked.connect(self.on_check_legend_frameon)
        self._legend_shadow_checkbox.clicked.connect(self.on_check_legend_shadow)
        self._grid_groupbox.clicked.connect(self.on_show_grid)
        self._grid_line_style_combobox.activated.connect(self.on_change_grid_line_style)
        self._grid_width_doublespinbox.valueChanged.connect(self.on_change_grid_width)
        self._grid_color_pushbutton.clicked.connect(self.on_change_grid_color)

    def on_change_grid_color(self):
        """Callback called when the grid color is changed."""
        color = QtWidgets.QColorDialog(self).getColor()
        if not color.isValid():
            return
        rgb_255 = (color.red(), color.green(), color.blue())
        self._grid_color_pushbutton.setStyleSheet(f"background-color : rgb{rgb_255}")
        grid_color = (rgb_255[0] / 255, rgb_255[1] / 255, rgb_255[2] / 255)
        self._plot_1d_model.set_grid_color(grid_color)

    def on_change_grid_line_style(self, index):
        """Callback called when the grid line style is changed.

        Args:
            index (int): the index of the activated item
        """
        self._plot_1d_model.set_grid_line_style(
            self._grid_line_style_combobox.currentText()
        )

    def on_change_grid_width(self, width):
        """Callback called when the grid width is changed.

        Args:
            width (float): the new grid width
        """
        self._plot_1d_model.set_grid_width(width)

    def on_change_legend_location(self, index):
        """Callback called when the legend location is changed.

        Args:
            index (int): the index of the activated item
        """
        self._plot_1d_model.set_legend_location(
            self._legend_location_combobox.currentText()
        )

    def on_check_legend_fancybox(self, state):
        """Callback called when the legend fancybox checkbox toggle state is changed.

        Args:
            state (bool): the legend fancybox checkbox state
        """
        self._plot_1d_model.set_legend_fancybox(state)

    def on_check_legend_frameon(self, state):
        """Callback called when the legend frameon checkbox toggle state is changed.

        Args:
            state (bool): the legend frameon checkbox state
        """
        self._plot_1d_model.set_legend_frameon(state)

    def on_check_legend_shadow(self, state):
        """Callback called when the legend shadow checkbox toggle state is changed.

        Args:
            state (bool): the legend shadow checkbox state
        """
        self._plot_1d_model.set_legend_shadow(state)

    def on_editing_figure_title(self, title):
        """Callback called when the figure title is edited.

        Args:
            title (str): the new figure title
        """
        self._plot_1d_model.set_figure_title(title)

    def on_editing_plot_title(self, title):
        """Callback called when the plot title is edited.

        Args:
            title (str): the new plot title
        """
        self._plot_1d_model.set_plot_title(title)

    def on_show_grid(self, state):
        """Callback called wen the show grid groupbox toggle state is changed.

        Args:
            state (bool): the show grid groupbox toggle state
        """
        self._plot_1d_model.set_show_grid(state)

    def on_show_legend(self, state):
        """Callback called wen the show legend groupbox toggle state is changed.

        Args:
            state (bool): the show legend groupbox toggle state
        """
        self._plot_1d_model.set_show_legend(state)

    def on_update(self):
        """Update the widgets of the dialog."""
        self._figure_title_lineedit.setText(self._plot_1d_model.get_figure_title())

        self._plot_title_lineedit.setText(self._plot_1d_model.get_plot_title())

        self._legend_groupbox.setChecked(self._plot_1d_model.get_show_legend())

        self._legend_location_combobox.clear()
        self._legend_location_combobox.addItems(Plot1DModel.legend_locations)
        self._legend_location_combobox.setCurrentText(
            self._plot_1d_model.get_legend_location()
        )

        state = (
            QtCore.Qt.CheckState.Checked
            if self._plot_1d_model.get_legend_frameon()
            else QtCore.Qt.CheckState.Unchecked
        )
        self._legend_frameon_checkbox.setCheckState(state)

        state = (
            QtCore.Qt.CheckState.Checked
            if self._plot_1d_model.get_legend_fancybox()
            else QtCore.Qt.CheckState.Unchecked
        )
        self._legend_fancybox_checkbox.setCheckState(state)

        state = (
            QtCore.Qt.CheckState.Checked
            if self._plot_1d_model.get_legend_shadow()
            else QtCore.Qt.CheckState.Unchecked
        )
        self._legend_shadow_checkbox.setCheckState(state)

        self._grid_groupbox.setChecked(self._plot_1d_model.get_show_grid())

        self._grid_line_style_combobox.clear()
        self._grid_line_style_combobox.addItems(Plot1DModel.line_styles)
        self._grid_line_style_combobox.setCurrentText(
            self._plot_1d_model.get_grid_line_style()
        )

        self._grid_width_doublespinbox.setValue(self._plot_1d_model.get_grid_width())

        grid_color = self._plot_1d_model.get_grid_color()
        grid_color_255 = tuple([int(255 * c) for c in grid_color])
        self._grid_color_pushbutton.setStyleSheet(
            f"background-color : rgb{grid_color_255}"
        )
