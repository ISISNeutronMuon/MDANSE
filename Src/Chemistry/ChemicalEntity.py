import abc
import collections
import copy

import numpy as np

import h5py

from MDANSE.Chemistry import ATOMS_DATABASE, MOLECULES_DATABASE, NUCLEOTIDES_DATABASE, RESIDUES_DATABASE
from MDANSE.Mathematics.Transformation import Transformation

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

class InvalidChemicalEntityError(Exception):
    pass

class InconsistentChemicalSystemError(Exception):
    pass

class ChemicalEntityError(Exception):
    pass

class _ChemicalEntity:

    __metaclass__ = abc.ABCMeta

    def __init__(self):

        self._parent = None

        self._name = ''
    
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
            full_name = '{}.{}'.format(parent.name,full_name)
            parent = parent.parent
            
        return full_name

    @abc.abstractmethod
    def number_of_atoms(self):
        pass

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self,parent):
        self._parent = parent

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self,name):
        self._name = name

    @abc.abstractmethod
    def serialize(self, h5_file):
        pass

    def group(self, name):

        selected_atoms = []
        for at in self.atom_list():
            if not hasattr(at,'groups'):
                continue

            if name in at.groups:
                selected_atoms.append(at)

        return selected_atoms

    def center_of_mass(self, configuration):

        coords = configuration['coordinates']

        com = np.zeros((3,),dtype=np.float)
        sum_masses = 0.0
        for at in self.atom_list():
            m = ATOMS_DATABASE[at.symbol]['atomic_weight']
            com += m*coords[at.index,:]
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

    def find_transformation_as_quaternion(self, conf1, conf2 = None):

        from MDANSE.Mathematics.Geometry import superposition_fit
        from MDANSE.Mathematics.LinearAlgebra import Vector

        chemical_system = self.root_chemical_system()

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
                Vector(*conf1['coordinates'][a.index,:]),
                Vector(*conf2['coordinates'][a.index,:])) for a in self.atom_list()])

    def find_transformation(self, conf1, conf2 = None):
        """
        :param conf1: a configuration object
        :type conf1: :class:`~MMTK.ParticleProperties.Configuration`
        :param conf2: a configuration object, or None for the
                      current configuration
        :type conf2: :class:`~MMTK.ParticleProperties.Configuration` or NoneType
        :returns: the linear transformation that, when applied to
                  the object in configuration conf1, minimizes the
                  RMS distance to the conformation in conf2, and the
                  minimal RMS distance.
                  If conf2 is None, returns the transformation from the
                  current configuration to conf1 and the associated
                  RMS distance.
        """

        from MDANSE.Mathematics.Transformation import Translation
        
        q, cm1, cm2, rms = self.find_transformation_as_quaternion(conf1, conf2)
        return Translation(cm2) * q.asRotation() * Translation(-cm1), rms

    def center_and_moment_of_inertia(self, configuration):
        """
        :param conf: a configuration object, or None for the
                     current configuration
        :type conf: :class:`~MMTK.ParticleProperties.Configuration` or NoneType
        :returns: the center of mass and the moment of inertia tensor
                  in the given configuration
        """
        
        from MDANSE.Mathematics.LinearAlgebra import delta, Tensor, Vector

        m = 0.0
        mr = Vector(0.0,0.0,0.0)
        t = Tensor(3*[3*[0.0]])
        for atom in self.atom_list():
            ma = ATOMS_DATABASE[atom.symbol]['atomic_weight']
            r = Vector(configuration['coordinates'][atom.index,:])
            m += ma
            mr += ma*r
            t += ma*r.dyadic_product(r)
        cm = mr/m
        t -= m*cm.dyadic_product(cm)
        t = t.trace()*delta - t
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

        from MDANSE.Mathematics.Transformation import Rotation, Translation

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
        return Rotation(diag)*Translation(-cm)

    def root_chemical_system(self):

        if isinstance(self,ChemicalSystem):
            return self
        else:
            return self._parent.root_chemical_system()

    def top_level_chemical_entity(self):

        if isinstance(self._parent,ChemicalSystem):
            return self
        else:
            return self._parent.top_level_chemical_entity()

