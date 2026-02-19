import json
from typing import Generator, Any
from pathlib import Path
import pytest
import h5py
import numpy as np

from MDANSE.MolecularDynamics.Trajectory import Trajectory

from MDANSE.Mathematics.Signal import FILTER_MAP, Filter

from scipy.interpolate import interp1d
from scipy.signal import find_peaks
from scipy.integrate import trapezoid as trap

from MDANSE.Framework.Jobs.IJob import IJob

from test_helpers.paths import CONV_DIR, RESULTS_DIR

# Trajectory constants
SINGLE_BIMODAL_ATOM_TRAJ = "simple_bimodal_atom.mdt"

SRTIO3_TRAJ = "cp2k_srtio3_unfiltered.mdt"

CUAU_TRAJ = "CuAu_asap_10fs-step_unfiltered.mdt"

GLYCYL_L_ALANINE_TRAJ = "glycyl_l_alanine_charmm_unfiltered.mdt"

SUFFIX = "_unfiltered_power_spectrum"


TWOPI = 2 * np.pi


def safe_mda(filename):
    ext = filename.suffix
    stripped = filename.with_suffix("").name
    stripped += f".mdt{SUFFIX}"
    return filename.with_name(stripped + ext)


class LocalDataset:
    """Mimics the SingleDataset class from MDANSE GUI."""

    def __init__(self, name: str, source: h5py.File):
        self._name = name
        self._filename = source.filename
        self._data_limits = None
        self._data = source[name][:]
        self._data_unit = source[name].attrs["units"]
        self._n_dim = len(self._data.shape)
        self._axes_tag = source[name].attrs["axis"]
        self._scaling_factor = 1.0
        self._scaling_factor = float(source[name].attrs["scaling_factor"])
        self._axes = {}
        self._axes_units = {}
        if self._axes_tag == "index":
            for dim_number, dim_length in enumerate(self._data.shape):
                self._axes[f"index{dim_number}"] = np.arange(dim_length)
                self._axes_units[f"index{dim_number}"] = "N/A"
            return
        self._current_units = {}
        self._axes_scaling = {}
        self._axes_order = []
        for ax_number, axis_name in enumerate(self._axes_tag.split("|")):
            aname = axis_name.strip()
            if aname == "index":
                axis_key = aname + str(ax_number)
                self._axes[axis_key] = np.arange(len(self._data))
                self._axes_units[axis_key] = "N/A"
            else:
                axis_key = aname
                self._axes[axis_key] = source[axis_key][:]
                self._axes_units[axis_key] = source[axis_key].attrs["units"]
            self._axes_order.append(axis_key)
            self._axes_scaling[axis_key] = 1.0
            self._current_units[axis_key] = self._axes_units[axis_key]


def run_trajectory_filter(
    name: Path, config: dict, n_atoms: int, traj_path: Path
) -> Path:
    """Runs the TrajectoryFilter job.

    Parameters
    ----------
    name : Path
        Temporary path to output trajectory.
    config : dict
        Filter configuration dictionary.
    frames : list
        List of trajectory frames.
    n_atoms : int
        Number of atoms indices to use.
    name : Path
        Temporary path to output trajectory.

    Returns
    -------
    Path
        Path to output trajectory.

    """
    out_file = name.with_suffix(".mdt")

    trajectory_filter_parameters = {
        "atom_selection": f'{{"0": {{"function_name": "select_all", "operation_type": "union"}}, "1": {{"function_name": "select_atoms", "index_range": [0, {n_atoms}], "operation_type": "intersection"}}}}',
        # "frames": frames,
        "instrument_resolution": ("ideal", {}),
        "output_files": (name, 64, 128, "gzip", "no logs"),
        "projection": ("NullProjector", []),
        "running_mode": ("single-core",),
        "trajectory": traj_path,
        "trajectory_filter": json.dumps(config),
        "weights": "atomic_weight",
    }

    trajectory_filter_job = IJob.create("TrajectoryFilter")
    trajectory_filter_job.run(trajectory_filter_parameters, status=True)

    return out_file


