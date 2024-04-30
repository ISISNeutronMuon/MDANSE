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
import os
import json

from MDANSE.Chemistry.Databases import (
    AtomsDatabase,
    MoleculesDatabase,
    NucleotidesDatabase,
    ResiduesDatabase,
)

ATOMS_DATABASE = AtomsDatabase()

MOLECULES_DATABASE = MoleculesDatabase()

RESIDUES_DATABASE = ResiduesDatabase()

NUCLEOTIDES_DATABASE = NucleotidesDatabase()

with open(os.path.join(os.path.dirname(__file__), "residues_alt_names.json"), "r") as f:
    RESIDUE_ALT_NAMES = json.load(f)
