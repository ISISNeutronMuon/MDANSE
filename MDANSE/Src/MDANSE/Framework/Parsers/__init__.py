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

from contextlib import suppress

with suppress(ImportError):
    from .ASE import ASEParser as ASEParser

from .CASTEP_MD import CASTEPMDFile as CASTEPMDFile
from .CP2K_Cell import CP2KCellFile as CP2KCellFile
from .DCDFile import DCDFile as DCDFile
from .DLPoly import FieldFile as DLPField
from .DLPoly import HistoryFile as DLPHistory
from .FortranUnformat import binary_file_reader as binary_file_reader
from .LAMMPS import LAMMPScustom as LAMMPScustom
from .LAMMPS import LAMMPSReader as LAMMPSReader
from .LAMMPS import LAMMPSxyz as LAMMPSxyz
from .LAMMPSConfig import LAMMPSConfigFile as LAMMPSConfigFile
from .pdb import PDBFile as PDBFile
from .trj import TrjFile as TrjFile
from .XDatCar import XDATCARFile as XDATCARFile
from .xtd import XTDFile as XTDFile
from .xyz import XYZFile as XYZFile
