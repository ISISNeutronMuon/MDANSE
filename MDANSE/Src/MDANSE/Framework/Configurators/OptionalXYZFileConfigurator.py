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

from .XYZFileConfigurator import XYZFileConfigurator


class OptionalXYZFileConfigurator(XYZFileConfigurator):
    """Input for an XYZ file. The filename can also be empty."""

    def configure(self, filepath: str) -> None:
        """Configure the XYZ file if the filepath is not empty.

        Parameters
        ----------
        filepath : str
            THe filepath of the xyz file.
        """
        if not filepath:
            self._original_input = filepath
            self["value"] = filepath
            self["filename"] = filepath
            self.error_status = "OK"
            return

        super().configure(filepath)
