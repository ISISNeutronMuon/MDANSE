# Run the complete test suite
#
# Written by Konrad Hinsen.
#

import unittest

import mmtk_basic_tests
import mmtk_energy_tests
import mmtk_enm_tests
import mmtk_internal_coordinate_tests
import mmtk_normal_mode_tests
import mmtk_pickle_tests
import mmtk_restraint_tests
import mmtk_subspace_tests
import mmtk_trajectory_tests
import mmtk_universe_tests


import scientific_clustering_tests
import scientific_intepolation_tests
import scientific_signal_tests
import scientific_vector_tests


def suite():
    test_suite = unittest.TestSuite()
    test_suite.addTests(scientific_clustering_tests.suite())
    test_suite.addTests(scientific_intepolation_tests.suite())
    test_suite.addTests(scientific_signal_tests.suite())
    test_suite.addTests(scientific_vector_tests.suite())
    test_suite.addTests(mmtk_basic_tests.suite())
    test_suite.addTests(mmtk_energy_tests.suite())
    test_suite.addTests(mmtk_enm_tests.suite())
    test_suite.addTests(mmtk_internal_coordinate_tests.suite())
    test_suite.addTests(mmtk_normal_mode_tests.suite())
    test_suite.addTests(mmtk_pickle_tests.suite())
    test_suite.addTests(mmtk_restraint_tests.suite())
    test_suite.addTests(mmtk_subspace_tests.suite())
    test_suite.addTests(mmtk_trajectory_tests.suite())
    test_suite.addTests(mmtk_universe_tests.suite())
    return test_suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

