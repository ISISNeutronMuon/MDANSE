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
import numpy as np
from enum import Enum
from collections import namedtuple
from typing import Tuple

from abc import ABC, abstractmethod
from scipy import signal, fftpack

from MDANSE.Mathematics.Arithmetic import assign_weights, get_weights, weighted_sum
from MDANSE.Core.Error import Error

from MDANSE.Framework.OutputVariables.IOutputVariable import OutputData


class SignalError(Error):
    pass


INTERPOLATION_ORDER = {}

INTERPOLATION_ORDER[1] = np.array([[-1.0, 1.0], [1.0, -1.0]], dtype=np.float64)


INTERPOLATION_ORDER[2] = np.array(
    [[-3.0, 4.0, -1.0], [-1.0, 0.0, 1.0], [1.0, -4.0, 3.0]], dtype=np.float64
)

INTERPOLATION_ORDER[3] = np.array(
    [
        [-11.0, 18.0, -9.0, 2.0],
        [-2.0, -3.0, 6.0, -1.0],
        [1.0, -6.0, 3.0, 2.0],
        [-2.0, 9.0, -18.0, 11.0],
    ],
    dtype=np.float64,
)

INTERPOLATION_ORDER[4] = np.array(
    [
        [-50.0, 96.0, -72.0, 32.0, -6.0],
        [-6.0, -20.0, 36.0, -12.0, 2.0],
        [2.0, -16.0, 0.0, 16.0, -2.0],
        [-2.0, 12.0, -36.0, 20.0, 6.0],
        [6.0, -32.0, 72.0, -96.0, 50.0],
    ],
    dtype=np.float64,
)

INTERPOLATION_ORDER[5] = np.array(
    [
        [-274.0, 600.0, -600.0, 400.0, -150.0, 24.0],
        [-24.0, -130.0, 240.0, -120.0, 40.0, -6.0],
        [6.0, -60.0, -40.0, 120.0, -30.0, 4.0],
        [-4.0, 30.0, -120.0, 40.0, 60.0, -6.0],
        [6.0, -40.0, 120.0, -240.0, 130.0, 24.0],
        [-24.0, 150.0, -400.0, 600.0, -600.0, 274.0],
    ],
    dtype=np.float64,
)


def correlation(x, y=None, axis=0, sumOverAxis=None, average=None):
    """Returns the numerical correlation between two signals.

    :param x: the first signal.
    :type x: NumPy array

    :param y: if not None, the correlation is performed between `x` and `y`. If None, the autocorrelation of `x` will be computed.
    :type y: NumPy array or None

    :param axis: the axis along which the correlation will be computed.
    :type axis: int

    :param sumOverAxis: if not None, the computed correlations will be sum over a given axis.
    :type sumOverAxis: int or None

    :param average: if not None, the computed correlations will be averaged over a given axis.
    :type average: int or None

    :return: the result of the numerical correlation.
    :rtype: NumPy array

    :note: The correlation is computed using the FCA algorithm.
    """

    x = np.array(x)

    n = x.shape[axis]

    X = np.fft.fft(x, 2 * n, axis=axis)

    if y is not None:
        y = np.array(y)
        Y = np.fft.fft(y, 2 * n, axis=axis)
    else:
        Y = X

    s = [slice(None)] * x.ndim

    s[axis] = slice(0, n, 1)  # the total lenght along 'axis' direction is 2*n
    # s selects all elements along all other directions,
    # and only half the elements along the 'axis' direction.

    s = tuple(s)

    corr = np.real(np.fft.ifft(np.conjugate(X) * Y, axis=axis)[s])

    norm = n - np.arange(n)

    s = [np.newaxis] * x.ndim
    s[axis] = slice(None)

    s = tuple(s)

    corr = corr / norm[s]

    if sumOverAxis is not None:
        corr = np.sum(corr, axis=sumOverAxis)
    elif average is not None:
        corr = np.average(corr, axis=average)

    return corr


def normalisation_factor(x: np.ndarray, axis: int = 0) -> np.ndarray:
    """Normalizes the signal by dividing x by the zeroth elements
    along the input axis.

    Parameters
    ----------
    x : np.ndarray
        The input array to normalize.
    axis : int
        The axis to normalize the array along.

    Returns
    -------
    np.ndarray
        The normalization factors.
    """
    s = [slice(None)] * x.ndim
    s[axis] = slice(0, 1, 1)

    s = tuple(s)
    scaling_factor = x.scaling_factor

    return 1 / (scaling_factor * x[s])


