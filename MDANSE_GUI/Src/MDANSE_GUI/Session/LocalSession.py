import os

from qtpy.QtCore import QObject, Signal, Slot


class LocalSession(QObject):
    """Stores different parameters, and the state
    of the software.

    The intention is to have a single session that
    can be accessed by different tabs.

    At the moment, LocalSession is meant to be used
    for testing individual GUI components, and
    is largely a mock object.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parameters = {}
        self._paths = {}
        self._units = {}
        self._state = None
        self.populate_defaults()

    def populate_defaults(self):
        self._paths["root_directory"] = os.path.expanduser("~")
        #
        self._units["energy"] = "meV"
        self._units["time"] = "fs"
        self._units["distance"] = "Ang"

    def get_parameter(self, key: str) -> str:
        value = self._parameters.get(key, None)
        return value

    def get_path(self, key: str) -> str:
        value = self._paths.get(key, ".")
        return value

    def get_unit(self, key: str) -> str:
        value = self._units.get(key, "1")
        return value
