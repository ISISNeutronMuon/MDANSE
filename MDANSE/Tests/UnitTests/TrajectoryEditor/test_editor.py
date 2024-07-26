import sys
import tempfile
import os
from os import path
import pytest

import numpy as np
import h5py
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.Framework.Jobs.IJob import IJob


sys.setrecursionlimit(100000)
short_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Data",
    "trajectory_no_unit_cell.mdt",
)

def test_editor_null():
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["output_files"] = (temp_name, 64, "gzip", "INFO")
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
    assert original.trajectory.chemical_system.number_of_atoms == changed.trajectory.chemical_system.number_of_atoms
    original.close()
    changed.close()
    os.remove(temp_name + ".mdt")
    os.remove(temp_name + ".log")

def test_editor_frames():
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["output_files"] = (temp_name, 64, "gzip", "INFO")
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
    assert original.trajectory.chemical_system.number_of_atoms == changed.trajectory.chemical_system.number_of_atoms
    original.close()
    changed.close()
    os.remove(temp_name + ".mdt")
    os.remove(temp_name + ".log")

def test_editor_atoms():
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["output_files"] = (temp_name, 64, "gzip", "INFO")
    parameters["trajectory"] = short_traj
    parameters["frames"] = (0, 501, 1)
    parameters["atom_selection"] = '{"all": false, "element": ["F"]}'
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
    assert original.trajectory.chemical_system.number_of_atoms > changed.trajectory.chemical_system.number_of_atoms
    assert changed.trajectory.chemical_system.number_of_atoms > 0
    original.close()
    changed.close()
    os.remove(temp_name + ".mdt")
    os.remove(temp_name + ".log")

def test_editor_unit_cell():
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["output_files"] = (temp_name, 64, "gzip", "INFO")
    parameters["trajectory"] = short_traj
    parameters["frames"] = (0, 501, 1)
    parameters["unit_cell"] = [[1,2,3], [4,5,6], [7,8,9]]
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
    assert original.trajectory.chemical_system.number_of_atoms == changed.trajectory.chemical_system.number_of_atoms
    assert np.allclose([[1,2,3], [4,5,6], [7,8,9]], changed.trajectory.unit_cell(0)._unit_cell)
    original.close()
    changed.close()
    os.remove(temp_name + ".mdt")
    os.remove(temp_name + ".log")

def test_editor_transmute():
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["output_files"] = (temp_name, 64, "gzip", "INFO")
    parameters["trajectory"] = short_traj
    parameters["frames"] = (0, 501, 1)
    parameters["atom_transmutation"] = '{"6": "B", "7": "B", "8": "B", "9": "B", "10": "B", "11": "B", "12": "B", "13": "B", "14": "B", "15": "B", "16": "B", "17": "B", "18": "B", "19": "B"}'
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
    assert original.trajectory.chemical_system.number_of_atoms == changed.trajectory.chemical_system.number_of_atoms
    old_symbols = [at.symbol for at in original.trajectory.chemical_system.atom_list]
    new_symbols = [at.symbol for at in changed.trajectory.chemical_system.atom_list]
    assert old_symbols != new_symbols
    assert 'B' not in old_symbols
    assert 'B' in new_symbols
    original.close()
    changed.close()
    os.remove(temp_name + ".mdt")
    os.remove(temp_name + ".log")