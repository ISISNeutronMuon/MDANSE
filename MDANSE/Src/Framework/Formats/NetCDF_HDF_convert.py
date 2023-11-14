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
 
class HDF5TrajectoryConverter(TrajectoryConverter):
    def __init__(self, trajectory_filename):
        self.trajectory_filename = trajectory_filename
        self.chemical_system = None
 
    def serialize(self, h5_file, trajectory_file, chemical_entity_data):
        if chemical_entity_data is not None:
            atoms = []
            for data in chemical_entity_data:
                atom = Atom(*data)
                atoms.append(atom)
            self.chemical_system = ChemicalSystem(atoms)
            chemical_group = h5_file.create_group("ChemicalSystem")
            for i, atom in enumerate(self.chemical_system.get_atoms()):
                atom_group = chemical_group.create_group(f"Atom_{i}")
                atom_group.create_dataset("element", data=atom.element)
                atom_group.create_dataset("mass", data=atom.mass)
                atom_group.create_dataset("position", data=atom.position)
 
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
                    print(f"Converted {self.trajectory_filename} to {h5_filename}.")
        except Exception as e:
            print(f"Error converting {self.trajectory_filename} to HDF5: {e}")
 
