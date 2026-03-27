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

import json
from traceback import format_exc

import numpy as np

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.Mathematics.Signal import (
    DEFAULT_FILTER,
    FILTER_MAP,
    filter_default_attributes,
    filter_description_string,
)


class TrajectoryFilterConfigurator(IConfigurator):
    """Defines the filter that will be applied to atom positions.

    The filters are provided by the scipy.signal library.

    Attributes
    ----------
    _default : str
        The default selection setting.

    """

    _default_filter = DEFAULT_FILTER

    _settings = filter_default_attributes()
    _expected_keys = {"filter", "attributes"}
    label = "Trajectory filter settings"
    tooltip = "Filter type and parameters specific to the type."

    @classmethod
    def get_default(cls) -> str:
        """Return the default filter string.

        Returns
        -------
        str
            A string representation of the default filter settings dictionary

        """
        return cls._default

    _default = filter_description_string()

    def configure(self, value: str):
        """Configure an input value.

        Parameters
        ----------
        value : str
            The selection setting in a json readable format.

        """
        if not self.update_needed(value):
            return
        self.warning_status = ""

        self._settings = value

        try:
            dict_value = json.loads(value)
        except (TypeError, json.JSONDecodeError):
            self.error_status = (
                f"Input {value} is not of correct format (expected JSON string)."
            )
            return

        if missing := self._expected_keys - dict_value.keys():
            self.error_status = f"The input dictionary is missing the expected keys: {', '.join(missing)}."
            return

        frames_configurator = self.configurable[self.dependencies["frames"]]

        dict_value["attributes"].setdefault("n_steps", frames_configurator["number"])
        dict_value["attributes"].setdefault(
            "time_step_ps", frames_configurator["time_step"]
        )

        try:
            filter_instance = FILTER_MAP[dict_value["filter"]](
                **dict_value["attributes"]
            )
        except Exception as e:
            self.error_status = f"Could not create the filter. {e}: {format_exc()}"
            return

        try:
            filter_instance.apply(np.empty((frames_configurator["number"],)))
        except Exception as e:
            self.error_status = f"Could not apply the filter. {e}: {format_exc()}"
            return

        expected_attributes = filter_instance.default_settings.keys() | {
            "n_steps",
            "time_step_ps",
        }
        if unknown_attributes := dict_value["attributes"].keys() - expected_attributes:
            self.warning_status = (
                f"Unexpected filter attributes: {','.join(unknown_attributes)}"
            )
        if (
            missing_attributes := filter_instance.default_settings.keys()
            - dict_value["attributes"].keys()
        ):
            self.warning_status = "\n".join(
                [
                    self.warning_status,
                    f"No values were given to expected filter attributes: {','.join(missing_attributes)}",
                ]
            )

        self.error_status = "OK"
        self["value"] = self._settings