def run_power_spectrum(name: Path, frames, n_atoms, traj_path: Path) -> Path:
    """Runs the PositionPowerSpectrum job.

    Parameters
    ----------
    name : Path
        Temporary path to output file.
    traj_path : Path
        Temporary path to trajectory.

    Returns
    -------
    Path
        Path to output file.

    """
    out_file = name.with_suffix(".mda")

    parameters = {
        "atom_selection": f'{{"0": {{"function_name": "select_all", "operation_type": "union"}}, "1": {{"function_name": "select_atoms", "index_range": [0, {n_atoms}], "operation_type": "intersection"}}}}',
        "frames": frames,
        "atom_transmutation": "{}",
        "instrument_resolution": ("ideal", {}),
        "output_files": (name, ["MDAFormat"], "no logs"),
        "projection": ("NullProjector", []),
        "running_mode": ("single-core",),
        "trajectory": traj_path,
        "weights": "atomic_weight",
    }

    power_spectrum = IJob.create("PositionPowerSpectrum")
    power_spectrum.run(parameters, status=True)

    return out_file


@pytest.fixture(scope="module")
def bimodal_spectrum_clean(tmp_path_factory):
    """Fixture returns the output file of the PositionPowerSpectrum job with the single atom containing two vibrational modes."""

    yield run_power_spectrum(
        tmp_path_factory.mktemp("data") / f"{SINGLE_BIMODAL_ATOM_TRAJ}{SUFFIX}",
        [0, 4000, 1, 2000],
        1,
        CONV_DIR / SINGLE_BIMODAL_ATOM_TRAJ,
    )


@pytest.fixture(scope="module")
def srtio3_spectrum_clean(tmp_path_factory):
    """Fixture returns the output file of the PositionPowerSpectrum job with the cp2k SrTiO3 trajectory as the input."""

    yield run_power_spectrum(
        tmp_path_factory.mktemp("data") / f"{SRTIO3_TRAJ}{SUFFIX}",
        [0, 320, 1, 160],
        60,
        CONV_DIR / SRTIO3_TRAJ,
    )


@pytest.fixture(scope="module")
def cuau_spectrum_clean(tmp_path_factory):
    """Fixture returns the output file of the PositionPowerSpectrum job with the ASAP CuAu trajectory as the input."""

    yield run_power_spectrum(
        tmp_path_factory.mktemp("data") / f"{CUAU_TRAJ}{SUFFIX}",
        [0, 1000, 1, 500],
        60,
        CONV_DIR / CUAU_TRAJ,
    )


@pytest.fixture(scope="module")
def glycl_l_alanine_spectrum_clean(tmp_path_factory):
    """Fixture returns the output file of the PositionPowerSpectrum job with the LAMMPS Glycl-L-Alanaine CHARMM
    trajectory as the input.

    """

    yield run_power_spectrum(
        tmp_path_factory.mktemp("data") / f"{GLYCYL_L_ALANINE_TRAJ}{SUFFIX}",
        [0, 25, 1, 13],
        60,
        CONV_DIR / GLYCYL_L_ALANINE_TRAJ,
    )


