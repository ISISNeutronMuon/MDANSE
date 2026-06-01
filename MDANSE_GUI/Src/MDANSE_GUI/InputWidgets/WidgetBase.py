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

from abc import abstractmethod
from enum import EnumMeta
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeVar

from more_itertools import first_true
from qtpy.QtCore import QObject, Qt, Signal, Slot
from qtpy.QtGui import QColor, QPalette
from qtpy.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from MDANSE.Framework.Parameters.Parameters import (
    ConfigError,
    ConfigureDescriptor,
    CustomChoices,
    CustomConfig,
    MinMax,
    Parameter,
)
from MDANSE_GUI.Utils import block_signals

Layouts = Literal["QHBoxLayout", "QVBoxLayout", "QGridLayout"]
Bases = Literal["QWidget", "QGroupBox"]
P = TypeVar("P", bound=Parameter)

class WidgetBase(QObject, Generic[P]):
    """Object to serve as an ABC to GUI widgets in MDANSE.

    Parameters
    ----------
    parent : Optional[QObject]
        Parent of widget.
    parameter : Parameter
        Parameter controlled by this widget.
    label : str
        Label of widget.
    tooltip : str
        Hover-over tooltip.
    base_type : QWidget | QGroupBox
        Base type to use.
    layout_type : QHBoxLayout | QVBoxLayout | QGridLayout
        Layout to add.
    """

    value_changed = Signal()
    valid_changed = Signal()

    def __init__(
        self,
        parent: QObject | None = None,
        *args,
        parameter: P,
        configurable: object,
        prop: str,
        parent_widget: WidgetBase | None = None,
        label: str = "",
        tooltip: str = "",
        base_type: Bases = "QGroupBox",
        layout_type: Layouts = "QHBoxLayout",
        **kwargs,
    ):
        super().__init__(*args, parent=parent, **kwargs)
        self._parent = parent
        self._value = None
        self._relative_size = 1
        self._label_text = label
        self._tooltip = tooltip
        self._base_type = base_type
        self._layout_type = layout_type

        self.parameter = parameter
        self._configurable = configurable
        self._property = prop
        self._parent_widget = parent_widget

        for dep in self.get_widget_deps().values():
            dep.value_changed.connect(self.updateValue)

        match self._layout_type:
            case "QHBoxLayout":
                layoutClass = QHBoxLayout
            case "QVBoxLayout":
                layoutClass = QVBoxLayout
            case "QGridLayout":
                layoutClass = QGridLayout
            case _:
                raise NotImplementedError(
                    f"Cannot create layout of type {self._layout_type}."
                )

        match self._base_type:
            case "QWidget":
                base = QWidget(parent)
                layout = layoutClass(base)
                base.setLayout(layout)
                self._label = QLabel(self._label_text, base)
                layout.addWidget(self._label)
            case "QGroupBox":
                base = QGroupBox(self._label_text, parent)
                base.setToolTip(self._tooltip)
                layout = layoutClass(base)
                base.setLayout(layout)
            case _:
                raise NotImplementedError(
                    f"Cannot create base of type {self._base_type}."
                )

        self._base = base
        self._base.setAutoFillBackground(True)
        self._layout = layout
        self._parent_dialog = parent
        self._empty = False
        self.has_warning = False

        if self.parameter.optional:
            self.setup_optional()

        self._widgets_in_layout = {}
        self._raw_widgets = {}

    def setup_optional(self) -> None:
        label = getattr(
            self.parameter, "optional_label", f"Default ({self.parameter.default})"
        )

        self._apply_box = QCheckBox(label, self._base)
        self._apply_box.setTristate(False)
        self._apply_box.setChecked(self.default is None)
        self._apply_box.checkStateChanged.connect(self.toggle_widgets)
        self._layout.addWidget(self._apply_box)

    @Slot()
    def toggle_widgets(self) -> None:
        if not self.parameter.optional:
            return

        self._field.setEnabled(self._apply_box.checkState() != Qt.CheckState.Checked)
        self.updateValue()

    def update_labels(self):
        """Update contained labels (dependent on base_type)."""

        match self._base_type:
            case "QWidget":
                self._label.setText(self._label_text)
            case "QGroupBox":
                self._base.setTitle(self._label_text)

        for widget in self._layout.children():
            if issubclass(widget, QWidget):
                widget.setToolTip(self._tooltip)

    def default_labels(self):
        """Provide default labels.

        Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured.
        """
        if not self._label_text:
            self._label_text = "Base Widget"
        if not self._tooltip:
            self._tooltip = "A specific tooltip for this widget SHOULD have been set"

    @abstractmethod
    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""

    def _get_widget_value(self):
        """Get the widget value ignoring disabled optionals."""

        if (
            self.parameter.optional
            and self._apply_box.checkState() == Qt.CheckState.Checked
        ):
            return None
        return self.get_widget_value()

    def mark_error(self, error_text: str, *, silent: bool = False):
        """Highlight an erroneous entry and display given error_text.

        Parameters
        ----------
        error_text : str
            Message displayed on hover-over.
        silent : bool
            If True, update the widget's error without sending signals

        """
        pal = self._base.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(180, 20, 180))
        self._base.setPalette(pal)
        font = self._base.font()
        font.setBold(True)
        self._base.setFont(font)
        self._base.setToolTip(error_text)
        if not silent:
            self.valid_changed.emit()

    def mark_warning(self, warning_text: str):
        """If the input caused a warning, display warning_text and highlight the widget.

        If warning_text is an empty string, this method will clear errors instead.

        Parameters
        ----------
        warning_text : str
            Message displayed on hover-over.
        """
        if warning_text:
            self.has_warning = True
            pal = self._base.palette()
            pal.setColor(QPalette.ColorRole.Window, QColor(220, 210, 30))
            self._base.setPalette(pal)
            font = self._base.font()
            font.setBold(True)
            self._base.setFont(font)
            self._base.setToolTip(warning_text)
            self.valid_changed.emit()
            return
        self.has_warning = False
        self.clear_error()

    def clear_error(self):
        """Remove error highlighting."""
        self._base.setPalette(QPalette())
        font = self._base.font()
        font.setBold(False)
        self._base.setFont(font)
        self._base.setToolTip("")
        self.valid_changed.emit()

    def set_parameter(self) -> None:
        setattr(self._configurable, self._property, self._get_widget_value())

    @property
    def valid(self) -> bool:
        return getattr(self._configurable, self.parameter.configured_var, False)

    @property
    def raw(self) -> Any:
        return getattr(self._configurable, self.parameter.raw_name, None)

    @property
    def default(self) -> Any:
        return self._configurable.default_parameters[self._property]

    @property
    def value(self) -> Any:
        return self.get_value()

    @value.setter
    def value(self, value) -> None:
        self.set_value(value)

    def get_value(self) -> Any:
        return getattr(self._configurable, self._property)

    def set_value(self, value: Any) -> None:
        with block_signals(self._field):
            self._field.setText(str(value))
        self.updateValue()

    def trajectory_changed(self) -> None:
        self.updateValue()

    @property
    def choices(self) -> set[Any] | None:
        if isinstance(self.parameter.choices, EnumMeta):
            return {member.name.capitalize() for member in self.parameter.choices}

        if isinstance(self.parameter, CustomChoices):
            if any(self.parameter._bad_deps(self._configurable)):
                self.mark_error("Invalid dependencies")
                return set()

            deps = {key: widget.value for key, widget in self.get_widget_deps().items()}

            try:
                return self.parameter.get_choices(deps)
            except ConfigError:
                self.mark_error("No valid choices")
                return set()

        if self.parameter.choices:
            return self.parameter.choices

        return None

    @property
    def ranges(self) -> tuple[Any, Any] | None:
        if not isinstance(self.parameter, MinMax):
            return None

        if any(self.parameter._bad_deps(self._configurable)):
            self.mark_error("Invalid dependencies")
            return (None, None)

        deps = self.parameter._get_deps(self._configurable)
        return self.parameter.get_ranges(deps)

    def get_widget_deps(self) -> dict[str, WidgetBase]:
        if isinstance(self._parent_widget, WidgetBase):
            parent_deps = self._parent_widget.get_widget_deps()
            return {
                key: self._parent_widget._raw_widgets[val]
                if val != "parent"
                else parent_deps[key]
                for key, val in self.parameter.depends.items()
            }

        return {
            key: self._parent._raw_widgets[val]
            for key, val in self.parameter.depends.items()
        }

    def add_widget(
        self,
        input_widget: WidgetBase,
        key: str,
        *,
        add_to_layout: bool = True,
    ) -> None:
        if add_to_layout:
            self._layout.addWidget(
                input_widget._base, stretch=input_widget._relative_size
            )
        self._widgets_in_layout[key] = input_widget._base
        self._raw_widgets[key] = input_widget
        input_widget.value_changed.connect(self.value_changed.emit)

    def remove_widget(self, key: str) -> None:
        widget = self._raw_widgets.pop(key)
        widget.value_changed.disconnect()
        del self._widgets_in_layout[key]
        self._layout.removeWidget(widget._base)
        widget._base.hide()
        widget._base.setParent(None)
        widget._base.deleteLater()

    @Slot()
    def updateValue(self) -> None:
        try:
            self.set_parameter()
            self.clear_error()
        except ConfigError as err:
            self.mark_error(str(err))

        self.value_changed.emit()

    @property
    def default_path(self) -> str:
        """Default path of parent dialog."""
        return self._parent_dialog.default_path

    @default_path.setter
    def default_path(self, value: str) -> None:
        self._parent_dialog.default_path = value

    def get_dep(self, dependency: str, default=None):
        return first_true(
            self.parent()._widgets,
            pred=lambda x: (
                x._configurator
                is self._configurator.configurable[
                    self._configurator.dependencies[dependency]
                ]
            ),
        )
