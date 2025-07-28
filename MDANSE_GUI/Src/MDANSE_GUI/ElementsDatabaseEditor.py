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
from __future__ import annotations

from qtpy.QtCore import QSortFilterProxyModel, Qt, Signal, Slot
from qtpy.QtGui import (
    QBrush,
    QColor,
    QDoubleValidator,
    QIntValidator,
    QStandardItem,
    QStandardItemModel,
    QValidator,
)
from qtpy.QtWidgets import (
    QApplication,
    QColorDialog,
    QDialog,
    QItemDelegate,
    QLineEdit,
    QMenu,
    QPushButton,
    QTableView,
    QVBoxLayout,
)

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.Databases import AtomsDatabaseError
from MDANSE.MLogging import LOG
from MDANSE_GUI.Tabs.Views.Delegates import ColourPicker
from MDANSE_GUI.Widgets.GeneralWidgets import InputDialog, InputVariable


class ComplexValidator(QValidator):
    """A complex number validator for a QLineEdit.

    It is intended to limit the input to a string
    that can be converted to a complex number.

    """

    def validate(self, input_string: str, position: int) -> tuple[int, str]:
        """Check the input string from a widget.

        Implementation of the virtual method of QValidator.
        It takes in the string from a QLineEdit and the cursor position,
        and an enum value of the validator state. Widgets will reject
        inputs which change the state to Invalid.

        Parameters
        ----------
        input_string : str
            current contents of a text input field
        position : int
            position of the cursor in the text input field

        Returns
        -------
        int
            Validator state.
        str
            Original input string.
        int
            Cursor position.

        """
        state = QValidator.State.Intermediate
        if input_string:
            try:
                _ = complex(input_string)
            except (TypeError, ValueError):
                bad_chars = [
                    char for char in input_string if char not in "0123456789+-.j()e "
                ]
                if bad_chars:
                    state = QValidator.State.Invalid
                else:
                    state = QValidator.State.Intermediate
            else:
                state = QValidator.State.Acceptable
        return state, input_string, position


class FloatInputField(QItemDelegate):
    """QLineEdit with a QDoubleValidator."""

    def setEditorData(self, editor, index):
        editor.setText(str(index.data()))

    def setModelData(self, editor, model, index):
        new_text = editor.text()
        try:
            float(new_text)
        except (ValueError, TypeError):
            return
        model.setData(index, new_text)

    def createEditor(self, parent, _option, _index):
        sbox = QLineEdit(parent)
        validator = QDoubleValidator()
        sbox.setValidator(validator)
        sbox.textChanged.connect(self.valueChanged)
        return sbox

    @Slot()
    def valueChanged(self):
        self.commitData.emit(self.sender())


class ComplexInputField(QItemDelegate):
    """QLineEdit with a ComplexValidator."""

    def setEditorData(self, editor, index):
        editor.setText(str(index.data()))

    def setModelData(self, editor, model, index):
        new_text = editor.text()
        try:
            complex(new_text)
        except (ValueError, TypeError):
            return
        model.setData(index, new_text)

    def createEditor(self, parent, _option, _index):
        sbox = QLineEdit(parent)
        validator = ComplexValidator()
        sbox.setValidator(validator)
        sbox.textChanged.connect(self.valueChanged)
        return sbox

    @Slot()
    def valueChanged(self):
        self.commitData.emit(self.sender())


class IntInputField(QItemDelegate):
    """QLineEdit with a QIntValidator."""

    def setEditorData(self, editor, index):
        editor.setText(str(index.data()))

    def setModelData(self, editor, model, index):
        new_text = editor.text()
        try:
            int(new_text)
        except (ValueError, TypeError):
            return
        model.setData(index, new_text)

    def createEditor(self, parent, _option, _index):
        sbox = QLineEdit(parent)
        validator = QIntValidator()
        sbox.setValidator(validator)
        sbox.textChanged.connect(self.valueChanged)
        return sbox

    @Slot()
    def valueChanged(self):
        self.commitData.emit(self.sender())