class Atom(_ChemicalEntity):

    def __init__(self, **kwargs):

        super(Atom,self).__init__()

        self._symbol = kwargs.get('symbol','H')

        if self._symbol not in ATOMS_DATABASE:
            raise UnknownAtomError('The atom {} is unknown'.format(self.symbol))

        self._name = kwargs.pop('name',self.symbol)

        self._bonds = kwargs.pop('bonds',[])

        self._groups = kwargs.pop('groups',[])

        self._ghost = kwargs.pop('ghost',False)

        self._index = None

        self._parent = None

        for k,v in kwargs.items():
            setattr(self,k,v)

    def copy(self):

        a = Atom(symbol=self._symbol)

        for k, v in self.__dict__.items():
            setattr(a,k,v)

        a._bonds = [bat.copy() for bat in self._bonds]

        return a

    def __getitem__(self,item):

        return getattr(self,item)

    def __str__(self):
        
        return self.full_name()

    def atom_list(self):
        return [self] if not self.ghost else []

    def total_number_of_atoms(self):
        return 1

    def number_of_atoms(self):
        return int(self.ghost)

    @property
    def bonds(self):

        return self._bonds

    @bonds.setter
    def ghost(self, bonds):

        self._bonds = bonds

    @property
    def ghost(self):

        return self._ghost

    @ghost.setter
    def ghost(self, ghost):

        self._ghost = ghost

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, index):
        if self._index is not None:
            return
        self._index = index

    @property
    def name(self):

        return self._name

    @name.setter
    def name(self, name):

        self._name = name

    @property
    def bonds(self):
        return self._bonds

    @property
    def symbol(self):

        return self._symbol

    @symbol.setter
    def symbol(self, symbol):

        self._symbol = symbol

    def serialize(self, h5_file, h5_contents):

        atom_str = 'H5Atom(self._h5_file,h5_contents,symbol="{}", name="{}", ghost={})'.format(self.symbol,self.name,self.ghost)

        h5_contents.setdefault('atoms',[]).append(atom_str)

        return ('atoms',len(h5_contents['atoms'])-1)

class AtomGroup(_ChemicalEntity):

    def __init__(self, atoms):

        super(AtomGroup,self).__init__()

        s = set([at.root_chemical_system() for at in atoms])
        if len(s) != 1:
            raise ChemicalEntityError('The atoms comes from different chemical systems')

        self._atoms = atoms

        self._chemical_system = list(s)[0]

    def atom_list(self):
        return list([at for at in self._atoms if not at.ghost])

    def copy(self):
        pass

    def number_of_atoms(self):
        return len([at for at in self._atoms if not at.ghost])

    def root_chemical_system(self):

        return self._chemical_system

    def serialize(self):
        pass

class AtomCluster(_ChemicalEntity):

    def __init__(self, name, atoms, parentless=False):

        super(AtomCluster,self).__init__()

        self._name = name

        self._atoms = []
        for at in atoms:
            if not parentless:
                at._parent = self
            self._atoms.append(at)

    def __getitem__(self,item):

        return self._atoms[item]

    def atom_list(self):
        return list([at for at in self._atoms if not at.ghost])

    def copy(self):

        atoms = [atom.copy() for atom in self._atoms]

        ac = AtomCluster(self._name,atoms,self._parentless)

        for at in ac._atoms:
            at._parent = ac

        return ac

    def number_of_atoms(self):
        return len([at for at in self._atoms if not at.ghost])

    def total_number_of_atoms(self):
        return len(self._atoms)

    def reorder_atoms(self, atoms):

        if set(atoms) != set([at.name for at in self._atoms]):
            raise InconsistentAtomNamesError('The set of atoms to reorder is inconsistent with molecular contents')

        reordered_atoms = []
        for at in atoms:
            reordered_atoms[at] = self._atoms[at]
        
        self._atoms = reordered_atoms

    def serialize(self,h5_file, h5_contents):

        if 'atoms' in h5_contents:
            at_indexes = list(range(len(h5_contents['atoms']),len(h5_contents['atoms'])+len(self._atoms)))
        else:
            at_indexes = list(range(len(self._atoms)))

        ac_str = 'H5AtomCluster(self._h5_file,h5_contents,{},name="{}")'.format(at_indexes,self._name)

        h5_contents.setdefault('atom_clusters',[]).append(ac_str)
        
        for at in self._atoms:
            at.serialize(h5_file,h5_contents)

        return ('atom_clusters',len(h5_contents['atom_clusters'])-1)

