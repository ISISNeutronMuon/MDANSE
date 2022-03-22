# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/OutputVariables/LineOutputVariable.py
# @brief     Implements module/class/test LineOutputVariable
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-2021
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Framework.OutputVariables.IOutputVariable import IOutputVariable

class LineOutputVariable(IOutputVariable):
        
    _nDimensions = 1
    
REGISTRY["line"] = LineOutputVariable

