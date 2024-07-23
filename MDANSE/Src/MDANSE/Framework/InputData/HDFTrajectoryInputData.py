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
import json

from MDANSE.Framework.InputData.IInputData import InputDataError
from MDANSE.Framework.InputData.InputFileData import InputFileData
from MDANSE.MolecularDynamics.Trajectory import Trajectory
from MDANSE.MLogging import LOG


json_decoder = json.decoder.JSONDecoder()


class HDFTrajectoryInputData(InputFileData):
    extension = "mdt"

    def load(self):
        self._metadata = {}
        try:
            traj = Trajectory(self._name)
        except IOError as e:
            raise InputDataError(str(e))
        except ValueError as e:
            raise InputDataError(str(e))

        self._data = traj
        self.check_metadata()

    def close(self):
        self._data.close()

    def info(self):
        val = []
        try:
            time_axis = self._data.time()
        except:
            timeline = "No time information!\n"
        else:
            if len(time_axis) < 1:
                timeline = "N/A\n"
            elif len(time_axis) < 5:
                timeline = f"{time_axis}\n"
            else:
                timeline = f"[{time_axis[0]}, {time_axis[1]}, ..., {time_axis[-1]}]\n"

        val.append("Path:")
        val.append("%s\n" % self._name)
        val.append("Number of steps:")
        val.append("%s\n" % len(self._data))
        val.append("Configuration:")
        val.append("\tIs periodic: {}\n".format("unit_cell" in self._data.file))
        val.append(
            "First unit cell (nm):\n{}\n".format(self._data.unit_cell(0)._unit_cell)
        )
        val.append("Frame times (1st, 2nd, ..., last) in ps:")
        val.append(timeline)
        val.append("Variables:")
        for k in self._data.variables():
            v = self._data.variable(k)
            try:
                val.append("\t- {}: {}".format(k, v.shape))
            except AttributeError:
                try:
                    val.append("\t- {}: {}".format(k, v["value"].shape))
                except KeyError:
                    continue

        val.append("\nConversion history:")
        for k, v in self._metadata.items():
            val.append(f"{k}: {v}")

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

    def check_metadata(self):
        meta_dict = {}

        def put_into_dict(name, obj):
            try:
                string = obj[:][0].decode()
            except:
                LOG.warning(f"Decode failed for {name}: {obj}")
            else:
                try:
                    meta_dict[name] = json_decoder.decode(string)
                except ValueError:
                    meta_dict[name] = string

        try:
            meta = self._data.file["metadata"]
        except KeyError:
            return
        else:
            meta.visititems(put_into_dict)
        self._metadata = meta_dict

    @property
    def trajectory(self):
        return self._data

    @property
    def chemical_system(self):
        return self._data.chemical_system

    @property
    def hdf(self):
        return self._data.file
