import abc
import collections
import copy

import numpy as np

import h5py

from MDANSE.Chemistry import ATOMS_DATABASE, MOLECULES_DATABASE, NUCLEOTIDES_DATABASE, RESIDUES_DATABASE
from MDANSE.Chemistry.Databases import ResiduesDatabaseError, NucleotidesDatabaseError
from MDANSE.Mathematics.Geometry import superposition_fit
from MDANSE.Mathematics.LinearAlgebra import delta, Tensor, Vector
from MDANSE.Mathematics.Transformation import Rotation, Transformation, Translation


class UnknownAtomError(Exception):
    pass


class InvalidMoleculeError(Exception):

    def __init__(self, code):
        self._message = 'The atom {} is unknown'.format(code)

    def __str__(self):
        return self._message


class UnknownMoleculeError(Exception):

    def __init__(self, code):
        self._message = 'The molecule {} is unknown'.format(code)

    def __str__(self):
        return self._message


class InconsistentAtomNamesError(Exception):
    pass


class InvalidResidueError(Exception):
    pass


class UnknownResidueError(Exception):

    def __init__(self, code):
        self._message = 'The residue {} is unknown'.format(code)

    def __str__(self):
        return self._message


class InvalidVariantError(Exception):
    pass


class InvalidNucleotideChainError(Exception):
    pass


class InvalidPeptideChainError(Exception):
    pass


class InvalidChemicalEntityError(Exception):
    pass


class InconsistentChemicalSystemError(Exception):
    pass


class ChemicalEntityError(Exception):
    pass


class _ChemicalEntity(metaclass=abc.ABCMeta):
    """Abstract base class for other chemical entities."""

    def __init__(self):

        self._parent = None

        self._name = ''

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state

    @abc.abstractmethod
    def atom_list(self):
        pass

    @abc.abstractmethod
    def copy(self):
        pass

    def full_name(self):

        full_name = self.name
        parent = self._parent
        while parent is not None:
            full_name = '{}.{}'.format(parent.name, full_name)
            parent = parent.parent

        return full_name

    @abc.abstractmethod
    def number_of_atoms(self):
        pass

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        self._parent = parent

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @abc.abstractmethod
    def serialize(self, h5_file):
        pass

    def group(self, name):

        selected_atoms = []
        for at in self.atom_list():
            if not hasattr(at, 'groups'):
                continue

            if name in at.groups:
                selected_atoms.append(at)

        return selected_atoms

    def center_of_mass(self, configuration):

        coords = configuration['coordinates']

        com = np.zeros((3,), dtype=np.float)
        sum_masses = 0.0
        for at in self.atom_list():
            m = ATOMS_DATABASE[at.symbol]['atomic_weight']
            com += m * coords[at.index, :]
            sum_masses += m

        com /= sum_masses

        return com

    def mass(self):

        sum_masses = 0.0
        for at in self.atom_list():
            m = ATOMS_DATABASE[at.symbol]['atomic_weight']
            sum_masses += m

        return sum_masses

    def masses(self):

        masses = []
        for at in self.atom_list():
            m = ATOMS_DATABASE[at.symbol]['atomic_weight']
            masses.append(m)

        return masses

    def find_transformation_as_quaternion(self, conf1, conf2=None):

        chemical_system = self.root_chemical_system()
        if chemical_system.configuration.is_periodic:
            raise ValueError("superposition in periodic configurations is not defined")

        if conf1.chemical_system != chemical_system:
            raise ValueError("conformations comes from different chemical systems")

        if conf2 is None:
            conf2 = conf1
            conf1 = chemical_system.configuration
        else:
            if conf2.chemical_system != chemical_system:
                raise ValueError("conformations comes from different chemical systems")

        weights = chemical_system.masses()

        return superposition_fit([
            (
                weights[a.index],
                Vector(*conf1['coordinates'][a.index, :]),
                Vector(*conf2['coordinates'][a.index, :])) for a in self.atom_list()])

    def find_transformation(self, conf1, conf2=None):
        """
        :param conf1: a configuration object
        :type conf1: :class:`~MDANSE.MolecularDynamics.Configuration.Configuration`
        :param conf2: a configuration object, or None for the current configuration
        :type conf2: :class:`~MDANSE.MolecularDynamics.Configuration.Configuration` or NoneType
        :returns: the linear transformation that, when applied to
                  the object in configuration conf1, minimizes the
                  RMS distance to the conformation in conf2, and the
                  minimal RMS distance.
                  If conf2 is None, returns the transformation from the
                  current configuration to conf1 and the associated
                  RMS distance.
        """

        q, cm1, cm2, rms = self.find_transformation_as_quaternion(conf1, conf2)
        return Translation(cm2) * q.asRotation() * Translation(-cm1), rms

    def center_and_moment_of_inertia(self, configuration):
        """
        :param conf: a configuration object, or None for the current configuration
        :type conf: :class:`~MDANSE.MolecularDynamics.Configuration.Configuration`
        :returns: the center of mass and the moment of inertia tensor
                  in the given configuration
        """

        m = 0.0
        mr = Vector(0.0, 0.0, 0.0)
        t = Tensor(3 * [3 * [0.0]])
        for atom in self.atom_list():
            ma = ATOMS_DATABASE[atom.symbol]['atomic_weight']
            r = Vector(configuration['coordinates'][atom.index, :])
            m += ma
            mr += ma * r
            t += ma * r.dyadic_product(r)
        cm = mr / m
        t -= m * cm.dyadic_product(cm)
        t = t.trace() * delta - t
        return cm, t

    def normalizing_transformation(self, configuration, repr=None):
        """
        Calculate a linear transformation that shifts the center of mass
        of the object to the coordinate origin and makes its
        principal axes of inertia parallel to the three coordinate
        axes.

        :param repr: the specific representation for axis alignment:
          Ir    : x y z <--> b c a
          IIr   : x y z <--> c a b
          IIIr  : x y z <--> a b c
          Il    : x y z <--> c b a
          IIl   : x y z <--> a c b
          IIIl  : x y z <--> b a c
        :returns: the normalizing transformation
        :rtype: Scientific.Geometry.Transformation.RigidBodyTransformation
        """

        cm, inertia = self.center_and_moment_of_inertia(configuration)
        ev, diag = np.linalg.eig(inertia.array)
        diag = np.transpose(diag)
        if np.linalg.det(diag) < 0:
            diag[0] = -diag[0]
        if repr != None:
            seq = np.argsort(ev)
            if repr == 'Ir':
                seq = np.array([seq[1], seq[2], seq[0]])
            elif repr == 'IIr':
                seq = np.array([seq[2], seq[0], seq[1]])
            elif repr == 'Il':
                seq = seq[2::-1]
            elif repr == 'IIl':
                seq[1:3] = np.array([seq[2], seq[1]])
            elif repr == 'IIIl':
                seq[0:2] = np.array([seq[1], seq[0]])
            diag = np.take(diag, seq)
        return Rotation(diag) * Translation(-cm)

    def root_chemical_system(self):

        if isinstance(self, ChemicalSystem):
            return self
        else:
            return self._parent.root_chemical_system()

    def top_level_chemical_entity(self):

        if isinstance(self._parent, ChemicalSystem):
            return self
        else:
            return self._parent.top_level_chemical_entity()


