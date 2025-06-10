import numpy
import numpy as np
from scipy import signal, fftpack
import math
import pytest
import unittest

from MDANSE.Mathematics.Signal import Filter, FILTER_MAP


class TrajectoryFilterTest(unittest.TestCase):
    SIMPLE_HYDROGEN_PATH = "../Data/methane_hydrogen_position.csv"

    def test_angular_freq_to_energy_conversion(self):
        """60.0 rad/ps to meV."""
        self.assertAlmostEqual(Filter.freq_to_energy(59.0, Filter.FrequencyUnits.ANGULAR), 39.0, 0)

    def test_energy_to_angular_freq_conversion(self):
        """39.0 meV to rad/ps."""
        self.assertAlmostEqual(Filter.energy_to_freq(39.0, Filter.FrequencyUnits.ANGULAR), 59.0, 0)

    def test_freq_to_energy_conversion(self):
        """60.0 THz to meV."""
        self.assertAlmostEqual(Filter.freq_to_energy(99.7, Filter.FrequencyUnits.CYCLIC), 412.0, 0)

    def test_energy_to_freq_conversion(self):
        """412.0 meV to THz."""
        self.assertAlmostEqual(Filter.energy_to_freq(412.0, Filter.FrequencyUnits.CYCLIC), 99.7, 0)

    def test_simple_filter_sinusoidal(self):
        """Apply 1st order Butterworth filter to a sinusoid consisting of two frequencies,
        attentuating the higher of the two.

        """
        filter_class = FILTER_MAP["Butterworth"]

        # Angular frequency and amplitude of lower frequency component
        cycles_per_second_0 = 1.5
        w0 = 2 * np.pi * cycles_per_second_0
        a0 = 20.0

        # Angular frequency and amplitude of higher frequency component
        cycles_per_second_1 = 60.0
        w1 = 2 * np.pi * cycles_per_second_1
        a1 = 5.0

        # Generate signal from summation of components
        N = 10000
        t = np.linspace(0, 20, N)
        fs = (t[1] - t[0]) ** (-1)
        x = a0 * np.sin(w0 * t) + a1 * np.sin(w1 * t)

        # Instantiate filter
        f = filter_class(
            attenuation_type="highpass",
            order=1,
            cutoff_freq=0.5 * w1,
            time_step_ps=1 / fs,
            n_steps=N,
        )

        # Apply filter to signal
        post_filter = f.apply(x)

        # Fourier transform results
        post_filter_freqs = {
            "h": fftpack.fft(post_filter),
            "w": fftpack.fftfreq(N, d=1 / fs),
        }

        w = post_filter_freqs["w"][: np.int32(N / 2)]
        amplitudes = (2 * (np.abs(post_filter_freqs["h"])) / N)[: np.int32(N / 2)]

        # Indices of peaks in FFT
        freqs = signal.find_peaks(amplitudes)[0]

        # Check low frequency sinusoid is greatly attenuated
        self.assertTrue(amplitudes[freqs[0]] < a1 * 10e-3)