def differentiate(a, dt=1.0, order=1):
    if order not in INTERPOLATION_ORDER:
        raise SignalError("Invalid differentiation order")

    coefs = INTERPOLATION_ORDER[order]

    # outputSeries is the output resulting from the differentiation
    ts = np.zeros(a.shape, dtype=np.float64)

    fact = 1.0 / dt

    if order == 1:
        ts[-1] = np.add.reduce(coefs[1, :] * a[-2:])

        gj = a[1:] - a[:-1]
        ts[:-1] = gj

    # Case of the order 2
    elif order == 2:
        ts[0] = np.add.reduce(coefs[0, :] * a[:3])
        ts[-1] = np.add.reduce(coefs[2, :] * a[-3:])

        gj = np.zeros((a.size - 2, 3), dtype=np.float64)
        gj[:, 0] = coefs[1, 0] * a[:-2]
        gj[:, 1] = coefs[1, 1] * a[1:-1]
        gj[:, 2] = coefs[1, 2] * a[2:]
        ts[1:-1] = np.add.reduce(gj, -1)

        fact /= 2.0

    # Case of the order 3
    elif order == 3:
        # Special case for the first and last elements
        ts[0] = np.add.reduce(coefs[0, :] * a[:4])
        ts[1] = np.add.reduce(coefs[1, :] * a[:4])
        ts[-1] = np.add.reduce(coefs[3, :] * a[-4:])

        # General case
        gj = np.zeros((a.size - 3, 4), dtype=np.float64)
        gj[:, 0] = coefs[2, 0] * a[:-3]
        gj[:, 1] = coefs[2, 1] * a[1:-2]
        gj[:, 2] = coefs[2, 2] * a[2:-1]
        gj[:, 3] = coefs[2, 3] * a[3:]
        ts[2:-1] = np.add.reduce(gj, -1)

        fact /= 6.0

    # Case of the order 4
    elif order == 4:
        # Special case for the first and last elements
        ts[0] = np.add.reduce(coefs[0, :] * a[:5])
        ts[1] = np.add.reduce(coefs[1, :] * a[:5])
        ts[-2] = np.add.reduce(coefs[3, :] * a[-5:])
        ts[-1] = np.add.reduce(coefs[4, :] * a[-5:])

        # General case
        gj = np.zeros((a.size - 4, 5), dtype=np.float64)
        gj[:, 0] = coefs[2, 0] * a[:-4]
        gj[:, 1] = coefs[2, 1] * a[1:-3]
        gj[:, 2] = coefs[2, 2] * a[2:-2]
        gj[:, 3] = coefs[2, 3] * a[3:-1]
        gj[:, 4] = coefs[2, 4] * a[4:]
        ts[2:-2] = np.add.reduce(gj, -1)

        fact /= 24.0

    # Case of the order 5
    elif order == 5:
        # Special case for the first and last elements
        ts[0] = np.add.reduce(coefs[0, :] * a[:6])
        ts[1] = np.add.reduce(coefs[1, :] * a[:6])
        ts[2] = np.add.reduce(coefs[2, :] * a[:6])
        ts[-2] = np.add.reduce(coefs[4, :] * a[-6:])
        ts[-1] = np.add.reduce(coefs[5, :] * a[-6:])

        # General case
        gj = np.zeros((a.size - 5, 6), dtype=np.float64)
        gj[:, 0] = coefs[3, 0] * a[:-5]
        gj[:, 1] = coefs[3, 1] * a[1:-4]
        gj[:, 2] = coefs[3, 2] * a[2:-3]
        gj[:, 3] = coefs[3, 3] * a[3:-2]
        gj[:, 4] = coefs[3, 4] * a[4:-1]
        gj[:, 5] = coefs[3, 5] * a[5:]
        ts[3:-2] = np.add.reduce(gj, -1)

        fact /= 120.0

    ts *= fact

    return ts


def symmetrize(signal, axis=0):
    """Return a symmetrized version of an input signal

    :Parameters:
        #. signal (np.array): the input signal
        #. axis (int): the axis along which the signal should be symmetrized
    :Returns:
        #. np.array: the symmetrized signal
    """

    s = [slice(None)] * signal.ndim
    s[axis] = slice(-1, 0, -1)

    s = tuple(s)

    signal = np.concatenate((signal[s], signal), axis=axis)

    return signal