class ColorInputField(ColourPicker):
    def setEditorData(self, editor, index):
        r, g, b = index.data().split(";")
        color = QColor(int(r), int(g), int(b))
        editor.setCurrentColor(color)

    def setModelData(self, editor, model, index):
        if editor.result() == QColorDialog.DialogCode.Accepted:
            color = editor.currentColor()
            model.setData(index, f"{color.red()};{color.green()};{color.blue()}")
            model.setData(index, color, role=Qt.ItemDataRole.BackgroundRole)
            self.valueChanged()

    def valueChanged(self):
        self.commitData.emit(self.sender())


class NewAtomTypeNameVariable(InputVariable):
    def inputValid(self) -> bool:
        """
        Returns
        -------
        bool
            True if the new atom type name is valid.
        """
        result = self.returnValue()
        if not result:
            self.invalid_tooltip = "New atom name should not be an empty string."
            return False
        if result in ATOMS_DATABASE.atoms:
            self.invalid_tooltip = "New atom name already exists."
            return False
        return True


class NewAtomPropertyNameVariable(InputVariable):
    def inputValid(self) -> bool:
        """
        Returns
        -------
        bool
            True if the new atom property name is valid.
        """
        result = self.returnValue()
        if not result:
            self.invalid_tooltip = (
                "New atom property name should not be an empty string."
            )
            return False
        if result in ATOMS_DATABASE.properties:
            self.invalid_tooltip = "New atom property name already exists."
            return False
        return True


