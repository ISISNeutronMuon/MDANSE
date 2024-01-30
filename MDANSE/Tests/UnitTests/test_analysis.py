import unittest

import numpy as np

from MDANSE.MolecularDynamics.Analysis import *


class TestAnalysis(unittest.TestCase):
    def test_mean_square_deviation_valid_no_masses_no_root(self):
        coords1 = np.array([[1, 1, 1], [2, 1, 1], [3, 1, 1]])
        coords2 = np.array([[0, 0, 0], [0, 0, 0], [0, 0, 0]])

        msd = mean_square_deviation(coords1, coords2)
        self.assertEqual(20 / 3, msd)

    def test_mean_square_deviation_masses(self):
        coords1 = np.array([[1, 1, 1], [2, 1, 1], [3, 1, 1]])
        coords2 = np.array([[0, 0, 0], [0, 0, 0], [0, 0, 0]])
        masses = np.array([3, 10, 1])

        msd = mean_square_deviation(coords1, coords2, masses)
        self.assertEqual(80 / 14, msd)

    def test_mean_square_displacement_root(self):
        coords1 = np.array([[1, 1, 1], [2, 1, 1], [8, 1, 1]])
        coords2 = np.array([[0, 0, 0], [0, 0, 0], [0, 0, 0]])

        msd = mean_square_deviation(coords1, coords2, root=True)
        self.assertEqual(5, msd)

    def test_mean_square_deviation_invalid(self):
        coords1 = np.zeros((3, 3))
        coords2 = np.zeros((4, 3))

        with self.assertRaises(AnalysisError):
            mean_square_deviation(coords1, coords2)

    def test_mean_square_displacement(self):
        coords = np.array([[1, 1, 1], [2, 1, 1], [3, 1, 1]])
        msd = mean_square_displacement(coords)
        self.assertTrue(np.allclose([0.0, 1.0, 4.0], msd), f"\nactual = {msd}")

    def test_mean_square_fluctuation_no_root(self):
        coords = np.array([[1, 2, 1], [2, 1, 1], [10, 5, 5], [1, 1, 2]])
        msf = mean_square_fluctuation(coords)
        self.assertEqual(19.625, msf)

    def test_mean_square_fluctuation_root(self):
        coords = np.array([[1, 2, 1], [2, 1, 1], [10, 5, 5], [1, 1, 2]])
        msf = mean_square_fluctuation(coords, True)
        self.assertEqual(np.sqrt(19.625), msf)

    def test_radius_of_gyration_no_masses_no_root(self):
        coords = np.array([[1, 2, 1], [2, 1, 1], [10, 5, 5], [1, 1, 2]])
        rog = radius_of_gyration(coords)
        self.assertEqual(19.625, rog)

    def test_radius_of_gyration_masses(self):
        coords = np.array([[1, 2, 1], [2, 1, 1], [10, 5, 5], [1, 1, 2]])
        masses = np.array([1, 1, 5, 1])
        rog = radius_of_gyration(coords, masses)
        self.assertEqual(24.15625, rog)

    def test_radius_of_gyration_root(self):
        coords = np.array([[1, 2, 1], [2, 1, 1], [10, 5, 5], [1, 1, 2]])
        msf = mean_square_fluctuation(coords, True)
        self.assertEqual(np.sqrt(19.625), msf)
