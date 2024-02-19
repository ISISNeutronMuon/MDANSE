# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      MDANSE_GUI/Tabs/Layouts/DoublePanel.py
# @brief     Base widget for the MDANSE GUI
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Research Software Group at ISIS (see AUTHORS)
#
# **************************************************************************
from qtpy.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QScrollArea,
    QLabel,
    QPushButton,
)
from qtpy.QtCore import Signal, Slot

from MDANSE_GUI.Tabs.Models.GeneralModel import GeneralModel


class DoublePanel(QWidget):
    """A basic component of the GUI, it combines the
    viewer for a data model, a visualiser for a specific
    component, and a button panel for actions.
    """

    error = Signal(str)
    item_picked = Signal(object)

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        self._model = None
        self._view = None
        self._visualiser = None

        data_side = kwargs.pop("data_side", None)
        visualiser_side = kwargs.pop("visualiser_side", None)
        self._tab_reference = kwargs.pop("tab_reference", None)

        super().__init__(*args, **kwargs)

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

        self._leftlayout = leftlayout
        self._rightlayout = rightlayout
        self._lb_layout = lb_layout
        self._ub_layout = ub_layout

        if visualiser_side is not None:
            self._visualiser = visualiser_side
            self._rightlayout.addWidget(visualiser_side)
            if self._view is not None:
                self._view.connect_to_visualiser(visualiser_side)

    def connect_logging(self):
        self.error.connect(self._tab_reference.error)
        for thing in [self._view, self._visualiser, self._model]:
            thing.error.connect(self._tab_reference.error)

    def set_model(self, model: GeneralModel):
        self._model = model
        self._view.setModel(model)

    @Slot(str)
    def set_label_text(self, text: str):
        self._tab_label.setText(text)

    def add_widget(self, tempwidget: QWidget = None, upper=True):
        if upper:
            self._ub_layout.addWidget(tempwidget)
        else:
            self._lb_layout.addWidget(tempwidget)

    def add_button(self, label: str = "Button!", slot=None, upper=True):
        temp = QPushButton(label, self._base)
        if slot is not None:
            temp.clicked.connect(slot)
        if upper:
            self._ub_layout.addWidget(temp)
        else:
            self._lb_layout.addWidget(temp)

    def current_item(self):
        try:
            index = self._view.currentIndex()
            item = self._model.itemFromIndex(index)
        except Exception as e:
            self.error.emit(repr(e))
        else:
            return item
