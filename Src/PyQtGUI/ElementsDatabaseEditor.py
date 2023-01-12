
from qtpy.QtWidgets import QDialog, QPushButton, QFrame, QGridLayout,\
                           QVBoxLayout, QWidget, QLabel, QApplication,\
                           QSizePolicy, QMenu, QLineEdit, QTableView
from qtpy.QtCore import Signal, Slot, Qt, QPoint, QSize, QSortFilterProxyModel
from qtpy.QtGui import QFont, QEnterEvent, QStandardItem, QStandardItemModel

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.PyQtGUI.Widgets.GeneralWidgets import InputVariable, InputDialog


class ElementView(QTableView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSortingEnabled(True)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        self.clickedPos = event.pos()
        Action1 = menu.addAction("New Atom")
        Action2 = menu.addAction("New Property")
        temp_model = self.model().sourceModel()
        if temp_model is not None:
            Action1.triggered.connect(temp_model.new_line_dialog)
            Action2.triggered.connect(temp_model.new_column_dialog)
        menu.exec_(event.globalPos())


class NewElementDialog(QDialog):

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

    def __init__(self, *args, element_database = None, **kwargs):
        super().__init__(*args, **kwargs)
    
        self.database = element_database
        self.parseDatabase()

        self.itemChanged.connect(self.write_to_database)

    def parseDatabase(self):

        all_column_names = self.database.properties
        all_row_names = self.database.atoms

        for entry in all_row_names:
            row = []
            atom_info = self.database[entry]
            for key in all_column_names:
                item = QStandardItem(str(atom_info[key]))
                try:
                    intnum = int(str(atom_info[key]))
                except ValueError:
                    try:
                        floatnum = float(atom_info[key])
                    except ValueError:
                        pass
                    except TypeError:
                        pass
                    else:
                        item.setData(floatnum, role = Qt.ItemDataRole.DisplayRole)
                except TypeError:
                    pass
                else:
                    item.setData(intnum, role = Qt.ItemDataRole.DisplayRole)
                row.append(item)
            self.appendRow(row)
        self.setHorizontalHeaderLabels(all_column_names)
        self.setVerticalHeaderLabels(all_row_names)

        self.all_column_names = all_column_names
        self.all_row_names = all_row_names
    
    @Slot('QStandardItem*')
    def write_to_database(self, item: 'QStandardItem'):
        data = item.data()
        text = item.text()
        row = item.row()
        column = item.column()
        print(f"data:{data}, text:{text},row:{row},column:{column}")
        print(f"column name={self.all_column_names[column]}, row name={self.all_row_names[row]}")
        self.database.set_value(self.all_row_names[row], self.all_column_names[column], text)
        self.save_changes()

    @Slot()
    def save_changes(self):

        self.database.save()
    
    @Slot() 
    def new_line_dialog(self):
        dialog_variables = [
            InputVariable(input_dict={'keyval':'atom_name',
                                      'format': str,
                                      'label':'New element name',
                                      'tooltip':'Type the name of the new chemical element here.',
                                      'values':['']})
        ]
        ne_dialog = InputDialog(fields = dialog_variables)
        ne_dialog.got_values.connect(self.add_new_line)
        ne_dialog.show()
        result = ne_dialog.exec()
    
    @Slot()
    def new_column_dialog(self):
        dialog_variables = [
            InputVariable(input_dict={'keyval':'property_name',
                                      'format': str,
                                      'label':'New property name',
                                      'tooltip':'Type the name of the new property here; it will be added to the table.',
                                      'values':['']}),
            InputVariable(input_dict={'keyval':'property_type',
                                      'format': str,
                                      'label':'Type of the new property',
                                      'tooltip':'One of the following: int, float, str, list',
                                      'values':['float']}),
        ]
        ne_dialog = InputDialog(fields = dialog_variables)
        ne_dialog.got_values.connect(self.add_new_column)
        ne_dialog.show()
        result = ne_dialog.exec()
    
    @Slot(dict)
    def add_new_line(self, input_variables: dict):
        new_label = 'Xx'
        try:
            new_label = input_variables['atom_name']
        except KeyError:
            return None
        if not new_label in self.database.atoms:
            self.database.add_atom(new_label)
            row = []
            for key in self.all_column_names:
                new_value = self.database.get_value(new_label, key)
                self.database.set_value(new_label, key, new_value)
                item = QStandardItem(str(new_value))
                row.append(item)
            self.all_row_names.append(new_label)
            self.appendRow(row)
            self.setVerticalHeaderItem(self.rowCount()-1, QStandardItem(str(new_label)))
            print(f"self.all_row_names has length: {len(self.all_row_names)}")
    
    @Slot(dict)
    def add_new_column(self, input_variables: dict):
        new_label = 'Xx'
        new_type = 'float'
        try:
            new_label = input_variables['property_name']
        except KeyError:
            return None
        try:
            new_type = input_variables['property_type']
        except KeyError:
            return None
        if not new_label in self.database.atoms:
            self.database.add_property(new_label, new_type)
            column = []
            for key in self.all_row_names:
                new_value = self.database.get_value(key, new_label)
                self.database.set_value(key, new_label, new_value)
                item = QStandardItem(str(new_value))
                column.append(item)
            self.all_column_names.append(new_label)
            self.appendColumn(column)
            self.setHorizontalHeaderItem(self.columnCount()-1, QStandardItem(str(new_label)))
            print(f"self.all_column_names has length: {len(self.all_column_names)}")


class ElementsDatabaseEditor(QDialog):

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


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    root = ElementsDatabaseEditor()
    root.show()
    app.exec()

