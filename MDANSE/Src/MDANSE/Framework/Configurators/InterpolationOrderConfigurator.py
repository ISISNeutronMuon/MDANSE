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


from MDANSE.Framework.Configurators.IConfigurator import ConfiguratorError
from MDANSE.Framework.Configurators.IntegerConfigurator import IntegerConfigurator


class InterpolationOrderConfigurator(IntegerConfigurator):
    """
    This configurator allows to input the interpolation order to be applied when deriving velocities from atomic coordinates.

    The allowed value are *'no interpolation'*,*'1st order'*,*'2nd order'*,*'3rd order'*,*'4th order'* or *'5th order'*, the 
    former one will not interpolate the velocities from atomic coordinates but will directly use the velocities stored in the trajectory file.
    
    :attention: it is of paramount importance for the trajectory to be sampled with a very low time \
    step to get accurate velocities interpolated from atomic coordinates. 

    :note: this configurator depends on 'trajectory' configurator to be configured.
    """

    _default = 1

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

        if value is None:
            value = self._default

        IntegerConfigurator.configure(self, value)

        if value == 0:
            trajConfig = self._configurable[self._dependencies["trajectory"]]

            if not "velocities" in trajConfig["instance"].variables():
                self.error_status = f"the trajectory does not contain any velocities. Use an interpolation order higher than 0"
                return

            self["variable"] = "velocities"

        else:
            self["variable"] = "coordinates"
        self.error_status = "OK"
