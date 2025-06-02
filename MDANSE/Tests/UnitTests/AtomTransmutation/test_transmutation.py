from contextlib import nullcontext as success

import pytest
from MDANSE.MolecularDynamics.Trajectory import Trajectory
from MDANSE.Framework.Configurators.AtomTransmutationConfigurator import AtomTransmuter
from test_helpers.paths import CONV_DIR

traj_2vb1 = CONV_DIR / "2vb1.mdt"


@pytest.fixture(scope="module")
def protein_trajectory():
    protein_trajectory = Trajectory(traj_2vb1)
    return protein_trajectory

@pytest.mark.parametrize("transmutations, expected", [
    ((), success({})),

    ([('{"0": {"function_name": "select_atoms", "atom_types": ["S"]}}',
       "CCC")],
     pytest.raises(ValueError, match="CCC not found in the atom database")),

    ([('{"0": {"function_name": "select_atoms", "atom_types": ["S"]}}', "C")],
     success({98: "C", 175: "C", 468: "C", 990: "C", 1160: "C",
              1217: "C", 1404: "C", 1557: "C", 1731: "C", 1913: "C"}),
    ),

    ([('{"0": {"function_name": "select_atoms", "atom_types": ["S"]}}', "C"),
      ('{"0": {"function_name": "select_atoms", "index_list": [98]}}', "N")],
     success({98: "N", 175: "C", 468: "C", 990: "C", 1160: "C",
              1217: "C", 1404: "C", 1557: "C", 1731: "C", 1913: "C"}),
     ),

    ([('{"0": {"function_name": "select_atoms", "atom_types": ["S"]}}', "C"),
      ('{"0": {"function_name": "select_atoms", "index_list": [98]}}', "S")],
     success({175: "C", 468: "C", 990: "C", 1160: "C", 1217: "C",
              1404: "C", 1557: "C", 1731: "C", 1913: "C"}),
     ),

    ([('{"0": {"function_name": "select_atoms", "atom_types": ["S"]}}', "C"),
      ('{"0": {"function_name": "select_atoms", "index_list": [98, 99]}}', "S")],
     success({99: "S", 175: "C", 468: "C", 990: "C", 1160: "C",
              1217: "C", 1404: "C", 1557: "C", 1731: "C", 1913: "C"}),
     ),
])
def test_atom_transmutation(protein_trajectory, transmutations, expected):
    atm_transmuter = AtomTransmuter(protein_trajectory)
    with expected as val:
        for transmute in transmutations:
            atm_transmuter.apply_transmutation(*transmute)
        assert atm_transmuter.get_setting() == val

def test_atom_transmutation_reset(protein_trajectory):
    atm_transmuter = AtomTransmuter(protein_trajectory)
    atm_transmuter.apply_transmutation('{"0": {"function_name": "select_atoms", "atom_types": ["S"]}}', "C")
    atm_transmuter.apply_transmutation('{"0": {"function_name": "select_atoms", "index_list": [98, 99]}}', "S")
    atm_transmuter.reset_setting()
    mapping = atm_transmuter.get_setting()
    assert mapping == {}
