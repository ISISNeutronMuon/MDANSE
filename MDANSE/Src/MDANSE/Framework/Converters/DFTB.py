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
        {"default": False, "label": "Fold coordinates into box"},
    )
    settings["output_file"] = (
        "OutputTrajectoryConfigurator",
        {
            "formats": ["MDTFormat"],
            "root": "xtd_file",
            "label": "MDANSE trajectory (filename, format)",
        },
    )
