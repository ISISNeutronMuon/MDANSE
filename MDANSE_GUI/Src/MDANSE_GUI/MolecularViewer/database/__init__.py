#    This file is part of MDANSE_GUI.
#
#    MDANSE_GUI is free software: you can redistribute it and/or modify
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
import yaml


def load_database(database_path):
    """Load in memory the database YAML file"""

    # Load the chemical elements database
    with open(database_path, "r") as fin:
        try:
            database = yaml.safe_load(fin)
        except yaml.YAMLError as exc:
            print(exc)

    return database


_libdir, _ = os.path.split(__file__)
CHEMICAL_ELEMENTS = load_database(os.path.join(_libdir, "chemical_elements.yml"))
STANDARD_RESIDUES = load_database(os.path.join(_libdir, "residues.yml"))
