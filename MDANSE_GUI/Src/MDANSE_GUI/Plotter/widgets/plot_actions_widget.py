# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/Plotter/__init__.py
# @brief     root file of Plotter
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2023-now
# @authors   Eric Pellegrini
#
# **************************************************************************

from PyQt6 import QtCore, QtWidgets


class PlotActionsWidget(QtWidgets.QWidget):
    plot_in_new_figure = QtCore.pyqtSignal(str)
    plot_in_current_figure = QtCore.pyqtSignal(str)

    _plot_types = {1: "Line", 2: "Image"}

    def __init__(self, *args, **kwargs):
        super(PlotActionsWidget, self).__init__(*args, **kwargs)

        self._build()

        self.reset()

    def _build(self):
        main_layout = QtWidgets.QVBoxLayout()
        hlayout = QtWidgets.QHBoxLayout()
        self._new_plot_pushbutton = QtWidgets.QPushButton("Plot in new figure")
        self._current_plot_pushbutton = QtWidgets.QPushButton("Plot in current figure")
        hlayout.addWidget(self._new_plot_pushbutton)
        hlayout.addWidget(self._current_plot_pushbutton)
        main_layout.addLayout(hlayout)
        self.setLayout(main_layout)

        self.reset()

        self._new_plot_pushbutton.clicked.connect(self.on_plot_in_new_figure)
        self._current_plot_pushbutton.clicked.connect(self.on_plot_in_current_figure)

    def on_plot_in_current_figure(self, state):
        if self._ndim is None:
            return
        plot_type = PlotActionsWidget._plot_types[self._ndim]
        self.plot_in_current_figure.emit(plot_type)

    def on_plot_in_new_figure(self, state):
        if self._ndim is None:
            return
        plot_type = PlotActionsWidget._plot_types[self._ndim]
        self.plot_in_new_figure.emit(plot_type)

    def reset(self):
        self._ndim = None
        self._new_plot_pushbutton.setDisabled(True)
        self._current_plot_pushbutton.setDisabled(True)

    def set_data(self, data):
        self._ndim = data.ndim
        self._new_plot_pushbutton.setDisabled(False)
        self._current_plot_pushbutton.setDisabled(self._ndim > 1)
