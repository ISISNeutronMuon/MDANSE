# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/Widgets/Oscillator.py
# @brief     A progress bar that goes there and back
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Research Software Group at ISIS (see AUTHORS)
#
# **************************************************************************

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