class ElementView(QTableView):
    """A table with a context menu for adding new rows and columns."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.int_delegate = IntInputField(self)
        self.float_delegate = FloatInputField(self)
        self.color_delegate = ColorInputField(self)
        self.complex_delegate = ComplexInputField(self)
        self.setSortingEnabled(True)

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        Action1 = menu.addAction("New Custom Atom")
        Action2 = menu.addAction("Copy Atoms")
        Action3 = menu.addAction("Rename Custom Atom")
        Action4 = menu.addAction("Delete Custom Atoms")
        Action5 = menu.addAction("New Custom Property")
        Action6 = menu.addAction("Copy Properties")
        Action7 = menu.addAction("Rename Custom Property")
        Action8 = menu.addAction("Delete Custom Properties")

        data_model = self.parent().data_model

        custom_atms = set(ATOMS_DATABASE.atoms) - set(
            ATOMS_DATABASE.default_atoms_types
        )
        custom_props = set(ATOMS_DATABASE.properties) - set(
            ATOMS_DATABASE.default_atoms_properties
        )

        vert_header_idxs = {
            self.model().mapToSource(idx).row()
            for idx in self.selectionModel().selectedIndexes()
        }
        atm_syms = [
            data_model.verticalHeaderItem(row_idx).text()
            for row_idx in vert_header_idxs
        ]
        def_atms = ATOMS_DATABASE.default_atoms_types
        enable_delete_atms = any(atm_sym not in def_atms for atm_sym in atm_syms)

        col_idxs = {idx.column() for idx in self.selectionModel().selectedIndexes()}
        prop_labels = [
            data_model.horizontalHeaderItem(col_idx).text() for col_idx in col_idxs
        ]
        def_props = ATOMS_DATABASE.default_atoms_properties
        enable_delete_props = any(
            prop_label not in def_props for prop_label in prop_labels
        )

        idx = self.currentIndex()
        self.mouse_prop = data_model.horizontalHeaderItem(idx.column()).text()
        self.mouse_atm = data_model.verticalHeaderItem(
            self.model().mapToSource(idx).row(),
        ).text()

        temp_model = self.model().sourceModel()
        if temp_model is not None:
            Action1.triggered.connect(temp_model.new_line_dialog)
            Action2.triggered.connect(temp_model.copy_rows)
            if self.mouse_atm in custom_atms:
                Action3.triggered.connect(temp_model.rename_row_dialog)
            else:
                Action3.setEnabled(False)
            if enable_delete_atms:
                Action4.triggered.connect(temp_model.delete_rows)
            else:
                Action4.setEnabled(False)
            Action5.triggered.connect(temp_model.new_column_dialog)
            Action6.triggered.connect(temp_model.copy_columns)
            if self.mouse_prop in custom_props:
                Action7.triggered.connect(temp_model.rename_column_dialog)
            else:
                Action7.setEnabled(False)
            if enable_delete_props:
                Action8.triggered.connect(temp_model.delete_columns)
            else:
                Action8.setEnabled(False)

        menu.exec_(event.globalPos())


class NewElementDialog(QDialog):
    """Helper dialog for creating new rows in ElementView."""

    got_name = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QVBoxLayout(self)
        edit = QLineEdit(self)
        layout.addWidget(edit)
        self.setLayout(layout)
        self.textedit = edit
        self.button = QPushButton("Accept!", self)
        self.button.clicked.connect(self.accept)
        self.accepted.connect(self.return_value)
        layout.addWidget(self.button)

    @Slot()
    def return_value(self):
        self.got_name.emit(self.textedit.text())


class ElementModel(QStandardItemModel):
    """A Qt model interfacing with MDANSE AtomDatabase.

    Note that the
    order of atom and properties in the atom database may not be the
    same as the order of the atom and properties in the table. Their
    orderings might diverge as the database gets edited and/or the
    table gets sorted.
    """

    def __init__(self, *args, element_database=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.custom_header_brush = QBrush(QColor(255, 165, 0))
        self.database = element_database
        self.parseDatabase()

        self.itemChanged.connect(self.write_to_database)

    @property
    def all_row_names(self):
        """Names of all atoms."""
        return self.database.atoms

    @property
    def all_column_names(self):
        """Names of all properties."""
        return self.database.properties

    def parseDatabase(self):
        """Build a Qt model from the MDANSE atom database."""
        def_columns = self.database.default_atoms_properties
        def_rows = self.database.default_atoms_types

        for entry in self.all_row_names:
            row = []
            atom_info = self.database[entry]
            for key in self.all_column_names:
                item = QStandardItem(str(atom_info[key]))
                item.setEditable(not (entry in def_rows and key in def_columns))
                if ATOMS_DATABASE._properties[key] == "color":
                    r, g, b = atom_info[key].split(";")
                    item.setBackground(QBrush(QColor(int(r), int(g), int(b))))
                row.append(item)
            self.appendRow(row)

        for i, entry in enumerate(self.all_row_names):
            item = QStandardItem(entry)
            if entry not in self.database.default_atoms_types:
                item.setForeground(self.custom_header_brush)
            self.setVerticalHeaderItem(i, item)

        for i, entry in enumerate(self.all_column_names):
            item = QStandardItem(entry)
            if entry not in self.database.default_atoms_properties:
                item.setForeground(self.custom_header_brush)
            self.setHorizontalHeaderItem(i, item)

    @Slot("QStandardItem*")
    def write_to_database(self, item: QStandardItem):
        data = item.data()
        text = item.text()
        viewer = self.parent().viewer
        selected_idx = viewer.selectionModel().selectedIndexes()[0]
        idx = viewer.model().mapToSource(selected_idx)
        row = idx.row()
        column = idx.column()
        row_name = self.verticalHeaderItem(row).text()
        column_name = self.horizontalHeaderItem(column).text()
        LOG.info(f"data:{data}, text:{text}, row:{row}, column:{column}")
        LOG.info(f"column name={column_name}, row name={row_name}")
        self.database.set_value(row_name, column_name, text)
        self.save_changes()

    @Slot()
    def save_changes(self):
        """Write the current database to the standard user file."""
        self.database.save()

    @Slot()
    def new_line_dialog(self):
        """Open a dialog window for creating custom atom types."""
        dialog_variables = [
            NewAtomTypeNameVariable(
                input_dict={
                    "keyval": "atom_name",
                    "format": str,
                    "label": "New element name",
                    "tooltip": "Type the name of the new chemical element here.",
                    "value": "",
                }
            )
        ]
        ne_dialog = InputDialog(
            parent=self.parent(),
            fields=dialog_variables,
            title="Create Custom Atom",
        )
        ne_dialog.got_values.connect(self.add_row)
        ne_dialog.show()
        _result = ne_dialog.exec()

    @Slot()
    def new_column_dialog(self):
        """Open a dialog window for creating custom properties."""
        dialog_variables = [
            InputVariable(
                input_dict={
                    "keyval": "property_name",
                    "format": str,
                    "label": "New property name",
                    "tooltip": "Type the name of the new property here; it will be added to the table.",
                    "value": "",
                },
            ),
            InputVariable(
                input_dict={
                    "keyval": "property_type",
                    "format": str,
                    "label": "Type of the new property",
                    "tooltip": "One of the following: int, float, complex, str, list",
                    "value": ["int", "float", "complex", "str", "list"],
                },
            ),
            InputVariable(
                input_dict={
                    "keyval": "property_unit",
                    "format": str,
                    "label": "Unit of the new property",
                    "tooltip": "A valid physical unit, as used by MDANSE units.py",
                    "value": "none",
                },
            ),
        ]
        ne_dialog = InputDialog(
            parent=self.parent(),
            fields=dialog_variables,
            title="Create Custom Property",
        )
        ne_dialog.got_values.connect(self.add_new_column)
        ne_dialog.show()
        _result = ne_dialog.exec()

    @Slot()
    def rename_row_dialog(self):
        """Open a dialog window for renaming custom atoms."""
        dialog_variables = [
            NewAtomTypeNameVariable(
                input_dict={
                    "keyval": "new_atom_name",
                    "format": str,
                    "label": f'Rename custom atom "{self.parent().viewer.mouse_atm}" to',
                    "tooltip": "Type the new name of the chemical element here.",
                    "value": "",
                },
            ),
        ]
        ne_dialog = InputDialog(
            parent=self.parent(),
            fields=dialog_variables,
            title="Rename Custom Atom",
        )
        ne_dialog.got_values.connect(self.rename_row)
        ne_dialog.show()
        _result = ne_dialog.exec()

    @Slot(dict)
    def rename_row(self, input_variables: dict):
        """Rename an atom from one label to another.

        Parameters
        ----------
        input_variables : dict
            Dictionary containing old and new atom names.

        """
        old_label = self.parent().viewer.mouse_atm
        new_label = input_variables["new_atom_name"]
        try:
            self.database.rename_atom_type(old_label, new_label)
        except AtomsDatabaseError as e:
            LOG.error(f"Failed to update database with error: {e}")
        header_row_text = [
            self.verticalHeaderItem(i).text() for i in range(self.rowCount())
        ]
        row_idx = header_row_text.index(old_label)
        item = QStandardItem(new_label)
        item.setForeground(self.custom_header_brush)
        self.setVerticalHeaderItem(row_idx, item)
        self.save_changes()

    @Slot()
    def rename_column_dialog(self):
        """Open a dialog window for renaming custom properties."""
        dialog_variables = [
            NewAtomPropertyNameVariable(
                input_dict={
                    "keyval": "new_prop_name",
                    "format": str,
                    "label": f'Rename custom property "{self.parent().viewer.mouse_prop}" to',
                    "tooltip": "Type the new name of the atom property here.",
                    "value": "",
                },
            ),
        ]
        ne_dialog = InputDialog(
            parent=self.parent(),
            fields=dialog_variables,
            title="Rename Custom Property",
        )
        ne_dialog.got_values.connect(self.rename_column)
        ne_dialog.show()
        _result = ne_dialog.exec()

    @Slot(dict)
    def rename_column(self, input_variables: dict):
        """Rename an atom property from one name to another.

        Parameters
        ----------
        input_variables : dict
            Dictionary containing old and new atom property names.

        """
        old_label = self.parent().viewer.mouse_prop
        new_label = input_variables["new_prop_name"]
        try:
            self.database.rename_atom_property(old_label, new_label)
        except AtomsDatabaseError as e:
            LOG.error(f"Failed to update database with error: {e}")
        header_column_text = [
            self.horizontalHeaderItem(i).text() for i in range(self.columnCount())
        ]
        column_idx = header_column_text.index(old_label)
        item = QStandardItem(new_label)
        item.setForeground(self.custom_header_brush)
        self.setHorizontalHeaderItem(column_idx, item)
        self.save_changes()

    def copy_row_in_database(self, new_label: str, db_key: str):
        """Copy row data into a new entry and update the table.

        Parameters
        ----------
        new_label : str
            The new label the results are copied to.
        db_key : str
            The key of the data the new_labels data will be copied from.

        """
        row = []
        for i in range(self.columnCount()):
            key = self.horizontalHeaderItem(i).text()
            new_value = self.database.get_value(db_key, key, raw_value=True)
            self.database.set_value(new_label, key, new_value)
            item = QStandardItem(str(new_value))
            if ATOMS_DATABASE._properties[key] == "color":
                r, g, b = new_value.split(";")
                item.setBackground(QBrush(QColor(int(r), int(g), int(b))))
            row.append(item)
        self.appendRow(row)
        item = QStandardItem(new_label)
        if new_label not in self.database.default_atoms_types:
            item.setForeground(self.custom_header_brush)
        self.setVerticalHeaderItem(self.rowCount() - 1, item)
        LOG.info(f"self.all_row_names has length: {len(self.all_row_names)}")

    @Slot()
    def copy_rows(self):
        """Update the database and table with a copied atoms."""
        view = self.parent().viewer

        idxs = view.selectionModel().selectedIndexes()
        row_idxs = {(idx.row(), view.model().mapToSource(idx).row()) for idx in idxs}
        row_idxs = sorted(row_idxs, key=lambda x: x[0])

        for _, idx in row_idxs:
            atm_sym = self.verticalHeaderItem(idx).text()
            atm_sym_copy = atm_sym + " (copy)"
            while True:
                if atm_sym_copy not in self.database.atoms:
                    self.database.add_atom(atm_sym_copy)
                    self.copy_row_in_database(atm_sym_copy, atm_sym)
                    break
                atm_sym_copy += " (copy)"
        self.save_changes()

    @Slot(dict)
    def add_row(self, input_variables: dict):
        """Add a new line to the table from the database.

        Parameters
        ----------
        input_variables : dict
            Variables used to create the new entry.

        """
        try:
            new_label = input_variables["atom_name"]
        except KeyError:
            return None
        if new_label not in self.database.atoms:
            self.database.add_atom(new_label)
            self.copy_row_in_database(new_label, new_label)
        self.save_changes()

    @Slot()
    def delete_rows(self):
        """Delete custom rows from the table and update the database."""
        view = self.parent().viewer

        idxs = view.selectionModel().selectedIndexes()
        row_idxs = {(idx.row(), view.model().mapToSource(idx).row()) for idx in idxs}
        row_idxs = sorted(row_idxs, key=lambda x: x[0], reverse=True)
        row_idxs_atm_syms = [
            (i, self.verticalHeaderItem(j).text()) for i, j in row_idxs
        ]

        def_atms = ATOMS_DATABASE.default_atoms_types
        for row_idx, atm_sym in row_idxs_atm_syms:
            if atm_sym not in def_atms:
                view.model().removeRow(row_idx)
                self.database.remove_atom(atm_sym)
        self.save_changes()

    def copy_column_in_database(
        self,
        new_prop_name: str,
        old_prop_name: str,
        prop_type: str,
        prop_unit: str,
    ):
        """Copy column data into a new column and update the table.

        Parameters
        ----------
        new_prop_name : str
            The label of the new property to add.
        old_prop_name : str
            The label of the property to copy from.
        prop_type : str
            The property type.
        prop_unit : str
            The physical unit of the property.

        """
        self.database.add_property(new_prop_name, prop_type, unit=prop_unit)
        column = []
        for i in range(self.rowCount()):
            key = self.verticalHeaderItem(i).text()
            new_value = self.database.get_value(key, old_prop_name, raw_value=True)
            self.database.set_value(key, new_prop_name, new_value)
            item = QStandardItem(str(new_value))
            if ATOMS_DATABASE._properties[old_prop_name] == "color":
                r, g, b = new_value.split(";")
                item.setBackground(QBrush(QColor(int(r), int(g), int(b))))
            column.append(item)
        self.appendColumn(column)
        item = QStandardItem(new_prop_name)
        if new_prop_name not in self.database.default_atoms_properties:
            item.setForeground(self.custom_header_brush)
        self.setHorizontalHeaderItem(self.columnCount() - 1, item)
        self.parent().set_column_delegate(self.columnCount() - 1)
        LOG.info(f"self.all_column_names has length: {len(self.all_column_names)}")

    @Slot(dict)
    def add_new_column(self, input_variables: dict):
        """Add a custom property to the atom database.

        Parameters
        ----------
        input_variables: dict
            A dictionary containing the property name and property type
            to add.

        """
        try:
            new_label = input_variables["property_name"]
        except KeyError:
            return
        try:
            new_type = input_variables["property_type"]
        except KeyError:
            return
        try:
            new_unit = input_variables["property_unit"]
        except KeyError:
            return
        if new_label not in self.database.atoms:
            self.copy_column_in_database(new_label, new_label, new_type, new_unit)
        self.save_changes()

    @Slot()
    def copy_columns(self):
        """Update the database and table with a copied properties."""
        view = self.parent().viewer
        col_idx = list(
            {idx.column() for idx in view.selectionModel().selectedIndexes()},
        )
        col_idx.sort()
        for idx in col_idx:
            prop_label = self.horizontalHeaderItem(idx).text()
            prop_label_copy = prop_label + " (copy)"
            prop_type = self.database._properties[prop_label]
            prop_unit = self.database._units[prop_label]
            while True:
                if prop_label_copy not in self.database.properties:
                    self.copy_column_in_database(
                        prop_label_copy, prop_label, prop_type, prop_unit
                    )
                    break
                prop_label_copy += " (copy)"
        self.save_changes()

    @Slot()
    def delete_columns(self):
        """Delete custom columns from the table and update the database."""
        view = self.parent().viewer
        col_idx = list(
            {idx.column() for idx in view.selectionModel().selectedIndexes()},
        )
        col_idx.sort(reverse=True)
        def_props = ATOMS_DATABASE.default_atoms_properties
        for idx in col_idx:
            prop_label = self.horizontalHeaderItem(idx).text()
            if prop_label not in def_props:
                view.model().removeColumn(idx)
                self.database.remove_property(prop_label)
        self.save_changes()


class ElementsDatabaseEditor(QDialog):
    """Dialog containing an ElementView table.

    Can be run standalone, or from MDANSE_GUI.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("MDANSE Chemical Elements Database Editor")

        layout = QVBoxLayout(self)

        self.setLayout(layout)

        self.viewer = ElementView(self)
        layout.addWidget(self.viewer)

        self.data_model = ElementModel(self, element_database=ATOMS_DATABASE)

        self.proxy_model = QSortFilterProxyModel(self)

        self.proxy_model.setSourceModel(self.data_model)
        self.viewer.setModel(self.proxy_model)
        for column_number in range(self.data_model.columnCount()):
            self.set_column_delegate(column_number)

        self.resize(1280, 720)

    def set_column_delegate(self, column_number: int):
        """Set the delegate for the column in the table.

        Parameters
        ----------
        column_number : int
            The column number that needs have the delegate to be set.

        """
        column_name = self.data_model.horizontalHeaderItem(column_number).text()
        column_type = ATOMS_DATABASE._properties.get(column_name, "str")
        if column_type == "color":
            self.viewer.setItemDelegateForColumn(
                column_number,
                self.viewer.color_delegate,
            )
        elif column_type == "float":
            self.viewer.setItemDelegateForColumn(
                column_number,
                self.viewer.float_delegate,
            )
        elif column_type == "int":
            self.viewer.setItemDelegateForColumn(
                column_number,
                self.viewer.int_delegate,
            )
        elif column_type == "complex":
            self.viewer.setItemDelegateForColumn(
                column_number,
                self.viewer.complex_delegate,
            )


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    root = ElementsDatabaseEditor()
    root.show()
    app.exec()
