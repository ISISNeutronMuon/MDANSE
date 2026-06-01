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
from __future__ import annotations

import collections

from MDANSE.Framework.Converters.Forcite import Forcite
from MDANSE.Framework.Parameters import (
    AtomMapping,
    Boolean,
    OutputTrajectory,
    PathParam,
    to_class,
)
from MDANSE.Framework.Parsers import TrjFile, XTDFile


class DFTB(Forcite):
    """Converts a DFTB trajectory to an MDT trajectory."""

    label = "DFTB"

    xtd_file = PathParam[XTDFile](
        mode="r",
        extensions={"XTD file": "*.xtd"},
        label="The XTD file.",
        on_set=to_class(XTDFile),
    )
    trj_file = PathParam[TrjFile](
        mode="r",
        extensions={"TRJ file": "*.trj"},
        label="The TRJ file.",
        on_set=to_class(TrjFile),
    )
    atom_aliases = AtomMapping(
        depends={"trajectory": "xtd_file"},
        label="Atom mapping",
        default={},
    )
    fold = Boolean(label="Fold coordinates into box")
    output_files = OutputTrajectory()
    settings = collections.OrderedDict()
