from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.DCDConverter import DCDConverter

class NAMDConverter(DCDConverter):
    """
    Converts a NAMD trajectory to a MMTK trajectory.
    """
    
    label = "NAMD"

REGISTRY['namd'] = NAMDConverter
