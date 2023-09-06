from qtpy import QtCore, QtWidgets


class QTableViewWithoutRightClick(QtWidgets.QTableView):
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.RightButton:
            return
        return super(QTableViewWithoutRightClick, self).mousePressEvent(event)
