# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Tests/UnitTests/TestGeometry.py
# @brief     Implements module/class/test TestGeometry
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

''' 
Created on May 29, 2015

@author: Eric C. Pellegrini
'''

import unittest

import numpy as np

from MDANSE.Chemistry.ChemicalEntity import Atom, AtomCluster, ChemicalSystem
from MDANSE.MolecularDynamics.Configuration import PeriodicBoxConfiguration, PeriodicRealConfiguration, \
    RealConfiguration, ConfigurationError
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class TestPeriodicConfiguration(unittest.TestCase):
    """Uses PeriodicBoxConfiguration to test the methods of its abstract base class, _PeriodicConfiguration."""

    def setUp(self):
        self.chem_system = ChemicalSystem()
        self._nAtoms = 4

        atoms = []
        for i in range(self._nAtoms):
            atoms.append(Atom(symbol='H'))
        ac = AtomCluster('', atoms)

        self.chem_system.add_chemical_entity(ac)

        self.coords = np.random.uniform(0, 1, (self._nAtoms, 3))
        self.unit_cell = UnitCell(np.random.uniform(0, 1, (3, 3)))
        self.conf = PeriodicBoxConfiguration(self.chem_system, self.coords, self.unit_cell)

    def test_instantiation_valid(self):
        self.assertEqual(self.chem_system, self.conf.chemical_system)
        self.assertTrue(np.allclose(self.coords, self.conf['coordinates']))
        self.assertEqual(self.unit_cell, self.conf.unit_cell)

    def test_instantiation_invalid_unit_cell(self):
        coords = np.random.uniform(0, 1, (self._nAtoms, 3))
        unit_cell = UnitCell(np.random.uniform(0, 1, (4, 4)))
        with self.assertRaises(ValueError):
            PeriodicBoxConfiguration(self.chem_system, coords, unit_cell)

    def test_clone_valid_chemical_system(self):
        clone = self.conf.clone(self.chem_system)

        self.assertEqual(self.chem_system, clone.chemical_system)
        self.assertTrue(np.allclose(self.coords, clone['coordinates']))
        self.assertEqual(self.unit_cell, clone.unit_cell)

    def test_clone_valid_none(self):
        clone = self.conf.clone()

        self.assertEqual(self.chem_system, clone.chemical_system)
        self.assertTrue(np.allclose(self.coords, clone['coordinates']))
        self.assertEqual(self.unit_cell, clone.unit_cell)

    def test_unit_cell_setter_valid(self):
        unit_cell_new = UnitCell(np.random.uniform(0, 2, (3, 3)))
        self.conf.unit_cell = unit_cell_new
        self.assertEqual(unit_cell_new, self.conf.unit_cell)

    def test_unit_cell_setter_invalid_shape(self):
        unit_cell_new = UnitCell(np.random.uniform(0, 2, (4, 4)))
        with self.assertRaises(ValueError):
            self.conf.unit_cell = unit_cell_new


