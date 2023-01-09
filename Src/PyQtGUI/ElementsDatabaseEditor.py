
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