class Molecule(_ChemicalEntity):
    
    def __init__(self, code, name):

        super(Molecule,self).__init__()

        self._atoms = collections.OrderedDict()

        self._code = code

        self._name = name

        self._build(code)

    def _build(self, code):

        for molname, molinfo in MOLECULES_DATABASE.items():
            if code == molname or code in molinfo['alternatives']:
                for at, atinfo in molinfo['atoms'].items():
                    info = copy.deepcopy(atinfo)
                    atom = Atom(name=at,**info)
                    atom.parent = self
                    self._atoms[at] = atom

                self._set_bonds()
                break
        else:
            raise UnknownMoleculeError(code)

    def __getitem__(self,item):
        return self._atoms[item]

    def _set_bonds(self):

        for atom in self._atoms.values():
            for i in range(len(atom.bonds)):
                try:
                    atom.bonds[i] = self._atoms[atom.bonds[i]]
                except KeyError:
                    continue

    def atom_list(self):
        return list([at for at in self._atoms.values() if not at.ghost])

    @property
    def code(self):
        return self._code

    def copy(self):

        m = Molecule(self._code, self._name)

        atom_names = [at for at in self._atoms]
        
        m.reorder_atoms(atom_names)

        for atname, at in m._atoms.items():
            at._parent = m
            at._index = self._atoms[atname]._index

        return m

    def number_of_atoms(self):
        return len([at for at in self._atoms.values() if not at.ghost])

    def total_number_of_atoms(self):
        return len(self._atoms)

    def reorder_atoms(self, atoms):

        if set(atoms) != set(self._atoms.keys()):
            raise InconsistentAtomNamesError('The set of atoms to reorder is inconsistent with molecular contents')

        reordered_atoms = collections.OrderedDict()
        for at in atoms:
            reordered_atoms[at] = self._atoms[at]
        
        self._atoms = reordered_atoms

    def serialize(self,h5_file, h5_contents):

        if 'atoms' in h5_contents:
            at_indexes = list(range(len(h5_contents['atoms']),len(h5_contents['atoms'])+len(self._atoms)))
        else:
            at_indexes = list(range(len(self._atoms)))

        mol_str = 'H5Molecule(self._h5_file,h5_contents,{},code="{}",name="{}")'.format(at_indexes,self._code,self._name)

        h5_contents.setdefault('molecules',[]).append(mol_str)
        
        for at in self._atoms.values():
            at.serialize(h5_file,h5_contents)

        return ('molecules',len(h5_contents['molecules'])-1)

def is_molecule(name):

    return name in MOLECULES_DATABASE

class Residue(_ChemicalEntity):
    
    def __init__(self, code, name, variant=None):

        super(Residue,self).__init__()

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
            except KeyError:
                raise InvalidVariantError('The variant {} is unknown'.format(self._variant))
            else:
                if not self._selected_variant['is_n_terminus'] and not self._selected_variant['is_c_terminus']:
                    raise InvalidVariantError('The variant {} is not valid'.format(self._variant))
        else:
            self._selected_variant = None

        self._atoms = collections.OrderedDict()

    def __getitem__(self,item):
        return self._atoms[item]

    def set_atoms(self, atoms):

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
            self._atoms[at] = Atom(name=at,**d[at])
            self._atoms[at].parent = self
        
        for at, atom in self._atoms.items():

            for i in range(len(atom.bonds)-1,-1,-1):
                if atom.bonds[i] in replaced_atoms:
                    del atom.bonds[i]

                try:
                    atom.bonds[i] = self._atoms[atom.bonds[i]]
                except KeyError:
                    continue

    def atom_list(self):
        return list([at for at in self._atoms.values() if not at.ghost])

    def number_of_atoms(self):
        return len([at for at in self._atoms.values() if not at.ghost])

    def total_number_of_atoms(self):
        return len(self._atoms)

    @property
    def code(self):
        return self._code

    def copy(self):

        r  = Residue(self._code, self._name, self._variant)
        atoms = [at for at in self._atoms]
        r.set_atoms(atoms)

        for atname, at in r._atoms.items():
            at._parent = r
            at._index = self._atoms[atname]._index

        return r

    def serialize(self,h5_file, h5_contents):

        if 'atoms' in h5_contents:
            at_indexes = list(range(len(h5_contents['atoms']),len(h5_contents['atoms'])+len(self._atoms)))
        else:
            at_indexes = list(range(len(self._atoms)))

        res_str = 'H5Residue(self._h5_file,h5_contents,{},code="{}",name="{}",variant={})'.format(at_indexes,self._code,self._name,repr(self._variant))

        h5_contents.setdefault('residues',[]).append(res_str)
        
        for at in self._atoms.values():
            at.serialize(h5_file,h5_contents)

        return ('residues',len(h5_contents['residues'])-1)

