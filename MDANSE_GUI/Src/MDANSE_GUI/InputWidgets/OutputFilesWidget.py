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

import re
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from qtpy.QtCore import Qt, Slot
from qtpy.QtWidgets import QComboBox, QFileDialog, QLabel, QLineEdit, QPushButton

from MDANSE.Framework.Configurators.OutputFilesConfigurator import (
    OutputFilesConfigurator,
)
from MDANSE.IO.IOUtils import get_next_name, unused_standard_output_filename
from MDANSE.MLogging import LOG
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from MDANSE_GUI.Session.Session import Session

from .CheckableComboBox import CheckableComboBox

if TYPE_CHECKING:
    from MDANSE_GUI.InputWidgets import HDFTrajectoryWidget
    from MDANSE_GUI.Tabs.Visualisers.Action import Action


class OutputHandler(WidgetBase):
    FILENAME_FMT = "{filename}_{job_name}_{trial}"
    FILENAME_RE = r"{filename}_{job_name}_\d+"

    _field: QLineEdit
    _parent: Action
    EXTENSION: str

    # @property
    def traj_stem(self) -> str:
        return Path(
            self._configurator.configurable[
                self._configurator.dependencies["trajectory"]
            ]["value"]
        ).stem

    @property
    def jobname(self) -> str:
        if hasattr(self._parent, "_job_instance") and hasattr(
            self._parent._job_instance, "label"
        ):
            return str(self._parent._job_instance.label).replace(" ", "")

        LOG.error("It was not possible to get the job name from the parent")
        return ""

    @property
    def _pdefault_path(self) -> Path:
        try:
            return Path(self._parent._default_path)
        except (KeyError, AttributeError) as e:
            LOG.error("%s in OutputTrajectoryWidget - can't get default path.", str(e))
            return Path.cwd()

    def get_name(self) -> str:
        trial = unused_standard_output_filename(
            self._pdefault_path,
            self.traj_stem(),
            self.jobname,
            "_",
            self.EXTENSION,
        )

        if trial is None:
            LOG.error("Cannot get default filename")
            return ""
        return str(trial)

    def update_name(
        self,
        *_,
        old_filename: str | None = None,
        old_jobname: str | None = None,
    ) -> None:

        if old_filename is not None:
            try:
                pth = Path(old_filename)
                old_filename = pth.stem
            except Exception:
                old_filename = r"\w+"
        else:
            old_filename = r"\w+"

        if old_jobname is not None:
            pass
        elif self.jobname:
            old_jobname = self.jobname
        else:
            old_jobname = r"(?:[A-Z][a-z0-9]*)+"

        # print(
        #     "Inner:",
        #     old_filename,
        #     self.FILENAME_RE.format(
        #         filename=old_filename, job_name=self.jobname or old_jobname
        #     ),
        #     Path(self._field.text()).stem,
        #     re.match(
        #         self.FILENAME_RE.format(
        #             filename=old_filename, job_name=self.jobname or old_jobname
        #         ),
        #         Path(self._field.text()).stem,
        #     ),
        # )
        # import traceback
        # traceback.print_stack(limit=4)
        if re.match(
            self.FILENAME_RE.format(
                filename=old_filename, job_name=self.jobname or old_jobname
            ),
            Path(self._field.text()).stem,
        ):
            self._field.setText(self.get_name())


class OutputFilesWidget(OutputHandler):
    EXTENSION: str = ".mda"

    def __init__(
        self,
        *args,
        layout_type: Literal["QGridLayout"] = "QGridLayout",
        parent: Action,
        **kwargs,
    ):
        super().__init__(parent, *args, layout_type=layout_type, **kwargs)

        default_value = self._configurator.default
        self._parent = parent

        self._session: Session = self._parent._parent_tab._session

        self.default_path = self._pdefault_path / "output"

        self.file_association = "Output file name (*)"
        self._value = default_value

        guess_name = self.get_name()
        self._field = QLineEdit(guess_name, self._base)
        self._field.setPlaceholderText(guess_name)

        self.type_box = CheckableComboBox(self._base)
        self.type_box.addItems(
            [
                fmt_string
                for fmt_string in self._configurator.formats
                if fmt_string != "FileInMemory"
            ]
        )

        self.type_box.set_default("MDAFormat")
        # self.type_box.setCurrentText(default_value[1])

        browse_button = QPushButton("Browse", self._base)
        browse_button.clicked.connect(self.file_dialog)

        label = QLabel("Log file output:")
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.logs_combo = QComboBox(self._base)
        self.logs_combo.addItems(OutputFilesConfigurator.log_options)

        self._layout.addWidget(self._field, 0, 0)
        self._layout.addWidget(self.type_box, 0, 1)
        self._layout.addWidget(browse_button, 0, 2)
        self._layout.addWidget(label, 1, 0)
        self._layout.addWidget(self.logs_combo, 1, 1)

        self._default_value = default_value
        self._field.textChanged.connect(self.updateValue)
        self.type_box.lineEdit().textChanged.connect(self.updateValue)

        self.default_labels()
        self.update_labels()

        self.updateValue()
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "Analysis output will be saved under this name, and using the selected file types"

        self._field.setToolTip(tooltip_text)
        self.type_box.setToolTip(tooltip_text)

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if self._label_text == "":
            self._label_text = "OutputFilesWidget"
        if self._tooltip == "":
            self._tooltip = "Analysis output will be saved under this name, and using the selected file types"

    @Slot()
    def file_dialog(self):
        """A Slot defined to allow the GUI to be updated based on
        the new path received from a FileDialog.
        This will start a FileDialog, take the resulting path,
        and emit a signal to update the value show by the GUI.
        """
        try:
            self.default_path = Path(self._parent._default_path)
        except AttributeError:
            self.default_path = Path(".").absolute()
        new_value = QFileDialog.getSaveFileName(
            self._base,  # the parent of the dialog
            "Save files",  # the label of the window
            str(self.default_path),  # the initial search path
            self.file_association,  # text string specifying the file name filter.
        )
        if len(new_value[0]) > 0:
            self._field.setText(str(Path(new_value[0])))
            self.updateValue()

    def get_widget_value(self):
        self._configurator.forbidden_files = self._session.reserved_filenames
        filename = self._field.text()
        if len(filename) < 1:
            filename = self._default_value[0]

        formats = self.type_box.checked_values()
        log_level = self.logs_combo.currentText()

        return (str(Path(filename).absolute()), formats, log_level)