def run_convolution_test(
    filter_config: dict,
    trajectory_name: str,
    frames: list[int],
    n_atoms: int,
    unfiltered_power_spectrum: Generator[Path, Any, None],
    filter_type: str,
    filter_attributes: dict,
    max_freq: float,
    max_freq_precision: int,
    tmp_path: Path,
):
    """The performance of the MDANSE trajectory filter is tested by analysing functional form.
    In this case we compare the form of the power spectrum function of the filtered trajectory against the
    power spectrum of the unfiltered trajectory.

    The convolution theorem

        x(t) * h(t) = X(w)H(w)

    states that convolution in the time domain is equivalent to multiplication in the frequency domain.
    Therefore, the power spectrum of the filtered trajectory, F(w), should be close (with some tolerance) to the product
    of the unfiltered trajectory power spectrum, U(w), and the filter frequency response, H(w).
    """

    # Retrieve U(w), check the data is as expected
    original_data = LocalDataset(
        "pps/isotropic/total", h5py.File(unfiltered_power_spectrum, "r+")
    )
    u_x_axis_name = list(original_data._axes_units.keys())

    assert u_x_axis_name == ["pps/axes/romega"]
    assert original_data._axes_units[u_x_axis_name[0]] == "rad/ps"

    u_x_axis = original_data._axes["pps/axes/romega"]

    assert np.round(u_x_axis.min(), 0) == 0
    assert np.round(u_x_axis.max(), max_freq_precision) == max_freq

    uw = original_data._data

    # Retrieve filter configuration dict
    filter_class = FILTER_MAP[filter_type]

    # Instantiate filter object
    filter_object = filter_class(**filter_attributes)

    # Supply frequencies against which to calculate response H(w)
    filter_object.custom_freq_range = u_x_axis
    filter_object.set_freq_response(Filter.FrequencyRangeMethod.CUSTOM)

    # Resample H(w) to length of U(w)
    attenuation = interp1d(
        filter_object.freq_response.frequencies,
        filter_object.freq_response.magnitudes,
        fill_value=0.0,
        bounds_error=False,
    )

    # Generate the modelled attenuation, assuming an exponentiation to the 4th power
    # due to the contributions from sosfiltfilt, which makes two passes of the filter,
    # and the Wiener-Khinchin theorem, which yields another squaring of the power spectrum
    # by autocorrelation.
    hw = abs(attenuation(filter_object.freq_response.frequencies)) ** 4

    # Compute the frequency domain convolution U(w)H(w) that we will compare F(w) with
    model = hw * uw

    # Run TrajectoryFilter job on the input trajectory
    f_name = "filtered_trajectory"
    temp_name = tmp_path / f_name
    f_trajectory_out_file = run_trajectory_filter(
        temp_name, filter_config, n_atoms, CONV_DIR / trajectory_name
    )
    assert f_trajectory_out_file.is_file()

    # Run PositionPowerSpectrum job on the filtered trajectory
    temp_name = tmp_path / "filtered_power_spectrum"
    fw_out_file = run_power_spectrum(temp_name, frames, n_atoms, f_trajectory_out_file)

    assert fw_out_file.is_file()

    # Retrieve F(w), check the data is as expected
    filtered_data = LocalDataset("pps/isotropic/total", h5py.File(fw_out_file, "r+"))
    f_x_axis_name = list(filtered_data._axes_units.keys())

    assert f_x_axis_name == ["pps/axes/romega"]
    assert filtered_data._axes_units[f_x_axis_name[0]] == "rad/ps"

    f_x_axis = filtered_data._axes["pps/axes/romega"]

    assert np.round(f_x_axis.min(), 0) == 0
    assert np.round(f_x_axis.max(), max_freq_precision) == max_freq

    fw = filtered_data._data

    assert len(fw) == len(uw)

    return model, fw


@pytest.mark.parametrize(
    "filter_config",
    [
        {
            "filter": "ChebyshevTypeII",
            "attributes": {
                "n_steps": 4000,
                "time_step_ps": 0.001,
                "order": 1,
                "attenuation_type": "bandpass",
                "cutoff_freq": [12.5, 50.0],
            },
        },
        {
            "filter": "Butterworth",
            "attributes": {
                "n_steps": 4000,
                "time_step_ps": 0.001,
                "order": 8,
                "attenuation_type": "highpass",
                "cutoff_freq": 70.25,
            },
        },
    ],
)
def test_convolution_simple(
    tmp_path,
    bimodal_spectrum_clean,
    filter_config,
):
    TOLERANCE = 3

    model, test = run_convolution_test(
        filter_config=filter_config,
        trajectory_name=SINGLE_BIMODAL_ATOM_TRAJ,
        frames=[0, 4000, 1, 2000],
        n_atoms=1,
        unfiltered_power_spectrum=safe_mda(bimodal_spectrum_clean),
        filter_type=filter_config["filter"],
        filter_attributes=filter_config["attributes"],
        max_freq=499.8749593476265 * TWOPI,
        max_freq_precision=3,
        tmp_path=tmp_path,
    )

    # H(w) and F(w) spectra should be very close - we expect a single dominant peak in either, with a magnitude error of 3%
    get_peak_location = lambda x: x[0][0]
    get_peak_magnitude = lambda x: x[1]["peak_heights"][0]
    model_peaks = find_peaks(model, height=7.0e-6)
    filtered_peaks = find_peaks(test, height=7.0e-6)
    assert len(model_peaks[0] == 1) and len(filtered_peaks[0] == 1)
    assert get_peak_location(model_peaks) == get_peak_location(filtered_peaks)
    assert np.isclose(
        get_peak_magnitude(model_peaks),
        get_peak_magnitude(filtered_peaks),
        rtol=1e-2 * TOLERANCE,
    )


