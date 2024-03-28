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

from qtpy.QtCore import Signal, Slot, Qt, QTimer, QMutex
from qtpy.QtWidgets import (
    QWidget,
    QGridLayout,
    QSlider,
    QLineEdit,
    QHBoxLayout,
    QSpinBox,
    QVBoxLayout,
    QPushButton,
    QStyle,
    QSizePolicy,
    QTreeView,
    QDoubleSpinBox,
    QColorDialog,
    QGroupBox,
    QCheckBox,
)
from qtpy.QtGui import (
    QDoubleValidator,
    QIntValidator,
    QIcon,
    QPaintEvent,
    QPainter,
    QColor,
)

from MDANSE_GUI.MolecularViewer.MolecularViewer import MolecularViewer

button_lookup = {
    "start": QStyle.StandardPixmap.SP_MediaSkipBackward,
    "back": QStyle.StandardPixmap.SP_MediaSeekBackward,
    "stop": QStyle.StandardPixmap.SP_MediaStop,
    "play": QStyle.StandardPixmap.SP_MediaPlay,
    "fwd": QStyle.StandardPixmap.SP_MediaSeekForward,
    "end": QStyle.StandardPixmap.SP_MediaSkipForward,
}

jogger_stylesheet = """QSpinBox {
  border: 1px solid #ABABAB;
  border-radius: 3px;
}

QSpinBox::down-button  {
  subcontrol-origin: margin;
  subcontrol-position: center left;
  image: url(:/icons/leftArrow.png);
}

QSpinBox::up-button  {
  subcontrol-origin: margin;
  subcontrol-position: center right;
  image: url(:/icons/rightArrow.png);
}"""

another_stylesheet = """QSpinBox {
  border: 1px solid #ABABAB;
  border-radius: 3px;
}

QSpinBox::up-button  {
  subcontrol-origin: margin;
  subcontrol-position: center left;
  image: url(:/icons/leftArrow.png);
  background-color: #ABABAB;
  left: 1px;
  height: 24px;
  width: 24px;
}

QSpinBox::down-button  {
  subcontrol-origin: margin;
  subcontrol-position: center right;
  image: url(:/icons/rightArrow.png);
  background-color: #ABABAB;
  right: 1px;
  height: 24px;
  width: 24px;
}
"""


class ColourButton(QPushButton):
    def __init__(self, *args, colour=(255, 255, 255), **kwargs):
        super().__init__(*args, **kwargs)

        self._current_colour = QColor(colour[0], colour[1], colour[2])

    def paintEvent(self, a0: QPaintEvent) -> None:
        painter = QPainter()
        painter.setBrush(self._current_colour)
        painter.fillRect(self.rect())
        return super().paintEvent(a0)

    @Slot()
    def pickColour(self):
        new_colour = QColorDialog.getColor(initial=self._current_colour)
        if new_colour is not None:
            self._current_colour = new_colour


