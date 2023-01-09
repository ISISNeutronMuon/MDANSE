
from qtpy.QtWidgets import QDialog, QToolButton, QFrame, QGridLayout,\
                           QVBoxLayout, QWidget, QLabel, QApplication,\
                           QSizePolicy, QMenu, QTextEdit, QTableView
from qtpy.QtCore import Signal, Slot, Qt, QPoint, QSize, QSortFilterProxyModel
from qtpy.QtGui import QFont, QEnterEvent, QStandardItem, QStandardItemModel

from MDANSE.Chemistry import ATOMS_DATABASE


class ElementView(QTableView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSortingEnabled(True)


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

