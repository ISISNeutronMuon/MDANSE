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

# This dict will store a map between a filename extension and the actual reader corresponding to that file extension
REGISTERED_READERS = {}


def register_reader(typ):
    def decorator_register(cls):
        REGISTERED_READERS[typ] = cls
        return cls

    return decorator_register
