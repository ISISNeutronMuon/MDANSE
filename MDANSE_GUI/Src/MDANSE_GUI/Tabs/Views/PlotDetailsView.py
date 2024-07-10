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

from qtpy.QtWidgets import QTreeView, QComboBox, QItemDelegate, QColorDialog
from qtpy.QtCore import Signal, Slot, Qt
from qtpy.QtGui import QColor

from MDANSE_GUI.Tabs.Models.PlottingContext import get_mpl_lines, get_mpl_markers


class ColourPicker(QItemDelegate):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def createEditor(self, parent, option, index):
        dialog = QColorDialog(parent)
        return dialog

    def setEditorData(self, editor, index):
        colour_string = index.data()
        color = QColor(colour_string)
        editor.setCurrentColor(color)

    def setModelData(self, editor, model, index):
        if editor.result() == QColorDialog.DialogCode.Accepted:
            color = editor.currentColor()
            colour_string = color.toRgb()
            model.setData(index, colour_string)


class MplStyleCombo(QItemDelegate):

    def __init__(self, *args, mpl_items=None, **kwargs) -> None:
        self._items = list([str(x) for x in mpl_items.keys()])
        super().__init__(*args, **kwargs)

    def setEditorData(self, editor, index):
        editor.blockSignals(True)
        text = index.model().data(index, Qt.DisplayRole)
        try:
            i = self._items.index(text)
        except ValueError:
            i = 0
        editor.setCurrentIndex(i)
        editor.blockSignals(False)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText())

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        li = []
        for item in self._items:
            li.append(item)
        combo.addItems(li)
        combo.currentIndexChanged.connect(self.currentIndexChanged)
        return combo

    @Slot()
    def currentIndexChanged(self):
        self.commitData.emit(self.sender())


class PlotDetailsView(QTreeView):
    details_changed = Signal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._delegates = {
            "colour": ColourPicker(),
            "line": MplStyleCombo(mpl_items=get_mpl_lines()),
            "marker": MplStyleCombo(mpl_items=get_mpl_markers()),
        }
        self.setItemDelegateForColumn(5, self._delegates["colour"])
        self.setItemDelegateForColumn(6, self._delegates["line"])
        self.setItemDelegateForColumn(7, self._delegates["marker"])

    def connect_to_visualiser(self, visualiser) -> None:
        """Connect to a visualiser.

        Parameters
        ----------
        visualiser : Action or TextInfo
            A visualiser to connect to this view.
        """
        self.details_changed.connect(visualiser.update_plot_details)