class Atom(_ChemicalEntity):
    """A representation of atom in a trajectory."""

    def __init__(self, **kwargs):

        super(Atom, self).__init__()

        self._symbol = kwargs.get('symbol', 'H')

        if self._symbol not in ATOMS_DATABASE:
            raise UnknownAtomError('The atom {} is unknown'.format(self.symbol))

        self._name = kwargs.pop('name', self.symbol)

        self._bonds = kwargs.pop('bonds', [])

        self._groups = kwargs.pop('groups', [])

        self._ghost = kwargs.pop('ghost', False)

        self._index = None

        self._parent = None

        for k, v in kwargs.items():
            setattr(self, k, v)

    def copy(self) -> 'Atom':
        """
        Creates a copy of the current instance of this class.

        :return: A copy of the current instance.
        :rtype: MDANSE.Chemistry.ChemicalEntity.Atom
        """

        a = Atom(symbol=self._symbol)

        for k, v in self.__dict__.items():
            setattr(a, k, v)

        a._bonds = [bat.copy() for bat in self._bonds]

        return a

    def __getitem__(self, item):

        return getattr(self, item)

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):

        self.__dict__ = state

    def __str__(self):

        return self.full_name()

    def __repr__(self):
        contents = ''
        for key, value in self.__dict__.items():
            key = key[1:] if key[0] == "_" else key
            if key == "bonds":
                bonds = ', '.join([f'Atom({atom.name if hasattr(atom, "name") else atom})' for atom in self.bonds])
                contents += f'bonds=[{bonds}]'
            elif isinstance(value, _ChemicalEntity):
                class_name = str(type(value)).replace('<class \'', '').replace('\'>', '')
                contents += f'{key}={class_name}({value.name})'
            else:
                contents += f'{key}={repr(value)}'
            contents += ', '

        return f'MDANSE.Chemistry.ChemicalEntity.Atom({contents[:-2]})'

    def atom_list(self) -> list['Atom']:
        return [self] if not self.ghost else []

    @staticmethod
    def total_number_of_atoms() -> int:
        return 1

    def number_of_atoms(self) -> int:
        return int(self.ghost)

    @property
    def bonds(self) -> list['Atom']:
        """A list of atoms to which this atom is chemically bonded."""
        return self._bonds

    @bonds.setter
    def bonds(self, bonds: list) -> None:

        self._bonds = bonds

    @property
    def ghost(self) -> bool:

        return self._ghost

    @ghost.setter
    def ghost(self, ghost: bool) -> None:

        self._ghost = ghost

    @property
    def groups(self) -> list[str]:
        """A list of groups to which this atom belongs."""
        return self._groups

    @property
    def index(self) -> int:
        """The index of the atom in the trajectory. Once set, it cannot be changed anymore."""
        return self._index

    @index.setter
    def index(self, index: int) -> None:
        if self._index is not None:
            return
        self._index = index

    @property
    def name(self) -> str:
        """The full name of the atom, e.g. Hydrogen."""
        return self._name

    @name.setter
    def name(self, name: str) -> None:

        self._name = name

    @property
    def symbol(self) -> str:
        """The chemical symbol of the atom. Must be in the atoms database."""
        return self._symbol

    @symbol.setter
    def symbol(self, symbol: str) -> None:
        if symbol not in ATOMS_DATABASE:
            raise UnknownAtomError('The atom {} is unknown'.format(symbol))

        self._symbol = symbol

    def serialize(self, h5_contents: dict) -> tuple[str, int]:

        atom_str = 'H5Atom(self._h5_file,h5_contents,symbol="{}", name="{}", ghost={})'.format(self.symbol, self.name,
                                                                                               self.ghost)

        h5_contents.setdefault('atoms', []).append(atom_str)

        return 'atoms', len(h5_contents['atoms']) - 1


class AtomGroup(_ChemicalEntity):
    """A selection of atoms that belong to the same chemical system."""

    def __init__(self, atoms: list):
        super(AtomGroup, self).__init__()

        s = set([at.root_chemical_system() for at in atoms])
        if len(s) != 1:
            raise ChemicalEntityError('The atoms comes from different chemical systems')

        self._atoms = atoms

        self._chemical_system = list(s)[0]

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict = state

    def atom_list(self):
        return list([at for at in self._atoms if not at.ghost])

    def copy(self):
        pass

    def number_of_atoms(self):
        return len([at for at in self._atoms if not at.ghost])

    def root_chemical_system(self):
        return self._chemical_system

    def serialize(self, h5_file):
        pass


