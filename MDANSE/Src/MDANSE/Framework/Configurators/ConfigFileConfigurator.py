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
import re
import numpy as np

from MDANSE.Core.Error import Error
from MDANSE.Framework.AtomMapping import AtomLabel

from .FileWithAtomDataConfigurator import FileWithAtomDataConfigurator
from MDANSE.MLogging import LOG


class LAMMPSConfigFileError(Error):
    pass


def parse_unit_cell(inputs):

    unit_cell = np.zeros(9)

    xlo, xhi, xy = inputs[0], inputs[1], inputs[2]
    ylo, yhi, xz = inputs[3], inputs[4], inputs[5]
    zlo, zhi, yz = inputs[6], inputs[7], inputs[8]
    # The ax component.
    unit_cell[0] = xhi - xlo

    # The bx and by components.
    unit_cell[3] = xy
    unit_cell[4] = yhi - ylo

    # The cx, cy and cz components.
    unit_cell[6] = xz
    unit_cell[7] = yz
    unit_cell[8] = zhi - zlo

    unit_cell = np.reshape(unit_cell, (3, 3))

    return unit_cell


class ConfigFileConfigurator(FileWithAtomDataConfigurator):

    def parse(self):
        self._filename = self["filename"]

        self["n_bonds"] = None

        self["bonds"] = []

        self["n_atoms"] = None

        self["n_atom_types"] = None

        self["elements"] = []

        self["atom_types"] = []

        self["charges"] = []

        self["unit_cell"] = np.zeros((3, 3))

        with open(self._filename, "r") as source_file:
            lines = []
            for l in source_file.readlines():
                l = l.strip()
                if l:
                    lines.append(l)

        for i, line in enumerate(lines):
            toks = line.split()

            if "xlo" in line and "xhi" in line:
                try:
                    x_inputs = [float(x) for x in toks[0:3]]
                except:
                    xspan = float(toks[1]) - float(toks[0])
                    self["unit_cell"][0, 0] = xspan
            elif "ylo" in line and "yhi" in line:
                try:
                    y_inputs = [float(x) for x in toks[0:3]]
                except:
                    yspan = float(toks[1]) - float(toks[0])
                    self["unit_cell"][1, 1] = yspan
            elif "zlo" in line and "zhi" in line:
                try:
                    z_inputs = [float(x) for x in toks[0:3]]
                except:
                    zspan = float(toks[1]) - float(toks[0])
                    self["unit_cell"][2, 2] = zspan

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
                    )  # Remove comments, if present
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

            if re.match("^\s*Atoms\s*$", line.split("#")[0]):
                if not "#" in line:
                    num_of_columns = len(lines[i + 2].split())
                    if num_of_columns <= 5:
                        type_index = 1
                        charge_index = None
                        line_limit = 6
                    else:
                        type_index = 2
                        charge_index = 3
                        line_limit = 7
                else:
                    if "charge" in line.split("#")[-1]:
                        type_index = 1
                        charge_index = 2
                        line_limit = 6
                    elif "atomic" in line.split("#")[-1]:
                        type_index = 1
                        charge_index = None
                        line_limit = 6
                    elif "full" in line.split("#")[-1]:
                        type_index = 2
                        charge_index = 3
                        line_limit = 7
                    else:
                        type_index = 2
                        charge_index = 3
                        line_limit = 7
                if self["n_atoms"] is not None:
                    self["atom_types"] = self["n_atoms"] * [0]
                    self["charges"] = self["n_atoms"] * [0.0]
                    for j in range(self["n_atoms"]):
                        atoks = lines[i + j + 1].split()
                        self["atom_types"][j] = int(atoks[type_index])
                        if len(atoks) >= line_limit and charge_index is not None:
                            self["charges"][j] = float(atoks[charge_index])

        if np.trace(np.abs(self["unit_cell"])) < 1e-8:
            # print(f"Concatenated: {np.concatenate([x_inputs, y_inputs, z_inputs])}")
            try:
                self["unit_cell"] = parse_unit_cell(
                    np.concatenate([x_inputs, y_inputs, z_inputs])
                )
            except:
                LOG.error(f"LAMMPS ConfigFileConfigurator failed to find a unit cell")

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
