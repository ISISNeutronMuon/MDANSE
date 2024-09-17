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
from enum import Enum
from collections import namedtuple
from functools import partial

import scipy.signal
from scipy import signal

from MDANSE.Core.Error import Error


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


def normalize(x, axis=0):
    s = [slice(None)] * x.ndim
    s[axis] = slice(0, 1, 1)

    s = tuple(s)

    nx = x / x[s]
    return nx


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


class Filter1D:
    """Base class for a filter operating on a 1-dimensional signal.
    """

    # Container for the filter transfer tranfer function expressed in terms of the numerator/denominator coefficients of a rational polynomial
    TransferFunction = namedtuple('TransferFunction', ['numerator', 'denominator'])

    # Container for the frequency response of the filter
    FrequencyDomain = namedtuple('FrequencyDomain', ['range', 'frequencies'])

    # Coefficients for numerator and denominator of filter transfer function
    _coeffs = None

    # Frequency response of filter
    _freq_response = None

    def __init__(self, filter, inputs: dict):
        if not hasattr(filter, 'default_settings'):
            filter.__class__.set_defaults()

        self.set_filter_attributes(filter, inputs)

    def apply(self, input: np.array) -> np.ndarray:
        """Returns the convolution of the designed filter with an input signal.

        :Parameters:
            #. input (np.array): the input signal
        :Returns:
            #. np.array: the resulting signal due to convolution with the filter instance
        """
        return signal.filtfilt(self.coeffs.numerator, self.coeffs.denominator, input)

    @property
    def freq_response(self) -> FrequencyDomain:
        """Returns the frequency response of the filter, i.e. amplitude as a function of frequency.

        :Returns:
            #. FrequencyDomain: named tuple containing the x-axis (frequency range) and y-axis (amplitude) of the filter
        """
        return self._freq_response

    @freq_response.setter
    def freq_response(self, expr: TransferFunction) -> None:
        """Calculates the frequency response of the filter from the filter's transfer function numerator and denominator coefficients.

        :Parameters:
            #. expr (np.array): the rational polynomial expression for the filter transfer function, in terms of its numerator and denominator coefficients
        """
        self._freq_response = signal.freqs(self.FrequencyDomain(*expr))

    @property
    def coeffs(self) -> TransferFunction:
        """Returns the filter's transfer function numerator and denominator coefficients.

        """
        return self._coeffs

    @coeffs.setter
    def coeffs(self, expr: TransferFunction) -> None:
        """Sets the filter's transfer function numerator and denominator coefficients.

        :Parameters:
            #. expr (np.array): the rational polynomial expression for the filter transfer function, in terms of its numerator and denominator coefficients
        """
        self._coeffs = expr

    def set_filter_attributes(self, filter, attributes: dict) -> None:
        """

        """
        settings = filter.default_settings

        for attr in settings.keys():
            filter.__dict__.update(
                {
                    attr: attributes.get(attr, settings[attr]['value'])
                }
            )


class Butterworth(Filter1D):
    """Interface for the butterworth filter.

    Frequency response: flat passband with a smooth roll off, making it ideal for low-pass filter operations.
    """
    callable = signal.butter

    @classmethod
    def set_defaults(cls):
        """Set up the default filter settings.
        """
        cls.default_settings = {
            "order": {
                "value": 4
            },
            "critical_freq": {
                "value": []
            },
            "type": {
                "values": {"lowpass", "highpass", "bandpass", "bandstop"},
                "value": "low"
            },
            "analog": {
                "values": {True, False},
                "value": False
            },
            "output": {
                "values": {"ba", "zpk", "sos"},
                "value": "sos"
            },
            "sample_freq": {
                "value": 1.0
            }
        }

    def __init__(self, **kwargs):
        super().__init__(self, **kwargs)

        self.coeffs = self.TransferFunction(
            *self.callable(self.order, self.critical_freq, btype=self.type, analog=self.analog, output=self.output, fs=self.sample_freq)
        )
        self.freq_response = self.coeffs


class ChebyshevTypeI(Filter1D):
    """
    """
    callable = signal.cheby1

    @classmethod
    def setDefaults(cls):
        """Set up the default filter settings.
        """
        cls.default_settings = {
            "order": {
                "value": 4
            },
            "critical_freq": {
                "value": []
            },
            "type": {
                "values": {"lowpass", "highpass", "bandpass", "bandstop"},
                "value": "low"
            },
            "analog": {
                "values": {True, False},
                "value": False
            },
            "output": {
                "values": {"ba", "zpk", "sos"},
                "value": "ba"
            },
            "sample_freq": {
                "value": 1.0
            },
            "max_ripple": {
                "value": 1.0
            }
        }

    def __init__(self, **kwargs):
        super().__init__(self, **kwargs)

        self.coeffs = self.TransferFunction(
            *self.callable(self.order, self.max_ripple, self.critical_freq, btype=self.type, analog=self.analog, output=self.output, fs=self.sample_freq)
        )
        self.freq_response = self.coeffs


