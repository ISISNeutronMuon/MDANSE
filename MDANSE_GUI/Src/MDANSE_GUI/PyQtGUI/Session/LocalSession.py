
from qtpy.QtCore import QObject, Signal, Slot


class LocalSession(QObject):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    