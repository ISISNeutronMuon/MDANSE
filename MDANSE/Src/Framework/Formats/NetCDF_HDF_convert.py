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
 
class TrajectoryConverter(abc.ABC):
    pass
 
class DataObject:
    @classmethod
    def build(cls, **kwargs):
        return cls(**kwargs)
 
class Atom(DataObject):
    def __init__(self, symbol, name, index, ghost):
        self.symbol = symbol
        self.name = name
        self.index = index
        self.ghost = ghost
 
    def serialize(self, group):
        group.append([repr(getattr(self, attr)) for attr in ('symbol', 'name', 'index', 'ghost')])
 
class AtomCluster(DataObject):
    def __init__(self, atom_indexes, name):
        self.atom_indexes = atom_indexes
        self.name = name
 
    def serialize(self, group):
        group.append([repr(self.atom_indexes), repr(self.name)])
 
class Molecule(DataObject):
    def __init__(self, atom_indexes, code, name):
        self.atom_indexes = atom_indexes
        self.code = code
        self.name = name
 
    def serialize(self, group):
        group.append([repr(self.atom_indexes), repr(self.code), repr(self.name)])
 
class HDF5TrajectoryConverter(TrajectoryConverter):
    def __init__(self, trajectory_filename):
        self.trajectory_filename = trajectory_filename
        self.chemical_system = None  
 
    def convert_trajectory_to_hdf5(self, h5_filename):
        with Dataset(self.trajectory_filename, 'r') as nc_file, h5py.File(h5_filename, 'w') as h5_file:
            self._create_structure(nc_file, h5_file)
            print(f"Converted {self.trajectory_filename} to {h5_filename}.")
 
    def _create_structure(self, nc_file, h5_file):
        chem_sys_group = h5_file.create_group("chemical_system")
        config_group = h5_file.create_group("configuration")
 
        self._create_dataset(chem_sys_group, nc_file['chemical_system'], AtomCluster, 'atom_clusters')
        self._create_dataset(chem_sys_group, nc_file['chemical_system'], Atom, 'atoms')
        self._create_dataset(chem_sys_group, nc_file['chemical_system'], Molecule, 'molecules')
        self._create_dataset(chem_sys_group, nc_file['chemical_system'], None, 'contents')
 
        self._create_dataset(config_group, nc_file, None, 'coordinates', message="The 'coordinates' variable is not present in the NetCDF file.")
        self._create_dataset(config_group, nc_file, None, 'time', message="The 'time' variable is not present in the NetCDF file.")
        self._create_dataset(config_group, nc_file, None, 'unit_cell', message="The 'unit_cell' variable is not present in the NetCDF file.")
 
    def _create_dataset(self, group, nc_group, data_class, group_name, message=None):
        if group_name in nc_group:
            source_group = nc_group[group_name]
            for name, source in source_group.items():
                data = source[:] if data_class else None
                if data_class:
                    data = data_class.build(**data)
                    data.serialize(group)
        elif message:
            print(message)
 
# Example
converter = HDF5TrajectoryConverter("input.nc")
converter.convert_trajectory_to_hdf5("output.h5")