import abc
import collections
import copy

import h5py

from Databases import ATOMS, MOLECULES, NUCLEOTIDES, RESIDUES

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
    
    @abc.abstractmethod
    def atom_list(self):
        pass

    @abc.abstractmethod
    def number_of_atoms(self):
        pass

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self,parent):
        self._parent = parent

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

class Atom(_ChemicalEntity):

    def __init__(self, **kwargs):

        super(Atom,self).__init__()

        self.symbol = kwargs.get('symbol','H')

        self.name = kwargs.get('name',self.symbol)

        self.bonds = kwargs.get('bonds',[])

        self.groups = kwargs.get('groups',[])

        self._index = None

    def __getitem__(self,item):

        return getattr(self,item)

    def atom_list(self):
        return [self]

    def number_of_atoms(self):
        return 1

    def full_name(self):

        full_name = self.name
        parent = self._parent
        while parent is not None:
            full_name = '{}.{}'.format(parent.name,full_name)
            parent = parent.parent
            
        return full_name

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, index):
        self._index = index

    def serialize(self,h5_file, h5_contents):

        atom_str = 'H5Atom(self._h5_file,h5_contents,symbol="{}", name="{}")'.format(self.symbol,self.name)

        h5_contents.setdefault('atoms',[]).append(atom_str)

        return ('atoms',len(h5_contents['atoms'])-1)

class AtomCluster(_ChemicalEntity):

    def __init__(self, code, atoms, number=None):

        super(AtomCluster,self).__init__()

        self._atoms = collections.OrderedDict()

        self._code = code

        self._number = number

        self._build(code,atoms,number)

    def _build(self, code, atoms, number = None):

        if number is not None:
            self._name = '{}{}'.format(self._code,self._number)
        else:
            self._name = code

        for at in atoms:
            at.parent = self
            self._atoms[at.name] = at

    def __getitem__(self,item):
        return self._atoms[item]

    def atom_list(self):
        return list(self._atoms.values())

    @property
    def code(self):
        return self._code

    @property
    def name(self):
        return self._name

    @property
    def number(self):
        return self._number

    def number_of_atoms(self):
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

        ac_str = 'H5AtomCluster(self._h5_file,h5_contents,{},code="{}",number={})'.format(at_indexes,self._code,self._number)

        h5_contents.setdefault('atom_clusters',[]).append(ac_str)
        
        for at in self._atoms.values():
            at.serialize(h5_file,h5_contents)

        return ('atom_clusters',len(h5_contents['atom_clusters'])-1)

class Molecule(_ChemicalEntity):
    
    def __init__(self, code, number=None):

        super(Molecule,self).__init__()

        self._atoms = collections.OrderedDict()

        self._code = code

        self._number = number

        self._molname = None

        self._build(code,number)

    def _build(self, code, number = None):

        for molname, molinfo in MOLECULES.items():

            if code == molname or code in molinfo['alternatives']:
                break
        else:
            raise UnknownMoleculeError(code)

        self._molname = molname

        if number is not None:
            self._name = '{}{}'.format(self._molname,number)
        else:
            self._name = code

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
        return list(self._atoms.values())

    @property
    def code(self):
        return self._code

    @property
    def molname(self):
        return self._molname

    @property
    def name(self):
        return self._name

    @property
    def number(self):
        return self._number

    def number_of_atoms(self):
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

        mol_str = 'H5Molecule(self._h5_file,h5_contents,{},code="{}",number={})'.format(at_indexes,self._code,self._number)

        h5_contents.setdefault('molecules',[]).append(mol_str)
        
        for at in self._atoms.values():
            at.serialize(h5_file,h5_contents)

        return ('molecules',len(h5_contents['molecules'])-1)

def is_molecule(molname):

    return molname in MOLECULES

