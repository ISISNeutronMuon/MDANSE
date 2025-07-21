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
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.Framework.NewQVectors.QVector import QVectorGenerator
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from qtpy.QtCore import Qt, Signal, Slot
from qtpy.QtWidgets import QCheckBox, QComboBox, QGroupBox, QHBoxLayout

from .BooleanWidget import BooleanWidget
from .FloatWidget import FloatWidget
from .IntegerWidget import IntegerWidget
from .OptionalFloatWidget import OptionalFloatWidget
from .RangeWidget import RangeWidget
from .StringWidget import StringWidget
from .VectorListWidget import VectorListWidget
from .VectorWidget import VectorWidget
from .InputFileWidget import InputFileWidget

WIDGETS = {
    "VectorConfigurator": VectorWidget,
    "FloatConfigurator": FloatWidget,
    "OptionalFloatConfigurator": OptionalFloatWidget,
    "BooleanConfigurator": BooleanWidget,
    "StringConfigurator": StringWidget,
    "IntegerConfigurator": IntegerWidget,
    "RangeConfigurator": RangeWidget,
    "VectorList": VectorListWidget,
    "VectorInputFileConfigurator": InputFileWidget,
}


def get_value(widget: WidgetBase):
    raw = widget.get_widget_value()
    cls = type(widget)

    if cls is FloatWidget:
        return float(raw)
    if cls is OptionalFloatWidget:
        if not raw[0]:
            return None
        return float(raw)
    if cls is IntegerWidget:
        return int(raw)

    return raw


class QVectorParameters(WidgetBase):
    type_changed = Signal()
    input_is_valid = Signal(bool)

    def __init__(self, *args, trajectory=None, **kwargs):
        kwargs["layout_type"] = "QVBoxLayout"
        super().__init__(*args, configurator=None, **kwargs)
        self._generator = None
        self._defaults = []
        self._trajectory = trajectory
        self._widgets = []
        self._widgets_in_layout = []

    @Slot(str)
    def switch_qvector_type(self, vector_type: str, optional_settings: dict | None = None):
        for base, widget in zip(self._widgets, self._widgets_in_layout):
            # remove it from the layout list
            base.valid_changed.disconnect()
            self._layout.removeWidget(widget)
            # remove it from the gui
            widget.hide()
            widget.setParent(None)
            widget.deleteLater()

        self._widgets.clear()
        self._widgets_in_layout.clear()

        self._defaults = []
        self._generator = QVectorGenerator.indirect_subclass_dictionary()[vector_type]

        for param, (config_type, settings) in self._generator.gui_defaults.items():
            cls = WIDGETS[config_type]

            configurator = IConfigurator.create(
                config_type, param, configurable=self._generator, **settings
            )
            widget = cls(configurator=configurator, **settings)
            widget.valid_changed.connect(self.is_valid)
            base = widget._base

            self._layout.addWidget(base, stretch=widget._relative_size)
            self._widgets_in_layout.append(base)
            self._widgets.append(widget)

        self.get_params()
        # self._base.update()

    def is_valid(self):
        all_valid = True
        for widget in self._widgets_in_layout:
            if widget.styleSheet():
                all_valid = False
                widget.setStyleSheet(
                    widget.styleSheet().replace("180,20,180", "240, 20, 20")
                )

        if not all_valid:
            self.mark_error("At least one component is failing.")
        else:
            self.clear_error()

    def get_params(self) -> dict:
        return {
            param: get_value(widget)
            for param, widget in zip(self._generator.gui_defaults, self._widgets)
        }

class NewQVectorsWidget(WidgetBase):
    def __init__(self, *args, use_shells: bool = True, **kwargs):
        kwargs["layout_type"] = "QVBoxLayout"
        super().__init__(*args, **kwargs)
        self._relative_size = 3

        trajectory_configurator = kwargs.get("trajectory_configurator", None)

        trajectory = (
            trajectory_configurator["instance"]
            if trajectory_configurator is not None
            else None
        )

        self._use_shells_container = QGroupBox("Use shells", self._base)
        layout = QHBoxLayout(self._use_shells_container)
        self._use_shells_container.setLayout(layout)
        self._use_shells_container.setToolTip("Whether to integrate over shells.")
        self._use_shells = QCheckBox(None)
        self._use_shells.setChecked(use_shells)
        layout.addWidget(self._use_shells)
        self._use_shells_widgets_in_layout = []
        self._use_shells_widgets = []
        self._layout.addWidget(self._use_shells_container)
        self._exclude = ["shells", "width"]

        self._widgets_in_layout = []
        self._widgets = []

        self._selector = QComboBox(self._base)

        self._model = QVectorParameters(trajectory=trajectory)
        model_base = self._model._base

        for param in self._configurator.gui_defaults.keys():
            config_type, settings = self._configurator.gui_defaults[param]
            cls = WIDGETS[config_type]

            configurator = IConfigurator.create(
                config_type, param, configurable=self._configurator, **settings
            )
            widget = cls(configurator=configurator, **settings)
            # widget.valid_changed.connect(self.is_valid)
            base = widget._base

            self._layout.addWidget(base, stretch=widget._relative_size)

            if param in self._exclude:
                self._use_shells_widgets_in_layout.append(base)
                self._use_shells_widgets.append(widget)
            else:
                self._widgets_in_layout.append(base)
                self._widgets.append(widget)

        self.rebuild()

        self._layout.addWidget(self._selector)
        self._layout.addWidget(model_base)
        self._use_shells.stateChanged.connect(self.rebuild)
        self._selector.currentTextChanged.connect(self._model.switch_qvector_type)
        self._model.switch_qvector_type("SphericalQVectors")
        self.updateValue()

        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "The parameters needed by the specific q-vector generator can be input here"

        model_base.setToolTip(tooltip_text)
        self._selector.setToolTip(
            "The q vectors will be generated using the method chosen here."
        )

        self._model.input_is_valid.connect(self.validate_model_parameters)

    @Slot()
    def rebuild(self):
        if self.use_shells:
            to_add = [
                name
                for name, cls in QVectorGenerator.indirect_subclass_dictionary().items()
                if hasattr(cls, "generate_shell")
            ]
        else:
            to_add = QVectorGenerator.indirect_subclasses()

        self._selector.clear()
        self._selector.addItems(to_add)
        self._selector.setCurrentText("SphericalQVectors")

        for base, widget in zip(self._use_shells_widgets_in_layout, self._use_shells_widgets):
            base.setEnabled(self.use_shells)

    @property
    def use_shells(self):
        return self._use_shells.checkState() is Qt.CheckState.Checked

    def type_change_update(self):
        # need to disconnect itemChanged otherwise updateValue will
        # be called multiple times as the item data has been changed
        # during the type update
        self._model.itemChanged.disconnect()
        self.updateValue()
        self._model.itemChanged.connect(self.updateValue)

    @Slot(bool)
    def validate_model_parameters(self, all_are_correct: bool):
        if all_are_correct:
            self.clear_error()
        else:
            self.mark_error("Some entries in the parameter table are invalid.")

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        pardict = self._model.get_params()

        pardict["generator_name"] = self._selector.currentText()
        for param, widget in zip(self._configurator.gui_defaults, self._widgets):
            pardict[param] = get_value(widget)

        pardict["use_shells"] = self.use_shells
        if self.use_shells:
            for param, widget in zip(self._exclude, self._use_shells_widgets):
                pardict[param] = get_value(widget)

        print(pardict)
        return pardict

    def configure_using_default(self):
        """This is too complex to have a default value"""
