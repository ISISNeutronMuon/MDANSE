# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/pygenplot/__init__.py
# @brief     molecular viewer code from the "waterstay" project
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2023-now
# @authors   Eric Pellegrini
#
# **************************************************************************

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
