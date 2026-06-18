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

import copy

from more_itertools import first, nth
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

from MDANSE.Framework.Configurators.BooleanConfigurator import BOOL_MAPPING
from MDANSE.Framework.Configurators.MDTrajAnalysisConfigurator import MDTRAJ_JOBS
from MDANSE.Framework.QVectors.IQVectors import IQVectors
from MDANSE.mdtraj.analysis import mdtraj_initial_params
from MDANSE.MLogging import LOG
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from MDANSE_GUI.Utils import block_signals


class MDTrajModel(QStandardItemModel):
    """Qt model for passing MDTraj Analysis parameters."""

    type_changed = Signal()
    input_is_valid = Signal(bool)

    def __init__(self, *args, trajectory=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._generator = None
        self._defaults = []
        self._trajectory = trajectory

    @Slot(str)
    def switch_job_type(
        self,
        analysis_type: str,
        optional_settings: dict | None = None,
    ):
        """Create a table of input parameters for the current job.

        Parameters
        ----------
        analysis_type : str
            Name of the IQVectors subclass to be created.
        optional_settings : dict | None, optional
            Dictionary of input parameters, by default None
        """
        self.clear()
        self.analysis_type = analysis_type
        args, kwargs = mdtraj_initial_params(MDTRAJ_JOBS[analysis_type])
        args.pop(args.index("traj"))
        self.arg_names = args
        self.kwarg_names = [x for x, _ in kwargs]
        for arg in args:
            name = arg
            value = "" if optional_settings is None else optional_settings.get(name, "")
            vtype = "Any"
            items = [QStandardItem(str(x)) for x in [name, value, vtype]]
            for it in items[0::2]:
                it.setEditable(False)
            for it in items[1::2]:
                it.setData(value, role=Qt.ItemDataRole.ToolTipRole)
            self.appendRow(items)
        for name, value in kwargs:
            vtype = type(value).__name__
            items = [QStandardItem(str(x)) for x in [name, value, vtype]]
            for it in items[0::2]:
                it.setEditable(False)
            for it in items[1::2]:
                it.setData(value, role=Qt.ItemDataRole.ToolTipRole)
            self.appendRow(items)
        self.type_changed.emit()

    def params_summary(self) -> dict:
        """Validate input types and return a dictionary of input parameters."""
        args, kwargs = [], {}
        all_inputs_are_valid = True
        with block_signals(self):
            # block signals to stop updateValue call on the colour
            # background change
            for rownum in range(self.rowCount()):
                name = str(self.item(rownum, 0).text())
                value = str(self.item(rownum, 1).text())
                vtype = str(self.item(rownum, 2).text())
                try:
                    parsed = self.parse_vtype(vtype, value, name)
                except ValueError:
                    parsed = "failed"
                if parsed == "failed":
                    self.item(rownum, 1).setData(
                        QBrush(Qt.GlobalColor.red),
                        role=Qt.ItemDataRole.BackgroundRole,
                    )
                    all_inputs_are_valid = False
                else:
                    self.item(rownum, 1).setData(0, role=Qt.ItemDataRole.BackgroundRole)
                if name in self.arg_names:
                    args.append(parsed)
                elif name in self.kwarg_names:
                    kwargs[name] = parsed
        self.input_is_valid.emit(all_inputs_are_valid)
        return args, kwargs

    def parse_vtype(self, vtype: str, value: str, vname: str):
        """Cast the input value to the type specified by the vtype keyword."""
        if vtype == "float":
            return float(value)
        elif vtype == "int":
            return int(value)
        elif vtype == "bool":
            try:
                value = BOOL_MAPPING[value.lower() if isinstance(value, str) else value]
            except (KeyError, ValueError):
                LOG.warning("Could not parse %s as logical true/false value", value)
            else:
                return value
        else:
            return value

        return "failed"


class MDTrajAnalysisWidget(WidgetBase):
    """Inputs parameters required by a specific MDTraj analysis."""

    new_shell_number = Signal(int)

    def __init__(self, *args, **kwargs):
        kwargs["layout_type"] = "QVBoxLayout"
        super().__init__(*args, **kwargs)
        self._relative_size = 3
        self.helper = None
        top_bar_layout = QHBoxLayout()
        top_bar_layout.addWidget(QLabel("MDTraj analysis type:"), stretch=0)
        self._selector = QComboBox(self._base)
        self._selector.addItems([str(x) for x in MDTRAJ_JOBS])
        self._model = MDTrajModel(self._base)
        self._view = QTableView(self._base)
        top_bar_layout.addWidget(self._selector, stretch=1)
        top_bar_layout.addStretch(1)
        self._layout.addLayout(top_bar_layout)
        self._layout.addWidget(self._view)
        self._view.setModel(self._model)
        self._selector.currentTextChanged.connect(self._model.switch_job_type)
        self._model.itemChanged.connect(self.updateValue)
        self._model.type_changed.connect(self.updateValue)
        self.updateValue()
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "The parameters needed by the specific MDTraj analysis can be input here"
        self._view.setToolTip(tooltip_text)
        self._selector.setToolTip(
            "Pick the MDTraj analysis which you want to run.",
        )
        policy = self._view.sizePolicy()
        policy.setVerticalPolicy(QSizePolicy.Policy.Minimum)
        self._view.setSizePolicy(policy)
        self._view.horizontalHeader().hide()
        self._view.setSizeAdjustPolicy(
            QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents,
        )
        self._selector.setCurrentText(first(MDTRAJ_JOBS))
        self._model.switch_job_type(first(MDTRAJ_JOBS))

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        analysis_type = self._selector.currentText()
        args, kwargs = self._model.params_summary()
        return (analysis_type, args, kwargs)

    def configure_using_default(self):
        """This is too complex to have a default value"""
