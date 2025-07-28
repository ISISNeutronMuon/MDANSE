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

import multiprocessing

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator


class RunningModeConfigurator(IConfigurator):
    """Specifies how many CPU cores will be used by this task.

    MDANSE currently support single-core or multicore (SMP) running modes.
    In the latter case, you have to specify the number of slots used for
    running the analysis.
    """

    availablesModes = ["single-core", "multicore"]

    _default = ("single-core", 1)

    def configure(self, value):
        """
        Configure the running mode.

        :param value: the running mode specification. It can be *'single-core'* or a 2-tuple whose first element \
        must be *'multicore'* and 2nd element the number of slots allocated for running the analysis.
        :type value: *'single-core'* or 2-tuple
        """
        if not self.update_needed(value):
            return

        self._original_input = value

        if isinstance(value, str):
            mode = value
        else:
            mode = value[0].lower()

        if mode not in self.availablesModes:
            self.error_status = f"{mode} is not a valid running mode."
            return

        if mode == "single-core":
            slots = 1

        else:
            slots = int(value[1])
            maxSlots = multiprocessing.cpu_count()

            if slots < 0:
                slots = min(abs(slots), maxSlots)
            elif slots == 0 or slots > maxSlots:
                self.error_status = "invalid number of allocated slots."
                return

        self["mode"] = mode

        self["slots"] = slots
        self.error_status = "OK"
