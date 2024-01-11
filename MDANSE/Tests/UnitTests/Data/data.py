from os import path

_ABS_DIR_PATH = path.split(path.abspath(__file__))[0]

short_traj = _ABS_DIR_PATH + "/short_trajectory_after_changes.h5"
mol_traj = _ABS_DIR_PATH + "/short_trajectory_with_molecules.h5"
