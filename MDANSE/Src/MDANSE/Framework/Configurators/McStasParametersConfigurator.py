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

import re
import subprocess

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.Framework.Configurators.McStasOptionsConfigurator import parse_dictionary
from MDANSE.MLogging import LOG


class McStasParametersConfigurator(IConfigurator):
    """
    This configurator allows to input the McStas instrument parameters that will be used to run a McStas executable file.
    """

    _mcStasTypes = {"double": float, "int": int, "string": str}

    _default = {
        "beam_wavelength_Angs": 2.0,
        "environment_thickness_m": 0.002,
        "beam_resolution_meV": 0.1,
        "container": "INPUT_FILENAME.laz",
        "container_thickness_m": 5e-05,
        "sample_height_m": 0.05,
        "environment": "INPUT_FILENAME.laz",
        "environment_radius_m": 0.025,
        "sample_thickness_m": 0.001,
        "sample_detector_distance_m": 4.0,
        "sample_width_m": 0.02,
        "sample_rotation_deg": 45.0,
        "detector_height_m": 3.0,
    }

    def __init__(self, name, exclude=None, **kwargs):
        """
        Initializes the configurator.

        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param exclude: the parameters that exclude when building the McStas instrument parameters list.
        :type exclude: list of str
        """

        # The base class constructor.
        IConfigurator.__init__(self, name, **kwargs)

        self._exclude = exclude if exclude is not None else []

    def configure(self, value):
        """
        Configure the McStas instrument parameters command line.

        :param configuration: the current configuration.
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the McStas instrument parameters.
        :type value: dict
        """
        if not self.update_needed(value):
            return

        self._original_input = value

        instrConfig = self.configurable[self.dependencies["instrument"]]

        exePath = instrConfig["value"]

        s = subprocess.Popen(
            [exePath, "-h"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )

        parameters_bytes = s.communicate()[0]
        parameters_string = parameters_bytes.decode(encoding="utf-8")

        instrParameters = dict(
            [
                (v[0], [v[1], v[2]])
                for v in re.findall(
                    r"\s*(\w+)\s*\((\w+)\)\s*\[default='(\S+)'\]", parameters_string
                )
                if v[0] not in self._exclude
            ]
        )

        val = {}
        parsed = parse_dictionary(value)
        LOG.info(f"Parsed input: {parsed}")
        LOG.info(f"Received from McStas: {instrParameters}")
        for k, v in list(parsed.items()):
            if k not in instrParameters:
                # instrParameters.pop(k)  # how was that supposed to work?
                continue
            val[k] = self._mcStasTypes[instrParameters[k][0]](v)

        self["value"] = [f"{k}={v}" for k, v in val.items()]

    @property
    def exclude(self):
        """
        Returns the McStas instrument parameters to exclude from the McStas command-line.

        :return: the McStas instrument parameters to exclude from the McStas command-line.
        :rtype: list of str
        """

        return self._exclude
