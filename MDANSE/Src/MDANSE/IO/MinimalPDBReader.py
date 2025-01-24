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

from typing import List

import numpy as np
from ase.io import read as ase_read

from MDANSE.MLogging import LOG
from MDANSE.Framework.Units import measure
from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.MolecularDynamics.Configuration import (
    RealConfiguration,
    PeriodicRealConfiguration,
)
from MDANSE.MolecularDynamics.UnitCell import UnitCell

atom_line_records = {
    "record_name": (0, 6),
    "atom_number": (6, 11),
    "atom_name": (12, 16),
    "location": (16, 17),
    "residue_name": (17, 20),
    "chain_id": (21, 22),
    "residue_number": (22, 26),
    "insertion_code": (26, 27),
    "pos_x": (30, 38),
    "pos_y": (38, 46),
    "pos_z": (46, 54),
    "occupancy": (54, 60),
    "temperature_factor": (60, 66),
    "element_symbol": (76, 78),
    "charge": (78, 80),
}


def atom_line_slice(keyword: str) -> slice:
    try:
        limits = atom_line_records[keyword]
    except KeyError:
        return slice()
    else:
        return slice(limits[0], limits[1])


class MinimalPDBReader:

    def __init__(self, filename: str):

        self._unit_cell = None
        cell_params = self.find_unit_cell(filename)
        if len(cell_params) == 0:
            self.periodic = False
        else:
            try:
                ase_atoms = ase_read(filename, format="pdb", index=0)
                cell = ase_atoms.get_cell()
            except Exception:
                self.periodic = False
            else:
                self.periodic = True
                self._unit_cell = np.vstack(cell)
        self._chemical_system = ChemicalSystem(filename)
        atom_lines = self.find_atoms(filename)
        self.build_chemical_system(atom_lines)

    def find_unit_cell(self, filename: str, frame_number: int = 0):
        cell_found = False
        cell_params = []
        cell_line = ""
        fail_count = 0
        with open(filename, "r") as source:
            for line in source:
                if "CRYST" in line[0:5]:
                    cell_found = True
                    cell_line += line
                    break
                if "ENDMDL" in line[0:6]:
                    fail_count += 1
                if fail_count > 2:
                    cell_line = ""
                    cell_found = False
                    break
        if not cell_found:
            return cell_params
        cell_params = [float(x) for x in cell_line.split()[1:7]]
        return cell_params

    def find_atoms(self, filename: str, frame_number: int = 0):
        fail_count = 0
        result = []
        with open(filename, "r") as source:
            for line in source:
                if "ATOM" in line[0:5]:
                    result.append(line)
                elif "HETATM" in line[0:6]:
                    result.append(line)
                if "END" in line[0:3]:
                    fail_count += 1
                if fail_count > 0:
                    break
        return result

    def build_chemical_system(self, atom_lines: List[str]):
        """Build the chemical system.

        Returns:
            MDANSE.Chemistry.ChemicalSystem.ChemicalSystem: the chemical system
        """

        coordinates = []
        element_slice = atom_line_slice("element_symbol")
        name_slice = atom_line_slice("atom_name")
        posx_slice = atom_line_slice("pos_x")
        posy_slice = atom_line_slice("pos_y")
        posz_slice = atom_line_slice("pos_z")
        residue_slice = atom_line_slice("residue_name")
        residue_number_slice = atom_line_slice("residue_number")

        element_list = []
        name_list = []
        label_dict = {}
        clusters = {}

        for atom_number, atom_line in enumerate(atom_lines):
            chemical_element = atom_line[element_slice].strip()
            atom_name = atom_line[name_slice]
            processed_atom_name = atom_name[:2].strip()
            if len(processed_atom_name) == 2:
                if processed_atom_name[0].isnumeric():
                    processed_atom_name = processed_atom_name[1].upper()
                else:
                    processed_atom_name = (
                        processed_atom_name[0].upper() + processed_atom_name[1].lower()
                    )
            if len(chemical_element) == 2:
                chemical_element = (
                    chemical_element[0].upper() + chemical_element[1].lower()
                )
            backup_element = atom_line.rstrip().split()[-1]
            backup_element2 = atom_line.split()[-2].strip()
            if atom_name[-2:].isnumeric():
                backup_element3 = atom_name[0]
            else:
                backup_element3 = "fail"
            if backup_element in ATOMS_DATABASE.atoms:
                element_list.append(backup_element)
            elif backup_element2 in ATOMS_DATABASE.atoms:
                element_list.append(backup_element2)
            elif backup_element3 in ATOMS_DATABASE.atoms:
                element_list.append(backup_element3)
            elif chemical_element in ATOMS_DATABASE.atoms:
                element_list.append(chemical_element)
            elif processed_atom_name in ATOMS_DATABASE.atoms:
                element_list.append(processed_atom_name)
            else:
                LOG.warning(f"Dummy atom introduced from line {atom_line}")
                element_list.append("Du")
            x, y, z = (
                atom_line[posx_slice],
                atom_line[posy_slice],
                atom_line[posz_slice],
            )
            coordinates.append([float(aaa) for aaa in [x, y, z]])
            residue_name = atom_line[residue_slice]
            if residue_name not in label_dict.keys():
                label_dict[residue_name] = []
            label_dict[residue_name].append(atom_number)
            name_list.append(atom_name.strip())
            residue_number_string = atom_line[residue_number_slice]
            try:
                residue_number = int(residue_number_string)
            except ValueError:
                try:
                    residue_number = int(residue_number_string, base=16)
                except ValueError:
                    continue
            if (residue_name, residue_number) in clusters.keys():
                clusters[(residue_name, residue_number)].append(atom_number)
            else:
                clusters[(residue_name, residue_number)] = [atom_number]
        self._chemical_system.initialise_atoms(element_list, name_list)
        self._chemical_system.add_labels(label_dict)
        self._chemical_system.add_clusters(clusters.values())
