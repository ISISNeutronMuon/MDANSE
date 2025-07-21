import numpy as np
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE_GUI.InputWidgets.InputFileWidget import OptionalInputFileWidget
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from qtpy.QtCore import Signal, Slot
from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QPushButton, QSizePolicy, QSpinBox, QTableView


class VectorListTable(QStandardItemModel):
    """Vector list container."""

    rowAdded = Signal(int)

    def __init__(self, *args, n_dims: int = 3, **kwargs):
        super().__init__(*args, **kwargs)
        self.n_vecs = 0
        self.n_dims = n_dims

    @Slot(int)
    def set_rows(self, n: int):
        if n < self.n_vecs:  # Remove
            self.setRowCount(n)

        for _ in range(n - self.n_vecs):  # Add
            self.appendRow([QStandardItem("0") for _ in self.dims])
        self.n_vecs = n

    @property
    def dims(self):
        yield from range(self.n_dims)

    def get_widget_value(self):
        return [
            [self.item(rownum, dim).text() for dim in self.dims]
            for rownum in range(self.rowCount())
        ]

    @Slot(np.ndarray)
    def set_values(self, value: np.ndarray):
        if value.ndim != 2:
            raise ValueError(f"Cannot represent {value.ndim}-d vectors.")
        if value.shape[1] != self.n_dims:
            raise ValueError(
                f"Vectors expected to be {self.n_dims}-d received {value.shape[1]}-d."
            )

        self.set_rows(value.shape[0])
        for rownum, row in zip(range(self.rowCount()), value):
            for dim, elem in zip(self.dims, row):
                self.item(rownum, dim).setText(str(elem))

    @Slot()
    def add_row(self):
        self.appendRow([QStandardItem("0") for _ in self.dims])
        self.n_vecs += 1
        self.rowAdded.emit(self.n_vecs)


class VectorListWidget(WidgetBase):
    def __init__(self, n_rows: int, *args, **kwargs):
        kwargs["layout_type"] = "QVBoxLayout"
        super().__init__(*args, **kwargs)

        self._table = VectorListTable()

        self._view = QTableView(self._base)
        self._layout.addWidget(self._view)
        self._view.setModel(self._table)
        policy = self._view.sizePolicy()
        policy.setVerticalPolicy(QSizePolicy.Policy.Minimum)
        self._view.setSizePolicy(policy)
        self._view.horizontalHeader().hide()

        self._rows = QSpinBox(self._base)
        self._rows.setRange(0, 1000)
        self._layout.addWidget(self._rows)

        self._rows.valueChanged.connect(self._table.set_rows)
        self._rows.setValue(n_rows)
        self._table.rowAdded.connect(self._rows.setValue)

        self._add_row = QPushButton("Add vector")
        self._add_row.clicked.connect(self._table.add_row)
        self._layout.addWidget(self._add_row)

        self._table.itemChanged.connect(self.updateValue)
        self._table.rowAdded.connect(self.updateValue)

        if self._configurator.wildcard is not None:
            self._vector_input = IConfigurator.create(
                "VectorInputFileConfigurator",
                "File loader",
                wildcard=self._configurator.wildcard,
                label="From file",
                tooltip="Load vectors from file.",
            )
            self._file_dialog = OptionalInputFileWidget(
                parent=None, button_label="Load", configurator=self._vector_input
            )
            self._layout.addWidget(self._file_dialog._base)
            self._file_dialog.value_updated.connect(self.from_file)

    @Slot()
    def from_file(self):
        try:
            self._table.set_values(self._vector_input["vectors"])
            self._file_dialog.clear_error()
        except ValueError as err:
            self._file_dialog.mark_error(str(err))

    def updateValue(self):
        current_value = self._table.get_widget_value()

        try:
            self._configurator.configure(current_value)
        except Exception:
            self.mark_error(
                "COULD NOT SET THIS VALUE - you may need to change the values in other widgets"
            )

        self.value_changed.emit()

        if self._configurator.valid:
            self.clear_error()
            self.value_updated.emit()
        else:
            self.mark_error(self._configurator.error_status)
