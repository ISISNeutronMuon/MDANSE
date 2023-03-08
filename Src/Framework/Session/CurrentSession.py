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


class CurrentSession():

    def __init__(self, fname = None):

        self.settings_dir = os.path.join(expanduser('~'), '.MDANSE')
    
    def loadSettings(self, fname = None):
        
        if fname is not None:
            source = json.load(fname)
