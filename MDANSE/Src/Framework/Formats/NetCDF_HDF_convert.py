# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Formats/NetCDFFormat.py
# @brief     Implements module/class/test NetCDFFormat
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************
"""
Converts NetCDF files to HDF5 format in the MDANSE project.
This script provides functions to convert NetCDF files to HDF5 format. 
It includes functions for reading the NetCDF file header,
 removing null characters, and performing the conversion. 
Proper exception handling and file management are implemented.
For more information about the MDANSE project, visit: https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx

"""
import abc
import h5py
from netCDF4 import Dataset
from MDANSE.Chemistry.ChemicalEntity import Atom, ChemicalSystem
 
class TrajectoryConverter(abc.ABC):
 
    @abc.abstractmethod
    def serialize(self, h5_file):
        """ Abstract method to serialize data into HDF5 format. """
        pass

    def __init__(self, trajectory_filename):
        self.trajectory_filename = trajectory_filename
        self.chemical_system = None

    def extract_entity_data(self, entity_group):
        entity_data = []
        for entity_varname, entity_var in entity_group.variables.items():
            properties = {}
            for prop_varname, prop_var in entity_var.variables.items():
                properties[prop_varname] = prop_var[:]
            entity_data.append(properties)
        return entity_data

class Atom:
        @classmethod
    def build(
        cls,
        h5_contents: Union[None, dict[str, list[list[str]]]],
        symbol: str,
        name: str,
        index: str,
        ghost: bool,
    ) -> Atom:
        """
        Creates an instance of the Atom class.
        """
        return cls(symbol=symbol, name=name, index=int(index), ghost=ghost)
    def serialize(self, h5_contents: dict[str, list[list[str]]]) -> tuple[str, int]:
        h5_contents.setdefault("atoms", []).append(
            [repr(self.symbol), repr(self.name), str(self.index), str(self.ghost)]
        )
        return "atoms", len(h5_contents["atoms"]) - 1

class AtomCluster:
        @classmethod
    def build(
        cls, h5_contents: dict[str, list[list[str]]], atom_indexes: list[int], name: str
    ) -> AtomCluster:
        """
        Creates an instance of the AtomCluster class.
        """
        contents = h5_contents["atoms"]
        atoms = []
        for index in atom_indexes:
            args = [literal_eval(arg.decode("utf8")) for arg in contents[index]]
            atoms.append(Atom.build(None, *args))

        return cls(name, atoms)

    def serialize(self, h5_contents: dict[str, list[list[str]]]) -> tuple[str, int]:
        if "atoms" in h5_contents:
            at_indexes = list(
                range(
                    len(h5_contents["atoms"]),
                    len(h5_contents["atoms"]) + len(self._atoms),
                )
            )
        else:
            at_indexes = list(range(len(self._atoms)))

        h5_contents.setdefault("atom_clusters", []).append(
            [str(at_indexes), repr(self._name)]
        )

        for at in self._atoms:
            at.serialize(h5_contents)

        return "atom_clusters", len(h5_contents["atom_clusters"]) - 1

class Molecule:
        """
        Creates an instance of the Molecule class.
        """    
        @classmethod
    def build(
        cls,
        h5_contents: dict[str, list[list[str]]],
        atom_indexes: list[int],
        code: str,
        name: str,
    ) -> Molecule:
       
        mol = cls(code, name)
        contents = h5_contents["atoms"]

        names = [literal_eval(contents[index][1]) for index in atom_indexes]

        mol.reorder_atoms(names)

        return mol

    def serialize(self, h5_contents: dict[str, list[list[str]]]) -> tuple[str, int]:
        if "atoms" in h5_contents:
            at_indexes = list(
                range(
                    len(h5_contents["atoms"]),
                    len(h5_contents["atoms"]) + len(self._atoms),
                )
            )
        else:
            at_indexes = list(range(len(self._atoms)))

        h5_contents.setdefault("molecules", []).append(
            [str(at_indexes), repr(self._code), repr(self._name)]
        )

        for at in self._atoms.values():
            at.serialize(h5_contents)

        return "molecules", len(h5_contents["molecules"]) - 1
    

class Residue:

    def serialize(self, h5_contents: dict[str, list[list[str]]]) -> tuple[str, int]:

    @classmethod
    def build(
        cls,
        h5_contents: dict[str, list[list[str]]],
        atom_indexes: list[int],
        code: str,
        name: str,
        variant: Union[str, None],
    ) -> Residue:
        """
        Creates an instance of the Residue class.
        """
        res = cls(code, name, variant)

        names = [literal_eval(h5_contents["atoms"][index][1]) for index in atom_indexes]
        res.set_atoms(names)

        return res

