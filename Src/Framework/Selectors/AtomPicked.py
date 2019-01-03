from MDANSE import REGISTRY
from MDANSE.Framework.Selectors.AtomIndex import AtomIndex
        
class AtomPicked(AtomIndex):

    section = "miscellaneous"
    
REGISTRY["atom_picked"] = AtomPicked

