import numpy as np
import h5py

from MDANSE.Framework.Jobs.IJob import IJob
from test_helpers.paths import CONV_DIR, RESULTS_DIR


mdmc_traj = CONV_DIR / "Ar_mdmc_h5md.h5"


def test_disf_selection_plus_inverse_results_equal_to_all_selection_results(tmp_path):

    parameters = {
        "atom_selection": None,
        "atom_transmutation": None,
        "frames": (0, 10, 1, 5),
        "instrument_resolution": ("Ideal", {}),
        "q_vectors": (
            "GridQVectors",
            {"hrange": [0, 3, 1], "krange": [0, 3, 1], "lrange": [0, 3, 1], "qstep": 1}
        ),
        "running_mode": ("single-core",),
        "trajectory": mdmc_traj,
        "weights": "b_incoherent",
    }

    disf = IJob.create("DynamicIncoherentStructureFactor")
    result_all = tmp_path / f"disf_all_selection.mda"
    parameters["output_files"] = (result_all, ("MDAFormat", ), "INFO")
    disf.run(parameters, status=True)

    disf = IJob.create("DynamicIncoherentStructureFactor")
    result_select = tmp_path / f"disf_sphere_selection.mda"
    parameters["output_files"] = (result_select, ("MDAFormat", ), "INFO")
    parameters["atom_selection"] = \
        ('{"0": {"function_name": "select_all", "operation_type": "union"}, '
         '"1": {"function_name": "invert_selection"}, '
         '"2": {"function_name": "select_sphere", "frame_number": 0, "sphere_centre": [1.73, 1.73, 1.73], "sphere_radius": 1.5, "operation_type": "union"}}')
    disf.run(parameters, status=True)

    disf = IJob.create("DynamicIncoherentStructureFactor")
    result_inv = tmp_path / f"disf_sphere_selection_inverse.mda"
    parameters["output_files"] = (result_inv, ("MDAFormat", ), "INFO")
    parameters["atom_selection"] = \
        ('{"0": {"function_name": "select_all", "operation_type": "union"}, '
         '"1": {"function_name": "invert_selection"}, '
         '"2": {"function_name": "select_sphere", "frame_number": 0, "sphere_centre": [1.73, 1.73, 1.73], "sphere_radius": 1.5, "operation_type": "union"}, '
         '"3": {"function_name": "invert_selection"}}')
    disf.run(parameters, status=True)

    with h5py.File(result_all) as all, h5py.File(result_select) as select, h5py.File(result_inv) as inv:
        for key in ["/f(q,t)_total", "/s(q,f)_total"]:
            all_results = np.array(all[key])
            select_results = np.array(select[key]) * select[key].attrs["scaling_factor"]
            inv_results = np.array(inv[key]) * inv[key].attrs["scaling_factor"]
            np.testing.assert_allclose(all_results, select_results + inv_results)
