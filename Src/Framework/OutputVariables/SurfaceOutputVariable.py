from MDANSE import REGISTRY
from MDANSE.Framework.OutputVariables.IOutputVariable import IOutputVariable

class SurfaceOutputVariable(IOutputVariable):
        
    _nDimensions = 2
    
REGISTRY["surface"] = SurfaceOutputVariable
    
