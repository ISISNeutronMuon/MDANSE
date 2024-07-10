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
import glob
import itertools
import os
import os.path

from qtpy.QtWidgets import QComboBox, QLineEdit, QPushButton, QFileDialog, QLabel
from qtpy.QtCore import Slot, Qt

from MDANSE.MLogging import LOG
from MDANSE.Framework.Configurators.OutputStructureConfigurator import (
    OutputStructureConfigurator,
)

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class OutputStructureWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, layout_type="QGridLayout", **kwargs)
        default_value = self._configurator.default
        try:
            parent = kwargs.get("parent", None)
            self.default_path = parent.default_path
        except KeyError:
            self.default_path = "."
            LOG.error("KeyError in OutputTrajectoryWidget - can't get default path.")
        except AttributeError:
            self.default_path = "."
            LOG.error(
                "AttributeError in OutputTrajectoryWidget - can't get default path."
            )
        self.file_association = ".*"
        self._value = default_value
        self._field = QLineEdit(default_value[0], self._base)
        self._field.setPlaceholderText(default_value[0])
        self.format_box = QComboBox(self._base)
        self.format_box.addItems(self._configurator._formats)
        self.format_box.setCurrentText(default_value[1])
        browse_button = QPushButton("Browse", self._base)
        browse_button.clicked.connect(self.file_dialog)
        label = QLabel("Log file output:")
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.logs_combo = QComboBox(self._base)
        self.logs_combo.addItems(OutputStructureConfigurator.log_options)
        self._layout.addWidget(self._field, 0, 0)
        self._layout.addWidget(self.format_box, 0, 1)
        self._layout.addWidget(browse_button, 0, 2)
        self._layout.addWidget(label, 1, 0)
        self._layout.addWidget(self.logs_combo, 1, 1)
        self._default_value = default_value
        self._field.textChanged.connect(self.updateValue)
        self.default_labels()
        self.update_labels()
        self.updateValue()
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = (
                "The average structure of the trajectory"
                "will be saved under this name,"
                "using the selected format"
            )
        self._field.setToolTip(tooltip_text)

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if self._label_text == "":
            self._label_text = "OutputStructureWidget"
        if self._tooltip == "":
            self._tooltip = (
                "The average structure of the trajectory"
                "will be saved under this name,"
                "using the selected format"
            )

    @Slot()
    def file_dialog(self):
        """A Slot defined to allow the GUI to be updated based on
        the new path received from a FileDialog.
        This will start a FileDialog, take the resulting path,
        and emit a signal to update the value show by the GUI.
        """
        new_value = QFileDialog.getSaveFileName(
            self._base,  # the parent of the dialog
            "Load a file",  # the label of the window
            self.default_path,  # the initial search path
            self.file_association,  # text string specifying the file name filter.
        )
        if len(new_value[0]) > 0:
            self._field.setText(new_value[0])
            self.updateValue()

    @staticmethod
    def _get_unique_filename(directory, basename):
        filesInDirectory = [
            os.path.join(directory, e)
            for e in itertools.chain(
                glob.iglob(os.path.join(directory, "*")),
                glob.iglob(os.path.join(directory, ".*")),
            )
            if os.path.isfile(os.path.join(directory, e))
        ]
        basenames = [os.path.splitext(f)[0] for f in filesInDirectory]

        initialPath = path = os.path.join(directory, basename)
        comp = 1
        while True:
            if path in basenames:
                path = "%s(%d)" % (initialPath, comp)
                comp += 1
                continue
            return path

    def get_widget_value(self):
        filename = self._field.text()
        if len(filename) < 1:
            filename = self._default_value[0]
        format = self.format_box.currentText()
        log_level = self.logs_combo.currentText()
        return (filename, format, log_level)