class TestPeriodicBoxConfiguration(unittest.TestCase):
    def setUp(self):
        self.chem_system = ChemicalSystem()
        self._nAtoms = 4

        atoms = []
        for i in range(self._nAtoms):
            atoms.append(Atom(symbol='H'))
        ac = AtomCluster('', atoms)

        self.chem_system.add_chemical_entity(ac)

    def test_fold_coordinates(self):
        coords = np.array([
            [-1.65955991, 4.40648987, -9.9977125],
            [-3.95334855, -7.06488218, -8.1532281],
            [-6.27479577, -3.08878546, -2.06465052],
            [0.77633468, -1.61610971, 3.70439001]])
        unit_cell = UnitCell(np.array([[1.0, 2.0, 1.0], [2.0, -1.0, 1.0], [3.0, 1.0, 1.0]]))
        conf = PeriodicBoxConfiguration(self.chem_system, coords, unit_cell)

        self.assertTrue(np.allclose(conf['coordinates'], [[-1.65955991, 4.40648987, -9.9977125],
                                                          [-3.95334855, -7.06488218, -8.1532281],
                                                          [-6.27479577, -3.08878546, -2.06465052],
                                                          [0.77633468, -1.61610971, 3.70439001]], rtol=1.0e-6),
                        f'actual = {conf["coordinates"]}')

    def test_to_box_coordinates(self):
        unit_cell = UnitCell(np.array([[1.0, 2.0, 1.0], [2.0, -1.0, 1.0], [3.0, 1.0, 1.0]]))
        coords = np.array(([1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]))
        conf = PeriodicBoxConfiguration(self.chem_system, coords, unit_cell)

        self.assertTrue(np.allclose(coords, conf.to_box_coordinates()), f'\nactual = {conf.to_box_coordinates()}')

    def test_to_real_coordinates(self):
        unit_cell = UnitCell(np.array([[1.0, 2.0, 1.0], [2.0, -1.0, 1.0], [3.0, 1.0, 1.0]]))
        coords = np.array(([1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]))
        conf = PeriodicBoxConfiguration(self.chem_system, coords, unit_cell)

        self.assertTrue(np.allclose([[14.0, 3.0, 6.0], [32.0, 9.0, 15.0], [50.0, 15.0, 24.0], [68.0, 21.0, 33.0]],
                                    conf.to_real_coordinates()), f'\nactual = {conf.to_real_coordinates()}')

    def test_to_real_configuration(self):
        unit_cell = UnitCell(np.array([[1.0, 2.0, 1.0], [2.0, -1.0, 1.0], [3.0, 1.0, 1.0]]))
        coords = np.array(([1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]))
        conf = PeriodicBoxConfiguration(self.chem_system, coords, unit_cell)
        real = conf.to_real_configuration()

        self.assertTrue(isinstance(real, PeriodicRealConfiguration))
        self.assertEqual(repr(self.chem_system), repr(real._chemical_system))
        self.assertEqual(['coordinates'], list(real._variables.keys()))
        self.assertTrue(np.allclose([[14.0, 3.0, 6.0], [32.0, 9.0, 15.0], [50.0, 15.0, 24.0], [68.0, 21.0, 33.0]],
                                    real['coordinates']), f'\nactual = {real["coordinates"]}')
        self.assertEqual(unit_cell, real._unit_cell)

    @unittest.skip
    def test_atoms_in_shell(self):
        unit_cell = UnitCell(np.array([[10, 0, 0], [0, 10, 0], [0, 0, 10]]))
        coords = np.array(([1, 1, 1], [2, 1, 1], [5, 1, 1], [9, 1, 1]))
        conf = PeriodicBoxConfiguration(self.chem_system, coords, unit_cell)
        atoms = conf.atoms_in_shell(0, 0.0, 5)

        self.assertEqual([1, 2], [at.index for at in atoms])

    def test_contiguous_configuration(self):
        unit_cell = UnitCell(np.array([[2, 1, 0], [-3, 2, 0], [2, 1, -4]]))
        coords = [[0.1, 0.1, 0.1], [0.3, 0.2, 0.4], [-1.3, -1.1, -1.3], [1.9, 1.5, 1.9]]
        conf = PeriodicBoxConfiguration(self.chem_system, coords, unit_cell)
        contiguous_conf = conf.contiguous_configuration()

        self.assertTrue(isinstance(contiguous_conf, PeriodicBoxConfiguration))
        self.assertEqual(repr(self.chem_system), repr(contiguous_conf._chemical_system))
        self.assertEqual(['coordinates'], list(contiguous_conf._variables.keys()))
        self.assertTrue(np.allclose([[0.1, 0.1, 0.1], [0.8, 1.1, -1.6], [-0.9, -0.8, 1.2], [-1.9, 0.8, 0.4]],
                                    contiguous_conf['coordinates']), f'\nactual = {contiguous_conf["coordinates"]}')

    @unittest.skip
    def test_contiguous_offsets_valid_no_input(self):
        self.chem_system.add_chemical_entity(AtomCluster('2', [Atom(), Atom()]))

        unit_cell = UnitCell(np.array([[2, 1, 0], [-3, 2, 0], [2, 1, -4]]))
        coords = [[0.1, 0.1, 0.1], [0.3, 0.2, 0.4], [-1.3, -1.1, -1.3], [1.9, 1.5, 1.9], [1, 1.5, 1], [0.1, 1.5, 1.1]]
        conf = PeriodicBoxConfiguration(self.chem_system, coords, unit_cell)
        offsets = conf.contiguous_offsets()

        self.assertTrue(np.allclose([[0, 0, 0], [0.8, 1.1, -1.6], [-0.9, -0.8, 1.2], [-1.9, 0.8, 0.4], [0, 0, 0],
                                     [1.9, 1.5, 1.9]], offsets), f'\nactual = {offsets}')

    @unittest.skip
    def test_contiguous_offsets_valid_specified_list(self):
        self.chem_system.add_chemical_entity(AtomCluster('2', [Atom(), Atom()]))

        unit_cell = UnitCell(np.array([[2, 1, 0], [-3, 2, 0], [2, 1, -4]]))
        coords = [[0.1, 0.1, 0.1], [0.3, 0.2, 0.4], [-1.3, -1.1, -1.3], [1.9, 1.5, 1.9], [1, 1.5, 1], [0.1, 1.5, 1.1]]
        conf = PeriodicBoxConfiguration(self.chem_system, coords, unit_cell)
        offsets = conf.contiguous_offsets(self.chem_system.chemical_entities[0])

        self.assertTrue(np.allclose([[0, 0, 0], [0.8, 1.1, -1.6], [-0.9, -0.8, 1.2], [-1.9, 0.8, 0.4]], offsets),
                        f'\nactual = {offsets}')

    def test_contiguous_offsets_invalid(self):
        unit_cell = UnitCell(np.array([[2, 1, 0], [-3, 2, 0], [2, 1, -4]]))
        coords = [[0.1, 0.1, 0.1], [0.3, 0.2, 0.4], [-1.3, -1.1, -1.3], [1.9, 1.5, 1.9]]
        conf = PeriodicBoxConfiguration(self.chem_system, coords, unit_cell)

        with self.assertRaises(ConfigurationError):
            conf.contiguous_offsets([Atom(parent=ChemicalSystem())])


