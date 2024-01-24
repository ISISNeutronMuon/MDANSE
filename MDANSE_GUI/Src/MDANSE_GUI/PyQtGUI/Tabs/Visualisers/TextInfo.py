from qtpy.QtCore import QObject, Slot, Signal
from qtpy.QtWidgets import QPushButton, QTextEdit, QWidget, QFileDialog


class TextInfo(QTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @Slot(object)
    def visualise_item(self, incoming: object):
        self.setText(incoming)
