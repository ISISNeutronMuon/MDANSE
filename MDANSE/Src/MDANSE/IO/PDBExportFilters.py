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


class PDBExportFilter:
    def processLine(self, type, data):
        return type, data

    def processResidue(self, name, number, terminus):
        return name, number

    def processChain(self, chain_id, segment_id):
        return chain_id, segment_id

    def terminateChain(self):
        pass


#
# XPlor export filter

import string


class XPlorExportFilter(PDBExportFilter):
    xplor_atom_names = {" OXT": "OT2"}

    def processLine(self, type, data):
        if type == "TER":
            return None, data
        if type == "ATOM" or type == "HETATM" or type == "ANISOU":
            name = self.xplor_atom_names.get(data["name"], data["name"])
            data["name"] = name
        return type, data


export_filters = {"xplor": XPlorExportFilter}
