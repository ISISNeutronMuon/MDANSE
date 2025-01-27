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

from MDANSE.Framework.InputData.IInputData import InputDataError
from MDANSE.Framework.InputData.InputFileData import InputFileData
from MDANSE.MolecularDynamics.MockTrajectory import MockTrajectory


class MockTrajectoryInputData(InputFileData):
    """Imitates the HDFTrajectoryInputData,
    but builds a MockTrajectory out of a JSON file instead.
    """

    extension = "json"

    def load(self):
        try:
            traj = MockTrajectory.from_json(self._name)
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
        val.append(f"{self._name}\n")
        val.append("Number of steps:")
        val.append(f"{self._data}\n")

        mol_types = {}
        val.append("\nMolecular types found:")
        for name, list in self._data.chemical_system._clusters.items():
            mol_types[name] = len(list)

        for k, v in mol_types.items():
            val.append(f"\t- {v:d} {k}")

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
        """There is no HDF5 file for a mock trajectory

        Returns
        -------
        str
            name of a nonexistent file
        """
        return self._data.file
