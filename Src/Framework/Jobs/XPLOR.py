from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.DCDConverter import DCDConverter

class XPLORConverter(DCDConverter):
    """
    Converts an Xplor trajectory to a MMTK trajectory.
    """
    
    label = "XPLOR"

REGISTRY['xplor'] = XPLORConverter
