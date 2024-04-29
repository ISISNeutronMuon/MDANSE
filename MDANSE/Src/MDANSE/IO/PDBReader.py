#    This file is part of MDANSE.
#
#    MDANSE is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
import copy
import string

import numpy as np

from MDANSE.Chemistry.ChemicalEntity import (
    Nucleotide,
    is_molecule,
    Atom,
    AtomCluster,
    ChemicalSystem,
    Molecule,
    Nucleotide,
    NucleotideChain,
    Residue,
    PeptideChain,
    Protein,
    UnknownAtomError,
)
from MDANSE.Chemistry import (
    ATOMS_DATABASE,
    MOLECULES_DATABASE,
    NUCLEOTIDES_DATABASE,
    RESIDUES_DATABASE,
    RESIDUE_ALT_NAMES,
)
from MDANSE.MolecularDynamics.Configuration import RealConfiguration
from MDANSE.IO.PDB import PDBMolecule, PDBNucleotideChain, PDBPeptideChain, Structure


class PDBReaderError(Exception):
    pass


class PDBReader:
    def __init__(self, filename):
        """Constructor.

        Args:
            filename (str): the input PDB file
        """

        self._chemicalEntities = []

        self._struct = Structure(filename)

        self._build_chemical_entities()

    def _build_chemical_entities(self):
        """Build the chemical entities stored in the PDB file."""

        peptide_chains = []
        for pdb_element in self._struct.objects:
            if isinstance(pdb_element, PDBPeptideChain):
                peptide_chains.append(self._process_peptide_chain(pdb_element))
            else:
                if peptide_chains:
                    p = Protein()
                    p.set_peptide_chains(peptide_chains)
                    self._chemicalEntities.append(p)
                    peptide_chains = []

                if isinstance(pdb_element, PDBNucleotideChain):
                    self._chemicalEntities.append(
                        self._process_nucleotide_chain(pdb_element)
                    )

                elif isinstance(pdb_element, PDBMolecule):
                    if len(pdb_element) == 1:
                        self._chemicalEntities.append(
                            self._process_atom(pdb_element[0])
                        )
                    else:
                        if is_molecule(pdb_element.name):
                            self._chemicalEntities.append(
                                self._process_molecule(pdb_element)
                            )
                        else:
                            self._chemicalEntities.append(
                                self._process_atom_cluster(pdb_element)
                            )

        if peptide_chains:
            p = Protein()
            p.set_peptide_chains(peptide_chains)
            self._chemicalEntities.append(p)
            peptide_chains = []

    def _guess_atom_symbol(self, atom):
        """Guess the atom symbol from an atom name.

        Args:
            atom (str): thhe atom name

        Returns:
            str: the atom symbol
        """

        atom_without_digits = "".join([at for at in atom if at not in string.digits])

        comp = 1
        while True:
            if atom_without_digits[:comp] in ATOMS_DATABASE:
                return atom_without_digits[:comp]
            comp += 1
            if comp > len(atom_without_digits):
                raise PDBReaderError(atom)

    def _process_atom(self, atom):
        """Process a PDB atom.

        Args:
            atom (MDANSE.IO.PDB.PDBAtom): the PDB entry corresponding to the atom

        Returns:
            MDANSE.Chemistry.ChemicalEntity.Atom: the processed atom
        """

        atname = atom.name.capitalize()

        atom_found = None
        for at, info in ATOMS_DATABASE.items():
            if at == atname:
                atom_found = Atom(name=at, **info)
            else:
                for alt in info.get("alternatives", []):
                    if alt == atname:
                        copy_info = copy.deepcopy(info)
                        atom_found = Atom(name=at, **copy_info)
                        atom_found.position = atom.position
                        break
                else:
                    continue

        if atom_found is None:
            raise PDBReaderError("The atom {} is unknown".format(atname))

        return atom_found

    def _process_atom_cluster(self, atom_cluster):
        """Process a PDB atom cluster.

        Args:
            atom (MDANSE.IO.PDB.PDBAtomCluster): the PDB entry corresponding to the atom cluster

        Returns:
            MDANSE.Chemistry.ChemicalEntity.AtomCluster: the processed atom cluster
        """

        ac_name = atom_cluster.name

        pdb_atoms = [at.name for at in atom_cluster]

        atoms = []
        for at in pdb_atoms:
            symbol = self._guess_atom_symbol(at)
            atoms.append(Atom(name=at, symbol=symbol))

        new_atom_cluster = AtomCluster(ac_name, atoms)

        return new_atom_cluster

    def _process_molecule(self, molecule):
        """Process a PDB molecule.

        Args:
            atom (MDANSE.IO.PDB.PDBMolecule): the PDB entry corresponding to the molecule

        Returns:
            MDANSE.Chemistry.ChemicalEntity.Molecule: the processed molecule
        """

        code = molecule.name

        pdb_atoms = [at.name for at in molecule]

        atoms_found = [None] * len(pdb_atoms)
        for at, info in MOLECULES_DATABASE[code]["atoms"].items():
            try:
                idx = pdb_atoms.index(at)
                atoms_found[idx] = at
            except ValueError:
                for alt in info["alternatives"]:
                    try:
                        idx = pdb_atoms.index(alt)
                        atoms_found[idx] = at
                    except ValueError:
                        continue
                    else:
                        break
                else:
                    raise PDBReaderError("Unknown atom")

        molname = "{}_{}".format(code, molecule.number)
        new_molecule = Molecule(code, molname)
        new_molecule.reorder_atoms(atoms_found)

        return new_molecule

    def _process_nter_residue(self, residue):
        """Process a N terminus residue.

        Args:
            residue (MDANSE.IO.PDB.PDBResidue): the residue

        Returns:
            MDANSE.Chemistry.ChemicalEntity.Residue: the processed residue
        """

        code = residue.name

        pdb_atoms = [at.name for at in residue]

        atoms_found = [None] * len(pdb_atoms)

        atoms_not_found = []

        for comp, pdb_atom in enumerate(pdb_atoms):
            # Loop over the atoms of this residue stored in the corresponding residue database entry
            for at, info in RESIDUES_DATABASE[code]["atoms"].items():
                # A match was found, pass to the next PDB atom
                if pdb_atom == at or pdb_atom in info["alternatives"]:
                    atoms_found[comp] = at
                    break
            # No match was found, the PDB atom is marked as not found
            else:
                atoms_not_found.append(pdb_atom)

        # Fetch all the N ter variants from the residues database
        nter_variants = [
            (name, res)
            for name, res in RESIDUES_DATABASE.items()
            if res["is_n_terminus"]
        ]

        # The atoms that has not been found so far will be searched now in the N ter variants entries of the database
        if atoms_not_found:
            # Loop over the N ter variants of the residues database
            for name, res in nter_variants:
                # Loop over the atom of the current variant
                for at, info in res["atoms"].items():
                    # These are all the names the atoms can take (actual DB name + alternatives)
                    allNames = [at] + info["alternatives"]
                    for aa in allNames:
                        # The variant atom match one of the not found atoms, mark it as known and pass to the next variant atom
                        if aa in atoms_not_found:
                            idx = pdb_atoms.index(aa)
                            atoms_found[idx] = at
                            break
                    # The variant atom was not found in the not found atoms, this variant can not be the right one. Skip it.
                    else:
                        break
                # All the variant atoms has been found in the not found atoms, this variant is the right one
                else:
                    nter = name
                    break
            else:
                raise PDBReaderError("The atom {} is unknown".format(at))

        resname = "{}{}".format(code, residue.number)
        new_residue = Residue(code, resname, variant=nter)
        new_residue.set_atoms(atoms_found)

        return new_residue

    def _process_5ter_residue(self, residue):
        """Process a 5 ter terminus nucleotide.

        Args:
            residue (MDANSE.IO.PDB.PDBNucleotide): the nucleotide

        Returns:
            MDANSE.Chemistry.ChemicalEntity.Nucleotide: the processed nucleotide
        """

        resname = residue.name

        pdb_atoms = [at.name for at in residue]

        atoms_found = [None] * len(pdb_atoms)

        atoms_not_found = []

        for comp, pdb_atom in enumerate(pdb_atoms):
            for at, info in NUCLEOTIDES_DATABASE[resname]["atoms"].items():
                if pdb_atom == at or pdb_atom in info["alternatives"]:
                    atoms_found[comp] = at
                    break
            else:
                atoms_not_found.append(pdb_atom)

        ter5_variants = [
            (name, res)
            for name, res in NUCLEOTIDES_DATABASE.items()
            if res["is_5ter_terminus"]
        ]

        if atoms_not_found:
            for name, res in ter5_variants:
                for at, info in res["atoms"].items():
                    allNames = [at] + info["alternatives"]
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
                raise PDBReaderError("The atom {} is unknown".format(at))

        new_residue = Nucleotide(resname, residue.number, variant=nter)
        new_residue.set_atoms(atoms_found)

        return new_residue

    def _process_cter_residue(self, residue):
        """Process the C terminal residue.

        Args:
            residue: MDANSE.IO.PDB.PDBResidue

        Returns:
            MDANSE.Chemistry.ChemicalEntity.Residue: the C ter residue
        """

        code = residue.name

        pdb_atoms = [at.name for at in residue]

        atoms_found = [None] * len(pdb_atoms)

        # Loop over the PDB atoms of this residue
        atoms_not_found = []
        for comp, pdb_atom in enumerate(pdb_atoms):
            # Loop over the atoms of this residue stored in the corresponding residue database entry
            for at, info in RESIDUES_DATABASE[code]["atoms"].items():
                # A match was found, pass to the next PDB atom
                if pdb_atom == at or pdb_atom in info["alternatives"]:
                    atoms_found[comp] = at
                    break
            # No match was found, the PDB atom is marked as not found
            else:
                atoms_not_found.append(pdb_atom)

        # Fetch all the C ter variants from the residues database
        cter_variants = [
            (name, res)
            for name, res in RESIDUES_DATABASE.items()
            if res["is_c_terminus"]
        ]

        # The atoms that has not been found so far will be searched now in the C ter variants entries of the database
        cter = None
        if atoms_not_found:
            # Loop over the C ter variants of the residues database
            for name, res in cter_variants:
                # Loop over the atom of the current variant
                for at, info in res["atoms"].items():
                    # These are all the names the atoms can take (actual DB name + alternatives)
                    allNames = [at] + info["alternatives"]
                    for aa in allNames:
                        # The variant atom match one of the not found atoms, mark it as known and pass to the next variant atom
                        if aa in atoms_not_found:
                            idx = pdb_atoms.index(aa)
                            atoms_found[idx] = at
                            break
                    # The variant atom was not found in the not found atoms, this variant can not be the right one. Skip it.
                    else:
                        break
                # All the variant atoms has been found in the not found atoms, this variant is the right one
                else:
                    cter = name
                    break
            else:
                raise PDBReaderError("The atoms {} are unknown".format(atoms_not_found))

        if cter is None:
            raise PDBReaderError(
                "Could not find a suitable CTER variant for residue {}{}".format(
                    residue.name, residue.number
                )
            )

        resname = "{}{}".format(code, residue.number)
        new_residue = Residue(code, resname, variant=cter)
        new_residue.set_atoms(atoms_found)

        return new_residue

    def _process_3ter_residue(self, residue):
        """Process the 3 ter terminal nucleotide.

        Args:
            residue: MDANSE.IO.PDB.PDBNucleotide

        Returns:
            MDANSE.Chemistry.ChemicalEntity.Nucleotide: the 3 ter nucleotide
        """

        resname = residue.name

        pdb_atoms = [at.name for at in residue]

        atoms_found = [None] * len(pdb_atoms)

        atoms_not_found = []

        for comp, pdb_atom in enumerate(pdb_atoms):
            for at, info in NUCLEOTIDES_DATABASE[resname]["atoms"].items():
                if pdb_atom == at or pdb_atom in info["alternatives"]:
                    atoms_found[comp] = at
                    break
            else:
                atoms_not_found.append(pdb_atom)

        ter3_variants = [
            (name, res)
            for name, res in NUCLEOTIDES_DATABASE.items()
            if res["is_3ter_terminus"]
        ]

        if atoms_not_found:
            for name, res in ter3_variants:
                for at, info in res["atoms"].items():
                    allNames = [at] + info["alternatives"]
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
                raise PDBReaderError("The atom {} is unknown".format(at))

        new_residue = Nucleotide(resname, residue.number, variant=cter)
        new_residue.set_atoms(atoms_found)

        return new_residue

    def _process_residue(self, residue):
        """Process a residue.

        Args:
            residue (MDANSE.IO.PDB.PDBResidue): the PDB residue

        Returns:
            MDANSE.Chemistry.ChemicalEntity.Residue: the processed residue
        """

        code = residue.name

        pdb_atoms = [at.name for at in residue]

        if code in RESIDUE_ALT_NAMES:
            # RESIDUES_DATABASE is a many-to-one map multiple codes
            # can map to one residue in MDANSE.
            # If the code is in RESIDUE_ALT_NAMES then it is a
            # many-to-many map. In this case the code can map to many
            # different residues.
            for new_code in RESIDUE_ALT_NAMES[code]:
                # go through each name that code could be
                atoms_found = [None] * len(pdb_atoms)
                for comp, pdb_atom in enumerate(pdb_atoms):
                    if len(atoms_found) != len(
                        RESIDUES_DATABASE[new_code]["atoms"].items()
                    ):
                        # different number of atoms break and try the next name
                        break
                    for at, info in RESIDUES_DATABASE[new_code]["atoms"].items():
                        if pdb_atom == at or pdb_atom in info["alternatives"]:
                            atoms_found[comp] = at
                            break
                    else:
                        # unable to match the atom in the RESIDUES_DATABASE
                        # try the next residue name
                        break
                if None not in atoms_found:
                    # matched all atoms found the residue so break
                    break
            else:
                # went through all alternative names looks like we were
                # unable to match the code to the MDANSE residues
                raise PDBReaderError(
                    "Unable to find residue for {}{}".format(code, residue.number)
                )
            # found the match from the alternate name to the name in
            # mdanse lets rename the code
            code = new_code
            residue.name = code

        else:
            atoms_found = [None] * len(pdb_atoms)
            for comp, pdb_atom in enumerate(pdb_atoms):
                for at, info in RESIDUES_DATABASE[code]["atoms"].items():
                    if pdb_atom == at or pdb_atom in info["alternatives"]:
                        atoms_found[comp] = at
                        break
                else:
                    raise PDBReaderError(
                        "The atom {}{}:{} is unknown".format(
                            code, residue.number, pdb_atom
                        )
                    )

        resname = "{}{}".format(code, residue.number)
        new_residue = Residue(code, resname, variant=None)
        new_residue.set_atoms(atoms_found)

        return new_residue

    def _process_nucleotide(self, residue):
        """Process a nucleotide.

        Args:
            residue (MDANSE.IO.PDB.PDBNucleotide): the PDB nucleotide

        Returns:
            MDANSE.Chemistry.ChemicalEntity.Nucleotide: the processed nucleotide
        """

        resname = residue.name

        pdb_atoms = [at.name for at in residue]

        atoms_found = [None] * len(pdb_atoms)

        atoms_not_found = []

        for comp, pdb_atom in enumerate(pdb_atoms):
            for at, info in NUCLEOTIDES_DATABASE[resname]["atoms"].items():
                if pdb_atom == at or pdb_atom in info["alternatives"]:
                    atoms_found[comp] = at
                    break
            else:
                atoms_not_found.append(pdb_atom)

        if atoms_not_found:
            raise PDBReaderError("The atoms {} are unknown".format(atoms_not_found))

        new_residue = Nucleotide(resname, residue.number, variant=None)
        new_residue.set_atoms(atoms_found)

        return new_residue

    def _process_nucleotide_chain(self, pdb_element):
        """Process a PDB nucleotide chain.

        Args:
            pdb_element (MDANSE.IO.PDB.PDBNucleotideChain): the PDB nucleotide chain to process

        Returns:
            MDANSE.Chemistry.ChemicalEntity.NucleotideChain: the process nucleotide chain
        """

        nucleotide_chain = NucleotideChain(pdb_element.chain_id)
        residues = []
        # Loop over the residues of the nucleotide chain
        for comp, residue in enumerate(pdb_element.residues):
            # Case the 5 ter residue
            if comp == 0:
                res = self._process_5ter_residue(residue)
            # Case the 3 ter residue
            elif comp == len(pdb_element.residues) - 1:
                res = self._process_3ter_residue(residue)
            # Normal residue
            else:
                res = self._process_nucleotide(residue)
            residues.append(res)
        nucleotide_chain.set_nucleotides(residues)

        return nucleotide_chain

    def _process_peptide_chain(self, pdb_element):
        """Process a PDB peptide chain.

        Args:
            pdb_element (MDANSE.IO.PDB.PeptideChain): the PDB peptide chain to process

        Returns:
            MDANSE.Chemistry.ChemicalEntity.PeptideChain: the process peptide chain
        """

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
        """Build the chemical system.

        Returns:
            MDANSE.Chemistry.ChemicalEntity.ChemicalSystem: the chemical system
        """

        chemical_system = ChemicalSystem()

        for ce in self._chemicalEntities:
            chemical_system.add_chemical_entity(ce)

        coordinates = []
        for obj in self._struct:
            for atom in obj.atom_list:
                coordinates.append(atom.position)
        coordinates = np.array(coordinates)
        coordinates *= 0.1

        chemical_system.configuration = RealConfiguration(chemical_system, coordinates)

        return chemical_system


if __name__ == "__main__":
    print("Reading")
    pdb_reader = PDBReader("/home/pellegrini/apoferritin.pdb")
    print("Building chemical system")
    cs = pdb_reader.build_chemical_system()

    from MDANSE.MolecularDynamics.Configuration import RealConfiguration

    conf = RealConfiguration(
        cs,
        np.empty((cs.number_of_atoms(), 3), dtype=np.float64),
        np.empty((3, 3), dtype=np.float64),
        **{"velocities": np.empty((cs.number_of_atoms(), 3), dtype=np.float64)},
    )
    cs.configuration = conf

    cs1 = cs.copy()

    print(cs1.configuration["velocities"])

    # print('Serializing')
    # cs.serialize('test.h5')
    # print('Loading')
    # cs.load('test.h5')
    # print(cs.chemical_entities)
