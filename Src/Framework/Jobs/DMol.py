from MDANSE import REGISTRY
from MDANSE.Framework.Jobs.Discover import DiscoverConverter
        
class DMolConverter(DiscoverConverter):
    """
    Converts a DMol trajectory to a MMTK trajectory.
    """
    
    label = "DMol"
    
REGISTRY['dmol'] = DMolConverter
