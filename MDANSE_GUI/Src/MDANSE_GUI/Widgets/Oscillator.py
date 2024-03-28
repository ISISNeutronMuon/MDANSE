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

from qtpy.QtCore import Slot, Signal, QObject, QTimer
from qtpy.QtWidgets import QProgressBar


class FlexBar(QProgressBar):
    def __init__(self, parent):
        super().__init__(parent)
        self.forward = True
        self.setTextVisible(False)

    @Slot()
    def reverse(self):
        if self.forward == True:
            self.forward = False
        else:
            self.forward = True
        self.setInvertedAppearance(not self.forward)


class Oscillator(QObject):
    nextvalue = Signal(int)
    turnaround = Signal()
    clearbar = Signal()

    def __init__(self, progbar, parent=None, totalsteps=100):
        super().__init__(parent)
        self.progbar = progbar
        self.progbar.setMaximum(totalsteps)
        self.currval = 0
        self.maxval = totalsteps
        self.minval = 0
        self.forward = True
        self.timer = QTimer(self)
        self.nextvalue.connect(progbar.setValue)
        self.turnaround.connect(progbar.reverse)
        self.clearbar.connect(progbar.reset)
        self.timer.setInterval(10)
        self.timer.timeout.connect(self.step)

    def start(self):
        self.timer.start()

    def stop(self):
        self.timer.stop()
        self.clearbar.emit()
        self.currval = 0
        self.forward = True
        self.progbar.setInvertedAppearance(False)

    @Slot()
    def step(self):
        if self.forward:
            self.currval += 1
        else:
            self.currval -= 1
        if self.currval >= self.maxval:
            self.forward = not self.forward
            self.turnaround.emit()
        elif self.currval <= self.minval:
            self.forward = not self.forward
        self.nextvalue.emit(self.currval)
