import h5py
import numpy as np
from test_helpers.compare_hdf5 import compare_hdf5
from test_helpers.paths import CONV_DIR, RESULTS_DIR

from MDANSE.Framework.Jobs.IJob import IJob

mdmc_traj = CONV_DIR / "Ar_mdmc_h5md.h5"


def test_disf_selection_plus_inverse_results_equal_to_all_selection_results(tmp_path):
    parameters = {
        "atom_selection": None,
        "atom_transmutation": None,
        "frames": (0, 10, 1, 5),
        "instrument_resolution": ("Ideal", {}),
        "q_vectors": (
            "GridQVectors",
            {"hrange": [0, 3, 1], "krange": [0, 3, 1], "lrange": [0, 3, 1], "qstep": 1},
        ),
        "running_mode": ("single-core",),
        "trajectory": mdmc_traj,
        "weights": "b_incoherent",
    }
    result_all = tmp_path / "disf_all_selection.mda"
    result_select = tmp_path / "disf_sphere_selection.mda"
    result_inv = tmp_path / "disf_sphere_selection_inverse.mda"

    all_params = {"output_files": (result_all, ("MDAFormat",), "INFO")}
    select_params = {
        "output_files": (result_select, ("MDAFormat",), "INFO"),
        "atom_selection": (
            '{"0": {"function_name": "select_all", "operation_type": "union"}, '
            '"1": {"function_name": "invert_selection"}, '
            '"2": {"function_name": "select_sphere", "frame_number": 0, "sphere_centre": [1.73, 1.73, 1.73], "sphere_radius": 1.5, "operation_type": "union"}}'
        ),
    }
    inv_params = {
        "output_files": (result_inv, ("MDAFormat",), "INFO"),
        "atom_selection": (
            '{"0": {"function_name": "select_all", "operation_type": "union"}, '
            '"1": {"function_name": "invert_selection"}, '
            '"2": {"function_name": "select_sphere", "frame_number": 0, "sphere_centre": [1.73, 1.73, 1.73], "sphere_radius": 1.5, "operation_type": "union"}, '
            '"3": {"function_name": "invert_selection"}}'
        ),
    }

    for job_params in (all_params, select_params, inv_params):
        disf = IJob.create("DynamicIncoherentStructureFactor")
        disf.run(parameters | job_params, status=True)

    outputs = ("disf/f(q,t)/total", "disf/s(q,f)/total")

    with (
        h5py.File(result_all) as all,
        h5py.File(result_select) as select,
        h5py.File(result_inv) as inv,
    ):
        for key in outputs:
            all_results = np.array(all[key])
            select_results = np.array(select[key]) * select[key].attrs["scaling_factor"]
            inv_results = np.array(inv[key]) * inv[key].attrs["scaling_factor"]
            np.testing.assert_allclose(all_results, select_results + inv_results)
