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


from MDANSE.Framework.Configurators.IConfigurator import (
    IConfigurator,
    ConfiguratorError,
)


class TrajectoryVariableConfigurator(IConfigurator):
    """
    This configurator allows to check that a given variable is actually present in a configuration.

    :note: this configurator depends on 'trajectory' configurator to be configured
    """

    _default = "velocities"

    def configure(self, value):
        """
        Configure the configuration variable.

        :param configuration: the current configuration
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the name of the trajectory variable as it should appear in the configuration
        :type value: str
        """

        trajConfig = self._configurable[self._dependencies["trajectory"]]

        if not value in trajConfig["instance"].chemical_system.configuration:
            self.error_status = f"{value} is not registered as a trajectory variable."
            return

        self["value"] = value
        self.error_status = "OK"

    def get_information(self):
        """
        Returns string information about this configurator.

        :return: the information about this configurator.
        :rtype: str
        """

        return "Selected variable: %r\n" % self["value"]
