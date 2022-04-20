# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/InputData/MVITraceInputData.py
# @brief     Implements module/class/test MVITraceInputData
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Framework.InputData.InputFileData import InputFileData

class MviTraceInputData(InputFileData):
        
    extension = "mvi"
    
    def load(self):
        pass
        
    def close(self):
        pass   

REGISTRY["mvi_trace"] = MviTraceInputData