class AtomCluster(_ChemicalEntity):
    """A cluster of atoms."""

    def __init__(self, name: str, atoms: list[Atom], parentless=False):

        super(AtomCluster, self).__init__()

        self._name = name

        self._parentless = parentless

        self._atoms = collections.OrderedDict()
        for at in atoms:
            if not parentless:
                at._parent = self

            name = at.name
            i = 1
            while name in self._atoms.keys():
                name = ''.join([at.name, i])
                i += 1
            self._atoms[name] = at

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state

    def __getitem__(self, item: str) -> Atom:

        return self._atoms[item]

    def atom_list(self) -> list[Atom]:
        """A list of atoms in the cluster which are not ghosts."""
        return list([at for at in self._atoms.values() if not at.ghost])

    def copy(self) -> 'AtomCluster':
        """Copies the instance of AtomCluster into a new, identical instance."""
        atoms = [atom.copy() for atom in self._atoms.values()]

        ac = AtomCluster(self._name, atoms, self._parentless)

        for at in ac._atoms:  # TODO: Are you actually sure that we want to ignore parentless here?
            at._parent = ac

        return ac

    def number_of_atoms(self) -> int:
        """The number of non-ghost atoms in the cluster."""
        return len([at for at in self._atoms.values() if not at.ghost])

    def total_number_of_atoms(self) -> int:
        """The total number of atoms in the cluster, including ghosts."""
        return len(self._atoms)

    def reorder_atoms(self, atoms: list[Atom]) -> None:

        if set(atoms) != set([at.name for at in self._atoms.values()]):
            raise InconsistentAtomNamesError('The set of atoms to reorder is inconsistent with molecular contents')

        reordered_atoms = collections.OrderedDict()
        for at in atoms:
            reordered_atoms[at] = self._atoms[at]

        self._atoms = reordered_atoms

    def serialize(self, h5_contents: dict) -> tuple[str, int]:

        if 'atoms' in h5_contents:
            at_indexes = list(range(len(h5_contents['atoms']), len(h5_contents['atoms']) + len(self._atoms)))
        else:
            at_indexes = list(range(len(self._atoms)))

        ac_str = 'H5AtomCluster(self._h5_file,h5_contents,{},name="{}")'.format(at_indexes, self._name)

        h5_contents.setdefault('atom_clusters', []).append(ac_str)

        for at in self._atoms:
            at.serialize(h5_contents)

        return ('atom_clusters', len(h5_contents['atom_clusters']) - 1)


class Molecule(_ChemicalEntity):
    """A group of atoms that form a molecule."""

    def __init__(self, code: str, name: str):

        super(Molecule, self).__init__()

        self._atoms = collections.OrderedDict()

        self._code = code

        self._name = name

        self._build(code)

    def _build(self, code: str) -> None:

        for molname, molinfo in MOLECULES_DATABASE.items():
            if code == molname or code in molinfo['alternatives']:
                for at, atinfo in molinfo['atoms'].items():
                    info = copy.deepcopy(atinfo)
                    atom = Atom(name=at, **info)
                    atom.parent = self
                    self._atoms[at] = atom

                self._set_bonds()
                break
        else:
            raise UnknownMoleculeError(code)

    def __getitem__(self, item: str) -> Atom:
        return self._atoms[item]

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state

    def __repr__(self):
        contents = ''
        for key, value in self.__dict__.items():
            key = key[1:] if key[0] == "_" else key
            if isinstance(value, _ChemicalEntity) and not isinstance(value, Atom):
                class_name = str(type(value)).replace('<class \'', '').replace('\'>', '')
                contents += f'{key}={class_name}({value.name})'
            else:
                contents += f'{key}={repr(value)}'
            contents += ', '

        return f'MDANSE.MolecularDynamics.ChemicalEntity.Molecule({contents[:-2]})'

    def _set_bonds(self) -> None:

        for atom in self._atoms.values():
            for i in range(len(atom.bonds)):
                try:
                    atom.bonds[i] = self._atoms[atom.bonds[i]]
                except KeyError:
                    continue

    def atom_list(self) -> list[Atom]:
        """The list of non-ghost atoms in the molecule."""
        return list([at for at in self._atoms.values() if not at.ghost])

    @property
    def code(self) -> str:
        """The code corresponding to the name of the molecule, e.g. WAT for water."""
        return self._code

    def copy(self) -> 'Molecule':
        """Copies the instance of Molecule into a new, identical instance."""

        m = Molecule(self._code, self._name)

        atom_names = [at for at in self._atoms]

        m.reorder_atoms(atom_names)

        for atname, at in m._atoms.items():
            at._parent = m
            at._index = self._atoms[atname].index

        return m

    def number_of_atoms(self) -> int:
        """The number of non-ghost atoms in the molecule."""
        return len([at for at in self._atoms.values() if not at.ghost])

    def total_number_of_atoms(self) -> int:
        """The total number of atoms in the molecule, including ghosts."""
        return len(self._atoms)

    def reorder_atoms(self, atoms: list[str]) -> None:
        """
        Change the order in which the atoms in this molecule are stored.

        :param atoms: A list of atoms. The atoms in the Molecule will be reordered to be in the same order as provided.
        :type atoms: list of strings
        """

        if set(atoms) != set(self._atoms.keys()):
            raise InconsistentAtomNamesError('The set of atoms to reorder is inconsistent with molecular contents')

        reordered_atoms = collections.OrderedDict()
        for at in atoms:
            reordered_atoms[at] = self._atoms[at]

        self._atoms = reordered_atoms

    def serialize(self, h5_contents: dict) -> tuple[str, int]:

        if 'atoms' in h5_contents:
            at_indexes = list(range(len(h5_contents['atoms']), len(h5_contents['atoms']) + len(self._atoms)))
        else:
            at_indexes = list(range(len(self._atoms)))

        mol_str = 'H5Molecule(self._h5_file,h5_contents,{},code="{}",name="{}")'.format(at_indexes, self._code,
                                                                                        self._name)

        h5_contents.setdefault('molecules', []).append(mol_str)

        for at in self._atoms.values():
            at.serialize(h5_contents)

        return 'molecules', len(h5_contents['molecules']) - 1


def is_molecule(name: str) -> bool:
    """
    Checks if a given molecule is in the molecules database.

    :param name: A code or an alternative code (e.g. 'WAT' for water) corresponding to a molecule
    :type name: str

    :return: Whether the provided molecule is in MOLECULES_DATABASE
    :rtype: bool
    """
    return name in MOLECULES_DATABASE