class TestPeriodicRealConfiguration(unittest.TestCase):
    def setUp(self):
        self.chem_system = ChemicalSystem()
        self._nAtoms = 4

        atoms = []
        for i in range(self._nAtoms):
            atoms.append(Atom(symbol='H'))
        ac = AtomCluster('', atoms)

        self.chem_system.add_chemical_entity(ac)

    def test_fold_coordinates(self):
        coords = np.array([
            [-1.65955991, 4.40648987, -9.9977125],
            [-3.95334855, -7.06488218, -8.1532281],
            [-6.27479577, -3.08878546, -2.06465052],
            [0.77633468, -1.61610971, 3.70439001]])
        unit_cell = UnitCell(np.array([[2, 1, 0], [-3, 2, 0], [2, 1, -4]]))
        conf = PeriodicRealConfiguration(self.chem_system, coords, unit_cell)
        conf.fold_coordinates()

        self.assertTrue(np.allclose(conf['coordinates'], [[-0.65955991, 1.40648987, -1.9977125],
                                                          [1.04665145, -1.06488218, -0.1532281],
                                                          [-0.27479577, -0.08878546, 1.93534948],
                                                          [-0.22366532, 1.38389029, -0.29560999]], rtol=1.0e-6),
                        f'actual = {conf["coordinates"]}')

    def test_to_box_coordinates(self):
        coords = np.array([[14.0, 3.0, 6.0], [32.0, 9.0, 15.0], [50.0, 15.0, 24.0], [68.0, 21.0, 33.0]])
        unit_cell = UnitCell(np.array([[1.0, 2.0, 1.0], [2.0, -1.0, 1.0], [3.0, 1.0, 1.0]]))
        conf = PeriodicRealConfiguration(self.chem_system, coords, unit_cell)

        box = conf.to_box_coordinates()
        self.assertTrue(np.allclose([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]], box), f'\nactual = {box}')

    def test_to_box_configuration(self):
        coords = np.array([[14.0, 3.0, 6.0], [32.0, 9.0, 15.0], [50.0, 15.0, 24.0], [68.0, 21.0, 33.0]])
        unit_cell = UnitCell(np.array([[1.0, 2.0, 1.0], [2.0, -1.0, 1.0], [3.0, 1.0, 1.0]]))
        conf = PeriodicRealConfiguration(self.chem_system, coords, unit_cell)

        box_conf = conf.to_box_configuration()
        self.assertTrue(isinstance(box_conf, PeriodicBoxConfiguration))
        self.assertEqual(repr(self.chem_system), repr(box_conf._chemical_system))
        self.assertEqual(['coordinates'], list(box_conf._variables.keys()))
        self.assertTrue(np.allclose([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]], box_conf['coordinates']),
                        f'\nactual = {box_conf["coordinates"]}')
        self.assertEqual(unit_cell, box_conf._unit_cell)

    def test_to_real_coordinates(self):
        coords = np.array([[14.0, 3.0, 6.0], [32.0, 9.0, 15.0], [50.0, 15.0, 24.0], [68.0, 21.0, 33.0]])
        unit_cell = UnitCell(np.array([[1.0, 2.0, 1.0], [2.0, -1.0, 1.0], [3.0, 1.0, 1.0]]))
        conf = PeriodicRealConfiguration(self.chem_system, coords, unit_cell)

        real = conf.to_real_coordinates()
        self.assertTrue(np.allclose(coords, real), f'\nactual = {real}')

    @unittest.skip
    def test_atoms_in_shell(self):
        coords = np.array([[1, 1, 1], [2, 1, 1], [5, 1, 1], [9, 1, 1]])
        unit_cell = UnitCell(np.array([[10, 0, 0], [0, 10, 0], [0, 0, 10]]))
        conf = PeriodicRealConfiguration(self.chem_system, coords, unit_cell)
        atoms = conf.atoms_in_shell(0, 0, 5)

        self.assertEqual([1, 2], [at.index for at in atoms])

    @unittest.skip
    def test_contiguous_configuration(self):
        coords = np.array([[14.0, 3.0, 6.0], [32.0, 9.0, 15.0], [50.0, 15.0, 24.0], [68.0, 21.0, 33.0]])
        unit_cell = UnitCell(np.array([[1.0, 2.0, 1.0], [2.0, -1.0, 1.0], [3.0, 1.0, 1.0]]))
        conf = PeriodicRealConfiguration(self.chem_system, coords, unit_cell)

        result = conf.contiguous_configuration()
        self.assertTrue(isinstance(result, PeriodicRealConfiguration))
        self.assertEqual(repr(self.chem_system), repr(result._chemical_system))
        self.assertEqual(['coordinates'], list(result._variables.keys()))
        self.assertTrue(np.allclose([[14., 3., 6.], [14., 3., 6.], [14., 3., 6.], [14., 3., 6.]],
                                    result['coordinates']), f'\nactual = {result["coordinates"]}')
        self.assertEqual(unit_cell, result._unit_cell)

    @unittest.skip
    def test_continuous_configuration(self):
        coords = np.array([[14.0, 3.0, 6.0], [32.0, 9.0, 15.0], [50.0, 15.0, 24.0], [68.0, 21.0, 33.0]])
        unit_cell = UnitCell(np.array([[1.0, 2.0, 1.0], [2.0, -1.0, 1.0], [3.0, 1.0, 1.0]]))
        conf = PeriodicRealConfiguration(self.chem_system, coords, unit_cell)

        result = conf.continuous_configuration()
        self.assertTrue(isinstance(result, PeriodicRealConfiguration))
        self.assertEqual(repr(self.chem_system), repr(result._chemical_system))
        self.assertEqual(['coordinates'], list(result._variables.keys()))
        self.assertTrue(np.allclose([[14.0, 3.0, 6.0], [32.0, 9.0, 15.0], [50.0, 15.0, 24.0], [68.0, 21.0, 33.0]],
                                    result['coordinates']), f'\nactual = {result["coordinates"]}')
        self.assertEqual(unit_cell, result._unit_cell)

    @unittest.skip
    def test_contiguous_offsets_valid_no_input(self):
        coords = np.array([[14.0, 3.0, 6.0], [32.0, 9.0, 15.0], [50.0, 15.0, 24.0], [68.0, 21.0, 33.0]])
        unit_cell = UnitCell(np.array([[1.0, 2.0, 1.0], [2.0, -1.0, 1.0], [3.0, 1.0, 1.0]]))
        conf = PeriodicRealConfiguration(self.chem_system, coords, unit_cell)

        offsets = conf.contiguous_offsets()
        self.assertTrue(np.allclose([[ 0.,  0.,  0.], [-3., -3., -3.], [-6., -6., -6.], [-9., -9., -9.]], offsets),
                        f'\nactual = {offsets}')

    @unittest.skip
    def test_contiguous_offsets_valid_specified_list(self):
        self.chem_system.add_chemical_entity(AtomCluster('2', [Atom(), Atom()]))

        coords = np.array([[14.0, 3.0, 6.0], [32.0, 9.0, 15.0], [50.0, 15.0, 24.0], [68.0, 21.0, 33.0],
                          [15.0, 15.0, 15.0], [10.0, 10.0, 10.0]])
        unit_cell = UnitCell(np.array([[1.0, 2.0, 1.0], [2.0, -1.0, 1.0], [3.0, 1.0, 1.0]]))
        conf = PeriodicRealConfiguration(self.chem_system, coords, unit_cell)

        offsets = conf.contiguous_offsets(self.chem_system.chemical_entities[0])
        self.assertTrue(np.allclose([[ 0.,  0.,  0.], [-3., -3., -3.], [-6., -6., -6.], [-9., -9., -9.]],
                                    offsets), f'\nactual = {offsets}')

    def test_contiguous_offsets_invalid(self):
        coords = np.array([[14.0, 3.0, 6.0], [32.0, 9.0, 15.0], [50.0, 15.0, 24.0], [68.0, 21.0, 33.0]])
        unit_cell = UnitCell(np.array([[1.0, 2.0, 1.0], [2.0, -1.0, 1.0], [3.0, 1.0, 1.0]]))
        conf = PeriodicRealConfiguration(self.chem_system, coords, unit_cell)

        with self.assertRaises(ConfigurationError):
            conf.contiguous_offsets([Atom(parent=ChemicalSystem())])


