from MDANSE import REGISTRY
from MDANSE.Framework.InputData.InputFileData import InputFileData

class MviTraceInputData(InputFileData):
        
    extension = "mvi"
    
    def load(self):
        pass
        
    def close(self):
        pass   

REGISTRY["mvi_trace"] = MviTraceInputData