class ChebyshevTypeII(Filter1D):
    """
    """
    callable = signal.cheby2

    @classmethod
    def setDefaults(cls):
        """Set up the default filter settings.
        """
        cls.default_settings = {
            "order": {
                "value": 4
            },
            "critical_freq": {
                "value": []
            },
            "type": {
                "values": {"lowpass", "highpass", "bandpass", "bandstop"},
                "value": "low"
            },
            "analog": {
                "values": {True, False},
                "value": False
            },
            "output": {
                "values": {"ba", "zpk", "sos"},
                "value": "ba"
            },
            "sample_freq": {
                "value": 1.0
            },
            "min_attenuation": {
                "value": 0
            }
        }

    def __init__(self, **kwargs):
        super().__init__(self, **kwargs)

        self.coeffs = self.TransferFunction(
            *self.callable(self.order, self.critical_freq, btype=self.type, analog=self.analog, output=self.output, fs=self.sample_freq)
        )
        self.freq_response = self.coeffs


class Elliptical(Filter1D):
    """
    """
    callable = signal.ellip

    @classmethod
    def setDefaults(cls):
        """Set up the default filter settings.
        """
        cls.default_settings = {
            "order": {
                "value": 4
            },
            "critical_freq": {
                "value": []
            },
            "type": {
                "values": {"lowpass", "highpass", "bandpass", "bandstop"},
                "value": "low"
            },
            "analog": {
                "values": {True, False},
                "value": False
            },
            "output": {
                "values": {"ba", "zpk", "sos"},
                "value": "ba"
            },
            "sample_freq": {
                "value": 1.0
            }
        }

    def __init__(self, **kwargs):
        super().__init__(self, **kwargs)

        self.coeffs = self.TransferFunction(
            *self.callable(self.order, self.critical_freq, btype=self.type, analog=self.analog, output=self.output, norm=self.normalization, fs=self.sample_freq)
        )
        self.freq_response = self.coeffs


class Bessel(Filter1D):
    """
    """
    callable = signal.bessel

    @classmethod
    def setDefaults(cls):
        """Set up the default filter settings.
        """
        cls.default_settings = {
            "order": {
                "value": 4
            },
            "critical_freq": {
                "value": []
            },
            "type": {
                "values": {"lowpass", "highpass", "bandpass", "bandstop"},
                "value": "low"
            },
            "analog": {
                "values": {True, False},
                "value": False
            },
            "output": {
                "values": {"ba", "zpk", "sos"},
                "value": "ba"
            },
            "sample_freq": {
                "value": 1.0
            },
            "norm": {
                "values": {"phase", "delay", "mag"},
                "value": "phase"
            }
        }

    def __init__(self, **kwargs):
        super().__init__(self, **kwargs)

        self.coeffs = self.TransferFunction(
            *self.callable(self.order, self.critical_freq, btype=self.type, analog=self.analog, output=self.output, norm=self.normalization, fs=self.sample_freq)
        )
        self.freq_response = self.coeffs


class Notch(Filter1D):
    """
    """
    callable = signal.iirnotch

    @classmethod
    def setDefaults(cls):
        """Set up the default filter settings.
        """
        cls.default_settings = {
            "fundamental_freq": {
                "value": 1.0
            },
            "quality_factor": {
                "value": 1.0
            },
            "sample_freq": {
                "value": 1.0
            }
        }

    def __init__(self, **kwargs):
        super().__init__(self, **kwargs)

        self.coeffs = self.TransferFunction(
            *self.callable(self.fundamental_freq, self.quality_factor, fs=self.sample_freq)
        )
        self.freq_response = self.coeffs


class Peak(Filter1D):
    """
    """
    callable = signal.iirpeak

    @classmethod
    def setDefaults(cls):
        """Set up the default filter settings.
        """
        cls.default_settings = {
            "fundamental_freq": {
                "value": 1.0
            },
            "quality_factor": {
                "value": 1.0
            },
            "sample_freq": {
                "value": 1.0
            }
        }

    def __init__(self, **kwargs):
        super().__init__(self, **kwargs)

        self.coeffs = self.TransferFunction(
            *self.callable(self.fundamental_freq, self.quality_factor, fs=self.sample_freq)
        )
        self.freq_response = self.coeffs


class Comb(Filter1D):
    """
    """
    callable = signal.iircomb

    @classmethod
    def setDefaults(cls):
        """Set up the default filter settings.
        """
        cls.default_settings = {
            "fundamental_freq": {
                "value": 1.0
            },
            "quality_factor": {
                "value": 1.0
            },
            "comb_type": {
                "values": {"peak", "notch"},
                "value": "notch"
            },
            "sample_freq": {
                "value": 1.0
            },
            "pass_zero": {
                "values": {True, False},
                "value":  False
            }
        }

    def __init__(self, **kwargs):
        super().__init__(self, **kwargs)

        self.coeffs = self.TransferFunction(
            *self.callable(self.fundamental_freq, self.quality_factor, ftype=self.comb_type, fs=self.sample_freq, pass_zero=self.pass_zero)
        )
        self.freq_response = self.coeffs
