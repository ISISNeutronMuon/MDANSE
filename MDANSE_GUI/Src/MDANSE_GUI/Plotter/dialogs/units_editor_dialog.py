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

import copy

import numpy as np

from qtpy import QtCore, QtGui, QtWidgets

from MDANSE.Framework.Units import _UNAMES, UNITS_MANAGER


class UnitsEditorDialog(QtWidgets.QDialog):
    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(UnitsEditorDialog, self).__init__(*args, **kwargs)

        self._default_units = copy.deepcopy(UNITS_MANAGER.units)

        self._build()

    def _build(self):
        """Build the dialog."""
        main_layout = QtWidgets.QVBoxLayout()

        hlayout = QtWidgets.QHBoxLayout()

        vlayout = QtWidgets.QVBoxLayout()

        self._registered_units_listview = QtWidgets.QListView()
        self._registered_units_listview.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )
        self._registered_units_listview.installEventFilter(self)
        vlayout.addWidget(self._registered_units_listview)

        self._new_unit_pushbutton = QtWidgets.QPushButton("New unit")
        vlayout.addWidget(self._new_unit_pushbutton)

        hlayout.addLayout(vlayout)

        unit_definition_groupbox = QtWidgets.QGroupBox()
        unit_definition_groupbox.setTitle("Definition")
        unit_definition_groupbox_layout = QtWidgets.QFormLayout()
        unit_definition_groupbox.setLayout(unit_definition_groupbox_layout)
        label = QtWidgets.QLabel("Factor")
        self._factor_doublespinbox = QtWidgets.QDoubleSpinBox()
        self._factor_doublespinbox.setMinimum(-np.inf)
        self._factor_doublespinbox.setMaximum(np.inf)
        self._factor_doublespinbox.setDecimals(20)
        self._factor_doublespinbox.setSingleStep(1.0e-20)
        self._factor_doublespinbox.setButtonSymbols(
            QtWidgets.QAbstractSpinBox.ButtonSymbols.NoButtons
        )
        self._factor_doublespinbox.setFixedWidth(200)
        self._factor_doublespinbox.editingFinished.connect(self.on_update_unit)
        unit_definition_groupbox_layout.addRow(label, self._factor_doublespinbox)
        self._dimension_spinboxes = {}
        for si_unit in _UNAMES:
            label = QtWidgets.QLabel(si_unit)
            self._dimension_spinboxes[si_unit] = QtWidgets.QSpinBox()
            self._dimension_spinboxes[si_unit].setMinimum(-100)
            self._dimension_spinboxes[si_unit].setMaximum(100)
            self._dimension_spinboxes[si_unit].editingFinished.connect(
                self.on_update_unit
            )
            unit_definition_groupbox_layout.addRow(
                label, self._dimension_spinboxes[si_unit]
            )

        hlayout.addWidget(unit_definition_groupbox)

        main_layout.addLayout(hlayout)

        buttons_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Save
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
            | QtWidgets.QDialogButtonBox.StandardButton.Ok
        )
        main_layout.addWidget(buttons_box)

        self.setLayout(main_layout)

        self.setWindowTitle("Units editor")
        self.resize(800, 200)

        self._update_units_listview()

        self._new_unit_pushbutton.clicked.connect(self.on_new_unit)

        buttons_box.accepted.connect(self.accept)
        buttons_box.rejected.connect(self.reject)
        buttons_box.button(
            QtWidgets.QDialogButtonBox.StandardButton.Save
        ).clicked.connect(self.on_save_units)

    def _update_units_listview(self):
        """Update the units listview."""
        units_model = QtGui.QStandardItemModel()
        units = sorted(UNITS_MANAGER.units.keys(), key=lambda v: v.lower())
        for u in units:
            units_model.appendRow(QtGui.QStandardItem(u))
        self._registered_units_listview.setModel(units_model)
        self._registered_units_listview.selectionModel().currentRowChanged.connect(
            self.on_select_unit
        )

    def eventFilter(self, source, event):
        """Event filter for the dialog.

        Args:
            source (qtpy.QtWidgets.QWidget): the widget triggering the event
            event (qtpy.QtCore.QEvent): the event
        """
        if event.type() == QtCore.QEvent.Type.KeyPress:
            if event.key() == QtCore.Qt.Key.Key_Delete:
                if source == self._registered_units_listview:
                    index = self._registered_units_listview.currentIndex()
                    units_model = self._registered_units_listview.model()
                    unit = units_model.data(index, QtCore.Qt.ItemDataRole.DisplayRole)
                    UNITS_MANAGER.delete_unit(unit)
                    self._registered_units_listview.model().removeRow(
                        self._registered_units_listview.currentIndex().row(),
                        QtCore.QModelIndex(),
                    )

        return super(UnitsEditorDialog, self).eventFilter(source, event)

    def on_new_unit(self):
        """Callback called when the new unit button is clicked."""
        unit_name, ok = QtWidgets.QInputDialog.getText(self, "New unit dialog", "Name")
        if not ok:
            return

        unit_name = unit_name.strip()
        if not UNITS_MANAGER.has_unit(unit_name):
            UNITS_MANAGER.add_unit(unit_name)
            self._update_units_listview()

        items = self._registered_units_listview.model().findItems(unit_name)
        if not items:
            return
        self._registered_units_listview.setCurrentIndex(items[0].index())

    def on_save_units(self):
        """Callback called when the save units button is clicked"""
        UNITS_MANAGER.save()

    def on_select_unit(self, index):
        """Callback called when a unit is selected from the units listview."""
        unit_model = self._registered_units_listview.model()
        selected_unit = unit_model.data(index, QtCore.Qt.ItemDataRole.DisplayRole)
        selected_unit = UNITS_MANAGER.get_unit(selected_unit)
        self._factor_doublespinbox.setValue(selected_unit.factor)
        dim = selected_unit.dimension
        for k, v in zip(_UNAMES, dim):
            self._dimension_spinboxes[k].setValue(v)

    def on_update_unit(self):
        """Callback called when a unit has been updated."""
        unit_model = self._registered_units_listview.model()
        selected_unit = unit_model.data(
            self._registered_units_listview.currentIndex(),
            QtCore.Qt.ItemDataRole.DisplayRole,
        )
        selected_unit = UNITS_MANAGER.get_unit(selected_unit)
        if selected_unit is None:
            return

        new_factor = self._factor_doublespinbox.value()
        selected_unit.factor = new_factor

        new_dimension = [self._dimension_spinboxes[u].value() for u in _UNAMES]
        selected_unit.dimension = new_dimension

    def reject(self):
        """Callback called when the dialog is canceled."""
        UNITS_MANAGER.units = self._default_units
        self._update_units_listview()
        super(UnitsEditorDialog, self).reject()
