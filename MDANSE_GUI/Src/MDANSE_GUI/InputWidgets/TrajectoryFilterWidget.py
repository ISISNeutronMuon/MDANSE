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
from qtpy.QtCore import Qt, Slot
from qtpy.QtWidgets import (
    QLineEdit,
    QPushButton,
    QDialog,
    QComboBox,
    QCheckBox,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QSpinBox,
    QTextEdit,
    QWidget,
)
from MDANSE_GUI.Tabs.Visualisers import DataPlotter
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.Framework.Configurators.TrajectoryFilterConfigurator import TrajectoryFilterConfigurator, FILTERS


class FilterDesigner(QDialog):
    """Generates a string that specifies the filter.

    Attributes
    ----------
    _helper_title : str
        The title of the helper dialog window.
    _types_cbox_map : dict
        The dictionary that maps the filter designer type string to the corresponding filter class
    """

    _helper_title = "Filter desginer"
    _visualiser = DataPlotter()

    def __init__(self, field: QLineEdit, configurator: TrajectoryFilterConfigurator, parent, *args, **kwargs):
        """
        Parameters
        ----------
        field : QLineEdit
            The QLineEdit field that will need to be updated when
            applying the setting.
        """
        super().__init__(parent, *args, **kwargs)
        self.setWindowTitle(self._helper_title)
        self._field = field
        self._configurator = configurator

        self.panels = [QVBoxLayout()]*2
        graph_view, settings_view = self.panels

        # Produce the filter designer graphical interface
        self.create_graph(graph_view)

        # Produce the filter designer settings interface
        self.create_settings(settings_view)

    def create_settings(self, widget_area: QVBoxLayout):
        """
        """
        filter = self._configurator.filter

        # Filter type combobox
        type_cbox = QComboBox()
        for type in FILTERS:
            type_cbox.addItem(type.__name__)

        type_label = QLabel("Filter type")
        type_cbox.setCurrentText(filter.__name__)

        filter_type_layout = QHBoxLayout()
        filter_type_layout.addWidget(type_label)
        filter_type_layout.addWidget(type_cbox)

        widget_area.addLayout(filter_type_layout)

        # Fiter settings
        for key, value in filter.default_settings.items():
            setting_layout = QHBoxLayout()

            default = value["value"]
            label = QLabel(key)

            setting_layout.addWidget(label)

            setting_widget = self.setting_to_widget(updater=self._configurator.add_setting, val_name=key, val_group=value, setting=default)

            self.setting_connector(setting_widget, value=default)

            # TODO: Connect settings widgets to configurator dictionary

            setting_layout.addWidget()

            widget_area.addLayout(setting_layout)

    @staticmethod
    def setting_to_widget(updater: callable, val_name: str, val_group: dict, setting):
        if isinstance(setting, int):
            widget = QSpinBox()
            widget.setValue(setting)
            widget.setMinimum(0)
            widget.singleStep(1)

        if isinstance(setting, float):
            widget = QSpinBox()
            widget.setValue(setting)

        if isinstance(setting, bool):
            widget = QCheckBox()
            widget.setChecked(False)

        elif isinstance(setting, str):
            if val_group.get("values", None):
                widget = QComboBox()
                { widget.addItem(i) for i in val_group["values"] }
                widget.setCurrentText(setting)
                return widget
            widget = QLineEdit(setting)

        return widget


class TrajectoryFilterWidget(WidgetBase):
    """Trajectory filter designer widget."""

    _push_button_text = "Filter designer"
    _default_value = '{ "filter": "' + f'{TrajectoryFilterConfigurator.filter}"' + f'{TrajectoryFilterConfigurator.settings()}' + '}'
    _tooltip_text = "Design a trajectory filter. The input is a JSON string, and can be created using the helper dialog."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._value = self._default_value
        self._field = QLineEdit(self._default_value, self._base)
        self._field.setPlaceholderText(self._default_value)
        self._field.setMaxLength(2147483647)  # set to the largest possible
        self._field.textChanged.connect(self.updateValue)
        self.filter_designer = self.create_helper()
        helper_button = QPushButton(self._push_button_text, self._base)
        helper_button.clicked.connect(self.helper_dialog)
        self._layout.addWidget(self._field)
        self._layout.addWidget(helper_button)
        self.update_labels()
        self.updateValue()
        self._field.setToolTip(self._tooltip_text)

    def create_helper(self) -> FilterDesigner:
        """
        Returns
        -------
        FilterDesigner
            Create and return the filter designer QDialog.
        """
        return FilterDesigner(self._field, self._configurator, self._base)

    @Slot()
    def helper_dialog(self) -> None:
        """Opens the helper dialog."""
        if self.filter_designer.isVisible():
            self.filter_designer.close()
        else:
            self.filter_designer.show()

    def get_widget_value(self) -> str:
        """
        Returns
        -------
        str
            The JSON selector setting.
        """
        selection_string = self._field.text()
        if len(selection_string) < 1:
            self._empty = True
            return self._default_value
        else:
            self._empty = False
        return selection_string