class ViewerControls(QWidget):
    def __init__(self, *args, **kwargs):
        super(QWidget, self).__init__(*args, **kwargs)
        layout = QGridLayout(self)
        self._viewer = None
        self._buttons = {}
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self.advance_frame)
        self._mutex = QMutex()
        self._frame_step = 1
        self._time_per_frame = 80  # in ms
        self._frame_factor = 1  # just a scalar multiplication factor
        self._visibility = [True, True, True, True]
        self.createSlider()
        self.createButtons(Qt.Orientation.Horizontal)
        self.createSidePanel()

    def createSlider(self):
        """This method creates a slider which illustrates the progress of the
        trajectory animation.
        """
        base = QWidget(self)
        base.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)
        hlay = QHBoxLayout(base)
        frame_slider = QSlider(base)
        frame_slider.setToolTip("Select a frame")
        frame_slider.setOrientation(Qt.Orientation.Horizontal)
        self._frame_slider = frame_slider
        hlay.addWidget(frame_slider)
        frame_selector = QSpinBox(base)
        # frame_selector.setStyleSheet(jogger_stylesheet)
        frame_selector.setValue(0)
        frame_selector.setMinimum(0)
        hlay.addWidget(frame_selector)
        frame_selector.valueChanged.connect(frame_slider.setValue)
        frame_slider.valueChanged.connect(frame_selector.setValue)
        self._frame_selector = frame_selector
        self.layout().addWidget(base, 2, 0, 1, 3)  # row, column, rowSpan, columnSpan

    def setViewer(self, viewer: MolecularViewer):
        self._viewer = viewer
        self.layout().addWidget(viewer, 0, 0, 2, 2)  # row, column, rowSpan, columnSpan
        self._frame_slider.valueChanged.connect(viewer.set_coordinates)
        viewer.new_max_frames.connect(self._frame_slider.setMaximum)
        viewer.new_max_frames.connect(self._frame_selector.setMaximum)
        viewer.new_max_frames.connect(self.stop_animation)
        # self._database.setViewer(viewer)
        # viewer.setDataModel(viewer._colour_manager)
        self._atom_details.setModel(viewer._colour_manager)
        viewer._colour_manager.new_atom_properties.connect(viewer.take_atom_properties)

    def createButtons(self, orientation: Qt.Orientation):
        """Create a bar with video player buttons for controlling the
        animation.
        """
        base = QWidget(self)
        base.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)
        if orientation == Qt.Orientation.Horizontal:
            layout = QHBoxLayout(base)
            self.layout().addWidget(
                base, 3, 0, 1, 3
            )  # row, column, rowSpan, columnSpan
        elif orientation == Qt.Orientation.Vertical:
            layout = QVBoxLayout(base)
            self.layout().addWidget(
                base, 0, 2, 2, 1
            )  # row, column, rowSpan, columnSpan
        for button_name, button_role in button_lookup.items():
            temp = QPushButton(base)
            icon = self.style().standardIcon(button_role)
            temp.setIcon(icon)
            layout.addWidget(temp)
            self._buttons[button_name] = temp
        self._buttons["stop"].clicked.connect(self.stop_animation)
        self._buttons["play"].clicked.connect(lambda: self.animate())
        self._buttons["fwd"].clicked.connect(lambda: self.animate(step_size=10))
        self._buttons["back"].clicked.connect(lambda: self.animate(step_size=-10))
        self._buttons["start"].clicked.connect(lambda: self.go_to_end(last_frame=False))
        self._buttons["end"].clicked.connect(lambda: self.go_to_end(last_frame=True))

    def createSidePanel(self):
        """Adds widgets for finer control of the playback"""
        base = QWidget(self)
        layout = QVBoxLayout(base)
        base.setLayout(layout)
        # the table of chemical elements
        wrapper1 = QGroupBox("Atom properties", base)
        layout1 = QHBoxLayout(wrapper1)
        self._atom_details = QTreeView(base)
        self._atom_details.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum
        )
        layout1.addWidget(self._atom_details)
        wrapper1.setLayout(layout1)
        layout.addWidget(wrapper1)
        # the widget selecting time per animation frame
        wrapper2 = QGroupBox("Time per frame (ms)", base)
        layout2 = QHBoxLayout(wrapper2)
        frame_time_selector = QSpinBox(base)
        frame_time_selector.setToolTip("Larger number means slower animation")
        frame_time_selector.setValue(5)
        frame_time_selector.setMinimum(1)
        frame_time_selector.setMaximum(5000)
        frame_time_selector.valueChanged.connect(self.setTimeStep)
        layout2.addWidget(frame_time_selector)
        wrapper2.setLayout(layout2)
        layout.addWidget(wrapper2)
        # the widget for frame skipping
        wrapper3 = QGroupBox("Show every N frames", base)
        layout3 = QHBoxLayout(wrapper3)
        frame_skip = QSpinBox(base)
        frame_skip.setToolTip("Animate every N frames in fast forward")
        frame_skip.setValue(1)
        frame_skip.setMinimum(1)
        frame_skip.setMaximum(5000)
        frame_skip.valueChanged.connect(self.setFrameSkip)
        layout3.addWidget(frame_skip)
        wrapper3.setLayout(layout3)
        layout.addWidget(wrapper3)
        # the widget for atom size scaling
        wrapper4 = QGroupBox("Atom size scaling", base)
        layout4 = QHBoxLayout(wrapper4)
        size_factor = QDoubleSpinBox(base)
        size_factor.setToolTip("Scaling factor for atom size")
        size_factor.setValue(0.8)
        size_factor.setMinimum(0.0)
        size_factor.setMaximum(50.0)
        size_factor.setSingleStep(0.05)
        size_factor.valueChanged.connect(self.setAtomSize)
        layout4.addWidget(size_factor)
        wrapper4.setLayout(layout4)
        layout.addWidget(wrapper4)
        wrapper5 = QGroupBox("Visible Objects", base)
        layout5 = QHBoxLayout(wrapper5)
        atoms_visible = QCheckBox("atoms", wrapper5)
        bonds_visible = QCheckBox("bonds", wrapper5)
        axes_visible = QCheckBox("axes", wrapper5)
        cell_visible = QCheckBox("cell", wrapper5)
        self._visibility_checkboxes = [
            atoms_visible,
            bonds_visible,
            axes_visible,
            cell_visible,
        ]
        for nw, box in enumerate(self._visibility_checkboxes):
            box.setTristate(False)
            box.setChecked(self._visibility[nw])
            box.stateChanged.connect(self.setVisibility)
            layout5.addWidget(box)
        layout.addWidget(wrapper5)
        # the database of atom types
        # self._database = TrajectoryAtomData()
        self.layout().addWidget(base, 0, 2, 2, 1)  # row, column, rowSpan, columnSpan

    @Slot()
    def setVisibility(self):
        for nw, box in enumerate(self._visibility_checkboxes):
            self._visibility[nw] = box.isChecked()
        self._viewer._new_visibility(self._visibility)

    @Slot(int)
    def setTimeStep(self, new_value: int):
        self._time_per_frame = new_value

    @Slot(int)
    def setFrameSkip(self, new_value: int):
        self._frame_factor = new_value

    @Slot(float)
    def setAtomSize(self, new_value: float):
        if self._viewer is None:
            return
        self._viewer._new_scaling(new_value)

    @Slot(bool)
    def go_to_end(self, last_frame: bool = True):
        self.stop_animation()
        if last_frame:
            target = self._frame_selector.maximum()
        else:
            target = self._frame_selector.minimum()
        self._frame_selector.setValue(target)

    @Slot()
    def stop_animation(self):
        """Stop changing trajectory frames."""
        self._mutex.lock()
        if self._animation_timer.isActive():
            self._animation_timer.stop()
        self._mutex.unlock()

    def animate(self, step_size: int = 1):
        """Plays the animation as a movie.

        Keyword Arguments:
            step_time -- time per frame in ms (default: {80})
            step_size -- step in frames, 1 means show every frame (default: {1})
        """
        if self._animation_timer.isActive():
            self._animation_timer.stop()
        self._frame_step = step_size * self._frame_factor
        self._animation_timer.setInterval(self._time_per_frame)
        self._animation_timer.start()

    def advance_frame(self):
        firstFrame = self._frame_selector.minimum()
        lastFrame = self._frame_selector.maximum()
        new_value = self._frame_selector.value() + self._frame_step
        if new_value < firstFrame:
            self._frame_selector.setValue(firstFrame)
            self.stop_animation()
        elif new_value > lastFrame:
            self._frame_selector.setValue(lastFrame)
            self.stop_animation()
        else:
            self._frame_selector.setValue(new_value)
