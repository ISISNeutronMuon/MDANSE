import copy
import string

import numpy as np

from ChemicalEntity import Nucleotide, is_molecule, Atom, AtomCluster, ChemicalSystem, Molecule, Nucleotide, NucleotideChain, Residue, PeptideChain, UnknownAtomError
from Databases import ATOMS, MOLECULES, NUCLEOTIDES, RESIDUES
from PDB import PDBAtom, PDBMolecule, PDBNucleotideChain, PDBPeptideChain, Structure

class UncompleteVariantError(Exception):
    pass

class UnknownNTerminus(Exception):
    pass

class UnknownCTerminus(Exception):
    pass

class PDBReader:

    def __init__(self, filename):

        self._chemicalEntities = []

        self._struct = Structure(filename)
        
        self._build_chemical_entities()

    def _build_chemical_entities(self):

        for pdb_element in self._struct.objects:
            if isinstance(pdb_element,PDBPeptideChain):
                self._chemicalEntities.append(self._process_peptide_chain(pdb_element))

            elif isinstance(pdb_element,PDBNucleotideChain):
                self._chemicalEntities.extend(self._process_nucleotide_chain(pdb_element))

            elif isinstance(pdb_element,PDBMolecule):

                if len(pdb_element) == 1:
                    self._chemicalEntities.append(self._process_atom(pdb_element[0]))
                else:                
                    if is_molecule(pdb_element.name):
                        self._chemicalEntities.append(self._process_molecule(pdb_element))            
                    else:
                        self._chemicalEntities.append(self._process_atom_cluster(pdb_element))            

    def _guess_atom_symbol(self, atom):

        atom_without_digits = ''.join([at for at in atom if at not in string.digits])
        
        comp = 1
        while True:
            if atom_without_digits[:comp] in ATOMS:
                return atom_without_digits[:comp]
            comp += 1
            if comp > len(atom_without_digits):
                raise UnknownAtomError(atom)

    def _process_atom(self, atom):

        atname = atom.name

        atom_found = None
        for at, info in ATOMS.items():
            if at == atname:
                atom_found = Atom(name=at,**info)
            else:
                for alt in info['alternatives']:
                    if alt == atname:
                        copy_info = copy.deepcopy(info)                                            
                        atom_found = Atom(name=at,**copy_info)
                        atom_found.position = atom.position
                        break
                else:
                    continue

        if atom_found is None:
            raise UnknownAtomError('The atom {} is unknown'.format(at))

        return atom_found

    def _process_atom_cluster(self, atom_cluster):

        ac_name = atom_cluster.name

        pdb_atoms = [at.name for at in atom_cluster]

        atoms = []
        for at in pdb_atoms:
            symbol = self._guess_atom_symbol(at)
            atoms.append(Atom(name=at,symbol=symbol))

        new_atom_cluster = AtomCluster(ac_name,atoms,number=atom_cluster.number)

        return new_atom_cluster

    def _process_molecule(self, molecule):

        molname = molecule.name

        pdb_atoms = [at.name for at in molecule]

        atoms_found = [None]*len(pdb_atoms)
        for at, info in MOLECULES[molname]['atoms'].items():

            try:
                idx = pdb_atoms.index(at)
                atoms_found[idx] = at
            except ValueError:
                for alt in info['alternatives']:
                    try:
                        idx = pdb_atoms.index(alt)
                        atoms_found[idx] = at
                    except ValueError:
                        continue
                    else:
                        break
                else:
                    raise UnknownAtomError('The atom {} is unknown'.format(at))

        new_molecule = Molecule(molname,molecule.number)
        new_molecule.reorder_atoms(atoms_found)

        return new_molecule

    def _guess_prot_terminus_type(self, pdb_atoms, nter=True):

        for resname,residue in RESIDUES.items():
            if nter and not residue['is_n_terminus']:
                continue
            if not nter and not residue['is_c_terminus']:
                continue
            atoms_map = {}
            for at,info in residue['atoms'].items():
                alt = [at] + info['alternatives']
                for a in alt:
                    if a in pdb_atoms:
                        atoms_map[a] = at
                        break
                else:
                    break
            else:
                return (resname,atoms_map)
        else:
            raise UnknownNTerminus()

    def _guess_nucl_terminus_type(self, pdb_atoms, ter5=True):

        for nuclname,nucleotide in NUCLEOTIDES.items():
            if ter5 and not nucleotide['is_5ter_terminus']:
                continue
            if not ter5 and not nucleotide['is_3ter_terminus']:
                continue
            atoms_map = {}
            for at,info in nucleotide['atoms'].items():
                alt = [at] + info['alternatives']
                for a in alt:
                    if a in pdb_atoms:
                        atoms_map[a] = at
                        break
                else:
                    break
            else:
                return (nuclname,atoms_map)
        else:
            raise UnknownNTerminus()

    def _process_nter_residue(self, residue):

        resname = residue.name

        pdb_atoms = [at.name for at in residue]

        nter, nter_atoms_map = self._guess_prot_terminus_type(pdb_atoms,nter=True)

        atoms_found = [None]*len(pdb_atoms)
        for at, info in RESIDUES[resname]['atoms'].items():

            if at == 'H':
                continue

            try:
                idx = pdb_atoms.index(at)
                atoms_found[idx] = at
            except ValueError:
                for alt in info['alternatives']:
                    try:
                        idx = pdb_atoms.index(alt)
                        atoms_found[idx] = at
                    except ValueError:
                        continue
                    else:
                        break
                else:
                    raise UnknownAtomError('The atom {} is unknown'.format(at))

        for i in range(len(atoms_found)):
            at = atoms_found[i]
            if at is None:
                try:
                    atoms_found[i] = nter_atoms_map[pdb_atoms[i]]
                except KeyError:
                    raise UnknownAtomError('The atom {} is unknown'.format(at))

        new_residue = Residue(resname,residue.number,variant=nter)
        new_residue.reorder_atoms(atoms_found)

        return new_residue

    def _process_5ter_residue(self, residue):

        nuclname = residue.name

        pdb_atoms = [at.name for at in residue]

        ter, ter_atoms_map = self._guess_nucl_terminus_type(pdb_atoms,ter5=True)

        atoms_found = [None]*len(pdb_atoms)
        for at, info in NUCLEOTIDES[nuclname]['atoms'].items():

            if at in ['OP1','OP2','P']:
                continue

            try:
                idx = pdb_atoms.index(at)
                atoms_found[idx] = at
            except ValueError:
                for alt in info['alternatives']:
                    try:
                        idx = pdb_atoms.index(alt)
                        atoms_found[idx] = at
                    except ValueError:
                        continue
                    else:
                        break
                else:
                    raise UnknownAtomError('The atom {} is unknown'.format(at))

        for i in range(len(atoms_found)):
            at = atoms_found[i]
            if at is None:
                try:
                    atoms_found[i] = ter_atoms_map[pdb_atoms[i]]
                except KeyError:
                    raise UnknownAtomError('The atom {} is unknown'.format(at))

        new_nucleotide = Nucleotide(nuclname,residue.number,variant=ter)
        new_nucleotide.reorder_atoms(atoms_found)

        return new_nucleotide

    def _process_cter_residue(self, residue):

        resname = residue.name

        pdb_atoms = [at.name for at in residue]

        cter, cter_atoms_map = self._guess_prot_terminus_type(pdb_atoms,nter=False)

        atoms_found = [None]*len(pdb_atoms)
        for at, info in RESIDUES[resname]['atoms'].items():

            try:
                idx = pdb_atoms.index(at)
                atoms_found[idx] = at
            except ValueError:
                for alt in info['alternatives']:
                    try:
                        idx = pdb_atoms.index(alt)
                        atoms_found[idx] = at
                    except ValueError:
                        continue
                    else:
                        break
                else:
                    raise UnknownAtomError('The atom {} is unknown'.format(at))

        for i in range(len(atoms_found)):
            at = atoms_found[i]
            if at is None:
                try:
                    atoms_found[i] = cter_atoms_map[pdb_atoms[i]]
                except KeyError:
                    raise UnknownAtomError('The atom {} is unknown'.format(at))

        new_residue = Residue(resname,residue.number,variant=cter)
        new_residue.reorder_atoms(atoms_found)

        return new_residue

    def _process_3ter_residue(self, residue):

        nuclname = residue.name

        pdb_atoms = [at.name for at in residue]

        cter, cter_atoms_map = self._guess_nucl_terminus_type(pdb_atoms,ter5=False)

        atoms_found = [None]*len(pdb_atoms)
        for at, info in NUCLEOTIDES[nuclname]['atoms'].items():

            try:
                idx = pdb_atoms.index(at)
                atoms_found[idx] = at
            except ValueError:
                for alt in info['alternatives']:
                    try:
                        idx = pdb_atoms.index(alt)
                        atoms_found[idx] = at
                    except ValueError:
                        continue
                    else:
                        break
                else:
                    raise UnknownAtomError('The atom {} is unknown'.format(at))

        for i in range(len(atoms_found)):
            at = atoms_found[i]
            if at is None:
                try:
                    atoms_found[i] = cter_atoms_map[pdb_atoms[i]]
                except KeyError:
                    raise UnknownAtomError('The atom {} is unknown'.format(at))

        new_nucleotide = Nucleotide(nuclname,residue.number,variant=cter)
        new_nucleotide.reorder_atoms(atoms_found)

        return new_nucleotide

    def _process_residue(self, residue):

        resname = residue.name

        pdb_atoms = [at.name for at in residue]

        atoms_found = [None]*len(pdb_atoms)
        for at, info in RESIDUES[resname]['atoms'].items():

            try:
                idx = pdb_atoms.index(at)
                atoms_found[idx] = at
            except ValueError:
                for alt in info['alternatives']:
                    try:
                        idx = pdb_atoms.index(alt)
                        atoms_found[idx] = at
                    except ValueError:
                        continue
                    else:
                        break
                else:
                    raise UnknownAtomError('The atom {} is unknown'.format(at))

        new_residue = Residue(resname,residue.number,variant=None)
        new_residue.reorder_atoms(atoms_found)

        return new_residue

    def _process_nucleotide(self, residue):

        nuclname = residue.name

        pdb_atoms = [at.name for at in residue]

        atoms_found = [None]*len(pdb_atoms)
        for at, info in NUCLEOTIDES[nuclname]['atoms'].items():

            try:
                idx = pdb_atoms.index(at)
                atoms_found[idx] = at
            except ValueError:
                for alt in info['alternatives']:
                    try:
                        idx = pdb_atoms.index(alt)
                        atoms_found[idx] = at
                    except ValueError:
                        continue
                    else:
                        break
                else:
                    raise UnknownAtomError('The atom {} is unknown'.format(at))

        new_nucleotide = Nucleotide(nuclname,residue.number,variant=None)
        new_nucleotide.reorder_atoms(atoms_found)

        return new_nucleotide            

    def _is_ter_nucleotide(self, nucleotide, ter5=True):

        terminus_keyword = 'is_5ter_terminus' if ter5 else 'is_3ter_terminus'

        pdb_atoms = [at.name for at in nucleotide.atom_list]

        for nucl in NUCLEOTIDES.values():

            if not nucl[terminus_keyword]:
                continue
            atoms = nucl['atoms'].keys()

            for at in atoms:
                if at not in pdb_atoms:
                    break
            else:
                return True
                    
    def _split_nucleotide_chain(self, pdb_element):

        splitted_chains = []

        ter3_variants = [variant for variant in NUCLEOTIDES.values() if variant['is_3ter_terminus']]

        start = 0
        for comp, residue in enumerate(pdb_element.residues):
            pdb_atoms = [at.name for at in residue.atom_list]
            for variant in ter3_variants:
                for vat in variant['atoms']:
                    if vat not in pdb_atoms:
                        break
                else:
                    splitted_chains.append(pdb_element.residues[start:comp+1])
                    start = comp + 1

        return splitted_chains

    def _process_nucleotide_chain(self, pdb_element):

        splitted_chains = self._split_nucleotide_chain(pdb_element)

        nucleotide_chains = []
        for comp, chain in enumerate(splitted_chains):
            nucleotide_chain = NucleotideChain('{}{}'.format(pdb_element.chain_id,comp+1))
            nucleotides = []
            for nucleotide in chain:
                if self._is_ter_nucleotide(nucleotide,ter5=True):
                    res = self._process_5ter_residue(nucleotide)
                elif self._is_ter_nucleotide(nucleotide,ter5=False):
                    res = self._process_3ter_residue(nucleotide)
                else:
                    res = self._process_nucleotide(nucleotide)
                nucleotides.append(res)
            nucleotide_chain.set_nucleotides(nucleotides)
            nucleotide_chains.append(nucleotide_chain)
        
        return nucleotide_chains

    def _process_peptide_chain(self, pdb_element):

        peptide_chain = PeptideChain(pdb_element.chain_id)
        residues = []
        for comp, residue in enumerate(pdb_element.residues):
            if comp == 0:
                res = self._process_nter_residue(residue)
            elif comp == len(pdb_element.residues) - 1:
                res = self._process_cter_residue(residue)
            else:
                res = self._process_residue(residue)
            residues.append(res)
        peptide_chain.set_residues(residues)

        return peptide_chain

    def build_chemical_system(self):
        
        chemical_system = ChemicalSystem()

        for ce in self._chemicalEntities:
            chemical_system.add_chemical_entity(ce)

        from Configuration import RealConfiguration

        coordinates = []
        for obj in self._struct:
            for atom in obj.atom_list:
                coordinates.append(atom.position)
        coordinates = np.array(coordinates)
        coordinates *= 0.1

        chemical_system.configuration = RealConfiguration(chemical_system,coordinates)

        return chemical_system

if __name__ == '__main__':

    pdb_reader = PDBReader('nuc.pdb')
    print('here0')
    cs = pdb_reader.build_chemical_system()
    print('here1')
    cs.serialize('test.h5')
    print('here2')
    cs.load('test.h5')
    print(cs.group('base'))
