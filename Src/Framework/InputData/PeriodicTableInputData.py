from MDANSE import REGISTRY
from MDANSE.Framework.InputData.IInputData import IInputData

class PeriodicTableData(IInputData):
        
    extension = None

REGISTRY["periodic_table"] = PeriodicTableData
