from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.Forcite import ForciteConverter
        
class DFTBConverter(ForciteConverter):
    """
    Converts a DFTB trajectory to a MMTK trajectory.
    """
    
    label = "DFTB"
    
REGISTRY['dftb'] = DFTBConverter