@unittest.skip
class TestConfiguration(unittest.TestCase):
    '''
    Unittest for the geometry-related functions
    '''

    def setUp(self):
        self._chemicalSystem = ChemicalSystem()
        self._nAtoms = 4

        atoms = []
        for i in range(self._nAtoms):
            atoms.append(Atom(symbol='H'))
        ac = AtomCluster('', atoms)

        self._chemicalSystem.add_chemical_entity(ac)

    def test_assertion(self):
        coordinates = np.random.uniform(0, 1, (2, 3))
        with self.assertRaises(ValueError):
            _ = RealConfiguration(self._chemicalSystem, coordinates)

        coordinates = np.random.uniform(0, 1, (2, 3))
        with self.assertRaises(ValueError):
            _ = BoxConfiguration(self._chemicalSystem, coordinates)

    def test_real_configuration(self):
        coordinates = np.random.uniform(0, 1, (self._nAtoms, 3))
        conf = RealConfiguration(self._chemicalSystem, coordinates)
        self.assertTrue(np.allclose(conf.to_real_coordinates(), coordinates, rtol=1.0e-6))

    def test_to_box_coordinates(self):
        coordinates = np.random.uniform(0, 1, (self._nAtoms, 3))
        conf = RealConfiguration(self._chemicalSystem, coordinates)
        self.assertTrue(np.allclose(conf.to_box_coordinates(), coordinates, rtol=1.0e-6))

        unitCell = np.array([[1.0, 2.0, 1.0], [2.0, -1.0, 1.0], [3.0, 1.0, 1.0]], dtype=np.float)
        coordinates = np.array(([1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]), dtype=np.float)
        conf = RealConfiguration(self._chemicalSystem, coordinates, unitCell)

        boxCoordinates = conf.to_box_coordinates()
        self.assertTrue(np.allclose(boxCoordinates, [[3.0, 2.0, -2.0],
                                                     [5.4, 3.2, -2.6],
                                                     [7.8, 4.4, -3.2],
                                                     [10.2, 5.6, -3.8]], rtol=1.0e-6))

    def test_fold_coordinates(self):
        unitCell = np.array([[1.0, 2.0, 1.0], [2.0, -1.0, 1.0], [3.0, 1.0, 1.0]], dtype=np.float)
        coordinates = np.array(([1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]), dtype=np.float)
        conf = RealConfiguration(self._chemicalSystem, coordinates, unitCell)
        conf.fold_coordinates()

        self.assertTrue(np.allclose(conf.variables['coordinates'], [[0.0, 0.0, 0.0],
                                                                    [2.0, 1.0, 1.0],
                                                                    [0.0, -1.0, 0.0],
                                                                    [0.0, 1.0, 0.0]], rtol=1.0e-6))

    def test_box_configuration(self):
        coordinates = np.random.uniform(0, 1, (self._nAtoms, 3))
        conf = BoxConfiguration(self._chemicalSystem, coordinates)
        self.assertTrue(np.allclose(conf.to_box_coordinates(), coordinates, rtol=1.0e-6))

    def test_to_real_coordinates(self):
        unitCell = np.array([[1.0, 2.0, 1.0], [2.0, -1.0, 1.0], [3.0, 1.0, 1.0]], dtype=np.float)
        coordinates = np.array(([1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]), dtype=np.float)
        conf = BoxConfiguration(self._chemicalSystem, coordinates, unitCell)

        realCoordinates = conf.to_real_coordinates()
        self.assertTrue(np.allclose(realCoordinates, [[14.0, 3.0, 6.0],
                                                      [32.0, 9.0, 15.0],
                                                      [50.0, 15.0, 24.0],
                                                      [68.0, 21.0, 33.0]], rtol=1.0e-6))

    def test_fold_coordinates_real_pbc(self):
        unit_cell = np.array([[2, 1, 0], [-3, 2, 0], [2, 1, -4]], dtype=np.float)
        coords = np.array([
            [-1.65955991, 4.40648987, -9.9977125],
            [-3.95334855, -7.06488218, -8.1532281],
            [-6.27479577, -3.08878546, -2.06465052],
            [0.77633468, -1.61610971, 3.70439001]])

        conf = RealConfiguration(self._chemicalSystem, coords, unit_cell)
        conf.fold_coordinates()

        real_coordinates = conf['coordinates']

        self.assertTrue(np.allclose(real_coordinates, [[-0.65955991, 1.40648987, -1.9977125],
                                                       [1.04665145, -1.06488218, -0.1532281],
                                                       [-0.27479577, -0.08878546, 1.93534948],
                                                       [-0.22366532, 1.38389029, -0.29560999]], rtol=1.0e-6))

    def test_fold_coordinates_real_nopbc(self):
        coords = np.array([
            [-1.65955991, 4.40648987, -9.9977125],
            [-3.95334855, -7.06488218, -8.1532281],
            [-6.27479577, -3.08878546, -2.06465052],
            [0.77633468, -1.61610971, 3.70439001]])

        conf = RealConfiguration(self._chemicalSystem, coords)
        conf.fold_coordinates()

        real_coordinates = conf['coordinates']

        self.assertTrue(np.allclose(real_coordinates, coords, rtol=1.0e-6))

    def test_fold_coordinates_box_pbc(self):
        unit_cell = np.array([[2, 1, 0], [-3, 2, 0], [2, 1, -4]], dtype=np.float)
        coords = np.array([
            [0.6, 0.8, -0.7],
            [0.3, -0.1, 1.2],
            [0.4, 0.2, -0.9],
            [-0.2, 0.4, 0.6]])

        conf = BoxConfiguration(self._chemicalSystem, coords, unit_cell)
        conf.fold_coordinates()

        real_coordinates = conf['coordinates']

        self.assertTrue(np.allclose(real_coordinates, [[-0.4, -0.2, 0.3],
                                                       [0.3, -0.1, 0.2],
                                                       [0.4, 0.2, 0.1],
                                                       [-0.2, 0.4, -0.4]], rtol=1.0e-6))

    def test_fold_coordinates_box_nopbc(self):
        coords = np.array([
            [0.6, 0.8, -0.7],
            [0.3, -0.1, 1.2],
            [0.4, 0.2, -0.9],
            [-0.2, 0.4, 0.6]])

        conf = BoxConfiguration(self._chemicalSystem, coords)
        conf.fold_coordinates()

        real_coordinates = conf['coordinates']

        self.assertTrue(np.allclose(real_coordinates, coords, rtol=1.0e-6))

    def test_contiguous_configuration_real_pbc(self):
        unit_cell = np.array([[2, 1, 0], [-3, 2, 0], [2, 1, -4]], dtype=np.float)

        box_coords = [[0.1, 0.1, 0.1], [0.3, 0.2, 0.4], [-1.3, -1.1, -1.3], [1.9, 1.5, 1.9]]
        box_conf = BoxConfiguration(self._chemicalSystem, box_coords, unit_cell)
        real_coords = box_conf.to_real_coordinates()
        real_conf = RealConfiguration(self._chemicalSystem, real_coords, unit_cell)

        contiguous_conf = real_conf.contiguous_configuration()
        real_coordinates = contiguous_conf['coordinates']

        self.assertTrue(np.allclose(real_coordinates, [[0.1, 0.4, -0.4],
                                                       [0.8, 1.1, -1.6],
                                                       [-0.9, -0.8, 1.2],
                                                       [-1.9, 0.8, 0.4]], rtol=1.0e-6))


def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestConfiguration))
    return s


if __name__ == '__main__':
    unittest.main(verbosity=2)