class Nucleotide(_ChemicalEntity):
    
    def __init__(self, code, name, variant=None):

        super(Nucleotide,self).__init__()

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
            except KeyError:
                raise InvalidVariantError('The variant {} is unknown'.format(self._variant))
            else:
                if not self._selected_variant['is_5ter_terminus'] and not self._selected_variant['is_3ter_terminus']:
                    raise InvalidVariantError('The variant {} is not valid'.format(self._variant))
        else:
            self._selected_variant = None

        self._atoms = collections.OrderedDict()

    def __getitem__(self,item):
        return self._atoms[item]

    def copy(self):

        n  = Nucleotide(self._code, self._name, self._variant)
        atoms = [at for at in self._atoms]
        n.set_atoms(atoms)

        for atname, at in n._atoms.items():
            at._parent = n
            at._index = self._atoms[atname]._index

        return n

    def set_atoms(self, atoms):

        replaced_atoms = set()
        if self._selected_variant is not None:
            for v in self._selected_variant['atoms'].values():
                replaced_atoms.update(v['replaces'])

        res_atoms = set(NUCLEOTIDES_DATABASE[self._resname]['atoms'])
        res_atoms.difference_update(replaced_atoms)
        if self._selected_variant is not None:
            res_atoms.update(self._selected_variant['atoms'])

        if res_atoms != set(atoms):
            raise InconsistentAtomNamesError('The set of atoms to reorder is inconsistent with residue contents')

        d = copy.deepcopy(NUCLEOTIDES_DATABASE[self._resname]['atoms'])
        if self._selected_variant is not None:
            d.update(self._selected_variant['atoms'])

        self._atoms.clear()
        for at in atoms:
            self._atoms[at] = Atom(name=at,**d[at])
            self._atoms[at].parent = self
        
        for at, atom in self._atoms.items():

            for i in range(len(atom.bonds)-1,-1,-1):
                if atom.bonds[i] in replaced_atoms:
                    del atom.bonds[i]
                    continue
                else:
                    try:
                        atom.bonds[i] = self._atoms[atom.bonds[i]]
                    except KeyError:
                        continue

    def atom_list(self):
        return list([at for at in self._atoms.values() if not at.ghost])

    def number_of_atoms(self):
        return len([at for at in self._atoms.values() if not at.ghost])

    def total_number_of_atoms(self):
        return len(self._atoms)

    @property
    def code(self):
        return self._code

    def serialize(self, h5_file, h5_contents):

        if 'atoms' in h5_contents:
            at_indexes = list(range(len(h5_contents['atoms']),len(h5_contents['atoms'])+len(self._atoms)))
        else:
            at_indexes = list(range(len(self._atoms)))

        res_str = 'H5Nucleotide(self._h5_file,h5_contents,{},code="{}",name="{}",variant={})'.format(at_indexes,self._code,self._name,repr(self._variant))

        h5_contents.setdefault('nucleotides',[]).append(res_str)
        
        for at in self._atoms.values():
            at.serialize(h5_file,h5_contents)

        return ('nucleotides',len(h5_contents['nucleotides'])-1)

