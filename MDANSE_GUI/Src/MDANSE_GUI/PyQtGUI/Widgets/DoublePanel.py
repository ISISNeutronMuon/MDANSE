# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/MainWindow.py
# @brief     Base widget for the MDANSE GUI
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Research Software Group at ISIS (see AUTHORS)
#
# **************************************************************************

from typing import Union, Iterable
from collections import OrderedDict
import copy
import os

from icecream import ic
from qtpy.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QScrollArea,
)
from qtpy.QtCore import Signal, Slot, QAbstractItemModel, QModelIndex

from MDANSE_GUI.PyQtGUI.DataViewModel.GeneralModel import GeneralModel


class DoublePanel(QWidget):
    """A basic component of the GUI, it combines the
    viewer for a data model, a visualiser for a specific
    component, and a button panel for actions.
    """

    item_picked = Signal(object)

    def __init__(
        self,
        *args,
        data_side: QWidget = None,
        visualiser_side: QWidget = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self._model = None
        self._view = None
        self._visualiser = None

        buffer = QWidget(self)
        scroll_area = QScrollArea()
        scroll_area.setWidget(buffer)
        scroll_area.setWidgetResizable(True)
        layout = QHBoxLayout(buffer)
        base_layout = QHBoxLayout(self)
        buffer.setLayout(layout)
        base_layout.addWidget(scroll_area)
        self.setLayout(base_layout)
        self._base = buffer

        if data_side is not None:
            layout.addWidget(data_side)
            self._view = data_side
        if visualiser_side is not None:
            layout.addWidget(visualiser_side)
            self._visualiser = visualiser_side

    def set_model(self, model: GeneralModel):
        self._model = model
        self._view.setDataModel(model)

    @Slot(QModelIndex)
    def visualise_item(self, index: QModelIndex):
        number = index.data()
        item = self._model._nodes[number]
        self.item_picked.emit(item)
