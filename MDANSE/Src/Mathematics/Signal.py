# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Mathematics/Signal.py
# @brief     Implements module/class/test Signal
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import numpy as np

from MDANSE.Core.Error import Error


class SignalError(Error):
    pass


INTERPOLATION_ORDER = {}

INTERPOLATION_ORDER[1] = np.array(
    [[-3.0, 4.0, -1.0], [-1.0, 0.0, 1.0], [1.0, -4.0, 3.0]], dtype=np.float64
)


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
        ts[0] = np.add.reduce(coefs[0, :] * a[:3])
        ts[-1] = np.add.reduce(coefs[2, :] * a[-3:])

        gj = a[1:] - a[:-1]
        ts[1:-1] = gj[1:] + gj[:-1]

        fact /= 2.0

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


def get_spectrum(signal, window=None, timeStep=1.0, axis=0):
    signal = symmetrize(signal, axis)

    if window is None:
        window = np.ones(signal.shape[axis])

    window /= window[len(window) // 2]

    s = [np.newaxis] * signal.ndim
    s[axis] = slice(None)

    s = tuple(s)

    # We compute the unitary inverse fourier transform with angular frequencies as described in
    # https://en.wikipedia.org/wiki/Fourier_transform#Discrete_Fourier_Transforms_and_Fast_Fourier_Transforms

    # For information about the manipulation around fftshift and ifftshift
    # http://www.mathworks.com/matlabcentral/newsreader/view_thread/285244

    fftSignal = (
        0.5
        * np.fft.fftshift(
            np.fft.fft(np.fft.ifftshift(signal * window[s], axes=axis), axis=axis),
            axes=axis,
        )
        * timeStep
        / np.pi
    )
    return fftSignal.real