class NucleotideChain(_ChemicalEntity):

    def __init__(self, name):

        super(NucleotideChain,self).__init__()

        self._name = name

        self._nucleotides = []

    def __getitem__(self, item):
        return self._nucleotides[item]

    def __str__(self):
        return 'NucleotideChain of {} nucleotides'.format(len(self._nucleotides))

    def _connect_nucleotides(self):
                
        ratoms_in_first_residue = [at for at in self._nucleotides[0].atom_list() if getattr(at,'o5prime_connected',False)]
        n_atom_in_first_residue = self._nucleotides[0]["O5'"]
        n_atom_in_first_residue.bonds.extend(ratoms_in_first_residue)

        ratoms_in_last_residue = [at for at in self._nucleotides[-1].atom_list() if getattr(at,'o3prime_connected',False)]
        c_atom_in_last_residue = self._nucleotides[-1]["O3'"]
        idx = c_atom_in_last_residue.bonds.index('+R')
        del c_atom_in_last_residue.bonds[idx]
        c_atom_in_last_residue.bonds.extend(ratoms_in_last_residue)

        for i in range(len(self._nucleotides)-1):
            current_residue = self._nucleotides[i]
            next_residue = self._nucleotides[i+1]

            ratoms_in_current_residue = [at for at in current_residue.atom_list() if '+R' in at.bonds][0]
            ratoms_in_next_residue = [at for at in next_residue.atom_list() if '-R' in at.bonds][0]

            idx = ratoms_in_current_residue.bonds.index('+R')
            ratoms_in_current_residue.bonds[idx] = ratoms_in_next_residue

            idx = ratoms_in_next_residue.bonds.index('-R')
            ratoms_in_next_residue.bonds[idx] = ratoms_in_current_residue

    def atom_list(self):

        atoms = []
        for res in self._nucleotides:
            atoms.extend(res.atom_list())
        return atoms

    @property
    def bases(self):
        atoms = []
        for at in self.atom_list():
            if 'base' in at.groups:
                atoms.append(at)
        return atoms

    def copy(self):

        nc = NucleotideChain(self._code, self._name)

        nucleotides = [nucl.copy() for nucl in self._nucleotides]

        nc._nucleotides = nucleotides

        for nucl in nc._nucleotides:
            nucl._parent = nc

        nc._connect_residues()

        return nc

    @property
    def nucleotides(self):

        return self._nucleotides

    def number_of_atoms(self):

        number_of_atoms = 0
        for nucleotide in self._nucleotides:
            number_of_atoms += nucleotide.number_of_atoms()
        return number_of_atoms

    def total_number_of_atoms(self):

        number_of_atoms = 0
        for nucleotide in self._nucleotides:
            number_of_atoms += nucleotide.total_number_of_atoms()
        return number_of_atoms

    def serialize(self,h5_file, h5_contents):
        
        if 'nucleotides' in h5_contents:
            res_indexes = list(range(len(h5_contents['nucleotides']),len(h5_contents['nucleotides'])+len(self._nucleotides)))
        else:
            res_indexes = list(range(len(self._nucleotides)))

        pc_str = 'H5NucleotideChain(self._h5_file,h5_contents,"{}",{})'.format(self._name,res_indexes)
        
        for nucl in self._nucleotides:
            nucl.serialize(h5_file,h5_contents)

        h5_contents.setdefault('nucleotide_chains',[]).append(pc_str)

        return ('nucleotide_chains',len(h5_contents['nucleotide_chains'])-1)

    def set_nucleotides(self, nucleotides):

        for nucleotide in nucleotides:
            nucleotide.parent = self
            self._nucleotides.append(nucleotide)

        self._connect_nucleotides()

    @property
    def sugars(self):
        atoms = []
        for at in self.atom_list():
            if 'sugar' in at.groups:
                atoms.append(at)
        return atoms

