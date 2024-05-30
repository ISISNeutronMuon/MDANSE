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
from typing import Union, Iterator
from itertools import count, groupby
from qtpy.QtCore import Qt, QEvent, Slot, QObject
from qtpy.QtGui import QStandardItem
from qtpy.QtWidgets import (
    QComboBox,
    QLineEdit,
    QPushButton,
    QDialog,
    QCheckBox,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QTextEdit,
    QWidget,
)
from MDANSE.Framework.AtomSelector import Selector
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from MDANSE_GUI.Tabs.Visualisers.View3D import View3D
from MDANSE_GUI.MolecularViewer.MolecularViewer import MolecularViewerWithPicking
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData


class CheckableComboBox(QComboBox):
    """A multi-select checkable combobox"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.view().viewport().installEventFilter(self)
        self.view().setAutoScroll(False)
        # it's faster to access the items through this python list than
        # through self.model().item(idx)
        self._items = []
        self.addItem("select all")
        self.lineEdit().setText("")

    def eventFilter(self, a0: Union[QObject, None], a1: Union[QEvent, None]) -> bool:
        """Updates the check state of the items and the lineEdit.

        Parameters
        ----------
        a0 : QObject or None
            A QT object.
        a1 : QEvent or None
            A QT event.
        """
        if a0 == self.view().viewport() and a1.type() == QEvent.MouseButtonRelease:
            idx = self.view().indexAt(a1.pos())
            item = self.model().item(idx.row())

            if item.checkState() == Qt.Checked:
                check_uncheck = Qt.Unchecked
            else:
                check_uncheck = Qt.Checked

            if idx.row() == 0:
                # need to block signals temporarily otherwise as we
                # need to make a change on all the items which could
                # cause alot of signals to be emitted
                self.model().blockSignals(True)
                for i in self.getItems():
                    i.setCheckState(check_uncheck)
                self.model().blockSignals(False)
                item.setCheckState(check_uncheck)
            else:
                item.setCheckState(check_uncheck)
                self.update_all_selected()

            self.update_line_edit()
            return True

        return super().eventFilter(a0, a1)

    def update_all_selected(self):
        """check/uncheck select all since everything is/isn't selected."""
        if all([i.checkState() == Qt.Checked for i in self.getItems()]):
            self.model().item(0).setCheckState(Qt.Checked)
        else:
            self.model().item(0).setCheckState(Qt.Unchecked)

    def addItems(self, texts: list[str]) -> None:
        """
        Parameters
        ----------
        texts : list[str]
            A list of items texts to add.
        """
        for text in texts:
            self.addItem(text)

    def configure_using_default(self):
        """This is too complex to have a default value"""

    def addItem(self, text: str) -> None:
        """
        Parameters
        ----------
        text : str
            The text of the item to add.
        """
        item = QStandardItem()
        item.setText(text)
        item.setEnabled(True)
        item.setCheckable(True)
        self.model().appendRow(item)
        self._items.append(item)

    def getItems(self) -> Iterator[QStandardItem]:
        """
        Yields
        ------
        QStandardItem
            Yields the items in the combobox except for the zeroth
            item because that is the select all item.
        """
        for i in range(self.model().rowCount()):
            if i == 0:  # skips the select all item
                continue
            yield self._items[i]

    def check_items_castable_to_int(self) -> bool:
        """
        Returns
        -------
        bool
            Returns true if the text of all items can be cast to int.
        """
        try:
            [int(i.text()) for i in self.getItems()]
            return True
        except ValueError:
            return False

    def update_line_edit(self) -> None:
        """Updates the lineEdit text of the combobox."""
        vals = []
        for item in self.getItems():
            if item.checkState() == Qt.Checked:
                vals.append(item.text())
        if self.check_items_castable_to_int():
            vals = [int(i) for i in vals]
            # changes for example 1,2,3,5,6,7,9,10 -> 1-3,5-7,9-10
            gr = (list(x) for _, x in groupby(vals, lambda x, c=count(): next(c) - x))
            text = ",".join("-".join(map(str, (g[0], g[-1])[: len(g)])) for g in gr)
            self.lineEdit().setText(text)
        else:
            self.lineEdit().setText(",".join(vals))


