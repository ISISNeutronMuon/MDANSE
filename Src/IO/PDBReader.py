import copy
import string

import numpy as np

from MDANSE.Chemistry.ChemicalEntity import Nucleotide, is_molecule, Atom, AtomCluster, ChemicalSystem, Molecule, Nucleotide, NucleotideChain, Residue, PeptideChain, UnknownAtomError
from MDANSE.Chemistry import ATOMS_DATABASE, MOLECULES_DATABASE, NUCLEOTIDES_DATABASE, RESIDUES_DATABASE
from MDANSE.IO.PDB import PDBMolecule, PDBNucleotideChain, PDBPeptideChain, Structure

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
                self._chemicalEntities.append(self._process_nucleotide_chain(pdb_element))

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
            if atom_without_digits[:comp] in ATOMS_DATABASE:
                return atom_without_digits[:comp]
            comp += 1
            if comp > len(atom_without_digits):
                raise UnknownAtomError(atom)

    def _process_atom(self, atom):

        atname = atom.name

        atom_found = None
        for at, info in ATOMS_DATABASE.items():
            if at == atname:
                atom_found = Atom(name=at,**info)
            else:
                for alt in info.get('alternatives',[]):
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

        code = molecule.name

        pdb_atoms = [at.name for at in molecule]

        atoms_found = [None]*len(pdb_atoms)
        for at, info in MOLECULES_DATABASE[code]['atoms'].items():

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
                    raise UnknownAtomError('Unknown atom')

        molname = '{}_{}'.format(code,molecule.number)
        new_molecule = Molecule(code,molname)
        new_molecule.reorder_atoms(atoms_found)

        return new_molecule

    def _guess_prot_terminus_type(self, pdb_atoms, nter=True):

        for resname,residue in RESIDUES_DATABASE.items():
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

        for nuclname,nucleotide in NUCLEOTIDES_DATABASE.items():
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

        code = residue.name

        pdb_atoms = [at.name for at in residue]

        atoms_found = [None]*len(pdb_atoms)

        nter_variants = [(name,res) for name,res in RESIDUES_DATABASE.items() if res['is_n_terminus']]

        atoms_not_found = []

        for comp, pdb_atom in enumerate(pdb_atoms):
            for at, info in RESIDUES_DATABASE[code]['atoms'].items():
                if pdb_atom == at or pdb_atom in info['alternatives']:
                    atoms_found[comp] = at
                    break
            else:
                atoms_not_found.append(pdb_atom)

        if atoms_not_found:
            for name,res in nter_variants:
                for at, info in res['atoms'].items():
                    allNames = [at] + info['alternatives']
                    for aa in allNames:                        
                        if aa in atoms_not_found:
                            idx = pdb_atoms.index(aa)
                            atoms_found[idx] = at
                            break
                    else:
                        break
                else:
                    nter = name
                    break
            else:
                raise UnknownAtomError('The atom {} is unknown'.format(at))

        resname = '{}{}'.format(code,residue.number)
        new_residue = Residue(code,resname,variant=nter)
        new_residue.set_atoms(atoms_found)

        return new_residue

    def _process_5ter_residue(self, residue):

        resname = residue.name

        pdb_atoms = [at.name for at in residue]

        atoms_found = [None]*len(pdb_atoms)

        nter_variants = [(name,res) for name,res in NUCLEOTIDES_DATABASE.items() if res['is_5ter_terminus']]

        atoms_not_found = []

        for comp, pdb_atom in enumerate(pdb_atoms):
            for at, info in NUCLEOTIDES_DATABASE[resname]['atoms'].items():
                if pdb_atom == at or pdb_atom in info['alternatives']:
                    atoms_found[comp] = at
                    break
            else:
                atoms_not_found.append(pdb_atom)

        if atoms_not_found:
            for name,res in nter_variants:
                for at, info in res['atoms'].items():
                    allNames = [at] + info['alternatives']
                    for aa in allNames:                        
                        if aa in atoms_not_found:
                            idx = pdb_atoms.index(aa)
                            atoms_found[idx] = at
                            break
                    else:
                        break
                else:
                    nter = name
                    break
            else:
                raise UnknownAtomError('The atom {} is unknown'.format(at))

        new_residue = Nucleotide(resname,residue.number,variant=nter)
        new_residue.set_atoms(atoms_found)

        return new_residue

    def _process_cter_residue(self, residue):

        code = residue.name

        pdb_atoms = [at.name for at in residue]

        atoms_found = [None]*len(pdb_atoms)

        cter_variants = [(name,res) for name,res in RESIDUES_DATABASE.items() if res['is_c_terminus']]

        atoms_not_found = []

        for comp, pdb_atom in enumerate(pdb_atoms):
            for at, info in RESIDUES_DATABASE[code]['atoms'].items():
                if pdb_atom == at or pdb_atom in info['alternatives']:
                    atoms_found[comp] = at
                    break
            else:
                atoms_not_found.append(pdb_atom)

        if atoms_not_found:
            for name,res in cter_variants:
                for at, info in res['atoms'].items():
                    allNames = [at] + info['alternatives']
                    for aa in allNames:                        
                        if aa in atoms_not_found:
                            idx = pdb_atoms.index(aa)
                            atoms_found[idx] = at
                            break
                    else:
                        break
                else:
                    cter = name
                    break
            else:
                raise UnknownAtomError('The atoms {} are unknown'.format(atoms_not_found))

        resname = '{}{}'.format(code,residue.number)
        new_residue = Residue(code,resname,variant=cter)
        new_residue.set_atoms(atoms_found)

        return new_residue

    def _process_3ter_residue(self, residue):

        resname = residue.name

        pdb_atoms = [at.name for at in residue]

        atoms_found = [None]*len(pdb_atoms)

        cter_variants = [(name,res) for name,res in NUCLEOTIDES_DATABASE.items() if res['is_3ter_terminus']]

        atoms_not_found = []

        for comp, pdb_atom in enumerate(pdb_atoms):
            for at, info in NUCLEOTIDES_DATABASE[resname]['atoms'].items():
                if pdb_atom == at or pdb_atom in info['alternatives']:
                    atoms_found[comp] = at
                    break
            else:
                atoms_not_found.append(pdb_atom)

        if atoms_not_found:
            for name,res in cter_variants:
                for at, info in res['atoms'].items():
                    allNames = [at] + info['alternatives']
                    for aa in allNames:                        
                        if aa in atoms_not_found:
                            idx = pdb_atoms.index(aa)
                            atoms_found[idx] = at
                            break
                    else:
                        break
                else:
                    cter = name
                    break
            else:
                raise UnknownAtomError('The atom {} is unknown'.format(at))

        new_residue = Nucleotide(resname,residue.number,variant=cter)
        new_residue.set_atoms(atoms_found)

        return new_residue

    def _process_residue(self, residue):

        code = residue.name

        pdb_atoms = [at.name for at in residue]

        atoms_found = [None]*len(pdb_atoms)

        for comp, pdb_atom in enumerate(pdb_atoms):
            for at, info in RESIDUES_DATABASE[code]['atoms'].items():
                if pdb_atom == at or pdb_atom in info['alternatives']:
                    atoms_found[comp] = at
                    break
            else:
                raise UnknownAtomError('The atom {}:{} is unknown'.format(code,pdb_atom))

        resname = '{}{}'.format(code,residue.number)
        new_residue = Residue(code,resname,variant=None)
        new_residue.set_atoms(atoms_found)

        return new_residue

    def _process_nucleotide(self, residue):

        resname = residue.name

        pdb_atoms = [at.name for at in residue]

        atoms_found = [None]*len(pdb_atoms)

        atoms_not_found = []

        for comp, pdb_atom in enumerate(pdb_atoms):
            for at, info in NUCLEOTIDES_DATABASE[resname]['atoms'].items():
                if pdb_atom == at or pdb_atom in info['alternatives']:
                    atoms_found[comp] = at
                    break
            else:
                atoms_not_found.append(pdb_atom)

        if atoms_not_found:
            raise UnknownAtomError('The atoms {} are unknown'.format(atoms_not_found))

        new_residue = Nucleotide(resname,residue.number,variant=None)
        new_residue.set_atoms(atoms_found)

        return new_residue

    def _is_ter_nucleotide(self, nucleotide, ter5=True):

        terminus_keyword = 'is_5ter_terminus' if ter5 else 'is_3ter_terminus'

        pdb_atoms = [at.name for at in nucleotide.atom_list]

        for nucl in NUCLEOTIDES_DATABASE:

            if not nucl[terminus_keyword]:
                continue
            atoms = nucl['atoms'].keys()

            for at in atoms:
                if at not in pdb_atoms:
                    break
            else:
                return True
        else:
            return False
                    
    def _process_nucleotide_chain(self, pdb_element):
        
        nucleotide_chain = NucleotideChain(pdb_element.chain_id)
        residues = []
        for comp, residue in enumerate(pdb_element.residues):
            if comp == 0:
                res = self._process_5ter_residue(residue)
            elif comp == len(pdb_element.residues) - 1:
                res = self._process_3ter_residue(residue)
            else:
                res = self._process_nucleotide(residue)
            residues.append(res)
        nucleotide_chain.set_nucleotides(residues)

        return nucleotide_chain

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

        from MDANSE.MolecularDynamics.Configuration import RealConfiguration

        coordinates = []
        for obj in self._struct:
            for atom in obj.atom_list:
                coordinates.append(atom.position)
        coordinates = np.array(coordinates)
        coordinates *= 0.1

        chemical_system.configuration = RealConfiguration(chemical_system,coordinates)

        return chemical_system

if __name__ == '__main__':

    print('Reading')
    pdb_reader = PDBReader('/home/pellegrini/apoferritin.pdb')
    print('Building chemical system')
    cs = pdb_reader.build_chemical_system()
    # print('Serializing')
    # cs.serialize('test.h5')
    # print('Loading')
    # cs.load('test.h5')
    # print(cs.chemical_entities)
