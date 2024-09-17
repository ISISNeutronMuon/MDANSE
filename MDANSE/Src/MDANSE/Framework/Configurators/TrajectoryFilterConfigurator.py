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
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.Mathematics.Signal import Butterworth, ChebyshevTypeI, ChebyshevTypeII, Elliptical, Bessel, Notch, Peak, Comb

FILTERS = (Butterworth, ChebyshevTypeI, ChebyshevTypeII, Elliptical, Bessel, Notch, Peak, Comb)

class TrajectoryFilterConfigurator(IConfigurator):
    """This configurator allows the application of a filter to the trajectory of atoms in the simulation.

    Attributes
    ----------
    _default : str
        The defaults selection setting.
    """

    _filter = FILTERS[0]
    _dict = dict()

    @classmethod
    def settings(cls, filter=_filter):
        filter.set_defaults()
        settings_dict = dict()
        for setting, values in filter.default_settings.items():
            settings_dict.update({setting: values["value"]})
        return settings_dict

    _default = '{ "filter": "' + f'{_filter.__name__}"' + f'{json.dumps(settings.__func__(object()))}' + '}'

    def configure(self, value: str) -> None:
        """Configure an input value.

        Parameters
        ----------
        value : str
            The selection setting in a json readable format.
        """

    def update_settings(self, key: str, value: str) -> None:
        """Configure an input value.

        Parameters
        ----------
        value : str
            The selection setting in a json readable format.

        value : str
            The selection setting in a json readable format.
        """
        self._dict.update({key: value})

    @property
    def filter(self):
        return self._filter

    @filter.setter
    def filter(self, name):
        self._filter = name

