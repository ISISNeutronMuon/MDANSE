# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/OutputTrajectoryWidget.py
# @brief     Implements module/class/test OutputTrajectoryWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import glob
import itertools
import os
import os.path

from qtpy.QtWidgets import QComboBox, QLabel, QLineEdit, QPushButton, QFileDialog
from qtpy.QtCore import Qt, Slot
from qtpy.QtGui import QStandardItemModel, QStandardItem

from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter
from MDANSE_GUI.PyQtGUI.InputWidgets.WidgetBase import WidgetBase


dtype_lookup = {"float16": 16, "float32": 32, "float64": 64, "float128": 128}


class OutputTrajectoryWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        default_value = self._configurator.default
        try:
            parent = kwargs.get("parent", None)
            self.default_path = parent.default_path
        except KeyError:
            self.default_path = "."
            print("KeyError in OutputTrajectoryWidget - can't get default path.")
        except AttributeError:
            self.default_path = "."
            print("AttributeError in OutputTrajectoryWidget - can't get default path.")
        self.file_association = ".*"
        self._value = default_value
        self.field = QLineEdit(default_value[0], self._base)
        self.dtype_box = QComboBox(self._base)
        self.dtype_box.addItems(["float16", "float32", "float64", "float128"])
        self.dtype_box.set_default("float64")
        self.compression_box = QComboBox(self._base)
        self.compression_box.addItems(["none"] + TrajectoryWriter.allowed_compression)
        self.compression_box.set_default("lza")
        # self.type_box.setCurrentText(default_value[1])
        browse_button = QPushButton("Browse", self._base)
        browse_button.clicked.connect(self.file_dialog)
        self._layout.addWidget(self.field)
        self._layout.addWidget(self.dtype_box)
        self._layout.addWidget(self.compression_box)
        self._layout.addWidget(browse_button)
        self.default_labels()
        self.update_labels()

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if self._label_text == "":
            self._label_text = "OutputTrajectoryWidget"
        if self._tooltip == "":
            self._tooltip = (
                "Analysis output will be saved under this name,"
                "with the selected floating point number precision"
                "and compression type"
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
            self.field.setText(new_value[0])
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
        filename = self.field.text()
        dtype = dtype_lookup[self.dtype_box.currentText()]
        compression = self.compression_box.currentText()
        return (filename, dtype, compression)
