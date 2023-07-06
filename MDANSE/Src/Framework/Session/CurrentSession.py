# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Session/CurrentSession.py
# @brief     Beginning of the user session definition
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

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
            'raw_files' : 'raw_data/',
            'trajectories' : 'mdanse_trajectories/',
            'results' : 'results/'
        }


class CurrentSession():

    def __init__(self, fname = None):

        self.settings_dir = os.path.join(expanduser('~'), '.MDANSE')
        if fname is not None:
            self.loadSettings(fname)
    
    def loadSettings(self, fname = None):
        
        if fname is not None:
            source = json.load(fname)
