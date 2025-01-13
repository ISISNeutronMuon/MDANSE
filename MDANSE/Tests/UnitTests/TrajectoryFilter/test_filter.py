import numpy
import numpy as np
from scipy import signal, fftpack
import math
import pytest

from MDANSE.Mathematics.Signal import Filter, filter_map

SIMPLE_HYDROGEN_PATH = 'methane_hydrogen_position.csv'

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

def test_simple_filter_sinusoidal():
    """
    Apply 1st order Butterworth filter to a sinusoid consisting of two frequencies,
    attentuating the higher of the two.
    """
    filter_class = filter_map["Butterworth"]
    filter_class.set_defaults()

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
    fs = (t[1] - t[0])**(-1)
    x = a0 * np.sin(w0 * t) + a1 * np.sin(w1 * t)

    # Instantiate filter
    f = filter_class(**{
        "attenuation_type": "highpass",
        "order": 1,
        "cutoff_freq": 0.5 * w1,
        "time_step_ps": 1/fs,
        "n_steps": N}
    )

    # Apply filter to signal
    post_filter = f.apply(x)

    # Fourier transform results
    post_filter_freqs = {
        "h": fftpack.fft(post_filter),
        "w": fftpack.fftfreq(N, d=1/fs)
    }

    w = post_filter_freqs["w"][:np.int32(N/2)]
    amplitudes = (2 * (np.abs(post_filter_freqs["h"])) / N)[:np.int32(N/2)]

    freqs = signal.find_peaks(amplitudes)

    assert (amplitudes(freqs[0]) > amplitudes(freqs[1]) and amplitudes(freqs[1]) < a1)

def test_simple_filter_methane():
    """
    Apply filter to a methane hydrogen atom trajectory to remove large amplitude motion below 44 meV.
    """
    filter_class = filter_map["ChebyshevTypeI"]
    filter_class.set_defaults()

    hydrogen_atom_traj = numpy.loadtxt(SIMPLE_HYDROGEN_PATH, delimiter=',')

    # Instantiate filter
    f = filter_class(**{
        "n_steps": 10000,
        "time_step_ps": 0.005,
        "order": 2,
        "attenuation_type": "highpass",
        "cutoff_freq": 25.0,
        "max_ripple": 1.0
    })

    # Pre-filter frequency analysis
    pre_filter_freqs = {
        "h": fftpack.fft(hydrogen_atom_traj),
        "w": fftpack.fftfreq(f.n_steps, d=1/f.sample_freq)
    }

    w = pre_filter_freqs["w"][:np.int32(f.n_steps / 2)]
    dw = w[1] - w[0]
    pre_amplitudes = (2 * (np.abs(pre_filter_freqs["h"])) / f.n_steps)[:np.int32(f.n_steps / 2)]

    # Apply designed filter to hydrogen trajectory
    filt_traj = f.apply(hydrogen_atom_traj)

    # Post-filter frequency analysis
    post_filter_freqs = {
        "h": fftpack.fft(filt_traj),
        "w": fftpack.fftfreq(f.n_steps, d=1/f.sample_freq)
    }

    post_amplitudes = (2 * (np.abs(post_filter_freqs["h"])) / f.n_steps)[:np.int32(f.n_steps2)]

    assert (
            np.argsort(post_amplitudes)[-2:][1] == np.argsort(pre_amplitudes)[-2][0] # results in higher frequency, initially smaller peak now the dominant peak
            and w[np.min(np.argsort(post_amplitudes)[-100:])] > 25.0 # and the frequency at which the lowest of the 100 lowest frequency peaks is above the cutoff frequency
    )

def test_filter_job_methane():
    pass