class PeptideChain(_ChemicalEntity):

    def __init__(self, name):

        super(PeptideChain,self).__init__()

        self._name = name

        self._residues = []

    def _connect_residues(self):
                
        ratoms_in_first_residue = [at for at in self._residues[0].atom_list() if getattr(at,'nter_connected',False)]
        n_atom_in_first_residue = self._residues[0]['N']
        idx = n_atom_in_first_residue.bonds.index('-R')
        del n_atom_in_first_residue.bonds[idx]
        n_atom_in_first_residue.bonds.extend(ratoms_in_first_residue)

        ratoms_in_last_residue = [at for at in self._residues[-1].atom_list() if getattr(at,'cter_connected',False)]
        c_atom_in_last_residue = self._residues[-1]['C']
        idx = c_atom_in_last_residue.bonds.index('+R')
        del c_atom_in_last_residue.bonds[idx]
        c_atom_in_last_residue.bonds.extend(ratoms_in_last_residue)

        for i in range(len(self._residues)-1):
            current_residue = self._residues[i]
            next_residue = self._residues[i+1]

            ratoms_in_current_residue = [at for at in current_residue.atom_list() if '+R' in at.bonds][0]
            ratoms_in_next_residue = [at for at in next_residue.atom_list() if '-R' in at.bonds][0]

            idx = ratoms_in_current_residue.bonds.index('+R')
            ratoms_in_current_residue.bonds[idx] = ratoms_in_next_residue

            idx = ratoms_in_next_residue.bonds.index('-R')
            ratoms_in_next_residue.bonds[idx] = ratoms_in_current_residue

    def __getitem__(self, item):
        return self._residues[item]

    def __str__(self):
        return 'PeptideChain of {} residues'.format(len(self._residues))

    def atom_list(self):

        atoms = []
        for res in self._residues:
            atoms.extend(res.atom_list())
        return atoms

    def backbone(self):

        atoms = []
        for at in self.atom_list():
            if 'backbone' in at.groups:
                atoms.append(at)
        return atoms

    def copy(self):

        pc = PeptideChain(self._name)

        residues = [res.copy() for res in self._residues]

        pc._residues = residues

        for res in pc._residues:
            res._parent = pc

        pc._connect_residues()

        return pc

    def number_of_atoms(self):

        number_of_atoms = 0
        for residue in self._residues:
            number_of_atoms += residue.number_of_atoms()
        return number_of_atoms

    def total_number_of_atoms(self):

        number_of_atoms = 0
        for residue in self._residues:
            number_of_atoms += residue.total_number_of_atoms()
        return number_of_atoms

    @property
    def peptide_chains(self):
        return [self]

    @property
    def peptides(self):
        atoms = []
        for at in self.atom_list():
            if 'peptide' in at.groups:
                atoms.append(at)
        return atoms

    @property
    def residues(self):

        return self._residues

    def serialize(self,h5_file, h5_contents):
        
        if 'residues' in h5_contents:
            res_indexes = list(range(len(h5_contents['residues']),len(h5_contents['residues'])+len(self._residues)))
        else:
            res_indexes = list(range(len(self._residues)))

        pc_str = 'H5PeptideChain(self._h5_file,h5_contents,"{}",{})'.format(self._name,res_indexes)
        
        for res in self._residues:
            res.serialize(h5_file,h5_contents)

        h5_contents.setdefault('peptide_chains',[]).append(pc_str)

        return ('peptide_chains',len(h5_contents['peptide_chains'])-1)

    def set_residues(self, residues):

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

    def serialize(self,h5_file, h5_contents):
        if 'peptide_chains' in h5_contents:
            pc_indexes = list(range(len(h5_contents['pepide_chains']),len(h5_contents['pepide_chains'])+len(self._peptide_chains)))
        else:
            pc_indexes = list(range(len(self._peptide_chains)))

        prot_str = 'H5Protein(self._h5_file,h5_contents,"{}",{})'.format(self._name,pc_indexes)

        h5_contents.setdefault('proteins',[]).append(prot_str)

        for pc in self._peptide_chains:
            pc.serialize(h5_file,h5_contents)

        return ('proteins',len(h5_contents['proteins'])-1)

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

        super(ChemicalSystem,self).__init__()

        self._chemical_entities = []

        self._configuration = None

        self._number_of_atoms = 0

        self._total_number_of_atoms = 0

        self._name = name

    def add_chemical_entity(self, chemical_entity):

        if not isinstance(chemical_entity,_ChemicalEntity):
            raise InvalidChemicalEntityError('Invalid type')

        for at in chemical_entity.atom_list():
            if not at.ghost:
                at.index = self._number_of_atoms
                self._number_of_atoms += 1

            self._total_number_of_atoms += 1

        chemical_entity.parent = self

        self._chemical_entities.append(chemical_entity)

        self._configuration = None

    def atom_list(self):

        atom_list = []
        for ce in self._chemical_entities:
            atom_list.extend(ce.atom_list())

        return atom_list

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

            variables = copy.deepcopy(self._configuration.variables)
            
            conf = self._configuration.__class__(
                cs,
                variables.pop('coordinates'),
                self._configuration.unit_cell,
                **variables)

            cs._configuration = conf

        return cs

    def load(self, h5_filename):

        from MDANSE.Chemistry.H5ChemicalEntity import H5Atom, H5AtomCluster, H5Molecule, H5Nucleotide, H5NucleotideChain, H5Residue, H5PeptideChain, H5Protein

        self._h5_file = h5py.File(h5_filename,'r',libver='latest')
        grp = self._h5_file['/chemical_system']
        self._chemical_entities = []
        skeleton = self._h5_file['/chemical_system/contents'][:]

        self._name = grp.attrs['name']

        h5_contents = {}
        for k in grp.keys():
            if k =='contents':
                continue
            h5_contents[k] = grp[k][:]

        for entity_type, entity_index in skeleton:
            entity_index = int(entity_index)
            h5_chemical_entity_instance = eval(grp[entity_type][entity_index])
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
            contents.append((entity_type,str(entity_index)))

        for k,v in h5_contents.items():
            grp.create_dataset(k,data=v,dtype=string_dt)
        grp.create_dataset('contents', data=contents, dtype=string_dt)