@pytest.mark.parametrize(
    "filter_config",
    [
        {
            "trajectory": SRTIO3_TRAJ,
            "max_frequency": (626, 0),
            "frames": [0, 320, 1, 160],
            "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_atoms", "index_range": [0, 60], "operation_type": "intersection"}}',
            "filter": "Butterworth",
            "attributes": {
                "n_steps": 320,
                "time_step_ps": 0.005,
                "order": 1,
                "attenuation_type": "lowpass",
                "cutoff_freq": 19.635 / TWOPI,
            },
        },
        {
            "trajectory": SRTIO3_TRAJ,
            "max_frequency": (626, 0),
            "frames": [0, 320, 1, 160],
            "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_atoms", "index_range": [0, 60], "operation_type": "intersection"}}',
            "filter": "Butterworth",
            "attributes": {
                "n_steps": 320,
                "time_step_ps": 0.005,
                "order": 1,
                "attenuation_type": "highpass",
                "cutoff_freq": 31.416 / TWOPI,
            },
        },
        {
            "trajectory": SRTIO3_TRAJ,
            "max_frequency": (626, 0),
            "frames": [0, 320, 1, 160],
            "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_atoms", "index_range": [0, 60], "operation_type": "intersection"}}',
            "filter": "ChebyshevTypeII",
            "attributes": {
                "n_steps": 320,
                "time_step_ps": 0.005,
                "order": 1,
                "min_attenuation": 12.7,
                "attenuation_type": "bandpass",
                "cutoff_freq": [27.489000000000004 / TWOPI, 376.992 / TWOPI],
            },
        },
        {
            "trajectory": SRTIO3_TRAJ,
            "max_frequency": (626, 0),
            "frames": [0, 320, 1, 160],
            "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_atoms", "index_range": [0, 60], "operation_type": "intersection"}}',
            "filter": "Bessel",
            "attributes": {
                "n_steps": 320,
                "time_step_ps": 0.005,
                "order": 1,
                "norm": "phase",
                "attenuation_type": "bandstop",
                "cutoff_freq": [27.489000000000004 / TWOPI, 70.686 / TWOPI],
            },
        },
        {
            "trajectory": SRTIO3_TRAJ,
            "max_frequency": (626, 0),
            "frames": [0, 320, 1, 160],
            "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_atoms", "index_range": [0, 60], "operation_type": "intersection"}}',
            "filter": "ChebyshevTypeII",
            "attributes": {
                "n_steps": 320,
                "time_step_ps": 0.005,
                "order": 2,
                "min_attenuation": 20.0,
                "attenuation_type": "bandpass",
                "cutoff_freq": [15.708000000000002 / TWOPI, 145.299 / TWOPI],
            },
        },
        {
            "trajectory": SRTIO3_TRAJ,
            "max_frequency": (626, 0),
            "frames": [0, 320, 1, 160],
            "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_atoms", "index_range": [0, 60], "operation_type": "intersection"}}',
            "filter": "ChebyshevTypeII",
            "attributes": {
                "n_steps": 320,
                "time_step_ps": 0.005,
                "order": 2,
                "min_attenuation": 2.0,
                "attenuation_type": "bandpass",
                "cutoff_freq": [15.708000000000002 / TWOPI, 145.299 / TWOPI],
            },
        },
        {
            "trajectory": SRTIO3_TRAJ,
            "max_frequency": (626, 0),
            "frames": [0, 320, 1, 160],
            "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_atoms", "index_range": [0, 60], "operation_type": "intersection"}}',
            "filter": "Notch",
            "attributes": {
                "n_steps": 320,
                "time_step_ps": 0.005,
                "fundamental_freq": 6.875,
                "quality_factor": 1.6,
            },
        },
        {
            "trajectory": CUAU_TRAJ,
            "max_frequency": (314, 0),
            "frames": [0, 1000, 1, 500],
            "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_atoms", "index_range": [0, 60], "operation_type": "intersection"}}',
            "filter": "Peak",
            "attributes": {
                "n_steps": 1000,
                "time_step_ps": 0.01,
                "fundamental_freq": 5.7,
                "quality_factor": 1.5,
            },
        },
        # {
        #     "trajectory": CUAU_TRAJ,
        #     "max_frequency": (314, 0),
        #     "frames": [0, 1000, 1, 500],
        #     "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_atoms", "index_range": [0, 60], "operation_type": "intersection"}}',
        #     "filter": "Comb",
        #     "attributes": {
        #         "n_steps": 1000,
        #         "time_step_ps": 0.01,
        #         "fundamental_freq": 5.0,
        #         "quality_factor": 30.0,
        #         "comb_type": "notch",
        #         "pass_zero": True,
        #     },
        # },
        {
            "trajectory": GLYCYL_L_ALANINE_TRAJ,
            "max_frequency": (0.000754, 7),
            "frames": [0, 25, 1, 13],
            "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_atoms", "index_range": [0, 60], "operation_type": "intersection"}}',
            "filter": "ChebyshevTypeII",
            "attributes": {
                "n_steps": 25,
                "time_step_ps": 4000.0,
                "order": 1,
                "min_attenuation": 10.0,
                "attenuation_type": "bandstop",
                "cutoff_freq": [0.00031415 / TWOPI, 0.00043981 / TWOPI],
            },
        },
        # {
        #     "trajectory": GLYCYL_L_ALANINE_TRAJ,
        #     "max_frequency": (0.000754, 7),
        #     "frames": [0, 25, 1, 13],
        #     "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_atoms", "index_range": [0, 60], "operation_type": "intersection"}}',
        #     "filter": "Elliptical",
        #     "attributes": {
        #         "n_steps": 25,
        #         "time_step_ps": 4000.0,
        #         "order": 2,
        #         "max_ripple": 1.0,
        #         "min_attenuation": 20.0,
        #         "attenuation_type": "bandpass",
        #         "cutoff_freq": [0.00006283 / TWOPI, 0.00018849 / TWOPI],
        #     },
        # },
        {
            "trajectory": GLYCYL_L_ALANINE_TRAJ,
            "max_frequency": (0.000754, 7),
            "frames": [0, 25, 1, 13],
            "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_atoms", "index_range": [0, 60], "operation_type": "intersection"}}',
            "filter": "ChebyshevTypeI",
            "attributes": {
                "n_steps": 25,
                "time_step_ps": 4000.0,
                "order": 1,
                "max_ripple": 5.0,
                "attenuation_type": "bandstop",
                "cutoff_freq": [0.00006283 / TWOPI, 0.00012566 / TWOPI],
            },
        },
    ],
)
def test_convolution(
    tmp_path,
    srtio3_spectrum_clean,
    cuau_spectrum_clean,
    glycl_l_alanine_spectrum_clean,
    filter_config,
):
    """The performance of the MDANSE trajectory filter is tested by analysing functional form.
    In this case we compare the form of the power spectrum function of the filtered trajectory against the
    power spectrum of the unfiltered trajectory.

    The convolution theorem

        x(t) * h(t) = X(w)H(w)

    states that convolution in the time domain is equivalent to multiplication in the frequency domain.
    Therefore, the power spectrum of the filtered trajectory, F(w), should be close (with some tolerance) to the product
    of the unfiltered trajectory power spectrum, U(w), and the filter frequency response, H(w).
    """
    # Trajectory .mdt file name
    trajectory_name = filter_config["trajectory"]

    # Select unfiltered power spectrum fixture
    if trajectory_name == SRTIO3_TRAJ:
        unfiltered_power_spectrum = safe_mda(srtio3_spectrum_clean)
    elif trajectory_name == CUAU_TRAJ:
        unfiltered_power_spectrum = safe_mda(cuau_spectrum_clean)
    elif trajectory_name == GLYCYL_L_ALANINE_TRAJ:
        unfiltered_power_spectrum = safe_mda(glycl_l_alanine_spectrum_clean)
    else:
        ValueError(f"{trajectory_name} is not a recognised .mdt file.")

    model, test = run_convolution_test(
        filter_config=filter_config,
        trajectory_name=trajectory_name,
        frames=filter_config["frames"],
        n_atoms=json.loads(filter_config["atom_selection"])["1"]["index_range"][1],
        unfiltered_power_spectrum=unfiltered_power_spectrum,
        filter_type=filter_config["filter"],
        filter_attributes=filter_config["attributes"],
        max_freq=filter_config["max_frequency"][0],
        max_freq_precision=filter_config["max_frequency"][1],
        tmp_path=tmp_path,
    )

    # Calculate the relative area under curve for model {U(w)H(w)} and F(w) and assert they are close to
    # within 15% at most
    assert (
        np.abs(1e2 * (trap(np.abs(model)) - trap(np.abs(test))) / trap(np.abs(model)))
        < 15
    )

    # Count peaks in H(w) and F(w) that are greater in height than the 2nd standard deviation of the data
    model_peaks = find_peaks(
        model, height=np.mean(np.abs(model)) + 2 * np.std(np.abs(model))
    )
    filtered_peaks = find_peaks(
        test, height=np.mean(np.abs(test)) + 2 * np.std(np.abs(test))
    )

    # Assert that the number of features satisfying the criteria is the same in both H(w) and F(w)
    assert len(model_peaks) == len(filtered_peaks)

    # Finally, assert that the mean squared error between the indices of these features in H(w) and F(w) do not deviate
    # by more than 8
    assert 8 >= (1 / len(model_peaks)) * np.sum(
        (model_peaks[0] - filtered_peaks[0]) ** 2
    )


