
import numpy as np
import pytest

from test_helpers.paths import CONV_DIR

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Mathematics.Arithmetic import get_weights
from MDANSE.MolecularDynamics.Trajectory import Trajectory

short_traj = CONV_DIR / "short_trajectory_after_changes.mdt"
mdmc_traj = CONV_DIR / "Ar_mdmc_h5md.h5"
com_traj = CONV_DIR / "com_trajectory.mdt"


def test_b_coherent_values():
    test_values = [
        ['Cu', 'b_coherent', 7.718e-05],
        ['Cu', 'b_incoherent', 2.09e-05],
        ['O', 'b_coherent', 5.803e-05],
        ['O', 'b_incoherent', 7.98e-07],
        ['H', 'b_coherent', -3.739e-05],
        ['H', 'b_incoherent', 0.000252723],
    ]
    for atom, prop, value in test_values:
        dbase_value = ATOMS_DATABASE.get_atom_property(atom, prop)
        print(f"{atom} {prop} {value} {dbase_value}")
        assert np.isclose(complex(dbase_value).real, value, rtol=0.001, atol=0.001)

@pytest.mark.parametrize(
    "trajectory_filename",
    [short_traj, mdmc_traj, com_traj],
)
def test_properties_from_trajectory(trajectory_filename):
    traj = Trajectory(trajectory_filename)
    test_values = [
        ['Cu', 'b_coherent', 7.718e-05],
        ['Cu', 'b_incoherent', 2.09e-05],
        ['O', 'b_coherent', 5.803e-05],
        ['O', 'b_incoherent', 7.98e-07],
        ['H', 'b_coherent', -3.739e-05],
        ['H', 'b_incoherent', 0.000252723],
    ]
    for atom, prop, value in test_values:
        dbase_value = traj.get_atom_property(atom, prop)
        print(f"{atom} {prop} {value} {dbase_value}")
        assert np.isclose(complex(dbase_value).real, value, rtol=0.001, atol=0.001)

def test_CuSbS_from_trajectory():
    traj = Trajectory(short_traj)
    weights = {symbol: traj.get_atom_property(symbol, 'b_incoherent') for symbol in ['Cu', 'Sb', 'S']}
    composition = {'Cu': 208, 'S': 208, 'Sb': 64}
    wd = get_weights(weights, composition, 1)
    print(wd)
    assert np.isclose(wd[('Cu',)], 0.8714406908269398)
    assert np.isclose(wd[('S',)], 0.09831176886362851)
    assert np.isclose(wd[('Sb',)], 0.030247540309431713)
    assert np.isclose(wd['sum'], 1.0403049750413857e-05)

def test_CuSbS_from_trajectory_dim2():
    traj = Trajectory(short_traj)
    weights = {symbol: traj.get_atom_property(symbol, 'b_incoherent') for symbol in ['Cu', 'Sb', 'S']}
    composition = {'Cu': 208, 'S': 208, 'Sb': 64}
    wd = get_weights(weights, composition, 2)
    print(wd)
    expected = {
        ('Cu', 'Cu'): 0.7594088776289339,
        ('Cu', 'S'): 0.08567287577493887,
        ('Cu', 'Sb'): 0.026358937423066886,
        ('S', 'Cu'): 0.08567287577493887,
        ('S', 'S'): 0.00966520389709552,
        ('S', 'Sb'): 0.002973689191594138,
        ('Sb', 'Cu'): 0.026358937423066886,
        ('Sb', 'S'): 0.002973689191594138,
        ('Sb', 'Sb'): 0.0009149136947706968,
        'sum': 1.0822344410958575e-10}
    for key in expected:
        assert np.isclose(wd[key], expected[key])

def test_CuSbS_from_trajectory_dim2_sqrt():
    traj = Trajectory(short_traj)
    weights = {symbol: traj.get_atom_property(symbol, 'b_incoherent') for symbol in ['Cu', 'Sb', 'S']}
    composition = {'Cu': 208, 'S': 208, 'Sb': 64}
    wd = get_weights(weights, composition, 2, conc_exp=0.5)
    print(wd)
    expected = {
        ('Cu', 'Cu'): 1.75248202529754,
        ('Cu', 'S'): 0.19770663640370506,
        ('Cu', 'Sb'): 0.10965980820647803,
        ('S', 'Cu'): 0.19770663640370506,
        ('S', 'S'): 0.02230431668560505,
        ('S', 'Sb'): 0.012371294835675834,
        ('Sb', 'Cu'): 0.10965980820647803,
        ('Sb', 'S'): 0.012371294835675834,
        ('Sb', 'Sb'): 0.006861852710780225,
        'sum': 1.0822344410958575e-10}
    for key in expected:
        assert np.isclose(wd[key], expected[key])
