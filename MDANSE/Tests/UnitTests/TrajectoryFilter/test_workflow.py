import json
import tempfile
import os
from os import path
import pytest
import h5py
import scipy
import numpy as np

from MDANSE.Mathematics.Signal import FILTER_MAP, Filter

from MDANSE.Framework.Jobs.IJob import IJob

from MDANSE_GUI.Tabs.Models.PlottingContext import SingleDataset

from test_helpers.paths import CONV_DIR, RESULTS_DIR

SRTIO3_TRAJ = "cp2k_srtio3_unfiltered.mdt"

# Test results must satisfy a 5% tolerance to error
TOLERANCE = 5


@pytest.fixture(scope="module")
def unfiltered_power_spectrum(tmp_path_factory):
    """Fixture returns the output file of the PositionPowerSpectrum job with the SrTiO3 trajectory as the input."""

    temp_name = tmp_path_factory.mktemp("data") / "unfiltered_power_spectrum"
    out_file = temp_name.with_suffix(".mda")

    parameters = {
        "atom_selection": "{}",
        "atom_transmutation": "{}",
        "frames": [0, 320, 1, 160],
        "instrument_resolution": ("ideal", {}),
        "output_files": (temp_name, ["MDAFormat"], "no logs"),
        "projection": ("NullProjector", []),
        "running_mode": ("single-core",),
        "trajectory": CONV_DIR / SRTIO3_TRAJ,
        "weights": "atomic_weight",
    }

    power_spectrum = IJob.create("PositionPowerSpectrum")
    power_spectrum.run(parameters, status=True)

    yield out_file


@pytest.mark.parametrize(
    "filter_config",
    [
        {
            "filter": "Butterworth",
            "attributes": {
                "n_steps": 320,
                "time_step_ps": 0.005,
                "order": 1,
                "attenuation_type": "lowpass",
                "cutoff_freq": 19.635,
            },
        },
        {
            "filter": "Butterworth",
            "attributes": {
                "n_steps": 320,
                "time_step_ps": 0.005,
                "order": 1,
                "attenuation_type": "highpass",
                "cutoff_freq": 31.416,
            },
        },
        {
            "filter": "ChebyshevTypeII",
            "attributes": {
                "n_steps": 320,
                "time_step_ps": 0.005,
                "order": 1,
                "min_attenuation": 12.7,
                "attenuation_type": "bandpass",
                "cutoff_freq": [27.489000000000004, 376.992],
            },
        },
        {
            "filter": "Bessel",
            "attributes": {
                "n_steps": 320,
                "time_step_ps": 0.005,
                "order": 1,
                "norm": "phase",
                "attenuation_type": "bandstop",
                "cutoff_freq": [27.489000000000004, 70.686],
            },
        },
    ],
)
def test_filtered_functional_form(tmp_path, unfiltered_power_spectrum, filter_config):
    """The performance of the MDANSE trajectory filter is tested by analysing functional form.
    In this case we compare the form of the power spectrum function of the filtered trajectory against the
    power spectrum of the unfiltered trajectory.

    The convolution theorem

        x(t) * h(t) = X(w)H(w)

    states that convolution in the time domain is equivalent to multiplication in the frequency domain.
    Therefore, the power spectrum of the filtered trajectory, F(w), should be close (with some tolerance) to the product
    of the unfiltered trajectory power spectrum, U(w), and the filter frequency response, H(w).

    The deviation from the convolution theorem is assessed by taking the mean of the absolute error, | U(w)H(w) - F(w) |
    """

    # Retrieve U(w), check the data is as expected
    original_data = SingleDataset(
        "pps_total", h5py.File(unfiltered_power_spectrum, "r+")
    )
    u_x_axis_name = original_data.available_x_axes()

    assert u_x_axis_name == ["romega"]
    assert original_data._axes_units[u_x_axis_name[0]] == "rad/ps"

    u_x_axis = original_data._axes["romega"]

    assert np.round(u_x_axis.min(), 0) == 0
    assert np.round(u_x_axis.max(), 0) == 626

    uw = original_data.data

    # Retrieve filter configuration dict
    filter_class = FILTER_MAP[filter_config["filter"]]

    # Instantiate filter object
    filter_object = filter_class(**filter_config["attributes"])

    # Supply frequencies against which to calculate response H(w)
    filter_object.custom_freq_range = u_x_axis
    filter_object.freq_response = (
        filter_object.coeffs,
        Filter.FrequencyRangeMethod.CUSTOM,
    )

    assert np.round(filter_object.freq_response.frequencies.min(), 0) == 0
    assert np.round(filter_object.freq_response.frequencies.max(), 0) == 626

    # Resample H(w) to length of U(w)
    hw = np.abs(scipy.signal.resample(filter_object.freq_response.magnitudes, len(uw)))

    assert np.isclose(hw.max(), 1, 10e-3)

    # Compute the frequency domain convolution U(w)H(w) that we will compare F(w) with
    conv = hw * uw

    # Run TrajectoryFilter job on the input trajectory
    f_name = "filtered_trajectory"
    temp_name = tmp_path / f_name
    f_trajectory_out_file = temp_name.with_suffix(".mdt")

    trajectory_filter_parameters = {
        "atom_selection": "{}",
        "frames": [0, 320, 1, 160],
        "instrument_resolution": ("ideal", {}),
        "output_files": (temp_name, 64, 128, "gzip", "no logs"),
        "projection": ("NullProjector", []),
        "running_mode": ("single-core",),
        "trajectory": CONV_DIR / SRTIO3_TRAJ,
        "trajectory_filter": json.dumps(filter_config),
        "weights": "atomic_weight",
    }

    trajectory_filter_job = IJob.create("TrajectoryFilter")
    trajectory_filter_job.run(trajectory_filter_parameters, status=True)

    assert f_trajectory_out_file.is_file()

    # Run PositionPowerSpectrum job on the filtered trajectory
    temp_name = tmp_path / "filtered_power_spectrum"
    fw_out_file = temp_name.with_suffix(".mda")

    parameters = {
        "atom_selection": "{}",
        "atom_transmutation": "{}",
        "frames": [0, 320, 1, 160],
        "instrument_resolution": ("ideal", {}),
        "output_files": (temp_name, ["MDAFormat"], "no logs"),
        "projection": ("NullProjector", []),
        "running_mode": ("single-core",),
        "trajectory": f_trajectory_out_file,
        "weights": "atomic_weight",
    }

    fw_job = IJob.create("PositionPowerSpectrum")
    fw_job.run(parameters, status=True)

    assert fw_out_file.is_file()

    # Retrieve F(w), check the data is as expected
    filtered_data = SingleDataset("pps_total", h5py.File(fw_out_file, "r+"))
    f_x_axis_name = original_data.available_x_axes()

    assert f_x_axis_name == ["romega"]
    assert original_data._axes_units[f_x_axis_name[0]] == "rad/ps"

    f_x_axis = original_data._axes["romega"]

    assert np.round(f_x_axis.min(), 0) == 0
    assert np.round(f_x_axis.max(), 0) == 626

    fw = filtered_data.data

    assert len(fw) == len(uw)

    # Calculate differences between U(w)H(w) and F(w)
    normalisation_coeff = 100 / conv.max()
    normalised = (conv * normalisation_coeff, fw * normalisation_coeff)

    error = np.mean(np.abs(normalised[0] - normalised[1]))
    assert np.isclose(error, 0, atol=TOLERANCE)
