#    This file is part of MDANSE.
#
#    MDANSE is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

from io import StringIO

from rdkit.Chem.inchi import MolToInchi
from rdkit.Chem.rdmolfiles import MolFromPDBBlock
from rdkit.Chem import rdDetermineBonds


from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem
from MDANSE.MolecularDynamics.Trajectory import Trajectory
from MDANSE.IO.PDB import PDBFile


class DummyStringIO(StringIO):
    def close(self):
        pass

    def _close(self):
        super(DummyStringIO, self).close()


class MoleculeTester:
    """This is a wrapper that can be attached to an MDANSE ChemicalEntity
    in order to convert it into a PDB string buffer and feed it into
    a library that can identify molecules.
    """

    def __init__(self, chemical_entity, coordinates):
        self.chemical_entity = chemical_entity
        self.coordinates = coordinates
        self.molecule_object = None
        self.molecule_string = None

    def identify_molecule(self, frame_num: int = 0) -> str:
        positions = self.coordinates
        buffer = DummyStringIO()
        temp_pdb = PDBFile(buffer, mode="w")
        for natom, atom in enumerate(self.chemical_entity.atom_list):
            coords = positions[natom] * 10.0
            atom_data = {
                "position": coords,
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
        if mol_object is None:
            return ""
        try:
            rdDetermineBonds.DetermineBonds(mol_object, charge=0)
        except ValueError:
            self.molecule_string = ""
        else:
            self.molecule_string = MolToInchi(mol_object)
        self.molecule_object = mol_object
        return self.molecule_string


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
