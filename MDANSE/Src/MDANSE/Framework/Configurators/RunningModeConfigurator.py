# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/RunningModeConfigurator.py
# @brief     Implements module/class/test RunningModeConfigurator
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

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

    MDANSE currently support monoprocessor or multiprocessor (SMP) running modes. In the laster case, you have to
    specify the number of slots used for running the analysis.
    """

    availablesModes = ["monoprocessor", "threadpool", "multiprocessor"]

    _default = ("monoprocessor", 1)

    def configure(self, value):
        """
        Configure the running mode.
     
        :param value: the running mode specification. It can be *'monoprocessor'* or a 2-tuple whose first element \
        must be *'multiprocessor'* and 2nd element the number of slots allocated for running the analysis.
        :type value: *'monoprocessor'* or 2-tuple
        """

        if isinstance(value, str):
            mode = value
        else:
            mode = value[0].lower()

        if not mode in self.availablesModes:
            self.error_status = f"{mode} is not a valid running mode."
            return

        if mode == "monoprocessor":
            slots = 1

        else:
            slots = int(value[1])

            if mode == "multiprocessor":
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

        return "Run in %s mode (%d slots)" % (self["mode"], self["slots"])
