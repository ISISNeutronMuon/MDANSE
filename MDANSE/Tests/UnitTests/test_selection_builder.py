from __future__ import annotations

import numpy as np
import pytest
from test_helpers.paths import CONV_DIR

from MDANSE.Framework.AtomSelector.selection_builder import SelectionBuilder
from MDANSE.Framework.AtomSelector.selector import function_lookup
from MDANSE.MolecularDynamics.Trajectory import Trajectory

traj_2vb1 = CONV_DIR / "2vb1.mdt"

TRAJECTORY = Trajectory(traj_2vb1)

SET_FUNCS = {
    "set": lambda x, y: y,
    "union": set.union,
    "intersection": set.intersection,
    "difference": set.difference,
}


@pytest.mark.parametrize(
    "ops",
    (
        [("select_all", {})],
        [("select_molecules", {"molecule_names": ["H2 O1"], "operation_type": "set"})],
        [("select_molecules", {"molecule_names": ["C613 H959 N193 O185 S10"], "operation_type": "set"})],
        [("select_atoms", {"index_range": (1, 20)})],
        [("select_positions", {"position_minimum": [0.1, 0.1, 0.1]})],
        [("select_sphere", {"sphere_centre": [0.1, 0.1, 0.1], "sphere_radius": 1})],
        #  [("select_labels", {"atom_labels": ["C"]})],  - Never tested originally?
        # Multiple tasks
        [
            ("select_molecules", {"molecule_names": ["H2 O1"], "operation_type": "set"}),
            ("select_molecules", {"molecule_names": ["C613 H959 N193 O185 S10"], "operation_type": "union"})
         ],
        [("select_all", {}), ("select_none", {})],
        [("select_atoms", {"index_range": (1, 20)}), ("select_none", {})],
    ),
    ids = lambda x: "-".join(op[0] for op in x)
)
def test_selection_builder(ops):
    x = SelectionBuilder()

    acc = set()
    for op, params in ops:
        # Build ops in SelectionBuilder
        getattr(x, op)(**params)

        # Apply and accumulate ops directly
        val = function_lookup[op](TRAJECTORY, **params)
        acc = SET_FUNCS[params.get("operation_type", "union")](acc, val)


    assert len(x.ops) == len(ops)
    assert all(op == inop for (op, _), (inop, _) in zip(x.ops, ops))

    sel = x.apply(TRAJECTORY)

    assert sel
    assert acc == sel

def test_select_invert():
    x = SelectionBuilder()
    x.select_atoms(index_range=(0, 20))

    sel = x.apply(TRAJECTORY)
    assert sel == set(range(20))

    x.invert_selection()

    sel = x.apply(TRAJECTORY)
    assert sel == (set(TRAJECTORY.atom_indices) - set(range(20)))
