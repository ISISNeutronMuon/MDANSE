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

import abc

import numpy as np

from MDANSE.Core.Error import Error
from MDANSE.Core.SubclassFactory import SubclassFactory
from MDANSE.Framework.Configurable import Configurable


class InstrumentResolutionError(Error):
    pass


class IInstrumentResolution(Configurable, metaclass=SubclassFactory):
    def __init__(self):
        Configurable.__init__(self)

        self._omegaWindow = None

        self._timeWindow = None

    @abc.abstractmethod
    def set_kernel(self, omegas, dt):
        pass

    def apply_fft(self, omegaWindow, dt):
        timeWindow = np.fft.fftshift(np.fft.ifft(np.fft.ifftshift(omegaWindow)) / dt)
        return timeWindow

    @property
    def omegaWindow(self):
        if self._omegaWindow is None:
            raise InstrumentResolutionError("Undefined omega window")

        return self._omegaWindow

    @property
    def timeWindow(self):
        if self._timeWindow is None:
            raise InstrumentResolutionError("Undefined time window")

        return self._timeWindow