class Residue(_ChemicalEntity):
    """A group of atoms that make up an amino acid."""

    def __init__(self, code: str, name: str, variant: str = None):
        """

        :param code: A code corresponding to a residue in the residue database.
        :type code: str

        :param name: A name for the residue.
        :type name: str

        :param variant:
        :type variant: str
        """

        super(Residue, self).__init__()

        for resname, resinfo in RESIDUES_DATABASE.items():

            if code == resname or code in resinfo['alternatives']:
                break
        else:
            raise UnknownResidueError(code)

        self._code = code

        self._name = name

        self._variant = variant

        if self._variant is not None:
            try:
                self._selected_variant = RESIDUES_DATABASE[self._variant]
            except (KeyError, ResiduesDatabaseError):
                raise InvalidVariantError('The variant {} is unknown'.format(self._variant))
            else:
                if not self._selected_variant['is_n_terminus'] and not self._selected_variant['is_c_terminus']:
                    raise InvalidVariantError('The variant {} is not valid'.format(self._variant))
        else:
            self._selected_variant = None

        self._atoms = collections.OrderedDict()

    def __getitem__(self, item: str) -> Atom:
        return self._atoms[item]

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state

    def __repr__(self):
        contents = ''
        for key, value in self.__dict__.items():
            key = key[1:] if key[0] == "_" else key
            if isinstance(value, _ChemicalEntity) and not isinstance(value, Atom):
                class_name = str(type(value)).replace('<class \'', '').replace('\'>', '')
                contents += f'{key}={class_name}({value.name})'
            else:
                contents += f'{key}={repr(value)}'
            contents += ', '

        return f'MDANSE.MolecularDynamics.ChemicalEntity.Residue({contents[:-2]})'

    def set_atoms(self, atoms: list[str]) -> None:
        """
        Populates the Residue with the provided atoms using the data from RESIDUES_DATABASE. The input must correspond
        to the data in RESIDUES_DATABSE for this residue.

        :param atoms: A list of atoms to populate the residue with
        :type atom: list of strings

        :return: None
        """

        replaced_atoms = set()
        if self._selected_variant is not None:
            for v in self._selected_variant['atoms'].values():
                replaced_atoms.update(v['replaces'])

        res_atoms = set(RESIDUES_DATABASE[self._code]['atoms'])
        res_atoms.difference_update(replaced_atoms)
        if self._selected_variant is not None:
            res_atoms.update(self._selected_variant['atoms'])

        if res_atoms != set(atoms):
            raise InconsistentAtomNamesError('The set of atoms to reorder is inconsistent with residue contents')

        d = copy.deepcopy(RESIDUES_DATABASE[self._code]['atoms'])
        if self._selected_variant is not None:
            d.update(self._selected_variant['atoms'])

        self._atoms.clear()
        for at in atoms:
            self._atoms[at] = Atom(name=at, **d[at])
            self._atoms[at].parent = self

        for at, atom in self._atoms.items():

            for i in range(len(atom.bonds) - 1, -1, -1):
                if atom.bonds[i] in replaced_atoms:
                    del atom.bonds[i]

                try:
                    atom.bonds[i] = self._atoms[atom.bonds[i]]
                except KeyError:
                    continue

    def atom_list(self) -> list[Atom]:
        """List of atoms in the Residue."""
        return list([at for at in self._atoms.values() if not at.ghost])

    def number_of_atoms(self) -> int:
        """The number of non-ghost atoms in the residue."""
        return len([at for at in self._atoms.values() if not at.ghost])

    def total_number_of_atoms(self) -> int:
        """The total number of atoms in the molecule, including ghosts."""
        return len(self._atoms)

    @property
    def code(self) -> str:
        return self._code

    def copy(self) -> 'Residue':
        """Copies the instance of Residue into a new, identical instance."""
        r = Residue(self._code, self._name, self._variant)
        atoms = [at for at in self._atoms]
        r.set_atoms(atoms)

        for atname, at in r._atoms.items():
            at._parent = r
            at._index = self._atoms[atname]._index

        return r

    @property
    def variant(self):
        return self._variant

    def serialize(self, h5_contents: dict) -> tuple[str, int]:

        if 'atoms' in h5_contents:
            at_indexes = list(range(len(h5_contents['atoms']), len(h5_contents['atoms']) + len(self._atoms)))
        else:
            at_indexes = list(range(len(self._atoms)))

        res_str = 'H5Residue(self._h5_file,h5_contents,{},code="{}",name="{}",variant={})'.format(at_indexes,
                                                                                                  self._code,
                                                                                                  self._name,
                                                                                                  repr(self._variant))

        h5_contents.setdefault('residues', []).append(res_str)

        for at in self._atoms.values():
            at.serialize(h5_contents)

        return 'residues', len(h5_contents['residues']) - 1