class Residue(_ChemicalEntity):
    
    def __init__(self, code, number=None, variant=None):

        super(Residue,self).__init__()

        self._atoms = collections.OrderedDict()

        self._resname = None

        self._code = code

        self._number = number

        self._variant = variant

        self._build(code,number)

    def __getitem__(self,item):
        return self._atoms[item]

    def _build(self, code, number):

        for resname, resinfo in RESIDUES.items():

            if code == resname or code in resinfo['alternatives']:
                break
        else:
            raise UnknownResidueError(code)

        self._resname = resname

        if number is not None:
            self._name = '{}{}'.format(self._resname,number)
        else:
            self._name = code

        if self._variant is not None:
            try:
                self._selected_variant = RESIDUES[self._variant]
            except KeyError:
                raise InvalidVariantError('The variant {} is unknown'.format(self._variant))
            else:
                if not self._selected_variant['is_n_terminus'] and not self._selected_variant['is_c_terminus']:
                    raise InvalidVariantError('The variant {} is not valid'.format(self._variant))
        else:
            self._selected_variant = None

        atoms = list(resinfo['atoms'].items())
        if self._selected_variant is not None:
            atoms = list(self._selected_variant['atoms'].items()) + atoms

        for at,atinfo in atoms:

            if self._selected_variant is not None and self._selected_variant['is_n_terminus']:
                if at == 'H':
                    continue

            info = copy.deepcopy(atinfo)
            atom = Atom(name=at,**info)
            atom.parent = self
            self._atoms[at] = atom

        self._set_bonds()

    def reorder_atoms(self, atoms):
        if set(atoms) != set(self._atoms.keys()):
            raise InconsistentAtomNamesError('The set of atoms to reorder is inconsistent with residue contents')

        reordered_atoms = collections.OrderedDict()
        for at in atoms:
            reordered_atoms[at] = self._atoms[at]
        
        self._atoms = reordered_atoms

    def _set_bonds(self):

        for at, atom in self._atoms.items():

            if self._selected_variant is not None and self._selected_variant['is_n_terminus']:
                if at == 'N':
                    h_idx = atom.bonds.index('H')
                    del atom.bonds[h_idx]

            for i in range(len(atom.bonds)):
                try:
                    atom.bonds[i] = self._atoms[atom.bonds[i]]
                except KeyError:
                    continue

    def atom_list(self):
        return list(self._atoms.values())

    def number_of_atoms(self):
        return len(self._atoms)

    @property
    def code(self):
        return self._code

    @property
    def name(self):
        return self._name

    @property
    def number(self):
        return self._number

    @property
    def resname(self):
        return self._resname

    def serialize(self,h5_file, h5_contents):

        if 'atoms' in h5_contents:
            at_indexes = list(range(len(h5_contents['atoms']),len(h5_contents['atoms'])+len(self._atoms)))
        else:
            at_indexes = list(range(len(self._atoms)))

        res_str = 'H5Residue(self._h5_file,h5_contents,{},code="{}",number={},variant={})'.format(at_indexes,self._code,self._number,repr(self._variant))

        h5_contents.setdefault('residues',[]).append(res_str)
        
        for at in self._atoms.values():
            at.serialize(h5_file,h5_contents)

        return ('residues',len(h5_contents['residues'])-1)

