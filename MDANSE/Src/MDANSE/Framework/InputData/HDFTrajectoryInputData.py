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


from MDANSE.Framework.InputData.IInputData import InputDataError
from MDANSE.Framework.InputData.InputFileData import InputFileData
from MDANSE.MolecularDynamics.Trajectory import Trajectory


class HDFTrajectoryInputData(InputFileData):
    extension = "mdt"

    def load(self):
        try:
            traj = Trajectory(self._name)
        except IOError as e:
            raise InputDataError(str(e))
        except ValueError as e:
            raise InputDataError(str(e))

        self._data = traj

    def close(self):
        self._data.close()

    def info(self):
        val = []

        val.append("Path:")
        val.append("%s\n" % self._name)
        val.append("Number of steps:")
        val.append("%s\n" % len(self._data))
        val.append("Configuration:")
        val.append("\tIs periodic: {}\n".format("unit_cell" in self._data.file))
        val.append("Variables:")
        for k, v in self._data.file["/configuration"].items():
            val.append("\t- {}: {}".format(k, v.shape))

        mol_types = {}
        val.append("\nMolecular types found:")
        for ce in self._data.chemical_system.chemical_entities:
            if ce.__class__.__name__ in mol_types:
                mol_types[ce.__class__.__name__] += 1
            else:
                mol_types[ce.__class__.__name__] = 1

        for k, v in mol_types.items():
            val.append("\t- {:d} {}".format(v, k))

        val = "\n".join(val)

        return val

    @property
    def trajectory(self):
        return self._data

    @property
    def chemical_system(self):
        return self._data.chemical_system

    @property
    def hdf(self):
        return self._data.file
