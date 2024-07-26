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

import numpy as np

from MDANSE.MLogging import LOG
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.Mathematics.LinearAlgebra import Vector


class UnitCellConfigurator(IConfigurator):
    """
    This configurator allows to input a unit cell, in order to replace
    or change the existing cell definition
    """

    _default = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], False

    def __init__(self, name, **kwargs):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param valueType: the numeric type for the vector.
        :type valueType: int or float
        :param normalize: if True the vector will be normalized.
        :type normalize: bool
        :param notNull: if True, the vector must be non-null.
        :type notNull: bool
        :param dimension: the dimension of the vector.
        :type dimension: int
        """

        # The base class constructor.
        IConfigurator.__init__(self, name, **kwargs)
        self["apply"] = False

    def update_trajectory_information(self):
        traj_config = self._configurable[self._dependencies["trajectory"]]["instance"]
        has_valid_cell = True
        has_changing_cell = True
        try:
            first_cell = traj_config.unit_cell(0)._unit_cell
            last_cell = traj_config.unit_cell(len(traj_config) - 1)._unit_cell
        except:
            has_valid_cell = False
        else:
            if first_cell is None:
                has_valid_cell = False
            elif np.allclose(first_cell, 0.0) or np.allclose(last_cell, 0.0):
                has_valid_cell = False
            elif np.allclose(first_cell, last_cell):
                has_changing_cell = False

        if has_valid_cell and has_changing_cell:
            LOG.warning(
                "You will be overwriting a time-dependent unit cell definition with a FIXED unit cell!"
            )

        if not has_valid_cell:
            traj_config = self._configurable[self._dependencies["trajectory"]][
                "instance"
            ]
            self._recommended_cell = (
                2.0 * np.eye(3) * np.linalg.norm(traj_config.max_span)
            )
            LOG.info(
                "Setting recommended cell to twice the maximum distance found in the trajectory."
            )
        else:
            self._recommended_cell = (first_cell + last_cell) / 2.0

    def configure(self, value):
        """
        Configure the unit cell as a 3x3 array.

        :param value: the vector components.
        :type value: (np.ndarray, bool) tuple
        """
        self._original_input = value

        self.update_trajectory_information()

        try:
            input_array = np.array(value[0], dtype=float)
        except:
            self.error_status = (
                "Could not convert the inputs into a floating point array"
            )
            return
        else:
            if input_array.shape != (3, 3):
                self.error_status = "Input shape must be 3x3"
                return

        self["value"] = input_array
        self["apply"] = value[1]
        self.error_status = "OK"

    def get_information(self):
        """
        Returns string information about this configurator.

        :return: the information about this configurator.
        :rtype: str
        """
        if "value" not in self:
            return "Not configured yet\n"

        return "Value: %r\n" % self["value"]
