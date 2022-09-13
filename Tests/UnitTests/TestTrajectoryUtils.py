import unittest

from MDANSE.Chemistry.ChemicalEntity import Molecule, Protein, ChemicalSystem
from MDANSE.MolecularDynamics.Configuration import RealConfiguration
from MDANSE.MolecularDynamics.TrajectoryUtils import *


class TestTrajectoryUtils(unittest.TestCase):
    def test_atom_index_to_molecule_index(self):
        m1 = Molecule('WAT', 'w1')
        m2 = Molecule('WAT', 'w2')
        cs = ChemicalSystem()
        cs.add_chemical_entity(m1)
        cs.add_chemical_entity(m2)

        result = atom_index_to_molecule_index(cs)
        self.assertDictEqual({0: 0, 1: 0, 2: 0, 3: 1, 4: 1, 5: 1}, result)

    def test_brute_formula(self):
        m = Molecule('WAT', 'w1')
        self.assertEqual('H2_O1', brute_formula(m))
        self.assertEqual('H2O1', brute_formula(m, ''))
        self.assertEqual('H2O', brute_formula(m, '', True))

    def test_build_connectivity(self):
        cs = ChemicalSystem()

        m = Molecule('WAT', 'w')
        ac = AtomCluster('ac', [Atom(), Atom(), Atom(), Atom()])
        a = Atom()
        ag = AtomGroup([Atom(parent=cs)])

        for ce in [m, ac, a, ag]:
            cs.add_chemical_entity(ce)

        coords = np.array([[0, 0, 0], [0, 0, 0], [0, 0, 0],
                           [1, 1, 1], [1.044, 1, 1], [0.95, 1, 1], [1.055, 1, 1],
                           [1, 1, 1.02], [1, 1, 1.06]])
        conf = RealConfiguration(cs, coords)
        cs.configuration = conf

        build_connectivity(cs, 0.005)

        self.assertEqual([m['OW']], m['HW1'].bonds)
        self.assertEqual([m['HW1'], m['HW2']], m['OW'].bonds)
        self.assertEqual([m['OW']], m['HW2'].bonds)

        self.assertEqual([ac[1].index, ac[2].index], [at.index for at in ac[0].bonds])
        self.assertEqual([ac[0].index, ac[3].index], [at.index for at in ac[1].bonds])
        self.assertEqual([ac[0].index], [at.index for at in ac[2].bonds])
        self.assertEqual([ac[1].index], [at.index for at in ac[3].bonds])

        self.assertEqual([ag._atoms[0].index], [at.index for at in a.bonds])
        self.assertEqual([a.index], [at.index for at in ag._atoms[0].bonds])

    def test_find_atoms_in_molecule(self):
        m1 = Molecule('WAT', 'water')
        m2 = Molecule('WAT', 'water')
        m3 = Molecule('WAT', 'water')
        p = Protein('protein')
        p.set_peptide_chains([m3])

        cs = ChemicalSystem()
        for ce in [m1, m2, p]:
            cs.add_chemical_entity(ce)

        water_hydrogens = find_atoms_in_molecule(cs, 'water', ['HW2', 'HW1'])
        protein_oxygens = find_atoms_in_molecule(cs, 'protein', ['OW'])
        empty = find_atoms_in_molecule(cs, 'INVALID', ['OW'])
        empty2 = find_atoms_in_molecule(cs, 'water', ['INVALID'])
        water_hydrogen_indices = find_atoms_in_molecule(cs, 'water', ['HW2', 'HW1'], True)

        self.assertEqual([[m1['HW2'], m1['HW1']], [m2['HW2'], m2['HW1']]], water_hydrogens)
        self.assertEqual([[m3['OW']]], protein_oxygens)
        self.assertEqual([], empty)
        self.assertEqual([[], []], empty2)
        self.assertEqual([[1, 2], [4, 5]], water_hydrogen_indices)

    def test_get_chemical_objects_dict(self):
        m1 = Molecule('WAT', 'water')
        m2 = Molecule('WAT', 'water')
        m4 = Molecule('WAT', 'dihydrogen oxide')

        m3 = Molecule('WAT', 'water')
        p = Protein('protein')
        p.set_peptide_chains([m3])

        cs = ChemicalSystem()
        for ce in [m1, m2, m4, p]:
            cs.add_chemical_entity(ce)

        self.assertDictEqual({'water': [m1, m2], 'dihydrogen oxide': [m4], 'protein': [p]},
                             get_chemical_objects_dict(cs))

    def test_group_atoms(self):
        atoms = [Atom() for _ in range(10)]
        molecules = [Molecule('WAT', '') for _ in range(5)]
        atoms.extend(molecules)

        cs = ChemicalSystem()
        for ce in atoms:
            cs.add_chemical_entity(ce)

        groups = group_atoms(cs, [[0, 1, 2], [], [1, 5], [10], [11, 12, 13, 11, 20]])

        self.assertEqual(4, len(groups))
        self.assertEqual([atoms[0], atoms[1], atoms[2]], groups[0]._atoms)
        self.assertEqual([atoms[1], atoms[5]], groups[1]._atoms)
        self.assertEqual([molecules[0]['OW']], groups[2]._atoms)
        self.assertEqual([molecules[0]['HW2'], molecules[0]['HW1'], molecules[1]['OW'], molecules[0]['HW2'],
                          molecules[3]['HW2']], groups[3]._atoms)

    def test_resolve_undefined_molecules_name(self):
        m1 = Molecule('WAT', '')
        m2 = Molecule('WAT', ' water ')
        m4 = Molecule('WAT', '   ')

        m3 = Molecule('WAT', '')
        p = Protein('protein')
        p.set_peptide_chains([m3])

        cs = ChemicalSystem()
        for ce in [m1, m2, m4, p]:
            cs.add_chemical_entity(ce)

        resolve_undefined_molecules_name(cs)

        self.assertEqual('H2O1', m1.name)
        self.assertEqual(' water ', m2.name)
        self.assertEqual('H2O1', m4.name)
        self.assertEqual('', m3.name)
        self.assertEqual('protein', p.name)

    def test_sorted_atoms_normal(self):
        atoms = [Atom() for _ in range(10)]
        for i, atom in enumerate(atoms):
            atom.index = i

        result = sorted_atoms([atoms[1], atoms[2], atoms[5], atoms[9], atoms[0], atoms[3], atoms[8], atoms[4],
                               atoms[7], atoms[6]])
        self.assertEqual(atoms, result)

    def test_sorted_atoms_return_names(self):
        atoms = [Atom() for _ in range(10)]
        for i, atom in enumerate(atoms):
            atom.index = i

        result = sorted_atoms([atoms[1], atoms[2], atoms[5], atoms[9], atoms[0], atoms[3], atoms[8], atoms[4],
                               atoms[7], atoms[6]], 'name')
        self.assertEqual([at.name for at in atoms], result)