@pytest.mark.parametrize(
    "filter_config",
    (
        {
            "trajectory": GLYCYL_L_ALANINE_TRAJ,
            "filter": "Butterworth",
            "attributes": {
                "n_steps": 25,
                "time_step_ps": 4000.0,
                "cutoff_freq": 0.000377 / TWOPI,
            },
        },
        {
            "trajectory": GLYCYL_L_ALANINE_TRAJ,
            "filter": "ChebyshevTypeI",
            "attributes": {
                "n_steps": 25,
                "time_step_ps": 4000.0,
                "cutoff_freq": 0.000377 / TWOPI,
            },
        },
        {
            "trajectory": GLYCYL_L_ALANINE_TRAJ,
            "filter": "ChebyshevTypeII",
            "attributes": {
                "n_steps": 25,
                "time_step_ps": 4000.0,
                "cutoff_freq": 0.000377 / TWOPI,
                "min_attenuation": 10.0,
            },
        },
        {
            "trajectory": GLYCYL_L_ALANINE_TRAJ,
            "filter": "Elliptical",
            "attributes": {
                "n_steps": 25,
                "time_step_ps": 4000.0,
                "attenuation_type": "bandpass",
                "cutoff_freq": [0.000377 / TWOPI, 0.000577 / TWOPI],
            },
        },
        {
            "trajectory": GLYCYL_L_ALANINE_TRAJ,
            "filter": "Bessel",
            "attributes": {
                "n_steps": 25,
                "time_step_ps": 4000.0,
                "attenuation_type": "bandpass",
                "cutoff_freq": [0.000377 / TWOPI, 0.000577 / TWOPI],
            },
        },
        {
            "trajectory": GLYCYL_L_ALANINE_TRAJ,
            "filter": "Notch",
            "attributes": {
                "n_steps": 25,
                "time_step_ps": 4000.0,
                "fundamental_freq": 0.000125,
            },
        },
        {
            "trajectory": GLYCYL_L_ALANINE_TRAJ,
            "filter": "Peak",
            "attributes": {
                "n_steps": 25,
                "time_step_ps": 4000.0,
                "fundamental_freq": 0.000125,
            },
        },
    ),
)
def test_default_settings(
    tmp_path,
    filter_config,
):
    """This test case ensures that providing filter configurations with missing settings does not cause the trajectory filter
    job to fail, since missing settings should be interpolated via the defaults provided in the corresponding Filter derived class.

    """

    assert run_trajectory_filter(
        tmp_path,
        filter_config,
        60,
        CONV_DIR / filter_config["trajectory"],
    ).is_file()


