from MDANSE import REGISTRY
from MDANSE.Framework.OutputVariables.IOutputVariable import IOutputVariable

class LineOutputVariable(IOutputVariable):
        
    _nDimensions = 1
    
REGISTRY["line"] = LineOutputVariable

