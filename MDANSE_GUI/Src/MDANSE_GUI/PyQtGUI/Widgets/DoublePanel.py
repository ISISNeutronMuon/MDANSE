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
    QVBoxLayout,
    QScrollArea,
    QLabel,
    QPushButton,
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

        leftside = QWidget(self._base)
        leftlayout = QVBoxLayout(leftside)
        leftside.setLayout(leftlayout)

        rightside = QWidget(self._base)
        rightlayout = QVBoxLayout(rightside)
        rightside.setLayout(rightlayout)

        layout.addWidget(leftside)
        layout.addWidget(rightside)

        upper_buttons = QWidget(leftside)
        ub_layout = QHBoxLayout(upper_buttons)
        upper_buttons.setLayout(ub_layout)
        lower_buttons = QWidget(leftside)
        lb_layout = QHBoxLayout(lower_buttons)
        lower_buttons.setLayout(lb_layout)

        self._tab_label = QLabel(leftside)
        leftlayout.addWidget(self._tab_label)
        leftlayout.addWidget(upper_buttons)
        if data_side is not None:
            leftlayout.addWidget(data_side)
            self._view = data_side
        leftlayout.addWidget(lower_buttons)
        if visualiser_side is not None:
            rightlayout.addWidget(visualiser_side)
            self._visualiser = visualiser_side

        self._leftlayout = leftlayout
        self._rightlayout = rightlayout
        self._lb_layout = lb_layout
        self._ub_layout = ub_layout

    def set_model(self, model: GeneralModel):
        self._model = model
        self._view.setModel(model)

    @Slot(QModelIndex)
    def visualise_item(self, index: QModelIndex):
        number = index.data()
        item = self._model._nodes[number]
        self.item_picked.emit(item)

    @Slot(str)
    def set_label_text(self, text: str):
        self._tab_label.setText(text)

    def add_button(self, label: str = "Button!", slot=None, upper=True):
        temp = QPushButton(label, self._base)
        if slot is not None:
            temp.clicked.connect(slot)
        if upper:
            self._ub_layout.addWidget(temp)
        else:
            self._lb_layout.addWidget(temp)

    @Slot(str)
    def fail(self, message: str):
        """This method handles error messages in the GUI.
        It should be universal for all the tabs, so once
        a proper logger is added to the GUI, it can be
        added everywhere consistently.

        Parameters
        ----------
        message : str
            Text of the error message to be shown
        """
