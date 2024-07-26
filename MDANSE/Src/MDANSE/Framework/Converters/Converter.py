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
from abc import abstractmethod
from importlib import metadata

import h5py

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Core.SubclassFactory import SubclassFactory
from MDANSE.MLogging import LOG


class Converter(IJob, metaclass=SubclassFactory):
    category = ("Converters",)

    ancestor = ["empty_data"]

    @abstractmethod
    def run_step(self, index):
        pass

    def write_metadata(self, output_file):
        string_dt = h5py.special_dtype(vlen=str)
        meta = output_file.create_group("metadata")
        meta.create_dataset(
            "task_name", (1,), data=str(self.__class__.__name__), dtype=string_dt
        )
        meta.create_dataset(
            "MDANSE_version",
            (1,),
            data=str(metadata.version("MDANSE")),
            dtype=string_dt,
        )

        inputs = self.output_configuration()

        if inputs is not None:
            LOG.info(inputs)
            dgroup = meta.create_group("inputs")
            for key, value in inputs.items():
                dgroup.create_dataset(key, (1,), data=value, dtype=string_dt)

    def finalize(self):
        if not hasattr(self, "_trajectory"):
            return

        try:
            output_file = h5py.File(self.configuration["output_files"]["file"], "a")
            # f = netCDF4.Dataset(self._trajectory.filename,'a')
        except:
            LOG.warning("Skipping the finalize call in Converter")
            return

        self.write_metadata(output_file)

        try:
            if "time" in output_file:
                output_file["time"].attrs["units"] = "ps"
                output_file["time"].attrs["axis"] = "time"
                output_file["time"].attrs["name"] = "time"

            if "box_size" in output_file:
                output_file["box_size"].attrs["units"] = "nm"
                output_file["box_size"].attrs["axis"] = "time"
                output_file["box_size"].attrs["name"] = "box_size"

            if "configuration" in output_file:
                output_file["configuration"].attrs["units"] = "nm"
                output_file["configuration"].attrs["axis"] = "time"
                output_file["configuration"].attrs["name"] = "configuration"

            if "velocities" in output_file:
                output_file["velocities"].attrs["units"] = "nm/ps"
                output_file["velocities"].attrs["axis"] = "time"
                output_file["velocities"].attrs["name"] = "velocities"

            if "gradients" in output_file:
                output_file["gradients"].attrs["units"] = "amu*nm/ps"
                output_file["gradients"].attrs["axis"] = "time"
                output_file["gradients"].attrs["name"] = "gradients"
        finally:
            output_file.close()

        super().finalize()