class Nucleotide(_ChemicalEntity):
    
    def __init__(self, code, number=None, variant=None):

        super(Nucleotide,self).__init__()

        self._atoms = collections.OrderedDict()

        self._nuclname = None

        self._code = code

        self._number = number

        self._variant = variant

        self._build(code,number)

    def _build(self, code, number):

        for nuclname, nuclinfo in NUCLEOTIDES.items():

            if code == nuclname or code in nuclinfo['alternatives']:
                break
        else:
            raise UnknownResidueError(code)

        self._nuclname = nuclname

        if number is not None:
            self._name = '{}{}'.format(self._nuclname,number)
        else:
            self._name = code

        if self._variant is not None:
            try:
                self._selected_variant = NUCLEOTIDES[self._variant]
            except KeyError:
                raise InvalidVariantError('The variant {} is unknown'.format(self._variant))
            else:
                if not self._selected_variant['is_5ter_terminus'] and not self._selected_variant['is_3ter_terminus']:
                    raise InvalidVariantError('The variant {} is not valid'.format(self._variant))
        else:
            self._selected_variant = None

        atoms = list(nuclinfo['atoms'].items())
        if self._selected_variant is not None:
            atoms = list(self._selected_variant['atoms'].items()) + atoms

        for at,atinfo in atoms:

            if self._selected_variant is not None and self._selected_variant['is_5ter_terminus']:
                if at in ['OP1','OP2','P']:
                    continue

            info = copy.deepcopy(atinfo)

            atom = Atom(name=at,**info)
            atom.parent = self
            self._atoms[at] = atom

        self._set_bonds()

    def __getitem__(self,item):
        return self._atoms[item]

    def _set_bonds(self):

        if self._selected_variant is not None and self._selected_variant['is_5ter_terminus']:
            idx = self._atoms["O5'"].bonds.index('P')
            self._atoms["O5'"].bonds[idx] = '-R'

        for atom in self._atoms.values():
            
            bonds = []
            for i in range(len(atom.bonds)):
                bat = atom.bonds[i]
                if self._selected_variant is not None and self._selected_variant['is_5ter_terminus']:
                    if bat in ['OP1','OP2','P']:
                        continue
                if bat in self._atoms:
                    bonds.append(self._atoms[bat])
                else:
                    bonds.append(bat)
            atom.bonds = bonds

    def reorder_atoms(self, atoms):
        if set(atoms) != set(self._atoms.keys()):
            raise InconsistentAtomNamesError('The set of atoms to reorder is inconsistent with residue contents')

        reordered_atoms = collections.OrderedDict()
        for at in atoms:
            reordered_atoms[at] = self._atoms[at]
        
        self._atoms = reordered_atoms

    def atom_list(self):
        return list(self._atoms.values())

    def number_of_atoms(self):
        return len(self._atoms)

    @property
    def code(self):
        return self._code

    @property
    def name(self):
        return self._name

    @property
    def number(self):
        return self._number

    @property
    def nuclname(self):
        return self._nuclname

    def serialize(self, h5_file, h5_contents):

        if 'atoms' in h5_contents:
            at_indexes = list(range(len(h5_contents['atoms']),len(h5_contents['atoms'])+len(self._atoms)))
        else:
            at_indexes = list(range(len(self._atoms)))

        res_str = 'H5Nucleotide(self._h5_file,h5_contents,{},code="{}",number={},variant={})'.format(at_indexes,self._code,self._number,repr(self._variant))

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
                
        ratom_in_first_residue = [at for at in self._nucleotides[0].atom_list() if '+OR' in at.bonds][0]
        o5prime_atom_in_first_residue = self._nucleotides[0]["O5'"]

        idx = ratom_in_first_residue.bonds.index('+OR')
        ratom_in_first_residue.bonds[idx] = o5prime_atom_in_first_residue
        idx = o5prime_atom_in_first_residue.bonds.index('-R')
        del o5prime_atom_in_first_residue.bonds[idx]
        o5prime_atom_in_first_residue.bonds.append(ratom_in_first_residue)

        ho3prime_in_last_residue = self._nucleotides[-1]["HO3'"]
        o3prime_atom_in_last_residue = self._nucleotides[-1]["O3'"]
        idx = ho3prime_in_last_residue.bonds.index('-OR')
        ho3prime_in_last_residue.bonds[idx] = o3prime_atom_in_last_residue
        idx = o3prime_atom_in_last_residue.bonds.index('+R')
        del o3prime_atom_in_last_residue.bonds[idx]
        o3prime_atom_in_last_residue.bonds.append(ho3prime_in_last_residue)

        for i in range(len(self._nucleotides)-1):
            current_residue = self._nucleotides[i]
            next_residue = self._nucleotides[i+1]

            ratom_in_current_residue = [at for at in current_residue.atom_list() if '+R' in at.bonds][0]
            ratom_in_next_residue = [at for at in next_residue.atom_list() if '-R' in at.bonds][0]
            # print(ratom_in_current_residue.name,ratom_in_next_residue.name)

            idx = ratom_in_current_residue.bonds.index('+R')
            ratom_in_current_residue.bonds[idx] = ratom_in_next_residue

            idx = ratom_in_next_residue.bonds.index('-R')
            ratom_in_next_residue.bonds[idx] = ratom_in_current_residue

    def atom_list(self):

        atoms = []
        for res in self._nucleotides:
            atoms.extend(res.atom_list())
        return atoms

    @property
    def name(self):
        return self._name

    @property
    def nucleotides(self):

        return self._nucleotides

    def number_of_atoms(self):

        number_of_atoms = 0
        for nucleotide in self._nucleotides:
            number_of_atoms += nucleotide.number_of_atoms()
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

