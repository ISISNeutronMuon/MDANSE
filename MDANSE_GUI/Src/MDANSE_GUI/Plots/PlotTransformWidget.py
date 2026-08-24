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

import copy
from enum import Enum
from functools import partial
from itertools import count
from typing import Any, NamedTuple, NoReturn, overload

import matplotlib.pyplot as mpl
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from qtpy.QtCore import QEvent, QObject, Qt, Signal, Slot
from qtpy.QtGui import (
    QStandardItem,
    QStandardItemModel,
    QUndoCommand,
    QUndoStack,
)
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTableView,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from MDANSE_GUI.Plots.Ops.Op import (
    HasStats,
    HasStatsMult,
    HasStatsSingle,
    Op,
    Operation,
)
from MDANSE_GUI.Plots.PlotUtils import MDANSEMatPlotLibNavBar
from MDANSE_GUI.Tabs.Models.PlottingContext import (
    PlottingContext,
    plotting_column_index,
)
from MDANSE_GUI.Tabs.Plotters import Plotter
from MDANSE_GUI.Tabs.Visualisers.TextInfo import TextInfo
from MDANSE_GUI.Utils import HTML_wrap, from_param, get_main_signal, get_value


class ListModCommand(QUndoCommand):
    """Data class for undoing modifying lists."""

    def __init__(self, model: TransformModel):
        super().__init__()
        self.model: TransformModel = model

    def _insert(self, action: Operation, row: int | None = None):
        new_items = [QStandardItem(elem) for elem in action]
        for item in new_items:
            item.setEditable(False)

        if row is None:
            self.model.appendRow(new_items)
        else:
            self.model.insertRow(row, new_items)


class DeleteTransformationCommand(ListModCommand):
    """Delete rows from data as undoable action."""

    def __init__(self, model: TransformModel, rows: list[int]):
        super().__init__(model)
        self.rows = rows
        self.rows.sort(reverse=True)

    def redo(self) -> None:
        """Remove a transformation from the model."""
        self.actions = {row: list(self.model.takeRow(row)) for row in self.rows}

    def undo(self) -> None:
        """Add a transformation back into the model."""
        for row, action in reversed(self.actions.items()):
            self.model.insertRow(row, action)


class AppendTransformationCommand(ListModCommand):
    """Append rows to data as undoable action."""

    def __init__(self, model: TransformModel, action: Operation):
        super().__init__(model)
        self.action = action

    def redo(self) -> None:
        """Append a transformation to the model."""
        self._insert(self.action)

    def undo(self):
        """Remove the last transformation from the TransformModel."""
        self.model.removeRow(self.model.rowCount() - 1)


class TransformModel(QStandardItemModel):
    """Model representing sequences of transformation options."""

    can_undo = Signal(bool)
    can_redo = Signal(bool)

    transformation_changed = Signal()

    def __init__(self):
        """Assign the current trajectory to the model."""
        super().__init__(None)
        self.undo_stack = QUndoStack(self)
        self.setHorizontalHeaderLabels(["Operation", "Dataset", "Parameters"])

    def clear(self) -> None:
        """Reset model."""
        self.undo_stack.clear()
        super().clear()
        self.setHorizontalHeaderLabels(["Operation", "Dataset", "Parameters"])

    def get_ops(self):
        """Get contents as list of Operations."""
        ops = []
        for i in range(self.rowCount()):
            op = Operation(
                *[item.text() for col in range(3) if (item := self.item(i, col))]
            )
            ops.append(Op.from_tuple(op))

        return ops

    @Slot()
    def undo_last(self) -> None:
        """Execute QUndoStack.undo and update the undo/redo buttons."""
        self.undo_stack.undo()
        self.can_undo.emit(self.undo_stack.canUndo())
        self.can_redo.emit(self.undo_stack.canRedo())
        self.transformation_changed.emit()

    @Slot()
    def redo_last(self) -> None:
        """Execute QUndoStack.redo and update the undo/redo buttons."""
        self.undo_stack.redo()
        self.can_undo.emit(self.undo_stack.canUndo())
        self.can_redo.emit(self.undo_stack.canRedo())
        self.transformation_changed.emit()

    @Slot(tuple)
    def accept_from_widget(self, op: Operation) -> None:
        """Add a transformation operation sent from a transformation widget."""
        append_command = AppendTransformationCommand(self, op)
        self.undo_stack.push(append_command)
        self.can_undo.emit(self.undo_stack.canUndo())
        self.can_redo.emit(self.undo_stack.canRedo())
        self.transformation_changed.emit()

    @Slot(list)
    def remove_items(self, rows: list[int]) -> None:
        """remove a transformation operation."""
        remove_command = DeleteTransformationCommand(self, rows)
        self.undo_stack.push(remove_command)
        self.can_undo.emit(self.undo_stack.canUndo())
        self.can_redo.emit(self.undo_stack.canRedo())
        self.transformation_changed.emit()