class Nucleotide(_ChemicalEntity):
    """A group of atoms that make up a nucleotide."""

    def __init__(self, code: str, name: str, variant: str = None):
        """
        :param code: A code corresponding to a nucleotide in the nucleotide database.
        :type code: str

        :param name: A name for the residue.
        :type name: str

        :param variant:
        :type variant: str
        """
        super(Nucleotide, self).__init__()

        for resname, resinfo in NUCLEOTIDES_DATABASE.items():

            if code == resname or code in resinfo['alternatives']:
                self._resname = resname
                break
        else:
            raise UnknownResidueError(code)

        self._code = code

        self._name = name

        self._variant = variant

        if self._variant is not None:
            try:
                self._selected_variant = NUCLEOTIDES_DATABASE[self._variant]
            except (KeyError, NucleotidesDatabaseError):
                raise InvalidVariantError('The variant {} is unknown'.format(self._variant))
            else:
                if not self._selected_variant['is_5ter_terminus'] and not self._selected_variant['is_3ter_terminus']:
                    raise InvalidVariantError('The variant {} is not valid'.format(self._variant))
        else:
            self._selected_variant = None

        self._atoms = collections.OrderedDict()

    def __getitem__(self, item: str) -> Atom:
        return self._atoms[item]

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state

    def __repr__(self):
        contents = ''
        for key, value in self.__dict__.items():
            key = key[1:] if key[0] == "_" else key
            if isinstance(value, _ChemicalEntity) and not isinstance(value, Atom):
                class_name = str(type(value)).replace('<class \'', '').replace('\'>', '')
                contents += f'{key}={class_name}(name={value.name})'
            else:
                contents += f'{key}={repr(value)}'
            contents += ', '

        return f'MDANSE.MolecularDynamics.ChemicalEntity.Nucleotide({contents[:-2]})'

    def copy(self) -> 'Nucleotide':
        """Copies the instance of Nucleotide into a new, identical instance."""
        n = Nucleotide(self._code, self._name, self._variant)
        atoms = [at for at in self._atoms]
        n.set_atoms(atoms)

        for atname, at in n._atoms.items():
            at._parent = n
            at._index = self._atoms[atname].index

        return n

    def set_atoms(self, atoms: list[str]) -> None:
        """
        Populates the Nucleotide with the provided atoms using the data from NUCLEOTIDES_DATABASE. The input must
        correspond to the data in NUCLEOTIDES_DATABASE for this nucleotide.

        :param atoms: A list of atoms to populate the nucleotide with
        :type atom: list of strings

        :return: None
        """
        replaced_atoms = set()
        if self._selected_variant is not None:
            for v in self._selected_variant['atoms'].values():
                replaced_atoms.update(v['replaces'])

        res_atoms = set(NUCLEOTIDES_DATABASE[self._resname]['atoms'])
        res_atoms.difference_update(replaced_atoms)
        if self._selected_variant is not None:
            res_atoms.update(self._selected_variant['atoms'])

        if res_atoms != set(atoms):
            difference = res_atoms.difference(set(atoms)) if len(res_atoms) > len(atoms) else \
                set(atoms).difference(res_atoms)
            raise InconsistentAtomNamesError('The set of atoms to reorder is inconsistent with residue contents.\n'
                                             f'Expected: {res_atoms}\nActual: {set(atoms)}\nDifference: {difference}')

        d = copy.deepcopy(NUCLEOTIDES_DATABASE[self._resname]['atoms'])
        if self._selected_variant is not None:
            d.update(self._selected_variant['atoms'])

        self._atoms.clear()
        for at in atoms:
            self._atoms[at] = Atom(name=at, **d[at])
            self._atoms[at].parent = self

        for at, atom in self._atoms.items():

            for i in range(len(atom.bonds) - 1, -1, -1):
                if atom.bonds[i] in replaced_atoms:
                    del atom.bonds[i]
                    continue
                else:
                    try:
                        atom.bonds[i] = self._atoms[atom.bonds[i]]
                    except KeyError:
                        continue

    def atom_list(self) -> list[Atom]:
        """List of all non-ghost atoms in the Nucleotide."""
        return list([at for at in self._atoms.values() if not at.ghost])

    def number_of_atoms(self) -> int:
        """The number of non-ghost atoms in the residue."""
        return len([at for at in self._atoms.values() if not at.ghost])

    def total_number_of_atoms(self):
        """The total number of atoms in the molecule, including ghosts."""
        return len(self._atoms)

    @property
    def code(self):
        return self._code

    @property
    def variant(self):
        return self._variant

    def serialize(self, h5_contents: dict) -> tuple[str, int]:

        if 'atoms' in h5_contents:
            at_indexes = list(range(len(h5_contents['atoms']), len(h5_contents['atoms']) + len(self._atoms)))
        else:
            at_indexes = list(range(len(self._atoms)))

        res_str = 'H5Nucleotide(self._h5_file,h5_contents,{},code="{}",name="{}",variant={})'.format(at_indexes,
                                                                                                     self._code,
                                                                                                     self._name,
                                                                                                     repr(
                                                                                                         self._variant))

        h5_contents.setdefault('nucleotides', []).append(res_str)

        for at in self._atoms.values():
            at.serialize(h5_contents)

        return 'nucleotides', len(h5_contents['nucleotides']) - 1