class PeptideChain(_ChemicalEntity):

    def __init__(self, name):

        super(PeptideChain,self).__init__()

        self._name = name

        self._residues = []

    def _connect_residues(self):
                
        ratoms_in_first_residue = [at for at in self._residues[0].atom_list() if '+NR' in at.bonds]
        n_atom_in_first_residue = self._residues[0]['N']
        for at in ratoms_in_first_residue:
            idx = at.bonds.index('+NR')
            at.bonds[idx] = n_atom_in_first_residue
        idx = n_atom_in_first_residue.bonds.index('-R')
        del n_atom_in_first_residue.bonds[idx]
        n_atom_in_first_residue.bonds.extend(ratoms_in_first_residue)

        ratoms_in_last_residue = [at for at in self._residues[-1].atom_list() if '-CR' in at.bonds]
        c_atom_in_last_residue = self._residues[-1]['C']
        for at in ratoms_in_last_residue:
            idx = at.bonds.index('-CR')
            at.bonds[idx] = c_atom_in_last_residue
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

    def number_of_atoms(self):

        number_of_atoms = 0
        for residue in self._residues:
            number_of_atoms += residue.number_of_atoms()
        return number_of_atoms

    @property
    def name(self):
        return self._name

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

class Protein(_ChemicalEntity):

    def __init__(self, name=''):

        self._name = name

        self._peptide_chains = []

    def atom_list(self):

        atom_list = []
        for c in self._peptide_chains:
            atom_list.extend(c.atom_list())

        return atom_list

    def number_of_atoms(self):

        number_of_atoms = 0
        for peptide_chain in self._peptide_chains:
            number_of_atoms += peptide_chain.number_of_atoms()
        return number_of_atoms

    def set_peptide_chains(self, peptide_chains):

        self._peptide_chains = peptide_chains

    @property
    def name(self):
        return self._name

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

class ChemicalSystem(_ChemicalEntity):

    def __init__(self):

        self._chemical_entities = []

        self._unit_cell = None

        self._configuration = None

        self._number_of_atoms = 0

    def add_chemical_entity(self, chemical_entity):

        if not isinstance(chemical_entity,_ChemicalEntity):
            raise InvalidChemicalEntityError('invalid chemical entity')

        for at in chemical_entity.atom_list():
            at.index = self._number_of_atoms
            self._number_of_atoms += 1

        self._chemical_entities.append(chemical_entity)

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

    def load(self, h5_filename):

        from H5ChemicalEntity import H5Atom, H5AtomCluster, H5Molecule, H5Nucleotide, H5NucleotideChain, H5Residue, H5PeptideChain, H5Protein

        self._h5_file = h5py.File(h5_filename,'r',libver='latest')
        grp = self._h5_file['/chemical_system']
        self._chemical_entities = []
        skeleton = self._h5_file['/chemical_system/contents'][:]

        h5_contents = {}
        for k in grp.keys():
            if k =='contents':
                continue
            h5_contents[k] = grp[k][:]

        for entity_type, entity_index in skeleton:
            entity_index = int(entity_index)
            h5_chemical_entity_instance = eval(grp[entity_type][entity_index])
            self._chemical_entities.append(h5_chemical_entity_instance.build())
        self._h5_file.close()

    def number_of_atoms(self):

        return self._number_of_atoms

    def serialize(self, h5_filename):

        string_dt = h5py.special_dtype(vlen=str)

        h5_file = h5py.File(h5_filename, mode='w')

        grp = h5_file.create_group('/chemical_system')

        h5_contents = {}

        contents = []
        for ce in self._chemical_entities:
            entity_type, entity_index = ce.serialize(h5_file, h5_contents)
            contents.append((entity_type,str(entity_index)))

        for k,v in h5_contents.items():
            grp.create_dataset(k,data=v,dtype=string_dt)
        grp.create_dataset('contents', data=contents, dtype=string_dt)

        h5_file.close()
