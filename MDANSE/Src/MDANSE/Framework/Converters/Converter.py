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

from abc import ABC, abstractmethod
from typing import ClassVar

import h5py

from MDANSE.Core.RegisterFactory import RegisterFactory
from MDANSE.Framework.Formats.HDFFormat import write_metadata
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.IO.IOUtils import UCDict
from MDANSE.MLogging import LOG

TRAJ_UNITS = {
    "unit_cell": "nm",
    "charge": "e",
    "configuration/coordinates": "nm",
    "configuration/velocities": "nm/ps",
    "configuration/gradients": "amu*nm/ps",
    "time": "ps",
    "composition/atom_indices": "N/A",
}
TRAJ_AXES = {
    "unit_cell": "time|index|index",
    "charge": "composition/atom_indices",
    "configuration/coordinates": "time|composition/atom_indices|index",
    "configuration/velocities": "time|composition/atom_indices|index",
    "configuration/gradients": "time|composition/atom_indices|index",
    "time": "index",
    "composition/atom_indices": "index",
}


class Converter(IJob, RegisterFactory["Converter"], ABC):
    """Outputs a trajectory in the MDT format."""

    registry: ClassVar[UCDict[str, type[Converter]]] = UCDict()
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

        for dset_name, dset_unit in TRAJ_UNITS.items():
            if dset_name in output_file:
                output_file[dset_name].attrs["units"] = dset_unit
                output_file[dset_name].attrs["axis"] = TRAJ_AXES[dset_name]
                output_file[dset_name].attrs["name"] = dset_name

        if "charge" in output_file and output_file["charge"].ndim == 2:
            output_file[dset_name].attrs["axis"] = TRAJ_AXES[dset_name] + "|time"

        output_file.close()

        super().finalize()
