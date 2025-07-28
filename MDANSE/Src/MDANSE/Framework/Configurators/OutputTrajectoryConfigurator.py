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

from pathlib import Path

import numpy as np

from MDANSE import PLATFORM
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.Framework.Formats.IFormat import IFormat
from MDANSE.MolecularDynamics.Trajectory import TrajectoryWriter


class OutputTrajectoryConfigurator(IConfigurator):
    """Specifies how a trajectory should be output to a file.

    Allows to define:

    - path to the file,
    - precision of the floating point numbers,
    - HDF5 chunk size,
    - compression applied to the HDF5 datasets
    - logging level of the converter run.

    For trajectories, MDANSE supports only the MDT format (HDF5).
    """

    log_options = ("no logs", "DEBUG", "INFO", "WARN", "ERROR", "CRITICAL")
    _default = ("OUTPUT_TRAJECTORY", 64, 128, "none", "no logs")

    def __init__(self, name, format=None, **kwargs):
        """Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param formats: the list of output file formats supported.
        :type formats: list of str
        """
        IConfigurator.__init__(self, name, **kwargs)

        self.format = "MDTFormat"
        self._dtype = np.float64
        self._compression = "none"
        self.forbidden_files = []
        self._chunk_limit = 128

    def configure(self, value: tuple):
        self._original_input = value

        root, dtype, chunk_size, compression, logs = value
        root = Path(root)

        if logs not in self.log_options:
            self.error_status = "log level option not recognised"
            return

        if not root:
            self.error_status = "empty root name for the output file."
            return

        if not PLATFORM.is_file_writable(root):
            self.error_status = f"the file {root} is not writable"
            return

        if dtype < 17:
            self._dtype = np.float16
        elif dtype < 33:
            self._dtype = np.float32
        else:
            self._dtype = np.float64

        self._chunk_limit = chunk_size

        if compression in TrajectoryWriter.allowed_compression:
            self._compression = compression
        else:
            self._compression = None

        self["root"] = root
        self["format"] = self.format
        self["extension"] = IFormat.create(self.format).extension
        temp_name = root
        if self["extension"] != root.suffix:  # capture most extension lengths
            temp_name = root.with_suffix(root.suffix + self["extension"])
        self["file"] = temp_name

        if self["file"].absolute() in self.forbidden_files:
            self.error_status = f"File {self['file']} is either open or being written into. Please pick another name."
            return

        self["dtype"] = self._dtype
        self["compression"] = self._compression
        self["chunk_size"] = self._chunk_limit
        self["log_level"] = logs
        self["write_logs"] = logs != "no logs"
        self.error_status = "OK"
