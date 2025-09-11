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

from pathlib import Path
from typing import TYPE_CHECKING

from qtpy.QtCore import Signal, Slot
from qtpy.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from MDANSE_GUI.MolecularViewer.MolecularViewer import MolecularViewer


REC_BUTTON_ENABLED = "Start recording"
REC_BUTTON_DISABLED = "Recording every new frame"


class Save3DViewWidget(QWidget):
    new_image_filename = Signal(str)
    new_video_filename = Signal(str)
    save_image = Signal()
    start_recording = Signal()
    stop_recording = Signal()

    def __init__(self, parent):
        super().__init__(parent)
        self._molviewer = None

        self.setWindowTitle("Save 3D view to file")
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self._n_atoms = 0
        self.populate_layout()

    def initialise_values(self, viewer: MolecularViewer):
        """An instance of MolecularViewer will be saved as
        an internal attribute to allow this widget to
        access attributes and call methods directly.

        Parameters
        ----------
        viewer : MolecularViewer
            One of the 3D viewer instances in the MDANSE GUI
        """
        self._molviewer = viewer

    def create_image_widgets(self) -> QWidget:
        base = QGroupBox("Single image")
        layout = QVBoxLayout(base)
        self._image_filename_edit = QLineEdit(base)
        self._image_filename_edit.setPlaceholderText("Pick a name for the image file")
        self._image_browse_button = QPushButton("Browse", base)
        self._save_image_button = QPushButton("Save image", base)
        layout.addWidget(self._image_filename_edit)
        layout.addWidget(self._image_browse_button)
        layout.addWidget(self._save_image_button)
        self._save_image_button.clicked.connect(self.increment_image_number)
        self._image_browse_button.clicked.connect(self.set_image_name_from_dialog)
        return base

    def create_video_widgets(self) -> QWidget:
        base = QGroupBox("Animation")
        layout = QVBoxLayout(base)
        self._video_filename_edit = QLineEdit(base)
        self._video_filename_edit.setPlaceholderText("Pick a name for the video file.")
        self._video_browse_button = QPushButton("Browse", base)
        self._start_recording_button = QPushButton(REC_BUTTON_ENABLED, base)
        self._stop_recording_button = QPushButton("Stop recording", base)
        self._stop_recording_button.setEnabled(False)
        layout.addWidget(self._video_filename_edit)
        layout.addWidget(self._video_browse_button)
        layout.addWidget(self._start_recording_button)
        layout.addWidget(self._stop_recording_button)
        self._video_filename_edit.textChanged.connect(self.new_video_filename)
        self._start_recording_button.clicked.connect(self.start_recording)
        self._stop_recording_button.clicked.connect(self.stop_recording)
        self._start_recording_button.clicked.connect(self.toggle_widgets_on_rec_start)
        self._stop_recording_button.clicked.connect(self.toggle_widgets_on_rec_stop)
        self._video_browse_button.clicked.connect(self.set_video_name_from_dialog)
        return base

    def populate_layout(self):
        layout = self.layout()
        layout.addWidget(self.create_image_widgets())
        layout.addWidget(self.create_video_widgets())

    @Slot()
    def increment_image_number(self):
        image_name = Path(self._image_filename_edit.text())
        self.new_image_filename.emit(str(image_name))
        toks = str(image_name.stem).split("_")
        if len(toks) > 1:
            try:
                lastnum = int(toks[-1])
            except (ValueError, TypeError):
                new_name = "_".join(toks) + "_1"
            else:
                new_name = "_".join(toks[:-1]) + f"_{lastnum + 1}"
        elif len(toks) == 1:
            new_name = toks[0] + "_1"
        self._image_filename_edit.setText(new_name)

    def update_path(self):
        if self._molviewer._reader is not None:
            self._trajectory_path = str(Path(self._molviewer._reader.filename).parent)
        else:
            self._trajectory_path = "."

    def set_image_name_from_dialog(self):
        self.update_path()
        fname = QFileDialog.getSaveFileName(
            self,
            "Save current 3D view as PNG image",
            str(self._trajectory_path),
            "PNG file (*.png);;All files(*.*)",
        )
        if fname[0] is not None:
            self._image_filename_edit.setText(fname[0])

    def set_video_name_from_dialog(self):
        self.update_path()
        fname = QFileDialog.getSaveFileName(
            self,
            "Save 3D view frames as animation",
            str(self._trajectory_path),
            "AVI file (*.avi);;All files(*.*)",
        )
        if fname[0] is not None:
            self._video_filename_edit.setText(fname[0])

    @Slot()
    def toggle_widgets_on_rec_start(self):
        self._video_filename_edit.setEnabled(False)
        self._start_recording_button.setText(REC_BUTTON_DISABLED)
        self._start_recording_button.setEnabled(False)
        self._stop_recording_button.setEnabled(True)

    @Slot()
    def toggle_widgets_on_rec_stop(self):
        self._video_filename_edit.setEnabled(True)
        self._start_recording_button.setText(REC_BUTTON_ENABLED)
        self._start_recording_button.setEnabled(True)
        self._stop_recording_button.setEnabled(False)
