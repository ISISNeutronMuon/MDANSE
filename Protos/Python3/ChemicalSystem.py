import numpy as np

import h5py

from ChemicalEntity import ChemicalEntity, Atom, Molecule, Residue, PeptideChain, Protein
from H5ChemicalEntity import H5Atom, H5Molecule, H5Residue, H5PeptideChain, H5Protein

class InvalidChemicalEntityError(Exception):
    pass

class InconsistentChemicalSystemError(Exception):
    pass

class ChemicalSystem(ChemicalEntity):

    def __init__(self):

        self._chemical_entities = []

        self._unit_cell = None

        self._configuration = None

    def add_chemical_entity(self, chemical_entity):

        if not isinstance(chemical_entity,ChemicalEntity):
            raise InvalidChemicalEntityError('invalid chemical entity')

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

        self._h5_file = h5py.File(h5_filename,'r',libver='latest')
        grp = self._h5_file['/chemical_system']
        self._chemical_entities = []
        skeleton = self._h5_file['/chemical_system/contents'][:]

        h5_contents = {}
        for v in ['atoms','molecules','residues','peptide_chains','proteins']:
            h5_contents[v] = grp[v][:]

        for entity_type, entity_index in skeleton:
            entity_index = int(entity_index)
            h5_chemical_entity_instance = eval(grp[entity_type][entity_index])
            self._chemical_entities.append(h5_chemical_entity_instance.build())
        self._h5_file.close()

    def number_of_atoms(self):

        number_of_atoms = 0
        for ce in self._chemical_entities:
            number_of_atoms += ce.number_of_atoms()
        return number_of_atoms

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
        
if __name__ == '__main__':

    from ChemicalEntity import PeptideChain, Protein, Residue

    c1 = PeptideChain('Toto')
    residues = [Residue('LEU',variant='NT1'),Residue('VAL')]
    c1.set_residues(residues)
    p1 = Protein('insulin')
    p1.set_peptide_chains([c1])

    c2 = PeptideChain('Tata')
    residues = [Residue('LEU',variant='NT1'),Residue('VAL')]
    c2.set_residues(residues)
    p2 = Protein('crambin')
    p2.set_peptide_chains([c2])

    chemical_system = ChemicalSystem()
    chemical_system.add_chemical_entity(p1)
    chemical_system.add_chemical_entity(p2)

    chemical_system.serialize('test.h5')

    chemical_system = ChemicalSystem()
    chemical_system.load('test.h5')
