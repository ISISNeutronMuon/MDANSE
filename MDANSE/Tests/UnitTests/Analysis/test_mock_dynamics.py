import pytest
from MDANSE.Framework.Jobs.IJob import IJob
from test_helpers.compare_hdf5 import compare_hdf5
from test_helpers.paths import DATA_DIR, RESULTS_DIR

mock_json = DATA_DIR / "mock.json"


@pytest.mark.parametrize("interp_order", [1, 2, 3])
def test_vcf(generate_benchmarks, tmp_path, interp_order):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    result_file = RESULTS_DIR / f"mock_traj_vcf_{interp_order}.mda"

    if generate_benchmarks:
        temp_name = result_file.with_suffix("")

    parameters = {
        "frames": (0, 10, 1, 5),
        "interpolation_order": interp_order,
        "output_files": (temp_name, ("MDAFormat",), "INFO"),
        "running_mode": ("single-core",),
        "trajectory": mock_json,
    }

    vcf = IJob.create("VelocityCorrelationFunction", trajectory_input="mock")
    vcf.run(parameters, status=True)

    if generate_benchmarks:
        return

    assert out_file.is_file()
    assert log_file.is_file()

    compare_hdf5(out_file, result_file,
                [f"vcf/{comp}/{elem}"
                 for comp in ("isotropic", "xx", "xy", "xz", "yy", "yz", "zz")
                 for elem in ("H", "O", "Si", "total")],
                scale_result=False, compare_axis=True)
