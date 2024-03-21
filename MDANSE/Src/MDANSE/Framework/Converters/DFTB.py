# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      MDANSE/Framework/Jobs/DFTB.py
# @brief     Implements module/class/test DFTB
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import os


from MDANSE.Framework.Converters.Forcite import Forcite


class DFTB(Forcite):
    """
    Converts a DFTB trajectory to a HDF trajectory.
    """

    label = "DFTB"

    settings = collections.OrderedDict()
    settings["xtd_file"] = (
        "XTDFileConfigurator",
        {
            "wildcard": "XTD files (*.xtd)|*.xtd|All files|*",
            "default": "INPUT_FILENAME.xtd",
            "label": "The XTD file",
        },
    )
    settings["trj_file"] = (
        "InputFileConfigurator",
        {
            "wildcard": "TRJ files (*.trj)|*.trj|All files|*",
            "default": "INPUT_FILENAME.trj",
            "label": "The TRJ file",
        },
    )
    settings["atom_aliases"] = (
        "AtomMappingConfigurator",
        {
            "default": "{}",
            "label": "Atom mapping",
            "dependencies": {"input_file": "xtd_file"},
        },
    )
    settings["fold"] = (
        "BooleanConfigurator",
        {"default": True, "label": "Fold coordinates in to box"},
    )
    settings["output_file"] = (
        "OutputTrajectoryConfigurator",
        {
            "formats": ["MDTFormat"],
            "root": "xtd_file",
            "label": "MDANSE trajectory (filename, format)",
        },
    )
