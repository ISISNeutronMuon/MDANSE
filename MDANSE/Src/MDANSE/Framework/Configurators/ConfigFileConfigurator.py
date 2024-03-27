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
# Copyright (C)  Institut Laue Langevin 2013-now
# Copyright (C)  ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# Authors:    Scientific Computing Group at ILL (see AUTHORS)
import re
import numpy as np

from MDANSE.Core.Error import Error
from MDANSE.Framework.AtomMapping import AtomLabel

from .FileWithAtomDataConfigurator import FileWithAtomDataConfigurator


class LAMMPSConfigFileError(Error):
    pass


class ConfigFileConfigurator(FileWithAtomDataConfigurator):

    def parse(self):
        self._filename = self["filename"]

        self["n_bonds"] = None

        self["bonds"] = []

        self["n_atoms"] = None

        self["n_atom_types"] = None

        self["elements"] = []

        unit = open(self._filename, "r")
        lines = []
        for l in unit.readlines():
            l = l.strip()
            if l:
                lines.append(l)
        unit.close()

        for i, line in enumerate(lines):
            if self["n_atoms"] is None:
                m = re.match("^\s*(\d+)\s*atoms\s*$", line, re.I)
                if m:
                    self["n_atoms"] = int(m.groups()[0])

            if self["n_atom_types"] is None:
                m = re.match("^\s*(\d+)\s*atom types\s*$", line, re.I)
                if m:
                    self["n_atom_types"] = int(m.groups()[0])

            if self["n_bonds"] is None:
                m = re.match("^\s*(\d+)\s*bonds\s*$", line, re.I)
                if m:
                    self["n_bonds"] = int(m.groups()[0])

            if re.match("^\s*masses\s*$", line, re.I):
                if self["n_atom_types"] is None:
                    raise LAMMPSConfigFileError(
                        "Did not find the number of atom types."
                    )

                for j in range(1, self["n_atom_types"] + 1):
                    data_line = (
                        lines[i + j].strip().split("#")[0]
                    )  # Remove commentary if any
                    idx, mass = data_line.split()[0:2]
                    idx = int(idx)
                    mass = float(mass)
                    self["elements"].append([idx, mass])

            m = re.match("^\s*bonds\s*$", line, re.I)
            if m:
                for j in range(1, self["n_bonds"] + 1):
                    _, _, at1, at2 = lines[i + j].split()
                    at1 = int(at1) - 1
                    at2 = int(at2) - 1
                    self["bonds"].append([at1, at2])
                self["bonds"] = np.array(self["bonds"], dtype=np.int32)

    def get_atom_labels(self) -> list[AtomLabel]:
        """
        Returns
        -------
        list[AtomLabel]
            An ordered list of atom labels.
        """
        labels = []
        for idx, mass in self["elements"]:
            label = AtomLabel(str(idx), mass=mass)
            if label not in labels:
                labels.append(label)
        return labels