def get_spectrum(signal, window=None, timeStep=1.0, axis=0, fft="fft"):
    signal = symmetrize(signal, axis)

    if window is None:
        window = np.ones(signal.shape[axis])

    window /= window[len(window) // 2]

    s = [np.newaxis] * signal.ndim
    s[axis] = slice(None)

    s = tuple(s)

    # We compute the non-unitary fourier transform with angular
    # frequencies with a 1/2pi factor applied to the forward transform.
    # This is done for some historical reason see the git history.

    # For information about the manipulation around fftshift and ifftshift
    # http://www.mathworks.com/matlabcentral/newsreader/view_thread/285244

    if fft == "fft":
        fftSignal = (
            0.5
            * np.fft.fftshift(
                np.fft.fft(np.fft.ifftshift(signal * window[s], axes=axis), axis=axis),
                axes=axis,
            )
            * timeStep
            / np.pi
        )
    elif fft == "rfft":
        fftSignal = (
            0.5
            * np.fft.rfft(np.fft.ifftshift(signal * window[s], axes=axis), axis=axis)
            * timeStep
            / np.pi
        )
    else:
        raise ValueError("fft variable should be fft or rfft.")

    return fftSignal.real


# Default filter cutoff frequency in rad/ps
DEFAULT_FILTER_CUTOFF = 25.0


class Filter(ABC):
    """Base class for a filter operating on a signal."""

    # Symbolic variable for analog filter transfer function (Laplace plane)
    S = "iw"

    # Symbolic variable for digital filter transfer function (Z-plane)
    Z = "e^iw"

    # Useful physical constants (from [pwtools](https://github.com/elcorto/pwtools)
    Ry_to_Hz = 3289841960777247.0
    Ry_to_eV = 13.60569193

    # Conversion factor: frequency axis to energies in meV
    _freq_to_mev = 1e3 * Ry_to_eV / Ry_to_Hz

    # Container for the filter transfer tranfer function expressed in terms of the numerator/denominator coefficients of a rational polynomial
    TransferFunction = namedtuple("TransferFunction", ["numerator", "denominator"])

    # Container for the frequency response of the filter
    FrequencyDomain = namedtuple("FrequencyDomain", ["frequencies", "magnitudes"])

    # Coefficients for numerator and denominator of filter transfer function
    _coeffs = None

    # Stores a custom frequency range around which to compute the filter frequency response, as a linear series
    _custom_freq_range = None

    # Frequency response of filter
    _freq_response = None

    # Sample frequency of molecular dynamics simulation being analysed
    _sample_freq = None

    class FrequencyUnits(Enum):
        """Enumeration for frequency unit type"""

        CYCLIC: int = 0
        ANGULAR: int = 1

    class FrequencyRangeMethod(Enum):
        """Enumeration for custom (externally provided) and FFT-derived frequency ranges for plotting the filter response"""

        CUSTOM: int = 0
        FFT: int = 1

    class Flags(Enum):
        """Enumeration for flags associated with useage of filters"""

        DIGITAL_ONLY: int = 0
        DIGITAL_AND_ANALOGUE: int = 1
        FUNDAMENTAL_EVENLY_DIVIDES_FS: int = 2

    @abstractmethod
    def __init__(self, **kwargs):
        # Number of simulation steps
        self.n_steps = kwargs.pop("n_steps")
        # Simulation sample frequency in THz
        self._sample_freq = 1 / kwargs.pop("time_step_ps")
        self.set_filter_attributes(kwargs)

    def compute_frequencies(
        self, transfer_function: TransferFunction, range: np.ndarray
    ):
        """Computes the frequency magnitudes over given frequency range, from the filter transfer function.

        :Parameters:
            #. transfer_function (TransferFunction): the numerator and denominator of the filter transfer function
            #. range (np.ndarray): range of frequency values over which to compute
        :Returns:
            #. np.array: frequency response over a given range
        """

        return signal.freqs(*transfer_function, worN=range)

    def apply(self, input: np.array) -> np.ndarray:
        """Returns the convolution of the digital designed filter with an input signal.

        :Parameters:
            #. input (np.array): the input signal
        :Returns:
            #. np.array: the resulting signal due to convolution with the filter instance
        """
        coeffs = (
            self.to_digital_coeffs()
            if not (Filter.Flags.DIGITAL_ONLY in self.flags)
            else self._coeffs
        )
        return signal.filtfilt(coeffs.numerator, coeffs.denominator, input)

    def to_digital_coeffs(self) -> TransferFunction:
        """Returns the filter instance digital coefficients converted from analog, by performing a bilinear transform

        :Returns:
            #. TransferFunction: Transfer function for filter with digital coefficients
        """
        return self.TransferFunction(
            *signal.bilinear(
                self._coeffs.numerator, self._coeffs.denominator, self._sample_freq
            )
        )

    @property
    def freq_response(self) -> FrequencyDomain:
        """Returns the frequency response of the filter, i.e. amplitude as a function of frequency.

        :Returns:
            #. FrequencyDomain: named tuple containing the x-axis (frequency range) and y-axis (amplitude) of the filter
        """
        return self._freq_response

    @freq_response.setter
    def freq_response(
        self, params: Tuple[TransferFunction, FrequencyRangeMethod]
    ) -> None:
        """Calculates the frequency response of the filter from the filter's transfer function numerator and denominator coefficients.

        :Parameters:
            #. expr (np.array): the rational polynomial expression for the filter transfer function, in terms of its numerator and denominator coefficients
        """
        expr, method = params
        methods = self.__class__.FrequencyRangeMethod

        if method is methods.FFT:
            freq_range = self.frequency_range(self.n_steps, self._sample_freq ** (-1))
        elif self._custom_freq_range.any() and method is methods.CUSTOM:
            freq_range = self._custom_freq_range
        else:
            RuntimeError(
                f"Could not find supplied frequency range around which filter frequency response will be computed. \nPlease set the 'custom_freq_range' attribute on the instance of {self.__class__}"
            )

        # Get frequency response from transfer function expression and specify frequency range around which to compute response
        response = self.compute_frequencies(
            transfer_function=expr, range=np.abs(2 / np.pi * freq_range)
        )
        self._freq_response = self.FrequencyDomain(*response)

    @classmethod
    def frequency_resolution(cls, num_steps: float, timestep: float, units):
        """Returns the frequency resolution of the trajectory given N fixed timesteps.
        Analogous to the bin-width of an FFT of the trajecotry.

        :Parameters:
            #. num_steps (float): Number of simulation timesteps
            #. timestep (float): Simulation timestep in picoseconds
            #. units (FrequencyUnit): Frequency unit type for conversion (i.e. CYCLIC=THz, ANGULAR=rad/ps)
        :Returns:
            #. float: Frequency resolution
        """
        bin_width = 1 / (num_steps * timestep)
        if units == Filter.FrequencyUnits.ANGULAR:
            bin_width *= 2 * np.pi

        return bin_width

    @classmethod
    def nyquist(cls, timestep: float, units) -> float:
        """Returns the nyquist limit for the filter sample frequency.

        :Parameters:
            #. timestep (np.array): Simulation timestep in picoseconds
            #. units (FrequencyUnit): Frequency unit type for conversion (i.e. CYCLIC=THz, ANGULAR=rad/ps)
        :Returns:
            #. float: Nyquist limit
        """
        limit = (1 / timestep) / 2
        if units == Filter.FrequencyUnits.ANGULAR:
            limit *= 2 * np.pi

        return limit

    @staticmethod
    def frequency_range(
        N: int, timestep: float, resize_to: int = 1000, symmetric: bool = False
    ) -> np.ndarray:
        """Obtain an FFT-based frequency range for the frequency domain of a discrete time signal with a given number of elements and a constant time step.

        :Parameters:
            #. N (int): Number of samples in input signal (to which filter will be applied to)
            #. timestep (float): Input signal timestep in picoseconds
            #. resize_to (int): Up- or down- sample the frequency range array to a given length
            #. symmetric (bool): If true, retain symmetric property of frequencies, else take only one half of the frequencies
        :Returns:
            #. np.ndarray: Symbolic polynomial string
        """
        axis_frequencies = fftpack.fftfreq(N, timestep)
        limit = np.int32(np.floor(len(axis_frequencies) / 2)) if not symmetric else -1
        return np.linspace(axis_frequencies[0], axis_frequencies[limit], resize_to)

    def set_filter_attributes(self, attributes: dict) -> None:
        """Update filter instance attributes

        :Parameters:
            #. attributes (dict): Dictionary containing filter attributes
        """
        settings = self.default_settings

        for key, default in settings.items():
            setattr(self, key, attributes.get(key, default["value"]))

    @staticmethod
    def polynomial_string(coeffs, unit, analog: bool = True) -> str:
        """Formats a polynomial into a string that has a symbolic mathematical appearance.

        :Parameters:
            #. coeffs (np.ndarray): Array of polynomial coefficients
            #. unit (str): String representation of the mathematical symbol corresponding to the S or Z planes
        :Returns:
            #. str: Symbolic polynomial string
        """
        if not coeffs.any():
            return ""
        order = len(coeffs) - 1
        expr = ""

        for idx, coeff in enumerate(coeffs):
            power = order - idx if analog else -idx
            if coeff != 0:
                if idx > 0 and coeff > 0:
                    expr += " + "
                elif idx > 0 and coeff < 0:
                    expr += " - "

                abs_coeff = abs(coeff)
                if power == 0:
                    expr += f"{abs_coeff:.3f}"
                elif power == 1:
                    expr += f"{abs_coeff:.3f}*({unit})"
                else:
                    expr += f"{abs_coeff:.3f}*({unit})^{power}"
        return expr

    @classmethod
    def rational_polynomial_string(
        cls, numerator, denominator, analog=True
    ) -> dict[str, str]:
        """Formats a transfer function rational polynomial into a pair of strings.

        :Parameters:
            #. numerator (np.ndarray): Array of coefficients representing the numerator of the transfer function
            #. denominator (np.ndarray): Array of coefficients representing the denominator of the transfer function
            #. analog (bool): The filter is analog (Laplace/S-domain) or digital (Z-domain)
        :Returns:
            #. dict[str, str]: Dictionary of string coefficients representing the transfer function rational polynomial
        """
        if analog:
            # Analogue (Laplace-domain) transfer function
            numerator_str = cls.polynomial_string(numerator, cls.S)
            denominator_str = Filter.polynomial_string(denominator, cls.S)
            return {
                "unit": "S",
                "numerator": numerator_str,
                "denominator": denominator_str,
            }

        # Digital (Z-domain) transfer function
        numerator_str = Filter.polynomial_string(numerator, cls.Z, False)
        denominator_str = Filter.polynomial_string(denominator, cls.Z, False)
        return {"unit": "Z", "numerator": numerator_str, "denominator": denominator_str}

    def attributes_to_string(self, description) -> str:
        """Formats the given filter attribute into a description string.

        :Parameters:
            #. description (str): The description of the attribute as a multiline string
        :Returns:
            #. str: The description string concatenated with substrings for each filer attribute
        """
        settings = self.__class__.__dict__["default_settings"]
        for setting in settings.keys():
            description += f"""
  # {setting}
  {settings[setting]["description"]}
      {self.__dict__[setting]}
            """

        return description

    def __str__(self):
        """Returns a string representation of the filter.

        :Returns:
            #. str: string representation of the filter
        """
        string_representation = f"""Trajectory filter of type {self.__class__.__name__} implemented with the following parameters:

  # sample_freq
  Reciprocal of the molecular dynamics time step, in terahertz
      {self.__dict__["_sample_freq"]}

  # freq_response (analog)
  N coefficients of analog filter transfer function, numerator and denominator (multiples of {Filter.S}^(N-n))
      {tuple(self.__dict__["_coeffs"].numerator), tuple(self.__dict__["_coeffs"].denominator)}

  # freq_response (digital)
  M coefficients of digital filter transfer function, numerator and denominator (multiples of {Filter.Z}^(-m))
      {tuple(self.__dict__["_coeffs"].numerator), tuple(self.__dict__["_coeffs"].denominator)}
        """

        return self.attributes_to_string(string_representation)

    def to_json(self) -> dict:
        """Returns a concise dictionary (json) representation of the filter.

        :Returns:
            #. dict: dictionary containing filter attributes
        """
        return {"Filter": self.__class__.__name__} | {
            k: v for k, v in self.__dict__.items() if k != "_freq_response"
        }

    @classmethod
    def freq_to_energy(cls, freq, units):
        """Returns the energy value (or values) in millielectronvolts (meV), converted from frequency value (or values).

        :Parameters:
            #. freq (float | np.ndarray): frequency
            #. units (FrequencyUnit): Frequency unit type for conversion (i.e. CYCLIC=THz, ANGULAR=rad/ps)
        :Returns:
            #. float | np.ndarray: energy
        """
        scale_factor = 1.0
        if units == Filter.FrequencyUnits.ANGULAR:
            scale_factor *= 2 * np.pi

        if isinstance(freq, list):
            return (1 / scale_factor) * (np.array(freq) * 1e12) * cls._freq_to_mev

        return (1 / scale_factor) * (freq * 1e12) * cls._freq_to_mev

    @classmethod
    def energy_to_freq(cls, energy, units):
        """Returns the frequency value (or values), converted from energy value (or values) in millielectronvolts (meV).

        :Parameters:
            #. energy (float | np.ndarray): energy
            #. units (FrequencyUnit): Frequency unit type for conversion (i.e. CYCLIC=THz, ANGULAR=rad/ps)
        :Returns:
            #. float | np.ndarray: frequency
        """
        scale_factor = 1.0
        if units == Filter.FrequencyUnits.ANGULAR:
            scale_factor *= 2 * np.pi

        if isinstance(energy, list):
            return (np.array(energy) * scale_factor / cls._freq_to_mev) * 1e-12

        return (energy * scale_factor / cls._freq_to_mev) * 1e-12


class Butterworth(Filter):
    """Interface for the Butterworth filter."""

    flags = {Filter.Flags.DIGITAL_AND_ANALOGUE}

    default_settings = {
        "order": {"description": "The order of the filter", "value": 1},
        "attenuation_type": {
            "description": "Filter attenuation type",
            "values": {"lowpass", "highpass", "bandpass", "bandstop"},
            "value": "lowpass",
        },
        "cutoff_freq": {
            "description": "Cutoff frequency/vibrational energy (may be a 2-length array if bandpass/stop)",
            "value": DEFAULT_FILTER_CUTOFF,
        },
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._coeffs = self.TransferFunction(
            *signal.butter(
                self.order,
                self.cutoff_freq,
                btype=self.attenuation_type,
                analog=True,
                output="ba",
            )
        )
        self.freq_response = (self._coeffs, self.__class__.FrequencyRangeMethod.FFT)


class ChebyshevTypeI(Filter):
    """Interface for the Chebyshev type 1 filter."""

    flags = {Filter.Flags.DIGITAL_AND_ANALOGUE}

    default_settings = {
        "order": {"description": "The order of the filter", "value": 1},
        "max_ripple": {
            "description": "Decibel measure of maximum ripple allowed below unit gain in the passband",
            "value": 5.0,
        },
        "attenuation_type": {
            "description": "Filter attenuation type",
            "values": {"lowpass", "highpass", "bandpass", "bandstop"},
            "value": "lowpass",
        },
        "cutoff_freq": {
            "description": "Cutoff frequency/vibrational energy (may be a 2-length array if bandpass/stop)",
            "value": DEFAULT_FILTER_CUTOFF,
        },
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._coeffs = self.TransferFunction(
            *signal.cheby1(
                self.order,
                self.max_ripple,
                self.cutoff_freq,
                btype=self.attenuation_type,
                analog=True,
                output="ba",
            )
        )
        self.freq_response = (self._coeffs, self.__class__.FrequencyRangeMethod.FFT)


class ChebyshevTypeII(Filter):
    """Interface for the Chebyshev type 2 filter."""

    flags = {Filter.Flags.DIGITAL_AND_ANALOGUE}

    default_settings = {
        "order": {"description": "The order of the filter", "value": 1},
        "min_attenuation": {
            "description": "Decibel measure of minimum attenuation required in the stopband",
            "value": 20.0,
        },
        "attenuation_type": {
            "description": "Filter attenuation type",
            "values": {"lowpass", "highpass", "bandpass", "bandstop"},
            "value": "lowpass",
        },
        "cutoff_freq": {
            "description": "Cutoff frequency/vibrational energy (may be a 2-length array if bandpass/stop)",
            "value": DEFAULT_FILTER_CUTOFF,
        },
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._coeffs = self.TransferFunction(
            *signal.cheby2(
                self.order,
                self.min_attenuation,
                self.cutoff_freq,
                btype=self.attenuation_type,
                analog=True,
                output="ba",
            )
        )
        self.freq_response = (self._coeffs, self.__class__.FrequencyRangeMethod.FFT)


class Elliptical(Filter):
    """Interface for the elliptical filter."""

    flags = {Filter.Flags.DIGITAL_AND_ANALOGUE}

    default_settings = {
        "order": {"description": "The order of the filter", "value": 1},
        "max_ripple": {
            "description": "Decibel measure of maximum ripple allowed below unit gain in the passband",
            "value": 5.0,
        },
        "min_attenuation": {
            "description": "Decibel measure of minimum attenuation required in the stopband",
            "value": 20.0,
        },
        "attenuation_type": {
            "description": "Filter attenuation type",
            "values": {"lowpass", "highpass", "bandpass", "bandstop"},
            "value": "lowpass",
        },
        "cutoff_freq": {
            "description": "Cutoff frequency/vibrational energy (may be a 2-length array if bandpass/stop)",
            "value": DEFAULT_FILTER_CUTOFF,
        },
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._coeffs = self.TransferFunction(
            *signal.ellip(
                self.order,
                self.max_ripple,
                self.min_attenuation,
                self.cutoff_freq,
                btype=self.attenuation_type,
                analog=True,
                output="ba",
            )
        )
        self.freq_response = (self._coeffs, self.__class__.FrequencyRangeMethod.FFT)


class Bessel(Filter):
    """Interface for the Bessel filter."""

    flags = {Filter.Flags.DIGITAL_AND_ANALOGUE}

    default_settings = {
        "order": {"description": "The order of the filter", "value": 1},
        "norm": {
            "description": "Filter normalization results in the following behaviour at cutoff - phase: phase response obtains midpoint - delay: group delay in passband is the reciprocal of cutoff - mag: gain magnitude is -3 dB",
            "values": {"phase", "delay", "mag"},
            "value": "phase",
        },
        "attenuation_type": {
            "description": "Filter attenuation type",
            "values": {"lowpass", "highpass", "bandpass", "bandstop"},
            "value": "lowpass",
        },
        "cutoff_freq": {
            "description": "Cutoff frequency/vibrational energy (may be a 2-length array if bandpass/stop)",
            "value": DEFAULT_FILTER_CUTOFF,
        },
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._coeffs = self.TransferFunction(
            *signal.bessel(
                self.order,
                self.cutoff_freq,
                btype=self.attenuation_type,
                analog=True,
                output="ba",
                norm=self.norm,
            )
        )
        self.freq_response = (self._coeffs, self.__class__.FrequencyRangeMethod.FFT)


class Notch(Filter):
    """Interface for the notch filter."""

    flags = {Filter.Flags.DIGITAL_ONLY}

    default_settings = {
        "fundamental_freq": {
            "description": "Spacing between filter peaks (value must satisfy 0 < w0 < nyquist)",
            "value": DEFAULT_FILTER_CUTOFF,
        },
        "quality_factor": {
            "description": "Specifies bandwidth, proportional to time taken for filter to decay by a factor of 1/e",
            "value": 1.0,
        },
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._coeffs = self.TransferFunction(
            *signal.iirnotch(
                self.fundamental_freq, self.quality_factor, fs=self._sample_freq
            )
        )
        self.freq_response = (self._coeffs, self.__class__.FrequencyRangeMethod.FFT)

    def compute_frequencies(
        self, transfer_function: Filter.TransferFunction, range: np.ndarray
    ):
        """Computes the frequency magnitudes over given frequency range, from the filter transfer function.

        :Parameters:
            #. transfer_function (TransferFunction): the numerator and denominator of the filter transfer function
            #. range (np.ndarray): range of frequency values over which to compute
        :Returns:
            #. np.array: frequency response over a given range
        """

        return signal.freqz(*transfer_function, worN=range, fs=self._sample_freq)


class Peak(Filter):
    """Interface for the peak filter."""

    flags = {Filter.Flags.DIGITAL_ONLY}

    default_settings = {
        "fundamental_freq": {
            "description": "Spacing between filter peaks (value must satisfy 0 < w0 < nyquist)",
            "value": DEFAULT_FILTER_CUTOFF,
        },
        "quality_factor": {
            "description": "Specifies bandwidth, proportional to time taken for filter to decay by a factor of 1/e",
            "value": 1.0,
        },
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._coeffs = self.TransferFunction(
            *signal.iirpeak(
                self.fundamental_freq, self.quality_factor, fs=self._sample_freq
            )
        )
        self.freq_response = (self._coeffs, self.__class__.FrequencyRangeMethod.FFT)

    def compute_frequencies(
        self, transfer_function: Filter.TransferFunction, range: np.ndarray
    ):
        """Computes the frequency magnitudes over given frequency range, from the filter transfer function.

        :Parameters:
            #. transfer_function (TransferFunction): the numerator and denominator of the filter transfer function
            #. range (np.ndarray): range of frequency values over which to compute
        :Returns:
            #. np.array: frequency response over a given range
        """

        return signal.freqz(*transfer_function, worN=range, fs=self._sample_freq)


class Comb(Filter):
    """Interface for the comb filter."""

    flags = {Filter.Flags.DIGITAL_ONLY, Filter.Flags.FUNDAMENTAL_EVENLY_DIVIDES_FS}

    default_settings = {
        "fundamental_freq": {
            "description": "Spacing between filter peaks (value must evenly divide sample frequency)",
            "value": DEFAULT_FILTER_CUTOFF,
        },
        "quality_factor": {
            "description": "Specifies bandwidth, proportional to time taken for filter to decay by a factor of 1/e",
            "value": 1.0,
        },
        "comb_type": {
            "description": "Determines whether quality factor applies to notches or peaks",
            "values": {"peak", "notch"},
            "value": "notch",
        },
        "pass_zero": {
            "description": "Determines whether notches or peaks centered on integer multiples of fundamental frequency",
            "values": {True, False},
            "value": False,
        },
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._coeffs = self.TransferFunction(
            *signal.iircomb(
                self.fundamental_freq,
                self.quality_factor,
                ftype=self.comb_type,
                pass_zero=self.pass_zero,
                fs=self._sample_freq,
            )
        )
        self.freq_response = (self._coeffs, self.__class__.FrequencyRangeMethod.FFT)

    def compute_frequencies(
        self, transfer_function: Filter.TransferFunction, range: np.ndarray
    ):
        """Computes the frequency magnitudes over given frequency range, from the filter transfer function.

        :Parameters:
            #. transfer_function (TransferFunction): the numerator and denominator of the filter transfer function
            #. range (np.ndarray): range of frequency values over which to compute
        :Returns:
            #. np.array: frequency response over a given range
        """

        return signal.freqz(*transfer_function, worN=range, fs=self._sample_freq)


FILTERS = (
    Butterworth,
    ChebyshevTypeI,
    ChebyshevTypeII,
    Elliptical,
    Bessel,
    Notch,
    Peak,
    Comb,
)

FILTER_MAP = {filter_class.__name__: filter_class for filter_class in FILTERS}

# Default filter type is Butterworth
DEFAULT_FILTER = Butterworth

# Default simulation time step in picoseconds
DEFAULT_TIME_STEP = 0.005

# Default number of simulation steps
DEFAULT_N_STEPS = 320


def filter_default_attributes(filter=DEFAULT_FILTER):
    """Get the filter-specific settings dictionary for a filter class.

    :Parameters:
        #. filter (Filter) :  The filter class.
    :Returns:
        #. The filter settings dictionary
    """
    return {
        setting: values["value"] for setting, values in filter.default_settings.items()
    }


def filter_description_string(
    filter=DEFAULT_FILTER, settings=filter_default_attributes(DEFAULT_FILTER)
) -> str:
    """Convert a filter class and filter settings dictionary to a string.

    :Parameters:
        #. filter (str) : The filter class
        #. settings (dict) : Dictionary containing the filter settings
    :Returns:
        #. str: string representation of the filter settings dictionary
    """
    return f'{{ "filter": "{filter.__name__}", "attributes": {json.dumps(settings)}}}'


def power_spectrum(
    trajectory, frames, projection, atom_selection, weights, instrument_resolution
) -> Tuple[np.ndarray, np.ndarray]:
    """Returns the position power spectrum of a configuration's constituent atomic trajectories.

    :Parameters:
        #. trajectory (HDFTrajectoryConfigurator): atomic trajectory object
        #. frames (CorrelationFramesConfigurator): frames object
        #. projection (ProjectionConfigurator): projection object
        #. atom_selection (AtomSelectionConfigurator): atom selection object
        #. weights (WeightsConfigurator): weights object
        #. instrument_resolution (InstrumentResolutionConfigurator): instrument resolution object
    :Returns:
        #. Tuple[np.ndarray, np.ndarray]: tuple containing the omegas (frequency range) and the corresponding power spectrum of the atomic trajectories
    """
    trajectory = trajectory["instance"]

    output = OutputData()
    output.add(
        "romega", "LineOutputVariable", instrument_resolution["romega"], units="rad/ps"
    )

    for element in atom_selection["unique_names"]:
        output.add(
            f"pacf_{element}",
            "LineOutputVariable",
            np.zeros_like(output["romega"]),
            units="nm2",
        )

        output.add(
            f"pps_{element}",
            "LineOutputVariable",
            np.zeros_like(output["romega"]),
            units="au",
        )

    output.add(
        "pacf_total", "LineOutputVariable", np.zeros(frames["n_frames"]), units="nm2"
    )

    output.add(
        "pps_total", "LineOutputVariable", np.zeros_like(output["romega"]), units="nm2"
    )

    for indices, name in zip(atom_selection["indices"], atom_selection["names"]):
        series = trajectory.read_com_trajectory(
            indices,
            first=frames["first"],
            last=frames["last"] + 1,
            step=frames["step"],
        )

        series = series - np.average(series, axis=0)
        series = projection["projector"](series)

        n_configs = frames["n_configs"]
        atomicPACF = signal.correlate(series, series[:n_configs], mode="valid") / (
            3 * n_configs
        )

        output[f"pacf_{name}"] += np.array([x[0] for x in atomicPACF])

    nAtomsPerElement = atom_selection.get_natoms()
    for element, number in nAtomsPerElement.items():
        output[f"pacf_{element}"][:] /= number
        output[f"pps_{element}"][:] = get_spectrum(
            output[f"pacf_{element}"],
            instrument_resolution["time_window"],
            instrument_resolution["time_step"],
            fft="rfft",
        )

    weights = weights.get_weights()
    weight_dict = get_weights(weights, nAtomsPerElement, 1)
    assign_weights(output, weight_dict, "pacf_%s")
    assign_weights(output, weight_dict, "pps_%s")
    output["pacf_total"][:] = weighted_sum(output, weight_dict, "pacf_%s")
    output["pps_total"][:] = weighted_sum(output, weight_dict, "pps_%s")

    # Adjust to atom selection
    return (output["romega"], output["pps_total"])
