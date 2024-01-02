# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/DFTB.py
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


from MDANSE.Framework.Jobs.Forcite import ForciteConverter


class DFTBConverter(ForciteConverter):
    """
    Converts a DFTB trajectory to a HDF trajectory.
    """

    label = "DFTB"

    settings = collections.OrderedDict()
    settings["xtd_file"] = (
        "input_file",
        {
            "default": os.path.join(
                "..", "..", "..", "Data", "Trajectories", "DFTB", "H2O.xtd"
            ),
            "label": "The XTD file",
        },
    )
    settings["trj_file"] = (
        "input_file",
        {
            "default": os.path.join(
                "..", "..", "..", "Data", "Trajectories", "DFTB", "H2O.trj"
            ),
            "label": "The TRJ file",
        },
    )
    settings["fold"] = (
        "boolean",
        {"default": True, "label": "Fold coordinates in to box"},
    )
    settings["output_file"] = (
        "single_output_file",
        {"format": "hdf", "root": "xtd_file", "label": "Output file name"},
    )
