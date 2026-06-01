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

from typing import TYPE_CHECKING, Any, NamedTuple, TypedDict

import numpy as np
import numpy.typing as npt

from MDANSE.Framework.InstrumentResolutions.IInstrumentResolution import (
    IInstrumentResolution,
)
from MDANSE.Framework.InstrumentResolutions.PseudoVoigt import PseudoVoigt
from MDANSE.Framework.Parameters.Choices import SubclassChoice
from MDANSE.Framework.Parameters.Parameters import (
    ConfigError,
    Configurable,
    CustomConfig,
)
from MDANSE.Framework.Parameters.UtilTypes import DescID, PredictionResult

if TYPE_CHECKING:
    from collections.abc import Iterator

    from MDANSE.Framework.Parameters.Frames import FrameWindow


class Resolution(TypedDict, total=False):
    res_type: str
    mu: float
    sigma: float


class RunResolution(NamedTuple):
    omega: npt.NDArray[float]
    romega: npt.NDArray[float]
    resolution_parameters: Resolution
    time_window: npt.NDArray[float]
    omega_window: npt.NDArray[complex]
    time_window_positive: npt.NDArray[float]
    kernel: str

    @property
    def n_omegas(self) -> int:
        return len(self.omega)

    @property
    def n_romegas(self) -> int:
        return len(self.romega)

    @property
    def add_ideal(self) -> bool:
        return self.kernel.lower() != "ideal"

    def __repr__(self) -> str:
        return f"{type(self).__name__}(kernel={self.kernel!r}, parameters={self.resolution_parameters})"


ResolutionInput = RunResolution | Resolution | tuple[str, dict[str, Any]]
ResolutionType = type[IInstrumentResolution]


class InstrumentResolution(CustomConfig):
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

    default_tooltip = "Choose instrument resolution"
    default_label = "Instrument resolution"

    kernel = SubclassChoice[str | IInstrumentResolution, IInstrumentResolution](
        IInstrumentResolution,
        aliases={"PSEUDO-VOIGT": PseudoVoigt},
        default="Ideal",
    )

    def required_deps(self) -> set[DescID]:
        return super().required_deps() | {DescID("window")}

    def __set__(self, owner: Configurable, value) -> None:
        self.owner = owner

        match value:
            case RunResolution(kernel=kernel, resolution_parameters=params):
                self.kernel, self.kernel.configuration = kernel, params
            case {"res_type": kernel, **params} | {"kernel": kernel, **params}:
                self.kernel, self.kernel.configuration = kernel, params
            case {**params}:
                self.kernel.configuration = params
            case (kernel, params):
                self.kernel, self.kernel.configuration = kernel, params
            case str():
                self.kernel = value
            case _:
                super().__set__(owner, value)

    @property
    def params(self) -> dict[DescID, Any]:
        return self.kernel.configuration

    @params.setter
    def params(self, value: dict[DescID, Any]):
        self.kernel.configuration = value

    def preview_output_axis(self, value, raw) -> Iterator[PredictionResult]:
        frames = self.last_deps["window"]
        time_step = frames._frames.time_step
        romega = 2.0 * np.pi * np.fft.rfftfreq(2 * frames.n_frames - 1, time_step)
        yield PredictionResult("romega", romega, "rad/ps")

    @property
    def resolution(self) -> IInstrumentResolution:
        return self.kernel

    @property
    def run_resolution(self) -> RunResolution:
        """
        Configure the instrument resolution.

        Returns
        -------
        RunResolution
            Configured parameter set.
        """
        frames = self.last_deps["window"]

        if frames.n_frames < 2:
            raise ConfigError("This analysis requires more time steps")

        time_step = frames._frames.time_step

        # We compute angular frequency AND NOT ORDINARY FREQUENCY ANYMORE

        omega = (
            2.0
            * np.pi
            * np.fft.fftshift(np.fft.fftfreq(2 * frames.n_frames - 1, time_step))
        )

        # generate the rfftfreq for the positive frequency only results
        romega = 2.0 * np.pi * np.fft.rfftfreq(2 * frames.n_frames - 1, time_step)
        resolution = self.resolution
        resolution.set_kernel(omega, time_step)
        time_window = resolution.timeWindow.real

        return RunResolution(
            kernel=type(self.kernel).__name__,
            omega=omega,
            romega=romega,
            resolution_parameters=self.params,
            time_window=time_window,
            omega_window=resolution.omegaWindow,
            time_window_positive=np.fft.ifftshift(time_window)[: frames.window],
        )
