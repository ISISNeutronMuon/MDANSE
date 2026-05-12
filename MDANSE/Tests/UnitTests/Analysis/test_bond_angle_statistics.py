import pytest
from MDANSE.Framework.Jobs.IJob import IJob
from test_helpers.compare_hdf5 import compare_hdf5
from test_helpers.paths import CONV_DIR, RESULTS_DIR

short_traj = CONV_DIR / "named_molecules.mdt"

################################################################
# Job parameters                                               #
################################################################
@pytest.fixture(scope="function")
def parameters():
    parameters = {}
    parameters["trajectory"] = short_traj
    parameters["running_mode"] = ("single-core",)
    parameters["bond_1"] = ("C1_O2", 0, 1)
    parameters["bond_2"] = ("C1_O2", 0, 2)
    return parameters


def test_bas_runs(parameters, tmp_path):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")
    parameters["output_files"] = (temp_name, ("MDAFormat",), "INFO")

    job = IJob.create("BondAngleStatistics", trajectory_input="mdanse")
    try:
        job.run(parameters, status=True)
    except:
        for name, conf in job.configuration.items():
            print(name, conf.error_status)
        raise RuntimeError()

    assert out_file.is_file()
    assert log_file.is_file()
