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

from qtpy.QtCore import QObject, Qt, Signal, Slot
from qtpy.QtGui import QBrush, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import (
    QAbstractScrollArea,
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTableView,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from MDANSE.Framework.Configurators.QVectorsConfigurator import QVectorsConfigurator
from MDANSE.Framework.QVectors.IQVectors import IQVectors
from MDANSE.MLogging import LOG
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext
from MDANSE_GUI.Tabs.Views.PlotDataView import (
    vector_angular_datasets,
    vector_projection_datasets,
    vector_q_statistics_datasets,
)
from MDANSE_GUI.Tabs.Visualisers.PlotWidget import PlotWidget
from MDANSE_GUI.Utils import block_signals


def numerator_suffix(index: int) -> str:
    last_digit = int(str(index)[-1])
    match last_digit:
        case 1:
            return "st"
        case 2:
            return "nd"
        case 3:
            return "rd"
        case _:
            return "th"


class VectorModel(QStandardItemModel):
    type_changed = Signal()
    unit_cell_missing = Signal()
    input_is_valid = Signal(bool)

    def __init__(self, *args, trajectory=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._generator = None
        self._defaults = []
        self._trajectory = trajectory

    @Slot(str)
    def switch_qvector_type(
        self, vector_type: str, optional_settings: dict | None = None
    ):
        self.clear()
        self._defaults = []
        self._generator = IQVectors.create(vector_type, self._trajectory.unit_cell(0))
        settings = self._generator.settings
        for kv in settings.items():
            name = kv[0]  # dictionary key
            if optional_settings is None:
                value = kv[1][1]["default"]  # tuple value 1: dictionary
            else:
                try:
                    value = optional_settings[name]
                except KeyError:
                    value = kv[1][1]["default"]  # tuple value 1: dictionary
            self._defaults.append(value)
            vtype = kv[1][0]  # tuple value 0: type
            items = [QStandardItem(str(x)) for x in [name, value, vtype]]
            for it in items[0::2]:
                it.setEditable(False)
            for it in items[1::2]:
                it.setData(value, role=Qt.ItemDataRole.ToolTipRole)
            self.appendRow(items)
        self.type_changed.emit()

    def params_summary(self) -> dict:
        params = {}
        all_inputs_are_valid = True
        for rownum in range(self.rowCount()):
            name = str(self.item(rownum, 0).text())
            value = str(self.item(rownum, 1).text())
            vtype = str(self.item(rownum, 2).text())
            try:
                params[name] = self.parse_vtype(vtype, value, name)
            except ValueError:
                params[name] = "failed"
            if params[name] == "failed":
                self.item(rownum, 1).setData(
                    QBrush(Qt.GlobalColor.red), role=Qt.ItemDataRole.BackgroundRole
                )
                all_inputs_are_valid = False
            else:
                self.item(rownum, 1).setData(0, role=Qt.ItemDataRole.BackgroundRole)
        self.input_is_valid.emit(all_inputs_are_valid)
        return params

    def parse_vtype(self, vtype: str, value: str, vname: str):
        if vtype in ("RangeConfigurator", "VectorConfigurator"):
            inner_type = self._generator.settings[vname][1]["valueType"]
            tempstring = value.strip("()[] ")
            result = [inner_type(x) for x in tempstring.split(",")]
            if len(result) == 3:
                return result
        elif vtype == "FloatConfigurator":
            return float(value)
        elif vtype == "IntegerConfigurator":
            return int(value)
        else:
            return value

        return "failed"


class ShellPanel(QWidget):
    """GUI element for plotting the vectors in a single shell.

    It stores a reference to the vector generator and uses a spinbox
    to select different shells in the generator.
    """

    def __init__(
        self,
        *args,
        qvec_configurator: QVectorsConfigurator | None = None,
        plotter_type="Vectors3D",
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.qvec_config = qvec_configurator
        self.plotter_type = plotter_type
        self.create_layout()
        self.set_shell(0)

    def create_layout(self):
        layout = QGridLayout()
        self.setLayout(layout)
        box_label = QLabel("Vector shell: ", self)
        self.shell_selector = QSpinBox(self)
        self.shell_selector.setValue(0)
        self.shell_selector.valueChanged.connect(self.set_shell)
        self.shell_information = QLabel("th shell, |q| = N/A")
        self.plot_widget = PlotWidget(self, plotter_type=self.plotter_type)
        self.plot_widget.plot_selector.setVisible(False)
        self.plot_widget._normaliser.setVisible(False)
        self.plot_widget._sliderpack.setVisible(False)
        layout.addWidget(box_label, 0, 0)
        layout.addWidget(self.shell_selector, 0, 1)
        layout.addWidget(self.shell_information, 0, 2)
        layout.addWidget(self.plot_widget, 1, 0, 2, 3)

    def update_label(self, shell_index: int):
        vec_dict = self.qvec_config["q_vectors"]
        vec_keys = list(vec_dict.keys())
        self.shell_information.setText(
            f"{numerator_suffix(shell_index)} shell, |q| = {vec_keys[shell_index]}"
        )

    @Slot(int)
    def set_upper_limit(self, number_of_shells: int):
        current_shell = self.shell_selector.value()
        self.shell_selector.setMaximum(number_of_shells - 1)
        if current_shell >= number_of_shells:
            current_shell = number_of_shells - 1
        with block_signals(self.shell_selector):
            self.shell_selector.setValue(current_shell)
        self.set_shell(current_shell, update_limit=False)

    @Slot(int)
    def set_shell(self, shell_index: int, update_limit: bool = True):
        vec_dict = self.qvec_config["q_vectors"]
        if update_limit:
            self.set_upper_limit(len(vec_dict))
        try:
            vec_key = list(vec_dict.keys())[shell_index]
        except KeyError:
            LOG.warning(
                "Shell %i was not available in the Q vector generator", shell_index
            )
            self.plot_widget.plot_blank()
            return
        else:
            if vec_dict[vec_key] is None:
                LOG.warning("Shell %i does not contain any vectors", shell_index)
                self.plot_widget.plot_blank()
                return
        self.update_label(shell_index)
        new_model = PlottingContext()
        for dataset in vector_projection_datasets(self.qvec_config, vec_key):
            new_model.add_dataset(dataset)
        for dataset in vector_angular_datasets(self.qvec_config, vec_key):
            new_model.add_dataset(dataset)
        self.plot_widget.set_plotter(self.plotter_type)
        self.plot_widget.set_context(new_model)
        self.plot_widget.use_grid()
        self.plot_widget.use_legend()
        self.plot_widget.plot_data()
        new_model.needs_an_update.connect(self.update_plot)

    @Slot()
    def update_plot(self):
        self.set_shell(self.shell_selector.value())


class VectorViewer(QDialog):
    """A pop-up dialog for plotting vector distribution previews.

    Attributes
    ----------
    _helper_title : str
        The title of the helper dialog window.

    """

    _helper_title = "Q Vector Viewer"

    def __init__(
        self,
        parent: QObject,
        *args,
        configurator: QVectorsConfigurator | None = None,
        **kwargs,
    ):
        """Create the selection dialog.

        Parameters
        ----------
        parent : QObject
            parent object in the Qt object hierarchy
        *args : Any, ...
            catches all the arguments that may be passed to the QDialog constructor
        **kwargs : dict[str, Any]
            catches all the keyword arguments passed to the QDialog constructor

        """
        super().__init__(parent, *args, **kwargs)
        self.setWindowTitle(self._helper_title)
        self.setWindowFlags(Qt.Window)
        layout = QVBoxLayout()
        self.main_widget = QTabWidget(self)
        layout.addWidget(self.main_widget)
        self.setLayout(layout)
        self.plot_widget = PlotWidget(self, plotter_type="Vectors")
        self.plot_widget.plot_selector.setVisible(False)
        self.plot_widget._normaliser.setVisible(False)
        self.plot_widget._sliderpack.setVisible(False)
        self.main_widget.addTab(self.plot_widget, "Vector |q| statistics")
        self.shell_panel_3D = ShellPanel(
            qvec_configurator=configurator,
            plotter_type="Vectors3D",
        )
        self.main_widget.addTab(self.shell_panel_3D, "Vector angle statistics")

    @Slot()
    def update_plot(self):
        self.plot_widget.plot_data(update_only=True)
        self.shell_panel_3D.update_plot()


class QVectorsWidget(WidgetBase):
    new_shell_number = Signal(int)

    def __init__(self, *args, **kwargs):
        kwargs["layout_type"] = "QVBoxLayout"
        super().__init__(*args, **kwargs)
        self._relative_size = 3
        trajectory_configurator = kwargs.get("trajectory_configurator")
        trajectory = None
        if trajectory_configurator is not None:
            trajectory = trajectory_configurator["instance"]
        self.helper = None
        top_bar_layout = QHBoxLayout()
        top_bar_layout.addWidget(QLabel("Generator type:"), stretch=0)
        self._selector = QComboBox(self._base)
        self._selector.addItems(
            filter(
                lambda x: x not in ("LatticeQVectors",), IQVectors.indirect_subclasses()
            )
        )
        self._model = VectorModel(self._base, trajectory=trajectory)
        self._view = QTableView(self._base)
        self._preview_button = QPushButton("Preview vector distribution")
        self._preview_button.clicked.connect(self.helper_dialog)
        top_bar_layout.addWidget(self._selector, stretch=1)
        top_bar_layout.addStretch(1)
        top_bar_layout.addWidget(self._preview_button)
        self._layout.addLayout(top_bar_layout)
        self._layout.addWidget(self._view)
        self._view.setModel(self._model)
        self._selector.currentTextChanged.connect(self._model.switch_qvector_type)
        self._selector.setCurrentText("SphericalLatticeQVectors")
        self._model.itemChanged.connect(self.updateValue)
        self._model.type_changed.connect(self.updateValue)
        self._model.unit_cell_missing.connect(self.fail_early)
        self.updateValue()
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "The parameters needed by the specific q-vector generator can be input here"
        self._view.setToolTip(tooltip_text)
        self._selector.setToolTip(
            "The q vectors will be generated using the method chosen here."
        )
        self._model.input_is_valid.connect(self.validate_model_parameters)
        policy = self._view.sizePolicy()
        policy.setVerticalPolicy(QSizePolicy.Policy.Minimum)
        self._view.setSizePolicy(policy)
        self._view.horizontalHeader().hide()
        self._view.setSizeAdjustPolicy(
            QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents
        )
        self.value_changed.connect(self.preview_vectors)

    @Slot(bool)
    def validate_model_parameters(self, all_are_correct: bool):
        if all_are_correct:
            self.clear_error()
        else:
            self.mark_error("Some entries in the parameter table are invalid.")

    @Slot()
    def fail_early(self):
        """Interrupt the vector generation process early due to initial errors."""
        self._configurator.error_status = "Unit cell information is missing in the trajectory. Lattice vectors will not work."
        self.updateValue()

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        qvector_type = self._selector.currentText()
        pardict = self._model.params_summary()
        return (qvector_type, pardict)

    def configure_using_default(self):
        """This is too complex to have a default value"""

    def create_helper(
        self,
    ) -> VectorViewer:
        """Create the vector plotting dialog.

        The PlotWidget is modified compared to the normal plotter,
        not allowing the user to change the plotting mode from 'vectors'.
        """
        dialog_instance = VectorViewer(self._base, configurator=self._configurator)
        for shell_panel in (dialog_instance.shell_panel_3D,):
            self.new_shell_number.connect(shell_panel.set_upper_limit)
        return dialog_instance

    @Slot()
    def helper_dialog(self) -> None:
        """Open the helper dialog."""
        if self.helper is None:
            self.helper = self.create_helper()
        if self.helper.isVisible():
            geometry = self.helper.saveGeometry()
            self.helper.previous_geometry = geometry
            self.helper.close()
        else:
            if hasattr(self.helper, "previous_geometry"):
                self.helper.restoreGeometry(self.helper.previous_geometry)
            self.helper.show()
            self.preview_vectors()

    @Slot()
    def preview_vectors(self):
        """Build the data sets and plot them in the dialog window.

        If the dialog is not open, this function exits immediately."""
        if self.helper is None:
            self.helper = self.create_helper()
        if not self.helper.isVisible():
            return
        if self._configurator.error_status != "OK":
            self.helper.plot_widget._plotter.plot_blank()
            self.helper.shell_panel_3D.plot_widget._plotter.plot_blank()
            return
        model = PlottingContext()
        for qvec_dataset in vector_q_statistics_datasets(self._configurator):
            model.add_dataset(qvec_dataset)
        self.helper.plot_widget.set_plotter("Vectors")
        self.helper.plot_widget.set_context(model)
        self.helper.plot_widget.use_grid()
        self.helper.plot_widget.use_legend()
        self.helper.plot_widget.plot_data()
        model.needs_an_update.connect(self.helper.update_plot)

    def updateValue(self):
        temp = super().updateValue()
        self._preview_button.setEnabled(self._configurator.error_status == "OK")
        self.new_shell_number.emit(self._configurator["n_shells"])
        return temp
