from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.DCDConverter import DCDConverter

class CHARMMConverter(DCDConverter):
    """
    Converts a CHARMM trajectory to a MMTK trajectory.
    """
    
    label = "CHARMM"

REGISTRY['charmm'] = CHARMMConverter
