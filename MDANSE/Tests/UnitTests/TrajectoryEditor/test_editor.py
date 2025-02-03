import tempfile
import os
from os import path

import numpy as np
import h5py

from MDANSE.MolecularDynamics.Configuration import remove_jumps
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.Framework.Jobs.IJob import IJob


short_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Converted",
    "trajectory_no_unit_cell.mdt",
)


def test_jumps_removed_correctly():
    input_coords = np.array(
        [
            [0.8, 0.2, 0.3],
            [0.88, 0.22, 0.33],
            [0.97, 0.2, 0.3],
            [0.05, 0.22, 0.31],
            [0.03, 0.2, 0.3],
            [0.99, 0.22, 0.32],
        ]
    )
    expected_coords = np.array(
        [
            [0.8, 0.2, 0.3],
            [0.88, 0.22, 0.33],
            [0.97, 0.2, 0.3],
            [1.05, 0.22, 0.31],
            [1.03, 0.2, 0.3],
            [0.99, 0.22, 0.32],
        ]
    )
    corrected_coords = remove_jumps(input_coords)
    assert np.allclose(corrected_coords, expected_coords)


def test_editor_null():
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["output_files"] = (temp_name, 64, 128, "gzip", "INFO")
    parameters["trajectory"] = short_traj
    parameters["frames"] = (0, 501, 1)
    temp = IJob.create("TrajectoryEditor")
    temp.run(parameters, status=True)
    assert path.exists(temp_name + ".mdt")
    assert path.isfile(temp_name + ".mdt")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    # test if nothing has changed
    original = HDFTrajectoryInputData(short_traj)
    changed = HDFTrajectoryInputData(temp_name + ".mdt")
    assert len(original.trajectory) == len(changed.trajectory)
    assert (
        original.trajectory.chemical_system.number_of_atoms
        == changed.trajectory.chemical_system.number_of_atoms
    )
    original.close()
    changed.close()

    with h5py.File(temp_name + ".mdt") as actual,  h5py.File(short_traj) as desired:
        np.testing.assert_array_almost_equal(actual["/configuration/coordinates"], desired["/configuration/coordinates"])
        np.testing.assert_array_almost_equal(actual["/time"], desired["/time"])

    os.remove(temp_name + ".mdt")
    os.remove(temp_name + ".log")


def test_editor_frames():
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["output_files"] = (temp_name, 64, 128, "gzip", "INFO")
    parameters["trajectory"] = short_traj
    parameters["frames"] = (0, 501, 10)
    temp = IJob.create("TrajectoryEditor")
    temp.run(parameters, status=True)
    assert path.exists(temp_name + ".mdt")
    assert path.isfile(temp_name + ".mdt")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    # test if nothing has changed
    original = HDFTrajectoryInputData(short_traj)
    changed = HDFTrajectoryInputData(temp_name + ".mdt")
    assert len(original.trajectory) > len(changed.trajectory)
    assert len(changed.trajectory) > 0
    assert (
        original.trajectory.chemical_system.number_of_atoms
        == changed.trajectory.chemical_system.number_of_atoms
    )
    original.close()
    changed.close()

    with h5py.File(temp_name + ".mdt") as actual,  h5py.File(short_traj) as desired:
        np.testing.assert_array_almost_equal(actual["/configuration/coordinates"], desired["/configuration/coordinates"][0:501:10])
        np.testing.assert_array_almost_equal(actual["/time"], desired["/time"][0:501:10])

    os.remove(temp_name + ".mdt")
    os.remove(temp_name + ".log")


def test_editor_atoms():
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["output_files"] = (temp_name, 64, 128, "gzip", "INFO")
    parameters["trajectory"] = short_traj
    parameters["frames"] = (0, 501, 1)
    parameters["atom_selection"] = '{"all": false, "element": ["H"]}'
    temp = IJob.create("TrajectoryEditor")
    temp.run(parameters, status=True)
    assert path.exists(temp_name + ".mdt")
    assert path.isfile(temp_name + ".mdt")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    # test if nothing has changed
    original = HDFTrajectoryInputData(short_traj)
    changed = HDFTrajectoryInputData(temp_name + ".mdt")
    assert len(original.trajectory) == len(changed.trajectory)
    assert (
        original.trajectory.chemical_system.number_of_atoms
        > changed.trajectory.chemical_system.number_of_atoms
    )
    assert changed.trajectory.chemical_system.number_of_atoms > 0
    original.close()
    changed.close()

    with h5py.File(temp_name + ".mdt") as actual,  h5py.File(short_traj) as desired:
        np.testing.assert_array_almost_equal(actual["/configuration/coordinates"], desired["/configuration/coordinates"][:,6:20,:])
        np.testing.assert_array_almost_equal(actual["/time"], desired["/time"])

    os.remove(temp_name + ".mdt")
    os.remove(temp_name + ".log")