class Nucleotide:
    def serialize(self, h5_contents: dict[str, list[list[str]]]) -> tuple[str, int]:
        if "atoms" in h5_contents:
            at_indexes = list(
                range(
                    len(h5_contents["atoms"]),
                    len(h5_contents["atoms"]) + len(self._atoms),
                )
            )
        else:
            at_indexes = list(range(len(self._atoms)))

        h5_contents.setdefault("nucleotides", []).append(
            [str(at_indexes), repr(self._code), repr(self._name), repr(self._variant)]
        )

        for at in self._atoms.values():
            at.serialize(h5_contents)

        return "nucleotides", len(h5_contents["nucleotides"]) - 1

    @classmethod
    def build(
        cls,
        h5_contents: dict[str, list[list[str]]],
        atom_indexes: list[int],
        code: str,
        name: str,
        variant: Union[str, None],
    ) -> Nucleotide:
        nucl = cls(code, name, variant)

        names = [literal_eval(h5_contents["atoms"][index][1]) for index in atom_indexes]
        nucl.set_atoms(names)

        return nucl#
    def serialize(self, h5_contents: dict[str, list[list[str]]]) -> tuple[str, int]:
        if "atoms" in h5_contents:
            at_indexes = list(
                range(
                    len(h5_contents["atoms"]),
                    len(h5_contents["atoms"]) + len(self._atoms),
                )
            )
        else:
            at_indexes = list(range(len(self._atoms)))

        h5_contents.setdefault("nucleotides", []).append(
            [str(at_indexes), repr(self._code), repr(self._name), repr(self._variant)]
        )

        for at in self._atoms.values():
            at.serialize(h5_contents)

        return "nucleotides", len(h5_contents["nucleotides"]) - 1
    
 class NucleotideChain:
    @classmethod
    def build(
        cls, 
        h5_contents: dict[str, list[list[str]]], 
        name: str, 
        nucl_indexes: list[int]
    ) -> NucleotideChain:
        nc = cls(name)

        contents = h5_contents["nucleotides"]
        nucleotides = []
        for index in nucl_indexes:
            args = [literal_eval(arg.decode("utf8")) for arg in contents[index]]
            nucl = Nucleotide.build(h5_contents, *args)
            nucl.parent = nc
            nucleotides.append(nucl)

        try:
            nc.set_nucleotides(nucleotides)
        except (InvalidNucleotideChainError, InvalidResidueError) as e:
            raise CorruptedFileError(
                f"Could not reconstruct NucleotideChain with name {name} from the HDF5 trajectory "
                f"due to an issue with the terminal nucleotides. The NucleotideChain that could "
                f"not be reconstructed is located in the trajectory at /chemical_system/"
                f"nucleotide_chains at index INDEX. The original error is:\n{str(e)}"
            )
    def serialize(self, h5_contents: dict[str, list[list[str]]]) -> tuple[str, int]:
        if "nucleotides" in h5_contents:
            res_indexes = list(
                range(
                    len(h5_contents["nucleotides"]),
                    len(h5_contents["nucleotides"]) + len(self._nucleotides),
                )
            )
        else:
            res_indexes = list(range(len(self._nucleotides)))

        for nucl in self._nucleotides:
            nucl.serialize(h5_contents)

        h5_contents.setdefault("nucleotide_chains", []).append(
            [repr(self._name), str(res_indexes)]
        )

        return "nucleotide_chains", len(h5_contents["nucleotide_chains"]) - 1
     
class PeptideChain:

    @classmethod
    def build(
        cls, 
        h5_contents: dict[str, list[list[str]]], 
        name: str, 
        res_indexes: list[int]
    ) -> PeptideChain:
        pc = cls(name)

        contents = h5_contents["residues"]
        residues = []
        for index in res_indexes:
            args = [literal_eval(arg.decode("utf8")) for arg in contents[index]]
            res = Residue.build(h5_contents, *args)
            res.parent = pc
            residues.append(res)

        try:
            pc.set_residues(residues)
        except (InvalidPeptideChainError, InvalidResidueError) as e:
            raise CorruptedFileError(
                f"Could not reconstruct PeptideChain with name {name} from the HDF5 trajectory "
                f"due to an issue with the terminal residues. The PeptideChain that could "
                f"not be reconstructed is located in the trajectory at /chemical_system/"
                f"peptide_chains at index INDEX. The original error is:\n{str(e)}"
            )
    def serialize(self, h5_contents: dict[str, list[list[str]]]) -> tuple[str, int]:
        if "residues" in h5_contents:
            res_indexes = list(
                range(
                    len(h5_contents["residues"]),
                    len(h5_contents["residues"]) + len(self._residues),
                )
            )
        else:
            res_indexes = list(range(len(self._residues)))

        for res in self._residues:
            res.serialize(h5_contents)

        h5_contents.setdefault("peptide_chains", []).append(
            [repr(self._name), str(res_indexes)]
        )

        return "peptide_chains", len(h5_contents["peptide_chains"]) - 1        

        return pc

