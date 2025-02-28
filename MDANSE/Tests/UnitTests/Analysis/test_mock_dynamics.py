import pytest
from MDANSE.Framework.Jobs.IJob import IJob
from test_helpers.compare_hdf5 import compare_hdf5
from test_helpers.paths import DATA_DIR, RESULTS_DIR

mock_json = DATA_DIR / "mock.json"


@pytest.mark.parametrize("interp_order", [1, 2, 3])
@pytest.mark.parametrize("normalise", [True, False])
def test_vacf(tmp_path, interp_order, normalise):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")

    parameters = {
        "frames": (0, 10, 1, 5),
        "interpolation_order": interp_order,
        "output_files": (temp_name, ("MDAFormat",), "INFO"),
        "running_mode": ("single-core",),
        "normalize": normalise,
        "trajectory": mock_json,
    }

    vacf = IJob.create("VelocityAutoCorrelationFunction", trajectory_input="mock")
    vacf.run(parameters, status=True)

    assert out_file.is_file()
    assert log_file.is_file()

    if normalise:
        fname = f"mock_traj_vacf_{interp_order}_normalised.mda"
    else:
        fname = f"mock_traj_vacf_{interp_order}.mda"

    result_file = RESULTS_DIR / fname

    compare_hdf5(out_file, result_file,
                [f"vacf_{elem}" for elem in ("H", "O", "Si", "total")],
                scale_result=normalise)
