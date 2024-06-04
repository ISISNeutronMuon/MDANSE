import unittest

import numpy as np

from MDANSE.MolecularDynamics.UnitCell import UnitCell
from MDANSE.MolecularDynamics.UnitCell import get_expansions


class TestUnitCell(unittest.TestCase):
    def setUp(self):
        self.cell = UnitCell(np.array([[1, 0, 1], [0, 2, 0], [0, 0, 1 / 2]]))

    def test_instantiation(self):
        self.assertTrue(
            np.allclose(
                np.array([[1, 0, 1], [0, 2, 0], [0, 0, 1 / 2]]), self.cell._unit_cell
            ),
            f"actual = {self.cell._unit_cell}",
        )
        self.assertTrue(
            np.allclose(
                np.array([[1.0, 0.0, -2.0], [0.0, 0.5, 0.0], [0.0, 0.0, 2.0]]),
                self.cell._inverse_unit_cell,
            ),
            f"actual = {self.cell._inverse_unit_cell}",
        )

    def test_instantiation_invalid_cell_shape(self):
        with self.assertRaises(ValueError):
            UnitCell(np.ones((3, 5)))

    def test_dunder_eq(self):
        same_cell = UnitCell(np.array([[1, 0, 1], [0, 2, 0], [0, 0, 1 / 2]]))
        different_cell = UnitCell(np.array([[1, 0, 0], [0, 2, 0], [0, 0, 1 / 2]]))

        self.assertEqual(same_cell, self.cell)
        self.assertFalse(different_cell == self.cell)

    def test_dunder_repr(self):
        self.assertEqual(
            "MDANSE.MolecularDynamics.UnitCell.UnitCell(array([[1. , 0. , 1. ],\n       [0. , 2. , 0. ],\n"
            "       [0. , 0. , 0.5]]))",
            repr(self.cell),
        )

    def test_properties(self):
        self.assertTrue(
            np.allclose(np.array([1, 0, 1]), self.cell.a_vector),
            f"actual = {self.cell.a_vector}",
        )
        self.assertTrue(
            np.allclose(np.array([0, 2, 0]), self.cell.b_vector),
            f"actual = {self.cell.b_vector}",
        )
        self.assertTrue(
            np.allclose(np.array([0, 0, 1 / 2]), self.cell.c_vector),
            f"actual = {self.cell.c_vector}",
        )

    def test_matrices(self):
        self.assertTrue(
            np.allclose(
                np.array([[1, 0, 1], [0, 2, 0], [0, 0, 1 / 2]]), self.cell.direct
            ),
            f"actual = {self.cell.direct}",
        )
        self.assertTrue(
            np.allclose(
                np.array([[1.0, 0.0, -2.0], [0.0, 0.5, 0.0], [0.0, 0.0, 2.0]]),
                self.cell.inverse,
            ),
            f"actual = {self.cell.inverse}",
        )

    def test_transposed_matrices(self):
        self.assertTrue(
            np.allclose(
                np.array([[1, 0, 0], [0, 2, 0], [1, 0, 1 / 2]]),
                self.cell.transposed_direct,
            ),
            f"actual = {self.cell.transposed_direct}",
        )
        self.assertTrue(
            np.allclose(
                np.array([[1, 0, 0], [0, 0.5, 0], [-2, 0, 2]]),
                self.cell.transposed_inverse,
            ),
            f"actual = {self.cell.transposed_inverse}",
        )

    def test_volume(self):
        self.assertAlmostEqual(1, self.cell.volume)


def test_get_expansions_0():
    direct_matrix = np.array([
        [1, 0, 0],
        [0, 2, 0],
        [0, 0, 2],
    ]
    )
    assert (11, 6, 6) == get_expansions(direct_matrix, 10)


def test_get_expansions_1():
    direct_matrix = np.array([
        [2, 0, 0],
        [0, 10, 0],
        [0, 0, 11],
    ]
    )
    assert (16, 4, 4) == get_expansions(direct_matrix, 30)


def test_get_expansions_2():
    direct_matrix = np.array([
        [2, 0, 0],
        [0, 0, 11],
        [0, 10, 0],
    ]
    )
    assert (16, 4, 4) == get_expansions(direct_matrix, 30)


def test_get_expansions_3():
    direct_matrix = np.array([
        [0, 0, 11],
        [2, 0, 0],
        [0, 10, 0],
    ]
    )
    assert (4, 16, 4) == get_expansions(direct_matrix, 30)


def test_get_expansions_4():
    direct_matrix = np.array([
        [0, 0, 11],
        [0, 10, 0],
        [2, 0, 0],
    ]
    )
    assert (4, 4, 16) == get_expansions(direct_matrix, 30)
