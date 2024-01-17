# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/__init__.py
# @brief     Implements module/class/test __init__
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from abc import abstractmethod

from qtpy.QtCore import QObject, Slot
from qtpy.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QGroupBox,
    QVBoxLayout,
    QGridLayout,
)


class WidgetBase(QObject):
    def __init__(self, *args, **kwargs):
        parent = kwargs.get("parent", None)
        super().__init__(*args, parent=parent)
        self._value = None
        self._label_text = kwargs.get("label", "")
        self._tooltip = kwargs.get("tooltip", "")
        self._base_type = kwargs.get("base_type", "QGroupBox")
        self._layout_type = kwargs.get("layout_type", "QHBoxLayout")
        configurator = kwargs.get("configurator", None)
        if self._layout_type == "QHBoxLayout":
            layoutClass = QHBoxLayout
        elif self._layout_type == "QVBoxLayout":
            layoutClass = QVBoxLayout
        else:
            layoutClass = QGridLayout
        if self._base_type == "QWidget":
            base = QWidget(parent)
            layout = layoutClass(base)
            base.setLayout(layout)
            self._label = QLabel(self._label_text, base)
            layout.addWidget(self._label)
        elif self._base_type == "QGroupBox":
            base = QGroupBox(self._label_text)
            base.setToolTip(self._tooltip)
            layout = layoutClass(base)
            base.setLayout(layout)
        self._base = base
        self._layout = layout
        self._configurator = configurator
        self._parent_dialog = parent

    def update_labels(self):
        if self._base_type == "QWidget":
            self._label.setText(self._label_text)
        elif self._base_type == "QGroupBox":
            self._base.setTitle(self._label_text)
        for widget in self._layout.children():
            if issubclass(widget, QWidget):
                widget.setToolTip(self._tooltip)

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if self._label_text == "":
            self._label_text = "Base Widget"
        if self._tooltip == "":
            self._tooltip = "A specific tooltip for this widget SHOULD have been set"

    @abstractmethod
    def value_from_configurator(self):
        """Set the widgets to the values of the underlying configurator object.
        Should also check for dependencies of the configurator.
        """

    @abstractmethod
    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""

    @abstractmethod
    @Slot()
    def updateValue(self):
        current_value = self.get_widget_value()
        self._configurator.configure(current_value)

    @abstractmethod
    def get_value(self):
        self.updateValue()
        return self._configurator["value"]

    @property
    def default_path(self):
        return self._parent_dialog.default_path

    @default_path.setter
    def default_path(self, value: str) -> None:
        self._parent_dialog.default_path = value
