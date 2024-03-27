#    This file is part of MDANSE.
#
#    MDANSE is free software: you can redistribute it and/or modify
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
# Copyright (C)  Institut Laue Langevin 2013-now
# Copyright (C)  ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# Authors:    Scientific Computing Group at ILL (see AUTHORS)

import os
from os.path import expanduser
import json
from abc import ABC, abstractmethod


class AbstractSession(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def set_directories(self):
        raise NotImplementedError

    def load_session(self, fname: str):
        raise NotImplementedError


class SessionSettings(AbstractSession):
    def __init__(self):
        super().__init__()
        self.main_path = "."

    def create_structured_project(self):
        self.relative_paths = {
            "raw_files": "raw_data/",
            "trajectories": "mdanse_trajectories/",
            "results": "results/",
        }


class CurrentSession:
    def __init__(self, fname=None):
        self.settings_dir = os.path.join(expanduser("~"), ".MDANSE")
        if fname is not None:
            self.loadSettings(fname)

    def loadSettings(self, fname=None):
        if fname is not None:
            source = json.load(fname)
