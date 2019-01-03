# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Handlers/IHandler.py
# @brief     Implements module/class/test IHandler
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

class IHandler(object):
    '''
    Base class for the handlers of MDANSE logger.
    '''
    
    _registry = "handler"
