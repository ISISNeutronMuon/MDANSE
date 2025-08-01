import os
import tempfile

import h5py
import numpy as np
import pytest
from MDANSE.Framework.Jobs.IJob import IJob
from test_helpers.compare_hdf5 import compare_hdf5
from test_helpers.paths import CONV_DIR, RESULTS_DIR

short_traj = CONV_DIR / "short_trajectory_after_changes.mdt"

# Mean Square Displacements can accept many parameters, most of them optional
# settings['trajectory']=('hdf_trajectory',{})
# settings['frames']=('frames', {"dependencies":{'trajectory':'trajectory'}})
# settings['projection']=('projection', {"label":"project coordinates"})
# settings['atom_selection']=('atom_selection',{"dependencies":{'trajectory':'trajectory'}})
# settings['grouping_level']=('grouping_level',{"dependencies":{'trajectory':'trajectory','atom_selection':'atom_selection', 'atom_transmutation':'atom_transmutation'}})
# settings['atom_transmutation']=('atom_transmutation',{"dependencies":{'trajectory':'trajectory', 'atom_selection':'atom_selection'}})
# settings['weights']=('weights',{"dependencies":{"atom_selection":"atom_selection"}})
# settings['output_files']=('output_files', {"formats":["hdf","netcdf","ascii","svg"]})
# settings['running_mode']=('running_mode',{})

@pytest.mark.parametrize("running_mode", [("single-core",), ("multicore", -4)],
                         ids=lambda x: x[0])
def test_basic_meansquare(generate_benchmarks, tmp_path, running_mode):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    result_file = RESULTS_DIR / "basic_meansquare.mda"

    if generate_benchmarks:
        temp_name = result_file.with_suffix("")

    parameters = {
        "frames": (0, 10, 1, 5),
        "output_files": (temp_name, ("MDAFormat",), "INFO"),
        "running_mode": running_mode,
        "trajectory": short_traj,
    }

    msd = IJob.create("MeanSquareDisplacement")
    msd.run(parameters, status=True)

    if generate_benchmarks:
        return

    assert out_file.is_file()
    assert log_file.is_file()

    compare_hdf5(out_file, result_file,
                [f"/msd/{elem}" for elem in ("Cu", "S", "Sb", "total")], compare_axis=True)
