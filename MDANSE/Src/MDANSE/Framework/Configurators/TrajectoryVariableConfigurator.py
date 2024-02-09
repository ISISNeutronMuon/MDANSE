# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/TrajectoryVariableConfigurator.py
# @brief     Implements module/class/test TrajectoryVariableConfigurator
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************


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

        return "Selected variable: %r" % self["value"]
