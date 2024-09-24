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
    QDoubleSpinBox,
    QTextEdit,
    QWidget,
)
from MDANSE_GUI.Tabs.Visualisers import DataPlotter
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from MDANSE.Framework.Configurators.TrajectoryFilterConfigurator import TrajectoryFilterConfigurator, FILTERS


class FilterDesigner(QDialog):
    """Generates a string that specifies the filter.

    Attributes
    ----------
    _helper_title : str
        The title of the helper dialog window.
    _visualiser: DataPlotter
        The data visualisation class for the filter graph
    _settings: dict
        Dictionary to hold current filter settings
    _filter_map : dict
        The dictionary that maps the filter designer type string to the corresponding filter class
    """

    _helper_title = "Filter designer"
    _visualiser = DataPlotter
    _settings = dict()
    _filter_map = {filter.__name__: filter for filter in FILTERS}

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

        self.layouts = QHBoxLayout()

        self.update_type(self._configurator.filter.__name__)
        self.create_designer()

    def update_type(self, filter_type: str):
        self._settings.update({"filter": filter_type})
        self.create_designer()

    def create_designer(self):
        """
        """

        graph_layout = QVBoxLayout()
        settings_layout = QVBoxLayout()

        # Produce the filter designer settings UI component
        self.create_settings_layout(settings_layout)

        # Produce the filter designer frequency-domain graph UI component
        self.create_graph_layout(graph_layout)

        self.layouts = QHBoxLayout()
        self.layouts.addLayout(graph_layout)
        self.layouts.addLayout(settings_layout)
        self.setLayout(self.layouts)

    def edit(self, key: str, value: str):
        self.render_graph()
        self._settings["attributes"].update({key: value})

    def setting_to_widget(self, name: str, val_group: dict, setting: any):
        widget = None
        if isinstance(setting, int) and not val_group.get("values", None):
            widget = QSpinBox()
            widget.setValue(setting)
            widget.setMinimum(0)
            widget.setSingleStep(1)
            signal = widget.valueChanged

        if isinstance(setting, float):
            widget = QDoubleSpinBox()
            widget.setValue(setting)
            widget.setMinimum(0)
            widget.setSingleStep(0.1)
            signal = widget.valueChanged

        if isinstance(setting, bool):
            widget = QCheckBox()
            widget.setChecked(False)
            signal = widget.stateChanged

        if isinstance(setting, str) and val_group.get("values", None):
            widget = QComboBox()
            {widget.addItem(i) for i in val_group["values"]}
            widget.setCurrentText(setting)
            signal = widget.currentTextChanged

        signal.connect(lambda x: self.edit(name, x))
        return widget

    def create_settings_layout(self, widget_area: QVBoxLayout):
        """
        """
        filter = self._configurator.filter

        # Add filter type combobox
        type_cbox = QComboBox()
        for type in FILTERS:
            type_cbox.addItem(type.__name__)

        type_label = QLabel("Filter type")
        type_cbox.setCurrentText(filter.__name__)

        type_cbox.currentTextChanged.connect(lambda type: self.update_type(type))

        filter_type_layout = QHBoxLayout()
        filter_type_layout.addWidget(type_label)
        filter_type_layout.addWidget(type_cbox)

        widget_area.addLayout(filter_type_layout)

        filter_defaults = filter.default_settings

        # Preserve existing common filter settings
        self._settings["attributes"] = {
            key: value for key, value in self._settings.items() if key in set(filter_defaults.keys())
        }

        # Add filter settings
        for key, value in filter_defaults.items():
            setting_layout = QHBoxLayout()

            setting = self._settings["attributes"].get(key, value["value"])
            label = QLabel(key)

            setting_layout.addWidget(label)

            setting_widget = self.setting_to_widget(name=key, val_group=value, setting=setting)

            setting_layout.addWidget(setting_widget)

            widget_area.addLayout(setting_layout)

        # Add buttons
        buttons_layout = QHBoxLayout()
        for button in self.create_buttons():
            buttons_layout.addWidget(button)

        widget_area.addLayout(buttons_layout)

    def render_graph(self):
        """
        """
        pass

    def create_graph_layout(self, widget_area: QVBoxLayout):
        """
        """

        widget_area.addWidget(QPushButton("Pushez moi"))

    def apply(self) -> None:
        """Set the field of the TrajectoryFilterWidget to the currently
        chosen setting in this widget.
        """
        self._configurator.configure(self._settings)

        # update widget field text to reflect filter designer
        field = self._configurator.filter_description_string(
            self._filter_map[self._settings['filter']],
            self._settings
        )
        self._field.setText(field)

    def create_buttons(self) -> list[QPushButton]:
        """
        Returns
        -------
        list[QPushButton]
            List of push buttons to add to the last layout from
            create_layouts.
        """
        apply = QPushButton("Use Setting")
        close = QPushButton("Close")
        apply.clicked.connect(self.apply)
        close.clicked.connect(self.close)
        return [apply, close]


class TrajectoryFilterWidget(WidgetBase):
    """Trajectory filter designer widget."""

    _push_button_text = "Filter designer"
    _default_value = TrajectoryFilterConfigurator.get_json_string()
    _tooltip_text = "Design a trajectory filter. The input is a JSON string, and filter setting can be edited using the filter designer."

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
