# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/AtomSelectionWidget.py
# @brief     Implements module/class/test AtomSelectionWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************
from qtpy.QtCore import Qt, QEvent
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
    QApplication
)
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class CheckableComboBox(QComboBox):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.view().viewport().installEventFilter(self)
        self.view().setAutoScroll(False)
        self.model().dataChanged.connect(self.update_line_edit)

    def eventFilter(self, a0, a1):
        if a0 == self.view().viewport() \
                and a1.type() == QEvent.MouseButtonRelease:
            idx = self.view().indexAt(a1.pos())
            item = self.model().item(idx.row())
            if item.checkState() == Qt.Checked:
                item.setCheckState(Qt.Unchecked)
            else:
                item.setCheckState(Qt.Checked)
            return True
        return super().eventFilter(a0, a1)

    def addItems(self, texts):
        for text in texts:
            self.addItem(text)

    def addItem(self, text):
        item = QStandardItem()
        item.setText(text)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        item.setData(Qt.Unchecked, Qt.CheckStateRole)
        self.model().appendRow(item)
        self.update_line_edit()

    def update_line_edit(self):
        vals = []
        for i in range(self.model().rowCount()):
            if self.model().item(i).checkState() == Qt.Checked:
                vals.append(self.model().item(i).text())
        self.lineEdit().setText(",".join(vals))


class HelperDialog(QDialog):
    """Generates a string that specifies the atom selection."""

    cbox_text = {
        "all": "All atoms:",
        "hs_on_heteroatom": "Hs on heteroatoms:",
        "primary_amine": "Primary amine groups:",
        "hydroxy": "Hydroxy groups:",
        "methyl": "Methyl groups:",
        "phosphate": "Phosphate groups:",
        "sulphate": "Sulphate groups:",
        "thiol": "Thiol groups:",
        "water": "Water molecules:",
        "element": "Elements:",
        "hs_on_element": "Hs on elements:",
        "index": "Indexes:",
        "invert": "Invert the selection:"
    }

    def __init__(self, selector, field, parent, *args, min_width=250, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setWindowTitle("Atom selection helper")
        self.min_width = min_width
        self.setMinimumWidth(self.min_width)
        self.selector = selector
        self.field = field
        self.full_settings = self.selector.full_settings
        match_exists = self.selector.match_exists

        layout = QVBoxLayout()

        select = QGroupBox("selection")
        select_layout = QVBoxLayout()
        invert = QGroupBox("inversion")
        invert_layout = QVBoxLayout()

        self.check_boxes = []
        self.combo_boxes = []

        for k, v in self.full_settings.items():

            if isinstance(v, bool):
                check_layout = QHBoxLayout()
                checkbox = QCheckBox()
                checkbox.setChecked(v)
                checkbox.setLayoutDirection(Qt.RightToLeft)
                label = QLabel(self.cbox_text[k])
                checkbox.setObjectName(k)
                checkbox.stateChanged.connect(self.update_setting)
                if not match_exists[k]:
                    checkbox.setEnabled(False)
                    label.setStyleSheet("color: grey;")
                self.check_boxes.append(checkbox)
                check_layout.addWidget(label)
                check_layout.addWidget(checkbox)
                if k == "invert":
                    invert_layout.addLayout(check_layout)
                else:
                    select_layout.addLayout(check_layout)

            elif isinstance(v, dict):
                combo_layout = QHBoxLayout()
                combo = CheckableComboBox()
                items = [i for i in v.keys() if match_exists[k][i]]
                combo.addItems(items)
                combo.setObjectName(k)
                combo.model().dataChanged.connect(self.update_setting)
                label = QLabel(self.cbox_text[k])
                if len(items) == 0:
                    combo.setEnabled(False)
                    label.setStyleSheet("color: grey;")
                self.combo_boxes.append(combo)
                combo_layout.addWidget(label)
                combo_layout.addWidget(combo)
                select_layout.addLayout(combo_layout)

        select.setLayout(select_layout)
        invert.setLayout(invert_layout)
        layout.addWidget(select)
        layout.addWidget(invert)

        bottom = QHBoxLayout()
        apply = QPushButton("Apply")
        close = QPushButton("Close")
        apply.clicked.connect(self.apply)
        close.clicked.connect(self.close)
        bottom.addWidget(apply)
        bottom.addWidget(close)

        layout.addLayout(bottom)
        self.setLayout(layout)

    def update_setting(self):
        for check_box in self.check_boxes:
            self.full_settings[check_box.objectName()] = check_box.isChecked()
        for combo_box in self.combo_boxes:
            model = combo_box.model()
            for i in range(model.rowCount()):
                self.full_settings[combo_box.objectName()][model.item(i).text()] \
                    = model.item(i).checkState() == Qt.Checked

    def apply(self):
        self.selector.update_settings(self.full_settings)
        self.field.setText(self.selector.settings_to_json())


class AtomSelectionWidget(WidgetBase):
    """The atoms selection widget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        default_value = '{"all": true}'
        self._value = default_value
        self.field = QLineEdit(default_value, self._base)
        self.selector = self._configurator.get_selector()
        self.helper = HelperDialog(self.selector, self.field, self.parent())
        helper_button = QPushButton("Atom selection helper", self._base)
        helper_button.clicked.connect(self.helper_dialog)
        self.field.textChanged.connect(self.check_valid_field)
        self._layout.addWidget(self.field)
        self._layout.addWidget(helper_button)
        self.update_labels()

    def helper_dialog(self, offset: int = 10) -> None:
        """Opens the helper dialog.

        Parameters
        ----------
        offset : int
            Number of pixels to place the helper dialog away from the
            parent.
        """
        self.helper.show()

        # place the helper to the left of the parent, if there is not
        # enough screen space put it to the right
        total_width = sum([
            screen.size().width() for screen in QApplication.instance().screens()])
        right = self.parent().pos().x() + self.parent().width() + offset
        left = self.parent().pos().x() - self.helper.min_width
        if right + self.helper.min_width + offset < total_width:
            self.helper.move(right, self.parent().pos().y())
        else:
            self.helper.move(left, self.parent().pos().y())

    def check_valid_field(self, value: str) -> None:
        """Changes the color of the field if the selector setting is
        not valid.

        Parameters
        ----------
        value : str
            The atom selection JSON string.
        """
        if self.selector.check_valid_json_settings(value):
            self.field.setStyleSheet("color: black;")
        else:
            self.field.setStyleSheet("color: red;")

    def get_widget_value(self) -> str:
        """
        Returns
        -------
        str
            The JSON selector setting.
        """
        selection_string = self.field.text()
        return selection_string