def test_editor_unit_cell():
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["output_files"] = (temp_name, 64, 128, "gzip", "INFO")
    parameters["trajectory"] = short_traj
    parameters["frames"] = (0, 501, 1)
    parameters["unit_cell"] = ([[1, 2, 3], [4, 5, 6], [7, 8, 9]], True)
    temp = IJob.create("TrajectoryEditor")
    temp.run(parameters, status=True)
    assert path.exists(temp_name + ".mdt")
    assert path.isfile(temp_name + ".mdt")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    # test if nothing has changed
    original = HDFTrajectoryInputData(short_traj)
    changed = HDFTrajectoryInputData(temp_name + ".mdt")
    assert len(original.trajectory) == len(changed.trajectory)
    assert (
        original.trajectory.chemical_system.number_of_atoms
        == changed.trajectory.chemical_system.number_of_atoms
    )
    assert np.allclose(
        [[1, 2, 3], [4, 5, 6], [7, 8, 9]], changed.trajectory.unit_cell(0)._unit_cell
    )
    original.close()
    changed.close()

    with h5py.File(temp_name + ".mdt") as actual,  h5py.File(short_traj) as desired:
        np.testing.assert_array_almost_equal(actual["/configuration/coordinates"], desired["/configuration/coordinates"])
        np.testing.assert_array_almost_equal(actual["/time"], desired["/time"])

    os.remove(temp_name + ".mdt")
    os.remove(temp_name + ".log")


def test_editor_transmute():
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["output_files"] = (temp_name, 64, 128, "gzip", "INFO")
    parameters["trajectory"] = short_traj
    parameters["frames"] = (0, 501, 1)
    parameters["atom_transmutation"] = (
        '{"6": "B", "7": "B", "8": "B", "9": "B", "10": "B", "11": "B", "12": "B", "13": "B", "14": "B", "15": "B", "16": "B", "17": "B", "18": "B", "19": "B"}'
    )
    temp = IJob.create("TrajectoryEditor")
    temp.run(parameters, status=True)
    assert path.exists(temp_name + ".mdt")
    assert path.isfile(temp_name + ".mdt")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    # test if nothing has changed
    original = HDFTrajectoryInputData(short_traj)
    changed = HDFTrajectoryInputData(temp_name + ".mdt")
    assert len(original.trajectory) == len(changed.trajectory)
    assert (
        original.trajectory.chemical_system.number_of_atoms
        == changed.trajectory.chemical_system.number_of_atoms
    )
    old_symbols = [at for at in original.trajectory.chemical_system.atom_list]
    new_symbols = [at for at in changed.trajectory.chemical_system.atom_list]
    assert old_symbols != new_symbols
    assert "B" not in old_symbols
    assert "B" in new_symbols
    original.close()
    changed.close()

    with h5py.File(temp_name + ".mdt") as actual,  h5py.File(short_traj) as desired:
        np.testing.assert_array_almost_equal(actual["/configuration/coordinates"], desired["/configuration/coordinates"])
        np.testing.assert_array_almost_equal(actual["/time"], desired["/time"])

    os.remove(temp_name + ".mdt")
    os.remove(temp_name + ".log")


def test_editor_set_charges():
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["output_files"] = (temp_name, 64, 128, "gzip", "INFO")
    parameters["trajectory"] = short_traj
    parameters["atom_charges"] = (
        '{"0": 1.2, "1": 1.2, "2": 1.2, "3": 1.2, "4": 1.2, "5": 1.2, "6": -0.5, "7": -0.5, "8": -0.5, "9": -0.5, "10": -0.5, "11": -0.5, "12": -0.5, "13": -0.5, "14": -0.5, "15": -0.5, "16": -0.5, "17": -0.5, "18": -0.5, "19": -0.5}'
    )
    parameters["frames"] = (0, 501, 1)
    temp = IJob.create("TrajectoryEditor")
    temp.run(parameters, status=True)
    assert path.exists(temp_name + ".mdt")
    assert path.isfile(temp_name + ".mdt")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    # test if nothing has changed
    original = HDFTrajectoryInputData(short_traj)
    changed = HDFTrajectoryInputData(temp_name + ".mdt")
    assert len(original.trajectory) == len(changed.trajectory)
    assert np.allclose(original.trajectory.charges(0), 0.0)
    assert abs(np.sum(changed.trajectory.charges(0)) - 0.2) < 1e-5
    original.close()
    changed.close()

    with h5py.File(temp_name + ".mdt") as actual,  h5py.File(short_traj) as desired:
        np.testing.assert_array_almost_equal(actual["/configuration/coordinates"], desired["/configuration/coordinates"])
        np.testing.assert_array_almost_equal(actual["/time"], desired["/time"])

    os.remove(temp_name + ".mdt")
    os.remove(temp_name + ".log")


def test_editor_find_molecules():
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["output_files"] = (temp_name, 64, 128, "gzip", "INFO")
    parameters["trajectory"] = short_traj
    parameters["molecule_tolerance"] = [True, 0.04]
    parameters["frames"] = (0, 501, 1)
    temp = IJob.create("TrajectoryEditor")
    temp.run(parameters, status=True)
    assert path.exists(temp_name + ".mdt")
    assert path.isfile(temp_name + ".mdt")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    # test if nothing has changed
    original = HDFTrajectoryInputData(short_traj)
    changed = HDFTrajectoryInputData(temp_name + ".mdt")
    assert len(original.trajectory.chemical_system.unique_molecules()) == 0
    assert len(changed.trajectory.chemical_system.unique_molecules()) > 0
    original.close()
    changed.close()

    with h5py.File(temp_name + ".mdt") as actual,  h5py.File(short_traj) as desired:
        np.testing.assert_array_almost_equal(actual["/configuration/coordinates"], desired["/configuration/coordinates"])
        np.testing.assert_array_almost_equal(actual["/time"], desired["/time"])

    os.remove(temp_name + ".mdt")
    os.remove(temp_name + ".log")
