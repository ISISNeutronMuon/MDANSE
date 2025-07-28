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

import numpy as np

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.Framework.InstrumentResolutions.IInstrumentResolution import (
    IInstrumentResolution,
)


class InstrumentResolutionConfigurator(IConfigurator):
    r"""Defines the resolution function to use for signal broadening.

    The instrument resolution will be used in frequency-dependent analysis
    (e.g. the vibrational density of states) when performing the Fourier
    transform of its time-dependent counterpart. The convolution of the signal
    with a resolution function should be closer to the experimental spectrum.

    In MDANSE, the instrument resolution is calculated as a function of energy,
    and then Fourier-transformed into the time domain and applied to the
    time-dependent signal as follows:

    .. math:: FT(f(t)r(t)) = F(\omega) * R(\omega) = G(\omega)

    where f(t) and r(t) are, respectively, the time-dependent signal and
    instrument resolution. :math:`F(\omega)` and :math:`R(\omega)`
    are their corresponding spectra. Hence, :math:`G(\omega)` represents
    the convolution of the signal and the instrument resolution. This resolution
    is constant and not energy-dependent, as opposed to the real resolution
    of most neutron instruments.

    """

    _default = ("gaussian", {"mu": 0.0, "sigma": 10.0})

    def configure(self, value):
        """
        Configure the instrument resolution.

        :param value: the instrument resolution. It must a 2-tuple where the 1st element is the \
        is a string representing one of the supported instrument resolution and the 2nd element \
        is a dictionary that stores the parameters for this kernel.
        :type value: 2-tuple
        """
        if not self.update_needed(value):
            return

        self._original_input = value

        framesCfg = self.configurable[self.dependencies["frames"]]

        time = framesCfg["time"]
        self["n_frames"] = len(time)
        if len(time) < 2:
            framesCfg.error_status = "This analysis requires more time steps"
            return

        self._timeStep = framesCfg["time"][1] - framesCfg["time"][0]
        self["time_step"] = self._timeStep

        # We compute angular frequency AND NOT ORDINARY FREQUENCY ANYMORE
        self["omega"] = (
            2.0
            * np.pi
            * np.fft.fftshift(
                np.fft.fftfreq(2 * self["n_frames"] - 1, self["time_step"])
            )
        )
        self["n_omegas"] = len(self["omega"])

        # generate the rfftfreq for the positive frequency only results
        self["romega"] = (
            2.0 * np.pi * np.fft.rfftfreq(2 * self["n_frames"] - 1, self["time_step"])
        )
        self["n_romegas"] = len(self["romega"])

        kernel, parameters = value
        self["kernel"] = kernel
        self["parameters"] = parameters

        resolution = IInstrumentResolution.create(kernel)
        resolution.setup(parameters)
        resolution.set_kernel(self["omega"], self["time_step"])
        self["omega_window"] = resolution.omegaWindow
        self["time_window"] = resolution.timeWindow.real
        self["time_window_positive"] = np.fft.ifftshift(self["time_window"])[
            : len(time)
        ]
        self.error_status = "OK"

    def preview_output_axis(self):
        if not self.is_configured():
            return None, None
        if not self.valid:
            return None, None
        if "romega" in self:
            return self["romega"], "rad/ps"
        else:
            return None, None
