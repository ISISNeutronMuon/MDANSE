
import numpy as np
from rdkit.Chem.rdchem import Mol
from rdkit.Chem.rdmolops import SanitizeMol
from rdkit.Chem.rdmolops import GetMolFrags

from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem
from MDANSE.MolecularDynamics.Trajectory import Trajectory

class Topology():

    def __init__(self, trajectory: Trajectory = None, chem_system: ChemicalSystem = None) -> None:
        
        self._trajectory = trajectory
        self._chem_system = chem_system