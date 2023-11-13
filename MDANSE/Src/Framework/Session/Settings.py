# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Session/Settings.py
# @brief     Beginning of the user session definition
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Maciej Bartkowiak
#
# **************************************************************************

import json


class CascadingSettings:
    """Stores any kind of settings in a cascading way.
    The global settings can be retrieved from children,
    or masked by children using new values.
    This means that an instance of settings will first
    check its own dictionary for a key, and failing to find it
    will advance to its parent.
    """

    def __init__(self, *args, **kwargs):
        self._parent = None
        self._settings = {}
        self._current_filename = None

    def __getitem__(self, key: str):
        value = self._settings.get(key, None)
        if value is None:
            value = self._parent[key]
        return value

    def __setitem__(self, key: str, value):
        self._settings[key] = value

    def __eq__(self, another):
        if not set(self._settings.keys()) == set(another._settings.keys()):
            return False
        for key, value in self._settings.items():
            if not value == another._settings[key]:
                return False
        return True

    def __len__(self):
        return len(self._settings)

    def parent(self):
        if self._parent is not None:
            return self._parent.parent()
        return self

    def serialize(self, fname: str):
        with open(fname, "w") as target:
            json.dump(self._settings, target)
        self.currentFilename = fname

    def load_from_file(self, fname: str):
        with open(fname, "r") as source:
            try:
                contents = json.load(source)
            except json.JSONDecodeError:
                self._settings = {}
            else:
                self._settings = contents
        self.currentFilename = fname

    def writeChanges(self):
        if self.currentFilename is not None:
            self.serialize(self.currentFilename)

    def produce_child(self):
        child = CascadingSettings()
        child._parent = self
        return child

    @property
    def currentFilename(self):
        return self._current_filename

    @currentFilename.setter
    def currentFilename(self, fname: str):
        self._current_filename = fname