class NucleotideChain(_ChemicalEntity):
    """A group of Nucleotide objects connected by bonds in a chain."""

    def __init__(self, name: str):
        """

        :param name: A name for the chain.
        :type name: str
        """

        super(NucleotideChain, self).__init__()

        self._name = name

        self._nucleotides = []

    def __getitem__(self, item: int):
        return self._nucleotides[item]

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state

    def __str__(self):
        return 'NucleotideChain of {} nucleotides'.format(len(self._nucleotides))

    def __repr__(self):
        contents = ''
        for key, value in self.__dict__.items():
            key = key[1:] if key[0] == "_" else key
            if isinstance(value, _ChemicalEntity) and not isinstance(value, Nucleotide):
                class_name = str(type(value)).replace('<class \'', '').replace('\'>', '')
                contents += f'{key}={class_name}(name={value.name})'
            else:
                contents += f'{key}={repr(value)}'
            contents += ', '

        return f'MDANSE.MolecularDynamics.ChemicalEntity.NucleotideChain({contents[:-2]})'

    def _connect_nucleotides(self):

        ratoms_in_first_residue = [at for at in self._nucleotides[0].atom_list() if
                                   getattr(at, 'o5prime_connected', False)]
        if len(ratoms_in_first_residue) == 0:
            raise InvalidNucleotideChainError('The first nucleotide in the chain must contain an atom that is connected'
                                              ' to the 5\' terminal oxygen (O5\'). This is signified by an atom having'
                                              'the "o5prime_connected" property set to True, and happens automatically'
                                              'if the nucleotide was created with variant="5T1", and the set_atoms()'
                                              ' method was called with the correct atoms.\nThe provided first '
                                              f'nucleotide is {self._nucleotides[0].name}, its variant is '
                                              f'{self._nucleotides[0].variant} and it contains the following atoms: '
                                              f'{[at.name for at in self._nucleotides[0].atom_list()]}. The full info'
                                              f' on the first nucleotide is {repr(self._nucleotides[0])}.')

        try:
            n_atom_in_first_residue = self._nucleotides[0]["O5'"]
        except KeyError:
            raise InvalidNucleotideChainError('The first nucleotide in the chain must contain 5\' terminal oxygen atom'
                                              ' (O5\'). The first nucleotide that was provided is '
                                              f'{self._nucleotides[0].name} and contains only the following atoms: '
                                              f'{[at.name for at in self._nucleotides[0].atom_list()]}.\nThe full info'
                                              f' on the first nucleotide is {repr(self._nucleotides[0])}.')
        n_atom_in_first_residue.bonds.extend(ratoms_in_first_residue)

        ratoms_in_last_residue = [at for at in self._nucleotides[-1].atom_list() if
                                  getattr(at, 'o3prime_connected', False)]
        if len(ratoms_in_last_residue) == 0:
            raise InvalidNucleotideChainError('The last nucleotide in the chain must contain an atom that is connected'
                                              ' to the 3\' terminal oxygen (O3\'). This is signified by an atom having'
                                              'the "o3prime_connected" property set to True, and happens automatically'
                                              'if the nucleotide was created with variant="3T1", and the set_atoms()'
                                              ' method was called with the correct atoms.\nThe provided first '
                                              f'nucleotide is {self._nucleotides[-1].name}, its variant is '
                                              f'{self._nucleotides[0].variant} and it contains the following atoms: '
                                              f'{[at.name for at in self._nucleotides[-1].atom_list()]}. The full info'
                                              f' on the first nucleotide is {repr(self._nucleotides[-1])}.')
        try:
            c_atom_in_last_residue = self._nucleotides[-1]["O3'"]
        except KeyError:
            raise InvalidNucleotideChainError('The last nucleotide in the chain must contain 3\' terminal oxygen atom'
                                              ' (O3\'). The first nucleotide that was provided is '
                                              f'{self._nucleotides[0].name} and contains only the following atoms: '
                                              f'{[at.name for at in self._nucleotides[0].atom_list()]}.\nThe full info'
                                              f' on the first nucleotide is {repr(self._nucleotides[0])}.')
        idx = c_atom_in_last_residue.bonds.index('+R')
        del c_atom_in_last_residue.bonds[idx]
        c_atom_in_last_residue.bonds.extend(ratoms_in_last_residue)

        for i, current_residue in enumerate(self._nucleotides[:-1]):
            next_residue = self._nucleotides[i + 1]

            for atom in current_residue.atom_list():
                if '+R' in atom.bonds:
                    current_idx = atom.bonds.index('+R')
                    current_atom = atom
                    break
            else:
                raise InvalidResidueError(f'The provided nucleotide with index {i}, {current_residue.name}, is invalid '
                                          f'because it does not contain an atom bonded to "R+", i.e. another nucleo'
                                          f'tide.\nThe full info on this nucleotide is {repr(current_residue)}')

            for atom in next_residue.atom_list():
                if '-R' in atom.bonds:
                    next_idx = atom.bonds.index('-R')
                    next_atom = atom
                    break
            else:
                raise InvalidResidueError(
                    f'The provided nucleotide with index {i + 1}, {next_residue.name}, is invalid '
                    f'because it does not contain an atom bonded to "R+", i.e. another nucleo'
                    f'tide.\nThe full info on this nucleotide is {repr(next_residue)}')

            current_atom.bonds[current_idx] = next_atom
            next_atom.bonds[next_idx] = current_atom

    def atom_list(self) -> list[Atom]:
        """List of all non-ghost atoms in all the nucleotides in the chain."""
        atoms = []
        for res in self._nucleotides:
            atoms.extend(res.atom_list())
        return atoms

    @property
    def bases(self) -> list[Atom]:
        """A list of atoms that are part of a nucleotide base."""
        atoms = []
        for at in self.atom_list():
            if 'base' in at.groups:
                atoms.append(at)
        return atoms

    def copy(self) -> 'NucleotideChain':
        """Copies the instance of NucleotideChain into a new, identical instance."""
        nc = NucleotideChain(self._name)

        nucleotides = [nucl.copy() for nucl in self._nucleotides]

        nc._nucleotides = nucleotides

        for nucl in nc._nucleotides:
            nucl._parent = nc

        nc._connect_nucleotides()

        return nc

    @property
    def residues(self) -> list[Nucleotide]:
        """List of nucleotides in the chain."""
        return self._nucleotides

    def number_of_atoms(self) -> int:
        """Number of non-ghost atoms in the nucleotide chain."""
        number_of_atoms = 0
        for nucleotide in self._nucleotides:
            number_of_atoms += nucleotide.number_of_atoms()
        return number_of_atoms

    def total_number_of_atoms(self) -> int:
        """Total number of atoms in the nucleotide chain, including ghost atoms."""
        number_of_atoms = 0
        for nucleotide in self._nucleotides:
            number_of_atoms += nucleotide.total_number_of_atoms()
        return number_of_atoms

    def serialize(self, h5_contents: dict) -> tuple[str, int]:

        if 'nucleotides' in h5_contents:
            res_indexes = list(
                range(len(h5_contents['nucleotides']), len(h5_contents['nucleotides']) + len(self._nucleotides)))
        else:
            res_indexes = list(range(len(self._nucleotides)))

        pc_str = 'H5NucleotideChain(self._h5_file,h5_contents,"{}",{})'.format(self._name, res_indexes)

        for nucl in self._nucleotides:
            nucl.serialize(h5_contents)

        h5_contents.setdefault('nucleotide_chains', []).append(pc_str)

        return 'nucleotide_chains', len(h5_contents['nucleotide_chains']) - 1

    def set_nucleotides(self, nucleotides: list[Nucleotide]) -> None:
        """
        Sets the provided Nucleotide objects as the nucleotides making up this chain, and creates bonds between them.
        They are connected in the order that they are passed in to this method, so the first nucleotide must the 5'
        terminus and the last one must be the 3' terminus.

        :param nucleotides: A list of nucleotides that will make up this chain.
        :type nucleotides: list

        :return: None
        """
        self._nucleotides = []
        for nucleotide in nucleotides:
            nucleotide.parent = self
            self._nucleotides.append(nucleotide)

        self._connect_nucleotides()

    @property
    def sugars(self) -> list[Atom]:
        """A list of atoms in the nucleotide chain that are a part of the sugar part of a nucleotide."""
        atoms = []
        for at in self.atom_list():
            if 'sugar' in at.groups:
                atoms.append(at)
        return atoms


