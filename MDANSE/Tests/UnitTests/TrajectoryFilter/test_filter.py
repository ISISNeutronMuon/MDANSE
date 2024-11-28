import numpy as np
import math
import pytest

from MDANSE.Mathematics.Signal import Filter, filter_map

def test_freq_to_energy_conversion():
    """
    25.0 pHz to meV
    """
    assert np.round(Filter.freq_to_energy(25.0), 1) == 103.4

def test_energy_to_freq_conversion():
    """
    400.0 meV to pHz
    """
    assert np.round(Filter.energy_to_freq(400.0), 1) == 96.7

def test_simple_lowpass():
    """
    Apply 1st order Butterworth filter to a sinusoid consisting of two frequencies,
    removing the higher of the two.
    """
    filter_class = filter_map["Butterworth"]

    w0 = 2 * np.pi * 1.5
    a0 = 20.0

    w1 = 2 * np.pi * 60.0
    a1 = 5.0