class PlotTransformWidget(QDialog):
    """Transform data dialog."""

    _helper_title = "Apply Transformation"

    def __init__(
        self,
        parent: QWidget | None = None,
        *args,
        plotting_context: PlottingContext,
        **kwargs,
    ):
        super().__init__(parent, *args, **kwargs)
        self.setWindowTitle(self._helper_title)
        self.setWindowFlags(Qt.Window)

        self._plotting_context = plotting_context
        self._local_pc = PlottingContext(plotting_context._unit_lookup)
        self.model = TransformModel()
        self.base_layout = QGridLayout(self)
        self.current_ds = None
        self.orig_ds = None

        fig_layout = self._make_canvas()
        op_layout = self._make_op_list()
        param_layout = self._make_param_entry()

        self.base_layout.addLayout(fig_layout, 0, 0, 2, 2)
        self.base_layout.addLayout(op_layout, 0, 2, 2, 1)
        self.base_layout.addLayout(param_layout, 0, 3, 2, 1)

    def _make_canvas(self) -> QLayout:
        """Build the canvas and associated settings.

        Returns
        -------
        QLayout
            Canvas layout.
        """
        fig_layout = QVBoxLayout()
        fs = QHBoxLayout()
        self._ds_select = QComboBox()
        self._ds_select.addItems(self._plotting_context._datasets.keys())
        self._ds_range = QLineEdit()
        self._ds_range.setPlaceholderText(":")
        replot = QPushButton("Replot")

        fs.addWidget(self._ds_select)
        fs.addWidget(self._ds_range)
        fs.addWidget(replot)

        self._figure = mpl.figure(layout="constrained")
        figAgg = FigureCanvasQTAgg(self._figure)
        figAgg.setParent(self)
        figAgg.updateGeometry()

        self._toolbar = MDANSEMatPlotLibNavBar(figAgg, self)
        self._toolbar.update()

        self._plotter_select = QComboBox()
        self._plotter_select.addItems(
            [str(x) for x in Plotter.raw_names() if str(x) != "Text"]
        )
        self._plotter_select.currentTextChanged.connect(self.set_plotter)
        self._plotter_select.setCurrentText("Single")

        self._local_pc.needs_an_update.connect(self.plot_data)
        self.model.transformation_changed.connect(self.plot_data)

        self._ds_select.currentTextChanged.connect(self.change_ds)
        replot.pressed.connect(self.change_data_limits)

        fig_layout.addLayout(fs)
        fig_layout.addWidget(figAgg, stretch=1)
        fig_layout.addWidget(self._toolbar)
        fig_layout.addWidget(self._plotter_select)

        self.change_ds(self._ds_select.currentText())

        self.finished.connect(self.apply_ops)

        return fig_layout

    def _make_op_list(self) -> QLayout:
        """Make controls for operations list."""
        op_layout = QVBoxLayout()
        button_layout = QHBoxLayout()

        buttons = {
            # "Edit": self.edit_action,
            "Delete": self.delete_op,
            "Undo": self.model.undo_last,
            "Redo": self.model.redo_last,
        }

        for label, func in buttons.items():
            button = QPushButton(label, None)
            button.pressed.connect(func)
            op_layout.addWidget(button)

        op_layout.addLayout(button_layout)

        self.ops_list = QTableView()
        self.ops_list.setModel(self.model)

        op_layout.addWidget(self.ops_list)

        return op_layout

    def _make_param_entry(self) -> QLayout:
        param_entry = QVBoxLayout()

        self.ops_select = QListWidget()
        self.params_entry = QStackedWidget()

        for name, cls in Op.registry.items():
            widget = QWidget()
            layout = QGridLayout(widget)

            self.ops_select.addItem(name.title())

            enum = count()

            for i, (param, typ) in zip(enum, cls.param_types().items(), strict=False):
                label_widget, val_widget = from_param(param, typ)
                layout.addWidget(label_widget, i, 0)
                layout.addWidget(val_widget, i, 1)
                get_main_signal(val_widget).connect(self._update_info)

            self.params_entry.addWidget(widget)

        self.ops_select.currentRowChanged.connect(self.params_entry.setCurrentIndex)
        self.params_entry.currentChanged.connect(self._update_info)

        self._op_info = TextInfo()

        add = QPushButton("Add")
        add.pressed.connect(self.add_op)

        param_entry.addWidget(self.ops_select)
        param_entry.addWidget(self.params_entry)
        param_entry.addWidget(add)
        param_entry.addWidget(self._op_info)

        self.ops_select.setCurrentRow(0)
        self._update_info()

        return param_entry

    @Slot()
    def _update_info(self) -> None:
        """Update info panel on changed widget."""
        op = self.get_op()

        self._op_info.update_panel(f"""\
<h3>Operation</h3>
{op.__doc__}
<h3>Predictions</h3>
{self.compute_stats()}
""")

    @Slot(str)
    def change_ds(self, ds_label: str) -> None:
        """Actions on changeing dataset.

        - Set the local plotting context to disaply selected dataset.
        - Load operations applied to new dataset.

        Parameters
        ----------
        ds_label : str
            Label to load.
        """
        self.apply_ops()
        self._local_pc.clear()

        self.orig_ds = self._plotting_context._datasets[ds_label]
        self.current_ds = copy.copy(self.orig_ds)
        self._local_pc.add_dataset(
            self.current_ds,
            self._plotting_context.datasets()[ds_label],
        )

        limit = self._local_pc.item(0, plotting_column_index["Use it?"]).text()

        self._ds_range.setText(limit)

        self.model.clear()

        for operation in self.current_ds.ops:
            self.model.accept_from_widget(operation.as_tuple)

        self.plot_data()

    @Slot()
    def change_data_limits(self) -> None:
        """Action on changing data limits."""
        if not self.current_ds:
            return

        data_limits = self._ds_range.text()
        self.current_ds.set_data_limits(data_limits)
        self._local_pc.item(0, plotting_column_index["Use it?"]).setText(data_limits)
        self.plot_data()

    @Slot(str)
    def set_plotter(self, plotter_option: str):
        """Change the class handling the plot operation.

        Parameters
        ----------
        plotter_option : str
            Plotter name
        """
        try:
            self._plotter: Plotter = Plotter.create(plotter_option)
        except Exception:
            self._plotter = Plotter()

        # No sliders here
        self._plotter.enable_slider = lambda *args, **kwargs: None
        self._plotter._figure = self._figure
        self.plot_data()

    def compute_stats(self):
        """Compute and display stats about an operation."""

        operation = self.get_op()

        match operation:
            case HasStatsSingle():  # Accumulate stats
                stats = {name: [] for name in operation.STATS}
                # Only one DS
                curves = next(self._local_pc.curves())
                for _db, _label, (_xdata, ydata) in curves:
                    operation.stats_calculate_single(ydata)
                    for stat, val in operation.stats.items():
                        stats[stat].append(val)

                headers = ["dataset", *stats.keys()]
                table = zip(
                    sorted(operation.targets(10)), *stats.values(), strict=False
                )

            case HasStatsMult():  # Just compute
                operation.stats_calculate(
                    [
                        ydata
                        for _db, _label, (_xdata, ydata) in next(
                            self._local_pc.curves()
                        )
                    ]
                )
                stats = operation.stats

                headers = ["dataset", *stats.keys()]
                table = ((operation.target, *stats.values()),)

            case _:
                return ""

        header = "\n".join(HTML_wrap("th", header) for header in headers)
        header = HTML_wrap("tr", header)

        to_tab_data = partial(HTML_wrap, "td")

        tab_data = "\n".join(
            HTML_wrap("tr", "".join(map(to_tab_data, row))) for row in table
        )

        return HTML_wrap("table", header + "\n" + tab_data, style='"width:100%"')

    def plot_data(self):
        """Plot data to local figure."""
        if self.current_ds is None:
            return

        self.current_ds.ops = self.model.get_ops()

        self._figure.set_layout_engine("tight")
        self._plotter.plot(
            self._local_pc,
            self._figure,
            toolbar=self._toolbar,
        )

    def get_op(self) -> Op:
        """Get operation from panel."""
        op_cls = Op.instance(self.ops_select.currentItem().text())

        params_widget = self.params_entry.currentWidget()
        assert params_widget is not None

        params = {
            param: get_value(params_widget.findChild(QWidget, name=param))
            for param in op_cls.param_types()
        }

        return op_cls(self._ds_range.text(), **params)

    @Slot()
    def add_op(self) -> None:
        """Add operation from panel to the list of operations."""
        operation = self.get_op()

        self.model.accept_from_widget(operation.as_tuple)

    @Slot()
    def delete_op(self) -> None:
        """Delete operation from list of operations."""
        rows = [index.row() for index in self.ops_list.selectedIndexes()]
        self.model.remove_items(rows)

    @Slot()
    def apply_ops(self) -> None:
        """Store operations from panel on dataset."""
        if not self.orig_ds:
            return

        self.orig_ds.ops = self.model.get_ops()


if __name__ == "__main__":
    import sys

    import numpy as np
    from qtpy.QtWidgets import (
        QApplication,
    )

    from MDANSE_GUI.Tabs.Models.PlottingContext import SingleDataset

    app = QApplication(sys.argv)
    pc = PlottingContext()

    tmp_data = SingleDataset("Geoff", None, data=list(range(-5, 5)))
    tmp_data_2 = SingleDataset("Bob", None, data=np.random.random((10, 3)))
    pc.add_dataset(tmp_data)
    pc.add_dataset(tmp_data_2)

    root = PlotTransformWidget(None, plotting_context=pc)
    root.show()
    app.exec()
