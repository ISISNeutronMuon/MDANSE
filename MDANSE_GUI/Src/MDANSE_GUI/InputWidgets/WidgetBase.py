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
from typing import TYPE_CHECKING, Literal, Optional

from qtpy.QtCore import QObject, Signal, Slot
from qtpy.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from MDANSE.MLogging import LOG

if TYPE_CHECKING:
    from MDANSE.Framework.Configurators.IConfigurator import IConfigurator

Layouts = Literal["QHBoxLayout", "QVBoxLayout", "QGridLayout"]
Bases = Literal["QWidget", "QGroupBox"]

WARNING_STYLE = (
    "QWidget#InputWidget { background-color:rgb(220,210,30); font-weight: bold }"
)
ERROR_STYLE = (
    "QWidget#InputWidget { background-color:rgb(180,20,180); font-weight: bold }"
)


class WidgetBase(QObject):
    """Object to serve as an ABC to GUI widgets in MDANSE.

    Parameters
    ----------
    parent : Optional[QObject]
        Parent of widget.
    configurator : IConfigurator
        Configurator controlled by this widget.
    label : str
        Label of widget.
    tooltip : str
        Hover-over tooltip.
    base_type : QWidget | QGroupBox
        Base type to use.
    layout_type : QHBoxLayout | QVBoxLayout | QGridLayout
        Layout to add.
    """

    valid_changed = Signal()
    value_updated = Signal()
    value_changed = Signal()

    def __init__(
        self,
        parent: QObject | None = None,
        *args,
        configurator: IConfigurator,
        label: str = "",
        tooltip: str = "",
        base_type: Bases = "QGroupBox",
        layout_type: Layouts = "QHBoxLayout",
        **kwargs,
    ):
        super().__init__(*args, parent=parent)
        self._value = None
        self._relative_size = 1
        self._label_text = label
        self._tooltip = tooltip
        self._base_type = base_type
        self._layout_type = layout_type

        if self._layout_type == "QHBoxLayout":
            layoutClass = QHBoxLayout
        elif self._layout_type == "QVBoxLayout":
            layoutClass = QVBoxLayout
        elif self._layout_type == "QGridLayout":
            layoutClass = QGridLayout
        else:
            raise NotImplementedError(
                f"Cannot create layout of type {self._layout_type}."
            )

        if self._base_type == "QWidget":
            base = QWidget(parent)
            layout = layoutClass(base)
            base.setLayout(layout)
            self._label = QLabel(self._label_text, base)
            layout.addWidget(self._label)
        elif self._base_type == "QGroupBox":
            base = QGroupBox(self._label_text, parent)
            base.setToolTip(self._tooltip)
            layout = layoutClass(base)
            base.setLayout(layout)
        else:
            raise NotImplementedError(f"Cannot create base of type {self._base_type}.")

        self._base = base
        self._base.setObjectName("InputWidget")
        self._layout = layout
        self._configurator = configurator
        self._parent_dialog = parent
        self._empty = False
        self.has_warning = False

    def update_labels(self):
        """Update contained labels (dependent on base_type)."""

        if self._base_type == "QWidget":
            self._label.setText(self._label_text)
        elif self._base_type == "QGroupBox":
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
    def value_from_configurator(self):
        """
        Set the widgets to the values of the underlying configurator object.

        Should also check for dependencies of the configurator.
        """

    @abstractmethod
    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""

    @abstractmethod
    def configure_using_default(self):
        """Use configurator's default value, and highlight in the GUI"""
        default = self._configurator.default
        LOG.info(f"Setting {default} as placeholder text")
        self._field.setPlaceholderText(str(default))
        self._configurator.configure(default)

    def mark_error(self, error_text: str, *, silent: bool = False):
        """Highlight an erroneous entry and display given error_text.

        Parameters
        ----------
        error_text : str
            Message displayed on hover-over.
        silent : bool
            If True, update the widget's error without sending signals

        """
        self._base.setStyleSheet(ERROR_STYLE)
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
            self._base.setStyleSheet(WARNING_STYLE)
            self._base.setToolTip(warning_text)
            self.valid_changed.emit()
            return
        self.has_warning = False
        self.clear_error()

    def clear_error(self):
        """Remove error highlighting."""
        self._base.setStyleSheet("")
        self._base.setToolTip("")
        self.valid_changed.emit()

    @abstractmethod
    @Slot()
    def updateValue(self):
        current_value = self.get_widget_value()
        if self._empty:
            self.configure_using_default()
        try:
            self._configurator.configure(current_value)
        except Exception:
            self.mark_error(
                "COULD NOT SET THIS VALUE - you may need to change the values in other widgets"
            )
        self.value_changed.emit()
        if not self._configurator.valid:
            self.mark_error(self._configurator.error_status)
        else:
            self.mark_warning(self._configurator.warning_status)
            self.value_updated.emit()

    @abstractmethod
    def get_value(self):
        self.updateValue()
        return self._configurator["value"]

    @property
    def default_path(self) -> str:
        """Default path of parent dialog."""
        return self._parent_dialog.default_path

    @default_path.setter
    def default_path(self, value: str) -> None:
        self._parent_dialog.default_path = value
