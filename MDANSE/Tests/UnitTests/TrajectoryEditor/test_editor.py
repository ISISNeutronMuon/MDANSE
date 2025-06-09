import numpy as np
import pytest
from MDANSE.MolecularDynamics.Trajectory import \
    Trajectory
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Configuration import remove_jumps
from test_helpers.compare_hdf5 import compare_hdf5
from test_helpers.get_deep_attr import get_deep_attr
from test_helpers.paths import CONV_DIR

short_traj = CONV_DIR / "trajectory_no_unit_cell.mdt"

CHARGE_ARRAY = [1.2, 1.2, 1.2, 1.2, 1.2, 1.2,
                -0.5, -0.5, -0.5, -0.5, -0.5, -0.5,
                -0.5, -0.5, -0.5, -0.5, -0.5, -0.5,
                -0.5, -0.5]


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


@pytest.mark.parametrize("file_compare, traj_compare, parameters", [
    (("/configuration/coordinates", "/time"),
     ("chemical_system.number_of_atoms", "__len__()"),
     {"trajectory": short_traj, "frames": (0, 501, 1)},
     ),

    ((("/configuration/coordinates", slice(0, 501, 10)),
      ("/time", slice(0, 501, 10))),
     ("chemical_system.number_of_atoms", ("__len__()", 51)),
     {"trajectory": short_traj, "frames": (0, 501, 10)},
     ),

    ((("/configuration/coordinates", (slice(None), slice(6, 20), slice(None))),
      "/time"),
     ("__len__()", ("chemical_system.number_of_atoms", 14)),
     {"trajectory": short_traj, "frames": (0, 501, 1),
      "atom_selection": '{"0": {"function_name": "select_atoms", "atom_types": ["H"]}}'},
     ),

    (("/configuration/coordinates", "/time"),
     ("chemical_system.number_of_atoms", "__len__()",
      ("unit_cell(0)._unit_cell", np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]))),
     {"trajectory": short_traj, "frames": (0, 501, 1),
      "unit_cell": (np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]), True)},
     ),

    (("/configuration/coordinates", "/time"),
     ("chemical_system.number_of_atoms", "__len__()",
      ("chemical_system.atom_list", ['C', 'C', 'C', 'C', 'C', 'C',
                                                'B', 'B', 'B', 'B', 'B', 'B', 'B',
                                                'B', 'B', 'B', 'B', 'B', 'B', 'B'])),
     {"trajectory": short_traj, "frames": (0, 501, 1),
      "atom_transmutation": (
          '{"6": "B", "7": "B", "8": "B", "9": "B", "10": "B", "11": "B", "12": "B",'
          ' "13": "B", "14": "B", "15": "B", "16": "B", "17": "B", "18": "B", "19": "B"}'
      )},
     ),

    (("/configuration/coordinates", "/time"),
     (("charges(0)", CHARGE_ARRAY), "__len__()"),
     {"trajectory": short_traj, "frames": (0, 501, 1),
      "atom_charges": (
        '{"0": 1.2, "1": 1.2, "2": 1.2, "3": 1.2, "4": 1.2, "5": 1.2, '
          '"6": -0.5, "7": -0.5, "8": -0.5, "9": -0.5, "10": -0.5, "11": -0.5, '
          '"12": -0.5, "13": -0.5, "14": -0.5, "15": -0.5, "16": -0.5, "17": -0.5, '
          '"18": -0.5, "19": -0.5}'
      )}
     ),

    (("/configuration/coordinates", "/time"),
     (("chemical_system.unique_molecules()", ["C6_H14"]),),
     {"trajectory": short_traj, "frames": (0, 501, 1),
      "molecule_tolerance": [True, 0.04]},
     ),

    ((("/configuration/coordinates", (slice(None), slice(6, 20), slice(None))), "/time"),
     (("__len__()", ("chemical_system.number_of_atoms", 14))),
     {"trajectory": short_traj, "frames": (0, 501, 1),
      "atom_selection": '{"0": {"function_name": "select_atoms", "atom_types": ["H"]}}'},
     ),
],
                         ids=["null", "frames", "atoms", "unit_cell", "transmute",
                              "set_charges", "find_molecules", "editor_atoms"])
@pytest.mark.parametrize("result", ["trajectory_no_unit_cell.mdt"])
def test_editor(tmp_path, result, file_compare, traj_compare, parameters):
    temp_name = tmp_path / "output"
    out_name = temp_name.with_suffix(".mdt")
    log_name = temp_name.with_suffix(".log")
    result_name = CONV_DIR / result

    parameters["output_files"] = (temp_name, 64, 128, "gzip", "INFO")

    temp = IJob.create("TrajectoryEditor")
    temp.run(parameters, status=True)

    assert out_name.exists()
    assert log_name.exists()

    original = Trajectory(result_name)
    changed = Trajectory(out_name)

    for key in traj_compare:
        if isinstance(key, tuple):
            key, val = key
        elif isinstance(key, str):
            val = get_deep_attr(original, key)
        else:
            raise TypeError("Invalid key, key must be tuple or str. "
                            f"Received: {type(key).__name__}")

        new = get_deep_attr(changed, key)

        assert new == pytest.approx(val)

    original.close()
    changed.close()

    compare_hdf5(out_name, result_name, file_compare)
