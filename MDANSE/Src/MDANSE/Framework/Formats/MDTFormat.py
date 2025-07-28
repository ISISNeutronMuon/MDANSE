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

from MDANSE.Framework.Formats.HDFFormat import HDFFormat


class MDTFormat(HDFFormat):
    """
    This class handles the writing of output variables in MDT file format.

    Attributes
    ----------
    extension : str
        File extension used when writing.
    extensions : list[str]
        Other possible extensions of this file format.
    """

    extension = ".mdt"
    extensions = [".mdt"]
