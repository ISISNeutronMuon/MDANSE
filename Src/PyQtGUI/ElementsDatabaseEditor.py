
from qtpy.QtWidgets import QDialog, QPushButton, QFrame, QGridLayout,\
                           QVBoxLayout, QWidget, QLabel, QApplication,\
                           QSizePolicy, QMenu, QLineEdit, QTableView
from qtpy.QtCore import Signal, Slot, Qt, QPoint, QSize, QSortFilterProxyModel
from qtpy.QtGui import QFont, QEnterEvent, QStandardItem, QStandardItemModel

from MDANSE.Chemistry import ATOMS_DATABASE


class ElementView(QTableView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSortingEnabled(True)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        self.clickedPos = event.pos()
        Action = menu.addAction("New Entry")
        temp_model = self.model().sourceModel()
        if temp_model is not None:
            Action.triggered.connect(temp_model.new_line_dialog)
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
        ne_dialog = NewElementDialog()
        ne_dialog.got_name.connect(self.add_new_line)
        ne_dialog.show()
        result = ne_dialog.exec()
    
    @Slot(str)
    def add_new_line(self, new_label: str):
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

