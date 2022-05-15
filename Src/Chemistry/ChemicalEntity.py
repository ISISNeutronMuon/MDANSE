import abc
import collections
import copy

import h5py

from MDANSE.Chemistry import ATOMS_DATABASE, MOLECULES_DATABASE, NUCLEOTIDES_DATABASE, RESIDUES_DATABASE

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

class _ChemicalEntity:

    __metaclass__ = abc.ABCMeta

    def __init__(self):

        self._parent = None

        self._name = ''
    
    @abc.abstractmethod
    def atom_list(self):
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

    def root_chemical_system(self):

        if self._parent is None:
            return self
        else:
            return self._parent.top_level_chemical_entity()

    def top_level_chemical_entity(self):

        if isinstance(self._parent,ChemicalSystem):
            return self
        else:
            return self._parent.top_level_chemical_entity()

class Atom(_ChemicalEntity):

    def __init__(self, **kwargs):

        super(Atom,self).__init__()

        self.symbol = kwargs.get('symbol','H')

        if self.symbol not in ATOMS_DATABASE:
            raise UnknownAtomError('The atom {} is unknown'.format(self.symbol))

        self._name = kwargs.pop('name',self.symbol)

        self._bonds = kwargs.pop('bonds',[])

        self.groups = kwargs.pop('groups',[])

        self.ghost = kwargs.pop('ghost',False)

        self.position = None

        for k,v in kwargs.items():
            setattr(self,k,v)

        self._index = None

        self._true_index = None

        for propName,propValue in ATOMS_DATABASE[self.symbol].items():
            setattr(self,propName,propValue)

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
    def index(self):
        return self._index

    @index.setter
    def index(self, index):
        if self._index is not None:
            return
        self._index = index

    @property
    def bonds(self):
        return self._bonds

    @property
    def true_index(self):
        return self._true_index

    @true_index.setter
    def true_index(self, true_index):
        if self._true_index is not None:
            return
        self._true_index = true_index

    def serialize(self,h5_file, h5_contents):

        atom_str = 'H5Atom(self._h5_file,h5_contents,symbol="{}", name="{}", ghost={})'.format(self.symbol,self.name,self.ghost)

        h5_contents.setdefault('atoms',[]).append(atom_str)

        return ('atoms',len(h5_contents['atoms'])-1)

class AtomCluster(_ChemicalEntity):

    def __init__(self, name, atoms):

        super(AtomCluster,self).__init__()

        self._name = name

        self._atoms = []
        for at in atoms:
            at.parent = self
            self._atoms.append(at)

    def __getitem__(self,item):

        return self._atoms[item]

    def atom_list(self):
        return list([at for at in self._atoms if not at.ghost])

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
                break
        else:
            raise UnknownMoleculeError(code)

        for at, atinfo in molinfo['atoms'].items():

            info = copy.deepcopy(atinfo)
            atom = Atom(name=at,**info)
            atom.parent = self
            self._atoms[at] = atom

        self._set_bonds()

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

        self._chemical_entities = []

        self._configuration = None

        self._number_of_atoms = 0

        self._total_number_of_atoms = 0

        self._name = name

        self._parent = None

    def add_chemical_entity(self, chemical_entity):

        if not isinstance(chemical_entity,_ChemicalEntity):
            raise InvalidChemicalEntityError('invalid chemical entity')

        for at in chemical_entity.atom_list():
            if not at.ghost:
                at.index = self._number_of_atoms
                self._number_of_atoms += 1

            at.true_index = self._total_number_of_atoms
            self._total_number_of_atoms += 1

        self._chemical_entities.append(chemical_entity)

        chemical_entity.parent = self

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

        for comp, at in enumerate(self.atom_list()):
            at.position = self._configuration['coordinates'][comp,:]

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
            self.add_chemical_entity(h5_chemical_entity_instance.build())
        
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