@pytest.mark.parametrize(
    "filter_config",
    [
        {
            "trajectory": SRTIO3_TRAJ,
            "max_frequency": (626, 0),
            "frames": [0, 320, 1, 160],
            "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_atoms", "index_range": [0, 60], "operation_type": "intersection"}}',
            "filter": "Butterworth",
            "attributes": {
                "n_steps": 320,
                "time_step_ps": 0.005,
                "order": 1,
                "attenuation_type": "highpass",
                "cutoff_freq": 19.635 / TWOPI,
            },
        },
        {
            "trajectory": SRTIO3_TRAJ,
            "max_frequency": (626, 0),
            "frames": [0, 320, 1, 160],
            "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_atoms", "index_range": [0, 60], "operation_type": "intersection"}}',
            "filter": "Butterworth",
            "attributes": {
                "n_steps": 320,
                "time_step_ps": 0.005,
                "order": 2,
                "attenuation_type": "bandpass",
                "cutoff_freq": [19.635 / TWOPI, 31.416 / TWOPI],
            },
        },
        {
            "trajectory": SRTIO3_TRAJ,
            "max_frequency": (626, 0),
            "frames": [0, 320, 1, 160],
            "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_atoms", "index_range": [0, 60], "operation_type": "intersection"}}',
            "filter": "ChebyshevTypeII",
            "attributes": {
                "n_steps": 320,
                "time_step_ps": 0.005,
                "order": 1,
                "min_attenuation": 12.7,
                "attenuation_type": "highpass",
                "cutoff_freq": 376.992 / TWOPI,
            },
        },
        # {
        #     "trajectory": SRTIO3_TRAJ,
        #     "max_frequency": (626, 0),
        #     "frames": [0, 320, 1, 160],
        #     "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_atoms", "index_range": [0, 60], "operation_type": "intersection"}}',
        #     "filter": "Comb",
        #     "attributes": {
        #         "n_steps": 320,
        #         "time_step_ps": 0.005,
        #         "fundamental_freq": 10.0,
        #         "quality_factor": 2.0,
        #     },
        # },
        # {
        #     "trajectory": SRTIO3_TRAJ,
        #     "max_frequency": (626, 0),
        #     "frames": [0, 320, 1, 160],
        #     "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_atoms", "index_range": [0, 60], "operation_type": "intersection"}}',
        #     "filter": "Comb",
        #     "attributes": {
        #         "n_steps": 320,
        #         "time_step_ps": 0.005,
        #         "fundamental_freq": 10.0,
        #         "quality_factor": 20.0,
        #         "comb_type": "peak",
        #     },
        # },
        # {
        #     "trajectory": SRTIO3_TRAJ,
        #     "max_frequency": (626, 0),
        #     "frames": [0, 320, 1, 160],
        #     "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_atoms", "index_range": [0, 60], "operation_type": "intersection"}}',
        #     "filter": "Comb",
        #     "attributes": {
        #         "n_steps": 320,
        #         "time_step_ps": 0.005,
        #         "fundamental_freq": 10.0,
        #         "quality_factor": 20.0,
        #         "comb_type": "peak",
        #         "pass_zero": True,
        #     },
        # },
        {
            "trajectory": CUAU_TRAJ,
            "max_frequency": (314, 0),
            "frames": [0, 1000, 1, 500],
            "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_atoms", "index_range": [0, 60], "operation_type": "intersection"}}',
            "filter": "Peak",
            "attributes": {
                "n_steps": 1000,
                "time_step_ps": 0.01,
                "fundamental_freq": 5.7,
                "quality_factor": 1.5,
            },
        },
        # {
        #     "trajectory": CUAU_TRAJ,
        #     "max_frequency": (314, 0),
        #     "frames": [0, 1000, 1, 500],
        #     "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_atoms", "index_range": [0, 60], "operation_type": "intersection"}}',
        #     "filter": "Comb",
        #     "attributes": {
        #         "n_steps": 1000,
        #         "time_step_ps": 0.01,
        #         "fundamental_freq": 5.0,
        #         "quality_factor": 30.0,
        #         "comb_type": "notch",
        #         "pass_zero": True,
        #     },
        # },
        {
            "trajectory": GLYCYL_L_ALANINE_TRAJ,
            "max_frequency": (0.000754, 7),
            "frames": [0, 25, 1, 13],
            "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_atoms", "index_range": [0, 60], "operation_type": "intersection"}}',
            "filter": "ChebyshevTypeII",
            "attributes": {
                "n_steps": 25,
                "time_step_ps": 4000.0,
                "order": 4,
                "min_attenuation": 10.0,
                "attenuation_type": "highpass",
                "cutoff_freq": 0.00006283 / TWOPI,
            },
        },
        {
            "trajectory": GLYCYL_L_ALANINE_TRAJ,
            "max_frequency": (0.000754, 7),
            "frames": [0, 25, 1, 13],
            "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_atoms", "index_range": [0, 60], "operation_type": "intersection"}}',
            "filter": "ChebyshevTypeII",
            "attributes": {
                "n_steps": 25,
                "time_step_ps": 4000.0,
                "order": 2,
                "min_attenuation": 0.1,
                "attenuation_type": "lowpass",
                "cutoff_freq": 0.00006283 / TWOPI,
            },
        },
        {
            "trajectory": GLYCYL_L_ALANINE_TRAJ,
            "max_frequency": (0.000754, 7),
            "frames": [0, 25, 1, 13],
            "atom_selection": '{"0": {"function_name": "select_all", "operation_type": "union"}, "1": {"function_name": "select_atoms", "index_range": [0, 60], "operation_type": "intersection"}}',
            "filter": "ChebyshevTypeI",
            "attributes": {
                "n_steps": 25,
                "time_step_ps": 4000.0,
                "order": 1,
                "max_ripple": 0.4,
                "attenuation_type": "bandpass",
                "cutoff_freq": [0.00018849 / TWOPI, 0.00062830 / TWOPI],
            },
        },
    ],
)
def test_position_stability(tmp_path, filter_config):
    """This test case ensures that atomic initial positions are preserved after filtering."""
    TOLERANCE = 10

    # Unfiltered trajectory
    initial = Trajectory(CONV_DIR / filter_config["trajectory"])

    n_atoms = json.loads(filter_config["atom_selection"])["1"]["index_range"][1]

    # Initial positions when no filter applied
    initial_x0 = initial._trajectory[:]["coordinates"][0][:n_atoms]

    # Filtered trajectory
    filtered = Trajectory(
        run_trajectory_filter(
            tmp_path,
            filter_config,
            n_atoms,
            CONV_DIR / filter_config["trajectory"],
        )
    )

    # Initial positions when filter applied
    filtered_x0 = filtered._trajectory[:]["coordinates"][0]

    # Get distances (magnitudes) of initial and filtered atomic displacements and check they are within 10% of each other
    a = np.sqrt(np.array([np.sum(xyz**2) for xyz in initial_x0]))
    b = np.sqrt(np.array([np.sum(xyz**2) for xyz in filtered_x0]))
    assert np.all(np.isclose(a, b, rtol=1e-2 * TOLERANCE))
