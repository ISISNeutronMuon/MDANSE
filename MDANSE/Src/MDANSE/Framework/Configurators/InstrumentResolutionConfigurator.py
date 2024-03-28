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

import numpy as np


from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.Framework.InstrumentResolutions.IInstrumentResolution import (
    IInstrumentResolution,
)


class InstrumentResolutionConfigurator(IConfigurator):
    """
    This configurator allows to set an instrument resolution.

    The instrument resolution will be used in frequency-dependant analysis (e.g. the vibrational density
    of states) when performing the fourier transform of its time-dependant counterpart. This allow to
    convolute of the signal with a resolution function to have a better match with experimental spectrum.

    In MDANSE, the instrument resolution are defined in omegas space and are internally
    inverse-fourier-transformed to get a time-dependant version. This time-dependant resolution function will then
    be multiplied by the time-dependant signal to get the resolution effect according to the Fourier Transform theorem:

    .. math:: TF(f(t) * r(t)) = F(\omega) \otimes R(\omega) = G(\omega)

    where f(t) and r(t) are respectively the time-dependant signal and instrument resolution and
    F(\omega) and R(\omega) are their corresponding spectrum. Hence, G(\omega) represents the signal
    convoluted by the instrument resolution and, as such, represents the quantity to be compared directly with
    experimental results.

    An instrument resolution is represented in MDANSE by a kernel function and a sets of parameters for this function.
    MDANSE currently supports the aussian, lorentzian, square, triangular and pseudo-voigt kernels.

    :note: this configurator depends on the 'frame' configurator to be configured.
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

        framesCfg = self._configurable[self._dependencies["frames"]]

        time = framesCfg["time"]
        self["n_frames"] = len(time)

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

        kernel, parameters = value

        resolution = IInstrumentResolution.create(kernel)

        resolution.setup(parameters)

        resolution.set_kernel(self["omega"], self["time_step"])

        self["omega_window"] = resolution.omegaWindow

        self["time_window"] = resolution.timeWindow.real

        self["kernel"] = kernel
        self["parameters"] = parameters

    def get_information(self):
        """
        Returns some informations the instrument resolution.

        :return: the information the instrument resolution.
        :rtype: str
        """

        if "kernel" not in self:
            return "No configured yet"

        info = ["Instrument resolution kernel: %s" % self["kernel"]]
        if self["parameters"]:
            info.append("Parameters:")
            for k, v in list(self["parameters"].items()):
                info.append("%s = %s" % (k, v))

        info = "\n".join(info)

        return info + "\n"
