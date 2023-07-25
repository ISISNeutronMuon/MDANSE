
from qtpy.QtCore import Signal, Slot, Qt, QTimer, QMutex
from qtpy.QtWidgets import QWidget, QGridLayout, QSlider, QLineEdit, QHBoxLayout, QSpinBox,\
                           QVBoxLayout, QPushButton, QStyle
from qtpy.QtGui import QDoubleValidator, QIntValidator, QIcon

from MDANSE_GUI.PyQtGUI.MolecularViewer.MolecularViewer import MolecularViewer

button_lookup = {
    'start' : QStyle.StandardPixmap.SP_MediaSkipBackward,
    'back' : QStyle.StandardPixmap.SP_MediaSeekBackward,
    'stop' : QStyle.StandardPixmap.SP_MediaStop,
    'play' : QStyle.StandardPixmap.SP_MediaPlay,
    'fwd' : QStyle.StandardPixmap.SP_MediaSeekForward,
    'end' : QStyle.StandardPixmap.SP_MediaSkipForward,
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
        self.createSlider()
        self.createButtons(Qt.Orientation.Horizontal)

    def createSlider(self):
        """This method creates a slider which illustrates the progress of the
        trajectory animation.
        """
        base = QWidget(self)
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
        self.layout().addWidget(base, 2,0,1,2)  # row, column, rowSpan, columnSpan

    def setViewer(self, viewer: MolecularViewer):
        self._viewer = viewer
        self.layout().addWidget(viewer, 0,0,2,2)  # row, column, rowSpan, columnSpan
        self._frame_slider.valueChanged.connect(viewer.set_coordinates)
        viewer.new_max_frames.connect(self._frame_slider.setMaximum)
        viewer.new_max_frames.connect(self._frame_selector.setMaximum)
        viewer.new_max_frames.connect(self.stop_animation)

    def createButtons(self, orientation : Qt.Orientation):
        """Create a bar with video player buttons for controlling the
        animation.
        """
        base = QWidget(self)
        if orientation == Qt.Orientation.Horizontal:
            layout = QHBoxLayout(base)
            self.layout().addWidget(base, 3,0,1,2)  # row, column, rowSpan, columnSpan
        elif orientation == Qt.Orientation.Vertical:
            layout = QVBoxLayout(base)
            self.layout().addWidget(base, 0,2,2,1)  # row, column, rowSpan, columnSpan
        for button_name, button_role in button_lookup.items():
            temp = QPushButton(base)
            icon = self.style().standardIcon(button_role)
            temp.setIcon(icon)
            layout.addWidget(temp)
            self._buttons[button_name] = temp
        self._buttons['stop'].clicked.connect(self.stop_animation)
        self._buttons['play'].clicked.connect(lambda: self.animate())
        self._buttons['fwd'].clicked.connect(lambda: self.animate(step_size=10))
        self._buttons['back'].clicked.connect(lambda: self.animate(step_size=-10))
        self._buttons['start'].clicked.connect(lambda: self.go_to_end(last_frame=False))
        self._buttons['end'].clicked.connect(lambda: self.go_to_end(last_frame=True))
        
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
        """Stop changing trajectory frames.
        """
        self._mutex.lock()
        if self._animation_timer.isActive():
            self._animation_timer.stop()
        self._mutex.unlock()

    def animate(self, step_time: int = 80, step_size: int = 1):
        """Plays the animation as a movie.

        Keyword Arguments:
            step_time -- time per frame in ms (default: {80})
            step_size -- step in frames, 1 means show every frame (default: {1})
        """
        if self._animation_timer.isActive():
            self._animation_timer.stop()
        self._frame_step = step_size
        self._animation_timer.setInterval(step_time)
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

        
