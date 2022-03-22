# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Core/Error.py
# @brief     Implements module/class/test Error
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-2021
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

class Error(Exception):
    '''
    Base class for handling exception occurring in MDANSE.
    
    Any exception defined in MDANSE should derive from it in order to be properly handled
    in the GUI application.
    '''
    
    def __init__(self, msg=None):
            
            self._msg = msg
            
    def __str__(self):
                
        return repr(self._msg)
    