class PeptideChain(_ChemicalEntity):
    """A peptide chain composed of bonded amino acid residues."""

    def __init__(self, name: str):
        """
        The PeptideChain is instantiated empty. To set its component Residues, the set_residues() method must be called.

        :param name: The name of this PeptideChain
        :type name: str
        """

        super(PeptideChain, self).__init__()

        self._name = name

        self._residues = []

    def _connect_residues(self) -> None:
        # Process the first atom
        ratoms_in_first_residue = [at for at in self._residues[0].atom_list() if getattr(at, 'nter_connected', False)]
        if not ratoms_in_first_residue:
            raise InvalidPeptideChainError('The first residue in the chain must contain an atom that is connected to '
                                           'the terminal nitrogen. This is signified by an atom having the '
                                           '"nter_connected" property set to True, and happens automatically if the '
                                           'residue was created with variant="NT1", and the set_atoms() method was '
                                           'called with the correct atoms.\nThe provided first residue is '
                                           f'{self._residues[0].name}, its variant is {self._residues[0].variant} and '
                                           f'it contains the following atoms: '
                                           f'{[at.name for at in self._residues[0].atom_list()]}. The full info on the '
                                           f'first residue is {repr(self._residues[0])}.')
        try:
            n_atom_in_first_residue = self._residues[0]['N']
        except KeyError:
            raise InvalidPeptideChainError('The first residue in the chain must contain the terminal nitrogen atom. '
                                           f'However, the first residue that was provided is {self._residues[0].name} '
                                           f'and contains only the following atoms: '
                                           f'{[at.name for at in self._residues[0].atom_list()]}.\nThe full info'
                                           f' on the first nucleotide is {repr(self._residues[0])}.')
        idx = n_atom_in_first_residue.bonds.index('-R')
        del n_atom_in_first_residue.bonds[idx]
        n_atom_in_first_residue.bonds.extend(ratoms_in_first_residue)

        # Process the last atom
        ratoms_in_last_residue = [at for at in self._residues[-1].atom_list() if getattr(at, 'cter_connected', False)]
        if not ratoms_in_last_residue:
            raise InvalidPeptideChainError('The last residue in the chain must contain an atom that is connected to '
                                           'the terminal carbon. This is signified by an atom having the '
                                           '"cter_connected" property set to True, and happens automatically if the '
                                           'residue was created with variant="CT1", and the set_atoms() method was '
                                           'called with the correct atoms.\nThe provided last residue is '
                                           f'{self._residues[-1].name}, its variant is {self._residues[-1].variant} and'
                                           f' it contains the following atoms: '
                                           f'{[at.name for at in self._residues[-1].atom_list()]}. The full info on the'
                                           f' last residue is {repr(self._residues[-1])}.')
        try:
            c_atom_in_last_residue = self._residues[-1]['C']
        except KeyError:
            raise InvalidPeptideChainError('The last residue in the chain must contain the terminal carbon atom. '
                                           f'However, the last residue that was provided is {self._residues[-1].name} '
                                           f'and contains only the following atoms: '
                                           f'{[at.name for at in self._residues[-1].atom_list()]}.\nThe full info'
                                           f' on the last nucleotide is {repr(self._residues[-1])}.')
        idx = c_atom_in_last_residue.bonds.index('+R')
        del c_atom_in_last_residue.bonds[idx]
        c_atom_in_last_residue.bonds.extend(ratoms_in_last_residue)

        # Create bonds
        for i, current_residue in enumerate(self._residues[:-1]):
            next_residue = self._residues[i + 1]

            for atom in current_residue.atom_list():
                if '+R' in atom.bonds:
                    current_atom = atom
                    current_index = atom.bonds.index('+R')
                    break
            else:
                raise InvalidResidueError(f'The provided residue with index {i}, {current_residue.name}, is invalid '
                                          f'because it does not contain an atom bonded to "R+", i.e. another residue.'
                                          f'\nThe full info on this residue is {repr(current_residue)}')

            for atom in next_residue.atom_list():
                if '-R' in atom.bonds:
                    next_atom = atom
                    next_index = atom.bonds.index('-R')
                    break
            else:
                raise InvalidResidueError(f'The provided residue with index {i+1}, {next_residue.name}, is invalid '
                                          f'because it does not contain an atom bonded to "R+", i.e. another residue.'
                                          f'\nThe full info on this residue is {repr(next_residue)}')

            current_atom.bonds[current_index] = next_atom
            next_atom.bonds[next_index] = current_atom

    def __getitem__(self, item: int):
        return self._residues[item]

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state

    def __str__(self):
        return 'PeptideChain of {} residues'.format(len(self._residues))

    def __repr__(self):
        contents = ''
        for key, value in self.__dict__.items():
            key = key[1:] if key[0] == "_" else key
            if isinstance(value, _ChemicalEntity) and not isinstance(value, Residue):
                class_name = str(type(value)).replace('<class \'', '').replace('\'>', '')
                contents += f'{key}={class_name}(name={value.name})'
            else:
                contents += f'{key}={repr(value)}'
            contents += ', '

        return f'MDANSE.MolecularDynamics.ChemicalEntity.PeptideChain({contents[:-2]})'

    def atom_list(self) -> list[Atom]:
        """A list of all non-ghost atoms in the PeptideChain."""
        atoms = []
        for res in self._residues:
            atoms.extend(res.atom_list())
        return atoms

    def backbone(self) -> list[Atom]:
        """A list of all atoms in the PeptideChain that are a part of the backbone."""
        atoms = []
        for at in self.atom_list():
            if 'backbone' in at.groups:
                atoms.append(at)
        return atoms

    def copy(self) -> 'PeptideChain':
        """Copies the instance of NucleotideChain into a new, identical instance."""
        pc = PeptideChain(self._name)

        residues = [res.copy() for res in self._residues]

        pc._residues = residues

        for res in pc._residues:
            res._parent = pc

        pc._connect_residues()

        return pc

    def number_of_atoms(self) -> int:
        """The number of non-ghost in the PeptideChain."""
        number_of_atoms = 0
        for residue in self._residues:
            number_of_atoms += residue.number_of_atoms()
        return number_of_atoms

    def total_number_of_atoms(self) -> int:
        """The total number of atoms in the PeptideChain, including ghosts."""
        number_of_atoms = 0
        for residue in self._residues:
            number_of_atoms += residue.total_number_of_atoms()
        return number_of_atoms

    @property
    def peptide_chains(self) -> list['PeptideChain']:
        """The list of PeptideChains in this PeptideChain"""
        return [self]

    @property
    def peptides(self) -> list[Atom]:
        """The list of atoms in the PeptideChain that are a part of a peptide."""
        atoms = []
        for at in self.atom_list():
            if 'peptide' in at.groups:
                atoms.append(at)
        return atoms

    @property
    def residues(self) -> list[Residue]:
        """The list of amino acid Residues that make up this PeptideChain."""
        return self._residues

    def serialize(self, h5_contents: dict) -> tuple[str, int]:

        if 'residues' in h5_contents:
            res_indexes = list(range(len(h5_contents['residues']), len(h5_contents['residues']) + len(self._residues)))
        else:
            res_indexes = list(range(len(self._residues)))

        pc_str = 'H5PeptideChain(self._h5_file,h5_contents,"{}",{})'.format(self._name, res_indexes)

        for res in self._residues:
            res.serialize(h5_contents)

        h5_contents.setdefault('peptide_chains', []).append(pc_str)

        return 'peptide_chains', len(h5_contents['peptide_chains']) - 1

    def set_residues(self, residues: list[Residue]) -> None:
        """
        Populates the PeptideChain with amino acid Residues.

        :param residues: List of residues that the PeptideChain consists of.
        :type residues: list

        :return: None
        """
        self._residues = []
        for residue in residues:
            residue.parent = self
            self._residues.append(residue)

        self._connect_residues()

    @property
    def sidechains(self):
        atoms = []
        for at in self.atom_list():
            if 'sidechain' in at.groups:
                atoms.append(at)
        return atoms


