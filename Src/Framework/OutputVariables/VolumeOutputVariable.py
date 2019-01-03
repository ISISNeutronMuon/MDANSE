# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/OutputVariables/VolumeOutputVariable.py
# @brief     Implements module/class/test VolumeOutputVariable
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Framework.OutputVariables.IOutputVariable import IOutputVariable

class VolumeOutputVariable(IOutputVariable):
        
    _nDimensions = 3
    
REGISTRY["volume"] = VolumeOutputVariable
    
