import abc

class _H5ChemicalEntity:

    __metaclass__ = abc.ABCMeta

    def __init__(self, h5_file, h5_contents):

        self._h5_file = h5_file

        self._h5_contents = h5_contents

    @abc.abstractmethod
    def build(self):
        pass

class H5Atom(_H5ChemicalEntity):

    def __init__(self, h5_file, h5_contents, symbol, name, ghost):

        super(H5Atom,self).__init__(h5_file, h5_contents)

        self._symbol = symbol

        self._name = name

        self._ghost = ghost

    def build(self):

        from ChemicalEntity import Atom
        a = Atom(symbol=self._symbol,name=self._name, ghost=self._ghost)

        return a

class H5AtomCluster(_H5ChemicalEntity):

    def __init__(self, h5_file, h5_contents, atom_indexes, name):

        super(H5AtomCluster,self).__init__(h5_file, h5_contents)

        self._atom_indexes = atom_indexes

        self._name = name

    def build(self):

        atoms = []
        for atom_index in self._atom_indexes:
            h5_atom_instance = eval(self._h5_contents['atoms'][atom_index],globals(),{'self':self,'h5_contents':self._h5_contents})
            atoms.append(h5_atom_instance.build())

        from ChemicalEntity import AtomCluster
        ac = AtomCluster(self._name,atoms)
        
        return ac

class H5Molecule(_H5ChemicalEntity):

    def __init__(self, h5_file, h5_contents, atom_indexes, code, name):

        super(H5Molecule,self).__init__(h5_file, h5_contents)

        self._atom_indexes = atom_indexes

        self._code = code

        self._name = name

    def build(self):

        from ChemicalEntity import Molecule
        mol = Molecule(self._code,self._name)

        atoms = []
        for atom_index in self._atom_indexes:
            h5_atom_instance = eval(self._h5_contents['atoms'][atom_index],globals(),{'self':self,'h5_contents':self._h5_contents})
            atom = h5_atom_instance.build()
            atom.parent = mol
            atoms.append(atom)

        atoms = [at.name for at in atoms]
        mol.reorder_atoms(atoms)
        
        return mol

class H5Residue(_H5ChemicalEntity):

    def __init__(self, h5_file, h5_contents, atom_indexes, code, name, variant):

        super(H5Residue,self).__init__(h5_file, h5_contents)

        self._atom_indexes = atom_indexes

        self._code = code

        self._name = name

        self._variant = variant

    def build(self):

        from ChemicalEntity import Residue
        res = Residue(self._code,self._name,self._variant)

        atoms = []
        for atom_index in self._atom_indexes:
            h5_atom_instance = eval(self._h5_contents['atoms'][atom_index],globals(),{'self':self,'h5_contents':self._h5_contents})
            atom = h5_atom_instance.build()
            atom.parent = res
            atoms.append(atom)

        atoms = [at.name for at in atoms]
        res.set_atoms(atoms)
        
        return res

class H5Nucleotide(_H5ChemicalEntity):

    def __init__(self, h5_file, h5_contents, atom_indexes, code, name, variant):

        super(H5Nucleotide,self).__init__(h5_file, h5_contents)

        self._atom_indexes = atom_indexes

        self._code = code

        self._name = name

        self._variant = variant

    def build(self):

        from ChemicalEntity import Nucleotide
        nucl = Nucleotide(self._code,self._name,self._variant)

        atoms = []
        for atom_index in self._atom_indexes:
            h5_atom_instance = eval(self._h5_contents['atoms'][atom_index],globals(),{'self':self,'h5_contents':self._h5_contents})
            atom = h5_atom_instance.build()
            atom.parent = nucl
            atoms.append(atom)

        atoms = [at.name for at in atoms]
        nucl.set_atoms(atoms)
        
        return nucl

class H5PeptideChain(_H5ChemicalEntity):

    def __init__(self, h5_file, h5_contents, name, res_indexes):

        super(H5PeptideChain,self).__init__(h5_file, h5_contents)

        self._name = name

        self._res_indexes = res_indexes

    def build(self):
 
        from ChemicalEntity import PeptideChain

        pc = PeptideChain(self._name)

        residues = []
        for res_index in self._res_indexes:
            h5_residue_instance = eval(self._h5_contents['residues'][res_index],globals(),{'self':self,'h5_contents':self._h5_contents})
            res = h5_residue_instance.build()
            res.parent = pc
            residues.append(res)

        pc.set_residues(residues)

        return pc

class H5NucleotideChain(_H5ChemicalEntity):

    def __init__(self, h5_file, h5_contents, name, nucl_indexes):

        super(H5NucleotideChain,self).__init__(h5_file, h5_contents)

        self._name = name

        self._nucl_indexes = nucl_indexes

    def build(self):
 
        from ChemicalEntity import NucleotideChain

        nc = NucleotideChain(self._name)

        nucleotides = []
        for nucl_index in self._nucl_indexes:
            h5_nucleotide_instance = eval(self._h5_contents['nucleotides'][nucl_index],globals(),{'self':self,'h5_contents':self._h5_contents})
            nucl = h5_nucleotide_instance.build()
            nucl.parent = nc
            nucleotides.append(nucl)

        nc.set_nucleotides(nucleotides)

        return nc

class H5Protein(_H5ChemicalEntity):

    def __init__(self,h5_file,h5_contents,name,peptide_chain_indexes):

        super(H5Protein,self).__init__(h5_file, h5_contents)

        self._name = name

        self._peptide_chain_indexes = peptide_chain_indexes

    def build(self):

        from ChemicalEntity import Protein

        p = Protein(self._name)
        
        peptide_chains = []
        for pc_index in self._peptide_chain_indexes:
            h5_peptide_chain_instance = eval(self._h5_contents['peptide_chains'][pc_index],globals(),{'self':self,'h5_contents':self._h5_contents})
            pc = h5_peptide_chain_instance.build()
            pc.parent = p
            peptide_chains.append(pc)

        p.set_peptide_chains(peptide_chains)

        return p