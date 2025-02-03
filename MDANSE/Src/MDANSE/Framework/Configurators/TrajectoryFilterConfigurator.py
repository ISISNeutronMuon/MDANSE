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
from MDANSE.Mathematics.Signal import filter_map


class TrajectoryFilterConfigurator(IConfigurator):
    """This configurator allows the application of a filter to the trajectory of atoms in the simulation.

    Attributes
    ----------
    _default : str
        The defaults selection setting.
    """

    _filter = tuple(filter_map.values())[0]

    @classmethod
    def filter_default_attributes(cls, filter=_filter):
        """Get the filter-specific settings dictionary for a filter class.

        Parameters
        ----------
        filter :
            The filter class.

        Returns
        -------

            The filter settings dictionary
        """
        filter.set_defaults()
        settings_dict = dict()
        for setting, values in filter.default_settings.items():
            settings_dict.update({setting: values["value"]})
        return settings_dict

    _settings = filter_default_attributes.__func__(object())

    @classmethod
    def get_default(cls) -> str:
        """Return the default filter string.

        Returns
        -------

            A string representation of the default filter settings dictionary
        """
        return cls._default

    @staticmethod
    def filter_description_string(filter=_filter, settings=_settings) -> str:
        """Convert a filter class and filter settings dictionary to a string.

        Parameters
        ----------
        filter : str
            The filter class

        settings : dict
            Dictionary containing the filter settings

        Returns
        -------

            A string representation of the filter settings dictionary
        """
        return (
            '{ "filter": "'
            + f'{filter.__name__}"'
            + ", "
            + '"attributes": '
            + f"{json.dumps(settings)}"
            + "}"
        )

    _default = filter_description_string()

    @property
    def settings(self):
        return self._settings

    @settings.setter
    def settings(self, settings: dict):
        self._settings = settings

    @property
    def filter(self):
        return self._filter

    @filter.setter
    def filter(self, name):
        self._filter = name

    def configure(self, value: str):
        """Configure an input value.

        Parameters
        ----------
        value : str
            The selection setting in a json readable format.
        """
        self.settings = value

        try:
            dict_value = json.loads(value)

            try:
                {"filter", "attributes"} in set(dict_value.keys())
            except (TypeError, ValueError) as e:
                self.error_status = f"The dictionary \n{dict_value}\n does not contain the expected keys"

        except (TypeError, ValueError) as e:
            self.error_status = f"Value \n{value}\n in {self} is not of correct format (expected JSON string)"

        self.error_status = "OK"
        self["value"] = self.settings
