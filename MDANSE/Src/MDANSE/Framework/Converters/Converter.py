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

from abc import abstractmethod

import h5py

from MDANSE.Core.SubclassFactory import SubclassFactory
from MDANSE.Framework.Formats.HDFFormat import write_metadata
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MLogging import LOG


class Converter(IJob, metaclass=SubclassFactory):
    """Outputs a trajectory in the MDT format."""

    category = ("Converters", "Specific")
    ancestor = ["empty_data"]
    runscript_import_line = (
        "from MDANSE.Framework.Converters.Converter import Converter"
    )

    @abstractmethod
    def run_step(self, index):
        pass

    def finalize(self):
        if not hasattr(self, "_trajectory"):
            return

        try:
            output_file = h5py.File(self.configuration["output_files"]["file"], "a")
            # f = netCDF4.Dataset(self._trajectory.filename,'a')
        except Exception:
            LOG.warning("Skipping the finalize call in Converter")
            return

        write_metadata(self, output_file)

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