class Protein(_ChemicalEntity):

    def __init__(self, name=''):

        self._name = name

        self._peptide_chains = []

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state

    def atom_list(self):

        atom_list = []
        for c in self._peptide_chains:
            atom_list.extend(c.atom_list())

        return atom_list

    def backbone(self):

        atoms = []
        for at in self.atom_list():
            if 'backbone' in at.groups:
                atoms.append(at)
        return atoms

    def copy(self):

        p = Protein(self._name)

        peptide_chains = [pc.copy() for pc in self._peptide_chains]

        p._peptide_chains = peptide_chains

        for pc in p._peptide_chains:
            pc._parent = p

        return p

    def number_of_atoms(self):

        number_of_atoms = 0
        for peptide_chain in self._peptide_chains:
            number_of_atoms += peptide_chain.number_of_atoms()
        return number_of_atoms

    def total_number_of_atoms(self):

        number_of_atoms = 0
        for peptide_chain in self._peptide_chains:
            number_of_atoms += peptide_chain.total_number_of_atoms()
        return number_of_atoms

    def set_peptide_chains(self, peptide_chains):

        self._peptide_chains = peptide_chains
        for pc in self._peptide_chains:
            pc.parent = self

    @property
    def peptide_chains(self):
        return self._peptide_chains

    @property
    def peptides(self):
        atoms = []
        for at in self.atom_list():
            if 'peptide' in at.groups:
                atoms.append(at)
        return atoms

    @property
    def residues(self):

        residues = []
        for pc in self._peptide_chains:
            residues.extend(pc.residues)

        return residues

    def serialize(self, h5_file, h5_contents):
        if 'peptide_chains' in h5_contents:
            pc_indexes = list(
                range(len(h5_contents['pepide_chains']), len(h5_contents['pepide_chains']) + len(self._peptide_chains)))
        else:
            pc_indexes = list(range(len(self._peptide_chains)))

        prot_str = 'H5Protein(self._h5_file,h5_contents,"{}",{})'.format(self._name, pc_indexes)

        h5_contents.setdefault('proteins', []).append(prot_str)

        for pc in self._peptide_chains:
            pc.serialize(h5_file, h5_contents)

        return ('proteins', len(h5_contents['proteins']) - 1)

    @property
    def sidechains(self):
        atoms = []
        for at in self.atom_list():
            if 'sidechain' in at.groups:
                atoms.append(at)
        return atoms


def translate_atom_names(database, molname, atoms):
    if not molname in database:
        raise UnknownMoleculeError('The molecule {} is unknown'.format(molname))

    renamed_atoms = []
    for atom in atoms:
        for dbat, dbinfo in database[molname]['atoms'].items():
            if dbat == atom or atom in dbinfo['alternatives']:
                renamed_atoms.append(dbat)
                break
        else:
            raise UnknownAtomError('The atom {} is unknown'.format(atom))

    return renamed_atoms


class ChemicalSystem(_ChemicalEntity):

    def __init__(self, name=''):

        super(ChemicalSystem, self).__init__()

        self._chemical_entities = []

        self._configuration = None

        self._number_of_atoms = 0

        self._total_number_of_atoms = 0

        self._name = name

        self._atoms = None

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state

    def add_chemical_entity(self, chemical_entity):

        if not isinstance(chemical_entity, _ChemicalEntity):
            raise InvalidChemicalEntityError('Invalid type')

        for at in chemical_entity.atom_list():
            if not at.ghost:
                at.index = self._number_of_atoms
                self._number_of_atoms += 1

            self._total_number_of_atoms += 1

        chemical_entity.parent = self

        self._chemical_entities.append(chemical_entity)

        self._configuration = None

        self._atoms = None

    def atom_list(self):

        atom_list = []
        for ce in self._chemical_entities:
            atom_list.extend(ce.atom_list())

        return atom_list

    @property
    def atoms(self):

        from MDANSE.MolecularDynamics.TrajectoryUtils import sorted_atoms

        if self._atoms is None:
            self._atoms = sorted_atoms(self.atom_list())

        return self._atoms

    @property
    def chemical_entities(self):
        return self._chemical_entities

    @property
    def configuration(self):
        return self._configuration

    @configuration.setter
    def configuration(self, configuration):

        if configuration.chemical_system != self:
            raise InconsistentChemicalSystemError('Mismatch between chemical systems')

        self._configuration = configuration

    def copy(self):

        cs = ChemicalSystem(self._name)

        cs._parent = self._parent

        cs._chemical_entities = [ce.copy() for ce in self._chemical_entities]

        cs._number_of_atoms = self._number_of_atoms

        cs._total_number_of_atoms = self._total_number_of_atoms

        for ce in cs._chemical_entities:
            ce._parent = cs

        if self._configuration is not None:
            conf = self._configuration.clone(cs)

            cs._configuration = conf

        return cs

    def load(self, h5_filename):

        from MDANSE.Chemistry.H5ChemicalEntity import H5Atom, H5AtomCluster, H5Molecule, H5Nucleotide, \
            H5NucleotideChain, H5Residue, H5PeptideChain, H5Protein

        self._h5_file = h5py.File(h5_filename, 'r', libver='latest')
        grp = self._h5_file['/chemical_system']
        self._chemical_entities = []

        skeleton = self._h5_file['/chemical_system/contents'][:]

        self._name = grp.attrs['name']

        h5_contents = {}
        for k in grp.keys():
            if k == 'contents':
                continue
            h5_contents[k] = grp[k][:]

        for entity_type, entity_index in skeleton:
            entity_index = int(entity_index)
            h5_chemical_entity_instance = eval(h5_contents[entity_type.decode('utf-8')][entity_index])
            ce = h5_chemical_entity_instance.build()
            self.add_chemical_entity(ce)

        self._h5_file.close()

        self._h5_file = None

    def number_of_atoms(self):

        return self._number_of_atoms

    def total_number_of_atoms(self):

        return self._total_number_of_atoms

    def serialize(self, h5_file):

        string_dt = h5py.special_dtype(vlen=str)

        grp = h5_file.create_group('/chemical_system')

        grp.attrs['name'] = self._name

        h5_contents = {}

        contents = []
        for ce in self._chemical_entities:
            entity_type, entity_index = ce.serialize(h5_file, h5_contents)
            contents.append((entity_type, str(entity_index)))

        for k, v in h5_contents.items():
            grp.create_dataset(k, data=v, dtype=string_dt)
        grp.create_dataset('contents', data=contents, dtype=string_dt)
