# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/HDFTrajectoryWidget.py
# @brief     Implements module/class/test HDFTrajectoryWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from qtpy.QtWidgets import QLineEdit, QComboBox, QLabel, QTableView
from qtpy.QtCore import Slot, Signal, Qt
from qtpy.QtGui import QIntValidator, QStandardItemModel, QStandardItem, QBrush

from MDANSE.Framework.QVectors.IQVectors import IQVectors

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class VectorModel(QStandardItemModel):
    def __init__(self, *args, chemical_system=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._generator = None
        self._defaults = []
        self._chemical_system = chemical_system

    @Slot(str)
    def switch_qvector_type(self, vector_type: str):
        self.clear()
        self._defaults = []
        self._generator = IQVectors.create(vector_type, self._chemical_system)
        settings = self._generator.settings
        for kv in settings.items():
            name = kv[0]  # dictionary key
            value = kv[1][1]["default"]  # tuple value 1: dictionary
            self._defaults.append(value)
            vtype = kv[1][0]  # tuple value 0: type
            self.appendRow([QStandardItem(str(x)) for x in [name, value, vtype]])

    def params_summary(self) -> dict:
        params = {}
        for rownum in range(self.rowCount()):
            name = str(self.item(rownum, 0).text())
            value = str(self.item(rownum, 1).text())
            vtype = str(self.item(rownum, 2).text())
            try:
                params[name] = self.parse_vtype(vtype, value, name)
            except ValueError:
                params[name] = self._defaults[rownum]
                self.item(rownum, 1).setData(
                    QBrush(Qt.GlobalColor.red), role=Qt.ItemDataRole.BackgroundRole
                )
            else:
                self.item(rownum, 1).setData(
                    QBrush(Qt.GlobalColor.white), role=Qt.ItemDataRole.BackgroundRole
                )
        return params

    def parse_vtype(self, vtype: str, value: str, vname: str):
        if vtype == "RangeConfigurator":
            inner_type = self._generator.settings[vname][1]["valueType"]
            tempstring = value.strip("()[] ")
            return [inner_type(x) for x in tempstring.split(",")]
        elif vtype == "VectorConfigurator":
            inner_type = self._generator.settings[vname][1]["valueType"]
            tempstring = value.strip("()[] ")
            return [inner_type(x) for x in tempstring.split(",")]
        elif vtype == "FloatConfigurator":
            return float(value)
        elif vtype == "IntegerConfigurator":
            return int(value)
        else:
            return value


class QVectorsWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        kwargs["layout_type"] = "QVBoxLayout"
        super().__init__(*args, **kwargs)
        trajectory_configurator = kwargs.get("trajectory_configurator", None)
        chemical_system = None
        if trajectory_configurator is not None:
            chemical_system = trajectory_configurator["instance"].chemical_system
        self._selector = QComboBox(self._base)
        self._selector.addItems(IQVectors.subclasses())
        self._model = VectorModel(self._base, chemical_system=chemical_system)
        self._view = QTableView(self._base)
        self._layout.addWidget(self._selector)
        self._layout.addWidget(self._view)
        self._view.setModel(self._model)
        self._selector.currentTextChanged.connect(self._model.switch_qvector_type)
        self._selector.setCurrentIndex(1)
        self._model.itemChanged.connect(self.updateValue)
        self.updateValue()

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        qvector_type = self._selector.currentText()
        pardict = self._model.params_summary()
        return (qvector_type, pardict)

    def configure_using_default(self):
        """This is too complex to have a default value"""
