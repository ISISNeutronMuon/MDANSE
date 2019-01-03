from MDANSE import REGISTRY
from MDANSE.Framework.OutputVariables.IOutputVariable import IOutputVariable

class VolumeOutputVariable(IOutputVariable):
        
    _nDimensions = 3
    
REGISTRY["volume"] = VolumeOutputVariable
    
