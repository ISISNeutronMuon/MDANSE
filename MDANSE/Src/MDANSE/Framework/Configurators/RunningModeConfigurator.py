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
# Copyright (C)  Institut Laue Langevin 2013-now
# Copyright (C)  ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# Authors:    Scientific Computing Group at ILL (see AUTHORS)

import os
import multiprocessing

from MDANSE import PLATFORM
from MDANSE.Framework.Configurators.IConfigurator import (
    IConfigurator,
    ConfiguratorError,
)


class RunningModeConfigurator(IConfigurator):
    """
    This configurator allows to choose the mode used to run the calculation.

    MDANSE currently support single-core or multicore (SMP) running modes. In the laster case, you have to
    specify the number of slots used for running the analysis.
    """

    availablesModes = ["single-core", "threadpool", "multicore"]

    _default = ("single-core", 1)

    def configure(self, value):
        """
        Configure the running mode.
     
        :param value: the running mode specification. It can be *'single-core'* or a 2-tuple whose first element \
        must be *'multicore'* and 2nd element the number of slots allocated for running the analysis.
        :type value: *'single-core'* or 2-tuple
        """

        if isinstance(value, str):
            mode = value
        else:
            mode = value[0].lower()

        if not mode in self.availablesModes:
            self.error_status = f"{mode} is not a valid running mode."
            return

        if mode == "single-core":
            slots = 1

        else:
            slots = int(value[1])

            if mode == "multicore":
                maxSlots = multiprocessing.cpu_count()
                if slots > maxSlots:
                    self.error_status = "invalid number of allocated slots."
                    return

            if slots <= 0:
                self.error_status = "invalid number of allocated slots."
                return

        self["mode"] = mode

        self["slots"] = slots
        self.error_status = "OK"

    def get_information(self):
        """
        Returns string information about this configurator.

        :return: the information about this configurator.
        :rtype: str
        """

        return "Run in %s mode (%d slots)\n" % (self["mode"], self["slots"])