class SelectionHelper(QDialog):
    """Generates a string that specifies the atom selection.

    Attributes
    ----------
    _helper_title : str
        The title of the helper dialog window.
    _cbox_text : dict
        The dictionary that maps the selector settings to text used in
        the helper dialog.
    """

    _helper_title = "Atom selection helper"
    _cbox_text = {
        "all": "All atoms (excl. dummy atoms):",
        "dummy": "All dummy atoms:",
        "hs_on_heteroatom": "Hs on heteroatoms:",
        "primary_amine": "Primary amine groups:",
        "hydroxy": "Hydroxy groups:",
        "methyl": "Methyl groups:",
        "phosphate": "Phosphate groups:",
        "sulphate": "Sulphate groups:",
        "thiol": "Thiol groups:",
        "water": "Water molecules:",
        "hs_on_element": "Hs on elements:",
        "element": "Elements:",
        "name": "Atom name:",
        "fullname": "Atom fullname:",
        "index": "Indexes:",
    }

    def __init__(
        self,
        selector: Selector,
        traj_data: tuple[str, HDFTrajectoryInputData],
        field: QLineEdit,
        parent,
        *args,
        **kwargs,
    ):
        """
        Parameters
        ----------
        selector : Selector
            The MDANSE selector initialized with the current chemical
            system.
        traj_data : tuple[str, HDFTrajectoryInputData]
            A tuple of the trajectory data used to load the 3D viewer.
        field : QLineEdit
            The QLineEdit field that will need to be updated when
            applying the setting.
        """
        super().__init__(parent, *args, **kwargs)
        self.setWindowTitle(self._helper_title)

        self.selector = selector
        self._field = field
        self.full_settings = self.selector.full_settings

        self.selection_textbox = QTextEdit()
        self.selection_textbox.setReadOnly(True)

        mol_view = MolecularViewerWithPicking()
        mol_view.picked_atoms_changed.connect(self.update_from_3d_view)
        self.view_3d = View3D(mol_view)
        self.view_3d.update_panel(traj_data)

        layouts = self.create_layouts()

        bottom = QHBoxLayout()
        for button in self.create_buttons():
            bottom.addWidget(button)

        layouts[-1].addLayout(bottom)

        helper_layout = QHBoxLayout()
        for layout in layouts:
            helper_layout.addLayout(layout)

        self.setLayout(helper_layout)
        self.update_others()

        self.all_selection = True

    def closeEvent(self, a0):
        """Hide the window instead of closing. Some issues occur in the
        3D viewer when it is closed and then reopened.
        """
        a0.ignore()
        self.hide()

    def create_buttons(self) -> list[QPushButton]:
        """
        Returns
        -------
        list[QPushButton]
            List of push buttons to add to the last layout from
            create_layouts.
        """
        apply = QPushButton("Use Setting")
        reset = QPushButton("Reset")
        close = QPushButton("Close")
        apply.clicked.connect(self.apply)
        reset.clicked.connect(self.reset)
        close.clicked.connect(self.close)
        return [apply, reset, close]

    def create_layouts(self) -> list[QVBoxLayout]:
        """
        Returns
        -------
        list[QVBoxLayout]
            List of QVBoxLayout to add to the helper layout.
        """
        layout_3d = QVBoxLayout()
        layout_3d.addWidget(self.view_3d)

        left = QVBoxLayout()
        for widget in self.left_widgets():
            left.addWidget(widget)

        right = QVBoxLayout()
        for widget in self.right_widgets():
            right.addWidget(widget)

        return [layout_3d, left, right]

    def right_widgets(self) -> list[QWidget]:
        """
        Returns
        -------
        list[QWidget]
            List of QWidgets to add to the right layout from
            create_layouts.
        """
        return [self.selection_textbox]

    def left_widgets(self) -> list[QWidget]:
        """
        Returns
        -------
        list[QWidget]
            List of QWidgets to add to the left layout from
            create_layouts.
        """
        match_exists = self.selector.match_exists

        select = QGroupBox("selection")
        select_layout = QVBoxLayout()

        self.check_boxes = []
        self.combo_boxes = []

        for k, v in self.full_settings.items():

            if isinstance(v, bool):
                check_layout = QHBoxLayout()
                checkbox = QCheckBox()
                checkbox.setChecked(v)
                checkbox.setLayoutDirection(Qt.RightToLeft)
                label = QLabel(self._cbox_text[k])
                checkbox.setObjectName(k)
                checkbox.stateChanged.connect(self.update_others)
                if not match_exists[k]:
                    checkbox.setEnabled(False)
                    label.setStyleSheet("color: grey;")
                self.check_boxes.append(checkbox)
                check_layout.addWidget(label)
                check_layout.addWidget(checkbox)
                select_layout.addLayout(check_layout)

            elif isinstance(v, dict):
                combo_layout = QHBoxLayout()
                combo = CheckableComboBox()
                items = [str(i) for i in v.keys() if match_exists[k][i]]
                # we blocksignals here as there can be some
                # performance issues with a large number of items
                combo.model().blockSignals(True)
                combo.addItems(items)
                combo.model().blockSignals(False)
                combo.setObjectName(k)
                combo.model().dataChanged.connect(self.update_others)
                label = QLabel(self._cbox_text[k])
                if len(items) == 0:
                    combo.setEnabled(False)
                    label.setStyleSheet("color: grey;")
                self.combo_boxes.append(combo)
                combo_layout.addWidget(label)
                combo_layout.addWidget(combo)
                select_layout.addLayout(combo_layout)

        select.setLayout(select_layout)
        return [select]

    def update_others(self) -> None:
        """Using the checkbox and combobox widgets: update the settings,
        get the selection and update the textedit box with details of
        the current selection and the 3d view to match the selection.
        """
        for check_box in self.check_boxes:
            self.full_settings[check_box.objectName()] = check_box.isChecked()
        for combo_box in self.combo_boxes:
            for item in combo_box.getItems():
                txt = item.text()
                if combo_box.objectName() == "index":
                    key = int(txt)
                else:
                    key = txt
                self.full_settings[combo_box.objectName()][key] = (
                    item.checkState() == Qt.Checked
                )

        self.selector.update_settings(self.full_settings)
        idxs = self.selector.get_idxs()
        self.view_3d._viewer.change_picked(idxs)
        self.update_selection_textbox(idxs)

    def update_from_3d_view(self, selection: set[int]) -> None:
        """A selection/deselection was made in the 3d view, update the
        check_boxes, combo_boxes and textbox.

        Parameters
        ----------
        selection : set[int]
            Selection indexes from the 3d view.
        """
        self.selector.update_with_idxs(selection)
        self.full_settings = self.selector.full_settings
        self.update_selection_widgets()
        self.update_selection_textbox(self.selector.get_idxs())

    def update_selection_widgets(self) -> None:
        """Updates the selection widgets so that it matches the full
        setting.
        """
        for check_box in self.check_boxes:
            check_box.blockSignals(True)
            if self.full_settings[check_box.objectName()]:
                check_box.setCheckState(Qt.Checked)
            else:
                check_box.setCheckState(Qt.Unchecked)
            check_box.blockSignals(False)
        for combo_box in self.combo_boxes:
            combo_box.model().blockSignals(True)
            for item in combo_box.getItems():
                txt = item.text()
                if combo_box.objectName() == "index":
                    key = int(txt)
                else:
                    key = txt
                if self.full_settings[combo_box.objectName()][key]:
                    item.setCheckState(Qt.Checked)
                else:
                    item.setCheckState(Qt.Unchecked)
            combo_box.update_all_selected()
            combo_box.update_line_edit()
            combo_box.model().blockSignals(False)

    def update_selection_textbox(self, idxs: set[int]) -> None:
        """Update the selection textbox.

        Parameters
        ----------
        idxs : set[int]
            The selected indexes.
        """
        num_sel = len(idxs)
        text = [f"Number of atoms selected:\n{num_sel}\n\nSelected atoms:\n"]
        atoms = self.selector.system.atom_list
        for idx in idxs:
            text.append(f"{idx}  ({atoms[idx].full_name})\n")
        self.selection_textbox.setText("".join(text))

    def apply(self) -> None:
        """Set the field of the AtomSelectionWidget to the currently
        chosen setting in this widget.
        """
        self.selector.update_settings(self.full_settings)
        self._field.setText(self.selector.settings_to_json())

    def reset(self) -> None:
        """Resets the helper to the default state."""
        self.selector.reset_settings()
        self.selector.settings["all"] = self.all_selection
        self.full_settings = self.selector.full_settings
        self.update_selection_widgets()
        idxs = self.selector.get_idxs()
        self.view_3d._viewer.change_picked(idxs)
        self.update_selection_textbox(idxs)