class Protein:

    @classmethod
    def build(
        cls,
        h5_contents: dict[str, list[list[str]]],
        name: str,
        peptide_chain_indexes: list[int],
    ) -> Protein:
        p = cls(name)

        contents = h5_contents["peptide_chains"]
        peptide_chains = []
        for index in peptide_chain_indexes:
            args = [literal_eval(arg.decode("utf8")) for arg in contents[index]]
            pc = PeptideChain.build(h5_contents, *args)
            pc.parent = p
            peptide_chains.append(pc)

        p.set_peptide_chains(peptide_chains)
    def serialize(self, h5_contents: dict[str, list[list[str]]]) -> tuple[str, int]:
        if "peptide_chains" in h5_contents:
            pc_indexes = list(
                range(
                    len(h5_contents["peptide_chains"]),
                    len(h5_contents["peptide_chains"]) + len(self._peptide_chains),
                )
            )
        else:
            pc_indexes = list(range(len(self._peptide_chains)))

        h5_contents.setdefault("proteins", []).append(
            [repr(self._name), str(pc_indexes)]
        )

        for pc in self._peptide_chains:
            pc.serialize(h5_contents)

        return "proteins", len(h5_contents["proteins"]) - 1
        return p


        writer.close()
 
    def write_configuration(self, h5_file, trajectory_file):
        configuration_grp = h5_file.create_group("/configuration")
        for varname, var in trajectory_file.variables.items():
            if varname not in ['time', 'unit_cell', 'chemical_entity']:  
                data = var[:]
                dtype = data.dtype 
                dset = configuration_grp.create_dataset(
                    varname,
                    data=data,
                    dtype=dtype,
                    compression='gzip')
                if hasattr(var, 'units'):
                    dset.attrs["units"] = var.units
        if 'unit_cell' in trajectory_file.variables:
            unit_cell_grp = h5_file.create_group("/unit_cell")
            unit_cell = trajectory_file.variables['unit_cell'][:]
            dtype = unit_cell.dtype  
            unit_cell_dset = unit_cell_grp.create_dataset(
                "data",
                data=unit_cell,
                dtype=dtype)
            if hasattr(trajectory_file.variables['unit_cell'], 'units'):
                unit_cell_dset.attrs["units"] = trajectory_file.variables['unit_cell'].units
        if 'time' in trajectory_file.variables:
            time_grp = h5_file.create_group("/time")
            time = trajectory_file.variables['time'][:]
            dtype = time.dtype  
            time_dset = time_grp.create_dataset(
                "data",
                data=time,
                dtype=dtype)
            if hasattr(trajectory_file.variables['time'], 'units'):
                time_dset.attrs["units"] = trajectory_file.variables['time'].units



    def convert_trajectory_to_hdf5(self, h5_filename):
        try:
            with Dataset(self.trajectory_filename, 'r') as trajectory_file:
                chemical_entity_data = None
                if 'chemical_entity' in trajectory_file.variables:
                    chemical_entity_data = trajectory_file.variables['chemical_entity'][:]

                with h5py.File(h5_filename, 'w') as h5_file:
                    self.serialize(h5_file, trajectory_file, chemical_entity_data)
                    self.write_configuration(h5_file, trajectory_file)

                    self._write_trajectory_data(h5_file)

                    print(f"Converted {self.trajectory_filename} to {h5_filename}.")
        except Exception as e:
            print(f"Error converting {self.trajectory_filename} to HDF5: {e}")

    def _write_trajectory_data(self, h5_file):

        writer = TrajectoryWriter(
            h5_file,
            self.chemical_system,
            self.n_steps,
            selected_atoms=None,  
            positions_dtype=np.float64,
            chunking_axis=1,
            compression="none",  
        )
        for step in range(self.n_steps):
            writer.dump_configuration(time, units)


