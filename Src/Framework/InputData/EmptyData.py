from MDANSE import REGISTRY
from MDANSE.Framework.InputData.IInputData import IInputData

class EmptyData(IInputData):

    extension = None
    
REGISTRY["empty_data"] = EmptyData    