class AtomSelectionWidget(WidgetBase):
    """The atoms selection widget."""

    _push_button_text = "Atom selection helper"
    _default_value = '{"all": true}'
    _tooltip_text = "Specify which atoms will be used in the analysis. The input is a JSON string, and can be created using the helper dialog."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._value = self._default_value
        self._field = QLineEdit(self._default_value, self._base)
        self._field.setPlaceholderText(self._default_value)
        self._field.setMaxLength(2147483647)  # set to the largest possible
        self._field.textChanged.connect(self.updateValue)
        traj_config = self._configurator._configurable[
            self._configurator._dependencies["trajectory"]
        ]
        traj_filename = traj_config["filename"]
        hdf_traj = traj_config["hdf_trajectory"]
        self.helper = self.create_helper((traj_filename, hdf_traj))
        helper_button = QPushButton(self._push_button_text, self._base)
        helper_button.clicked.connect(self.helper_dialog)
        self._layout.addWidget(self._field)
        self._layout.addWidget(helper_button)
        self.update_labels()
        self.updateValue()
        self._field.setToolTip(self._tooltip_text)

    def create_helper(
        self, traj_data: tuple[str, HDFTrajectoryInputData]
    ) -> SelectionHelper:
        """
        Parameters
        ----------
        traj_data : tuple[str, HDFTrajectoryInputData]
            A tuple of the trajectory data used to load the 3D viewer.

        Returns
        -------
        SelectionHelper
            Create and return the selection helper QDialog.
        """
        selector = self._configurator.get_selector()
        return SelectionHelper(selector, traj_data, self._field, self._base)

    @Slot()
    def helper_dialog(self) -> None:
        """Opens the helper dialog."""
        if self.helper.isVisible():
            self.helper.close()
        else:
            self.helper.show()

    def get_widget_value(self) -> str:
        """
        Returns
        -------
        str
            The JSON selector setting.
        """
        selection_string = self._field.text()
        if len(selection_string) < 1:
            self._empty = True
            return self._default_value
        else:
            self._empty = False
        return selection_string
