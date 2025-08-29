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

from MDANSE.Framework.Configurators.IntegerConfigurator import IntegerConfigurator


class InterpolationOrderConfigurator(IntegerConfigurator):
    """Specifies the order of a numerical derivative used for interpolation.

    Normally it is used for calculating atom velocities from their positions.
    Values from 1 to 5 are allowed. If MD engine velocities are provided in the
    trajectory file, you can (and should) choose to use them by setting this to 0.

    The velocities calculated from atom positions may differ from the values used
    by the MD engine during the simulation. Additionally, if your MD engine was
    not writing out every frame, the velocities are likely to be
    underestimated compared to the values used by the MD engine in the simulation,
    and the error in the calculation increases quickly with the number of trajectory
    frames skipped in the MD output.

    """

    _default = 3

    def __init__(self, name, **kwargs):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str.
        """

        IntegerConfigurator.__init__(self, name, **kwargs)

    def configure(self, value):
        """
        Configure the input interpolation order.

        :param value: the interpolation order to be configured.
        :type value: str one of *'no interpolation'*,*'1st order'*,*'2nd order'*,*'3rd order'*,*'4th order'* or *'5th order'*.
        """
        if not self.update_needed(value):
            return
        self.warning_status = ""

        frames_configurator = self.configurable[self.dependencies["frames"]]
        if not frames_configurator.valid:
            self.error_status = "Frames configurator is not valid."
            return

        self._original_input = value
        if value is None or value == "":
            value = self._default

        IntegerConfigurator.configure(self, value)

        trajConfig = self.configurable[self.dependencies["trajectory"]]
        traj_has_velocities = trajConfig["instance"].has_variable("velocities")

        if value == 0:
            if not traj_has_velocities:
                self.error_status = "the trajectory does not contain any velocities. Use an interpolation order higher than 0"
                return
            self["variable"] = "velocities"
        elif value > 5:
            self.error_status = (
                "Use an interpolation order greater than 5 is not implemented."
            )
            return
        else:
            number = frames_configurator["number"]
            if number < value + 1:
                self.error_status = (
                    f"Not enough MD frames to apply derivatives of order {value}"
                )
                return
            self["variable"] = "coordinates"
        self.error_status = "OK"
        if value > 0 and traj_has_velocities:
            self.warning_status = (
                "Input trajectory contains velocities."
                " There should be no need to interpolate atom positions."
                " Set interpolation order to 0 to use the velocities"
                " from the trajectory file."
            )
