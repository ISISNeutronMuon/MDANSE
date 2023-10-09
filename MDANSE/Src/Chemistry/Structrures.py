from io import StringIO

import numpy as np
from rdkit.Chem.rdchem import Mol
from rdkit.Chem.rdmolops import SanitizeMol
from rdkit.Chem.rdmolops import GetMolFrags
from rdkit.Chem.rdmolfiles import MolFromPDBBlock

from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem
from MDANSE.MolecularDynamics.Trajectory import Trajectory
from MDANSE.IO.PDB import PDBFile


class DummyStringIO(StringIO):
    def close(self):
        pass

    def _close(self):
        super(DummyStringIO, self).close()


class Topology:
    def __init__(
        self, trajectory: Trajectory = None, chem_system: ChemicalSystem = None
    ) -> None:
        self._trajectory = trajectory
        self._chem_system = chem_system

    def scan_trajectory_frame(self, frame_num: int = 0):
        unit_cell = self._chem_system.configuration.unit_cell
        temp = unit_cell.abc_and_angles
        abc = temp[0:3]  # lattice constants in nm
        angles = temp[3:6]  # lattice angles in degrees
        lattice_data = {
            "a": round(abc[0] * 10.0, 3),
            "b": round(abc[1] * 10.0, 3),
            "c": round(abc[2] * 10.0, 3),
            "alpha": round(angles[0], 3),
            "beta": round(angles[1], 3),
            "gamma": round(angles[2], 3),
            "space_group": "",
            "z": "",
        }
        buffer = DummyStringIO()
        temp_pdb = PDBFile(buffer, mode="w")
        # temp_pdb.writeLine('TITLE')
        # temp_pdb.writeLine('AUTHOR')
        temp_pdb.writeLine("CRYST1", lattice_data)
        positions = (
            self._trajectory.trajectory.coordinates(frame_num) * 10.0
        )  # Angstroms, not nm
        atoms = self._chem_system.atom_list
        for natom in range(self._chem_system._total_number_of_atoms):
            atom = atoms[natom]
            atom_data = {
                "position": positions[natom],
                "serial_number": atom.index,
                "name": atom.name,
                "occupancy": 1.0,
                "element": atom.symbol,
                "charge": "",  # putting a number here makes it fail!
            }
            try:
                temp_pdb.writeLine("ATOM", atom_data)
            except:
                print(atom_data)
        temp_pdb.close()
        mol_object = MolFromPDBBlock(buffer.getvalue())
        buffer._close()
        return mol_object
